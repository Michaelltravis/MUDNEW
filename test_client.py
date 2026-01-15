"""Simple MUD test client"""
import socket
import time
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

def test_mud():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 4000))

    # Read welcome message
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("=== WELCOME ===")
    print(data)

    # Send name
    sock.send(b'testplayer\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== NAME RESPONSE ===")
    print(data)

    # Confirm new character
    sock.send(b'y\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== NEW CHARACTER ===")
    print(data)

    # Enter password (password123)
    sock.send(b'password123\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== PASSWORD ===")
    print(data)

    # Confirm password
    sock.send(b'password123\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== PASSWORD CONFIRMED ===")
    print(data)

    # Choose race (Human)
    sock.send(b'human\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== RACE SELECTED ===")
    print(data)

    # Choose class (Warrior)
    sock.send(b'warrior\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== CLASS SELECTED ===")
    print(data)

    # Accept stats
    sock.send(b'y\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== CHARACTER CREATED ===")
    print(data)

    # Test look command
    sock.send(b'look\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== LOOK COMMAND ===")
    print(data)

    # Test time command
    sock.send(b'time\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== TIME COMMAND ===")
    print(data)

    # Test weather command
    sock.send(b'weather\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== WEATHER COMMAND ===")
    print(data)

    # Test score
    sock.send(b'score\n')
    time.sleep(0.5)
    data = sock.recv(4096).decode('utf-8', errors='ignore')
    print("\n=== SCORE ===")
    print(data)

    sock.close()

if __name__ == '__main__':
    test_mud()
