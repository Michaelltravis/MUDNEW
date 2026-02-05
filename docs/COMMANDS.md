# RealmsMUD Command Reference

A complete reference of all player commands, organized by category.

> 💡 **Tip:** Most commands can be abbreviated! `n` = `north`, `l` = `look`, `i` = `inventory`

---

## 🧭 Movement

| Command | Alias | Description |
|---------|-------|-------------|
| `north` | `n` | Move north |
| `south` | `s` | Move south |
| `east` | `e` | Move east |
| `west` | `w` | Move west |
| `up` | `u` | Move up |
| `down` | `d` | Move down |
| `enter <portal>` | | Enter a portal or doorway |
| `leave` | | Leave current area |
| `recall` | `rec` | Teleport to the temple (emergency) |
| `follow <player>` | | Follow another player |
| `group <player>` | | Form/join a group |
| `flee` | `fl` | Escape from combat (costs XP) |

---

## 👁️ Information & Looking

| Command | Alias | Description |
|---------|-------|-------------|
| `look` | `l` | Look at the current room |
| `look <target>` | | Look at a person, mob, or item |
| `examine <item>` | `ex` | Get detailed info about an item |
| `exits` | | List available exits |
| `score` | `sc` | View your character stats |
| `inventory` | `i` | List items you're carrying |
| `equipment` | `eq` | Show equipped items |
| `who` | `wh` | List online players |
| `where` | `whe` | Find players/mobs in the zone |
| `consider <mob>` | `con` | Gauge enemy difficulty |
| `time` | | Show in-game time |
| `weather` | | Check current weather |
| `map` | `zones` | View the world map |
| `minimap` | `mm` | Toggle ASCII minimap display |
| `scan` | | Look in all directions |

---

## ⚔️ Combat

### Basic Combat

| Command | Alias | Description |
|---------|-------|-------------|
| `kill <target>` | `k` | Attack a target |
| `flee` | `fl` | Attempt to escape |
| `assist <player>` | | Join combat helping an ally |
| `consider <mob>` | `con` | Check if you can win |

### Combat Skills

| Command | Alias | Class | Description |
|---------|-------|-------|-------------|
| `kick` | | All | Basic kick attack |
| `bash` | | War/Pal | Shield bash, can stun |
| `backstab <target>` | | Thi/Ass | Sneak attack from behind |
| `rescue <ally>` | `resc` | War/Pal | Pull enemy off an ally |
| `disarm` | | Warrior | Knock weapon from enemy |
| `trip` | | Thief | Trip enemy, causing fall |
| `circle` | | Thief | Circle behind for extra damage |

### Class-Specific Combat Commands

**Warriors:**
| Command | Alias | Description |
|---------|-------|-------------|
| `execute` | `exec` | Massive damage to low-HP enemies |
| `rampage` | `ramp` | Bonus damage after kills |
| `warcry` | `wc` | Buff yourself and allies |
| `battleshout` | `bs` | Group damage buff |
| `stance <type>` | | Change stance (battle/berserk/defensive/precision) |

**Thieves:**
| Command | Alias | Description |
|---------|-------|-------------|
| `combo` | `cp` | Check your combo points |
| `eviscerate` | `evis` | Finishing move (1+ combo) |
| `kidneyshot` | `ks` | Stun finisher (4+ combo) |
| `slicedice` | `snd` | Multi-hit finisher (3+ combo) |

**Paladins:**
| Command | Alias | Description |
|---------|-------|-------------|
| `smite` | `sm` | Holy damage attack |
| `layhands` | `loh` | Emergency self-heal |
| `aura <type>` | | Set aura (devotion/protection/retribution) |

**Clerics:**
| Command | Alias | Description |
|---------|-------|-------------|
| `turnundead` | `turn` | Damage/fear undead enemies |
| `holysmite` | `hs` | Spend Divine Favor for damage |
| `divinefavor` | `df` | Check Divine Favor points |

**Rangers:**
| Command | Alias | Description |
|---------|-------|-------------|
| `track <target>` | `tr` | Find a creature's direction |
| `ambush` | `amb` | Attack from hiding |
| `camouflage` | `camo` | Blend into surroundings |
| `tame <animal>` | | Tame an animal companion |

**Necromancers:**
| Command | Alias | Description |
|---------|-------|-------------|
| `raise <type>` | `undead` | Raise undead (warrior/healer/caster/rogue) |
| `soulstone` | `stone` | Use soulstone abilities |

**Bards:**
| Command | Alias | Description |
|---------|-------|-------------|
| `perform <song>` | `sing` | Perform a magical song |
| `encore` | `enc` | Extend current song |
| `countersong` | `cs` | Counter enemy magic |
| `fascinate` | `fasc` | Mesmerize enemies |

**Assassins:**
| Command | Alias | Description |
|---------|-------|-------------|
| `assassinate` | | Instant kill attempt |
| `envenom` | | Poison your weapon |
| `garrote` | | Silence and damage |
| `shadowstep` | `ss` | Teleport behind target |

---

## ✨ Magic & Spells

| Command | Alias | Description |
|---------|-------|-------------|
| `cast <spell>` | `c` | Cast a spell on yourself |
| `cast <spell> <target>` | | Cast a spell on a target |
| `spells` | | List known spells |
| `spells <school>` | | List spells by school |

### Example Spells

```bash
# Offensive
cast fireball goblin
cast lightning_bolt orc
cast magic_missile rat

# Healing
cast cure_light              # Heal yourself
cast cure_serious thorin     # Heal a friend
cast group_heal              # Heal your party

# Buffs
cast armor                   # Magical armor
cast bless                   # Combat bonuses
cast sanctuary               # Damage reduction
cast haste                   # Speed boost
cast invisibility            # Turn invisible

# Utility
cast teleport midgaard       # Travel instantly
cast identify sword          # Learn item properties
cast word_of_recall          # Return to temple
```

---

## 🎒 Items & Equipment

### Picking Up & Dropping

| Command | Alias | Description |
|---------|-------|-------------|
| `get <item>` | `ge` | Pick up an item |
| `get all` | | Pick up everything |
| `get <item> <container>` | | Get from container |
| `drop <item>` | `dp` | Drop an item |
| `put <item> <container>` | `pu` | Put item in container |

### Using Equipment

| Command | Alias | Description |
|---------|-------|-------------|
| `wear <item>` | `we` | Wear armor/clothing |
| `wield <item>` | `wi` | Wield a weapon |
| `hold <item>` | `ho` | Hold an item |
| `remove <item>` | `rem` | Remove worn equipment |
| `equipment` | `eq` | See what you're wearing |

### Other Item Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `give <item> <player>` | `gi` | Give item to someone |
| `eat <food>` | `ea` | Eat food |
| `drink <container>` | `dr` | Drink from a container |
| `quaff <potion>` | | Drink a potion |
| `read <item>` | `rd` | Read a scroll or book |
| `use <item>` | | Use an item's special ability |

---

## 💬 Communication

| Command | Alias | Description |
|---------|-------|-------------|
| `say <message>` | `'` | Speak to the room |
| `shout <message>` | | Shout to the zone |
| `gossip <message>` | | Global chat channel |
| `tell <player> <msg>` | | Private message |
| `reply <message>` | | Reply to last tell |
| `gtell <message>` | `gt` | Message your group |
| `emote <action>` | `:` | Roleplay action |

### Example Communication

```bash
say Hello, fellow adventurers!
> You say, "Hello, fellow adventurers!"

emote waves cheerfully.
> Thorin waves cheerfully.

tell gandalf Need help with a quest!
> You tell Gandalf, "Need help with a quest!"

gossip Anyone want to group for Dragon's Domain?
> [Gossip] Thorin: Anyone want to group for Dragon's Domain?
```

---

## 📋 Quests & Journal

| Command | Alias | Description |
|---------|-------|-------------|
| `quest list` | | See available quests nearby |
| `quest accept <id>` | | Accept a quest |
| `quest log` | | View active quests |
| `quest info <id>` | | Quest details |
| `quest abandon <id>` | | Abandon a quest |
| `talk <npc>` | | Talk to an NPC |
| `journal` | `jr` | View your adventure journal |
| `journal add <note>` | | Add a journal entry |

---

## 🔨 Crafting & Gathering

| Command | Alias | Description |
|---------|-------|-------------|
| `craft list` | | List known recipes |
| `craft <recipe>` | | Craft an item |
| `gather` | | Gather nearby resources |
| `mine` | | Mine ore deposits |
| `skin <corpse>` | | Skin a creature |
| `forage` | | Search for herbs |

---

## 📚 Skills & Abilities

| Command | Alias | Description |
|---------|-------|-------------|
| `skills` | | View your skills |
| `spells` | | View your spells |
| `practice` | `pr` | Practice at a guildmaster |
| `talents` | | View talent trees |
| `talent learn <id>` | | Learn a talent |
| `lore <target>` | `lo` | Use lore skill on target |

---

## 👥 Groups & Social

| Command | Alias | Description |
|---------|-------|-------------|
| `group <player>` | | Invite to / join group |
| `group` | | View group members |
| `follow <player>` | | Follow someone |
| `unfollow` | | Stop following |
| `companion` | `pet` | View your companions |
| `dismiss` | | Dismiss a companion |

---

## 🛒 Shops & Trading

| Command | Description |
|---------|-------------|
| `list` | See shop inventory |
| `buy <item>` | Purchase an item |
| `sell <item>` | Sell an item |
| `value <item>` | Check sell price |
| `repair <item>` | Repair damaged equipment |

---

## 🛏️ Resting & Recovery

| Command | Alias | Description |
|---------|-------|-------------|
| `sit` | | Sit down |
| `rest` | `re` | Rest (faster regen) |
| `sleep` | `sl` | Sleep (fastest regen) |
| `wake` | `wa` | Wake up |
| `stand` | `st` | Stand up |

> 💡 Resting at an inn builds up Rested XP for bonus experience!

---

## ⚙️ Character & Settings

| Command | Alias | Description |
|---------|-------|-------------|
| `save` | | Save your character |
| `quit` | `q` | Leave the game |
| `password` | | Change password |
| `title <text>` | | Set your title |
| `description` | | Set your description |
| `alias <name> <cmd>` | | Create command shortcut |
| `autocombat` | | Toggle automatic combat |
| `brief` | | Toggle brief room descriptions |
| `compact` | | Toggle compact mode |
| `color` | | Toggle color |
| `tips` | | Toggle game tips |

---

## 🔧 Utility

| Command | Alias | Description |
|---------|-------|-------------|
| `help` | `h`, `?` | Get help |
| `help <topic>` | | Help on specific topic |
| `commands` | | List all commands |
| `time` | | In-game time |
| `date` | | In-game date |
| `version` | | Server version |
| `bug <report>` | | Report a bug |
| `idea <suggestion>` | | Submit an idea |
| `typo <report>` | | Report a typo |

---

## 🔒 Doors & Locks

| Command | Alias | Description |
|---------|-------|-------------|
| `open <door>` | `op` | Open a door |
| `close <door>` | `cl` | Close a door |
| `lock <door>` | | Lock a door |
| `unlock <door>` | | Unlock a door |
| `pick <door>` | | Pick a lock (Thief) |
| `knock <door>` | | Knock on a door |

---

## 🎮 Advanced Features

| Command | Alias | Description |
|---------|-------|-------------|
| `achievements` | | View your achievements |
| `reputation` | `rep` | Check faction reputation |
| `newgameplus` | `newgame+` | Start New Game+ mode |
| `search` | `se` | Search for hidden things |
| `detect` | | Use detection abilities |

---

## Quick Reference Card

```
MOVEMENT        COMBAT          ITEMS           CHAT
─────────────   ─────────────   ─────────────   ─────────────
n/s/e/w/u/d     kill <mob>      get <item>      say <msg>
look (l)        flee            drop <item>     tell <p> <msg>
recall          kick            wear <item>     gossip <msg>
map             cast <spell>    wield <item>    emote <action>

INFO            SKILLS          QUESTS          OTHER
─────────────   ─────────────   ─────────────   ─────────────
score (sc)      skills          quest list      save
inventory (i)   spells          quest accept    quit
equipment (eq)  practice        quest log       help
who             talents         talk <npc>      rest/sleep
```

---

Need more help? Type `help <command>` in-game for detailed information about any command!
