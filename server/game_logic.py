import time
import threading
from server.player_session import PlayerSession
from server.room_state import RoomState
import logging

class GameLogic:
    def __init__(self, network_handler, max_players=4):
        self.network = network_handler
        self.players : dict[str, PlayerSession] = {}  
        self.room = RoomState()
        self.max_players = max_players
        
        self.battle_duration = 600  # 10 minutes
        self.start_time = None
        self.is_battle_active = False
        self.game_started = False
        self.match_ended = False

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _broadcast_lobby_state(self):
        self.network.broadcast({
            "type": "lobby_state",
            "current_players": len(self.players),
            "max_players": self.max_players,
            "started": self.game_started
        })

    def _get_spawn_position(self):
        spawn_room = self.room.rooms.get("room_spawn", {})
        if spawn_room:
            spawn_x = spawn_room.get("x", 400) + (spawn_room.get("w", 200) // 2) - 20
            spawn_y = spawn_room.get("y", 550) + (spawn_room.get("h", 100) // 2) - 27
            return spawn_x, spawn_y
        return 480, 580

    def _start_game(self):
        if self.game_started:
            return

        self.game_started = True
        self.is_battle_active = True
        self.match_ended = False
        self.start_time = time.time()

        self.network.broadcast({
            "type": "game_start",
            "battle_duration": self.battle_duration,
            "start_time": self.start_time,
            "max_players": self.max_players
        })
        self.network.broadcast({
            "type": "sync_players",
            "players": {pid: p.to_dict() for pid, p in self.players.items()}
        })

    def remove_player(self, client_id):
        if client_id in self.players:
            del self.players[client_id]
            if not self.game_started:
                self._broadcast_lobby_state()
            else:
                self.network.broadcast({
                    "type": "sync_players",
                    "players": {pid: p.to_dict() for pid, p in self.players.items()}
                })

    def process_action(self, client_id, data):
        action = data.get("action")

        if self.match_ended:
            if action == "join":
                return {"type": "join_ack", "status": "ended", "message": "Match sudah selesai", "current_players": len(self.players), "max_players": self.max_players}
            return {"type": "error", "message": "Match sudah selesai"}

        if self.game_started and not self.is_battle_active:
            return {"type": "error", "message": "Waktu battle sudah habis!"}

        
        if action == "join":
           
            if len(self.players) >= self.max_players:
                return {"type": "join_ack", "status": "full", "message": "Room penuh", "current_players": len(self.players), "max_players": self.max_players}

            
            used = {p.asset for p in self.players.values()}
            assigned = None
            for i in range(1, 5):
                if i not in used:
                    assigned = i
                    break

            if assigned is None:
                assigned = 1

            spawn_x, spawn_y = self._get_spawn_position()
            self.players[client_id] = PlayerSession(client_id, start_x=spawn_x, start_y=spawn_y, asset_index=assigned)

            
            self.network.broadcast({
                "type": "sync_map",
                "map_state": self.room.get_full_state()
            })
            self.network.broadcast({
                "type": "sync_players",
                "players": {pid: p.to_dict() for pid, p in self.players.items()}
            })

            self._broadcast_lobby_state()

            if len(self.players) >= self.max_players:
                self._start_game()

            return {"type": "join_ack", "status": "success", "asset": assigned, "current_players": len(self.players), "max_players": self.max_players, "started": self.game_started}

        
        action = data.get("action")

        if client_id not in self.players:
           
            used = {p.asset for p in self.players.values()}
            assigned = None
            for i in range(1, 5):
                if i not in used:
                    assigned = i
                    break
            if assigned is None:
                assigned = 1

            spawn_x, spawn_y = self._get_spawn_position()
            self.players[client_id] = PlayerSession(client_id, start_x=spawn_x, start_y=spawn_y, asset_index=assigned)
            self.network.broadcast({
                "type": "sync_map",
                "map_state": self.room.get_full_state()
            })
            self._broadcast_lobby_state()
            if len(self.players) >= self.max_players and not self.game_started:
                self._start_game()
            
        player = self.players[client_id]

        if not self.game_started and action != "join":
            return {"type": "error", "message": f"Menunggu player lain ({len(self.players)}/{self.max_players})"}

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

                    
                    if all(player.terminal_solve_state.values()):
                        self._end_game(winner=client_id)
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

    def _monitor_loop(self):
        while True:
            try:
                if not self.game_started or self.start_time is None:
                    time.sleep(1)
                    continue

                elapsed = time.time() - self.start_time
                if elapsed >= self.battle_duration:
                    self._end_game(reason="time")
                    break

                
                for pid, player in list(self.players.items()):
                    if all(player.terminal_solve_state.values()):
                        self._end_game(winner=pid)
                        return

                time.sleep(1)
            except Exception:
                time.sleep(1)

    def _end_game(self, winner: str | None = None, reason: str = "complete"):
        if not self.is_battle_active:
            return
        self.is_battle_active = False
        self.game_started = False
        self.match_ended = True

        # prepare leaderboard
        leaderboard = sorted(
            [(p.player_id, p.points) for p in self.players.values()],
            key=lambda x: x[1],
            reverse=True
        )

        payload = {
            "type": "game_over",
            "reason": reason,
            "winner": winner,
            "leaderboard": [{"player_id": pid, "points": pts} for pid, pts in leaderboard]
        }

        try:
            self.network.broadcast(payload)
            # also send final sync_players for client convenience
            self.network.broadcast({
                "type": "sync_players",
                "players": {pid: p.to_dict() for pid, p in self.players.items()}
            })
            self.network.broadcast({
                "type": "lobby_state",
                "current_players": len(self.players),
                "max_players": self.max_players,
                "started": self.game_started
            })
        except Exception:
            pass