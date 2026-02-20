#!/usr/bin/env python3
"""
Misthollow Stress Test
Simulates multiple concurrent connections
"""

import asyncio
import random
import time
import sys
import os

HOST = 'localhost'
PORT = 4000

# Configuration
NUM_CONNECTIONS = 25      # Total connections to make
CONCURRENT_MAX = 10       # Max at same time
TEST_DURATION = 20        # seconds per connection
COMMANDS_DELAY = 0.5      # seconds between commands

# Test credentials
ACCOUNT = "deckard"
PASSWORD = "gnrl dyks gpnv kmbz"

COMMANDS = [
    "look", "north", "south", "east", "west", "score", "who",
    "inventory", "equipment", "exits", "time", "weather", "map",
    "north", "south", "look", "help", "affects"
]

stats = {
    'connections': 0,
    'successful_logins': 0,
    'commands_sent': 0,
    'errors': 0,
    'bytes_received': 0
}

async def stress_connection(conn_id, char_num):
    """Single stress test connection."""
    global stats
    
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(HOST, PORT),
            timeout=10
        )
        stats['connections'] += 1
    except Exception as e:
        print(f"[{conn_id}] Connection failed: {e}")
        stats['errors'] += 1
        return
    
    try:
        # Read welcome
        data = await asyncio.wait_for(reader.read(4096), timeout=5)
        stats['bytes_received'] += len(data)
        
        # Login
        writer.write(f"{ACCOUNT}\n".encode())
        await writer.drain()
        await asyncio.sleep(0.2)
        data = await reader.read(2048)
        stats['bytes_received'] += len(data)
        
        writer.write(f"{PASSWORD}\n".encode())
        await writer.drain()
        await asyncio.sleep(0.2)
        data = await reader.read(2048)
        stats['bytes_received'] += len(data)
        
        # Select character
        writer.write(f"{char_num}\n".encode())
        await writer.drain()
        await asyncio.sleep(0.3)
        data = await reader.read(4096)
        stats['bytes_received'] += len(data)
        
        stats['successful_logins'] += 1
        print(f"[{conn_id}] Logged in as char {char_num}")
        
        # Send commands for duration
        end_time = time.time() + TEST_DURATION
        while time.time() < end_time:
            cmd = random.choice(COMMANDS)
            writer.write(f"{cmd}\n".encode())
            await writer.drain()
            stats['commands_sent'] += 1
            
            try:
                data = await asyncio.wait_for(reader.read(4096), timeout=2)
                stats['bytes_received'] += len(data)
            except asyncio.TimeoutError:
                pass
            
            await asyncio.sleep(COMMANDS_DELAY + random.uniform(-0.1, 0.1))
        
        # Quit
        writer.write(b"quit\ny\n")
        await writer.drain()
        
    except Exception as e:
        print(f"[{conn_id}] Error: {e}")
        stats['errors'] += 1
    
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
    
    print(f"[{conn_id}] Disconnected")

async def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              Misthollow Stress Test                           ║
╠══════════════════════════════════════════════════════════════╣
║  Total connections:  {NUM_CONNECTIONS:<4}                                   ║
║  Concurrent max:     {CONCURRENT_MAX:<4}                                   ║
║  Duration each:      {TEST_DURATION}s                                    ║
║  Command interval:   {COMMANDS_DELAY}s                                   ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    start_time = time.time()
    
    # Run in batches
    for batch_start in range(0, NUM_CONNECTIONS, CONCURRENT_MAX):
        batch_end = min(batch_start + CONCURRENT_MAX, NUM_CONNECTIONS)
        batch_size = batch_end - batch_start
        
        print(f"\n[*] Starting batch {batch_start//CONCURRENT_MAX + 1}: connections {batch_start+1}-{batch_end}")
        
        tasks = []
        for i in range(batch_start, batch_end):
            # Rotate through characters 1-8
            char_num = (i % 8) + 1
            task = asyncio.create_task(stress_connection(i+1, char_num))
            tasks.append(task)
            await asyncio.sleep(0.1)  # Stagger connections
        
        await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              STRESS TEST RESULTS                             ║
╠══════════════════════════════════════════════════════════════╣
║  Total time:         {elapsed:>6.1f}s                                 ║
║  Connections made:   {stats['connections']:>6}                                  ║
║  Successful logins:  {stats['successful_logins']:>6}                                  ║
║  Commands sent:      {stats['commands_sent']:>6}                                  ║
║  Commands/sec:       {stats['commands_sent']/elapsed:>6.1f}                                 ║
║  Data received:      {stats['bytes_received']/1024:>6.1f} KB                              ║
║  Errors:             {stats['errors']:>6}                                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    success_rate = stats['successful_logins'] / max(stats['connections'], 1) * 100
    
    if success_rate >= 95 and stats['errors'] <= 2:
        print("✅ STRESS TEST PASSED!")
        return 0
    elif success_rate >= 80:
        print("⚠️  STRESS TEST PASSED (with issues)")
        return 0
    else:
        print("❌ STRESS TEST FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
