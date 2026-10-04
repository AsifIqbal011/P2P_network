import os
import socket
import threading
import uuid
from typing import Callable, Dict, Optional

import protocol


class PeerConnection:
    """Represents an active connection with another peer."""

    def __init__(self,peer_id: str, peer_name: str, sock: socket.socket, remote_ip: str, remote_port: int,
    ):
        self.peer_id = peer_id
        self.peer_name = peer_name
        self.sock = sock
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.send_lock = threading.Lock()
        self.is_active = True

    def display_str(self) -> str:
        return f"{self.peer_name} [{self.peer_id}] ({self.remote_ip}:{self.remote_port})"


class P2PNode:
    """
    Main Peer-to-Peer node capable of listening for incoming connections
    and connecting out to remote peers.
    """

    def __init__(
        self,
        name: str = "Asif",
        port: int = 5000,
        download_dir: str = "downloads",
        on_message: Optional[Callable[[str, str, str], None]] = None,
        on_file_received: Optional[Callable[[str, str, str, str, int], None]] = None,
        on_peer_connected: Optional[Callable[[str, str, str, int], None]] = None,
        on_peer_disconnected: Optional[Callable[[str, str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.name = name
        self.port = port
        self.peer_id = uuid.uuid4().hex[:8]
        self.download_dir = download_dir

        # Callbacks for GUI/event logging
        self.on_message = on_message
        self.on_file_received = on_file_received
        self.on_peer_connected = on_peer_connected
        self.on_peer_disconnected = on_peer_disconnected
        self.on_status = on_status
        self.on_error = on_error

        self.server_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Active peers: peer_id -> PeerConnection
        self.peers: Dict[str, PeerConnection] = {}
        self.peers_lock = threading.Lock()

        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)

    def _log_status(self, message: str) -> None:
        if self.on_status:
            self.on_status(message)

    def _log_error(self, message: str) -> None:
        if self.on_error:
            self.on_error(message)

    def start(self) -> bool:
        """Starts the TCP listening server in a background thread."""
        if self.is_running:
            self._log_error("Peer is already running.")
            return False

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.port))
            self.server_socket.listen(5)
            self.is_running = True

            self.server_thread = threading.Thread(
                target=self._listen_loop,
                name=f"ServerListenThread-{self.port}",
                daemon=True,
            )
            self.server_thread.start()

            self._log_status(
                f"[SYSTEM] Peer started: {self.name} [{self.peer_id}] on port {self.port}"
            )
            return True
        except Exception as e:
            self.is_running = False
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
                self.server_socket = None
            self._log_error(f"[ERROR] Failed to start peer server on port {self.port}: {e}")
            return False

    def stop(self) -> None:
        """Stops the peer server and closes all active peer connections."""
        if not self.is_running:
            return

        self.is_running = False

        # Close all active peer connections
        with self.peers_lock:
            for peer_id, peer in list(self.peers.items()):
                peer.is_active = False
                try:
                    peer.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    peer.sock.close()
                except Exception:
                    pass
            self.peers.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        self._log_status(f"[SYSTEM] Peer stopped.")

    def _listen_loop(self) -> None:
        """Accepts incoming peer connections continuously."""
        while self.is_running and self.server_socket:
            try:
                client_sock, client_addr = self.server_socket.accept()
            except OSError:
                # Socket closed during shutdown
                break
            except Exception as e:
                if self.is_running:
                    self._log_error(f"[ERROR] Accept error: {e}")
                break

            # Handle incoming handshake in a separate thread
            threading.Thread(
                target=self._handle_incoming_handshake,
                args=(client_sock, client_addr),
                daemon=True,
            ).start()

    def _handle_incoming_handshake(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        """Handles incoming HELLO handshake and establishes peer session."""
        try:
            sock.settimeout(10.0)
            hello_msg = protocol.recv_message(sock)
            if hello_msg.get("type") != protocol.MSG_TYPE_HELLO:
                sock.close()
                return

            remote_id = hello_msg.get("peer_id", "unknown")
            remote_name = hello_msg.get("peer_name", "Anonymous")
            remote_listen_port = hello_msg.get("port", addr[1])

            # Check for self-connection
            if remote_id == self.peer_id:
                sock.close()
                return

            # Check if peer is already connected
            with self.peers_lock:
                if remote_id in self.peers:
                    # Already connected
                    sock.close()
                    return

            # Send HELLO_ACK response
            ack_msg = {
                "type": protocol.MSG_TYPE_HELLO_ACK,
                "peer_id": self.peer_id,
                "peer_name": self.name,
                "port": self.port,
            }
            protocol.send_message(sock, ack_msg)

            # Reset timeout for normal communication
            sock.settimeout(None)

            peer = PeerConnection(
                peer_id=remote_id,
                peer_name=remote_name,
                sock=sock,
                remote_ip=addr[0],
                remote_port=remote_listen_port,
            )

            with self.peers_lock:
                self.peers[remote_id] = peer

            self._log_status(f"[SYSTEM] Connected to {remote_name}")
            if self.on_peer_connected:
                self.on_peer_connected(
                    remote_id, remote_name, addr[0], remote_listen_port
                )

            # Enter receiver loop for this peer
            self._peer_receiver_loop(peer)

        except Exception as e:
            try:
                sock.close()
            except Exception:
                pass
            if self.is_running:
                self._log_error(f"[ERROR] Handshake failed with {addr}: {e}")

    def connect_to_peer(self, ip: str, port: int) -> bool:
        """
        Initiates a connection to a remote peer, performs HELLO handshake,
        and starts the receiver thread.
        """
        if not self.is_running:
            self._log_error("[ERROR] Local peer is not running. Start peer first.")
            return False

        # Prevent connecting to oneself
        if (ip in ("127.0.0.1", "localhost", "0.0.0.0")) and port == self.port:
            self._log_error("[ERROR] Cannot connect to your own listening port.")
            return False

        # Run connection attempt in background so GUI doesn't freeze
        threading.Thread(
            target=self._do_connect,
            args=(ip, port),
            daemon=True,
        ).start()
        return True

    def _do_connect(self, ip: str, port: int) -> None:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_sock.settimeout(5.0)
            client_sock.connect((ip, port))

            # Send HELLO message
            hello_msg = {
                "type": protocol.MSG_TYPE_HELLO,
                "peer_id": self.peer_id,
                "peer_name": self.name,
                "port": self.port,
            }
            protocol.send_message(client_sock, hello_msg)

            # Wait for HELLO_ACK
            ack_msg = protocol.recv_message(client_sock)
            if ack_msg.get("type") != protocol.MSG_TYPE_HELLO_ACK:
                raise ValueError("Invalid handshake response from peer.")

            remote_id = ack_msg.get("peer_id", "unknown")
            remote_name = ack_msg.get("peer_name", "Anonymous")
            remote_port = ack_msg.get("port", port)

            with self.peers_lock:
                if remote_id in self.peers:
                    client_sock.close()
                    self._log_status(
                        f"[SYSTEM] Already connected to {remote_name} [{remote_id}]."
                    )
                    return

                # Remove socket timeout for ongoing traffic
                client_sock.settimeout(None)

                peer = PeerConnection(
                    peer_id=remote_id,
                    peer_name=remote_name,
                    sock=client_sock,
                    remote_ip=ip,
                    remote_port=remote_port,
                )
                self.peers[remote_id] = peer

            self._log_status(f"[SYSTEM] Connected to {remote_name}")
            if self.on_peer_connected:
                self.on_peer_connected(remote_id, remote_name, ip, remote_port)

            # Start receiver loop for this connection
            self._peer_receiver_loop(peer)

        except ConnectionRefusedError:
            try:
                client_sock.close()
            except Exception:
                pass
            self._log_error("[ERROR] Connection failed: Connection refused")
        except (socket.timeout, TimeoutError):
            try:
                client_sock.close()
            except Exception:
                pass
            self._log_error("[ERROR] Connection failed: Connection timed out")
        except Exception as e:
            try:
                client_sock.close()
            except Exception:
                pass
            self._log_error(f"[ERROR] Connection failed to {ip}:{port}: {e}")

    def _peer_receiver_loop(self, peer: PeerConnection) -> None:
        """Continuously reads incoming messages or files from a peer."""
        while self.is_running and peer.is_active:
            try:
                msg = protocol.recv_message(peer.sock)
                msg_type = msg.get("type")

                if msg_type == protocol.MSG_TYPE_TEXT:
                    sender_id = msg.get("sender_id", peer.peer_id)
                    sender_name = msg.get("sender_name", peer.peer_name)
                    text = msg.get("message", "")
                    if self.on_message:
                        self.on_message(sender_id, sender_name, text)

                elif msg_type == protocol.MSG_TYPE_FILE:
                    sender_id = msg.get("sender_id", peer.peer_id)
                    sender_name = msg.get("sender_name", peer.peer_name)
                    filename = os.path.basename(msg.get("filename", "received_file"))
                    filesize = int(msg.get("filesize", 0))

                    # Prevent file overwrite by appending duplicate counter if needed
                    save_path = os.path.join(self.download_dir, filename)
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(save_path):
                        save_path = os.path.join(
                            self.download_dir, f"{base}_{counter}{ext}"
                        )
                        counter += 1

                    # Receive raw bytes
                    protocol.recv_file_data(peer.sock, save_path, filesize)

                    saved_filename = os.path.basename(save_path)
                    if self.on_file_received:
                        self.on_file_received(
                            sender_id, sender_name, saved_filename, save_path, filesize
                        )

                elif msg_type == protocol.MSG_TYPE_DISCONNECT:
                    break

            except (ConnectionResetError, EOFError, OSError):
                # Peer disconnected or socket closed
                break
            except Exception as e:
                if self.is_running and peer.is_active:
                    self._log_error(f"[ERROR] Error receiving from {peer.peer_name}: {e}")
                break

        # Cleanup peer connection
        self._disconnect_peer(peer)

    def _disconnect_peer(self, peer: PeerConnection) -> None:
        """Cleans up a disconnected peer."""
        with self.peers_lock:
            if peer.peer_id in self.peers:
                del self.peers[peer.peer_id]
        peer.is_active = False
        try:
            peer.sock.close()
        except Exception:
            pass

        self._log_status(f"[SYSTEM] Peer disconnected: {peer.peer_name}")
        if self.on_peer_disconnected:
            self.on_peer_disconnected(peer.peer_id, peer.peer_name)

    def send_text(self, peer_id: str, text: str) -> bool:
        """Sends a text message to a specific connected peer."""
        if not text.strip():
            return False

        with self.peers_lock:
            peer = self.peers.get(peer_id)

        if not peer:
            self._log_error("[ERROR] Attempting to send without selecting a peer.")
            return False

        payload = {
            "type": protocol.MSG_TYPE_TEXT,
            "sender_id": self.peer_id,
            "sender_name": self.name,
            "message": text,
        }

        try:
            with peer.send_lock:
                protocol.send_message(peer.sock, payload)
            return True
        except Exception as e:
            self._log_error(f"[ERROR] Failed to send text to {peer.peer_name}: {e}")
            self._disconnect_peer(peer)
            return False

    def send_file(
        self,
        peer_id: str,
        filepath: str,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Transfers a file to a specific connected peer in two stages:
        Stage 1: Send metadata JSON
        Stage 2: Send raw binary bytes in chunks
        """
        if not os.path.isfile(filepath):
            self._log_error(f"[ERROR] File does not exist: {filepath}")
            return False

        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        with self.peers_lock:
            peer = self.peers.get(peer_id)

        if not peer:
            self._log_error("[ERROR] Attempting to send without selecting a peer.")
            return False

        metadata = {
            "type": protocol.MSG_TYPE_FILE,
            "sender_id": self.peer_id,
            "sender_name": self.name,
            "filename": filename,
            "filesize": filesize,
        }

        try:
            with peer.send_lock:
                # Stage 1: Send Metadata
                protocol.send_message(peer.sock, metadata)

                # Stage 2: Stream raw bytes in chunks
                def chunk_cb(sent_bytes):
                    if progress_cb:
                        progress_cb(sent_bytes, filesize)

                protocol.send_file_data(peer.sock, filepath, progress_cb=chunk_cb)
            return True
        except Exception as e:
            self._log_error(f"[ERROR] Failed to send file to {peer.peer_name}: {e}")
            self._disconnect_peer(peer)
            return False

    def get_peer(self, peer_id: str) -> Optional[PeerConnection]:
        with self.peers_lock:
            return self.peers.get(peer_id)

    def get_connected_peers(self) -> list[PeerConnection]:
        with self.peers_lock:
            return list(self.peers.values())
