import socket
import threading
import time
import logging
from shared.config import SERVER_IP, SERVER_PORT
from shared.packet_parser import encode_packet, decode_stream

class NetworkClient:
    def __init__(self, player_id):
        self.player_id = player_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.game_state = {
            "players": {},
            "map_state": {"doors": {}, "terminals": {}},
            "ping": 0,
            "game_started": False,
            "battle_duration": 0,
            "game_start_time": None,
            "lobby": {"current_players": 0, "max_players": 0, "started": False}
        }
        self.is_connected = False

    def connect(self):
        try:
            self.sock.connect((SERVER_IP, SERVER_PORT))
            self.is_connected = True
            
            self.send({"type": "join", "player_id": self.player_id})
            
            receive_thread = threading.Thread(target=self._receive_loop)
            receive_thread.daemon = True
            receive_thread.start()
            
            ping_thread = threading.Thread(target=self._ping_loop)
            ping_thread.daemon = True
            ping_thread.start()
            
        except Exception as e:
            logging.error(f"Gagal connect ke server: {e}")

    def send(self, data_dict):
        if self.is_connected:
            try:
                self.sock.sendall(encode_packet(data_dict).encode('utf-8'))
            except Exception as e:
                logging.error(f"Koneksi terputus saat kirim data: {e}")
                self.is_connected = False

    def _ping_loop(self):
        while self.is_connected:
            self.send({"type": "ping", "time": time.time()})
            time.sleep(2)

    def _receive_loop(self):
        buffer = ""
        try:
            while self.is_connected:
                data = self.sock.recv(2048)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                packets, buffer = decode_stream(buffer)
                
                for packet in packets:
                    self._handle_packet(packet)
                    
        except Exception as e:
            logging.error(f"Error pada receive loop: {e}")
        finally:
            self.is_connected = False
            self.sock.close()

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
            if packet.get("status") == "full":
                self.game_state["join_full"] = packet
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