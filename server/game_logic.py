import time
from server.player_session import PlayerSession
from server.room_state import RoomState
import logging

class GameLogic:
    def __init__(self, network_handler):
        self.network = network_handler
        self.players = {}  
        self.room = RoomState()
        
        self.battle_duration = 300 
        self.start_time = time.time()
        self.is_battle_active = True

    def process_action(self, client_id, data):
        if not self.is_battle_active:
            return {"type": "error", "message": "Waktu battle sudah habis!"}

        action = data.get("action")

        if client_id not in self.players:
            self.players[client_id] = PlayerSession(client_id)
            
        player = self.players[client_id]

        if action == "move":
            player.x = data.get("x", player.x)
            player.y = data.get("y", player.y)
            player.dir = data.get("dir", player.dir)
            
            self.network.broadcast({
                "type": "sync_players",
                "players": {pid: p.to_dict() for pid, p in self.players.items()}
            })
            return {"type": "ack", "message": "move_processed"}

        elif action == "hack_terminal":
            term_id = data.get("terminal_id")
            if term_id in self.room.terminals and not self.room.terminals[term_id]["is_solved"]:
                self.room.terminals[term_id]["is_solved"] = True
                player.points += self.room.terminals[term_id]["reward"]
                logging.info(f"Player {client_id} meretas {term_id}! Poin: {player.points}")
                
                self.network.broadcast({
                    "type": "sync_map",
                    "map_state": self.room.get_full_state()
                })
                self.network.broadcast({
                    "type": "sync_players",
                    "players": {pid: p.to_dict() for pid, p in self.players.items()}
                })
            return None

        elif action == "open_door":
            door_id = data.get("door_id")
            if door_id in self.room.doors and not self.room.doors[door_id]["is_open"]:
                req_pts = self.room.doors[door_id]["required_pts"]
                
                if (player.points - req_pts) > 0:
                    self.room.doors[door_id]["is_open"] = True
                    player.points -= req_pts 
                    logging.info(f"Pintu {door_id} dibuka oleh {client_id}")
                    
                    self.network.broadcast({
                        "type": "sync_map",
                        "map_state": self.room.get_full_state()
                    })
                else:
                    return {"type": "error", "message": f"Poin tidak cukup! Butuh > {req_pts} poin."}
            return None
            
        return {"type": "error", "message": "Unknown action"}