import socket
import threading
from typing import Dict
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_CLIENTS = 10
CHUNK_SIZE = 4096

class VoiceServer:
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.clients: Dict[socket.socket, str] = {}
        self.clients_lock = threading.Lock()
        self.running = True
        self.active_calls: Dict[socket.socket, socket.socket] = {}  # socket -> partner or pending target

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CLIENTS)
            logger.info(f"Voice Server listening on port {self.port} (max {MAX_CLIENTS} clients)...")
            signal.signal(signal.SIGINT, self.handle_shutdown)

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()

                    if len(self.clients) >= MAX_CLIENTS:
                        client_socket.send(b"SERVER_FULL")
                        client_socket.close()
                        continue

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except Exception as e:
                    logger.error(f"Error accepting connection: {e}")

        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket, address):
        try:
            name_data = client_socket.recv(1024).decode()
            if name_data.startswith("NAME:"):
                client_name = name_data[5:]
                with self.clients_lock:
                    self.clients[client_socket] = client_name
                logger.info(f"New client connected: {client_name} from {address}")
                self.broadcast_control_message(f"SERVER: {client_name} joined", client_socket)

                while self.running:
                    data = client_socket.recv(CHUNK_SIZE)
                    if not data:
                        break

                    # Handle slash commands text
                    try:
                        text = data.decode().strip()
                        if text.startswith("/"):
                            self.handle_command(text, client_socket)
                            continue
                    except:
                        pass

                    self.broadcast_audio(data, client_socket)

        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            self.remove_client(client_socket)

    def handle_command(self, cmd, client_socket):
        user = self.clients.get(client_socket)

        if cmd.startswith("/call "):
            target_name = cmd.split(" ", 1)[1].strip()
            with self.clients_lock:
                for sock, name in self.clients.items():
                    if name == target_name:
                        sock.send(f"CONTROL:INCOMING_CALL:{user}".encode())
                        client_socket.send(b"CONTROL:CALLING...")
                        # mark as pending: caller_socket -> target_socket
                        self.active_calls[client_socket] = sock
                        return
            client_socket.send(b"CONTROL:User not found")

        elif cmd == "/accept":
            # find a pending call where this socket is target
            for caller_socket, target_socket in list(self.active_calls.items()):
                if target_socket == client_socket:
                    # establish call both directions
                    self.active_calls[caller_socket] = client_socket
                    self.active_calls[client_socket] = caller_socket
                    caller_socket.send(b"CONTROL:CALL_ACCEPTED")
                    client_socket.send(b"CONTROL:CALL_ACCEPTED")
                    return
            client_socket.send(b"CONTROL:No call to accept")

        elif cmd == "/reject":
            # find pending caller
            for caller_socket, target_socket in list(self.active_calls.items()):
                if target_socket == client_socket:
                    self.active_calls.pop(caller_socket, None)
                    caller_socket.send(b"CONTROL:CALL_REJECTED")
                    client_socket.send(b"CONTROL:CALL_REJECTED")
                    return
            client_socket.send(b"CONTROL:No call to reject")

        elif cmd == "/end":
            if client_socket in self.active_calls:
                partner = self.active_calls.pop(client_socket)
                # Remove reverse link if exists
                if partner in self.active_calls:
                    self.active_calls.pop(partner, None)
                client_socket.send(b"CONTROL:CALL_ENDED")
                partner.send(b"CONTROL:CALL_ENDED")
            else:
                client_socket.send(b"CONTROL:No active call")

    def broadcast_audio(self, audio_data, sender_socket):
        # Private call routing
        if sender_socket in self.active_calls:
            partner = self.active_calls[sender_socket]
            try:
                partner.send(audio_data)
            except:
                pass
            return

        # Group lobby
        with self.clients_lock:
            for sock in self.clients:
                if sock != sender_socket:
                    try:
                        sock.send(audio_data)
                    except:
                        continue

    def broadcast_control_message(self, message: str, exclude_socket=None):
        with self.clients_lock:
            for sock in self.clients:
                if sock != exclude_socket:
                    try:
                        sock.send(f"CONTROL:{message}".encode())
                    except:
                        continue

    def remove_client(self, client_socket):
        with self.clients_lock:
            if client_socket in self.clients:
                client_name = self.clients[client_socket]
                del self.clients[client_socket]
                logger.info(f"Client disconnected: {client_name}")
                self.broadcast_control_message(f"SERVER: {client_name} left")
            # End any active call involving this client
            if client_socket in self.active_calls:
                partner = self.active_calls.pop(client_socket)
                if partner in self.active_calls:
                    self.active_calls.pop(partner, None)
                partner.send(b"CONTROL:CALL_ENDED")
        client_socket.close()

    def handle_shutdown(self, signum, frame):
        logger.info("Shutting down server...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        with self.clients_lock:
            for client_socket in self.clients:
                client_socket.close()
            self.clients.clear()
        self.server_socket.close()

if __name__ == "__main__":
    server = VoiceServer()
    server.start()