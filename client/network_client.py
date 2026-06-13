import socket
import threading
import time
import logging
import json
from shared.config import SERVER_IP, SERVER_PORT, DISCOVERY_PORT, DISCOVERY_REQUEST, DISCOVERY_RESPONSE
from shared.packet_parser import encode_packet, decode_stream

def discover_server(timeout=3.0, attempts=3):
    message = json.dumps({
        "type": DISCOVERY_REQUEST,
        "client_time": time.time()
    }).encode("utf-8")

    for attempt in range(attempts):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_sock.settimeout(timeout / max(attempts, 1))

        try:
            udp_sock.sendto(message, ("255.255.255.255", DISCOVERY_PORT))

            while True:
                data, addr = udp_sock.recvfrom(2048)
                try:
                    response = json.loads(data.decode("utf-8").strip())
                except Exception:
                    continue

                if response.get("type") != DISCOVERY_RESPONSE:
                    continue

                server_ip = addr[0]
                server_port = int(response.get("server_port", SERVER_PORT))
                logging.info(f"Server ditemukan otomatis di {server_ip}:{server_port}")
                return server_ip, server_port

        except socket.timeout:
            logging.info(f"Discovery attempt {attempt + 1}/{attempts} belum menemukan server.")
        except Exception as e:
            logging.warning(f"LAN discovery gagal pada attempt {attempt + 1}: {e}")
        finally:
            try:
                udp_sock.close()
            except Exception:
                pass

    return None

class NetworkClient:
    def __init__(self, player_id, server_ip=SERVER_IP, server_port=SERVER_PORT):
        self.player_id = player_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None
        self.lock = threading.Lock()
        self._stop_requested = False
        self._reconnect_thread_running = False
        self._ping_thread_running = False

        self.game_state = {
            "players": {},
            "map_state": {"doors": {}, "terminals": {}},
            "ping": 0,
            "game_started": False,
            "battle_duration": 0,
            "game_start_time": None,
            "connection_status": "disconnected",
            "lobby": {"current_players": 0, "max_players": 0, "started": False}
        }
        self.is_connected = False

    def connect(self):
        if self.is_connected:
            return True

        new_sock = None
        try:
            new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_sock.settimeout(5)
            new_sock.connect((self.server_ip, self.server_port))
            new_sock.settimeout(None)

            with self.lock:
                self.sock = new_sock
                self.is_connected = True
                self.game_state["connection_status"] = "connected"

            self.send({"type": "join", "player_id": self.player_id})

            receive_thread = threading.Thread(target=self._receive_loop, args=(new_sock,), daemon=True)
            receive_thread.start()

            if not self._ping_thread_running:
                ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
                ping_thread.start()

            logging.info(f"Berhasil connect/reconnect ke server {self.server_ip}:{self.server_port}.")
            return True

        except Exception as e:
            logging.error(f"Gagal connect ke server: {e}")
            with self.lock:
                self.is_connected = False
                self.game_state["connection_status"] = "reconnecting"
            if new_sock:
                try:
                    new_sock.close()
                except Exception:
                    pass
            if not self._reconnect_thread_running and not self._stop_requested:
                self._schedule_reconnect()
            return False

    def close(self):
        self._stop_requested = True
        with self.lock:
            self.is_connected = False
            self.game_state["connection_status"] = "closed"
            current_sock = self.sock
            self.sock = None

        if current_sock:
            try:
                current_sock.close()
            except Exception:
                pass

    def send(self, data_dict):
        with self.lock:
            current_sock = self.sock
            connected = self.is_connected

        if connected and current_sock:
            try:
                current_sock.sendall(encode_packet(data_dict).encode('utf-8'))
                return True
            except Exception as e:
                logging.error(f"Koneksi terputus saat kirim data: {e}")
                self._mark_disconnected(current_sock)
                self._schedule_reconnect()
        return False

    def _mark_disconnected(self, sock):
        with self.lock:
            if self.sock is sock:
                self.is_connected = False
                self.game_state["connection_status"] = "reconnecting"
        try:
            sock.close()
        except Exception:
            pass

    def _schedule_reconnect(self):
        if self._stop_requested:
            return
        if self._reconnect_thread_running:
            return

        self._reconnect_thread_running = True
        reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        reconnect_thread.start()

    def _reconnect_loop(self):
        try:
            while not self._stop_requested and not self.is_connected:
                self.game_state["connection_status"] = "reconnecting"
                logging.info("Mencoba reconnect ke server...")
                if self.connect():
                    break
                time.sleep(2)
        finally:
            self._reconnect_thread_running = False

    def _ping_loop(self):
        self._ping_thread_running = True
        try:
            while not self._stop_requested:
                if self.is_connected:
                    self.send({"type": "ping", "time": time.time()})
                time.sleep(2)
        finally:
            self._ping_thread_running = False

    def _receive_loop(self, sock):
        buffer = ""
        try:
            while not self._stop_requested and self.is_connected:
                data = sock.recv(2048)
                if not data:
                    break

                buffer += data.decode('utf-8')
                packets, buffer = decode_stream(buffer)

                for packet in packets:
                    self._handle_packet(packet)

        except Exception as e:
            if not self._stop_requested:
                logging.error(f"Error pada receive loop: {e}")
        finally:
            self._mark_disconnected(sock)
            if not self._stop_requested:
                self._schedule_reconnect()

    def _handle_packet(self, packet):
        p_type = packet.get("type")
        if p_type == "sync_players":
            self.game_state["players"] = packet.get("players", {})
        elif p_type == "sync_map":
            self.game_state["map_state"] = packet.get("map_state", {})
        elif p_type == "pong":
            latency = (time.time() - packet.get("client_time", time.time())) * 1000
            self.game_state["ping"] = int(latency)
        elif p_type == "join_ack":
            self.game_state["join_ack"] = packet
            status = packet.get("status")
            if status == "full":
                self.game_state["join_full"] = packet
            if packet.get("started"):
                self.game_state["game_started"] = True
                self.game_state["battle_duration"] = packet.get("battle_duration", self.game_state.get("battle_duration", 0))
                self.game_state["game_start_time"] = packet.get("start_time", self.game_state.get("game_start_time"))
            self.game_state["lobby"] = {
                "current_players": packet.get("current_players", self.game_state.get("lobby", {}).get("current_players", 0)),
                "max_players": packet.get("max_players", self.game_state.get("lobby", {}).get("max_players", 0)),
                "started": packet.get("started", self.game_state.get("game_started", False))
            }
        elif p_type == "game_over":
            self.game_state["game_over"] = packet
            self.game_state["game_started"] = False
        elif p_type == "game_start":
            self.game_state["game_started"] = True
            self.game_state["battle_duration"] = packet.get("battle_duration", 0)
            self.game_state["game_start_time"] = packet.get("start_time")
        elif p_type == "notify":
            self.game_state.setdefault("notifications", []).append(packet.get("message"))
        elif p_type == "lobby_state":
            self.game_state["lobby"] = {
                "current_players": packet.get("current_players", 0),
                "max_players": packet.get("max_players", 0),
                "started": packet.get("started", False)
            }
