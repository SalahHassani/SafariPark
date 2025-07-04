import sys, os, pygame
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.model.safariMap import Map

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    yield
    pygame.quit()

def test_map_has_capital_and_visitor_count():
    game_map = Map(difficulty="easy")
    assert hasattr(game_map, "capital")
    assert hasattr(game_map, "visitor_count")
    assert isinstance(game_map.visitor_count, int)