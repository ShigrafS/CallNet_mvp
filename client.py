import socket
import threading
import pyaudio
import signal
import sys
from termcolor import colored
import time
import argparse

class VoiceClient:
    # Audio parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = True
        self.name = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio = pyaudio.PyAudio()
        
        # Set up audio streams
        self.input_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        self.output_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            output=True,
            frames_per_buffer=self.CHUNK
        )
        
        # Connect to server
        print(colored(f"Connecting to voice server at {host}:{port}...", "yellow"))
        try:
            self.sock.connect((host, port))
        except ConnectionRefusedError:
            print(colored("Connection refused. Make sure the server is running.", "red"))
            self.cleanup()
            sys.exit(1)
        print(colored("Connected to voice server.", "green"))
        
    def start(self):
        """Start the voice client"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.handle_signal)
        
        # Get user's name
        while not self.name:
            self.name = input(colored("Enter your name: ", "blue")).strip()
            
        # Send name to server
        self.sock.send(f"NAME:{self.name}".encode())
        
        # Start audio threads
        receive_thread = threading.Thread(target=self.receive_audio)
        send_thread = threading.Thread(target=self.send_audio)
        
        receive_thread.daemon = True
        send_thread.daemon = True
        
        receive_thread.start()
        send_thread.start()
        
        print(colored("Voice chat started! Press Ctrl+C to exit.", "yellow"))
        
        # Keep main thread alive (cross-platform)
        try:
            while self.running:
                time.sleep(0.1)  # Sleep briefly to prevent high CPU usage
        except KeyboardInterrupt:
            self.handle_signal(None, None)

    def send_audio(self):
        """Capture and send audio to server"""
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
        """Receive and play audio from server"""
        while self.running:
            try:
                data = self.sock.recv(self.CHUNK * 2)
                if not data:
                    break
                    
                # Check for control messages
                if data.startswith(b"CONTROL:"):
                    message = data[8:].decode()
                    print(colored(message, "cyan"))
                    continue
                    
                # Check for server full message
                if data == b"SERVER_FULL":
                    print(colored("Server is full. Try again later.", "red"))
                    self.running = False
                    break
                    
                # Play audio data
                self.output_stream.write(data)
                
            except Exception as e:
                if self.running:
                    print(colored(f"Error receiving audio: {e}", "red"))
                break
                
    def handle_signal(self, signum, frame):
        """Handle Ctrl+C"""
        print(colored("\nExiting voice chat...", "yellow"))
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if hasattr(self, 'input_stream'):
            self.input_stream.stop_stream()
            self.input_stream.close()
        if hasattr(self, 'output_stream'):
            self.output_stream.stop_stream()
            self.output_stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        if hasattr(self, 'sock'):
            self.sock.close()
            
def main():
    parser = argparse.ArgumentParser(description='Voice Chat Client')
    parser.add_argument('host', help='server address')
    parser.add_argument('port', type=int, help='server port')
    args = parser.parse_args()
    
    client = VoiceClient(args.host, args.port)
    client.start()
    
if __name__ == "__main__":
    main()