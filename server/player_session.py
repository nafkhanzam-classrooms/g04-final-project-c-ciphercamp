class PlayerSession:
    def __init__(self, player_id, start_x=480, start_y=580, asset_index: int = 1):
        self.player_id = player_id
        self.x = start_x
        self.y = start_y
        self.dir = "down"
        self.points = 0
        self.energy = 200
        self.asset = asset_index
        self.connected = True
        self.disconnected_at = None
        self.door_open_state : dict[str, bool] = {
            "door_main": False,
            "door_left": False,
            "door_right": False,
            "door_top": False,
            "door_sec1": False,
            "door_sec2": False
        }
        self.terminal_solve_state : dict[str, bool] = {
            "term_tut": False,
            "term_e1": False,
            "term_e2": False,
            "term_e3": False,
            "term_m1":False,
            "term_m2": False,
            "term_m3": False,
            "term_h1": False,
            "term_h2": False,
            "term_h3": False,
            "term_sec1":False,
            "term_sec2": False
        }

    def mark_connected(self):
        self.connected = True
        self.disconnected_at = None

    def mark_disconnected(self, disconnected_at):
        self.connected = False
        self.disconnected_at = disconnected_at

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "x": self.x,
            "y": self.y,
            "dir": self.dir,
            "asset": getattr(self, "asset", 1),
            "points": self.points,
            "energy": self.energy,
            "connected": self.connected,
            "disconnected_at": self.disconnected_at,
            "door_open_state": self.door_open_state,
            "terminal_solve_state": self.terminal_solve_state
        }
