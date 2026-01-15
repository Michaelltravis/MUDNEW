"""
RealmsMUD Shop System
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

logger = logging.getLogger('RealmsMUD.Shops')


class ShopKeeper:
    """Merchant NPC that buys and sells items."""

    def __init__(self, mob: 'Mobile', shop_config: Dict):
        self.mob = mob
        self.config = Config()

        # What types of items this shop deals with
        self.buy_types = shop_config.get('buys', ['weapon', 'armor', 'treasure'])

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

    def get_sell_price(self, item: 'Object') -> int:
        """Get the price this shop sells an item for."""
        base_value = getattr(item, 'value', 100)
        return int(base_value * self.markup)

    def get_buy_price(self, item: 'Object') -> int:
        """Get the price this shop will pay for an item."""
        base_value = getattr(item, 'value', 100)
        return int(base_value * self.markdown)

    def will_buy(self, item: 'Object') -> bool:
        """Check if shop will buy this type of item."""
        item_type = getattr(item, 'item_type', 'misc')
        return item_type in self.buy_types

    def get_sellable_items(self) -> List['Object']:
        """Get all items available for sale."""
        return self.inventory + self.bought_items

    async def list_items(self, player: 'Player'):
        """Show player what's for sale."""
        c = self.config.COLORS

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
            price = self.get_sell_price(item)
            item_name = item.short_desc[:40].ljust(40)
            await player.send(f"{c['bright_cyan']}║ {c['white']}{i:2}. {item_name} {price:6} gold {c['bright_cyan']}║{c['reset']}")

        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════╝{c['reset']}")
        await player.send(f"{c['yellow']}Use 'buy <number>' or 'buy <item name>' to purchase.{c['reset']}\n")

    async def sell_to_player(self, player: 'Player', item_identifier: str) -> bool:
        """Sell an item to a player."""
        c = self.config.COLORS
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

        price = self.get_sell_price(item)

        # Check if player has enough gold
        if player.gold < price:
            await player.send(f"{c['red']}{self.mob.name} says, 'You need {price} gold for that. You only have {player.gold}.'{c['reset']}")
            return False

        # Complete transaction
        player.gold -= price
        self.gold += price

        # Remove from shop inventory
        if item in self.inventory:
            self.inventory.remove(item)
        elif item in self.bought_items:
            self.bought_items.remove(item)

        # Give to player
        player.inventory.append(item)

        await player.send(f"{c['bright_green']}{self.mob.name} says, 'Here you go! That'll be {price} gold.'{c['reset']}")
        await player.send(f"{c['green']}You buy {item.short_desc} for {price} gold.{c['reset']}")

        logger.info(f"{player.name} bought {item.name} from {self.mob.name} for {price} gold")
        return True

    async def buy_from_player(self, player: 'Player', item_name: str) -> bool:
        """Buy an item from a player."""
        c = self.config.COLORS

        # Find item in player's inventory
        item = None
        for it in player.inventory:
            if item_name.lower() in it.name.lower():
                item = it
                break

        if not item:
            await player.send(f"{c['red']}You don't have that item.{c['reset']}")
            return False

        # Check if shop will buy this type
        if not self.will_buy(item):
            await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't deal in that type of item.'{c['reset']}")
            return False

        price = self.get_buy_price(item)

        # Check if shop has enough gold
        if self.gold < price:
            await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't have enough gold to buy that right now.'{c['reset']}")
            return False

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

        # Find item in player's inventory
        item = None
        for it in player.inventory:
            if item_name.lower() in it.name.lower():
                item = it
                break

        if not item:
            await player.send(f"{c['red']}You don't have that item.{c['reset']}")
            return

        if not self.will_buy(item):
            await player.send(f"{c['yellow']}{self.mob.name} says, 'I don't deal in that type of item.'{c['reset']}")
            return

        price = self.get_buy_price(item)
        await player.send(f"{c['cyan']}{self.mob.name} says, 'I'll give you {price} gold for {item.short_desc}.'{c['reset']}")


class ShopManager:
    """Manages all shops in the game."""

    shops = {}  # mob_vnum -> ShopKeeper

    @classmethod
    def create_shop(cls, mob: 'Mobile', shop_config: Dict) -> ShopKeeper:
        """Create a shop for a merchant mob."""
        shop = ShopKeeper(mob, shop_config)
        cls.shops[mob.vnum] = shop

        # Initialize shop inventory
        from objects import create_object
        for item_vnum in shop.sells_vnums:
            item = create_object(item_vnum)
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
