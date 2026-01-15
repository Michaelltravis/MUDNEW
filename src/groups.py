"""
RealmsMUD Group System
======================
Party formation and group benefits.
"""

import logging
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

from config import Config

logger = logging.getLogger('RealmsMUD.Groups')


class Group:
    """A party/group of players."""

    def __init__(self, leader: 'Player'):
        self.leader = leader
        self.members = [leader]  # Leader is always first member
        self.config = Config()

    def add_member(self, player: 'Player') -> bool:
        """Add a player to the group."""
        if player in self.members:
            return False

        if len(self.members) >= 8:  # Max group size
            return False

        self.members.append(player)
        logger.info(f"{player.name} joined {self.leader.name}'s group")
        return True

    def remove_member(self, player: 'Player'):
        """Remove a player from the group."""
        if player in self.members:
            self.members.remove(player)
            logger.info(f"{player.name} left {self.leader.name}'s group")

    def disband(self):
        """Disband the group."""
        for member in list(self.members):
            if hasattr(member, 'group'):
                member.group = None
                member.following = None

        self.members.clear()
        logger.info(f"{self.leader.name}'s group disbanded")

    def get_exp_bonus(self) -> float:
        """Get the group exp bonus multiplier."""
        # +10% per member, max +50% for 6+ members
        bonus_per_member = 0.10
        max_bonus = 0.50
        bonus = min(len(self.members) * bonus_per_member, max_bonus)
        return 1.0 + bonus

    def get_exp_share(self, total_exp: int) -> dict:
        """
        Calculate exp share for each member.

        Takes into account level differences to prevent power-leveling.
        """
        if not self.members:
            return {}

        bonus_mult = self.get_exp_bonus()
        total_with_bonus = int(total_exp * bonus_mult)

        # Calculate average level
        avg_level = sum(m.level for m in self.members) / len(self.members)

        # Calculate shares based on level relative to average
        shares = {}
        total_weight = 0

        for member in self.members:
            # Members significantly below average get reduced share
            level_diff = member.level - avg_level
            if level_diff < -5:
                weight = 0.5  # 50% for low levels
            elif level_diff < -2:
                weight = 0.75  # 75% for slightly low
            else:
                weight = 1.0  # Full share

            shares[member] = weight
            total_weight += weight

        # Distribute exp proportionally
        exp_per_member = {}
        for member, weight in shares.items():
            member_exp = int((weight / total_weight) * total_with_bonus)
            exp_per_member[member] = member_exp

        return exp_per_member

    async def group_tell(self, sender: 'Player', message: str):
        """Send a message to all group members."""
        c = self.config.COLORS

        for member in self.members:
            if member == sender:
                await member.send(f"{c['bright_cyan']}You tell the group, '{message}'{c['reset']}")
            else:
                await member.send(f"{c['bright_cyan']}{sender.name} tells the group, '{message}'{c['reset']}")

    async def split_gold(self, total_gold: int):
        """Split gold evenly among group members."""
        if not self.members:
            return

        gold_per_member = total_gold // len(self.members)
        remainder = total_gold % len(self.members)

        c = self.config.COLORS

        for member in self.members:
            member.gold += gold_per_member
            await member.send(f"{c['yellow']}You receive {gold_per_member} gold as your share.{c['reset']}")

        # Give remainder to leader
        if remainder > 0:
            self.leader.gold += remainder

    def is_member(self, player: 'Player') -> bool:
        """Check if a player is in this group."""
        return player in self.members

    def is_leader(self, player: 'Player') -> bool:
        """Check if a player is the group leader."""
        return player == self.leader


class GroupManager:
    """Manages all groups in the game."""

    @staticmethod
    async def create_group(leader: 'Player', member: 'Player') -> Optional[Group]:
        """Create a new group with leader and one member."""
        c = leader.config.COLORS

        # Check if either player is already in a group
        if hasattr(leader, 'group') and leader.group:
            await leader.send(f"{c['red']}You're already in a group!{c['reset']}")
            return None

        if hasattr(member, 'group') and member.group:
            await leader.send(f"{c['red']}{member.name} is already in a group!{c['reset']}")
            return None

        # Check if member is following leader
        if not hasattr(member, 'following') or member.following != leader:
            await leader.send(f"{c['red']}{member.name} must be following you first!{c['reset']}")
            return None

        # Create group
        group = Group(leader)
        group.add_member(member)

        leader.group = group
        member.group = group

        await leader.send(f"{c['bright_green']}{member.name} joins your group!{c['reset']}")
        await member.send(f"{c['bright_green']}You join {leader.name}'s group!{c['reset']}")

        logger.info(f"{leader.name} formed a group with {member.name}")
        return group

    @staticmethod
    async def join_group(leader: 'Player', new_member: 'Player') -> bool:
        """Add a new member to an existing group."""
        c = leader.config.COLORS

        if not hasattr(leader, 'group') or not leader.group:
            # Create new group
            return await GroupManager.create_group(leader, new_member) is not None

        group = leader.group

        if not group.is_leader(leader):
            await leader.send(f"{c['red']}Only the group leader can add members!{c['reset']}")
            return False

        if hasattr(new_member, 'group') and new_member.group:
            await leader.send(f"{c['red']}{new_member.name} is already in a group!{c['reset']}")
            return False

        if not hasattr(new_member, 'following') or new_member.following != leader:
            await leader.send(f"{c['red']}{new_member.name} must be following you first!{c['reset']}")
            return False

        if not group.add_member(new_member):
            await leader.send(f"{c['red']}Your group is full! (Maximum 8 members){c['reset']}")
            return False

        new_member.group = group

        # Announce to group
        for member in group.members:
            if member == new_member:
                await member.send(f"{c['bright_green']}You join {leader.name}'s group!{c['reset']}")
            else:
                await member.send(f"{c['bright_green']}{new_member.name} joins the group!{c['reset']}")

        return True

    @staticmethod
    async def leave_group(player: 'Player'):
        """Leave the current group."""
        c = player.config.COLORS

        if not hasattr(player, 'group') or not player.group:
            await player.send(f"{c['red']}You're not in a group!{c['reset']}")
            return

        group = player.group

        if group.is_leader(player):
            # Leader leaving disbands the group
            for member in group.members:
                if member != player:
                    await member.send(f"{c['yellow']}{player.name} has disbanded the group.{c['reset']}")

            group.disband()
            await player.send(f"{c['yellow']}You disband the group.{c['reset']}")
        else:
            # Member leaving
            group.remove_member(player)
            player.group = None
            player.following = None

            await player.send(f"{c['yellow']}You leave the group.{c['reset']}")

            for member in group.members:
                await member.send(f"{c['yellow']}{player.name} leaves the group.{c['reset']}")

    @staticmethod
    async def show_group(player: 'Player'):
        """Show group information."""
        c = player.config.COLORS

        if not hasattr(player, 'group') or not player.group:
            await player.send(f"{c['yellow']}You're not in a group.{c['reset']}")
            return

        group = player.group

        await player.send(f"\n{c['bright_cyan']}╔══════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}                    Your Group                         {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}Leader: {group.leader.name.ljust(48)} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}Members: {len(group.members)}/8{' ' * 44} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}EXP Bonus: +{int((group.get_exp_bonus() - 1.0) * 100)}%{' ' * 42} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")

        for member in group.members:
            hp_percent = (member.hp / member.max_hp * 100) if member.max_hp > 0 else 0
            mana_percent = (member.mana / member.max_mana * 100) if member.max_mana > 0 else 0

            # Color code HP
            if hp_percent > 75:
                hp_color = c['bright_green']
            elif hp_percent > 50:
                hp_color = c['green']
            elif hp_percent > 25:
                hp_color = c['yellow']
            else:
                hp_color = c['red']

            leader_mark = "[LEADER] " if member == group.leader else ""
            name_str = f"{leader_mark}{member.name}".ljust(20)

            await player.send(
                f"{c['bright_cyan']}║ {c['white']}{name_str} "
                f"Lv:{member.level:2} "
                f"{hp_color}HP:{hp_percent:3.0f}%{c['white']} "
                f"{c['bright_blue']}MP:{mana_percent:3.0f}%{c['white']}"
                f" {c['bright_cyan']}║{c['reset']}"
            )

        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════╝{c['reset']}\n")
