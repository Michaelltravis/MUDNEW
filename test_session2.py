#!/usr/bin/env python3
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
                    if data: output += data.decode('utf-8', errors='replace')
                    else: return False
                except (BlockingIOError, OSError): pass
        return True
    recv_all(initial_wait)
    for cmd in commands:
        try: s.sendall((cmd + '\r\n').encode())
        except: break
        recv_all(delay)
    try: s.close()
    except: pass
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
    out = result[-5000:] if len(result) > 5000 else result
    sys.stdout.write(out + "\n")
    sys.stdout.flush()
    return result

# Test: Shops (weapon, magic, general, bakery)
r = run_test("SHOPS", LOGIN + [
    'goto 3011', 'look', 'list', 'buy sword', 'buy dagger', 'inventory',
    'sell dagger',
    'goto 3033', 'look', 'list', 'buy potion', 'buy scroll',
    'inventory', 'quaff potion',
    'goto 3010', 'look', 'list',
    'goto 3009', 'look', 'list', 'buy bread',
    'gold',
    'quit', 'y'
])

# Test: Rent
r = run_test("RENT", LOGIN + [
    'goto 3008', 'look', 'rent', 'offer',
    'quit', 'y'
])

# Test: Locked doors  
r = run_test("LOCKED DOORS", LOGIN + [
    'goto 22000', 'look', 'exits',
    'north', 'east', 'south', 'west',
    'goto 8000', 'look', 'exits',
    'north', 'east', 'south', 'west',
    'pick north', 'pick east',
    'goto 14000', 'look', 'exits',
    'north', 'east', 'south', 'west',
    'quit', 'y'
])

# Test: Boss 1 - zone 80
r = run_test("BOSS ZONE 80", LOGIN + [
    'goto 8001', 'look',
    'goto 8050', 'look',
    'goto 8099', 'look',
    'kill scorathax', 'kill dragon',
    'look',
], delay=4)
# wait for combat
time.sleep(8)
r2 = mud_session(['flee', 'quit', 'y'], delay=2)
sys.stdout.write(r2[-2000:] + "\n")

# Test: Boss 2 - zone 73
r = run_test("BOSS ZONE 73", LOGIN + [
    'goto 7300', 'look',
    'goto 7350', 'look',
    'goto 7399', 'look',
    'kill mindflayer', 'kill master',
    'look',
], delay=4)
time.sleep(8)
r2 = mud_session(['flee', 'quit', 'y'], delay=2)
sys.stdout.write(r2[-2000:] + "\n")

# Test: Mail
r = run_test("MAIL", LOGIN + [
    'mail send Deckard Hello from testing!',
    'mail list',
    'mail read 1',
    'mail delete 1',
    'quit', 'y'
])

# Test: Pet purchase
r = run_test("PET BUY", LOGIN + [
    'goto 3031', 'list', 'buy kitten', 'buy wolf',
    'look', 'south', 'look',
    'companions', 'pets', 'followers',
    'order kitten follow', 'order wolf follow',
    'quit', 'y'
])

print("\n\nALL TESTS COMPLETE")
sys.stdout.flush()
