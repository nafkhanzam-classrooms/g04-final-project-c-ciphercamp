class RoomState:
    def __init__(self):
        self.doors = {
            "door_1": {"required_pts": 50, "is_open": False},
            "door_2": {"required_pts": 150, "is_open": False}
        }
        
        self.terminals = {
            "term_1": {"reward": 50, "is_solved": False},
            "term_2": {"reward": 50, "is_solved": False},
            "term_3": {"reward": 100, "is_solved": False},
            "term_4": {"reward": 300, "is_solved": False}
        }

    def get_full_state(self):
        return {
            "doors": self.doors,
            "terminals": self.terminals
        }