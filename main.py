import pygame
import sys
from src.config.settings import *
from src.model.safariMap import Map
from src.view.startWindow import select_difficulty
from src.view.pauseMenu import PauseMenu
from src.view.tutorialManager import TutorialManager
from src.view.dayNightCycle import DayNightCycle
from src.model.jeep import Jeep

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Safari Park')
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = self.menu_screen
        self.selected_difficulty = None
        self.tutorial_manager = TutorialManager(self)
        self.map = None
    def run(self):
        while self.running:
            self.current_screen()
            
    def menu_screen(self, skip_intro=False):
        self.selected_difficulty = select_difficulty(self.screen, skip_intro)
        if self.selected_difficulty is None:
            self.running = False
            pygame.quit()
            sys.exit()
            
        self.map = Map(difficulty=self.selected_difficulty, game_reference=self)
        jeep_start = self.map.jeep_start
        if jeep_start:
            self.current_screen = self.game_screen  # <-- ✅ THIS IS MANDATORY!
            
    def game_screen(self):
        if not hasattr(self, 'tutorial_completed'):
            self.tutorial_manager.start()
            self.tutorial_completed = True
        game_running = True
        while game_running:
            events = pygame.event.get()
            dt = self.clock.tick(60) / 1000.0
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                # Handle tutorial events first (when active)
                if self.tutorial_manager.active and self.tutorial_manager.handle_event(event):
                    continue
                    
                if self.map.time_indicator.handle_event(event):
                    continue
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.map.day_night_rect.collidepoint(event.pos):
                        self.map.toggle_day_night()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        self.map.toggle_day_night()

                if self.map.pause_menu.handle_event(event):
                    self.map.paused = self.map.pause_menu.menu_open
                    if self.map.pause_menu.new_game_requested:
                        self.map.pause_menu.new_game_requested = False
                        self.current_screen = lambda: self.menu_screen(skip_intro=True)
                        return
                        
                if not self.map.paused:
                    self.map.store_ui.handle_event(event)
                    
            self.map.run(dt, events)
            if self.map.new_game_requested:
                self.map.new_game_requested = False
                self.current_screen = lambda: self.menu_screen(skip_intro=True)
                return

            if self.tutorial_manager.active:
                self.tutorial_manager.draw()
            
            pygame.display.update()

if __name__ == '__main__':
    game = Game()
    game.run()
    
    