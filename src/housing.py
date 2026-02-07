"""
RealmsMUD Housing System
========================
Provides simple player-owned housing and storage.
"""

import logging
from typing import Optional

logger = logging.getLogger('RealmsMUD.Housing')


class HouseManager:
    """Manages basic player housing."""

    DEFAULT_HOUSE_COST = 5000

    @staticmethod
    def can_buy_here(player) -> bool:
        if not player.room:
            return False
        return player.room.sector_type == 'city'

    @staticmethod
    async def buy_house(player, cost: Optional[int] = None) -> bool:
        """Buy a house in the current city room."""
        if hasattr(player, 'house_vnum') and player.house_vnum:
            c = player.config.COLORS
            await player.send(f"{c['yellow']}You already own a house.{c['reset']}")
            return False

        if not HouseManager.can_buy_here(player):
            c = player.config.COLORS
            await player.send(f"{c['red']}You can only buy a house in a city.{c['reset']}")
            return False

        cost = cost or HouseManager.DEFAULT_HOUSE_COST
        if player.gold < cost:
            c = player.config.COLORS
            await player.send(f"{c['red']}You need {cost} gold to buy a house.{c['reset']}")
            return False

        player.gold -= cost
        player.house_vnum = player.room.vnum
        if not hasattr(player, 'house_storage') or player.house_storage is None:
            player.house_storage = []

        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You purchase a modest house here!{c['reset']}")
        logger.info(f"{player.name} bought house at room {player.house_vnum}")
        return True

    @staticmethod
    def in_house(player) -> bool:
        return hasattr(player, 'house_vnum') and player.house_vnum and player.room and player.room.vnum == player.house_vnum
