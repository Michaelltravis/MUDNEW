"""
RealmsMUD Auction House
=======================
Player economy system with fixed-price and bidding listings.
Persisted to data/auction_house.json independent of player saves.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger('RealmsMUD.AuctionHouse')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
AUCTION_FILE = os.path.join(DATA_DIR, 'auction_house.json')

# Constants
LISTING_FEE_PERCENT = 0.05      # 5% listing fee
TRANSACTION_TAX_PERCENT = 0.10  # 10% sales tax (gold sink)
MAX_LISTINGS_PER_PLAYER = 10
LISTING_DURATION_SECONDS = 48 * 3600  # 48 hours
AUCTION_HOUSE_ROOM = 3014       # Market Square in Midgaard
AUCTIONEER_NAME = "Guildmaster Harlan"

CATEGORIES = {
    'weapons': ['weapon'],
    'armor': ['armor'],
    'materials': ['material', 'component', 'ore', 'herb', 'skin', 'fish'],
    'consumables': ['food', 'drink', 'potion', 'scroll', 'pill'],
    'misc': ['light', 'container', 'treasure', 'key', 'boat', 'other', 'furniture', 'wand', 'staff'],
}

# Flags that prevent auctioning
FORBIDDEN_FLAGS = {'soulbound', 'quest_item', 'no_drop', 'no_sell', 'no_auction', 'nodrop', 'nosell'}


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _categorize_item(item) -> str:
    """Determine auction category for an item."""
    item_type = getattr(item, 'item_type', 'other')
    for cat, types in CATEGORIES.items():
        if item_type in types:
            return cat
    return 'misc'


class AuctionHouse:
    """Manages all auction listings and transactions."""

    _data = None  # In-memory cache

    @classmethod
    def _load(cls) -> dict:
        if cls._data is not None:
            return cls._data
        _ensure_dir()
        if os.path.exists(AUCTION_FILE):
            try:
                with open(AUCTION_FILE, 'r') as f:
                    cls._data = json.load(f)
            except Exception:
                cls._data = {'listings': [], 'history': [], 'price_history': {}, 'next_id': 1}
        else:
            cls._data = {'listings': [], 'history': [], 'price_history': {}, 'next_id': 1}
        return cls._data

    @classmethod
    def _save(cls):
        _ensure_dir()
        data = cls._load()
        with open(AUCTION_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def _next_id(cls) -> int:
        data = cls._load()
        lid = data.get('next_id', 1)
        data['next_id'] = lid + 1
        return lid

    @classmethod
    def get_active_listings(cls, category: str = None, keyword: str = None) -> List[dict]:
        data = cls._load()
        now = time.time()
        results = []
        for listing in data['listings']:
            if listing.get('sold') or listing.get('cancelled'):
                continue
            if listing.get('expires', 0) < now:
                continue
            if category and listing.get('category') != category:
                continue
            if keyword:
                kw = keyword.lower()
                if kw not in listing.get('item_name', '').lower() and kw not in listing.get('item_short', '').lower():
                    continue
            results.append(listing)
        return results

    @classmethod
    def get_player_listings(cls, player_name: str) -> List[dict]:
        data = cls._load()
        now = time.time()
        return [l for l in data['listings']
                if l.get('seller') == player_name and not l.get('sold')
                and not l.get('cancelled') and l.get('expires', 0) >= now]

    @classmethod
    def get_player_history(cls, player_name: str, limit: int = 20) -> List[dict]:
        data = cls._load()
        name_lower = player_name.lower()
        relevant = [h for h in data.get('history', [])
                    if h.get('seller', '').lower() == name_lower
                    or h.get('buyer', '').lower() == name_lower]
        return relevant[-limit:]

    @classmethod
    def create_listing(cls, player: 'Player', item, price: int, is_auction: bool = False, min_bid: int = 0) -> dict:
        """Create a new auction listing. Returns dict with 'success' and 'message'."""
        # Check location
        if not player.room or getattr(player.room, 'vnum', 0) != AUCTION_HOUSE_ROOM:
            return {'success': False, 'message': f'You must be at {AUCTIONEER_NAME} in Market Square to list items.'}

        # Check combat
        if player.fighting:
            player.fighting = None
            return {'success': False, 'message': "You can't auction items while fighting!"}

        # Check forbidden flags
        item_flags = getattr(item, 'flags', set())
        if isinstance(item_flags, list):
            item_flags = set(item_flags)
        if item_flags & FORBIDDEN_FLAGS:
            return {'success': False, 'message': 'That item cannot be auctioned.'}

        # Check max listings
        active = cls.get_player_listings(player.name)
        if len(active) >= MAX_LISTINGS_PER_PLAYER:
            return {'success': False, 'message': f'You already have {MAX_LISTINGS_PER_PLAYER} active listings.'}

        # Price validation
        if price < 1:
            return {'success': False, 'message': 'Price must be at least 1 gold.'}
        if price > 10000000:
            return {'success': False, 'message': 'Price cannot exceed 10,000,000 gold.'}

        # Listing fee
        fee = max(1, int(price * LISTING_FEE_PERCENT))
        if player.gold < fee:
            return {'success': False, 'message': f'You need {fee} gold for the listing fee (5% of price).'}

        # Deduct fee and remove item
        player.gold -= fee
        if item in player.inventory:
            player.inventory.remove(item)

        # Serialize item
        item_data = item.to_dict() if hasattr(item, 'to_dict') else {'name': str(item)}

        listing = {
            'id': cls._next_id(),
            'seller': player.name,
            'item_name': getattr(item, 'name', str(item)),
            'item_short': getattr(item, 'short_desc', getattr(item, 'name', str(item))),
            'item_data': item_data,
            'item_type': getattr(item, 'item_type', 'other'),
            'category': _categorize_item(item),
            'price': price,
            'is_auction': is_auction,
            'min_bid': min_bid if is_auction else 0,
            'current_bid': 0,
            'current_bidder': None,
            'created': time.time(),
            'expires': time.time() + LISTING_DURATION_SECONDS,
            'sold': False,
            'cancelled': False,
        }

        data = cls._load()
        data['listings'].append(listing)
        cls._save()

        return {
            'success': True,
            'message': f'Listed {listing["item_short"]} for {price} gold (fee: {fee}g). Listing #{listing["id"]}',
            'listing': listing,
        }

    @classmethod
    def buy_listing(cls, player: 'Player', listing_id: int) -> dict:
        """Buy a fixed-price listing or win an auction."""
        if not player.room or getattr(player.room, 'vnum', 0) != AUCTION_HOUSE_ROOM:
            return {'success': False, 'message': f'You must be at {AUCTIONEER_NAME} in Market Square to buy items.'}

        if player.fighting:
            player.fighting = None
            return {'success': False, 'message': "You can't buy items while fighting!"}

        data = cls._load()
        listing = None
        for l in data['listings']:
            if l['id'] == listing_id:
                listing = l
                break

        if not listing:
            return {'success': False, 'message': 'Listing not found.'}
        if listing.get('sold') or listing.get('cancelled'):
            return {'success': False, 'message': 'That listing is no longer available.'}
        if listing.get('expires', 0) < time.time():
            return {'success': False, 'message': 'That listing has expired.'}
        if listing['seller'] == player.name:
            return {'success': False, 'message': "You can't buy your own listing."}

        # For auction listings, this finalizes at current bid (only if auction ended)
        if listing.get('is_auction') and not listing.get('current_bidder'):
            return {'success': False, 'message': 'This is an auction listing. Use "auction bid <id> <amount>" to bid.'}

        price = listing['price']
        if listing.get('is_auction') and listing.get('current_bid', 0) > 0:
            # Buy-now at listed price for auctions
            pass

        if player.gold < price:
            return {'success': False, 'message': f'You need {price} gold to buy that. You have {player.gold}.'}

        # Process purchase
        player.gold -= price
        tax = max(1, int(price * TRANSACTION_TAX_PERCENT))
        seller_gets = price - tax

        listing['sold'] = True
        listing['buyer'] = player.name
        listing['sold_at'] = time.time()
        listing['sold_price'] = price

        # Give item to buyer
        from objects import Object
        item = Object.from_dict(listing['item_data'])
        player.inventory.append(item)

        # Credit seller (they may be offline — store as pending gold)
        cls._credit_seller(listing['seller'], seller_gets, listing['item_short'])

        # Record history
        history_entry = {
            'listing_id': listing['id'],
            'item_name': listing['item_short'],
            'seller': listing['seller'],
            'buyer': player.name,
            'price': price,
            'tax': tax,
            'time': time.time(),
            'type': 'auction' if listing.get('is_auction') else 'fixed',
        }
        data['history'].append(history_entry)

        # Update price history
        cls._record_price(listing['item_name'], price)

        cls._save()

        return {
            'success': True,
            'message': f'You purchased {listing["item_short"]} for {price} gold (tax: {tax}g). {AUCTIONEER_NAME} nods approvingly.',
            'item': item,
        }

    @classmethod
    def place_bid(cls, player: 'Player', listing_id: int, amount: int) -> dict:
        """Place a bid on an auction listing."""
        if not player.room or getattr(player.room, 'vnum', 0) != AUCTION_HOUSE_ROOM:
            return {'success': False, 'message': f'You must be at {AUCTIONEER_NAME} in Market Square to bid.'}

        data = cls._load()
        listing = None
        for l in data['listings']:
            if l['id'] == listing_id:
                listing = l
                break

        if not listing:
            return {'success': False, 'message': 'Listing not found.'}
        if not listing.get('is_auction'):
            return {'success': False, 'message': 'That listing is fixed-price. Use "auction buy <id>" instead.'}
        if listing.get('sold') or listing.get('cancelled'):
            return {'success': False, 'message': 'That listing is no longer available.'}
        if listing.get('expires', 0) < time.time():
            return {'success': False, 'message': 'That auction has expired.'}
        if listing['seller'] == player.name:
            return {'success': False, 'message': "You can't bid on your own listing."}

        min_required = max(listing.get('min_bid', 1), listing.get('current_bid', 0) + 1)
        if amount < min_required:
            return {'success': False, 'message': f'Minimum bid is {min_required} gold.'}
        if amount >= listing['price']:
            # Buyout
            return cls.buy_listing(player, listing_id)
        if player.gold < amount:
            return {'success': False, 'message': f'You need {amount} gold. You have {player.gold}.'}

        # Refund previous bidder
        if listing.get('current_bidder') and listing.get('current_bid', 0) > 0:
            cls._refund_bidder(listing['current_bidder'], listing['current_bid'], listing['item_short'])

        # Hold gold from new bidder
        player.gold -= amount
        listing['current_bid'] = amount
        listing['current_bidder'] = player.name

        cls._save()
        return {
            'success': True,
            'message': f'You bid {amount} gold on {listing["item_short"]} (listing #{listing_id}). Buyout: {listing["price"]}g.',
        }

    @classmethod
    def cancel_listing(cls, player: 'Player', listing_id: int) -> dict:
        """Cancel a listing and return item."""
        data = cls._load()
        listing = None
        for l in data['listings']:
            if l['id'] == listing_id:
                listing = l
                break

        if not listing:
            return {'success': False, 'message': 'Listing not found.'}
        if listing['seller'] != player.name:
            return {'success': False, 'message': "That's not your listing."}
        if listing.get('sold') or listing.get('cancelled'):
            return {'success': False, 'message': 'That listing is already closed.'}

        # Can't cancel if there's an active bid
        if listing.get('current_bidder') and listing.get('current_bid', 0) > 0:
            return {'success': False, 'message': "You can't cancel a listing with active bids."}

        listing['cancelled'] = True

        # Return item to player inventory (if at auction house) or via mail
        if player.room and getattr(player.room, 'vnum', 0) == AUCTION_HOUSE_ROOM:
            from objects import Object
            item = Object.from_dict(listing['item_data'])
            player.inventory.append(item)
            cls._save()
            return {'success': True, 'message': f'Listing #{listing_id} cancelled. {listing["item_short"]} returned to your inventory.'}
        else:
            cls._mail_item(player.name, listing['item_data'], listing['item_short'], 'cancelled listing')
            cls._save()
            return {'success': True, 'message': f'Listing #{listing_id} cancelled. {listing["item_short"]} sent to your mailbox.'}

    @classmethod
    def process_expirations(cls):
        """Process expired listings. Call periodically from game tick."""
        data = cls._load()
        now = time.time()
        changed = False

        for listing in data['listings']:
            if listing.get('sold') or listing.get('cancelled') or listing.get('expired'):
                continue
            if listing.get('expires', 0) >= now:
                continue

            # Expired
            listing['expired'] = True
            changed = True

            if listing.get('is_auction') and listing.get('current_bidder') and listing.get('current_bid', 0) > 0:
                # Auction ends — highest bidder wins
                price = listing['current_bid']
                tax = max(1, int(price * TRANSACTION_TAX_PERCENT))
                seller_gets = price - tax
                listing['sold'] = True
                listing['buyer'] = listing['current_bidder']
                listing['sold_at'] = now
                listing['sold_price'] = price

                # Send item to winner via mail
                cls._mail_item(listing['current_bidder'], listing['item_data'], listing['item_short'], 'auction win')
                cls._credit_seller(listing['seller'], seller_gets, listing['item_short'])

                data['history'].append({
                    'listing_id': listing['id'],
                    'item_name': listing['item_short'],
                    'seller': listing['seller'],
                    'buyer': listing['current_bidder'],
                    'price': price,
                    'tax': tax,
                    'time': now,
                    'type': 'auction',
                })
                cls._record_price(listing['item_name'], price)
            else:
                # No bids or fixed-price expired — return item to seller
                cls._mail_item(listing['seller'], listing['item_data'], listing['item_short'], 'expired listing')

        if changed:
            cls._save()

    @classmethod
    def _credit_seller(cls, seller_name: str, amount: int, item_name: str):
        """Credit gold to seller. If online, add directly; else mail notification."""
        from mail_system import MailManager
        MailManager.send_mail(
            'Auction House',
            seller_name,
            f'Your item "{item_name}" was sold! {amount} gold has been deposited to your account.\n'
            f'(After {int(TRANSACTION_TAX_PERCENT*100)}% transaction tax)'
        )
        # Store pending gold pickup
        data = cls._load()
        pending = data.get('pending_gold', {})
        pending[seller_name] = pending.get(seller_name, 0) + amount
        data['pending_gold'] = pending
        # Don't save here — caller saves

    @classmethod
    def collect_pending_gold(cls, player: 'Player') -> int:
        """Collect any pending gold from sales. Called when player visits auction house."""
        data = cls._load()
        pending = data.get('pending_gold', {})
        amount = pending.pop(player.name, 0)
        if amount > 0:
            player.gold += amount
            cls._save()
        return amount

    @classmethod
    def _refund_bidder(cls, bidder_name: str, amount: int, item_name: str):
        """Refund a previous bidder."""
        from mail_system import MailManager
        MailManager.send_mail(
            'Auction House',
            bidder_name,
            f'You were outbid on "{item_name}". {amount} gold has been refunded.'
        )
        data = cls._load()
        pending = data.get('pending_gold', {})
        pending[bidder_name] = pending.get(bidder_name, 0) + amount
        data['pending_gold'] = pending

    @classmethod
    def _mail_item(cls, player_name: str, item_data: dict, item_short: str, reason: str):
        """Send an item to a player via mail-like system (stored for pickup)."""
        data = cls._load()
        pending_items = data.get('pending_items', {})
        if player_name not in pending_items:
            pending_items[player_name] = []
        pending_items[player_name].append({
            'item_data': item_data,
            'item_short': item_short,
            'reason': reason,
            'time': time.time(),
        })
        data['pending_items'] = pending_items

        from mail_system import MailManager
        MailManager.send_mail(
            'Auction House',
            player_name,
            f'Your {reason} item "{item_short}" is available for pickup at the Auction House.'
        )

    @classmethod
    def collect_pending_items(cls, player: 'Player') -> List:
        """Collect pending items. Returns list of items added to inventory."""
        data = cls._load()
        pending = data.get('pending_items', {})
        items_data = pending.pop(player.name, [])
        if not items_data:
            return []

        from objects import Object
        collected = []
        for entry in items_data:
            item = Object.from_dict(entry['item_data'])
            player.inventory.append(item)
            collected.append(item)
        cls._save()
        return collected

    @classmethod
    def _record_price(cls, item_name: str, price: int):
        """Track price history for common items."""
        data = cls._load()
        ph = data.get('price_history', {})
        key = item_name.lower()
        if key not in ph:
            ph[key] = {'prices': [], 'avg': 0}
        ph[key]['prices'].append(price)
        # Keep last 50 prices
        ph[key]['prices'] = ph[key]['prices'][-50:]
        ph[key]['avg'] = sum(ph[key]['prices']) // len(ph[key]['prices'])
        data['price_history'] = ph

    @classmethod
    def get_avg_price(cls, item_name: str) -> Optional[int]:
        data = cls._load()
        ph = data.get('price_history', {})
        entry = ph.get(item_name.lower())
        return entry['avg'] if entry else None

    @classmethod
    def format_listing(cls, listing: dict, c: dict) -> str:
        """Format a single listing for display."""
        lid = listing['id']
        name = listing['item_short']
        price = listing['price']
        seller = listing['seller']
        cat = listing['category']

        time_left = listing.get('expires', 0) - time.time()
        if time_left > 3600:
            time_str = f"{int(time_left/3600)}h"
        elif time_left > 60:
            time_str = f"{int(time_left/60)}m"
        else:
            time_str = "<1m"

        bid_info = ""
        if listing.get('is_auction'):
            current = listing.get('current_bid', 0)
            bid_info = f" {c['cyan']}[BID: {current}g]" if current else f" {c['cyan']}[AUCTION]"

        return (f"  {c['bright_white']}#{lid:<5}{c['yellow']}{price:>9}g "
                f"{c['bright_green']}{name:<30} {c['white']}{cat:<12} "
                f"{c['magenta']}{seller:<14} {c['blue']}{time_str}{bid_info}{c['reset']}")
