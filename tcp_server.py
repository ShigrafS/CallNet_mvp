import socket
import threading
from typing import List
import socket
from threading import Lock
import dns.resolver
import dns.reversename

MAX_CLIENTS = 10

class ClientHandler:
    def __init__(self):
        self.clients: List[socket.socket] = []
        self.clients_lock = Lock()

    def handle_client(self, client_socket: socket.socket):
        """Handle individual client connections."""
        try:
            while True:
                # Receive data from client
                data = client_socket.recv(1024)
                if not data:
                    print("Client disconnected.")
                    break

                # Broadcast to all other clients
                with self.clients_lock:
                    # Remove dead sockets
                    self.remove_dead_clients()
                    
                    # Send message to all other clients
                    for other_socket in self.clients:
                        if other_socket != client_socket:
                            try:
                                other_socket.send(data)
                            except:
                                continue
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # Remove client from list
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()

    def remove_dead_clients(self):
        """Remove disconnected clients from the list."""
        self.clients = [client for client in self.clients if self._is_socket_connected(client)]

    def _is_socket_connected(self, sock: socket.socket) -> bool:
        """Check if a socket is still connected."""
        try:
            sock.getpeername()
            return True
        except:
            return False

    def add_client(self, client_socket: socket.socket) -> bool:
        """Add a new client to the list if space available."""
        with self.clients_lock:
            if len(self.clients) >= MAX_CLIENTS:
                return False
            self.clients.append(client_socket)
            return True

def lookup_addr(ip_addr: str) -> str:
    """Perform reverse DNS lookup."""
    try:
        addr = dns.reversename.from_address(ip_addr)
        return str(dns.resolver.resolve(addr, "PTR")[0])
    except Exception:
        return None

def main():
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind and listen
    server_address = ('0.0.0.0', 8080)
    server_socket.bind(server_address)
    server_socket.listen(10)
    
    print(f"Server listening on port 8080 (max {MAX_CLIENTS} clients)...")

    client_handler = ClientHandler()

    try:
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                ip_addr = client_address[0]
                
                # Try to get hostname
                hostname = lookup_addr(ip_addr)
                if hostname:
                    print(f"New connection from {client_address} ({hostname})")
                else:
                    print(f"New connection from {client_address}")

                # Check if we can add more clients
                if not client_handler.add_client(client_socket):
                    print(f"Max clients reached. Rejecting {client_address}")
                    client_socket.send(b"Server full.\n")
                    client_socket.close()
                    continue

                # Start new thread for client
                client_thread = threading.Thread(
                    target=client_handler.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                print(f"Connection failed: {e}")

    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()