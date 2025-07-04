import pygame
from src.config.settings import *

class Overlay:
    def __init__(self, player):
        
        
        self.display = pygame.display.get_surface()
        self.player = player
        