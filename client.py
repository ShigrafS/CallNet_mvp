import socket
import threading
import pyaudio
import signal
import sys
from termcolor import colored
import time
import argparse

# NEW: import register from the register_client file
from register_client import register

class VoiceClient:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    def __init__(self, host, port):
        # FIRST: perform registration and store the assigned number
        try:
            response = register()  # this prints and returns a number by default
            assigned = None

            # If response is a dict: extract number
            if isinstance(response, dict):
                assigned = response.get("number")
            # If it's a string (JSON text etc.), store it anyway
            elif isinstance(response, str):
                assigned = response
            self.assigned_number = assigned
            if assigned:
                print(colored(f"✓ Device registered. Assigned Number: {assigned}", "green"))
        except Exception as e:
            print(colored(f"[!] Registration failed: {e}", "red"))
            self.assigned_number = None

        self.host = host
        self.port = port
        self.running = True
        self.name = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio = pyaudio.PyAudio()
        self.call_active = False

        self.input_stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True,
            frames_per_buffer=self.CHUNK
        )
        self.output_stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, output=True,
            frames_per_buffer=self.CHUNK
        )

        print(colored(f"Connecting to voice server at {host}:{port}...", "yellow"))
        try:
            self.sock.connect((host, port))
        except ConnectionRefusedError:
            print(colored("Connection refused. Make sure the server is running.", "red"))
            self.cleanup()
            sys.exit(1)
        print(colored("Connected to voice server.", "green"))

    def start(self):
        signal.signal(signal.SIGINT, self.handle_signal)

        # Ask user name
        while not self.name:
            self.name = input(colored("Enter your name: ", "blue")).strip()

        # Attach assigned number
        if self.assigned_number:
            self.name = f"{self.name}#{self.assigned_number}"

        self.sock.send(f"NAME:{self.name}".encode())

        receive_thread = threading.Thread(target=self.receive_audio, daemon=True)
        send_thread = threading.Thread(target=self.send_audio, daemon=True)
        text_thread = threading.Thread(target=self.user_input_loop, daemon=True)

        receive_thread.start()
        send_thread.start()
        text_thread.start()

        print(colored("Voice chat started! Press Ctrl+C to exit.", "yellow"))

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.handle_signal(None, None)

    def send_audio(self):
        while self.running:
            try:
                data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                if self.running:
                    self.sock.send(data)
            except Exception as e:
                if self.running:
                    print(colored(f"Error sending audio: {e}", "red"))
                break

    def receive_audio(self):
        while self.running:
            try:
                data = self.sock.recv(self.CHUNK * 2)
                if not data:
                    break

                # Handle control / text messages
                if data.startswith(b"CONTROL:"):
                    message = data[8:].decode()

                    if message.startswith("INCOMING_CALL:"):
                        caller = message[len("INCOMING_CALL:"):]
                        print(colored(f"[!] Incoming call from {caller}. Type /accept or /reject", "cyan"))

                    elif message == "CALL_ACCEPTED":
                        self.call_active = True
                        print(colored("[✓] Call accepted!", "green"))

                    elif "CALL_ENDED" in message or "CALL_REJECTED" in message:
                        self.call_active = False
                        print(colored("[!] Call ended or rejected.", "red"))

                    else:
                        print(colored(message, "cyan"))
                    continue

                # If actual audio
                if self.call_active or True:
                    self.output_stream.write(data)

            except Exception as e:
                if self.running:
                    print(colored(f"Error receiving audio: {e}", "red"))
                break

    def user_input_loop(self):
        """Handle slash commands from user (text)"""
        while self.running:
            cmd = input().strip()
            if cmd:
                if cmd == "/quit":
                    self.handle_signal(None, None)
                else:
                    self.sock.send(cmd.encode())

    def handle_signal(self, signum, frame):
        print(colored("\nExiting voice chat...", "yellow"))
        self.running = False
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        self.running = False
        if hasattr(self, 'input_stream'):
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
        if hasattr(self, 'output_stream'):
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
        if hasattr(self, 'audio'):
            try:
                self.audio.terminate()
            except:
                pass
        if hasattr(self, 'sock'):
            try:
                self.sock.close()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description='Voice Chat Client')
    parser.add_argument('host', help='server address')
    parser.add_argument('port', type=int, help='server port')
    args = parser.parse_args()

    client = VoiceClient(args.host, args.port)
    client.start()

if __name__ == "__main__":
    main()
