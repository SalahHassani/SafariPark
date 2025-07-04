# src/utils/sound_manager.py
import pygame
import os

def play_background_music():
    pygame.mixer.init()
    path = os.path.join("src", "assets", "sounds", "nature.mp3")
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(loops=-1)



