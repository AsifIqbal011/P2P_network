import json
import os
import struct
import socket

# Standard chunk size for reading and sending files
CHUNK_SIZE = 64 * 1024

# Message Types
MSG_TYPE_HELLO = "hello"
MSG_TYPE_HELLO_ACK = "hello_ack"
MSG_TYPE_TEXT = "text"
MSG_TYPE_FILE = "file"
MSG_TYPE_DISCONNECT = "disconnect"


def recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Receives exactly `num_bytes` bytes from the socket.
    Raises ConnectionError if the connection is closed before all bytes are received.
    """
    buffer = bytearray()
    while len(buffer) < num_bytes:
        packet = sock.recv(min(num_bytes - len(buffer), 4096))
        if not packet:
            raise ConnectionResetError("Connection closed unexpectedly while receiving data.")
        buffer.extend(packet)
    return bytes(buffer)


def send_message(sock: socket.socket, msg_dict: dict) -> None:
    """
    Encodes a dictionary as a JSON string and sends it with a 4-byte big-endian length prefix.
    Format: [4-byte length][JSON payload]
    """
    json_bytes = json.dumps(msg_dict).encode("utf-8")
    length_prefix = struct.pack("!I", len(json_bytes))
    sock.sendall(length_prefix + json_bytes)


def recv_message(sock: socket.socket) -> dict:
    """
    Reads a 4-byte length prefix and then reads exactly that many bytes of JSON payload.
    Parses and returns the dictionary.
    """
    length_prefix = recv_exact(sock, 4)
    (msg_length,) = struct.unpack("!I", length_prefix)
    json_bytes = recv_exact(sock, msg_length)
    return json.loads(json_bytes.decode("utf-8"))


def send_file_data(sock: socket.socket, filepath: str, chunk_size: int = CHUNK_SIZE, progress_cb=None) -> int:
    """
    Sends the raw bytes of a file in chunks over the socket.
    Returns total bytes sent.
    """
    total_sent = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sock.sendall(chunk)
            total_sent += len(chunk)
            if progress_cb:
                progress_cb(total_sent)
    return total_sent


def recv_file_data(sock: socket.socket, save_path: str, filesize: int, chunk_size: int = CHUNK_SIZE, progress_cb=None) -> None:
    """
    Reads exactly `filesize` bytes in chunks from the TCP stream and writes them to `save_path`.
    """
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    
    received_bytes = 0
    with open(save_path, "wb") as f:
        while received_bytes < filesize:
            bytes_to_read = min(chunk_size, filesize - received_bytes)
            chunk = sock.recv(bytes_to_read)
            if not chunk:
                raise ConnectionResetError(
                    f"Connection closed during file transfer ({received_bytes}/{filesize} bytes received)."
                )
            f.write(chunk)
            received_bytes += len(chunk)
            if progress_cb:
                progress_cb(received_bytes, filesize)
