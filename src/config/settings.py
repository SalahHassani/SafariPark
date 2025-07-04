from pygame.math import Vector2
import pygame


pygame.init()

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w - 150, info.current_h - 150

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

TILE_SIZE = 64


# overlay positions 
OVERLAY_POSITIONS = {
	'tool' : (40, SCREEN_HEIGHT - 15), 
	'seed': (70, SCREEN_HEIGHT - 5)}

PLAYER_TOOL_OFFSET = {
	'left': Vector2(-50,40),
	'right': Vector2(50,40),
	'up': Vector2(0,-10),
	'down': Vector2(0,50)
}

LAYERS = {
	'water': 1,
	'grass': 2,
    'road':3,
	'hill': 4,
	'tiles': 5,
	'house_floor': 6,
	'house_walls': 7,
	'fence': 8,
    'roadtiles':9,
	'flowers': 10,
	'trees': 11,
	'mushrooms': 12,
    'main':13,
	'player_spawn': 14,
    'hit':15,
    'jeep':16,
    'jeep_path':17
}

APPLE_POS = {
	'Small': [(18,17), (30,37), (12,50), (30,45), (20,30), (30,10)],
	'Large': [(30,24), (60,65), (50,50), (16,40),(45,50), (42,70)]
}

GROW_SPEED = {
	'corn': 1,
	'tomato': 0.7
}

SALE_PRICES = {
	'wood': 4,
	'apple': 2,
	'corn': 10,
	'tomato': 20
}
PURCHASE_PRICES = {
	'corn': 4,
	'tomato': 5
}
