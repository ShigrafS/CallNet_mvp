# registry_server.py

import socket
import threading
import json
import os

REGISTRY_FILE = 'db.json'
HOST = '0.0.0.0'
PORT = 9000

# Load or initialize the registry
if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'r') as f:
        registry = json.load(f)
else:
    registry = {}

def save_registry():
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        request = json.loads(data)

        device_id = request['device_id']
        public_key = request['public_key']
        ip = request['ip']
        port = request['port']

        # Check if device is already registered
        existing = next((num for num, v in registry.items() if v['device_id'] == device_id), None)

        if existing:
            number = existing
        else:
            # Assign next available 3-digit number
            for i in range(100, 1000):
                number = str(i)
                if number not in registry:
                    registry[number] = {
                        'device_id': device_id,
                        'public_key': public_key,
                        'ip': ip,
                        'port': port
                    }
                    save_registry()
                    break

        response = {
            'status': 'ok',
            'number': number
        }
        conn.send(json.dumps(response).encode())

    except Exception as e:
        conn.send(json.dumps({'status': 'error', 'error': str(e)}).encode())
    finally:
        conn.close()

def main():
    print(f"Starting Registry Server on port {PORT}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()
