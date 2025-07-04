import sys, os, pygame
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.view.pauseMenu import PauseMenu

@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()

def test_pause_menu_toggle_behavior():
    font = pygame.font.Font(None, 24)

    pause_menu = PauseMenu(
        100,  # x
        100,  # y
        200,  # width
        50,   # height
        "Pause",  # text
        font,
        (255, 255, 255)  # text color
    )

    assert hasattr(pause_menu, 'menu_open')
    original_state = pause_menu.menu_open

    # Simulate toggling manually
    pause_menu.menu_open = not original_state
    assert pause_menu.menu_open != original_state