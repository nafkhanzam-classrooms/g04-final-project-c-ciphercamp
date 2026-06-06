import base64
import random
import time
from math import gcd

from shared.config import HEIGHT, WIDTH


class RoomState:
    def __init__(self):
        self.rng = random.Random(time.time_ns())
        self.layout_name = self.rng.choice(["base", "mirror_x", "mirror_y", "mirror_xy"])

        self.rooms = self._build_rooms()
        self.doors = self._build_doors()
        self.connections = self._build_connections()
        self.terminals = self._build_terminals()
        self.walls = self._build_walls()

    def _rect(self, x, y, w, h):
        return {"x": x, "y": y, "w": w, "h": h}

    def _transform_rect(self, rect):
        x = rect["x"]
        y = rect["y"]
        w = rect["w"]
        h = rect["h"]

        if self.layout_name in ("mirror_x", "mirror_xy"):
            x = WIDTH - x - w
        if self.layout_name in ("mirror_y", "mirror_xy"):
            y = HEIGHT - y - h
        return self._rect(x, y, w, h)

    def _build_rooms(self):
        base_rooms = {
            "room_spawn": self._rect(400, 550, 200, 100),
            "room_mid": self._rect(450, 350, 100, 200),
            "room_top_mid": self._rect(400, 200, 200, 150),
            "room_left": self._rect(100, 200, 200, 150),
            "room_right": self._rect(700, 200, 200, 150),
            "room_top": self._rect(300, 50, 400, 100),
            "room_sec_left": self._rect(100, 450, 150, 150),
            "room_sec_right": self._rect(750, 450, 150, 150),
            "room_left_bridge": self._rect(300, 230, 100, 90),
            "room_right_bridge": self._rect(600, 230, 100, 90),
            "room_top_bridge": self._rect(450, 150, 100, 50),
            "room_left_inner": self._rect(135, 350, 80, 100),
            "room_right_inner": self._rect(785, 350, 80, 100),
        }
        return {name: self._transform_rect(rect) for name, rect in base_rooms.items()}

    def _build_doors(self):
        base_doors = {
            "door_main": self._rect(450, 400, 100, 40),
            "door_left": self._rect(330, 230, 40, 90),
            "door_right": self._rect(630, 230, 40, 90),
            "door_top": self._rect(450, 155, 100, 40),
            "door_sec1": self._rect(135, 380, 80, 40),
            "door_sec2": self._rect(785, 380, 80, 40),
        }

        doors = {
            "door_main": {"required_energy": 50},
            "door_left": {"required_energy": 100},
            "door_right": {"required_energy": 200},
            "door_top": {"required_energy": 500},
            "door_sec1": {"required_energy": 150},
            "door_sec2": {"required_energy": 300},
        }

        for door_id, rect in base_doors.items():
            doors[door_id]["rect"] = self._transform_rect(rect)
        return doors

    def _build_connections(self):
        base_connections = [
            self._rect(451, 535, 98, 30),
            self._rect(451, 335, 98, 30),
            self._rect(285, 231, 30, 88),
            self._rect(385, 231, 30, 88),
            self._rect(585, 231, 30, 88),
            self._rect(685, 231, 30, 88),
            self._rect(451, 135, 98, 30),
            self._rect(451, 185, 98, 30),
            self._rect(136, 435, 78, 30),
            self._rect(136, 335, 78, 30),
            self._rect(786, 435, 78, 30),
            self._rect(786, 335, 78, 30),
        ]
        return [self._transform_rect(rect) for rect in base_connections]

    def _build_terminals(self):
        pools = {
            "easy": [
                "PROGJAR",
                "SOCKET",
                "PACKET",
                "SERVER",
                "CLIENT",
                "ROUTER",
                "KENTANG",
                "AYAMGORENG",
                "AKUSUKAPROGJAR",
            ],
            "medium": [
                "HANDSHAKE",
                "ENCRYPTION",
                "FIREWALL",
                "BANDWIDTH",
                "PROTOCOL",
                "STREAMING",
                "SEGMENTASI",
            ],
            "hard": [
                "ROUTE",
                "PACKET",
                "SERVER",
                "PROXY",
                "SOCKET",
                "TLS",
                "HASH",
                "SYNC",
                "QUEUE",
                "ACK",
            ],
        }

        tier_slots = {
            "easy": [
                self._rect(480, 570, 40, 40),
                self._rect(120, 220, 40, 40),
                self._rect(220, 220, 40, 40),
                self._rect(120, 280, 40, 40),
            ],
            "medium": [
                self._rect(720, 220, 40, 40),
                self._rect(820, 220, 40, 40),
                self._rect(720, 280, 40, 40),
                self._rect(150, 500, 40, 40),
            ],
            "hard": [
                self._rect(350, 70, 40, 40),
                self._rect(500, 70, 40, 40),
                self._rect(600, 70, 40, 40),
                self._rect(800, 500, 40, 40),
            ],
        }

        tier_terminal_ids = {
            "easy": ["term_tut", "term_e1", "term_e2", "term_e3"],
            "medium": ["term_m1", "term_m2", "term_m3", "term_sec1"],
            "hard": ["term_h1", "term_h2", "term_h3", "term_sec2"],
        }

        terminal_data = {}
        for tier, terminal_ids in tier_terminal_ids.items():
            slots = tier_slots[tier][:]
            ids = terminal_ids[:]
            self.rng.shuffle(slots)
            self.rng.shuffle(ids)

            for terminal_id, rect in zip(ids, slots):
                plaintext = self._pick_plaintext(pools[tier])
                question, answer = self._generate_question(tier, plaintext)
                reward = 50 if tier == "easy" else 100 if tier == "medium" else 200
                if terminal_id == "term_sec1":
                    reward = 150
                elif terminal_id == "term_sec2":
                    reward = 250

                terminal_data[terminal_id] = {
                    "rect": self._transform_rect(rect),
                    "tier": tier,
                    "reward": reward,
                    "question": question,
                    "flag": answer,
                }
        return terminal_data

    def _pick_plaintext(self, words):
        return self.rng.choice(words).upper().replace(" ", "")

    def _normalize_text(self, value):
        return "".join(ch for ch in value.upper() if ch.isalnum())

    def _caesar_encrypt(self, plaintext, shift):
        encoded = []
        for ch in plaintext:
            if "A" <= ch <= "Z":
                encoded.append(chr(((ord(ch) - 65 + shift) % 26) + 65))
            else:
                encoded.append(ch)
        return "".join(encoded)

    def _xor_encrypt(self, plaintext, key):
        raw = plaintext.encode("utf-8")
        xored = bytes([b ^ key for b in raw])
        return xored.hex().upper()

    def _word_to_int(self, plaintext):
        value = 0
        for ch in self._normalize_text(plaintext):
            if "A" <= ch <= "Z":
                digit = ord(ch) - 64
            elif ch.isdigit():
                digit = int(ch) + 27
            else:
                digit = 0
            value = value * 37 + digit
        return value

    def _generate_prime(self, minimum, maximum):
        candidate = self.rng.randint(minimum, maximum)
        if candidate % 2 == 0:
            candidate += 1
        while candidate <= maximum:
            if self._is_prime(candidate):
                return candidate
            candidate += 2
        candidate = minimum | 1
        while candidate < minimum + 500000:
            if self._is_prime(candidate):
                return candidate
            candidate += 2
        return 1000003

    def _is_prime(self, candidate):
        if candidate < 2:
            return False
        if candidate in (2, 3):
            return True
        if candidate % 2 == 0:
            return False
        divisor = 3
        while divisor * divisor <= candidate:
            if candidate % divisor == 0:
                return False
            divisor += 2
        return True

    def _generate_rsa_question(self, plaintext):
        plain_int = self._word_to_int(plaintext)
        p = self._generate_prime(50_000, 200_000)
        q = self._generate_prime(200_000, 500_000)
        while p == q:
            q = self._generate_prime(200_000, 500_000)

        n = p * q
        while n <= plain_int:
            p = self._generate_prime(p + 10_000, p + 50_000)
            q = self._generate_prime(q + 10_000, q + 50_000)
            if p == q:
                q = self._generate_prime(q + 1, q + 80_000)
            n = p * q

        phi = (p - 1) * (q - 1)
        e = 65537
        if gcd(e, phi) != 1:
            e = 17
            if gcd(e, phi) != 1:
                e = 5

        ciphertext = pow(plain_int, e, n)
        question = f"ciphertext: {ciphertext} | p: {p} | q: {q} | e: {e}"
        return question, self._normalize_text(plaintext)

    def _generate_question(self, tier, plaintext):
        if tier == "easy":
            algorithm = self.rng.choice(["base64", "rot13"])
            if algorithm == "base64":
                ciphertext = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")
                return f"ciphertext: {ciphertext} | Key: base64", self._normalize_text(plaintext)

            shift = 13
            ciphertext = self._caesar_encrypt(plaintext, shift)
            return f"ciphertext: {ciphertext} | Key: ROT{shift}", self._normalize_text(plaintext)

        if tier == "medium":
            algorithm = self.rng.choice(["xor", "arith"])
            if algorithm == "xor":
                key = self.rng.randint(1, 15)
                ciphertext = self._xor_encrypt(plaintext, key)
                return f"ciphertext: {ciphertext} | Key: XOR {key}", self._normalize_text(plaintext)

            mul = self.rng.choice([3, 5, 7, 9, 11, 13, 15, 17, 19])
            add = self.rng.randint(10, 999)
            modulus = 1_000_000_007
            while gcd(mul, modulus) != 1:
                mul += 2
            plain_int = self._word_to_int(plaintext)
            ciphertext = ((plain_int * mul) + add) % modulus
            return f"ciphertext: {ciphertext} | Key: a={mul}, b={add}, mod={modulus}", self._normalize_text(plaintext)

        return self._generate_rsa_question(plaintext)

    def _build_walls(self):
        wall_thickness = 15
        walls = []
        room_rects = list(self.rooms.values())
        for room in room_rects:
            walls.append(self._rect(room["x"] - wall_thickness, room["y"] - wall_thickness, room["w"] + wall_thickness * 2, wall_thickness))
            walls.append(self._rect(room["x"] - wall_thickness, room["y"] + room["h"], room["w"] + wall_thickness * 2, wall_thickness))
            walls.append(self._rect(room["x"] - wall_thickness, room["y"] - wall_thickness, wall_thickness, room["h"] + wall_thickness * 2))
            walls.append(self._rect(room["x"] + room["w"], room["y"] - wall_thickness, wall_thickness, room["h"] + wall_thickness * 2))

        carvers = [door["rect"] for door in self.doors.values()] + self.connections
        carved_walls = []
        for wall in walls:
            pieces = [wall]
            for carve in carvers:
                new_pieces = []
                for piece in pieces:
                    if self._rects_intersect(piece, carve):
                        if piece["w"] > piece["h"]:
                            left = self._rect(piece["x"], piece["y"], carve["x"] - piece["x"], piece["h"])
                            right = self._rect(carve["x"] + carve["w"], piece["y"], piece["x"] + piece["w"] - (carve["x"] + carve["w"]), piece["h"])
                            if left["w"] > 0:
                                new_pieces.append(left)
                            if right["w"] > 0:
                                new_pieces.append(right)
                        else:
                            top = self._rect(piece["x"], piece["y"], piece["w"], carve["y"] - piece["y"])
                            bottom = self._rect(piece["x"], carve["y"] + carve["h"], piece["w"], piece["y"] + piece["h"] - (carve["y"] + carve["h"]))
                            if top["h"] > 0:
                                new_pieces.append(top)
                            if bottom["h"] > 0:
                                new_pieces.append(bottom)
                    else:
                        new_pieces.append(piece)
                pieces = new_pieces
            carved_walls.extend(pieces)
        return carved_walls

    def _rects_intersect(self, a, b):
        return not (
            a["x"] + a["w"] <= b["x"]
            or a["x"] >= b["x"] + b["w"]
            or a["y"] + a["h"] <= b["y"]
            or a["y"] >= b["y"] + b["h"]
        )

    def get_full_state(self):
        safe_terminals = {}
        for t_id, t_data in self.terminals.items():
            safe_terminals[t_id] = {
                "reward": t_data.get("reward", 0),
                "question": t_data.get("question", "Soal belum tersedia."),
                "tier": t_data.get("tier", "?"),
                "rect": t_data.get("rect"),
            }

        return {
            "layout_name": self.layout_name,
            "rooms": self.rooms,
            "doors": self.doors,
            "connections": self.connections,
            "walls": self.walls,
            "terminals": safe_terminals,
        }