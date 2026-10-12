"""
Misthollow Group System
======================
Party formation, XP sharing, loot rules, group chat, auto-follow, and group effects.
"""

import asyncio
import logging
import random
import time
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
        self.loot_mode = 'roll'  # 'roll' (need/greed/pass), 'freeforall' or 'roundrobin'
        self._rr_index = 0  # round-robin pointer
        self.active_rolls: List['LootRoll'] = []
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
        """Disband the group (open loot rolls end: their items go back to the corpse)."""
        for roll in list(self.active_rolls):
            roll.cancel()
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
        # the group follows its new leader (no one keeps trailing the old one)
        for member in self.members:
            member.following = None if member is new_leader else (new_leader if self.auto_follow else None)
        logger.info(f"{new_leader.name} is now group leader")
        return True

    # ------------------------------------------------------------------
    # Loot
    # ------------------------------------------------------------------

    def next_looter(self, present: Optional[List['Player']] = None) -> 'Player':
        """Return the next player in the round-robin rotation (among `present`, when given)."""
        if not self.members:
            return None
        for _ in range(len(self.members)):
            self._rr_index = self._rr_index % len(self.members)
            looter = self.members[self._rr_index]
            self._rr_index = (self._rr_index + 1) % len(self.members)
            if present is None or looter in present:
                return looter
        return present[0] if present else None

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

    async def split_gold(self, total_gold: int, among: Optional[List['Player']] = None):
        """Split gold evenly among group members (or those given: the ones present)."""
        members = [m for m in (among if among is not None else self.members) if getattr(m, 'connection', None)]
        if not members:
            return
        gold_per = total_gold // len(members)
        remainder = total_gold % len(members)
        c = self.config.COLORS
        for member in members:
            member.gold += gold_per
            await member.send(f"{c['yellow']}You receive {gold_per} gold as your share.{c['reset']}")
        if remainder > 0:
            (self.leader if self.leader in members else members[0]).gold += remainder

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

        # Store pending invite (it lapses after INVITE_SECONDS)
        cls._pending_invites[target.name.lower()] = {'from': inviter, 'at': time.time()}
        await inviter.send(f"{c['green']}You invite {target.name} to join your group.{c['reset']}")
        await target.send(
            f"{c['bright_green']}{inviter.name} invites you to join their group.{c['reset']}\n"
            f"{c['cyan']}Type 'group accept' to join or 'group decline' to refuse.{c['reset']}"
        )
        await _event(target, {'type': 'group_invite', 'from': inviter.name, 'level': getattr(inviter, 'level', 1),
                              'char_class': getattr(inviter, 'char_class', ''), 'expires': INVITE_SECONDS})

    @classmethod
    async def accept_invite(cls, player: 'Player'):
        """Accept a pending group invite."""
        c = player.config.COLORS
        invite = cls._pending_invites.pop(player.name.lower(), None)
        if invite and time.time() - invite.get('at', 0) > INVITE_SECONDS:
            invite = None
        if not invite:
            await player.send(f"{c['yellow']}You have no pending group invitations.{c['reset']}")
            return

        inviter = invite['from']
        if not getattr(inviter, 'connection', None):
            await player.send(f"{c['yellow']}{inviter.name} is no longer here.{c['reset']}")
            return
        success = await cls.join_group(inviter, player)
        if success:
            await broadcast(inviter.group)

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
        member.following = leader if group.auto_follow else None

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
        new_member.following = leader if group.auto_follow else None

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
    async def leave_group(player: 'Player', reason: str = 'leaves'):
        """Leave the current group; the others are told, even the last one left."""
        c = player.config.COLORS
        group = getattr(player, 'group', None)
        if not group:
            await player.send(f"{c['red']}You're not in a group!{c['reset']}")
            return
        others = [m for m in group.members if m is not player]
        new_leader = None
        if group.is_leader(player) and others:
            new_leader = others[0]
            group.set_leader(new_leader)
        group.remove_member(player)          # disbands when one member would be left
        if reason == 'leaves':
            await player.send(f"{c['yellow']}You leave the group.{c['reset']}")
        line = {'leaves': f"{player.name} leaves the group.", 'quit': f"{player.name} has left the realm and the group.",
                'kicked': f"{player.name} has been removed from the group."}.get(reason, f"{player.name} leaves the group.")
        if group.members and new_leader:
            line += f" {new_leader.name} is now the leader."
        if not group.members:
            line += " The group is disbanded."
        for member in others:
            await member.send(f"{c['yellow']}{line}{c['reset']}")
        await _event(player, {'type': 'group', 'group': None})
        if group.members:
            await broadcast(group)
        else:
            for member in others:
                await _event(member, {'type': 'group', 'group': None})

    @classmethod
    async def kick(cls, leader: 'Player', target: 'Player'):
        """The leader removes a member (works in a group of two, which then disbands)."""
        c = leader.config.COLORS
        await target.send(f"{c['yellow']}{leader.name} removes you from the group.{c['reset']}")
        await leader.send(f"{c['yellow']}You remove {target.name} from the group.{c['reset']}")
        await cls.leave_group(target, reason='kicked')

    @classmethod
    async def disconnect(cls, player: 'Player'):
        """A member leaving the realm leaves the group too (no ghosts sharing loot and gold)."""
        cls._pending_invites.pop(player.name.lower(), None)
        for name, inv in list(cls._pending_invites.items()):
            if inv.get('from') is player:
                cls._pending_invites.pop(name, None)
        if getattr(player, 'group', None):
            await cls.leave_group(player, reason='quit')

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
        loot_label = {'roundrobin': 'Round-Robin', 'roll': 'Need/Greed roll'}.get(group.loot_mode, 'Free-for-All')
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


# ---------------------------------------------------------------------------
# Need / greed / pass loot rolls (modern group loot)
# ---------------------------------------------------------------------------
ROLL_TIMEOUT = 20
ROLL_WORTH_RARITIES = ('uncommon', 'rare', 'epic', 'legendary')
_roll_seq = 0


def _worth_rolling(item) -> bool:
    if getattr(item, 'rarity', 'common') in ROLL_WORTH_RARITIES:
        return True
    if getattr(item, 'item_type', '') in ('weapon', 'armor') and getattr(item, 'cost', 0) >= 50:
        return True
    return getattr(item, 'cost', 0) >= 200


class LootRoll:
    """One item up for need/greed/pass among the group members present."""

    def __init__(self, group: 'Group', item, corpse, members: List['Player']):
        global _roll_seq
        _roll_seq += 1
        self.id = _roll_seq
        self.group = group
        self.item = item
        self.corpse = corpse
        self.members = list(members)
        self.votes: Dict[str, str] = {}
        self.started = time.time()
        self.done = False
        self._task = None
        # the roll holds the item while it runs: nobody can pick it out of the corpse meanwhile
        if item in getattr(corpse, 'contents', []):
            corpse.contents.remove(item)

    def _give_back(self):
        """Return the item to its corpse (or the floor, if the corpse is gone)."""
        corpse = self.corpse
        room = getattr(getattr(self.group, 'leader', None), 'room', None)
        if corpse is not None and isinstance(getattr(corpse, 'contents', None), list) and \
                (room is None or corpse in getattr(room, 'items', [corpse])):
            corpse.contents.append(self.item)
        elif room is not None:
            room.items.append(self.item)

    def cancel(self):
        """The group broke up: the roll ends and the item goes back."""
        if self.done:
            return
        self.done = True
        if self._task:
            self._task.cancel()
        if self in self.group.active_rolls:
            self.group.active_rolls.remove(self)
        self._give_back()

    @property
    def item_name(self) -> str:
        return getattr(self.item, 'short_desc', None) or getattr(self.item, 'name', 'an item')

    def event(self) -> dict:
        return {'type': 'loot_roll', 'id': self.id, 'item': self.item_name,
                'rarity': getattr(self.item, 'rarity', 'common'), 'timeout': ROLL_TIMEOUT}

    async def announce(self):
        c = Config.COLORS
        for m in self.members:
            try:
                await m.send(f"{c['bright_yellow']}Loot roll: {self.item_name} — 'roll need', 'roll greed' or 'roll pass' ({ROLL_TIMEOUT}s).{c['reset']}")
                wm = getattr(getattr(m, 'world', None), 'web_map', None)
                if wm:
                    await wm.notify_event(m, self.event())
            except Exception:
                pass
        self._task = asyncio.create_task(self._expire())

    async def _expire(self):
        try:
            await asyncio.sleep(ROLL_TIMEOUT)
            await self.resolve()
        except asyncio.CancelledError:
            pass

    async def vote(self, player: 'Player', choice: str) -> bool:
        if self.done or player not in self.members:
            return False
        self.votes[player.name.lower()] = choice
        if all(m.name.lower() in self.votes for m in self.members):
            if self._task:
                self._task.cancel()
            await self.resolve()
        return True

    async def resolve(self):
        if self.done:
            return
        self.done = True
        c = Config.COLORS
        if self in self.group.active_rolls:
            self.group.active_rolls.remove(self)
        pool = [m for m in self.members if self.votes.get(m.name.lower()) == 'need']
        tier = 'need'
        if not pool:
            pool = [m for m in self.members if self.votes.get(m.name.lower()) == 'greed']
            tier = 'greed'
        # only someone still in the realm can win
        pool = [m for m in pool if getattr(m, 'connection', None)]
        if not pool:
            self._give_back()
            for m in self.members:
                try:
                    await m.send(f"{c['yellow']}Everyone passed on {self.item_name}; it stays in the corpse.{c['reset']}")
                    wm = getattr(getattr(m, 'world', None), 'web_map', None)
                    if wm:
                        await wm.notify_event(m, {'type': 'loot_result', 'id': self.id, 'item': self.item_name, 'winner': None})
                except Exception:
                    pass
            return
        rolls = {m.name: random.randint(1, 100) for m in pool}
        winner = max(pool, key=lambda m: rolls[m.name])
        try:
            winner.inventory.append(self.item)        # the roll held it: no one else has it
        except Exception:
            self._give_back()
        summary = ', '.join(f"{n} {r}" for n, r in sorted(rolls.items(), key=lambda kv: -kv[1]))
        for m in self.members:
            try:
                await m.send(f"{c['bright_green']}{winner.name} wins {self.item_name} ({tier}: {summary}).{c['reset']}")
                wm = getattr(getattr(m, 'world', None), 'web_map', None)
                if wm:
                    await wm.notify_event(m, {'type': 'loot_result', 'id': self.id, 'item': self.item_name,
                                              'winner': winner.name, 'tier': tier, 'rolls': rolls})
            except Exception:
                pass


async def start_rolls(killer: 'Player', corpse) -> int:
    """After a group kill, put each worthwhile item in the corpse up for a roll
    among the members standing in the room. Returns the number of rolls."""
    group = getattr(killer, 'group', None)
    if not group or group.loot_mode != 'roll' or not getattr(corpse, 'contents', None):
        return 0
    room = getattr(killer, 'room', None)
    members = [m for m in group.members if getattr(m, 'room', None) is room and getattr(m, 'connection', None)]
    if len(members) < 2:
        return 0
    n = 0
    for item in list(corpse.contents):
        if not _worth_rolling(item):
            continue
        roll = LootRoll(group, item, corpse, members)
        group.active_rolls.append(roll)
        await roll.announce()
        n += 1
        if n >= 4:
            break
    return n


async def cast_vote(player: 'Player', choice: str) -> Optional['LootRoll']:
    """Vote on the oldest open roll the player has not answered yet."""
    group = getattr(player, 'group', None)
    if not group:
        return None
    for roll in list(group.active_rolls):
        if not roll.done and player in roll.members and player.name.lower() not in roll.votes:
            await roll.vote(player, choice)
            return roll
    return None


# ---------------------------------------------------------------------------
# Graphical clients: what changed in the group, as events (party frames, invite popup)
# ---------------------------------------------------------------------------
INVITE_SECONDS = 60


async def _event(player: 'Player', event: dict):
    wm = getattr(getattr(player, 'world', None), 'web_map', None)
    if wm is None or not getattr(player, 'connection', None):
        return
    try:
        await wm.notify_event(player, event)
    except Exception:
        pass


async def broadcast(group: Optional['Group']):
    """Every member's party frames, now (joins, leaves, leader, loot mode, follow)."""
    if not group:
        return
    from map_system import build_group_block
    for member in list(group.members):
        await _event(member, {'type': 'group', 'group': build_group_block(member)})


def present_members(player: 'Player') -> List['Player']:
    """The player's group members in the room and in the realm, when at least two."""
    group = getattr(player, 'group', None)
    if not group:
        return []
    room = getattr(player, 'room', None)
    here = [m for m in group.members if getattr(m, 'room', None) is room and getattr(m, 'connection', None)]
    return here if len(here) >= 2 else []
