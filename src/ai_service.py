"""
Misthollow AI Service
====================
Local LLM integration via LM Studio for dynamic content generation.
Connects to LM Studio's OpenAI-compatible API on localhost:1234.
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger('Misthollow.AI')

@dataclass
class AIConfig:
    """AI service configuration."""
    base_url: str = "http://127.0.0.1:1234/v1"
    model: str = "local-model"  # LM Studio uses this as default
    max_tokens: int = 150
    temperature: float = 0.7
    timeout: int = 10
    enabled: bool = True
    cache_ttl: int = 300  # Cache responses for 5 minutes
    rate_limit: float = 0.5  # Min seconds between requests


class AIService:
    """
    AI service for dynamic MUD content generation.
    Uses LM Studio's local API for fast, free inference.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = AIConfig()
        self.cache: Dict[str, tuple] = {}  # hash -> (response, timestamp)
        self.last_request_time = 0
        self.available = None  # None = unknown, True/False = checked
        self._initialized = True
        
    async def check_availability(self) -> bool:
        """Check if LM Studio is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.base_url}/models",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status == 200:
                        self.available = True
                        logger.info("AI service connected to LM Studio")
                        return True
        except Exception as e:
            logger.debug(f"LM Studio not available: {e}")
        
        self.available = False
        return False
    
    def _get_cache_key(self, prompt: str, system: str = "") -> str:
        """Generate cache key for a prompt."""
        content = f"{system}|{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[str]:
        """Get cached response if valid."""
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < self.config.cache_ttl:
                return response
            del self.cache[key]
        return None
    
    def _set_cache(self, key: str, response: str):
        """Cache a response."""
        self.cache[key] = (response, time.time())
        
        # Cleanup old entries
        now = time.time()
        self.cache = {
            k: v for k, v in self.cache.items()
            if now - v[1] < self.config.cache_ttl
        }
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit:
            await asyncio.sleep(self.config.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate text using the local LLM.
        
        Args:
            prompt: The user prompt
            system: System message for context
            max_tokens: Override default max tokens
            temperature: Override default temperature
            use_cache: Whether to use response caching
            
        Returns:
            Generated text or None if unavailable
        """
        if not self.config.enabled:
            return None
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(prompt, system)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        # Check availability (lazy check)
        if self.available is None:
            await self.check_availability()
        
        if not self.available:
            return None
        
        # Rate limit
        await self._rate_limit()
        
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Make request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.base_url}/chat/completions",
                    json={
                        "model": self.config.model,
                        "messages": messages,
                        "max_tokens": max_tokens or self.config.max_tokens,
                        "temperature": temperature or self.config.temperature,
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"].strip()
                        
                        # Cache response
                        if use_cache:
                            self._set_cache(cache_key, content)
                        
                        return content
                    else:
                        logger.warning(f"AI request failed: {resp.status}")
                        
        except asyncio.TimeoutError:
            logger.warning("AI request timed out")
        except Exception as e:
            logger.warning(f"AI request error: {e}")
            self.available = False  # Mark as unavailable
        
        return None

    # ==================== MUD-SPECIFIC METHODS ====================
    
    async def npc_dialogue(
        self,
        npc_name: str,
        npc_desc: str,
        npc_personality: str,
        player_name: str,
        player_says: str,
        conversation_history: List[str] = None
    ) -> Optional[str]:
        """
        Generate NPC dialogue response.
        
        Args:
            npc_name: Name of the NPC
            npc_desc: Short description of the NPC
            npc_personality: Personality traits
            player_name: Name of the player talking
            player_says: What the player said
            conversation_history: Recent conversation lines
            
        Returns:
            NPC's response or None
        """
        system = f"""You are {npc_name}, {npc_desc}.
Personality: {npc_personality}

Rules:
- Stay in character as {npc_name}
- Keep responses brief (1-3 sentences)
- Use medieval fantasy speech patterns
- Never break character or mention being an AI
- React naturally to what the player says"""

        history = ""
        if conversation_history:
            history = "\nRecent conversation:\n" + "\n".join(conversation_history[-4:]) + "\n"
        
        prompt = f"{history}{player_name} says to you: \"{player_says}\"\n\nRespond as {npc_name}:"
        
        response = await self.generate(prompt, system, max_tokens=100, use_cache=False)
        
        if response:
            # Clean up response
            response = response.strip('"\'')
            # Remove any "NPC says:" prefix the model might add
            if response.lower().startswith(npc_name.lower()):
                response = response[len(npc_name):].lstrip(':').strip()
        
        return response
    
    async def generate_quest(
        self,
        quest_giver: str,
        location: str,
        player_level: int,
        available_mobs: List[str],
        available_items: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a dynamic quest.
        
        Returns:
            Quest dict with type, target, count, reward_gold, description
        """
        system = """You are a quest generator for a fantasy MUD game.
Generate simple fetch or kill quests.
Respond ONLY in JSON format with these fields:
- type: "kill" or "fetch"
- target: name of mob to kill or item to fetch
- count: number needed (1-10)
- reward_gold: gold reward (10-500 based on difficulty)
- description: brief quest description (1-2 sentences)"""

        prompt = f"""Generate a quest for a level {player_level} adventurer.
Quest giver: {quest_giver}
Location: {location}
Available monsters: {', '.join(available_mobs[:5])}
Available items: {', '.join(available_items[:5])}

Respond with JSON only:"""

        response = await self.generate(prompt, system, max_tokens=150, temperature=0.8)
        
        if response:
            try:
                # Try to parse JSON
                # Handle markdown code blocks
                if "```" in response:
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse quest JSON: {response}")
        
        return None
    
    async def combat_narration(
        self,
        attacker: str,
        defender: str,
        damage: int,
        weapon: str = "fists",
        is_crit: bool = False,
        is_kill: bool = False
    ) -> Optional[str]:
        """Generate dramatic combat narration."""
        
        system = """You are a combat narrator for a fantasy MUD.
Write brief, dramatic combat descriptions (1 sentence).
Use vivid action verbs. Be concise."""

        if is_kill:
            prompt = f"{attacker} delivers the killing blow to {defender} with their {weapon} ({damage} damage). Describe the death dramatically:"
        elif is_crit:
            prompt = f"{attacker} lands a critical hit on {defender} with their {weapon} ({damage} damage). Describe this devastating blow:"
        else:
            prompt = f"{attacker} strikes {defender} with their {weapon} for {damage} damage. Describe this briefly:"
        
        return await self.generate(prompt, system, max_tokens=60, temperature=0.9)
    
    async def room_ambiance(
        self,
        room_name: str,
        room_desc: str,
        time_of_day: str,
        weather: str
    ) -> Optional[str]:
        """Generate ambient room flavor text."""
        
        system = """Generate brief atmospheric descriptions for fantasy locations.
One short sentence only. Focus on sounds, smells, or small details."""

        prompt = f"""Location: {room_name}
Description: {room_desc}
Time: {time_of_day}
Weather: {weather}

Write one brief ambient detail:"""

        return await self.generate(prompt, system, max_tokens=40, temperature=0.9)
    
    async def item_lore(
        self,
        item_name: str,
        item_type: str,
        item_stats: str = ""
    ) -> Optional[str]:
        """Generate lore/flavor text for an item."""
        
        system = """Generate brief fantasy item lore. 
2-3 sentences about the item's history or magical properties.
Medieval fantasy style."""

        prompt = f"""Item: {item_name}
Type: {item_type}
{f'Stats: {item_stats}' if item_stats else ''}

Write brief lore for this item:"""

        return await self.generate(prompt, system, max_tokens=80, temperature=0.7)


# Global instance
ai_service = AIService()
