from shared.config import *
import pygame
import random
import math

MAX_ROOM_SEPERATION_ITER = 200

class Door:
    def __init__(self, id, rect, required_pts):
        self.id = id
        self.rect = pygame.Rect(rect)
        self.required_pts = required_pts
        self.is_open = False

    def draw(self, surface, player_pts):
        if not self.is_open:
            color = DOOR_OPEN if player_pts >= self.required_pts else DOOR_COLOR
            pygame.draw.rect(surface, color, self.rect)

class Terminal:
    def __init__(self, id, x, y, tier, color, reward_pts):
        self.id = id
        self.rect = pygame.Rect(x, y, 40, 40)
        self.tier = tier
        self.color = color
        self.reward_pts = reward_pts
        self.is_solved = False

    def draw(self, surface, font):
        draw_color = (100, 100, 100) if self.is_solved else self.color
        pygame.draw.rect(surface, draw_color, self.rect)
        text = font.render(self.tier, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

class Map:
    def __init__(self):
        self.doors : list[Door] = []
        self.terminal : list[Terminal] = []
        self.rooms = []
    def generate():
        initial_rooms : list[pygame.Rect] = []
        for i in range(1, 15):
            initial_rooms.append(pygame.Rect(0, 0, random.randint(4, 7), random.randint(4, 7)))
        separation_iter_count = 0
        continue_iter = True
        while (separation_iter_count < MAX_ROOM_SEPERATION_ITER | continue_iter):
            continue_iter = False
            separation_iter_count += 1
            for i, room_rect in enumerate(initial_rooms):
                for j, other_rect in enumerate(initial_rooms):
                    overlap_bound = other_rect.inflate(1)
                    if i != j :
                        # Steer rooms away
                        if(overlap_bound.colliderect(room_rect)):
                            continue_iter = True
                            dx = overlap_bound.x - room_rect.x
                            px = (overlap_bound.centerx + room_rect.centerx) - abs(dx)
                            dy = overlap_bound.y - room_rect.y
                            py = (overlap_bound.centery - room_rect.centery) - abs(dy)
                            if (px < py):
                                room_rect.x = overlap_bound.x + (overlap_bound.centerx * math.copysign(1, dx))
                            else:
                                pass # WIP


                            
                            


