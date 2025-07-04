# ──────────────────────────────────────────────────────────────────────────────
# pauseMenu.py – Handles the in-game pause menu UI and its interactions
# ──────────────────────────────────────────────────────────────────────────────

import pygame
import sys

# ──────────────────────────────────────────────────────────────────────────────
# PauseMenu Class – Renders pause overlay, buttons, and handles click events
# ──────────────────────────────────────────────────────────────────────────────
class PauseMenu:
    """
    Handles rendering and interaction for the in-game pause menu.
    Displays options to resume, start a new game, exit, toggle tutorial, and toggle day/night.
    """

    def __init__(self, x, y, width, height, text, font, text_color, game_reference=None):
        """
        Initializes the PauseMenu component.
        """
        # Display setup
        self.display_surface = pygame.display.get_surface()
        self.screen_width, self.screen_height = self.display_surface.get_size()

        # Menu button position
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text_color = text_color
        self.game_reference = game_reference
        self.new_game_requested = False

        # States
        self.is_hovered = False
        self.menu_open = False
        self.tutorial_manager = getattr(game_reference, 'tutorial_manager', None)

        # ──────────────────────────────────────────────────────────────────────
        # UI Colors (theme)
        # ──────────────────────────────────────────────────────────────────────
        self.colors = {
            "primary": (70, 90, 120),
            "secondary": (100, 130, 160),
            "dark": (50, 60, 80),
            "accent": (180, 150, 120),
            "text": (235, 235, 245),
            "white": (255, 255, 255),
            "item_bg": (60, 75, 95)
        }

        # ──────────────────────────────────────────────────────────────────────
        # Menu Dimensions & Header Font
        # ──────────────────────────────────────────────────────────────────────
        self.pause_menu_width = 400
        self.pause_menu_height = 400
        self.menu_rect = pygame.Rect(
            (self.screen_width - self.pause_menu_width) // 2,
            (self.screen_height - self.pause_menu_height) // 2,
            self.pause_menu_width,
            self.pause_menu_height
        )

        self.header_font = pygame.font.SysFont(None, 36)

        # ──────────────────────────────────────────────────────────────────────
        # Menu Option Buttons
        # ──────────────────────────────────────────────────────────────────────
        self.menu_options = [
            "Resume",
            "Start a new game",
            "Exit",
            "Tutorial",
            "Day/Night"
        ]
        self._create_buttons()

    # ──────────────────────────────────────────────────────────────────────────────
    # Button Setup – Layout and positioning
    # ──────────────────────────────────────────────────────────────────────────────
    def _create_buttons(self):
        """Create button rectangles for each menu option."""
        self.option_buttons = []
        button_width = 250
        button_height = 45
        spacing = 15

        total_height = len(self.menu_options) * button_height + (len(self.menu_options) - 1) * spacing
        start_y = self.menu_rect.y + 70 + ((self.pause_menu_height - 70) - total_height) // 2

        for i, option in enumerate(self.menu_options):
            button_rect = pygame.Rect(
                self.menu_rect.centerx - button_width // 2,
                start_y + i * (button_height + spacing),
                button_width,
                button_height
            )
            self.option_buttons.append((option, button_rect))

    # ──────────────────────────────────────────────────────────────────────────────
    # Rendering the menu (buttons, overlay, close button, etc.)
    # ──────────────────────────────────────────────────────────────────────────────
    def draw(self, surface):
        """Draws the pause menu or the menu button depending on the state."""
        mouse_pos = pygame.mouse.get_pos()

        if self.menu_open:
            # Dimmed overlay background
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))

            # Menu background
            menu_surface = pygame.Surface((self.pause_menu_width, self.pause_menu_height), pygame.SRCALPHA)
            pygame.draw.rect(menu_surface, (*self.colors["primary"], 180), menu_surface.get_rect(), border_radius=15)
            surface.blit(menu_surface, self.menu_rect.topleft)
            pygame.draw.rect(surface, self.colors["dark"], self.menu_rect, 2, border_radius=15)

            # Header
            header_rect = pygame.Rect(self.menu_rect.x, self.menu_rect.y, self.pause_menu_width, 40)
            pygame.draw.rect(surface, self.colors["dark"], header_rect, border_top_left_radius=15, border_top_right_radius=15)

            header_text = self.header_font.render("Game Menu", True, self.colors["white"])
            surface.blit(header_text, (
                self.menu_rect.x + (self.pause_menu_width - header_text.get_width()) // 2,
                self.menu_rect.y + 8
            ))

            self._draw_close_button(surface)

            # Menu buttons
            for option, rect in self.option_buttons:
                is_hovered = rect.collidepoint(mouse_pos)
                color = self.colors["accent"] if is_hovered else self.colors["secondary"]

                pygame.draw.rect(surface, color, rect, border_radius=10)
                pygame.draw.rect(surface, self.colors["dark"], rect, 2, border_radius=10)

                # Standard button label
                label = self.font.render(option, True, self.colors["text"])
                
                # Check if this is the Day/Night button and add the state indicator
                if option == "Day/Night" and hasattr(self.game_reference, 'day_night_cycle'):
                    # Get current state
                    state = "Night" if self.game_reference.day_night_cycle.is_night else "Day"
                    
                    # Render the option with the state
                    combined_text = f"{option} ({state})"
                    label = self.font.render(combined_text, True, self.colors["text"])
                
                # Position the label
                surface.blit(label, (
                    rect.x + (rect.width - label.get_width()) // 2,
                    rect.y + (rect.height - label.get_height()) // 2
                ))
        else:
            self._draw_hamburger_icon(surface, mouse_pos)

    # ──────────────────────────────────────────────────────────────────────────────
    # Close Button (X) in top-right of menu
    # ──────────────────────────────────────────────────────────────────────────────
    def _draw_close_button(self, surface):
        """Draws the close (X) button in the top-right corner."""
        radius = 12
        center = (self.menu_rect.x + self.pause_menu_width - 20, self.menu_rect.y + 20)

        pygame.draw.circle(surface, self.colors["white"], center, radius)
        pygame.draw.circle(surface, self.colors["dark"], center, radius, 2)

        offset = 6
        pygame.draw.line(surface, self.colors["dark"], (center[0] - offset, center[1] - offset),
                         (center[0] + offset, center[1] + offset), 2)
        pygame.draw.line(surface, self.colors["dark"], (center[0] - offset, center[1] + offset),
                         (center[0] + offset, center[1] - offset), 2)

        self.close_button = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)

    # ──────────────────────────────────────────────────────────────────────────────
    # Hamburger Icon (when menu is collapsed)
    # ──────────────────────────────────────────────────────────────────────────────
    def _draw_hamburger_icon(self, surface, mouse_pos):
        """Draws the hamburger menu button."""
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(surface, self.colors["secondary"], self.rect, border_radius=8)

        bar_width = self.rect.width * 0.6
        bar_height = 4
        gap = 5
        start_x = self.rect.x + (self.rect.width - bar_width) / 2
        start_y = self.rect.y + (self.rect.height - (3 * bar_height + 2 * gap)) / 2

        for i in range(3):
            bar_rect = pygame.Rect(start_x, start_y + i * (bar_height + gap), bar_width, bar_height)
            pygame.draw.rect(surface, self.colors["dark"], bar_rect)

    # ──────────────────────────────────────────────────────────────────────────────
    # Event Handling: Click interactions for open/close + menu actions
    # ──────────────────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        """
        Handles user interaction with the pause menu.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if not self.menu_open and self.rect.collidepoint(mouse_pos):
                self.menu_open = True
                return True

            elif self.menu_open:
                if self.close_button.collidepoint(mouse_pos):
                    self.menu_open = False
                    return True

                for option, rect in self.option_buttons:
                    if rect.collidepoint(mouse_pos):
                        return self._handle_option_click(option)

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)

        return False

    # ──────────────────────────────────────────────────────────────────────────────
    # Executes menu option logic when selected
    # ──────────────────────────────────────────────────────────────────────────────
    def _handle_option_click(self, option):
        """Executes the functionality tied to a specific option."""
        if option == "Resume":
            self.menu_open = False
        elif option == "Start a new game":
            self.new_game_requested = True
            self.menu_open = False
        elif option == "Exit":
            pygame.quit()
            sys.exit()
        elif option == "Tutorial" and self.tutorial_manager:
            self.tutorial_manager.start()
            self.menu_open = False
        elif option == "Day/Night":
            print("Day/Night option clicked")
            # Debug checks
            print(f"game_reference exists: {self.game_reference is not None}")
            
            # Access the map through the game reference
            if self.game_reference and hasattr(self.game_reference, 'map'):
                try:
                    self.game_reference.map.toggle_day_night()
                    self.menu_open = False
                    print("Day/Night toggled successfully")
                except Exception as e:
                    print(f"Error toggling day/night: {e}")

        return True