# RealmsMUD

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ███████╗ █████╗ ██╗     ███╗   ███╗███████╗         ║
    ║   ██╔══██╗██╔════╝██╔══██╗██║     ████╗ ████║██╔════╝         ║
    ║   ██████╔╝█████╗  ███████║██║     ██╔████╔██║███████╗         ║
    ║   ██╔══██╗██╔══╝  ██╔══██║██║     ██║╚██╔╝██║╚════██║         ║
    ║   ██║  ██║███████╗██║  ██║███████╗██║ ╚═╝ ██║███████║         ║
    ║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝         ║
    ║                       MUD                                     ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

**A Modern Fantasy Multi-User Dungeon**

RealmsMUD is a feature-rich text-based multiplayer RPG inspired by classic MUDs like CircleMUD and DikuMUD, built from the ground up in Python 3. Dive into a rich fantasy world with friends, battle monsters, cast spells, and become a legend.

---

## 🎮 Features

### Character System
- **7 Playable Races**: Human, Elf, Dwarf, Halfling, Half-Orc, Gnome, Dark Elf
- **9 Character Classes**: Warrior, Mage, Cleric, Thief, Ranger, Paladin, Necromancer, Bard, Assassin
- **Deep Talent Trees**: 3 specialization trees per class with 40+ talents each
- **6 Core Stats**: Strength, Intelligence, Wisdom, Dexterity, Constitution, Charisma

### Combat
- Real-time combat with 4-second attack rounds
- Class-specific mechanics (Rage, Combo Points, Divine Favor, Songs, etc.)
- 50+ combat skills and abilities
- Boss encounters with special mechanics and loot tables
- Equipment set bonuses

### Magic System
- **100+ Spells** across multiple schools
- Offensive: Fireball, Lightning Bolt, Meteor Swarm, Chain Lightning
- Healing: Cure Light through Group Heal, Resurrection
- Buffs & Debuffs: Sanctuary, Haste, Sleep, Fear, Curse
- Utility: Teleport, Identify, Word of Recall
- Bard Songs: Battle Hymn, Song of Rest, Dirge of Doom

### World
- **40 Unique Zones** with 2,494 rooms to explore:
  - City of Midgaard (starting city)
  - Newbie Training Zone (levels 1-7)
  - Haon Dor Forest (Light & Dark)
  - Mines of Moria, Dwarven Kingdom
  - The Great Pyramid, City of Thalos
  - High Tower of Magic
  - Sewers (3 levels), Haunted Swamp
  - Castle Apocalypse (endgame)
  - And many more!
- Dynamic day/night cycle with weather
- Quest system with 9-part tutorial
- Stealth & detection mechanics

### Pet & Companion System
- Rangers can tame wild animals
- Necromancers animate undead servants
- Pet commands: follow, stay, attack, assist

### Social Features
- Account system with multiple characters
- Group/party system with auto-follow
- 344 commands available
- Multiple chat channels (Say, Shout, Gossip, Tell, Group)
- Emotes for roleplay

### Modern Conveniences
- **Web Client** (browser-based, no download required)
- **Live World Map** in browser
- **Vitals Bar**: Real-time HP/Mana/Move display
- 500+ searchable help topics
- Journal for tracking adventures
- New Game+ mode for replayability

---

## 🚀 Quick Start

### Requirements
- Python 3.8 or higher
- No external dependencies required!

### Running the Server

```bash
# Start the server
cd src && python3 main.py
```

The server starts on multiple ports:
- **4000** - Telnet (MUD clients)
- **4001** - Web Map
- **4003** - Web Client

### Connecting

**Web Client (Recommended):**
```
http://your-server-ip:4003
```

**Telnet/MUD Client:**
```bash
telnet your-server-ip 4000
```

**Recommended MUD Clients:**
- [Mudlet](https://www.mudlet.org/) (Free, cross-platform)
- [TinTin++](https://tintin.mudhalla.net/) (Free, terminal-based)
- MUSHclient (Windows)
- Blowtorch (Android)

---

## 🛠️ Builder Tools (OLC)

RealmsMUD includes OasisOLC-style in-game building tools:

| Command | Description |
|---------|-------------|
| `redit` | Room editor (name, desc, exits, doors) |
| `medit <vnum>` | Mob editor (stats, flags, loot) |
| `oedit <vnum>` | Object editor (type, affects, wear) |
| `save <zone>` | Save zone to disk |

All editors are menu-driven. Type the option number to edit that field.

---

## 📖 Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](GETTING_STARTED.md) | New player tutorial |
| [Commands](COMMANDS.md) | Complete command reference |
| [Classes](CLASSES.md) | Class guide with talent trees |
| [Combat](COMBAT.md) | Combat mechanics explained |
| [OLC Spec](OLC_SPEC.md) | Builder documentation |

---

## 🏗️ Project Structure

```
RealmsMUD/
├── src/
│   ├── main.py         # Server entry point
│   ├── server.py       # Network/connection handling
│   ├── player.py       # Player class & character data
│   ├── world.py        # World management
│   ├── commands.py     # 344 player commands
│   ├── combat.py       # Combat system
│   ├── spells.py       # Magic system (100+ spells)
│   ├── talents.py      # Talent tree system
│   ├── mobs.py         # NPCs and monsters
│   ├── objects.py      # Items and equipment
│   ├── quests.py       # Quest system
│   ├── help_data.py    # 500+ help topics
│   ├── web_client.py   # Browser-based client
│   └── ...             # Additional systems
├── world/
│   └── zones/          # 40 zone JSON files
├── lib/
│   ├── players/        # Player save files
│   └── accounts/       # Account data
├── docs/               # Documentation
└── data/               # Game data files
```

---

## ⚙️ Configuration

Edit `src/config.py` to customize:

- `PORT`: Telnet port (default: 4000)
- `WEB_MAP_PORT`: Map server (default: 4001)
- `WEB_CLIENT_PORT`: Web client (default: 4003)
- `MAX_PLAYERS`: Maximum concurrent connections
- `STARTING_ROOM`: New player spawn location
- Combat parameters, experience rates, and more

---

## 📊 Statistics

- **40 zones** with 2,494 rooms
- **670 mob types**, **1,101 object types**
- **344 commands**, **500+ help topics**
- **9 classes** with unique mechanics
- **100+ spells and skills**

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Create new zones or content

---

## 📜 Credits

Inspired by CircleMUD, DikuMUD, and the classic MUD tradition. Built with Python 3 using only the standard library for maximum compatibility.

---

## 📄 License

This project is open source and available for personal and educational use.

---

*Welcome to the Realms, adventurer. Your legend awaits!* ⚔️
