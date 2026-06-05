import time
from server.player_session import PlayerSession
from server.room_state import RoomState
import logging

class GameLogic:
    def __init__(self, network_handler):
        self.network = network_handler
        self.players : dict[str, PlayerSession] = {}  
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
            self.network.broadcast({
                "type": "sync_map",
                "map_state": self.room.get_full_state()
            })
            
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

        elif action == "submit_flag":
            term_id = data.get("terminal_id")
            submitted_flag = data.get("flag", "").strip().lower()
            
            if term_id in self.room.terminals and not player.terminal_solve_state[term_id]:
                correct_flag = self.room.terminals[term_id].get("flag", "").lower()
                
                if submitted_flag == correct_flag:
                    player.terminal_solve_state[term_id] = True
                    reward = self.room.terminals[term_id]["reward"]
                    player.points += reward
                    player.energy += reward
                    
                    self.network.broadcast({
                        "type": "sync_map",
                        "map_state": self.room.get_full_state()
                    })
                    self.network.broadcast({
                        "type": "sync_players",
                        "players": {pid: p.to_dict() for pid, p in self.players.items()}
                    })
                    return {"type": "notify", "message": "Flag benar!"}
                else:
                    return {"type": "notify", "message": "Flag salah!"}
            return None

        elif action == "open_door":
            door_id = data.get("door_id")
            if door_id in self.room.doors and not player.door_open_state[door_id]:
                req_energy = self.room.doors[door_id]["required_energy"]
                
                if (player.energy - req_energy) >= 0:
                    player.door_open_state[door_id] = True
                    player.energy -= req_energy 
                    
                    self.network.broadcast({
                        "type": "sync_map",
                        "map_state": self.room.get_full_state()
                    })
                    self.network.broadcast({
                        "type": "sync_players",
                        "players": {pid: p.to_dict() for pid, p in self.players.items()}
                    })
                else:
                    return {"type": "error", "message": "Energy tidak cukup!"}
            return None
            
        return {"type": "error", "message": "Unknown action"}