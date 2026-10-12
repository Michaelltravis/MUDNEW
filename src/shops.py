"""
Misthollow Shop System
=====================
Merchant NPCs for buying and selling items.
"""

import logging
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from mobs import Mobile
    from objects import Object

from config import Config

logger = logging.getLogger('Misthollow.Shops')


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def repair_config(shop_config: Dict) -> Dict:
    """Undo the old shop import's misalignment. Many zones' shops were read a field off: the 2nd
    and 3rd products landed in markup and markdown (a 400-gold raft listed at 1,224,400), the
    buy profit in the list of what it buys ('1.2'), and the real buy types were lost. Products go
    back in the stock, a profit that slid into `buys` becomes the markup, and a shop left with
    no buy types gets its role's (World._ensure_shop)."""
    cfg = dict(shop_config or {})
    sells = [int(v) for v in (cfg.get('sells') or []) if _num(v) is not None]
    buys = list(cfg.get('buys') or [])
    markup, markdown = _num(cfg.get('markup', 1.5)), _num(cfg.get('markdown', 0.4))
    broken = markup is None or not 0.5 <= markup <= 10 or markdown is None or not 0 < markdown <= 1.5
    if broken:
        for x in (markup, markdown):
            if x is not None and x >= 100 and x == int(x):
                sells.append(int(x))
        profits = [_num(b) for b in buys if _num(b) is not None and 0 < _num(b) < 10]
        sells += [int(_num(b)) for b in buys if _num(b) is not None and _num(b) >= 100]
        markup = min(3.0, max(1.0, profits[0])) if profits else 1.5
        markdown = 0.4
    cfg['sells'] = list(dict.fromkeys(sells))
    cfg['markup'], cfg['markdown'] = markup, markdown
    # what it buys is item types, words: anything else is a mis-read field
    cfg['buys'] = [b for b in buys if isinstance(b, str) and b.isalpha()]
    return cfg


def carried(player, name: str):
    """What the player carries by `name`: "sword", or "2.sword" for the second (the /play shop
    window numbers by whole words; a part of a word still finds one when no word matches)."""
    name = str(name or '').strip().lower()
    n = 1
    if '.' in name and name.split('.', 1)[0].isdigit():
        n, name = int(name.split('.', 1)[0]), name.split('.', 1)[1]
    inv = list(getattr(player, 'inventory', None) or [])
    words = [it for it in inv if name in str(getattr(it, 'name', '')).lower().split()]
    found = words or [it for it in inv if name in str(getattr(it, 'name', '')).lower()]
    return found[n - 1] if 0 < n <= len(found) else None


class ShopKeeper:
    """Merchant NPC that buys and sells items."""

    def __init__(self, mob: 'Mobile', shop_config: Dict):
        self.mob = mob
        self.config = Config()

        shop_config = repair_config(shop_config)
        # What types of items this shop deals with
        self.buy_types = shop_config.get('buys', ['weapon', 'armor', 'treasure'])

        # Faction for reputation-based pricing
        self.faction = shop_config.get('faction') or getattr(mob, 'faction', None)
        self.min_rep_shop = getattr(mob, 'min_rep_shop', None)
        self.min_rep_shop_level = getattr(mob, 'min_rep_shop_level', None)

        # Items this shop sells (vnums)
        self.sells_vnums = shop_config.get('sells', [])

        # Pricing
        self.markup = shop_config.get('markup', 1.5)  # Sell at 150% of base value
        self.markdown = shop_config.get('markdown', 0.4)  # Buy at 40% of base value

        # Shop gold (for buying from players)
        self.gold = shop_config.get('starting_gold', 10000)

        # Operating hours (24-hour format)
        self.opening_hour = shop_config.get('opening_hour', 6)
        self.closing_hour = shop_config.get('closing_hour', 20)

        # Current inventory (items for sale)
        self.inventory = []

        # Items bought from players (to resell)
        self.bought_items = []

    def is_open(self, game_time) -> bool:
        """Check if shop is currently open."""
        if not game_time:
            return True  # Always open if no time system

        hour = game_time.hour
        if self.opening_hour < self.closing_hour:
            return self.opening_hour <= hour < self.closing_hour
        else:
            # Handles overnight shops (e.g., 20:00 to 6:00)
            return hour >= self.opening_hour or hour < self.closing_hour

    def get_sell_price(self, item: 'Object', player: Optional['Player'] = None) -> int:
        """Get the price this shop sells an item for."""
        base_value = getattr(item, 'value', 100)
        price = base_value * self.markup
        if player and self.faction:
            try:
                from factions import FactionManager
                modifier = FactionManager.get_price_modifier(player, FactionManager.normalize_key(self.faction))
                price *= modifier
            except Exception:
                pass
        return int(price)

    def get_buy_price(self, item: 'Object', player: Optional['Player'] = None) -> int:
        """Get the price this shop will pay for an item."""
        base_value = getattr(item, 'value', 100)
        price = base_value * self.markdown
        if player and self.faction:
            try:
                from factions import FactionManager
                modifier = FactionManager.get_price_modifier(player, FactionManager.normalize_key(self.faction))
                if modifier != 0:
                    price *= (1 / modifier)
            except Exception:
                pass
        return int(price)

    def will_buy(self, item: 'Object') -> bool:
        """Check if shop will buy this type of item."""
        item_type = getattr(item, 'item_type', 'misc')
        return item_type in self.buy_types

    def get_sellable_items(self) -> List['Object']:
        """Get all items available for sale."""
        return self.inventory + self.bought_items

    async def check_reputation_access(self, player: 'Player') -> bool:
        if not self.faction:
            return True
        try:
            from factions import FactionManager
            faction_key = FactionManager.normalize_key(self.faction)
            if not faction_key:
                return True
            min_required = None
            if self.min_rep_shop is not None:
                min_required = int(self.min_rep_shop)
            elif self.min_rep_shop_level:
                min_required = FactionManager.get_threshold_for_level(self.min_rep_shop_level)

            if min_required is None:
                return True

            if FactionManager.get_reputation(player, faction_key) < min_required:
                c = self.config.COLORS
                await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't do business with you.'{c['reset']}")
                return False
        except Exception:
            return True

        return True

    async def list_items(self, player: 'Player'):
        """Show player what's for sale."""
        c = self.config.COLORS

        if not await self.check_reputation_access(player):
            return

        items = self.get_sellable_items()

        if not items:
            await player.send(f"{c['yellow']}{self.mob.name} says, 'Sorry, I have nothing for sale right now.'{c['reset']}")
            return

        await player.send(f"\n{c['bright_cyan']}╔══════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}     {self.mob.name}'s Shop - Items for Sale           {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}Item                                      Price        {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")

        for i, item in enumerate(items, 1):
            price = self.get_sell_price(item, player)
            item_name = item.short_desc[:40].ljust(40)
            await player.send(f"{c['bright_cyan']}║ {c['white']}{i:2}. {item_name} {price:6} gold {c['bright_cyan']}║{c['reset']}")

        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════╝{c['reset']}")
        await player.send(f"{c['yellow']}Use 'buy <number>' or 'buy <item name>' to purchase.{c['reset']}\n")

    async def sell_to_player(self, player: 'Player', item_identifier: str) -> bool:
        """Sell an item to a player."""
        c = self.config.COLORS
        if not await self.check_reputation_access(player):
            return False
        items = self.get_sellable_items()

        # Find item by number or name
        item = None
        if item_identifier.isdigit():
            index = int(item_identifier) - 1
            if 0 <= index < len(items):
                item = items[index]
        else:
            for it in items:
                if item_identifier.lower() in it.name.lower():
                    item = it
                    break

        if not item:
            await player.send(f"{c['red']}{self.mob.name} says, 'I don't have that item.'{c['reset']}")
            return False

        price = self.get_sell_price(item, player)

        # Check if player has enough gold
        if player.gold < price:
            await player.send(f"{c['red']}{self.mob.name} says, 'You need {price} gold for that. You only have {player.gold}.'{c['reset']}")
            return False

        # Complete transaction
        player.gold -= price
        self.gold += price

        # Check if item is unlimited stock (food, drink, light, container)
        item_type = getattr(item, 'item_type', '').lower()
        unlimited_types = ['food', 'drink', 'light', 'container', 'potion']
        
        if item_type in unlimited_types and item in self.inventory:
            # Create a copy for the player, keep original in stock
            from objects import Object
            sold_item = Object.from_dict(item.to_dict(), player.world)
            player.inventory.append(sold_item)
        else:
            # Remove from shop inventory (limited stock)
            if item in self.inventory:
                self.inventory.remove(item)
            elif item in self.bought_items:
                self.bought_items.remove(item)
            # Give original to player
            player.inventory.append(item)

        await player.send(f"{c['bright_green']}{self.mob.name} says, 'Here you go! That'll be {price} gold.'{c['reset']}")
        await player.send(f"{c['green']}You buy {item.short_desc} for {price} gold.{c['reset']}")

        logger.info(f"{player.name} bought {item.name} from {self.mob.name} for {price} gold")
        return True

    async def buy_from_player(self, player: 'Player', item_name: str) -> bool:
        """Buy an item from a player."""
        c = self.config.COLORS
        if not await self.check_reputation_access(player):
            return False

        item = carried(player, item_name)

        if not item:
            await player.send(f"{c['red']}You don't have that item.{c['reset']}")
            return False

        # Check if shop will buy this type
        if not self.will_buy(item):
            await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't deal in that type of item.'{c['reset']}")
            return False

        price = self.get_buy_price(item, player)

        # a merchant never turns you away for want of coin: they send to their guild's
        # coffers for more (the owner: "ensure there's money so the merchants can transact")
        if self.gold < price:
            self.gold += max(price * 2, 10000)

        # Complete transaction
        player.gold += price
        self.gold -= price

        # Remove from player
        player.inventory.remove(item)

        # Add to shop's bought items
        self.bought_items.append(item)

        await player.send(f"{c['bright_green']}{self.mob.name} says, 'I'll give you {price} gold for that.'{c['reset']}")
        await player.send(f"{c['green']}You sell {item.short_desc} for {price} gold.{c['reset']}")

        logger.info(f"{player.name} sold {item.name} to {self.mob.name} for {price} gold")
        return True

    async def value_item(self, player: 'Player', item_name: str):
        """Tell player how much shop will pay for an item."""
        c = self.config.COLORS
        if not await self.check_reputation_access(player):
            return

        item = carried(player, item_name)

        if not item:
            await player.send(f"{c['red']}You don't have that item.{c['reset']}")
            return

        if not self.will_buy(item):
            await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't deal in that type of item.'{c['reset']}")
            return

        price = self.get_buy_price(item, player)
        await player.send(f"{c['cyan']}{self.mob.name} says, 'I'll give you {price} gold for {item.short_desc}.'{c['reset']}")


class ShopManager:
    """Manages all shops in the game."""

    shops = {}  # mob_vnum -> ShopKeeper

    @classmethod
    def create_shop(cls, mob: 'Mobile', shop_config: Dict, world: 'World') -> ShopKeeper:
        """Create a shop for a merchant mob."""
        shop = ShopKeeper(mob, shop_config)
        cls.shops[mob.vnum] = shop

        # Initialize shop inventory
        from objects import create_object
        for item_vnum in shop.sells_vnums:
            item = create_object(item_vnum, world)
            if item:
                shop.inventory.append(item)

        logger.info(f"Created shop for {mob.name} (vnum {mob.vnum}) with {len(shop.inventory)} items")
        return shop

    @classmethod
    def get_shop(cls, mob: 'Mobile') -> Optional[ShopKeeper]:
        """Get the shop for a merchant mob."""
        return cls.shops.get(mob.vnum)

    @classmethod
    def is_shopkeeper(cls, mob: 'Mobile') -> bool:
        """Check if a mob is a shopkeeper."""
        return hasattr(mob, 'special') and mob.special == 'shopkeeper'
