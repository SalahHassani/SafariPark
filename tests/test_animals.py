import sys, os, pygame
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.model.animals import Carnivore, Herbivore

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_carnivore_init():
    dummy_pos = (100, 200)
    dummy_group = pygame.sprite.Group()
    dummy_map_rect = pygame.Rect(0, 0, 1000, 1000)
    dummy_price = 300

    carn = Carnivore("Wolfie", "baby-wolf", 1, dummy_pos, dummy_group, dummy_map_rect, dummy_price)
    assert carn.name == "Wolfie"

def test_herbivore_init():
    dummy_pos = (50, 60)
    dummy_group = pygame.sprite.Group()
    dummy_map_rect = pygame.Rect(0, 0, 1000, 1000)
    dummy_price = 100

    herb = Herbivore("Deery", "deer", 2, dummy_pos, dummy_group, dummy_map_rect, dummy_price)
    assert herb.name == "Deery"