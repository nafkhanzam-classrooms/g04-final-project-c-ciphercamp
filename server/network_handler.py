import socket
import threading
import json
import logging
import time

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NetworkHandler:
    def __init__(self, game_logic_callback, host='0.0.0.0', port=5555, max_players=4):
        self.host = host
        self.port = port
        self.max_players = max_players
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.clients = {}
        self.lock = threading.Lock()

        self.process_action = game_logic_callback
        self.on_disconnect = None

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logging.info(f"Server berjalan dan mendengarkan di {self.host}:{self.port}")

            while True:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()

        except Exception as e:
            logging.error(f"Gagal memulai server: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, addr):
        logging.info(f"Koneksi baru masuk dari {addr}")
        client_id = None
        buffer = ""

        try:
            while True:
                data = client_socket.recv(2048)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    message_str = message_str.strip()
                    if not message_str:
                        continue

                    try:
                        parsed_data = json.loads(message_str)
                    except json.JSONDecodeError:
                        logging.warning(f"Malformed packet didrop dari {addr}: {message_str}")
                        self.send_to_client(client_socket, {"type": "error", "message": "Invalid JSON format"})
                        continue

                    packet_type = parsed_data.get("type")

                    if packet_type == "ping":
                        self.send_to_client(client_socket, {
                            "type": "pong",
                            "client_time": parsed_data.get("time", 0),
                            "server_time": time.time()
                        })
                        continue

                    if packet_type == "join":
                        client_id = parsed_data.get("player_id")
                        if not client_id:
                            self.send_to_client(client_socket, {"type": "error", "message": "Missing player_id"})
                            continue

                        with self.lock:
                            old_client = self.clients.get(client_id)
                            is_same_player_reconnect = old_client is not None

                            if not is_same_player_reconnect and len(self.clients) >= self.max_players:
                                logging.info(f"Rejecting {client_id} from {addr}: room full")
                                self.send_to_client(client_socket, {
                                    "type": "join_ack",
                                    "status": "full",
                                    "message": "Room penuh",
                                    "current_players": len(self.clients),
                                    "max_players": self.max_players
                                })
                                try:
                                    client_socket.close()
                                except Exception:
                                    pass
                                continue

                            if old_client:
                                try:
                                    old_client["socket"].close()
                                except Exception:
                                    pass
                                logging.info(f"Socket lama untuk Player {client_id} diganti dengan koneksi baru.")

                            self.clients[client_id] = {"socket": client_socket, "addr": addr}

                        logging.info(f"Player {client_id} (Re)Connected dari {addr}")

                        try:
                            resp = self.process_action(client_id, {"action": "join"})
                        except Exception as e:
                            logging.error(f"Gagal memproses join untuk {client_id}: {e}")
                            resp = None

                        if resp and resp.get("type") == "join_ack":
                            self.send_to_client(client_socket, resp)
                        else:
                            self.send_to_client(client_socket, {
                                "type": "join_ack",
                                "status": "success",
                                "current_players": len(self.clients),
                                "max_players": self.max_players
                            })

                        continue

                    if packet_type == "action" and client_id:
                        response = self.process_action(client_id, parsed_data)
                        if response:
                            self.send_to_client(client_socket, response)
                    else:
                        logging.warning(f"Paket tidak dikenal atau player belum join dari {addr}")

        except ConnectionResetError:
            logging.warning(f"Koneksi terputus secara tidak wajar dari {addr} (Player {client_id})")
        except Exception as e:
            logging.error(f"Error pada handler client {addr}: {e}")
        finally:
            self._cleanup_client(client_socket, client_id, addr)

    def _cleanup_client(self, client_socket, client_id, addr):
        removed_current_client = False

        with self.lock:
            if client_id and client_id in self.clients:
                current_client = self.clients.get(client_id)
                if current_client and current_client.get("socket") is client_socket:
                    del self.clients[client_id]
                    removed_current_client = True

        if removed_current_client and client_id and callable(self.on_disconnect):
            try:
                self.on_disconnect(client_id)
            except Exception as e:
                logging.error(f"Error pada on_disconnect untuk {client_id}: {e}")

        try:
            client_socket.close()
        except Exception:
            pass

        logging.info(f"Koneksi ditutup untuk {addr} (Player {client_id}).")

    def send_to_client(self, client_socket, data_dict):
        try:
            message = json.dumps(data_dict) + "\n"
            client_socket.sendall(message.encode('utf-8'))
            return True
        except Exception as e:
            logging.error(f"Gagal mengirim data ke klien: {e}")
            return False

    def broadcast(self, data_dict, exclude_client_id=None):
        with self.lock:
            clients_snapshot = list(self.clients.items())

        dead_clients = []
        for cid, client_info in clients_snapshot:
            if cid == exclude_client_id:
                continue
            if not self.send_to_client(client_info["socket"], data_dict):
                dead_clients.append((cid, client_info))

        for cid, client_info in dead_clients:
            self._cleanup_client(client_info["socket"], cid, client_info["addr"])

if __name__ == "__main__":
    def mock_game_logic(client_id, data):
        logging.info(f"Memproses aksi dari Player {client_id}: {data}")
        return {"type": "action_ack", "status": "processed"}

    server = NetworkHandler(game_logic_callback=mock_game_logic)
    server.start()
