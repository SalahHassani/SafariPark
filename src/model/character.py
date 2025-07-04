# character.py
import pygame
from src.config.settings import *

CHARACTER_DETECTION_RADIUS = 180

class Character(pygame.sprite.Sprite):
    def __init__(self, pos, group, map_rect):
        super().__init__(group)
        self.frame_index = 0
        self.direction = pygame.Vector2()
        self.last_direction = pygame.Vector2(0, 1)
        self.pos = pygame.math.Vector2(pos)
        self.speed = 60
        self.map_rect = map_rect
        self.z = LAYERS['main']

        self.pattern = [
            pygame.Vector2(0, 1), pygame.Vector2(1, 1), pygame.Vector2(1, 0),
            pygame.Vector2(1, -1), pygame.Vector2(0, -1), pygame.Vector2(-1, -1),
            pygame.Vector2(-1, 0), pygame.Vector2(-1, 1)
        ]
        self.current_step = 0
        self.step_timer = 0
        self.step_duration = 1.2
        self.idle_phase = False

        self.max_health = 100
        self.health = self.max_health

    def move(self, dt):
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
        self.pos += self.direction * self.speed * dt
        self.pos.x = max(self.map_rect.left, min(self.pos.x, self.map_rect.right))
        self.pos.y = max(self.map_rect.top, min(self.pos.y, self.map_rect.bottom))
        self.rect.center = self.pos

    def patrol_input(self, dt):
        self.step_timer += dt
        self.direction = pygame.Vector2()
        if self.step_timer >= self.step_duration:
            self.step_timer = 0
            self.idle_phase = not self.idle_phase
            if not self.idle_phase:
                self.current_step = (self.current_step + 1) % len(self.pattern)
        if not self.idle_phase:
            self.direction = self.pattern[self.current_step]


    #############################################################################################
    #############################################################################################
    def draw_detection_range(self, surface: pygame.Surface, cam_offset: pygame.Vector2, *,
     radius: int = CHARACTER_DETECTION_RADIUS) -> None:

        screen_r = pygame.Rect(cam_offset.x, cam_offset.y, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.rect.colliderect(screen_r):
            pygame.draw.circle(surface, (255, 100, 100), self.rect.center - cam_offset, radius, 2)
    #############################################################################################
