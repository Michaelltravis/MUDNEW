#!/usr/bin/env python3
"""MUD playtest automation script"""
import socket, time, re, select, sys

def mud_session(commands, delay=2, initial_wait=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 4000))
    s.setblocking(False)
    output = ''
    
    def recv_all(wait=2):
        nonlocal output
        end = time.time() + wait
        while time.time() < end:
            ready = select.select([s], [], [], 0.3)
            if ready[0]:
                try:
                    data = s.recv(8192)
                    if data:
                        output += data.decode('utf-8', errors='replace')
                    else:
                        return False
                except (BlockingIOError, OSError):
                    pass
        return True
    
    recv_all(initial_wait)
    
    for cmd in commands:
        try:
            s.sendall((cmd + '\r\n').encode())
        except:
            break
        recv_all(delay)
    
    try:
        s.close()
    except:
        pass
    
    output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    output = re.sub(r'\x1b\][^\x07]*\x07', '', output)
    output = re.sub(r'\xff[\xfb-\xfe].', '', output)
    output = re.sub(r'\r', '', output)
    return output

LOGIN = ['deckard', 'deckard123', 'play Deckard']

def run_test(name, commands, delay=2):
    sys.stdout.write(f"\n{'='*60}\nTEST: {name}\n{'='*60}\n")
    sys.stdout.flush()
    result = mud_session(commands, delay=delay)
    # Print last 4000 chars to save space
    out = result[-4000:] if len(result) > 4000 else result
    sys.stdout.write(out + "\n")
    sys.stdout.flush()
    return result

# Test 1: Login + misc
r1 = run_test("LOGIN + MISC", LOGIN + [
    'look', 'time', 'weather', 'score',
    'trade', 'duel', 'faction', 'reputation',
    'mail list', 'wimpy', 'wimpy 50',
    'quit', 'y'
])

# Test 2: Combat - find mobs
r2 = run_test("COMBAT", LOGIN + [
    'goto 3001', 'look',
    'goto 3059', 'look',  # south Midgaard - might have mobs
    'goto 3005', 'look',
    'kill guard',
    'kill citizen',
    'goto 5101', 'look',
    'kill mob',
    'kill rat',
    'kill spider',
    'flee',
    'quit', 'y'
], delay=3)

# Test 3: Shops
r3 = run_test("SHOPS", LOGIN + [
    'goto 3031', 'look', 'list',
    'buy sword', 'buy 1',
    'sell sword',
    'inventory',
    'goto 3032', 'look', 'list',
    'buy potion', 'buy 1',
    'quaff potion',
    'goto 3030', 'look', 'list',
    'goto 3010', 'look', 'list',
    'gold', 'balance',
    'quit', 'y'
])

# Test 4: Rent
r4 = run_test("RENT", LOGIN + [
    'goto 3008', 'look',
    'rent', 'rent cost', 'offer',
    'quit', 'y'
])

# Test 5: Locked doors
r5 = run_test("LOCKED DOORS", LOGIN + [
    'goto 22000', 'look',
    'north', 'south', 'east', 'west',
    'pick north', 'pick south',
    'unlock north',
    'goto 8000', 'look',
    'north', 'south', 'east', 'west',
    'goto 5300', 'look',
    'north', 'south', 'east', 'west',
    'quit', 'y'
])

# Test 6: Boss fights
r6 = run_test("BOSS FIGHTS", LOGIN + [
    'goto 8001', 'look',
    'goto 8050', 'look',
    'goto 8099', 'look',
    'kill scorathax', 'kill dragon', 'kill boss',
    'goto 7300', 'look',
    'goto 7350', 'look',
    'kill mindflayer', 'kill master',
    'flee',
    'quit', 'y'
], delay=3)

# Test 7: Mail  
r7 = run_test("MAIL", LOGIN + [
    'mail list',
    'mail send Deckard Testing mail system',
    'mail list',
    'mail read 1',
    'quit', 'y'
])

# Test 8: Pet store
r8 = run_test("PET STORE", LOGIN + [
    'goto 3031', 'look',
    'goto 3032', 'look', 'list',
    'buy pet', 'buy 1',
    'companions', 'pets', 'followers',
    'order pet follow',
    'quit', 'y'
])

print("\n\nALL TESTS COMPLETE")
sys.stdout.flush()
