# register_client.py

import json
import socket
from identity import get_device_id_and_key

def register(server_ip='127.0.0.1', port=9000, local_ip='127.0.0.1', voice_port=8081):
    device_id, public_key = get_device_id_and_key()

    request = {
        'device_id': device_id,
        'public_key': public_key,
        'ip': local_ip,
        'port': voice_port
    }

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, port))
        s.send(json.dumps(request).encode())
        response = s.recv(1024).decode()
        s.close()

        print("Registry Server Response:")
        print(response)

    except Exception as e:
        print(f"Failed to connect to registry server: {e}")

if __name__ == "__main__":
    register()
