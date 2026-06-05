import pygame
import sys
import os
import time
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
        question_font = pygame.font.SysFont("consolas", 16)
    except:
        pygame.font.init()
        font = pygame.font.SysFont(None, 24, bold=True)
        tooltip_font = pygame.font.SysFont(None, 18)
        question_font = pygame.font.SysFont(None, 20)

    player_sprites, has_sprites = load_player_sprites()

    rooms = [
        pygame.Rect(400, 550, 200, 100), 
        pygame.Rect(450, 350, 100, 200), 
        pygame.Rect(400, 200, 200, 150), 
        pygame.Rect(100, 200, 200, 150), 
        pygame.Rect(700, 200, 200, 150), 
        pygame.Rect(300, 50, 400, 100),  
        pygame.Rect(100, 450, 150, 150), 
        pygame.Rect(750, 450, 150, 150), 
        pygame.Rect(300, 230, 100, 90),  
        pygame.Rect(600, 230, 100, 90),  
        pygame.Rect(450, 150, 100, 50),  
        pygame.Rect(135, 350, 80, 100),  
        pygame.Rect(785, 350, 80, 100),  
    ]

    door_rects = {
        "door_main": pygame.Rect(450, 400, 100, 40),
        "door_left": pygame.Rect(330, 230, 40, 90),
        "door_right": pygame.Rect(630, 230, 40, 90),
        "door_top": pygame.Rect(450, 155, 100, 40),
        "door_sec1": pygame.Rect(135, 380, 80, 40),
        "door_sec2": pygame.Rect(785, 380, 80, 40)
    }

    connection_rects = [
        pygame.Rect(451, 535, 98, 30),
        pygame.Rect(451, 335, 98, 30),
        pygame.Rect(285, 231, 30, 88),
        pygame.Rect(385, 231, 30, 88),
        pygame.Rect(585, 231, 30, 88),
        pygame.Rect(685, 231, 30, 88),
        pygame.Rect(451, 135, 98, 30),
        pygame.Rect(451, 185, 98, 30),
        pygame.Rect(136, 435, 78, 30),
        pygame.Rect(136, 335, 78, 30),
        pygame.Rect(786, 435, 78, 30),
        pygame.Rect(786, 335, 78, 30)
    ]

    initial_walls = []
    wall_thickness = 15
    for r in rooms:
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.bottom, r.width + wall_thickness*2, wall_thickness)) 
        initial_walls.append(pygame.Rect(r.left - wall_thickness, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 
        initial_walls.append(pygame.Rect(r.right, r.top - wall_thickness, wall_thickness, r.height + wall_thickness*2)) 

    walls = []
    carvers = list(door_rects.values()) + connection_rects
    
    for w in initial_walls:
        pieces = [w]
        for c in carvers:
            new_pieces = []
            for p in pieces:
                if p.colliderect(c):
                    if p.width > p.height: 
                        left = pygame.Rect(p.x, p.y, c.left - p.x, p.height)
                        right = pygame.Rect(c.right, p.y, p.right - c.right, p.height)
                        if left.width > 0: new_pieces.append(left)
                        if right.width > 0: new_pieces.append(right)
                    else: 
                        top = pygame.Rect(p.x, p.y, p.width, c.top - p.y)
                        bottom = pygame.Rect(p.x, c.bottom, p.width, p.bottom - c.bottom)
                        if top.height > 0: new_pieces.append(top)
                        if bottom.height > 0: new_pieces.append(bottom)
                else:
                    new_pieces.append(p)
            pieces = new_pieces
        walls.extend(pieces)

    terminal_rects = {
        "term_tut": pygame.Rect(480, 570, 40, 40), 
        "term_e1": pygame.Rect(120, 220, 40, 40),  
        "term_e2": pygame.Rect(220, 220, 40, 40),
        "term_e3": pygame.Rect(120, 280, 40, 40),
        "term_m1": pygame.Rect(720, 220, 40, 40),  
        "term_m2": pygame.Rect(820, 220, 40, 40),
        "term_m3": pygame.Rect(720, 280, 40, 40),
        "term_h1": pygame.Rect(350, 70, 40, 40),   
        "term_h2": pygame.Rect(500, 70, 40, 40),
        "term_h3": pygame.Rect(600, 70, 40, 40),
        "term_sec1": pygame.Rect(150, 500, 40, 40),
        "term_sec2": pygame.Rect(800, 500, 40, 40) 
    }

    terminal_visuals = {
        "term_tut": {"tier": "T", "color": (150, 150, 150)},
        "term_e1": {"tier": "E", "color": (50, 150, 200)},
        "term_e2": {"tier": "E", "color": (50, 150, 200)},
        "term_e3": {"tier": "E", "color": (50, 150, 200)},
        "term_m1": {"tier": "M", "color": (200, 150, 50)},
        "term_m2": {"tier": "M", "color": (200, 150, 50)},
        "term_m3": {"tier": "M", "color": (200, 150, 50)},
        "term_h1": {"tier": "H", "color": (200, 50, 200)},
        "term_h2": {"tier": "H", "color": (200, 50, 200)},
        "term_h3": {"tier": "H", "color": (200, 50, 200)},
        "term_sec1": {"tier": "S", "color": (255, 100, 100)},
        "term_sec2": {"tier": "S", "color": (255, 100, 100)}
    }

    has_spawned = False
    hacking_mode = False
    active_terminal_id = None
    user_text = ""
    running = True

    while running:
        state = net_client.game_state
        map_state = state.get("map_state", {})
        terms_state = map_state.get("terminals", {})
        doors_state = map_state.get("doors", {}) 
        players_data = state.get("players", {}) 
        
        my_pts = players_data.get(player_id, {}).get("points", 0)
        my_nrg = players_data.get(player_id, {}).get("energy", 0)
        
        my_data = players_data.get(player_id)
        player_rect = pygame.Rect(0, 0, 40, 55)
        if my_data:
            player_rect.topleft = (my_data.get("x", 0), my_data.get("y", 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if hacking_mode:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        hacking_mode = False
                        user_text = ""
                    elif event.key == pygame.K_RETURN:
                        if active_terminal_id and user_text.strip():
                            net_client.send({
                                "type": "action", 
                                "action": "submit_flag", 
                                "terminal_id": active_terminal_id,
                                "flag": user_text
                            })
                        hacking_mode = False
                        user_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        user_text += event.unicode
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    for t_id, t_rect in terminal_rects.items():
                        if player_rect.colliderect(t_rect.inflate(40, 40)) and not terms_state.get(t_id, {}).get("is_solved"):
                            hacking_mode = True
                            active_terminal_id = t_id
                            user_text = ""
                            break
                            
                    for d_id, d_rect in door_rects.items():
                        if player_rect.colliderect(d_rect.inflate(40, 40)) and not doors_state.get(d_id, {}).get("is_open"):
                            net_client.send({"type": "action", "action": "open_door", "door_id": d_id})

        if not has_spawned:
            net_client.send({"type": "action", "action": "move", "x": 480, "y": 580, "dir": "down"})
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
            vis = terminal_visuals.get(t_id, {"tier": "?", "color": TERMINAL_COLOR})
            reward = t_data.get("reward", 0)
            
            draw_color = (100, 100, 100) if t_data.get("is_solved") else vis["color"]
            pygame.draw.rect(screen, draw_color, t_rect)
            
            tier_text = font.render(vis["tier"], True, (255, 255, 255))
            text_rect = tier_text.get_rect(center=t_rect.center)
            screen.blit(tier_text, text_rect)
            
            if not t_data.get("is_solved"):
                info_text = tooltip_font.render(f"+{reward} Pts/Nrg", True, (100, 100, 100))
                screen.blit(info_text, (t_rect.x - 15, t_rect.y - 20))
                
                if player_rect.colliderect(t_rect.inflate(40, 40)):
                    prompt = tooltip_font.render("[E] Retas Soal", True, (255, 255, 255))
                    screen.blit(prompt, (t_rect.x - 20, t_rect.bottom + 5))

        for d_id, d_rect in door_rects.items():
            d_data = doors_state.get(d_id, {})
            is_open = d_data.get("is_open")
            req_energy = d_data.get("required_energy", 0)
            
            color = DOOR_OPEN if is_open else DOOR_COLOR
            pygame.draw.rect(screen, color, d_rect)
            
            if not is_open:
                req_text = tooltip_font.render(f"Butuh: {req_energy} Nrg", True, (255, 255, 255))
                screen.blit(req_text, (d_rect.x - 30, d_rect.y - 20))
                
                if player_rect.colliderect(d_rect.inflate(40, 40)):
                    if my_nrg >= req_energy:
                        prompt = tooltip_font.render("[E] Buka Pintu", True, (255, 255, 255))
                    else:
                        prompt = tooltip_font.render("Energy Kurang!", True, (255, 50, 50))
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
            
            box_width, box_height = 800, 500
            box_x = WIDTH//2 - box_width//2
            box_y = HEIGHT//2 - box_height//2
            
            active_vis = terminal_visuals.get(active_terminal_id, {})
            active_data = terms_state.get(active_terminal_id, {})
            
            pygame.draw.rect(screen, (30, 30, 40), (box_x, box_y, box_width, box_height), border_radius=10)
            pygame.draw.rect(screen, active_vis.get("color", TERMINAL_COLOR), (box_x, box_y, box_width, box_height), width=3, border_radius=10)
            
            title = font.render(f"--- MERETAS TERMINAL TIER {active_vis.get('tier', '?')} ---", True, (255, 255, 255))
            screen.blit(title, (box_x + 30, box_y + 30))
            
            question_str = active_data.get("question", "Tunggu data dari server...")
            q_text = question_font.render(question_str, True, (200, 200, 200))
            screen.blit(q_text, (box_x + 30, box_y + 100))
            
            input_box = pygame.Rect(box_x + 30, box_y + 200, box_width - 60, 40)
            pygame.draw.rect(screen, (10, 10, 15), input_box)
            pygame.draw.rect(screen, active_vis.get("color", TERMINAL_COLOR), input_box, 2)
            
            txt_surface = font.render(user_text, True, (255, 255, 255))
            screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))
            
            if time.time() % 1 > 0.5:
                cursor_x = input_box.x + 10 + txt_surface.get_width()
                pygame.draw.rect(screen, (255, 255, 255), (cursor_x, input_box.y + 10, 2, 20))
                
            guide1 = tooltip_font.render("Ketik jawaban (FLAG) dan tekan ENTER untuk submit.", True, (150, 150, 150))
            guide2 = tooltip_font.render("Tekan ESC untuk membatalkan proses peretasan.", True, (150, 150, 150))
            screen.blit(guide1, (box_x + 30, box_y + 400))
            screen.blit(guide2, (box_x + 30, box_y + 420))

        pygame.display.flip()
        clock.tick(FPS)