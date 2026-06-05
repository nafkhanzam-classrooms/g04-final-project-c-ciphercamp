class PlayerSession:
    def __init__(self, player_id, start_x=480, start_y=580):
        self.player_id = player_id
        self.x = start_x
        self.y = start_y
        self.dir = "down"
        self.points = 0
        self.energy = 200
        self.door_open_state : dict[str, bool] = {
            "door_main": False,
            "door_left": False,
            "door_right": False,
            "door_top": False,
            "door_sec1": False,
            "door_sec2": False
        }
        
        
    def to_dict(self):
        return {
            "player_id": self.player_id,
            "x": self.x,
            "y": self.y,
            "dir": self.dir,
            "points": self.points,
            "energy": self.energy,
            "door_open_state": self.door_open_state
        }