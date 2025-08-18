import socket
import threading
from typing import List, Dict
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_CLIENTS = 10
CHUNK_SIZE = 4096  # Larger chunk size for audio data

class VoiceServer:
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.clients: Dict[socket.socket, str] = {}  # Socket to client name mapping
        self.clients_lock = threading.Lock()
        self.running = True
        
        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def start(self):
        """Start the voice server"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CLIENTS)
            logger.info(f"Voice Server listening on port {self.port} (max {MAX_CLIENTS} clients)...")
            
            # Handle Ctrl+C gracefully
            signal.signal(signal.SIGINT, self.handle_shutdown)
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    if len(self.clients) >= MAX_CLIENTS:
                        logger.info(f"Max clients reached. Rejecting {client_address}")
                        client_socket.send(b"SERVER_FULL")
                        client_socket.close()
                        continue
                        
                    # Start new client thread
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
            
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        try:
            # First message should be the client's name
            name_data = client_socket.recv(1024).decode()
            if name_data.startswith("NAME:"):
                client_name = name_data[5:]
                with self.clients_lock:
                    self.clients[client_socket] = client_name
                logger.info(f"New client connected: {client_name} from {address}")
                
                # Broadcast join notification
                self.broadcast_control_message(f"SERVER: {client_name} joined", client_socket)
                
                while self.running:
                    # Receive audio data
                    audio_data = client_socket.recv(CHUNK_SIZE)
                    if not audio_data:
                        break
                        
                    # Broadcast to other clients
                    self.broadcast_audio(audio_data, client_socket)
                    
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            self.remove_client(client_socket)
            
    def broadcast_audio(self, audio_data: bytes, sender_socket: socket.socket):
        """Broadcast audio data to all other clients"""
        with self.clients_lock:
            for client_socket in self.clients:
                if client_socket != sender_socket:
                    try:
                        client_socket.send(audio_data)
                    except:
                        continue
                        
    def broadcast_control_message(self, message: str, exclude_socket=None):
        """Broadcast control messages to clients"""
        with self.clients_lock:
            for client_socket in self.clients:
                if client_socket != exclude_socket:
                    try:
                        client_socket.send(f"CONTROL:{message}".encode())
                    except:
                        continue
                        
    def remove_client(self, client_socket: socket.socket):
        """Remove a client and cleanup"""
        with self.clients_lock:
            if client_socket in self.clients:
                client_name = self.clients[client_socket]
                del self.clients[client_socket]
                logger.info(f"Client disconnected: {client_name}")
                self.broadcast_control_message(f"SERVER: {client_name} left")
        client_socket.close()
        
    def handle_shutdown(self, signum, frame):
        """Handle server shutdown"""
        logger.info("Shutting down server...")
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """Cleanup server resources"""
        with self.clients_lock:
            for client_socket in self.clients:
                client_socket.close()
            self.clients.clear()
        self.server_socket.close()
        
if __name__ == "__main__":
    server = VoiceServer()
    server.start()