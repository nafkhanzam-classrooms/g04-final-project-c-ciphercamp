class PlayerSession:
    def __init__(self, player_id, start_x=500, start_y=350):
        self.player_id = player_id
        self.x = start_x
        self.y = start_y
        self.dir = "down"
        self.points = 0
        self.energy = 100
        
    def to_dict(self):
        return {
            "player_id": self.player_id,
            "x": self.x,
            "y": self.y,
            "dir": self.dir,
            "points": self.points,
            "energy": self.energy
        }