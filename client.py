import argparse
import socket
import threading
import signal
import sys
from termcolor import colored
import os

def clear_line():
    # Function to clear the current line in the terminal
    if os.name == 'nt':  # for Windows
        print('\r', end='')
    else:  # for Unix/Linux/MacOS
        print('\033[2K\r', end='')

class ChatClient:
    def __init__(self, host, port):
        self.running = True
        self.name = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(colored(f"Connecting to {host}:{port}...", "yellow"))
        try:
            self.sock.connect((host, port))
        except ConnectionRefusedError:
            print(colored("Connection refused. Make sure the server is running.", "red"))
            sys.exit(1)
        print(colored("Connected.", "yellow"))

    def handle_signal(self, signum, frame):
        print('\n' + colored("Received Ctrl+C, exiting...", "yellow"))
        self.running = False
        self.sock.close()
        sys.exit(0)

    def reader_thread(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode().strip()
                if not message:
                    print('\n' + colored("Connection closed by server.", "yellow"))
                    self.running = False
                    break

                clear_line()  # Clear the current input line
                if message.startswith(f"{self.name}:"):
                    # Our own message echoed back
                    content = message[len(f"{self.name}: "):]
                    print(f"\n{colored('You:', 'green', attrs=['bold'])} {content}")
                elif ': ' in message:
                    # Message from other users
                    prefix, rest = message.split(': ', 1)
                    print(f"\n{colored(prefix, 'cyan', attrs=['bold'])} {rest}")
                else:
                    # System message or unknown format
                    print(f"\n{message}")
                
                print(colored("You: ", "blue"), end='', flush=True)

            except ConnectionError:
                print('\n' + colored("Connection lost.", "yellow"))
                self.running = False
                break
            except Exception as e:
                print(f"\nError reading from server: {e}")
                self.running = False
                break

    def handle_command(self, command, arg=None):
        if command in ['/quit', '/exit']:
            print(colored("Exiting chat...", "yellow"))
            self.running = False
            return True
        elif command == '/name':
            if arg:
                new_name = arg.strip()
                if new_name:
                    self.name = new_name
                    print(colored("Name changed to ", "green") + 
                          colored(new_name, "green", attrs=['bold']))
                else:
                    print(colored("Usage: /name NEWNAME", "yellow"))
            else:
                print(colored("Usage: /name NEWNAME", "yellow"))
            return True
        else:
            print(colored("Unknown command. Available commands: /name, /quit, /exit", "yellow"))
            return True
        return False

    def run(self):
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.handle_signal)

        # Get user's name
        print(colored("Please Enter Your Name: ", "blue"), end='', flush=True)
        self.name = input().strip()

        print(colored("You can start sending messages now. Type and press Enter.", "yellow"))

        # Start reader thread
        reader = threading.Thread(target=self.reader_thread)
        reader.daemon = True
        reader.start()

        # Main loop for sending messages
        while self.running:
            try:
                print(colored("You: ", "blue"), end='', flush=True)
                message = input().strip()

                if message.startswith('/'):
                    # Handle commands
                    parts = message.split(maxsplit=1)
                    command = parts[0]
                    arg = parts[1] if len(parts) > 1 else None
                    if self.handle_command(command, arg):
                        continue

                # Send regular message
                full_message = f"{self.name}: {message}\n"
                self.sock.send(full_message.encode())

            except (EOFError, KeyboardInterrupt):
                print('\n' + colored("EOF detected, exiting...", "yellow"))
                break
            except Exception as e:
                print(f"Error sending message: {e}")
                break

        print(colored("Closing connection.", "yellow"))
        self.sock.close()

def main():
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('host', help='server address')
    parser.add_argument('port', type=int, help='server port')
    args = parser.parse_args()

    client = ChatClient(args.host, args.port)
    client.run()

if __name__ == "__main__":
    main()