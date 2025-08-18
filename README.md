# Simple Python Chat Application

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A lightweight terminal-based chat application implemented in Python using TCP sockets. It consists of a server and client that allow multiple users to chat in real-time over the network.

---

## Features

- Multi-client support (up to 10 simultaneous clients)
- User-friendly terminal interface with colored output
- Change your username on the fly with `/name` command
- Graceful handling of Ctrl+C and connection loss
- Reverse DNS lookup of client IP addresses on the server
- Broadcasts messages to all connected clients
- Distinguishes your own messages from others in the client UI

---

## Requirements

- Python 3.7 or newer
- [termcolor](https://pypi.org/project/termcolor/) — for colored terminal output
- [dnspython](https://pypi.org/project/dnspython/) — for reverse DNS lookup on server

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/ShigrafS/CallNet_mvp.git
   cd CallNet_mvp

2. Install dependencies:

   ```bash
   pip install termcolor dnspython
   ```

---

## Usage

### Start the Server

By default, the server listens on all interfaces (`0.0.0.0`) and port `8080`.

```bash
python server.py
```

Example output:

```
Server listening on port 8080 (max 10 clients)...
```

---

### Connect with a Client

Run the client with the server IP (or hostname) and port:

```bash
python client.py SERVER_IP 8080
```

Example connecting to a server on the same machine:

```bash
python client.py 127.0.0.1 8080
```

---

### Client Workflow

1. **Enter your display name** when prompted:

   ```
   Please Enter Your Name:
   ```

2. **Start chatting** by typing messages after the prompt:

   ```
   You:
   ```

3. **Incoming messages** from others show the sender's name in cyan bold text.

4. **Your own messages** are shown as `You:` in green bold text.

---

### Supported Client Commands

| Command            | Description                     | Example       |
| ------------------ | ------------------------------- | ------------- |
| `/name NEWNAME`    | Change your display name        | `/name Alice` |
| `/quit` or `/exit` | Exit the chat client gracefully | `/quit`       |

---

## Server Behavior

* Attempts reverse DNS lookup on client IPs.
* Rejects new clients when max capacity (default 10) is reached.
* Broadcasts all client messages to every other client.
* Cleans up disconnected clients automatically.
* Stop the server with `Ctrl+C` (SIGINT) to shut down gracefully.

---

## Notes

* Make sure client and server ports match.
* Open firewall ports if connecting across networks.
* The client expects newline (`\n`) delimited messages.
* The server currently does not echo your own messages back; clients show your messages locally.
* Use terminals that support ANSI colors for the best experience.

---

## Troubleshooting

| Issue                  | Possible Cause / Solution                                              |
| ---------------------- | ---------------------------------------------------------------------- |
| Connection refused     | Server not running or wrong IP/port                                    |
| "Server full." message | Maximum clients reached; wait or increase `MAX_CLIENTS` in `server.py` |
| No messages appearing  | Make sure you entered your name and typed messages correctly           |
| Reverse DNS errors     | Normal if client IP has no PTR record                                  |

---

## Customization

* Modify `MAX_CLIENTS` in `server.py` to change max clients.
* Change `server_address` tuple in `server.py` to use a different port or bind address.
* Extend client or server for more commands or encryption.

---

## License

This project is provided as-is for learning and demo purposes.

---

*Feel free to contribute or open issues if you find bugs or want features!*

---

**Happy chatting!** 🎉


