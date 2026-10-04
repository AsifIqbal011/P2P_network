# Peer-to-Peer (P2P) Network Communication and File Sharing

**Course:** CSE 433: Blockchain & Distributed Security Lab  
**Department:** Computer Science and Engineering, University of Asia Pacific (UAP)  
**Implementation:** Python 3 (TCP Sockets, Multi-threading, Tkinter GUI)

---

## 1. Project Description

This project implements a decentralized, lightweight Peer-to-Peer (P2P)network in Python that enables multiple computers or application instances to communicate directly with one another without relying on any central server.

In a traditional client-server architecture, all messages and files route through a central server (A -> Server -> B). If the server fails or goes offline, the entire network halts. In contrast, this P2P architecture treats every participating node as both a TCP Server (accepting incoming connections) and a TCP Client (initiating outgoing connections):

Every Peer= TCP Server+ TCP Client

### Key Features
- **Decentralized Direct Communication:** Direct peer-to-peer TCP socket communication without a central broker.
- **Identity Handshake Protocol:** Automatic exchange of `HELLO` and `HELLO_ACK` packets conveying `peer_id`, `peer_name`, and listening port.
- **Reliable Message Framing:** Custom application protocol utilizing `[4-byte big-endian length prefix] + [JSON payload]` framing over TCP byte streams.
- **Universal Binary File Transfer:** Two-stage file transmission protocol (Stage 1: Metadata JSON; Stage 2: Raw binary streaming in 64 KB chunks). Supports images (`.png`, `.jpg`), audio (`.mp3`), video (`.mp4`), documents (`.pdf`), archives (`.zip`), and arbitrary binary files.
- **Concurrent Multi-Peer Mesh:** Multi-threaded connection handling allowing each peer to maintain simultaneous active connections to multiple peers.
- **Resilient Error Handling:** Graceful handling of network drops, connection refused, port conflicts, duplicate connections, and malformed inputs without crashing.
- **User Interface:** Clean Tkinter GUI with real-time peer listing, color-coded message/event logs, and file transfer progress

---


## 2. Requirements

- **Python Version:** Python 3.9 or higher (Tested on Python 3.13)
- **Operating System:** Windows, macOS, or Linux
- **Dependencies:** Built using Python standard libraries:
  - `socket`: TCP networking primitives
  - `threading`: Concurrent connection and transfer handling
  - `json`: Structured protocol serialization
  - `struct`: 4-byte network byte-order message length framing
  - `tkinter`: Graphical user interface
  - `os`, `sys`, `uuid`, `hashlib`

*No third-party packages are required.*

---

## 3. Installation & Setup Instructions

### Step 1: Create Virtual Environment
Open a terminal in the project directory:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Verify Setup
Verify that Python and standard libraries are available:
```bash
python --version
```

---

## 4. How to Run the Application

### Running the Graphical Interface (GUI)
Start an instance of the peer application:
```bash
python main.py
```

To run multiple peers on the same computer for testing, open separate terminal windows and launch `python main.py` in each.

---

## 5. How to Connect Two Peers

### Testing on the Same Computer (Localhost)
1. **Launch Peer 1 (Alice):**
   - In the **My Peer** section:
     - Name: `Alice`
     - Port: `5000`
   - Click **Start Peer**.
   - The status will show: `Alice [a83f21c4] | Port 5000`.

2. **Launch Peer 2 (Bob):**
   - Open a second terminal window and run `python main.py`.
   - In the **My Peer** section:
     - Name: `Bob`
     - Port: `5001`
   - Click **Start Peer**.

3. **Establish Direct Connection:**
   - On Bob's window, navigate to **Connect to Another Peer**:
     - IP: `127.0.0.1`
     - Port: `5000`
   - Click **Connect**.
   - The `HELLO` handshake will complete immediately.
   - `Alice [a83f21c4] 127.0.0.1:5000` will appear in Bob's **Connected Peers** list.
   - `Bob [92bd71e3] 127.0.0.1:5001` will appear in Alice's **Connected Peers** list.

### Testing Across Two Computers on the Same LAN / Wi-Fi
1. Find Computer A's local IP address (`ipconfig` on Windows or `ifconfig` / `ip a` on Linux/macOS), e.g., `192.168.1.10`.
2. Start Peer A on Computer A with port `5000`.
3. Start Peer B on Computer B with port `5001`.
4. On Computer B, enter IP `192.168.1.10` and Port `5000`, then click **Connect**.

---

## 6. How to Exchange Messages & Transfer Files

### Text Messaging
1. Select the desired peer from the **Connected Peers** listbox on the left.
2. Type your message into the **Send Text** input box.
3. Press `Enter` or click **Send**.
4. Both peers will see the message logged in **Messages / Events**:
   - Sender: `You -> Bob: Hello Bob!`
   - Receiver: `Alice -> You: Hello Bob!`

### File Transfer
1. Select the destination peer from the **Connected Peers** list.
2. Click **Choose File & Send**.
3. Select any file (image `.png`/`.jpg`, audio `.mp3`, video `.mp4`, `.pdf`, `.zip`, `.txt`).
4. The file is streamed in 64 KB chunks.
5. The receiver automatically stores the file in the local `downloads/` directory.
6. The event log confirms:
   - Sender: `You -> Bob: File sent: photo.jpg`
   - Receiver: `Alice -> You: File received: photo.jpg (2456789 bytes)`

---

## 7. Example screenshots

![Screenshot 1](screenshots/Screenshot%202026-10-04%20141708.png)

![Screenshot 2](screenshots/Screenshot%202026-10-04%20141731.png)

![Screenshot 3](screenshots/Screenshot%202026-10-04%20141749.png)

![Screenshot 4](screenshots/Screenshot%202026-10-04%20141932.png)

![Screenshot 5](screenshots/Screenshot%202026-10-04%20142001.png)

![Screenshot 6](screenshots/Screenshot%202026-10-04%20142028.png)

![Screenshot 7](screenshots/Screenshot%202026-10-04%20142126.png)

![Screenshot 8](screenshots/Screenshot%202026-10-04%20142220.png)

![Screenshot 9](screenshots/Screenshot%202026-10-04%20142253.png)

![Screenshot 10](screenshots/Screenshot%202026-10-04%20142317.png)

![Screenshot 11](screenshots/Screenshot%202026-10-04%20142404.png)

![Screenshot 12](screenshots/Screenshot%202026-10-04%20142432.png)

![Screenshot 13](screenshots/Screenshot%202026-10-04%20142446.png)

![Screenshot 14](screenshots/Screenshot%202026-10-04%20142517.png)
---
