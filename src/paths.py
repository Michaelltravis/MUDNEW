"""The Path system: Lone Wolf vs Fellowship.

Every character may walk one of two paths:

  LONE WOLF   - bonuses only while UNGROUPED: damage reduction, lifesteal,
                and mastery of consumables. The self-sufficient road: with
                strategy and a full satchel, nothing in the realm is beyond
                a lone hunter - but groups gain nothing from them.

  FELLOWSHIP  - bonuses only while GROUPED: extra experience on top of the
                group bonus and coordinated strikes against shared targets.
                Solo, a fellowship character has no edge at all.

The first choice is free (`path lone_wolf` / `path fellowship`).
Switching requires completing the Trial of Unlearning, a repeatable
quest from Sage Aldric that scales with your level.
"""
import logging

logger = logging.getLogger('Misthollow.Paths')

PATHS = {
    'lone_wolf': {
        'name': 'Lone Wolf',
        'icon': '🐺',
        'description': 'Walk alone. Gain damage reduction, lifesteal and consumable '
                       'mastery while ungrouped. Grants nothing in a group.',
    },
    'fellowship': {
        'name': 'Fellowship',
        'icon': '🤝',
        'description': 'Strength in numbers. Gain bonus experience and coordinated '
                       'strikes while grouped. Grants nothing alone.',
    },
}


class PathManager:

    @staticmethod
    def get_path(player):
        return getattr(player, 'path', None)

    @staticmethod
    def lone_wolf_active(player) -> bool:
        return (getattr(player, 'path', None) == 'lone_wolf'
                and not getattr(player, 'group', None))

    @staticmethod
    def fellowship_active(player) -> bool:
        return (getattr(player, 'path', None) == 'fellowship'
                and getattr(player, 'group', None) is not None)

    # ----- Lone Wolf numbers (level-scaled, capped) -----
    @staticmethod
    def damage_reduction(player) -> float:
        """8% base, +2% per 10 levels, cap 20%."""
        lvl = getattr(player, 'level', 1)
        return min(0.20, 0.08 + (lvl // 10) * 0.02)

    @staticmethod
    def lifesteal(player) -> float:
        """4% base, +2% per 15 levels, cap 12%."""
        lvl = getattr(player, 'level', 1)
        return min(0.12, 0.04 + (lvl // 15) * 0.02)

    # ----- Fellowship numbers -----
    FELLOWSHIP_XP_BONUS = 0.15
    COORDINATED_DAMAGE_BONUS = 0.10

    @staticmethod
    def coordinated(attacker, defender) -> bool:
        """A groupmate in the room is fighting the same target."""
        group = getattr(attacker, 'group', None)
        room = getattr(attacker, 'room', None)
        if not group or not room:
            return False
        for member in getattr(group, 'members', []):
            if member is attacker:
                continue
            if getattr(member, 'room', None) is room and getattr(member, 'fighting', None) is defender:
                return True
        return False

    # ----- combat hooks -----
    @classmethod
    def modify_damage(cls, attacker, defender, damage: int) -> int:
        """Called once per landed hit, after all other modifiers."""
        try:
            # fellowship: coordinated strikes on shared targets
            if (hasattr(attacker, 'connection') and cls.fellowship_active(attacker)
                    and cls.coordinated(attacker, defender)):
                damage = int(damage * (1.0 + cls.COORDINATED_DAMAGE_BONUS))
            # lone wolf: the wolf shrugs off the blow
            if hasattr(defender, 'connection') and cls.lone_wolf_active(defender):
                damage = int(damage * (1.0 - cls.damage_reduction(defender)))
        except Exception as e:
            logger.debug(f"path modify_damage: {e}")
        return max(1, damage)

    @classmethod
    async def after_damage(cls, attacker, defender, damage: int):
        """Lone wolf lifesteal on hits the wolf lands."""
        try:
            if hasattr(attacker, 'connection') and cls.lone_wolf_active(attacker):
                heal = int(damage * cls.lifesteal(attacker))
                if heal > 0 and attacker.hp < attacker.max_hp:
                    attacker.hp = min(attacker.max_hp, attacker.hp + heal)
        except Exception as e:
            logger.debug(f"path after_damage: {e}")

    @classmethod
    async def after_quaff(cls, player):
        """Lone wolf consumable mastery: every potion restores extra."""
        try:
            if not cls.lone_wolf_active(player):
                return
            bonus_hp = int(getattr(player, 'max_hp', 0) * 0.08)
            bonus_mana = int(getattr(player, 'max_mana', 0) * 0.08)
            player.hp = min(player.max_hp, player.hp + bonus_hp)
            if hasattr(player, 'mana'):
                player.mana = min(player.max_mana, player.mana + bonus_mana)
            c = player.config.COLORS
            await player.send(f"{c['cyan']}Your lone wolf field mastery wrings extra potency from it. "
                              f"(+{bonus_hp} hp, +{bonus_mana} mana){c['reset']}")
        except Exception as e:
            logger.debug(f"path after_quaff: {e}")

    @classmethod
    def xp_bonus(cls, player) -> float:
        """Fellowship: extra xp multiplier while grouped."""
        return 1.0 + cls.FELLOWSHIP_XP_BONUS if cls.fellowship_active(player) else 1.0

    # ----- the path command -----
    @classmethod
    async def cmd_path(cls, player, args):
        c = player.config.COLORS
        current = getattr(player, 'path', None)
        if not args:
            await player.send(f"\r\n{c['bright_yellow']}═══ THE TWO PATHS ═══{c['reset']}")
            for pid, p in PATHS.items():
                marker = f" {c['bright_green']}◄ your path{c['reset']}" if current == pid else ''
                await player.send(f"{c['bright_white']}{p['icon']} {p['name']}{c['reset']}{marker}")
                await player.send(f"   {c['white']}{p['description']}{c['reset']}")
            if not current:
                await player.send(f"\r\n{c['yellow']}Choose with: path lone_wolf  |  path fellowship{c['reset']}")
                await player.send(f"{c['white']}Your first choice is free. Changing later requires the "
                                  f"Trial of Unlearning (ask Sage Aldric in the temple).{c['reset']}")
            elif getattr(player, 'path_switch_available', False):
                await player.send(f"\r\n{c['bright_green']}The Trial has cleansed you - you may choose anew.{c['reset']}")
            return

        choice = args[0].lower().replace('lonewolf', 'lone_wolf')
        if choice not in PATHS:
            await player.send(f"{c['red']}Unknown path. Choose lone_wolf or fellowship.{c['reset']}")
            return
        if current == choice:
            await player.send(f"{c['yellow']}You already walk the {PATHS[choice]['name']} path.{c['reset']}")
            return
        if current and not getattr(player, 'path_switch_available', False):
            await player.send(f"{c['red']}Your path is set. Complete the Trial of Unlearning "
                              f"(Sage Aldric, the Temple of Midgaard) to walk a different one.{c['reset']}")
            return
        player.path = choice
        if current:
            player.path_switch_available = False
        p = PATHS[choice]
        await player.send(f"\r\n{c['bright_yellow']}{p['icon']} You now walk the path of the "
                          f"{p['name'].upper()}.{c['reset']}")
        await player.send(f"{c['white']}{p['description']}{c['reset']}")
