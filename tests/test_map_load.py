# File: tests/test_safari_map.py
import sys, os
import pygame
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.model.safariMap import Map

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    yield
    pygame.quit()

def test_map_initializes():
    game_map = Map(difficulty="easy")
    assert game_map is not None
    assert hasattr(game_map, "visitor_count")

def test_map_has_font_and_capital():
    game_map = Map("medium")
    assert game_map.font is not None
    assert game_map.capital == 10_000