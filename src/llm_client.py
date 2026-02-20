"""
Misthollow LLM Client
====================
Connects to LM Studio (or any OpenAI-compatible API) for NPC conversations.
"""

import aiohttp
import asyncio
import logging
import json
from typing import Optional, Dict, List

logger = logging.getLogger('Misthollow.LLM')


class LLMClient:
    """Async client for LM Studio / OpenAI-compatible APIs."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.enabled = True
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def is_available(self) -> bool:
        """Check if LM Studio server is running."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/v1/models") as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str = "local-model"
    ) -> Optional[str]:
        """
        Send a chat completion request.
        
        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            temperature: Randomness (0.0-1.0)
            max_tokens: Max response length
            model: Model name (usually ignored by LM Studio)
        
        Returns:
            Response text or None on error
        """
        if not self.enabled:
            return None
        
        try:
            session = await self._get_session()
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"LLM API error {resp.status}: {error_text}")
                    return None
                
                data = await resp.json()
                
                # Extract response content
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    return message.get("content", "").strip()
                
                return None
                
        except asyncio.TimeoutError:
            logger.warning("LLM request timed out")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"LLM connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM unexpected error: {e}")
            return None
    
    async def ask_npc(
        self,
        npc_name: str,
        npc_personality: str,
        player_name: str,
        question: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """
        Get an NPC response to a player question.
        
        Args:
            npc_name: Name of the NPC
            npc_personality: System prompt describing the NPC
            player_name: Name of the player asking
            question: What the player asked
            context: Optional context (room, recent events, etc.)
            conversation_history: Previous messages in this conversation
        
        Returns:
            NPC's response text
        """
        messages = []
        
        # System prompt
        system_prompt = f"""You are {npc_name}, a character in a fantasy MUD (text-based RPG).

{npc_personality}

RULES:
- Stay in character at all times
- Keep responses concise (2-4 sentences usually)
- Use fantasy/medieval language appropriately
- Never break character or mention being an AI
- Reference the game world naturally
- If asked about things you don't know, deflect in character
"""
        
        if context:
            system_prompt += f"\nCURRENT CONTEXT:\n{context}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages max
                messages.append(msg)
        
        # Add current question
        messages.append({
            "role": "user", 
            "content": f"{player_name} asks: {question}"
        })
        
        return await self.chat(messages, temperature=0.8, max_tokens=300)


# Global client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


async def shutdown_llm_client():
    """Shutdown the LLM client."""
    global _client
    if _client:
        await _client.close()
        _client = None
