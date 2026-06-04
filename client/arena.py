import pygame
import sys
import os
from client.network_client import NetworkClient
from shared.config import *

def load_player_sprites():
    pygame.init()
    base_path = os.path.join('assets', 'player1')
    try:
        sprites = {
            'up': pygame.image.load(os.path.join(base_path, 'player_up.png')).convert_alpha(),
            'down': pygame.image.load(os.path.join(base_path, 'player_down.png')).convert_alpha(),
            'left': pygame.image.load(os.path.join(base_path, 'player_left.png')).convert_alpha(),
            'right': pygame.image.load(os.path.join(base_path, 'player_right.png')).convert_alpha()
        }
        for key in sprites:
            sprites[key] = pygame.transform.scale(sprites[key], (40, 55))
        return sprites, True
    except Exception:
        return None, False

def run_game(player_id, net_client):
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"CipherCamp CTF - {player_id}")
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("consolas", 18, bold=True)
        tooltip_font = pygame.font.SysFont("consolas", 14)
    except:
        pygame.font.init()
        font = pygame.font.SysFont(None, 24, bold=True)
        tooltip_font = pygame.font.SysFont(None, 18)

    player_sprites, has_sprites = load_player_sprites()

    rooms = [
        pygame.Rect(300, 150, 400, 400), 
        pygame.Rect(50, 150, 200, 150),  
        pygame.Rect(750, 150, 200, 150), 
        pygame.Rect(400, 550, 200, 100)  
    ]

    door_rects = {
        "door_1": pygame.Rect(250, 200, 50, 60),
        "door_2": pygame.Rect(700, 200, 50, 60)
    }

    initial_walls = []
    wall_thickness = 15
    for r in rooms:
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.bottom, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 
        initial_walls.append(pygame.Rect(r.right, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 

    walls = []
    for w in initial_walls:
        is_carved = False
        for d_id, d_rect in door_rects.items():
            if w.colliderect(d_rect):
                wall_top = pygame.Rect(w.x, w.y, w.width, d_rect.top - w.y)
                wall_bottom = pygame.Rect(w.x, d_rect.bottom, w.width, w.bottom - d_rect.bottom)
                if wall_top.height > 0: walls.append(wall_top)
                if wall_bottom.height > 0: walls.append(wall_bottom)
                is_carved = True
                break
        if not is_carved:
            walls.append(w)

    terminal_rects = {
        "term_1": pygame.Rect(450, 300, 40, 40),
        "term_2": pygame.Rect(550, 300, 40, 40),
        "term_3": pygame.Rect(100, 200, 40, 40),
        "term_4": pygame.Rect(850, 200, 40, 40)
    }

    terminal_visuals = {
        "term_1": {"tier": "E", "color": (50, 150, 200), "reward": 50},
        "term_2": {"tier": "E", "color": (50, 150, 200), "reward": 50},
        "term_3": {"tier": "M", "color": (200, 150, 50), "reward": 100},
        "term_4": {"tier": "H", "color": (200, 50, 200), "reward": 300}
    }

    has_spawned = False
    hacking_mode = False
    active_terminal_id = None
    running = True

    while running:
        state = net_client.game_state
        map_state = state.get("map_state", {})
        terms_state = map_state.get("terminals", {})
        doors_state = map_state.get("doors", {}) 
        players_data = state.get("players", {}) 
        
        my_pts = players_data.get(player_id, {}).get("points", 0)
        my_nrg = players_data.get(player_id, {}).get("energy", 100)
        
        my_data = players_data.get(player_id)
        player_rect = pygame.Rect(0, 0, 40, 55)
        if my_data:
            player_rect.topleft = (my_data.get("x", 0), my_data.get("y", 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if hacking_mode:
                    hacking_mode = False
                    if active_terminal_id and not terms_state.get(active_terminal_id, {}).get("is_solved"):
                        net_client.send({"type": "action", "action": "hack_terminal", "terminal_id": active_terminal_id})
                else:
                    for t_id, t_rect in terminal_rects.items():
                        if player_rect.colliderect(t_rect.inflate(40, 40)) and not terms_state.get(t_id, {}).get("is_solved"):
                            hacking_mode = True
                            active_terminal_id = t_id
                            break
                            
                    for d_id, d_rect in door_rects.items():
                        if player_rect.colliderect(d_rect.inflate(40, 40)) and not doors_state.get(d_id, {}).get("is_open"):
                            net_client.send({"type": "action", "action": "open_door", "door_id": d_id})

        if not has_spawned:
            net_client.send({"type": "action", "action": "move", "x": 480, "y": 320, "dir": "down"})
            has_spawned = True
            
        if my_data and not hacking_mode:
            new_x, new_y = my_data["x"], my_data["y"]
            current_dir = my_data.get("dir", "down")
            speed = 5
            moved = False
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]: new_y -= speed; moved = True; current_dir = "up"
            if keys[pygame.K_s]: new_y += speed; moved = True; current_dir = "down"
            if keys[pygame.K_a]: new_x -= speed; moved = True; current_dir = "left"
            if keys[pygame.K_d]: new_x += speed; moved = True; current_dir = "right"
            
            if moved:
                test_rect = pygame.Rect(new_x, new_y, 40, 55)
                collision = False
                
                for w in walls:
                    if test_rect.colliderect(w):
                        collision = True
                        break
                        
                for d_id, d_rect in door_rects.items():
                    if not doors_state.get(d_id, {}).get("is_open") and test_rect.colliderect(d_rect):
                        collision = True
                        break
                        
                if not collision:
                    net_client.send({"type": "action", "action": "move", "x": new_x, "y": new_y, "dir": current_dir})

        screen.fill(BG_COLOR)

        for r in rooms:
            pygame.draw.rect(screen, FLOOR_COLOR, r)
            
        for w in walls:
            pygame.draw.rect(screen, WALL_COLOR, w)

        for t_id, t_rect in terminal_rects.items():
            t_data = terms_state.get(t_id, {})
            vis = terminal_visuals.get(t_id, {"tier": "?", "color": TERMINAL_COLOR, "reward": 0})
            
            draw_color = (100, 100, 100) if t_data.get("is_solved") else vis["color"]
            pygame.draw.rect(screen, draw_color, t_rect)
            
            tier_text = font.render(vis["tier"], True, (255, 255, 255))
            text_rect = tier_text.get_rect(center=t_rect.center)
            screen.blit(tier_text, text_rect)
            
            if not t_data.get("is_solved"):
                info_text = tooltip_font.render(f"+{vis['reward']} Pts", True, (100, 100, 100))
                screen.blit(info_text, (t_rect.x - 5, t_rect.y - 20))
                
                if player_rect.colliderect(t_rect.inflate(40, 40)):
                    prompt = tooltip_font.render("[E] Retas Soal", True, (255, 255, 255))
                    screen.blit(prompt, (t_rect.x - 20, t_rect.bottom + 5))

        for d_id, d_rect in door_rects.items():
            d_data = doors_state.get(d_id, {})
            is_open = d_data.get("is_open")
            req_pts = 50 if d_id == "door_1" else 150
            
            color = DOOR_OPEN if is_open else DOOR_COLOR
            pygame.draw.rect(screen, color, d_rect)
            
            if not is_open:
                req_text = tooltip_font.render(f"Butuh: {req_pts} Pts", True, (255, 255, 255))
                screen.blit(req_text, (d_rect.x - 30, d_rect.y - 20))
                
                if player_rect.colliderect(d_rect.inflate(40, 40)):
                    if my_pts >= req_pts:
                        prompt = tooltip_font.render("[E] Buka Pintu", True, (255, 255, 255))
                    else:
                        prompt = tooltip_font.render("Poin Kurang!", True, (255, 50, 50))
                    screen.blit(prompt, (d_rect.x - 20, d_rect.bottom + 5))

        for pid, p_data in players_data.items():
            p_x = p_data.get("x", 0)
            p_y = p_data.get("y", 0)
            p_dir = p_data.get("dir", "down")
            
            if has_sprites and player_sprites and p_dir in player_sprites:
                screen.blit(player_sprites[p_dir], (p_x, p_y)) 
            else:
                p_color = PLAYER_ME_COLOR if pid == player_id else PLAYER_OTHER_COLOR
                pygame.draw.rect(screen, p_color, (p_x, p_y, 40, 55))
                
            name_text = tooltip_font.render(pid, True, TEXT_COLOR)
            screen.blit(name_text, (p_x, p_y - 20))

        hud_bg = pygame.Surface((WIDTH, 40))
        hud_bg.set_alpha(180)
        hud_bg.fill((10, 10, 20))
        screen.blit(hud_bg, (0, HEIGHT-40)) 
        
        ping = state.get("ping", 0)
        hud_txt = font.render(f"PID: {player_id} | ENERGY: {my_nrg} | POINTS: {my_pts} | PING: {ping}ms", True, TEXT_COLOR)
        screen.blit(hud_txt, (20, HEIGHT-30))

        if hacking_mode and active_terminal_id:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            box_width, box_height = 600, 400
            box_x = WIDTH//2 - box_width//2
            box_y = HEIGHT//2 - box_height//2
            
            active_vis = terminal_visuals.get(active_terminal_id, {})
            
            pygame.draw.rect(screen, (30, 30, 40), (box_x, box_y, box_width, box_height), border_radius=10)
            pygame.draw.rect(screen, active_vis.get("color", TERMINAL_COLOR), (box_x, box_y, box_width, box_height), width=3, border_radius=10)
            
            title = font.render(f"--- MERETAS TERMINAL TIER {active_vis.get('tier', '?')} ---", True, (255, 255, 255))
            desc = font.render("Simulasi selesai. Tekan 'E' untuk mengklaim poin.", True, (150, 150, 150))
            screen.blit(title, (box_x + 100, box_y + 50))
            screen.blit(desc, (box_x + 50, box_y + 150))

        pygame.display.flip()
        clock.tick(FPS)