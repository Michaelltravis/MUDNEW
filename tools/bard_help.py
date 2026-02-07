"""
Bard System Help Entries
========================
Help topics for the bard performance system.
"""

BARD_HELP = {
    # Main bard topic
    'bard': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                          THE BARD                                 ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Bards are charismatic performers who inspire allies and debilitate
enemies through the power of music. Unlike other casters, bards
use {bright_magenta}songs{white} - ongoing performances that provide continuous effects.{reset}

{yellow}♪ PERFORMANCE SYSTEM ♪{reset}
Bards channel songs as performances that last until stopped, the
bard runs out of mana, moves, or is interrupted. While performing:
  • Song effects apply to all allies or enemies in the room
  • Mana drains each tick (every few seconds)
  • You can still fight (singing while swinging!)
  • You cannot cast spells (your voice is busy)
  • Moving to another room ends the performance
  • Taking damage may interrupt your song

{cyan}BARD COMMANDS:{reset}
  {bright_green}songs{reset}      - View your known songs and current status
  {bright_green}perform{reset}    - Start performing a song (also: sing, play)
  {bright_green}stop{reset}       - End your current performance
  {bright_green}encore{reset}     - Double your song's power for 3 ticks (cooldown)
  {bright_green}countersong{reset} - Dispel magical effects on allies/enemies
  {bright_green}fascinate{reset}  - Charm an enemy into passivity
  {bright_green}mock{reset}       - Taunt and debuff an enemy with psychic damage

{cyan}SONG TYPES:{reset}
  {bright_yellow}Combat Songs{reset} - Buff allies or debuff enemies in battle
  {bright_yellow}Support Songs{reset} - Healing, regeneration, and utility effects
  {bright_yellow}Ultimate Songs{reset} - Devastating effects (high level)

{magenta}See also: SONGS, PERFORM, ENCORE, COUNTERSONG, FASCINATE, MOCK{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Songs list
    'songs': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                        BARD SONGS                                 ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Type {bright_green}songs{white} in-game to see songs available at your level.{reset}

{yellow}═══ COMBAT SONGS ═══{reset}
{bright_cyan}Song of Courage{reset} (Level 1) - 3 mana/tick
  +2 hitroll, +1 damroll to all allies in the room.
  Your allies fight with renewed vigor!

{bright_cyan}Battle Hymn{reset} (Level 10) - 4 mana/tick
  Haste effect + hitroll bonus to allies.
  Drives your party into a fighting frenzy!

{bright_cyan}Dirge of Doom{reset} (Level 15) - 4 mana/tick
  -2 hitroll, -1 damroll, -1 saves to all enemies.
  Your mournful melody saps enemy will to fight.

{bright_cyan}Discordant Note{reset} (Level 25) - 5 mana/tick
  Enemies have 20% chance to fumble attacks.
  Jarring notes throw enemies off balance.

{yellow}═══ SUPPORT SONGS ═══{reset}
{bright_cyan}Song of Rest{reset} (Level 3) - 2 mana/tick
  +50% HP/mana/move regeneration to allies.
  {red}Only works out of combat!{reset}

{bright_cyan}Lullaby{reset} (Level 12) - 5 mana/tick
  Cumulative sleep chance on enemies each tick.
  Keep singing to increase the chance!

{bright_cyan}Inspiring Ballad{reset} (Level 20) - 4 mana/tick
  +1 to all stats, +10% XP gain for allies.
  Tales of legendary heroes inspire your party!

{yellow}═══ ULTIMATE SONG ═══{reset}
{bright_red}Symphony of Destruction{reset} (Level 35) - 8 mana/tick
  2d6 sonic damage per tick to all enemies.
  15% chance to deafen targets each tick.

{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Perform command
    'perform': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         PERFORM                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Start performing a bard song.{reset}

{yellow}USAGE:{reset}
  perform <song name>
  sing <song name>
  play <song name>

{yellow}EXAMPLES:{reset}
  perform courage        - Start Song of Courage
  sing battle            - Start Battle Hymn
  perform destruction    - Start Symphony of Destruction

{yellow}NOTES:{reset}
  • Songs drain mana each tick while active
  • Moving to another room ends your performance
  • You can switch songs by performing a new one
  • Type {bright_green}stop{reset} to end your performance
  • Type {bright_green}songs{reset} to see available songs

{magenta}See also: SONGS, STOP, ENCORE, BARD{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Encore command
    'encore': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                          ENCORE                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Double the power of your current song for 3 ticks!{reset}

{yellow}USAGE:{reset}
  encore

{yellow}REQUIREMENTS:{reset}
  • Must be performing a song
  • Costs 30 mana
  • 60 second cooldown

{yellow}EFFECTS:{reset}
  • All song effects are doubled for 3 ticks
  • Mana cost per tick is also doubled
  • Stacks with song proficiency

{yellow}STRATEGY:{reset}
  Use encore during critical moments:
  • Boss fights when allies need extra power
  • When enemies are close to falling asleep (lullaby)
  • To maximize Symphony of Destruction damage

{magenta}See also: PERFORM, SONGS, BARD{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Countersong command
    'countersong': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                       COUNTERSONG                                 ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Use your music to disrupt and dispel magical effects.{reset}

{yellow}USAGE:{reset}
  countersong

{yellow}REQUIREMENTS:{reset}
  • Must have the countersong skill
  • Costs 25 mana
  • 30 second cooldown

{yellow}EFFECTS:{reset}
  {bright_green}On Allies:{reset} Removes debuffs (poison, blindness, curse, etc.)
  {bright_red}On Enemies:{reset} Removes buffs (haste, bless, armor, etc.)

{yellow}SUCCESS CHANCE:{reset}
  • Based on your countersong skill level
  • Ally debuff removal: full skill %
  • Enemy buff removal: half skill %

{magenta}See also: BARD, SONGS{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Fascinate command
    'fascinate': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                        FASCINATE                                  ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Charm an enemy with your captivating melody.{reset}

{yellow}USAGE:{reset}
  fascinate <target>

{yellow}REQUIREMENTS:{reset}
  • Must have the fascinate skill
  • Costs 20 mana
  • Target cannot be in combat

{yellow}EFFECTS:{reset}
  • Target becomes charmed and passive
  • Duration: 3-5 ticks (based on level)
  • Effect breaks if target takes damage

{yellow}STRATEGY:{reset}
  • Use to neutralize a dangerous enemy before a fight
  • Great for crowd control in multi-mob encounters
  • Works best on non-aggressive targets

{magenta}See also: BARD, MOCK{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Mock command
    'mock': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                         MOCKERY                                   ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}Hurl vicious mockery at an enemy, dealing psychic damage and
debuffing their combat ability.{reset}

{yellow}USAGE:{reset}
  mock <target>

{yellow}REQUIREMENTS:{reset}
  • Must have the mockery skill
  • Costs 10 mana

{yellow}EFFECTS:{reset}
  • Deals 1d4 + level/5 psychic damage
  • On successful skill check: -2 hitroll for 2-4 ticks
  • Initiates combat if not already fighting

{yellow}FLAVOR:{reset}
  Your bard hurls creative insults like:
  "Your mother was a hamster and your father smelt of elderberries!"
  "I've seen scarier things in a goblin's lunchbox!"

{magenta}See also: BARD, FASCINATE{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",

    # Song of Courage
    'song of courage': """
{cyan}╔══════════════════════════════════════════════════════════════════╗
║                     SONG OF COURAGE                               ║
╠══════════════════════════════════════════════════════════════════╣{reset}
{white}A stirring melody that fills allies with valor and fighting spirit.{reset}

{yellow}Level Required:{reset} 1
{yellow}Mana Cost:{reset} 3 per tick

{yellow}EFFECTS:{reset}
  +2 Hitroll to all allies in the room
  +1 Damroll to all allies in the room

{yellow}USAGE:{reset}
  perform courage

{bright_magenta}"♪ Your song of courage fills your allies with valor! ♪"{reset}

{magenta}See also: SONGS, PERFORM, BARD{reset}
{cyan}╚══════════════════════════════════════════════════════════════════╝{reset}
""",
}
