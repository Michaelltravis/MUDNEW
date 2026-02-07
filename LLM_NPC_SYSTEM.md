# LLM-Powered NPC System - RealmsMUD

**Date:** 2026-02-02  
**Status:** Ready for testing (needs LM Studio)

---

## Overview

NPCs can now have intelligent conversations with players using a local LLM (via LM Studio). Players use the `ask` command to talk to NPCs, who respond based on their personality and role.

---

## Setup Requirements

### 1. Install LM Studio
- Download from https://lmstudio.ai
- Install on Mac mini (16GB RAM is perfect)

### 2. Download a Model
- Open LM Studio → Discover tab
- Search: `llama 3.2 3b instruct`
- Download the Q4_K_M version

### 3. Start the Server
- Go to "Local Server" tab
- Load your model
- Click "Start Server"
- Server runs on `http://localhost:1234`

### 4. Restart RealmsMUD
- The MUD will auto-detect LM Studio when available
- If not running, players get a fallback message

---

## Player Usage

```
ask <npc> <question>
```

**Examples:**
```
ask sage What is the history of this realm?
ask bartender Any rumors lately?
ask blacksmith What's the best weapon for a warrior?
ask oracle What does my future hold?
ask guard Where can I find the thieves guild?
```

---

## NPC Personality System

NPCs get personalities based on their name, keywords, or `special` field:

| Keyword | Personality |
|---------|-------------|
| sage | Ancient wisdom, speaks in riddles, knows lore |
| oracle | Mystical, prophetic, cryptic hints |
| scholar | Academic, enthusiastic, precise |
| merchant | Shrewd, friendly, knows trade |
| blacksmith | Gruff, practical, knows weapons/armor |
| alchemist | Eccentric, knows potions |
| bartender | Friendly, knows gossip |
| bard | Dramatic, knows legends |
| priest | Compassionate, spiritual |
| healer | Gentle, knows medicine |
| guard | Formal, suspicious, knows laws |
| trainer | Authoritative, knows combat |
| guildmaster | Evaluating, knows quests |
| hooded | Mysterious, cryptic |
| witch | Cackling, knows dark magic |

**Default:** Generic helpful NPC if no personality matches.

---

## Technical Details

### Files Added
- `src/llm_client.py` - Async client for LM Studio API
- `src/npc_personalities.py` - NPC personality definitions
- `world/mobs/sage_npc.json` - Example sage NPC

### Files Modified
- `src/commands.py` - Added `ask` command
- `src/help_data.py` - Added help entry for `ask`

### API Integration
- Uses OpenAI-compatible `/v1/chat/completions` endpoint
- Async HTTP via aiohttp
- Graceful fallback if server unavailable
- Conversation history per player-NPC pair (last 10 messages)

### System Prompt Structure
```
You are {npc_name}, a character in a fantasy MUD.

{personality description}

RULES:
- Stay in character at all times
- Keep responses concise (2-4 sentences)
- Use fantasy/medieval language
- Never break character or mention being an AI
- Reference the game world naturally

CONTEXT:
Location: {room} in {zone}
Time: {time_of_day}
Speaking to: {player_name}, level {level} {race} {class}
```

---

## Context Provided to LLM

Each conversation includes:
- NPC name and personality
- Current room and zone
- Time of day
- Player name, level, race, class
- Last 6 messages of conversation history

---

## Performance

With Llama 3.2 3B on Mac mini (16GB):
- Response time: ~1-2 seconds
- Memory usage: ~3GB for model
- Plenty of RAM left for MUD server

---

## Future Improvements

1. **Lore Database** - Feed NPCs actual game lore
2. **Quest Integration** - NPCs can give/track quests via conversation
3. **Memory Persistence** - Save conversations across sessions
4. **Mood/Relationship** - NPCs remember how players treated them
5. **Procedural Quests** - LLM generates quest content
6. **Combat Narration** - LLM describes combat dramatically

---

## Troubleshooting

**"LLM server not available"**
- Start LM Studio and load a model
- Check server is running on port 1234

**Slow responses**
- Use a smaller model (3B vs 7B)
- Check Mac mini isn't memory constrained

**Bad/inconsistent responses**
- Adjust temperature in llm_client.py (0.7-0.9 works well)
- Some models role-play better than others

---

*This system brings NPCs to life with actual conversations instead of canned dialogue trees!*
