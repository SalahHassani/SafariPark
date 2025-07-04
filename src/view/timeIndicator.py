# ──────────────────────────────────────────────────────────────────────────────
# timeIndicator.py – UI element to display and manage in-game time progression
# ──────────────────────────────────────────────────────────────────────────────

import pygame

# ──────────────────────────────────────────────────────────────────────────────
# TimeIndicator: Controls in-game time display and speed adjustment
# ──────────────────────────────────────────────────────────────────────────────
class TimeIndicator:
    def __init__(self, difficulty):
        """
        Initialize the time indicator UI.
        Configures months/days based on difficulty and sets up layout.
        """
        self.display_surface = pygame.display.get_surface()
        self.screen_width = self.display_surface.get_width()
        
        self.time_mode = "day"  # Default mode
        self.time_modes = ["hour", "day", "week"]

        # Time settings based on difficulty
        self.difficulty = difficulty
        if difficulty == "Easy":
            self.total_months = 3
            self.days_per_minute = 3
        elif difficulty == "Medium":
            self.total_months = 6
            self.days_per_minute = 6
        elif difficulty == "Hard":
            self.total_months = 12
            self.days_per_minute = 12

        # Time tracking variables
        self.elapsed_seconds = 0
        self.current_day = 1
        self.current_month = 1
        self.days_in_month = 30
        
        # Hours display variables
        self.hours_per_day = 24  # Standard 24-hour day
        self.current_hour = 0    # Current hour (0-23)

        # Layout
        self.font = pygame.font.Font(None, 24)
        self.rect_width = 200
        self.rect_height = 40
        self.rect_x = (self.screen_width - self.rect_width) // 2
        self.rect_y = 10
        self.rect = pygame.Rect(self.rect_x, self.rect_y, self.rect_width, self.rect_height)

        # Speed control
        self.time_multiplier = 1.0
        self.speed_menu_open = False
        self.speed_options = [0.5, 0.75, 1.0, 1.25, 1.5]
        self.speed_rects = []
        self._create_speed_menu_rects()

    # ──────────────────────────────────────────────────────────────────────────────
    # Helper to prepare speed selection button layout
    # ──────────────────────────────────────────────────────────────────────────────
    def _create_speed_menu_rects(self):
        self.speed_menu_width = self.rect_width + 80
        self.speed_menu_height = 50

        speed_menu_x = self.rect_x - (self.speed_menu_width - self.rect_width) // 2
        speed_menu_y = self.rect_y + self.rect_height + 5
        self.speed_menu_rect = pygame.Rect(speed_menu_x, speed_menu_y,
                                           self.speed_menu_width, self.speed_menu_height)

        # Pre-fill placeholder rects (real positions are calculated in draw)
        self.speed_rects = [(pygame.Rect(0, 0, 0, 0), speed) for speed in self.speed_options]

    # ──────────────────────────────────────────────────────────────────────────────
    # Time utility methods
    # ──────────────────────────────────────────────────────────────────────────────
    def get_seconds_per_day(self):
        """Returns the number of real seconds per in-game day."""
        return 60 / self.days_per_minute

    def get_day_progress(self):
        """Returns the progress through the current day as a value between 0.0 and 1.0."""
        seconds_per_day = self.get_seconds_per_day()
        return (self.elapsed_seconds % seconds_per_day) / seconds_per_day

    def advance_time(self, hours):
        """
        Advance the game time by the specified number of in-game hours.
        
        Args:
            hours: Number of in-game hours to advance
        """
        seconds_per_day = self.get_seconds_per_day()
        seconds_to_add = (hours / self.hours_per_day) * seconds_per_day
        self.elapsed_seconds += seconds_to_add
        
        # Recalculate current day, month, and hour
        self._update_time_values()
        
    def _update_time_values(self):
        """Update day, month, and hour values based on elapsed seconds."""
        seconds_per_day = self.get_seconds_per_day()
        total_days = int(self.elapsed_seconds / seconds_per_day)
        
        self.current_day = (total_days % self.days_in_month) + 1
        self.current_month = min((total_days // self.days_in_month) + 1, self.total_months)
        
        # Calculate current hour
        day_progress = self.get_day_progress()
        self.current_hour = int(day_progress * self.hours_per_day)

    # ──────────────────────────────────────────────────────────────────────────────
    # Handles mouse input for toggling and changing time speed
    # ──────────────────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # Cycle through time modes
                current_index = self.time_modes.index(self.time_mode)
                self.time_mode = self.time_modes[(current_index + 1) % len(self.time_modes)]
                return True
        return False

    # ──────────────────────────────────────────────────────────────────────────────
    # Updates current time based on elapsed delta and speed multiplier
    # ──────────────────────────────────────────────────────────────────────────────
    def update(self, dt):
        # Adjust elapsed_seconds based on selected time mode
        if self.time_mode == "hour":
            self.elapsed_seconds += dt * 24  # 1 real second = 1 in-game hour
        elif self.time_mode == "day":
            self.elapsed_seconds += dt      # 1 real second = 1 in-game day
        elif self.time_mode == "week":
            self.elapsed_seconds += dt / 7  # 1 real second = 1/7th of a day
        self._update_time_values()

    # ──────────────────────────────────────────────────────────────────────────────
    # Renders the time bar UI with current day/month and speed menu
    # ──────────────────────────────────────────────────────────────────────────────
    def draw(self, surface):
        def draw_rounded_rect_alpha(surface, rect, color, border_radius):
            """Draws a rounded, semi-transparent rect."""
            temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(temp_surface, color, temp_surface.get_rect(), border_radius=border_radius)
            surface.blit(temp_surface, (rect.x, rect.y))

        # Draw time bar container
        draw_rounded_rect_alpha(surface, self.rect, (30, 30, 30, 180), border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)

        # Time label including hour
        am_pm = "AM" if self.current_hour < 12 else "PM"
        display_hour = self.current_hour if self.current_hour <= 12 else self.current_hour - 12
        if display_hour == 0:
            display_hour = 12
            
        time_text = f"M{self.current_month}/{self.total_months} D{self.current_day} {display_hour}{am_pm} [{self.time_mode.title()}]"
        text_surface = self.font.render(time_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

        # Progress bar
        progress_width = int((self.rect_width - 20) * (((self.current_month - 1) * self.days_in_month + self.current_day) / 
                                                       (self.total_months * self.days_in_month)))
        progress_rect = pygame.Rect(self.rect_x + 10, self.rect_y + self.rect_height - 8, progress_width, 4)
        pygame.draw.rect(surface, (120, 220, 120), progress_rect, border_radius=2)

        # Draw speed menu if open
        if self.speed_menu_open:
            draw_rounded_rect_alpha(surface, self.speed_menu_rect, (20, 20, 20, 210), border_radius=8)
            pygame.draw.rect(surface, (180, 180, 180), self.speed_menu_rect, 1, border_radius=8)

            # Button layout
            button_margin = 8
            button_width = (self.speed_menu_width - button_margin * (len(self.speed_options) + 1)) // len(self.speed_options)
            button_height = self.speed_menu_height - button_margin * 2
            y_pos = self.speed_menu_rect.y + button_margin

            for i, (rect, speed) in enumerate(self.speed_rects):
                x_pos = self.speed_menu_rect.x + button_margin + i * (button_width + button_margin)
                self.speed_rects[i] = (pygame.Rect(x_pos, y_pos, button_width, button_height), speed)

                is_selected = speed == self.time_multiplier
                button_color = (90, 160, 250) if is_selected else (60, 60, 60)
                border_color = (220, 220, 220) if is_selected else (100, 100, 100)

                pygame.draw.rect(surface, button_color, self.speed_rects[i][0], border_radius=6)
                pygame.draw.rect(surface, border_color, self.speed_rects[i][0], 1, border_radius=6)

                speed_text = f"{speed}x"
                text_surf = self.font.render(speed_text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=self.speed_rects[i][0].center)
                surface.blit(text_surf, text_rect)