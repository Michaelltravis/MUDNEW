# Getting Started with RealmsMUD

Welcome to RealmsMUD! This guide will help you create your first character and take your first steps in the world of the Realms.

---

## 📡 Connecting to the Server

### Step 1: Choose Your Client

You'll need a telnet or MUD client to connect. Here are some options:

**Beginner-Friendly:**
- **[Mudlet](https://www.mudlet.org/)** - Free, cross-platform, with a nice GUI
- **Web Client** - If the server has one enabled, just use your browser!

**Terminal Users:**
- `telnet localhost 4000` (basic but works)
- **[TinTin++](https://tintin.mudhalla.net/)** - Powerful terminal MUD client

### Step 2: Connect

```bash
# Using telnet
telnet <server-address> 4000

# Or if running locally
telnet localhost 4000
```

You should see the welcome screen with the RealmsMUD banner!

---

## 🆕 Creating Your Account & Character

When you connect for the first time, you'll be prompted to create an account.

### Account Creation

```
Welcome to RealmsMUD!

Enter your account name (or 'new' for a new account): new
Enter a name for your new account: MyAccount
Enter a password: ********
Confirm password: ********

Account created! Now let's create your first character.
```

> 💡 **Tip:** Your account can hold up to 8 characters, so you can try different classes!

### Character Creation

```
Enter a name for your character: Thorin
```

**Choose Your Race:**
```
Available Races:
  1) Human     - Versatile, bonus to Charisma
  2) Elf       - High INT/DEX, good for mages and rangers
  3) Dwarf     - Tough and sturdy, great for warriors
  4) Halfling  - Nimble and brave, perfect for thieves
  5) Half-Orc  - Raw strength, formidable warriors
  6) Gnome     - Clever illusionists
  7) Dark Elf  - Mysterious shadow magic users

Select race (1-7): 
```

**Choose Your Class:**
```
Available Classes:
  1) Warrior     - Masters of combat and defense
  2) Mage        - Wielders of arcane destruction
  3) Cleric      - Divine healers and undead slayers
  4) Thief       - Cunning rogues from the shadows
  5) Ranger      - Wilderness warriors with animal companions
  6) Paladin     - Holy warriors combining might and magic
  7) Necromancer - Dark mages commanding undeath
  8) Bard        - Charismatic performers with magical songs
  9) Assassin    - Deadly killers with lethal precision

Select class (1-9):
```

After creation, you'll appear in the Temple of Midgaard!

---

## 🎯 First Steps

### Look Around

When you first spawn, type `look` (or just `l`) to see your surroundings:

```
> look

The Temple of Midgaard
You are in the southern end of the temple hall in the Temple of 
Midgaard. The temple has been built in honor of the gods of the 
realm. Huge marble pillars support the painted ceiling high above.

Exits: [N]orth [S]outh [E]ast [W]est

You see:
  A healing fountain bubbles peacefully here.
  
Standing here:
  A temple guard stands watch. [GUARD]
```

### Check Your Stats

Type `score` (or `sc`) to see your character information:

```
> score

╔════════════════════════════════════════════╗
║  Thorin the Dwarven Warrior                ║
║  Level 1                                   ║
╠════════════════════════════════════════════╣
║  HP: 100/100   Mana: 20/20   Move: 100/100 ║
║  STR: 14  INT: 9   WIS: 11                 ║
║  DEX: 9   CON: 16  CHA: 9                  ║
╠════════════════════════════════════════════╣
║  Gold: 100      Experience: 0              ║
║  Armor Class: 100                          ║
╚════════════════════════════════════════════╝
```

### Get Equipped

Before venturing out, visit the shops! Head to the **General Store**:

```
> north
> east
> list

The shopkeeper shows you:
  1) Torch                    5 gold
  2) Backpack                10 gold
  3) Waterskin               3 gold
  4) Bread                   2 gold

> buy torch
You buy a torch for 5 gold.

> buy backpack
You buy a backpack for 10 gold.
```

Visit the **Armory** and **Weapons Shop** too:

```
> buy sword
> buy leather armor
> wield sword
You wield a short sword.

> wear armor
You wear leather armor on your body.
```

Check your equipment with `equipment` or `eq`:

```
> eq

You are using:
  <wielded>     a short sword
  <worn on body> leather armor
```

---

## ⚔️ Your First Fight

### Finding Monsters

Leave the city and find some creatures to fight. Head to **Haon Dor Forest**:

```
> south
> south  
> west

Haon Dor Forest - Trail Entrance
A well-worn path leads into the ancient forest...

Standing here:
  A small rabbit nibbles on some grass.
```

### Gauging Difficulty

Before attacking, use `consider` to see if you can win:

```
> consider rabbit
The rabbit looks like an easy kill!
```

The responses range from:
- "Easy kill!" - Much weaker than you
- "Looks like a fair fight" - Similar level
- "Could be tough..." - Slightly stronger
- "You would need a lot of luck!" - Much stronger
- "Are you MAD?!" - Don't even try

### Attacking

```
> kill rabbit
You attack the small rabbit!
You hit the rabbit for 8 damage!
The rabbit bites you for 2 damage!
You hit the rabbit for 12 damage!
The rabbit is DEAD!

You receive 50 experience points.
You get 3 gold coins from the corpse.
```

### If Things Go Wrong

If a fight isn't going well, you can try to run:

```
> flee
You flee north!
```

Fleeing costs some experience, but it's better than dying!

---

## 🗺️ Navigation

### Basic Movement

Move using cardinal directions:
- `north` or `n`
- `south` or `s`  
- `east` or `e`
- `west` or `w`
- `up` or `u`
- `down` or `d`

### Useful Navigation Commands

| Command | What it does |
|---------|--------------|
| `look` | See the current room |
| `exits` | List available exits |
| `map` | View the world map |
| `minimap` | Toggle ASCII minimap |
| `where` | Find players/mobs in zone |
| `recall` | Return to temple (emergency!) |

---

## 💬 Talking to Others

### Chat Commands

| Command | Range | Example |
|---------|-------|---------|
| `say <msg>` | Current room | `say Hello everyone!` |
| `shout <msg>` | Current zone | `shout Anyone need help?` |
| `gossip <msg>` | Entire server | `gossip Looking for a group!` |
| `tell <player> <msg>` | Private message | `tell Gandalf Nice robe!` |
| `emote <action>` | Roleplay | `emote waves hello.` |

### Talking to NPCs

Some NPCs give quests! Use `talk`:

```
> talk guard
The temple guard says, "Greetings, adventurer! The city has been
troubled by goblins lately. Would you help us deal with them?"

[Quest Available: Goblin Menace]
Type 'quest accept goblin_menace' to accept.
```

---

## 📋 Quests

### Getting Quests

1. Find an NPC with a quest (look for `[QUEST]` markers)
2. `talk <npc>` to hear about available quests
3. `quest accept <quest_name>` to accept

### Managing Quests

| Command | What it does |
|---------|--------------|
| `quest list` | See available quests nearby |
| `quest log` | View your active quests |
| `quest info <quest>` | Details about a quest |
| `quest abandon <quest>` | Give up on a quest |

---

## 💾 Saving & Quitting

Your character auto-saves periodically, but you can manually save:

```
> save
Character saved!

> quit
Goodbye! Your character has been saved.
```

---

## 📈 Leveling Up

As you gain experience, you'll level up automatically! Each level grants:
- More HP, Mana, and Movement
- Better combat stats
- Access to new skills and spells
- Talent points (starting at level 5)

### Practicing Skills

Visit a **Guildmaster** to practice skills:

```
> practice

You can practice:
  kick         [not learned]  - Cost: 1 practice
  bash         [not learned]  - Cost: 1 practice
  rescue       [not learned]  - Cost: 1 practice
  
You have 5 practice sessions.

> practice kick
You learn the basics of kicking.
Kick: 25%
```

---

## 🌟 Tips for New Players

1. **Don't be afraid to explore** - The world is big! Wander around and discover new areas.

2. **Check your rested XP** - Log out at an inn for bonus experience when you return!

3. **Group up** - Many areas are designed for groups. Use `gossip` to find other players.

4. **Read item descriptions** - Use `examine <item>` to learn about what you find.

5. **Use the help system** - Type `help <topic>` for detailed information on anything.

6. **Bind your recall** - The `recall` command teleports you back to the temple. It's a lifesaver!

7. **Rest to regenerate** - Use `rest` or `sleep` to recover HP/Mana faster.

8. **Save often** - While there's auto-save, `save` gives you peace of mind.

---

## 🆘 Getting Help

- `help` - List all help topics
- `help <topic>` - Get help on a specific topic
- `help commands` - List all available commands
- `gossip` - Ask other players for help!

---

## Next Steps

Now that you know the basics, check out these guides:
- **[Commands Reference](COMMANDS.md)** - Complete list of all commands
- **[Class Guide](CLASSES.md)** - Learn about your class's abilities
- **[Combat Guide](COMBAT.md)** - Master the combat system

Good luck, adventurer! May your sword stay sharp and your spells true! ⚔️✨
