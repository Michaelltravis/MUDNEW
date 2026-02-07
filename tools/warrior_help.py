"""
Warrior System Help Entries
===========================
Help topics for the warrior rage and stance system.
"""

WARRIOR_HELP = {
    'warrior': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         THE WARRIOR                               ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Warriors are masters of martial combat who build {bright_red}RAGE{white} through
battle and spend it on devastating abilities. They can also switch
between {bright_yellow}STANCES{white} for different tactical advantages.{reset}

{red}⚔ RAGE SYSTEM ⚔{reset}
Rage builds during combat and decays when resting:
  • {bright_green}+5 rage{reset} per hit you deal
  • {bright_green}+10 rage{reset} per hit you receive
  • {bright_red}-5 rage{reset} per tick out of combat
  • Berserk stance: +50% rage generation!

{yellow}RAGE ABILITIES:{reset}
  {bright_cyan}ignorepain{reset} (20) - Absorb incoming damage
  {bright_cyan}warcry{reset} (30) - Fear enemies, buff allies
  {bright_cyan}rampage{reset} (40) - Attack all enemies in room
  {bright_cyan}execute{reset} (50) - Devastating finisher (more damage at low HP)

{cyan}WARRIOR COMMANDS:{reset}
  {bright_green}rage{reset}        - View rage bar and abilities
  {bright_green}stance{reset}      - View or change combat stance
  {bright_green}battleshout{reset} - Buff party's STR and CON
  {bright_green}rescue{reset}      - Save ally from combat
  {bright_green}disarm{reset}      - Knock weapon from enemy

{magenta}See also: RAGE, STANCE, EXECUTE, RAMPAGE, WARCRY, IGNOREPAIN{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'rage': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                            RAGE                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Rage is the warrior's resource, building through combat.{reset}

{yellow}HOW TO BUILD RAGE:{reset}
  • Deal damage: +5 rage per hit
  • Take damage: +10 rage per hit  
  • Berserk stance: +50% bonus to all rage gains

{yellow}HOW RAGE DECAYS:{reset}
  • Out of combat: -5 rage per tick
  • Sleeping/resting: Resets to 0

{yellow}RAGE ABILITIES:{reset}
  {bright_cyan}ignorepain{reset} (20 rage) - Level 8
  {bright_cyan}warcry{reset} (30 rage) - Level 10
  {bright_cyan}rampage{reset} (40 rage) - Level 20
  {bright_cyan}execute{reset} (50 rage) - Level 15

{yellow}USAGE:{reset}
  Type {bright_green}rage{reset} to see your current rage bar and status.

{magenta}See also: WARRIOR, STANCE, EXECUTE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'stance': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                          STANCES                                  ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Warriors can switch between combat stances for tactical advantage.{reset}

{yellow}AVAILABLE STANCES:{reset}

{white}Battle Stance{reset} (default)
  Balanced offense and defense. No bonuses or penalties.

{bright_red}Berserker Stance{reset}
  +25% damage dealt
  -20 AC (take more damage)
  +50% rage generation
  {cyan}Best for: Burning down enemies fast{reset}

{bright_blue}Defensive Stance{reset}
  -25% damage dealt
  +30 AC (take less damage)
  +25% parry chance
  {cyan}Best for: Tanking tough enemies{reset}

{bright_yellow}Precision Stance{reset}
  +4 hit bonus
  -10% damage dealt
  +15% critical strike chance (crit on 18-20)
  {cyan}Best for: Fighting evasive enemies{reset}

{yellow}USAGE:{reset}
  stance           - Show current stance and options
  stance battle    - Switch to Battle Stance
  stance berserk   - Switch to Berserker Stance
  stance defensive - Switch to Defensive Stance  
  stance precision - Switch to Precision Stance

{magenta}See also: WARRIOR, RAGE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'execute': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         EXECUTE                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}A devastating finishing attack that deals more damage the lower
your target's health.{reset}

{yellow}REQUIREMENTS:{reset}
  • Level 15
  • 50 rage
  • Must be in combat

{yellow}DAMAGE FORMULA:{reset}
  Base weapon damage × (2 + (100 - target HP%) / 20)

  At 100% target HP: 2x damage
  At 50% target HP: 4.5x damage
  At 20% target HP: 6x damage
  At 0% target HP: 7x damage!

{yellow}STRATEGY:{reset}
  Save your rage until the enemy is wounded, then execute
  for massive damage. Perfect for finishing off tough enemies.

{magenta}See also: WARRIOR, RAGE, RAMPAGE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'rampage': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         RAMPAGE                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Go on a wild rampage, attacking every enemy in the room!{reset}

{yellow}REQUIREMENTS:{reset}
  • Level 20
  • 40 rage

{yellow}EFFECTS:{reset}
  • Deals 75% weapon damage to ALL enemies in the room
  • Gain +10 rage for each target hit
  • Initiates combat with surviving enemies

{yellow}STRATEGY:{reset}
  Perfect for clearing groups of weaker enemies. The rage
  refund from hitting multiple targets can fuel your next
  ability immediately.

{magenta}See also: WARRIOR, RAGE, EXECUTE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'warcry': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         WAR CRY                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Let out a thundering war cry that terrifies enemies and
inspires allies!{reset}

{yellow}REQUIREMENTS:{reset}
  • Level 10
  • 30 rage
  • 45 second cooldown

{yellow}EFFECTS:{reset}
  {bright_red}On Enemies:{reset}
    • 50% chance to fear for 2 ticks
    • Feared enemies may flee combat
  
  {bright_green}On Allies:{reset}
    • +2 hitroll for 5 ticks
    • +1 damroll for 5 ticks

{yellow}STRATEGY:{reset}
  Use at the start of big fights to debuff enemies and
  buff your party. Great for giving your group an edge.

{magenta}See also: WARRIOR, RAGE, BATTLESHOUT{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'ignorepain': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                       IGNORE PAIN                                 ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Steel yourself against incoming damage through sheer willpower.{reset}

{yellow}REQUIREMENTS:{reset}
  • Level 8
  • 20 rage

{yellow}EFFECTS:{reset}
  • Absorb the next X damage (10 + level × 2)
  • Lasts 3 ticks or until absorption depleted
  • At level 20: Absorbs 50 damage
  • At level 40: Absorbs 90 damage

{yellow}STRATEGY:{reset}
  Use before a big hit or when health is low. Good for
  surviving boss attacks or buying time to heal.

{magenta}See also: WARRIOR, RAGE, STANCE defensive{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'battleshout': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                       BATTLE SHOUT                                ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Let out a rallying battle shout that strengthens your party.{reset}

{yellow}REQUIREMENTS:{reset}
  • Must have battleshout skill
  • 15 move points
  • 60 second cooldown

{yellow}EFFECTS:{reset}
  • +2 STR to all allies in room
  • +1 CON to all allies in room
  • Duration: 10 ticks

{yellow}STRATEGY:{reset}
  Use before combat to buff your party. The STR bonus
  increases damage, while CON gives extra HP buffer.

{magenta}See also: WARRIOR, WARCRY{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'rescue': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                          RESCUE                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Heroically rescue an ally from combat, becoming the new target.{reset}

{yellow}REQUIREMENTS:{reset}
  • Must have rescue skill
  • Target must be fighting

{yellow}USAGE:{reset}
  rescue <ally name>

{yellow}EFFECTS:{reset}
  • On success: Enemy switches to attacking you
  • Ally is freed from combat
  • Warriors gain +15 rage for the heroic act

{yellow}SUCCESS CHANCE:{reset}
  Based on your rescue skill level.

{magenta}See also: WARRIOR, DISARM{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    'disarm': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                          DISARM                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Attempt to knock your enemy's weapon from their hands.{reset}

{yellow}REQUIREMENTS:{reset}
  • Must have disarm skill
  • Must be in combat
  • Enemy must be wielding a weapon

{yellow}USAGE:{reset}
  disarm

{yellow}EFFECTS:{reset}
  • On success: Enemy's weapon falls to the ground
  • Enemy fights with bare hands (reduced damage)
  • Warriors gain +10 rage

{yellow}SUCCESS CHANCE:{reset}
  Based on disarm skill, penalized by enemy level difference.

{magenta}See also: WARRIOR, RESCUE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",
}
