#!/usr/bin/env python3
"""
Misthollow Supervisor
- Auto-restarts on crash
- Discord webhook alerts
- Health monitoring
"""

import subprocess
import time
import os
import sys
import json
import urllib.request
import signal
from datetime import datetime

# Configuration
MUD_DIR = "/Users/michaeltravis/clawd/projects/Misthollow"
MUD_CMD = ["python3", "src/main.py"]
LOG_FILE = os.path.join(MUD_DIR, "server.log")
PID_FILE = os.path.join(MUD_DIR, "mud.pid")
DISCORD_WEBHOOK = os.environ.get("MISTHOLLOW_DISCORD_WEBHOOK", "")
MAX_RESTARTS = 5
RESTART_WINDOW = 300  # 5 minutes
RESTART_DELAY = 5

# Track restarts
restart_times = []
process = None

def send_discord_alert(title: str, message: str, color: int = 0xFF0000):
    """Send alert to Discord webhook."""
    if not DISCORD_WEBHOOK:
        print(f"[ALERT] {title}: {message}")
        return
    
    payload = {
        "embeds": [{
            "title": f"🎮 Misthollow: {title}",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }]
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[ERROR] Discord alert failed: {e}")

def get_last_log_lines(n: int = 10) -> str:
    """Get last N lines from log file."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-n:])
    except:
        return "(no log available)"

def cleanup_old_restarts():
    """Remove restart times outside the window."""
    global restart_times
    now = time.time()
    restart_times = [t for t in restart_times if now - t < RESTART_WINDOW]

def start_mud():
    """Start the MUD process."""
    global process
    
    with open(LOG_FILE, 'a') as log:
        process = subprocess.Popen(
            MUD_CMD,
            cwd=MUD_DIR,
            stdout=log,
            stderr=subprocess.STDOUT
        )
    
    # Write PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))
    
    return process

def handle_signal(signum, frame):
    """Handle shutdown signals."""
    global process
    print(f"\n[SUPERVISOR] Received signal {signum}, shutting down...")
    
    if process:
        process.terminate()
        process.wait(timeout=10)
    
    send_discord_alert("Shutdown", "Server stopped by administrator.", 0x808080)
    sys.exit(0)

def main():
    global process
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    print(f"[SUPERVISOR] Starting Misthollow supervisor...")
    print(f"[SUPERVISOR] Discord alerts: {'enabled' if DISCORD_WEBHOOK else 'disabled'}")
    
    send_discord_alert("Starting", "Server supervisor initializing...", 0x00FF00)
    
    while True:
        cleanup_old_restarts()
        
        # Check restart limit
        if len(restart_times) >= MAX_RESTARTS:
            msg = f"Too many restarts ({MAX_RESTARTS}) in {RESTART_WINDOW}s. Stopping supervisor."
            print(f"[SUPERVISOR] {msg}")
            send_discord_alert("CRITICAL", msg + f"\n\nLast log:\n```\n{get_last_log_lines(15)}\n```", 0xFF0000)
            sys.exit(1)
        
        # Start MUD
        print(f"[SUPERVISOR] Starting MUD process...")
        process = start_mud()
        
        if restart_times:
            send_discord_alert("Restarted", f"Server restarted (attempt {len(restart_times)+1})", 0xFFFF00)
        else:
            send_discord_alert("Online", "Server is now running!", 0x00FF00)
        
        # Wait for process to exit
        return_code = process.wait()
        
        print(f"[SUPERVISOR] MUD process exited with code {return_code}")
        
        if return_code == 0:
            # Clean shutdown
            send_discord_alert("Shutdown", "Server shut down cleanly.", 0x808080)
            break
        else:
            # Crash - restart
            restart_times.append(time.time())
            log_snippet = get_last_log_lines(20)
            send_discord_alert(
                "CRASH", 
                f"Server crashed with code {return_code}. Restarting in {RESTART_DELAY}s...\n\n```\n{log_snippet}\n```",
                0xFF0000
            )
            print(f"[SUPERVISOR] Waiting {RESTART_DELAY}s before restart...")
            time.sleep(RESTART_DELAY)
    
    # Cleanup
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

if __name__ == '__main__':
    main()
