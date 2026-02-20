#!/usr/bin/env python3
"""
Misthollow AI Player Agent
=========================
Connects to the MUD and uses a local LLM (LM Studio) to play.
Designed for exploratory testing and bug discovery.
"""

import socket
import time
import re
import sys
import asyncio
import logging
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AIMUD')


class SimpleMUDClient:
    """Basic MUD client wrapper."""
    
    def __init__(self, host='localhost', port=4000):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.buffer = ""
        self.last_room_text = ""
        
    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def send(self, command: str):
        if self.socket:
            self.socket.send(f"{command}\n".encode())
            logger.debug(f"> {command}")
    
    def receive(self, timeout=2.0) -> str:
        if not self.socket:
            return ""
        
        self.socket.settimeout(timeout)
        data = ""
        try:
            while True:
                chunk = self.socket.recv(4096).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                data += chunk
                if len(chunk) < 4096:
                    break
        except socket.timeout:
            pass
        
        # Strip ANSI
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean = ansi_escape.sub('', data)
        self.last_room_text = clean
        return clean
    
    def send_and_receive(self, command: str, wait=1.0) -> str:
        self.send(command)
        time.sleep(wait)
        return self.receive()
    
    def login(self, username: str, password: str) -> bool:
        self.receive(2)
        response = self.send_and_receive(username, 1.5)
        
        # Send password
        response = self.send_and_receive(password, 1.5)
        
        # Handle new character flow
        if "confirm" in response.lower():
            response = self.send_and_receive(password, 1.5)
        if "class" in response.lower():
            response = self.send_and_receive("warrior", 1.5)
        if "race" in response.lower():
            response = self.send_and_receive("human", 1.5)
        
        # Confirm login
        response = self.send_and_receive("look", 1.0)
        return len(response) > 50


class AIMUDPlayer:
    """AI player that uses local LLM to decide actions."""
    
    def __init__(self, host='localhost', port=4000):
        self.client = SimpleMUDClient(host, port)
        self.username = f"aibot_{int(time.time()) % 10000}"
        self.password = "aibotpass"
        self.running = False
        self.history: List[str] = []
        
    async def connect(self) -> bool:
        if not self.client.connect():
            return False
        if not self.client.login(self.username, self.password):
            logger.error("Login failed")
            return False
        logger.info(f"Logged in as {self.username}")
        return True
    
    async def think(self, room_text: str) -> str:
        """Ask local LLM what to do next."""
        try:
            from ai_service import ai_service
        except ImportError:
            logger.error("ai_service not available")
            return "look"
        
        system = """You are an AI player testing a MUD. Choose simple safe actions.
Goals:
- Explore
- Test commands
- Avoid dying
- Report interesting issues

Respond with ONE command only, no extra text."""

        prompt = f"""Current room text:
{room_text[:1500]}

Recent commands:
{', '.join(self.history[-5:]) if self.history else 'None'}

Choose next command:"""

        response = await ai_service.generate(prompt, system, max_tokens=20, temperature=0.3, use_cache=False)
        
        if response:
            # Extract first line/command
            cmd = response.split('\n')[0].strip()
            # Remove quotes if any
            cmd = cmd.strip('"\'')
            return cmd
        
        # Fallback
        return "look"
    
    async def run(self, steps: int = 50):
        """Run the AI player for a number of steps."""
        self.running = True
        
        for i in range(steps):
            if not self.running:
                break
            
            room_text = self.client.receive(1.0)
            if not room_text:
                room_text = self.client.send_and_receive("look", 1.0)
            
            command = await self.think(room_text)
            
            # Safety check - prevent dangerous commands
            if command.startswith(('quit', 'delete', 'drop all', 'give all')):
                command = 'look'
            
            logger.info(f"AI Command: {command}")
            self.history.append(command)
            
            response = self.client.send_and_receive(command, 1.0)
            logger.debug(response[:200])
            
            # Small delay
            await asyncio.sleep(1)
        
        logger.info("AI player finished.")


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    player = AIMUDPlayer(host, port)
    if await player.connect():
        await player.run(steps)


if __name__ == '__main__':
    asyncio.run(main())
