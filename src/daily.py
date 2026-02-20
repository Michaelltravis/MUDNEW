"""
Daily Login Bonus System for Misthollow

Rewards players for logging in daily with progressive bonuses.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

logger = logging.getLogger(__name__)


# Daily bonus rewards by streak day
DAILY_REWARDS = {
    1: {'gold': 50, 'xp': 100, 'message': 'Welcome back!'},
    2: {'gold': 75, 'xp': 150, 'message': 'Day 2 - Keep it up!'},
    3: {'gold': 100, 'xp': 200, 'message': 'Day 3 - Building momentum!'},
    4: {'gold': 125, 'xp': 250, 'message': 'Day 4 - Consistency pays off!'},
    5: {'gold': 150, 'xp': 300, 'message': 'Day 5 - Halfway through the week!'},
    6: {'gold': 200, 'xp': 400, 'message': 'Day 6 - Almost there!'},
    7: {'gold': 500, 'xp': 1000, 'message': '🎉 WEEKLY BONUS! Full week complete!'},
}

# Bonus items at certain milestones (one-time per character)
MILESTONE_REWARDS = {
    7: {'item_vnum': 3134, 'item_name': 'Potion of Greater Healing'},  # First week
    14: {'item_vnum': 3135, 'item_name': 'Potion of Greater Mana'},    # Second week
    30: {'item_vnum': 3138, 'item_name': 'Golden Key'},                # First month
}


class DailyBonusManager:
    """Manages daily login bonuses."""
    
    @classmethod
    async def check_daily_bonus(cls, player: 'Player') -> bool:
        """
        Check and award daily login bonus if eligible.
        Call this when player logs in.
        
        Returns True if bonus was awarded.
        """
        now = datetime.now()
        today = now.date()
        
        # Initialize daily bonus data if needed
        if not hasattr(player, 'daily_bonus'):
            player.daily_bonus = {
                'last_claim': None,
                'streak': 0,
                'total_days': 0,
                'milestones_claimed': [],
            }
        
        daily = player.daily_bonus
        
        # Parse last claim date
        last_claim = None
        if daily.get('last_claim'):
            try:
                last_claim = datetime.fromisoformat(daily['last_claim']).date()
            except (ValueError, TypeError):
                pass
        
        # Already claimed today?
        if last_claim == today:
            return False
        
        # Check if streak continues (claimed yesterday) or resets
        yesterday = today - timedelta(days=1)
        if last_claim == yesterday:
            # Streak continues
            daily['streak'] = daily.get('streak', 0) + 1
        else:
            # Streak reset
            if last_claim and (today - last_claim).days > 1:
                # Inform about broken streak
                c = player.config.COLORS
                old_streak = daily.get('streak', 0)
                if old_streak >= 3:
                    await player.send(f"\n{c['yellow']}Your {old_streak}-day login streak has been reset.{c['reset']}")
            daily['streak'] = 1
        
        # Cap streak for reward lookup (cycles weekly)
        streak_day = ((daily['streak'] - 1) % 7) + 1  # 1-7 cycling
        daily['total_days'] = daily.get('total_days', 0) + 1
        daily['last_claim'] = now.isoformat()
        
        # Get rewards for this day
        rewards = DAILY_REWARDS.get(streak_day, DAILY_REWARDS[1])
        
        c = player.config.COLORS
        
        # Display bonus notification
        await player.send(f"\n{c['bright_yellow']}╔══════════════════════════════════════╗{c['reset']}")
        await player.send(f"{c['bright_yellow']}║      🌟 DAILY LOGIN BONUS 🌟        ║{c['reset']}")
        await player.send(f"{c['bright_yellow']}╠══════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['bright_yellow']}║{c['white']} {rewards['message']:^36} {c['bright_yellow']}║{c['reset']}")
        await player.send(f"{c['bright_yellow']}╠══════════════════════════════════════╣{c['reset']}")
        
        # Award gold
        gold = rewards.get('gold', 0)
        if gold > 0:
            player.gold += gold
            await player.send(f"{c['bright_yellow']}║  {c['yellow']}+{gold} gold{' ' * (28 - len(str(gold)))}{c['bright_yellow']}║{c['reset']}")
        
        # Award XP
        xp = rewards.get('xp', 0)
        if xp > 0:
            await player.gain_exp(xp, source='daily')
            await player.send(f"{c['bright_yellow']}║  {c['bright_green']}+{xp} experience{' ' * (22 - len(str(xp)))}{c['bright_yellow']}║{c['reset']}")
        
        # Check for milestone rewards
        total = daily['total_days']
        milestones = daily.get('milestones_claimed', [])
        
        for milestone_day, milestone_reward in MILESTONE_REWARDS.items():
            if total >= milestone_day and milestone_day not in milestones:
                # Award milestone item
                try:
                    item = player.world.create_object(milestone_reward['item_vnum'])
                    if item:
                        player.inventory.append(item)
                        milestones.append(milestone_day)
                        await player.send(f"{c['bright_yellow']}║  {c['bright_cyan']}🎁 MILESTONE: {milestone_reward['item_name'][:18]:<18}{c['bright_yellow']}║{c['reset']}")
                except Exception as e:
                    logger.warning(f"Failed to give milestone reward: {e}")
        
        daily['milestones_claimed'] = milestones
        
        await player.send(f"{c['bright_yellow']}╠══════════════════════════════════════╣{c['reset']}")
        await player.send(f"{c['bright_yellow']}║  {c['white']}Streak: {daily['streak']:>3} days   Total: {total:>4} days {c['bright_yellow']}║{c['reset']}")
        await player.send(f"{c['bright_yellow']}╚══════════════════════════════════════╝{c['reset']}\n")
        
        # Save player
        await player.save()
        
        logger.info(f"Daily bonus awarded to {player.name}: streak={daily['streak']}, total={total}")
        return True
    
    @classmethod
    async def show_daily_status(cls, player: 'Player') -> None:
        """Show daily bonus status to player."""
        c = player.config.COLORS
        
        if not hasattr(player, 'daily_bonus'):
            player.daily_bonus = {
                'last_claim': None,
                'streak': 0,
                'total_days': 0,
                'milestones_claimed': [],
            }
        
        daily = player.daily_bonus
        now = datetime.now()
        today = now.date()
        
        # Check if already claimed
        claimed_today = False
        if daily.get('last_claim'):
            try:
                last_claim = datetime.fromisoformat(daily['last_claim']).date()
                claimed_today = (last_claim == today)
            except (ValueError, TypeError):
                pass
        
        streak = daily.get('streak', 0)
        total = daily.get('total_days', 0)
        
        await player.send(f"\n{c['bright_cyan']}═══════════════════════════════════════{c['reset']}")
        await player.send(f"{c['bright_yellow']}        🌟 Daily Login Status 🌟{c['reset']}")
        await player.send(f"{c['bright_cyan']}═══════════════════════════════════════{c['reset']}")
        
        if claimed_today:
            await player.send(f"{c['bright_green']}✓ Today's bonus claimed!{c['reset']}")
        else:
            await player.send(f"{c['yellow']}○ Bonus available! (awarded on login){c['reset']}")
        
        await player.send(f"\n{c['white']}Current streak: {c['bright_yellow']}{streak} days{c['reset']}")
        await player.send(f"{c['white']}Total logins:   {c['bright_cyan']}{total} days{c['reset']}")
        
        # Show this week's progress
        streak_day = ((streak - 1) % 7) + 1 if streak > 0 else 0
        await player.send(f"\n{c['white']}Weekly progress:{c['reset']}")
        
        week_display = ""
        for i in range(1, 8):
            if i <= streak_day and claimed_today:
                week_display += f"{c['bright_green']}★ "
            elif i < streak_day or (i == streak_day and not claimed_today):
                week_display += f"{c['bright_green']}★ "
            else:
                week_display += f"{c['bright_black']}☆ "
        
        await player.send(f"  {week_display}{c['reset']}")
        await player.send(f"  {c['bright_black']}M  T  W  T  F  S  S{c['reset']}")
        
        # Next milestone
        unclaimed = [m for m in sorted(MILESTONE_REWARDS.keys()) 
                     if m not in daily.get('milestones_claimed', [])]
        if unclaimed:
            next_milestone = unclaimed[0]
            days_left = next_milestone - total
            if days_left > 0:
                await player.send(f"\n{c['white']}Next milestone: {c['bright_cyan']}{days_left} days{c['reset']} until day {next_milestone} reward")
        
        await player.send(f"{c['bright_cyan']}═══════════════════════════════════════{c['reset']}\n")
