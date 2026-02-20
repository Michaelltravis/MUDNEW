"""
Misthollow Group System
======================
Party formation, XP sharing, loot rules, group chat, auto-follow, and group effects.
"""

import logging
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

from config import Config

logger = logging.getLogger('Misthollow.Groups')

MAX_GROUP_SIZE = 6


class Group:
    """A party/group of players."""

    def __init__(self, leader: 'Player'):
        self.leader = leader
        self.members: List['Player'] = [leader]
        self.config = Config()
        self.loot_mode = 'freeforall'  # 'freeforall' or 'roundrobin'
        self._rr_index = 0  # round-robin pointer
        self.auto_follow = True  # members auto-follow leader on move

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def add_member(self, player: 'Player') -> bool:
        """Add a player to the group."""
        if player in self.members:
            return False
        if len(self.members) >= MAX_GROUP_SIZE:
            return False
        self.members.append(player)
        logger.info(f"{player.name} joined {self.leader.name}'s group")
        return True

    def remove_member(self, player: 'Player'):
        """Remove a player from the group."""
        if player in self.members:
            self.members.remove(player)
            player.group = None
            player.following = None
            logger.info(f"{player.name} left {self.leader.name}'s group")
        # If only one member left, auto-disband
        if len(self.members) <= 1:
            self.disband()

    def disband(self):
        """Disband the group."""
        for member in list(self.members):
            if hasattr(member, 'group'):
                member.group = None
                member.following = None
        self.members.clear()
        logger.info(f"Group disbanded")

    # ------------------------------------------------------------------
    # Leader management
    # ------------------------------------------------------------------

    def set_leader(self, new_leader: 'Player') -> bool:
        """Transfer leadership to another member."""
        if new_leader not in self.members:
            return False
        self.leader = new_leader
        # Move leader to front
        self.members.remove(new_leader)
        self.members.insert(0, new_leader)
        logger.info(f"{new_leader.name} is now group leader")
        return True

    # ------------------------------------------------------------------
    # Loot
    # ------------------------------------------------------------------

    def next_looter(self) -> 'Player':
        """Return the next player in the round-robin rotation."""
        if not self.members:
            return None
        self._rr_index = self._rr_index % len(self.members)
        looter = self.members[self._rr_index]
        self._rr_index = (self._rr_index + 1) % len(self.members)
        return looter

    # ------------------------------------------------------------------
    # XP sharing
    # ------------------------------------------------------------------

    def get_exp_bonus(self) -> float:
        """Get the group exp bonus multiplier.
        
        +10% per extra member beyond the first to incentivize grouping.
        """
        extra = max(0, len(self.members) - 1)
        return 1.0 + extra * 0.10

    def get_members_in_room(self, room) -> List['Player']:
        """Return group members present in the given room."""
        return [m for m in self.members if m.room == room]

    def get_exp_share(self, total_exp: int, room=None) -> Dict['Player', int]:
        """Calculate exp share for members in the same room as the kill.

        XP is split among members in the room, with a 10% bonus per extra
        member to incentivize grouping.
        """
        if room is None:
            # Fallback: equal share among all members
            eligible = self.members
        else:
            eligible = self.get_members_in_room(room)

        if not eligible:
            return {}

        # Bonus: +10% per extra member
        extra = max(0, len(eligible) - 1)
        bonus_mult = 1.0 + extra * 0.10
        total_with_bonus = int(total_exp * bonus_mult)

        # Level-weighted distribution
        avg_level = sum(m.level for m in eligible) / len(eligible)
        weights: Dict['Player', float] = {}
        total_weight = 0.0
        for member in eligible:
            level_diff = member.level - avg_level
            if level_diff < -5:
                w = 0.5
            elif level_diff < -2:
                w = 0.75
            else:
                w = 1.0
            weights[member] = w
            total_weight += w

        exp_per_member: Dict['Player', int] = {}
        for member, w in weights.items():
            exp_per_member[member] = int((w / total_weight) * total_with_bonus)

        return exp_per_member

    # ------------------------------------------------------------------
    # Communication
    # ------------------------------------------------------------------

    async def group_tell(self, sender: 'Player', message: str):
        """Send a message to all group members regardless of location."""
        c = self.config.COLORS
        for member in self.members:
            if member == sender:
                await member.send(f"{c['bright_cyan']}You tell the group, '{message}'{c['reset']}")
            else:
                await member.send(f"{c['bright_cyan']}{sender.name} tells the group, '{message}'{c['reset']}")

    # ------------------------------------------------------------------
    # Gold splitting
    # ------------------------------------------------------------------

    async def split_gold(self, total_gold: int):
        """Split gold evenly among group members."""
        if not self.members:
            return
        gold_per = total_gold // len(self.members)
        remainder = total_gold % len(self.members)
        c = self.config.COLORS
        for member in self.members:
            member.gold += gold_per
            await member.send(f"{c['yellow']}You receive {gold_per} gold as your share.{c['reset']}")
        if remainder > 0:
            self.leader.gold += remainder

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_member(self, player: 'Player') -> bool:
        return player in self.members

    def is_leader(self, player: 'Player') -> bool:
        return player == self.leader


class GroupManager:
    """Manages group operations."""

    # Pending invites: target_name -> {'from': player, 'group': group_or_None}
    _pending_invites: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Invite flow
    # ------------------------------------------------------------------

    @classmethod
    async def invite(cls, inviter: 'Player', target: 'Player'):
        """Invite a player to the group (creates one if needed)."""
        c = inviter.config.COLORS

        if target == inviter:
            await inviter.send(f"{c['red']}You can't invite yourself.{c['reset']}")
            return

        # Target already in a group?
        if getattr(target, 'group', None):
            await inviter.send(f"{c['red']}{target.name} is already in a group.{c['reset']}")
            return

        # Inviter's group full?
        group = getattr(inviter, 'group', None)
        if group and len(group.members) >= MAX_GROUP_SIZE:
            await inviter.send(f"{c['red']}Your group is full ({MAX_GROUP_SIZE} members max).{c['reset']}")
            return

        # Only leader (or solo player forming) can invite
        if group and group.leader != inviter:
            await inviter.send(f"{c['red']}Only the group leader can invite.{c['reset']}")
            return

        # Store pending invite
        cls._pending_invites[target.name.lower()] = {'from': inviter}
        await inviter.send(f"{c['green']}You invite {target.name} to join your group.{c['reset']}")
        await target.send(
            f"{c['bright_green']}{inviter.name} invites you to join their group.{c['reset']}\n"
            f"{c['cyan']}Type 'group accept' to join or 'group decline' to refuse.{c['reset']}"
        )

    @classmethod
    async def accept_invite(cls, player: 'Player'):
        """Accept a pending group invite."""
        c = player.config.COLORS
        invite = cls._pending_invites.pop(player.name.lower(), None)
        if not invite:
            await player.send(f"{c['yellow']}You have no pending group invitations.{c['reset']}")
            return

        inviter = invite['from']
        # Make the player follow the leader
        player.following = inviter

        success = await cls.join_group(inviter, player)
        if not success:
            player.following = None

    @classmethod
    async def decline_invite(cls, player: 'Player'):
        """Decline a pending group invite."""
        c = player.config.COLORS
        invite = cls._pending_invites.pop(player.name.lower(), None)
        if not invite:
            await player.send(f"{c['yellow']}You have no pending group invitations.{c['reset']}")
            return
        inviter = invite['from']
        await player.send(f"{c['yellow']}You decline {inviter.name}'s group invitation.{c['reset']}")
        await inviter.send(f"{c['yellow']}{player.name} declines your group invitation.{c['reset']}")

    # ------------------------------------------------------------------
    # Create / Join / Leave
    # ------------------------------------------------------------------

    @staticmethod
    async def create_group(leader: 'Player', member: 'Player') -> Optional[Group]:
        """Create a new group with leader and one member."""
        c = leader.config.COLORS

        if getattr(leader, 'group', None):
            await leader.send(f"{c['red']}You're already in a group!{c['reset']}")
            return None
        if getattr(member, 'group', None):
            await leader.send(f"{c['red']}{member.name} is already in a group!{c['reset']}")
            return None

        group = Group(leader)
        group.add_member(member)
        leader.group = group
        member.group = group
        member.following = leader

        await leader.send(f"{c['bright_green']}{member.name} joins your group!{c['reset']}")
        await member.send(f"{c['bright_green']}You join {leader.name}'s group!{c['reset']}")
        logger.info(f"{leader.name} formed a group with {member.name}")
        return group

    @staticmethod
    async def join_group(leader: 'Player', new_member: 'Player') -> bool:
        """Add a new member to an existing group or create one."""
        c = leader.config.COLORS

        if not getattr(leader, 'group', None):
            return await GroupManager.create_group(leader, new_member) is not None

        group = leader.group
        if not group.is_leader(leader):
            await leader.send(f"{c['red']}Only the group leader can add members!{c['reset']}")
            return False
        if getattr(new_member, 'group', None):
            await leader.send(f"{c['red']}{new_member.name} is already in a group!{c['reset']}")
            return False
        if not group.add_member(new_member):
            await leader.send(f"{c['red']}Your group is full! (Maximum {MAX_GROUP_SIZE} members){c['reset']}")
            return False

        new_member.group = group
        new_member.following = leader

        for member in group.members:
            if member == new_member:
                await member.send(f"{c['bright_green']}You join {leader.name}'s group!{c['reset']}")
            else:
                await member.send(f"{c['bright_green']}{new_member.name} joins the group!{c['reset']}")

        # Achievement: First Friend
        try:
            from achievements import AchievementManager
            await AchievementManager.check_group_join(new_member)
        except Exception:
            pass

        return True

    @staticmethod
    async def leave_group(player: 'Player'):
        """Leave the current group."""
        c = player.config.COLORS
        if not getattr(player, 'group', None):
            await player.send(f"{c['red']}You're not in a group!{c['reset']}")
            return

        group = player.group
        if group.is_leader(player):
            # Transfer leadership if possible
            if len(group.members) > 1:
                new_leader = group.members[1]
                group.set_leader(new_leader)
                group.remove_member(player)
                await player.send(f"{c['yellow']}You leave the group. {new_leader.name} is the new leader.{c['reset']}")
                for member in group.members:
                    await member.send(f"{c['yellow']}{player.name} left. {new_leader.name} is now leader.{c['reset']}")
            else:
                group.disband()
                await player.send(f"{c['yellow']}You disband the group.{c['reset']}")
        else:
            group.remove_member(player)
            await player.send(f"{c['yellow']}You leave the group.{c['reset']}")
            for member in group.members:
                await member.send(f"{c['yellow']}{player.name} leaves the group.{c['reset']}")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @staticmethod
    async def show_group(player: 'Player'):
        """Show group information."""
        c = player.config.COLORS

        try:
            from pets import PetManager
        except Exception:
            PetManager = None

        if not getattr(player, 'group', None):
            # Solo display with pets
            if PetManager:
                my_pets = PetManager.get_player_pets(player)
            else:
                my_pets = []
            if not my_pets:
                await player.send(f"{c['yellow']}You're not in a group.{c['reset']}")
                return

            await player.send(f"\n{c['bright_cyan']}╔══════════════════════════════════════════════════════════╗{c['reset']}")
            await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}                    Your Party                          {c['bright_cyan']}║{c['reset']}")
            await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")
            hp_pct = (player.hp / player.max_hp * 100) if player.max_hp > 0 else 0
            mp_pct = (player.mana / player.max_mana * 100) if player.max_mana > 0 else 0
            hp_color = c['bright_green'] if hp_pct > 75 else c['green'] if hp_pct > 50 else c['yellow'] if hp_pct > 25 else c['red']
            await player.send(
                f"{c['bright_cyan']}║ {c['white']}{player.name.ljust(20)} "
                f"Lv:{player.level:2} "
                f"{hp_color}HP:{hp_pct:3.0f}%{c['white']} "
                f"{c['bright_blue']}MP:{mp_pct:3.0f}%{c['white']}"
                f" {c['bright_cyan']}║{c['reset']}"
            )
            for pet in my_pets:
                pet_hp = (pet.hp / pet.max_hp * 100) if pet.max_hp > 0 else 0
                pet_hp_color = c['bright_green'] if pet_hp > 75 else c['green'] if pet_hp > 50 else c['yellow'] if pet_hp > 25 else c['red']
                pet_name = f"  └ {pet.name}".ljust(20)
                await player.send(
                    f"{c['bright_cyan']}║ {c['magenta']}{pet_name} "
                    f"Lv:{pet.level:2} "
                    f"{pet_hp_color}HP:{pet_hp:3.0f}%{c['white']}         "
                    f" {c['bright_cyan']}║{c['reset']}"
                )
            await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════╝{c['reset']}\n")
            return

        group = player.group
        loot_label = 'Round-Robin' if group.loot_mode == 'roundrobin' else 'Free-for-All'
        follow_label = 'On' if group.auto_follow else 'Off'

        await player.send(f"\n{c['bright_cyan']}╔══════════════════════════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_cyan']}║{c['bright_yellow']}                    Your Group                         {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}Leader: {group.leader.name.ljust(48)} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}Members: {len(group.members)}/{MAX_GROUP_SIZE}  Loot: {loot_label}  Follow: {follow_label}{' ' * 15} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}║ {c['white']}EXP Bonus: +{int((group.get_exp_bonus() - 1.0) * 100)}%{' ' * 42} {c['bright_cyan']}║{c['reset']}")
        await player.send(f"{c['bright_cyan']}╠══════════════════════════════════════════════════════════╣{c['reset']}")

        for member in group.members:
            hp_percent = (member.hp / member.max_hp * 100) if member.max_hp > 0 else 0
            mana_percent = (member.mana / member.max_mana * 100) if member.max_mana > 0 else 0
            if hp_percent > 75:
                hp_color = c['bright_green']
            elif hp_percent > 50:
                hp_color = c['green']
            elif hp_percent > 25:
                hp_color = c['yellow']
            else:
                hp_color = c['red']

            leader_mark = "[L] " if member == group.leader else "    "
            loc = member.room.name[:12] if member.room else '???'
            name_str = f"{leader_mark}{member.name}".ljust(18)

            await player.send(
                f"{c['bright_cyan']}║ {c['white']}{name_str} "
                f"Lv:{member.level:2} "
                f"{hp_color}HP:{hp_percent:3.0f}%{c['white']} "
                f"{c['bright_blue']}MP:{mana_percent:3.0f}%{c['white']} "
                f"{c['cyan']}{loc}{c['white']}"
                f" {c['bright_cyan']}║{c['reset']}"
            )

            # Show member's pets
            if PetManager:
                member_pets = PetManager.get_player_pets(member)
                for pet in member_pets:
                    pet_hp = (pet.hp / pet.max_hp * 100) if pet.max_hp > 0 else 0
                    pet_hp_color = c['bright_green'] if pet_hp > 75 else c['green'] if pet_hp > 50 else c['yellow'] if pet_hp > 25 else c['red']
                    pet_name = f"      └ {pet.name}".ljust(18)
                    await player.send(
                        f"{c['bright_cyan']}║ {c['magenta']}{pet_name} "
                        f"Lv:{pet.level:2} "
                        f"{pet_hp_color}HP:{pet_hp:3.0f}%{c['white']}              "
                        f" {c['bright_cyan']}║{c['reset']}"
                    )

        await player.send(f"{c['bright_cyan']}╚══════════════════════════════════════════════════════════╝{c['reset']}\n")

    # ------------------------------------------------------------------
    # Group effects: apply bard songs / paladin auras to group in room
    # ------------------------------------------------------------------

    @staticmethod
    def get_group_members_in_room(player: 'Player') -> List['Player']:
        """Return group members (including player) in the same room."""
        group = getattr(player, 'group', None)
        if not group:
            return [player]
        return [m for m in group.members if m.room == player.room]

    @staticmethod
    def apply_group_song_bonuses(bard: 'Player', bonuses: dict):
        """Apply bard song bonuses to all group members in the same room."""
        group = getattr(bard, 'group', None)
        if not group:
            # Solo: just apply to bard
            bard.song_bonuses = bonuses
            return
        for member in group.members:
            if member.room == bard.room:
                if not hasattr(member, 'song_bonuses'):
                    member.song_bonuses = {}
                member.song_bonuses.update(bonuses)

    @staticmethod
    def clear_group_song_bonuses(bard: 'Player'):
        """Clear bard song bonuses from group members."""
        group = getattr(bard, 'group', None)
        targets = group.members if group else [bard]
        for member in targets:
            if hasattr(member, 'song_bonuses'):
                member.song_bonuses = {}

    @staticmethod
    def get_group_paladin_auras(player: 'Player') -> set:
        """Get paladin auras from group members in the same room."""
        auras = set()
        group = getattr(player, 'group', None)
        targets = group.members if group else []
        # Also check non-grouped paladins in room (existing behavior)
        room_chars = getattr(player.room, 'characters', []) if player.room else []
        check_list = list(set(targets + list(room_chars)))
        for char in check_list:
            if hasattr(char, 'char_class') and str(getattr(char, 'char_class', '')).lower() == 'paladin':
                if char.room == player.room:
                    aura = getattr(char, 'active_aura', None)
                    if aura:
                        auras.add(aura)
        return auras
