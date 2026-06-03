import pygame
import sys
import os

# Inisialisasi Pygame
pygame.init()

# Konstanta Layar & Warna
WIDTH, HEIGHT = 1000, 700
FPS = 60
BG_COLOR = (30, 30, 40)          
FLOOR_COLOR = (240, 235, 215)    
WALL_COLOR = (120, 115, 100)     
DOOR_COLOR = (200, 50, 50)       
DOOR_OPEN = (50, 200, 50)        

# Setup Layar & Font
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CipherCamp: Facility Map")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
tooltip_font = pygame.font.SysFont("consolas", 14)

# ==========================================
# KELAS PEMAIN
# ==========================================
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 55) 
        self.speed = 5
        self.points = 0
        self.energy = 100
        
        # Load Aset Gambar
        try:
            self.sprites = {
                'up': pygame.image.load(os.path.join('assets', 'player1', 'player_up.png')).convert_alpha(),
                'down': pygame.image.load(os.path.join('assets', 'player1', 'player_down.png')).convert_alpha(),
                'left': pygame.image.load(os.path.join('assets', 'player1', 'player_left.png')).convert_alpha(),
                'right': pygame.image.load(os.path.join('assets', 'player1', 'player_right.png')).convert_alpha()
            }
            # Resize agar pas dengan hitbox
            for key in self.sprites:
                self.sprites[key] = pygame.transform.scale(self.sprites[key], (40, 55))
        except FileNotFoundError:
            print("ERROR: Folder 'assets' atau gambar player tidak ditemukan!")
            pygame.quit()
            sys.exit()

        self.current_sprite = self.sprites['down'] 

    def move(self, keys, walls, doors):
        dx, dy = 0, 0
        
        # Update arah dan kecepatan
        if keys[pygame.K_w]: 
            dy = -self.speed
            self.current_sprite = self.sprites['up']
        if keys[pygame.K_s]: 
            dy = self.speed
            self.current_sprite = self.sprites['down']
        if keys[pygame.K_a]: 
            dx = -self.speed
            self.current_sprite = self.sprites['left']
        if keys[pygame.K_d]: 
            dx = self.speed
            self.current_sprite = self.sprites['right']

        # Hanya masukkan pintu yang BELUM terbuka ke daftar benda padat
        solid_objects = walls.copy()
        for d in doors:
            if not d.is_open:
                solid_objects.append(d.rect)

        # Gerak Horizontal & Cek Tabrakan
        self.rect.x += dx
        for obj in solid_objects:
            if self.rect.colliderect(obj):
                if dx > 0: self.rect.right = obj.left
                if dx < 0: self.rect.left = obj.right

        # Gerak Vertikal & Cek Tabrakan
        self.rect.y += dy
        for obj in solid_objects:
            if self.rect.colliderect(obj):
                if dy > 0: self.rect.bottom = obj.top
                if dy < 0: self.rect.top = obj.bottom

    def draw(self, surface):
        surface.blit(self.current_sprite, self.rect)

# ==========================================
# KELAS PINTU & TERMINAL
# ==========================================
class Door:
    def __init__(self, rect, required_pts):
        self.rect = pygame.Rect(rect)
        self.required_pts = required_pts
        self.is_open = False

    def draw(self, surface, player_pts):
        if not self.is_open:
            color = DOOR_OPEN if player_pts >= self.required_pts else DOOR_COLOR
            pygame.draw.rect(surface, color, self.rect)

class Terminal:
    def __init__(self, x, y, tier, color, reward_pts):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.tier = tier
        self.color = color
        self.reward_pts = reward_pts
        self.is_solved = False

    def draw(self, surface):
        draw_color = (100, 100, 100) if self.is_solved else self.color
        pygame.draw.rect(surface, draw_color, self.rect)
        text = font.render(self.tier, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


# ==========================================
# FUNGSI UTAMA GAME LOOP
# ==========================================
def main():
    player = Player(WIDTH // 2 - 20, HEIGHT // 2 - 20)

    # 1. MEMBUAT LAYOUT RUANGAN (Fasilitas)
    rooms = [
        pygame.Rect(300, 150, 400, 400), # Hall Utama
        pygame.Rect(50, 150, 200, 150),  # Ruang Kiri 
        pygame.Rect(750, 150, 200, 150), # Ruang Kanan
        pygame.Rect(400, 550, 200, 100)  # Lorong Bawah
    ]

    initial_walls = []
    wall_thickness = 15
    for r in rooms:
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.bottom, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 
        initial_walls.append(pygame.Rect(r.right, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 

    # 2. DEFINISI PINTU
    doors = [
        Door((250, 200, 50, wall_thickness*4), 50),   
        Door((700, 200, 50, wall_thickness*4), 150),  
    ]

    # --- PERBAIKAN: MELUBANGI TEMBOK UNTUK PINTU ---
    walls = []
    for w in initial_walls:
        is_carved = False
        for d in doors:
            if w.colliderect(d.rect):
                # Potong tembok secara vertikal menyisakan ruang untuk pintu
                wall_top = pygame.Rect(w.x, w.y, w.width, d.rect.top - w.y)
                wall_bottom = pygame.Rect(w.x, d.rect.bottom, w.width, w.bottom - d.rect.bottom)
                
                if wall_top.height > 0: walls.append(wall_top)
                if wall_bottom.height > 0: walls.append(wall_bottom)
                
                is_carved = True
                break
        
        if not is_carved:
            walls.append(w)

    # 3. DEFINISI TERMINAL (Soal)
    terminals = [
        Terminal(450, 300, "E", (50, 150, 200), 50),   
        Terminal(550, 300, "E", (50, 150, 200), 50),   
        Terminal(100, 200, "M", (200, 150, 50), 100),  
        Terminal(850, 200, "H", (200, 50, 200), 300)   
    ]

    hacking_mode = False
    active_terminal = None

    running = True
    while running:
        # --- 1. EVENT HANDLING ---
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if hacking_mode:
                        hacking_mode = False
                        if active_terminal and not active_terminal.is_solved:
                            active_terminal.is_solved = True
                            player.points += active_terminal.reward_pts
                    else:
                        # Cek Interaksi Terminal
                        for t in terminals:
                            if player.rect.colliderect(t.rect.inflate(40, 40)) and not t.is_solved:
                                hacking_mode = True
                                active_terminal = t
                                break
                        
                        # Cek Interaksi Pintu
                        for d in doors:
                            if player.rect.colliderect(d.rect.inflate(40, 40)) and not d.is_open:
                                if player.points >= d.required_pts:
                                    d.is_open = True

        # --- 2. UPDATE LOGIC ---
        if not hacking_mode:
            player.move(keys, walls, doors)

        # --- 3. DRAWING / RENDER ---
        screen.fill(BG_COLOR)

        for r in rooms:
            pygame.draw.rect(screen, FLOOR_COLOR, r)
        for w in walls:
            pygame.draw.rect(screen, WALL_COLOR, w)

        for t in terminals:
            t.draw(screen)
            if not t.is_solved:
                info_text = tooltip_font.render(f"+{t.reward_pts} Pts", True, (100, 100, 100))
                screen.blit(info_text, (t.rect.x - 5, t.rect.y - 20))
                
                if player.rect.colliderect(t.rect.inflate(40, 40)):
                    prompt = tooltip_font.render("[E] Retas Soal", True, (0, 0, 0))
                    screen.blit(prompt, (t.rect.x - 20, t.rect.bottom + 5))

        for d in doors:
            d.draw(screen, player.points)
            if not d.is_open:
                req_text = tooltip_font.render(f"Butuh: {d.required_pts} Pts", True, (0, 0, 0))
                screen.blit(req_text, (d.rect.x - 30, d.rect.y - 20))
                
                if player.rect.colliderect(d.rect.inflate(40, 40)):
                    if player.points >= d.required_pts:
                        prompt = tooltip_font.render("[E] Buka Pintu", True, (0, 0, 0))
                    else:
                        prompt = tooltip_font.render("Poin Kurang!", True, (200, 50, 50))
                    screen.blit(prompt, (d.rect.x - 20, d.rect.bottom + 5))

        player.draw(screen)

        hud_bg = pygame.Surface((WIDTH, 40))
        hud_bg.set_alpha(150)
        hud_bg.fill((0, 0, 0))
        screen.blit(hud_bg, (0, 0))
        
        hud_text = font.render(f"ENERGY: {player.energy} | POINTS: {player.points}", True, (255, 255, 255))
        screen.blit(hud_text, (20, 10))

        if hacking_mode:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            box_width, box_height = 600, 400
            box_x = WIDTH//2 - box_width//2
            box_y = HEIGHT//2 - box_height//2
            
            pygame.draw.rect(screen, (30, 30, 40), (box_x, box_y, box_width, box_height), border_radius=10)
            pygame.draw.rect(screen, active_terminal.color, (box_x, box_y, box_width, box_height), width=3, border_radius=10)
            
            title = font.render(f"--- MERETAS TERMINAL TIER {active_terminal.tier} ---", True, (255, 255, 255))
            desc = font.render("Simulasi selesai. Tekan 'E' untuk mengklaim poin.", True, (150, 150, 150))
            screen.blit(title, (box_x + 100, box_y + 50))
            screen.blit(desc, (box_x + 50, box_y + 150))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()