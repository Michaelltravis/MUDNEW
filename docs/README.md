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
- Real-time combat with automatic attack rounds
- Class-specific combat mechanics (Rage, Combo Points, Divine Favor, etc.)
- 30+ combat skills including Kick, Bash, Backstab, and more
- Boss encounters with special mechanics

### Magic System
- **50+ Spells** across multiple schools
- Offensive magic: Fireball, Lightning Bolt, Meteor Swarm
- Healing: Cure Light through Group Heal
- Buffs & Debuffs: Bless, Sanctuary, Haste, Sleep, Fear
- Utility: Teleport, Identify, Word of Recall

### World
- **7 Unique Zones** to explore:
  - City of Midgaard (starting city)
  - Haon Dor Forest
  - Greystone Castle
  - The Goblin Warrens
  - The Forgotten Crypt
  - The Dragon's Domain
  - Limbo (admin zone)
- Dynamic day/night cycle with weather
- Quest system with multiple objective types
- Crafting and gathering professions

### Social Features
- Account system with multiple characters
- Group/party system
- Guild support
- Multiple chat channels (Say, Shout, Gossip, Tell)
- Emotes for roleplay

### Modern Conveniences
- Web-based map viewer
- Achievement system
- Journal for tracking adventures
- New Game+ mode for replayability
- Rested XP bonus system

---

## 🚀 Quick Start

### Requirements
- Python 3.8 or higher
- No external dependencies required!

### Running the Server

```bash
# Clone the repository
git clone https://github.com/yourusername/RealmsMUD.git
cd RealmsMUD

# Make the launch script executable
chmod +x run.sh

# Start the server
./run.sh

# Or run directly
cd src && python3 main.py
```

The server starts on **port 4000** by default.

### Connecting

Use any telnet or MUD client:

```bash
telnet localhost 4000
```

**Recommended MUD Clients:**
- [Mudlet](https://www.mudlet.org/) (Free, cross-platform)
- [TinTin++](https://tintin.mudhalla.net/) (Free, terminal-based)
- MUSHclient (Windows)
- Blowtorch (Android)

---

## 📖 Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](GETTING_STARTED.md) | New player tutorial |
| [Commands](COMMANDS.md) | Complete command reference |
| [Classes](CLASSES.md) | Class guide with talent trees |
| [Combat](COMBAT.md) | Combat mechanics explained |

---

## 🏗️ Project Structure

```
RealmsMUD/
├── run.sh              # Launch script
├── src/
│   ├── main.py         # Server entry point
│   ├── server.py       # Network/connection handling
│   ├── player.py       # Player class & character data
│   ├── world.py        # World management
│   ├── commands.py     # All player commands
│   ├── combat.py       # Combat system
│   ├── spells.py       # Magic system
│   ├── talents.py      # Talent tree system
│   ├── mobs.py         # NPCs and monsters
│   ├── objects.py      # Items and equipment
│   ├── quests.py       # Quest system
│   └── ...             # Additional systems
├── world/
│   └── zones/          # Zone data files
├── lib/
│   ├── players/        # Player save files
│   └── accounts/       # Account data
├── docs/               # Documentation
└── log/                # Server logs
```

---

## ⚙️ Configuration

Edit `src/config.py` to customize:

- `PORT`: Server port (default: 4000)
- `MAX_PLAYERS`: Maximum concurrent connections
- `STARTING_ROOM`: New player spawn location
- Combat parameters
- Experience rates
- And much more...

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
