import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Optional

from p2p_node import P2PNode, PeerConnection


class P2PApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("UAP P2P Network")
        self.geometry("820x700")
        self.minsize(720, 560)

        # Peer node instance
        self.node: Optional[P2PNode] = None
        self.download_dir = os.path.abspath("downloads")
        os.makedirs(self.download_dir, exist_ok=True)

        # Peer map: listbox index / display text -> peer_id
        self.peer_display_map: dict[str, str] = {}

        self._init_style()
        self._build_ui()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("xpnative")
        except Exception:
            pass

    def _build_ui(self):
        main_container = ttk.Frame(self, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. My Peer Section
        peer_frame = ttk.LabelFrame(main_container, text="My Peer", padding=8)
        peer_frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(peer_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_name = ttk.Entry(row1, width=16)
        self.entry_name.insert(0, "Asif")
        self.entry_name.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row1, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_port = ttk.Entry(row1, width=8)
        self.entry_port.insert(0, "5000")
        self.entry_port.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_start = ttk.Button(
            row1, text="Start", command=self._start_peer
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_stop = ttk.Button(
            row1, text="Stop", command=self._stop_peer, state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT)

        # Node Status Info Label
        self.lbl_peer_info = ttk.Label(
            peer_frame,
            text="Status: Not started",
            font=("Segoe UI", 9, "italic"),
            foreground="#868687",
        )
        self.lbl_peer_info.pack(anchor=tk.W, pady=(5, 0))

        # 2. Connect to Another Peer Section
        connect_frame = ttk.LabelFrame(
            main_container, text="Connect to Another Peer", padding=8
        )
        connect_frame.pack(fill=tk.X, pady=(0, 8))

        crow = ttk.Frame(connect_frame)
        crow.pack(fill=tk.X, pady=2)

        ttk.Label(crow, text="IP:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_remote_ip = ttk.Entry(crow, width=18)
        self.entry_remote_ip.insert(0, "127.0.0.1")
        self.entry_remote_ip.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(crow, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_remote_port = ttk.Entry(crow, width=8)
        self.entry_remote_port.insert(0, "5001")
        self.entry_remote_port.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_connect = ttk.Button(
            crow, text="Connect", command=self._connect_peer, state=tk.DISABLED
        )
        self.btn_connect.pack(side=tk.LEFT)

        # 3. Middle Area: Connected Peers (Left) & Messages/Events (Right)
        middle_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        middle_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Left: Connected Peers List
        peers_container = ttk.LabelFrame(
            middle_paned, text="Connected Peers", padding=5
        )
        middle_paned.add(peers_container, weight=1)

        peers_scroll_frame = ttk.Frame(peers_container)
        peers_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.peer_listbox = tk.Listbox(
            peers_scroll_frame,
            selectmode=tk.SINGLE,
            font=("Segoe UI", 9),
            exportselection=False,
            height=12,
        )
        self.peer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        peer_scrollbar = ttk.Scrollbar(
            peers_scroll_frame, orient=tk.VERTICAL, command=self.peer_listbox.yview
        )
        peer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.peer_listbox.config(yscrollcommand=peer_scrollbar.set)

        # Right: Messages / Events
        events_container = ttk.LabelFrame(
            middle_paned, text="Messages / Files", padding=5
        )
        middle_paned.add(events_container, weight=3)

        self.text_events = ScrolledText(
            events_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED,
            background="#FAFAFA",
        )
        self.text_events.pack(fill=tk.BOTH, expand=True)

        # Text tags for coloring
        self.text_events.tag_config("SYSTEM", foreground="#0055AA", font=("Consolas", 10, "bold"))
        self.text_events.tag_config("ERROR", foreground="#CC0000", font=("Consolas", 10, "bold"))
        self.text_events.tag_config("INCOMING", foreground="#008000")
        self.text_events.tag_config("OUTGOING", foreground="#333333")
        self.text_events.tag_config("FILE_INFO", foreground="#8B008B", font=("Consolas", 10, "bold"))

        # 4. Bottom Controls: Send Text & Send File
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X, pady=(0, 4))

        # Send Text Row
        text_row = ttk.Frame(bottom_frame)
        text_row.pack(fill=tk.X, pady=3)

        ttk.Label(text_row, text="Send Text:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_message = ttk.Entry(text_row)
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_message.bind("<Return>", lambda e: self._send_text())

        self.btn_send = ttk.Button(
            text_row, text="Send", command=self._send_text, state=tk.DISABLED
        )
        self.btn_send.pack(side=tk.RIGHT)

        # Send File Row
        file_row = ttk.Frame(bottom_frame)
        file_row.pack(fill=tk.X, pady=3)

        ttk.Label(
            file_row,
            text="Text, image, audio, video, PDF, ZIP, etc.",
            foreground="#004E92",
            font=("Segoe UI", 9, "italic"),
        ).pack(side=tk.LEFT)

        self.btn_choose_file = ttk.Button(
            file_row,
            text="Choose File & Send",
            command=self._send_file,
            state=tk.DISABLED,
        )
        self.btn_choose_file.pack(side=tk.RIGHT)

        # 5. Status Bar
        self.status_bar = ttk.Label(
            self,
            text="Ready. Start peer to begin.",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(6, 2),
            font=("Segoe UI", 8),
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # Logging and UI Helpers (Thread-Safe)
    def log_event(self, text: str, tag: Optional[str] = None):
        """Thread-safe event logging into ScrolledText."""
        self.after(0, self._append_event_text, text, tag)

    def _append_event_text(self, text: str, tag: Optional[str]):
        self.text_events.config(state=tk.NORMAL)
        if tag:
            self.text_events.insert(tk.END, text + "\n", tag)
        else:
            self.text_events.insert(tk.END, text + "\n")
        self.text_events.see(tk.END)
        self.text_events.config(state=tk.DISABLED)

    def set_status(self, text: str):
        """Thread-safe update to bottom status bar."""
        self.after(0, self.status_bar.config, {"text": text})

    def refresh_peers_list(self):
        """Refreshes the Connected Peers listbox from node state."""
        if not self.node:
            return

        peers = self.node.get_connected_peers()
        selected_id = self._get_selected_peer_id()

        self.peer_listbox.delete(0, tk.END)
        self.peer_display_map.clear()

        new_selected_idx = 0
        for idx, peer in enumerate(peers):
            display = f"{peer.peer_name} [{peer.peer_id}] {peer.remote_ip}:{peer.remote_port}"
            self.peer_listbox.insert(tk.END, display)
            self.peer_display_map[display] = peer.peer_id
            if peer.peer_id == selected_id:
                new_selected_idx = idx

        # Maintain selection or auto-select if at least one peer exists
        if peers:
            self.peer_listbox.selection_clear(0, tk.END)
            self.peer_listbox.selection_set(new_selected_idx)
            self.peer_listbox.activate(new_selected_idx)

    def _get_selected_peer_id(self) -> Optional[str]:
        selection = self.peer_listbox.curselection()
        if not selection:
            # If there is exactly one peer, fallback to it
            if self.node:
                peers = self.node.get_connected_peers()
                if len(peers) == 1:
                    return peers[0].peer_id
            return None
        selected_text = self.peer_listbox.get(selection[0])
        return self.peer_display_map.get(selected_text)

    # Action Handlers
    def _start_peer(self):
        name = self.entry_name.get().strip()
        port_str = self.entry_port.get().strip()

        if not name:
            messagebox.showwarning("Validation Error", "Please enter a peer name.")
            return

        try:
            port = int(port_str)
            if not (1024 <= port <= 65535):
                raise ValueError("Port must be between 1024 and 65535.")
        except ValueError as e:
            messagebox.showerror("Invalid Port", f"Invalid port number: {e}")
            return

        self.node = P2PNode(
            name=name,
            port=port,
            download_dir=self.download_dir,
            on_message=self._on_message_received,
            on_file_received=self._on_file_received,
            on_peer_connected=self._on_peer_connected,
            on_peer_disconnected=self._on_peer_disconnected,
            on_status=self._on_node_status,
            on_error=self._on_node_error,
        )

        success = self.node.start()
        if success:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_connect.config(state=tk.NORMAL)
            self.btn_send.config(state=tk.NORMAL)
            self.btn_choose_file.config(state=tk.NORMAL)
            self.entry_name.config(state=tk.DISABLED)
            self.entry_port.config(state=tk.DISABLED)

            self.lbl_peer_info.config(
                text=f"{self.node.name} [{self.node.peer_id}] | Port {self.node.port}",
                foreground="#006600",
            )
            self.set_status(f"Peer started: {self.node.name} [{self.node.peer_id}] on port {self.node.port}")

    def _stop_peer(self):
        if self.node:
            self.node.stop()
            self.node = None

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_connect.config(state=tk.DISABLED)
        self.btn_send.config(state=tk.DISABLED)
        self.btn_choose_file.config(state=tk.DISABLED)
        self.entry_name.config(state=tk.NORMAL)
        self.entry_port.config(state=tk.NORMAL)

        self.lbl_peer_info.config(
            text="Status: Not started", foreground="#555555"
        )
        self.peer_listbox.delete(0, tk.END)
        self.peer_display_map.clear()
        self.set_status("Peer stopped.")

    def _connect_peer(self):
        if not self.node or not self.node.is_running:
            messagebox.showwarning("Warning", "Start the local peer first.")
            return

        ip = self.entry_remote_ip.get().strip()
        port_str = self.entry_remote_port.get().strip()

        if not ip:
            messagebox.showwarning("Validation Error", "Please enter remote IP address.")
            return

        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535.")
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be an integer between 1 and 65535.")
            return

        self.set_status(f"Connecting to {ip}:{port}...")
        self.node.connect_to_peer(ip, port)

    def _send_text(self):
        if not self.node or not self.node.is_running:
            return

        peer_id = self._get_selected_peer_id()
        if not peer_id:
            messagebox.showwarning(
                "Selection Required",
                "Please select a connected peer from the list to send a message.",
            )
            return

        msg_text = self.entry_message.get().strip()
        if not msg_text:
            return

        peer = self.node.get_peer(peer_id)
        if not peer:
            messagebox.showerror("Error", "Selected peer is no longer connected.")
            return

        success = self.node.send_text(peer_id, msg_text)
        if success:
            self.log_event(f"You -> {peer.peer_name}: {msg_text}", "OUTGOING")
            self.entry_message.delete(0, tk.END)
            self.set_status(f"Sent text to {peer.peer_name}")

    def _send_file(self):
        if not self.node or not self.node.is_running:
            return

        peer_id = self._get_selected_peer_id()
        if not peer_id:
            messagebox.showwarning(
                "Selection Required",
                "Please select a connected peer from the list to send a file.",
            )
            return

        peer = self.node.get_peer(peer_id)
        if not peer:
            messagebox.showerror("Error", "Selected peer is no longer connected.")
            return

        file_path = filedialog.askopenfilename(
            title="Select File to Send",
            filetypes=[("All Files", "*.*")],
        )
        if not file_path:
            return

        filename = os.path.basename(file_path)
        self.set_status(f"Sending {filename} to {peer.peer_name}...")

        def progress(sent, total):
            pct = int((sent / total) * 100) if total > 0 else 100
            self.set_status(f"Sending {filename} to {peer.peer_name}: {pct}% ({sent}/{total} bytes)")

        # Run in thread so large files don't block Tkinter UI
        def worker():
            success = self.node.send_file(peer_id, file_path, progress_cb=progress)
            if success:
                self.log_event(
                    f"You -> {peer.peer_name}: File sent: {filename}", "FILE_INFO"
                )
                self.set_status(f"File sent: {filename} to {peer.peer_name}")
            else:
                self.set_status(f"Failed to send file: {filename}")

        #if the file is so big and a 3rd peers disconnect the network the GUI will not update at the right time, if we don't use another thread for the file transfer
        import threading    
        threading.Thread(target=worker, daemon=True).start()

    # Node Callbacks
    def _on_message_received(self, sender_id: str, sender_name: str, text: str):
        self.log_event(f"{sender_name} -> You: {text}", "INCOMING")
        self.set_status(f"New message from {sender_name}")

    def _on_file_received(
        self,
        sender_id: str,
        sender_name: str,
        filename: str,
        filepath: str,
        filesize: int,
    ):
        self.log_event(
            f"{sender_name} -> You: File received: {filename} ({filesize} bytes)",
            "FILE_INFO",
        )
        self.set_status(f"Received: {filepath}")

    def _on_peer_connected(
        self, peer_id: str, peer_name: str, host: str, port: int
    ):
        self.after(0, self.refresh_peers_list)
        self.set_status(f"Connected to {peer_name}")

    def _on_peer_disconnected(self, peer_id: str, peer_name: str):
        self.after(0, self.refresh_peers_list)
        self.set_status(f"Peer disconnected: {peer_name}")

    def _on_node_status(self, message: str):
        self.log_event(message, "SYSTEM")
        self.set_status(message)

    def _on_node_error(self, message: str):
        self.log_event(message, "ERROR")
        self.set_status(message)

    def _on_close(self):
        if self.node:
            self.node.stop()
        self.destroy()

if __name__ == "__main__":
    app = P2PApplication()
    app.mainloop()