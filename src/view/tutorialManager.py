# ──────────────────────────────────────────────────────────────────────────────
#  tutorialManager.py – manages guided in-game onboarding/tutorial UI
# ──────────────────────────────────────────────────────────────────────────────

import pygame

class TutorialManager:
    # ──────────────────────────────────────────────────────────────────────────
    # Initialization
    # ──────────────────────────────────────────────────────────────────────────
    def __init__(self, game):
        self.game = game
        self.display_surface = pygame.display.get_surface()
        self.screen_width, self.screen_height = self.display_surface.get_width(), self.display_surface.get_height()

        self.active = False              # Whether the tutorial is currently running
        self.current_step = 0           # Index of current tutorial step

        # ── Colors used in the overlay/tutorial box ───────────────────────────
        self.colors = {
            "primary": (70, 90, 120),        # Navy blue-ish background
            "secondary": (100, 130, 160),    # Lighter blue (not used yet)
            "dark": (50, 60, 80),            # Dark border/box
            "accent": (180, 150, 120),       # Highlight / accent color
            "text": (235, 235, 245),         # Tutorial body text
            "white": (255, 255, 255),        # Headers & UI lines
            "overlay": (0, 0, 0, 160)        # Transparent black background
        }

        # ── Fonts for titles and body ─────────────────────────────────────────
        self.title_font = pygame.font.SysFont(None, 36)
        self.text_font = pygame.font.SysFont(None, 24)

        # ── List of tutorial steps ────────────────────────────────────────────
        # Each step has: title, description, and optional target area (highlight)
        self.tutorial_steps = [
            {
                "title": "Welcome to Safari Park!",
                "description": "This tutorial will guide you through the game's main features. Click anywhere to continue.",
                "target": None
            },
            {
                "title": "Main Menu",
                "description": "The menu button in the top left allows you to pause the game, start a new game, exit, or toggle day/night mode.",
                "target": pygame.Rect(15, 15, 30, 30)
            },
            {
                "title": "Day & Night Toggle",
                "description": "Click this button to switch between day and night. At night, only chipped animals remain visible.",
                "target": pygame.Rect(60, 10, 40, 40)
            },
            {
                "title": "Statistics Bar",
                "description": "At the top right, you can see your park's statistics including animal count, rangers, poachers, capital, and visitor count.",
                "target": pygame.Rect(self.screen_width - 400, 15, 390, 30)
            },
            {
                "title": "Time Control",
                "description": "The clock at the top center shows the current game time. Click it to adjust game speed.",
                "target": pygame.Rect(self.screen_width//2 - 90, 15, 180, 30)
            },
            {
                "title": "Mini Map",
                "description": "The mini map at the bottom left shows your location, animals, and rangers across the park territory.",
                "target": pygame.Rect(20, self.screen_height - 250, 230, 230)
            },
            {
                "title": "Store",
                "description": "The store at the bottom right lets you buy new animals and equipment for your park, or sell existing animals.",
                "target": pygame.Rect(self.screen_width - 100, self.screen_height - 100, 80, 80)
            },
            {
                "title": "That's it!",
                "description": "You now know all the main features of Safari Park. Have fun managing your park! Click to exit the tutorial.",
                "target": None
            }
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # Tutorial control methods
    # ──────────────────────────────────────────────────────────────────────────

    def start(self):
        """Start or restart the tutorial from the beginning."""
        self.active = True
        self.current_step = 0

    def next_step(self):
        """Go to the next tutorial step. If at end, deactivate."""
        self.current_step += 1
        if self.current_step >= len(self.tutorial_steps):
            self.active = False

    # ──────────────────────────────────────────────────────────────────────────
    # Draw the overlay & tutorial box
    # ──────────────────────────────────────────────────────────────────────────
    def draw(self):
        if not self.active:
            return

        # Semi-transparent overlay background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(self.colors["overlay"])
        self.display_surface.blit(overlay, (0, 0))

        current_tutorial = self.tutorial_steps[self.current_step]

        # Draw highlight box if target is provided
        if current_tutorial["target"]:
            target = current_tutorial["target"]
            pulse = (pygame.time.get_ticks() % 1000) / 1000  # Create a pulsing effect
            thickness = 3 + int(2 * pulse)
            highlight_rect = target.inflate(20, 20)
            pygame.draw.rect(self.display_surface, self.colors["accent"], highlight_rect, thickness, border_radius=10)

        # ── Calculate position of tutorial box ────────────────────────────────
        box_width = 500
        box_height = 180

        if current_tutorial["target"]:
            target = current_tutorial["target"]
            box_y = self.screen_height - box_height - 50 if target.centery < self.screen_height // 2 else 50
            box_x = self.screen_width - box_width - 50 if target.centerx < self.screen_width // 2 else 50
        else:
            box_x = (self.screen_width - box_width) // 2
            box_y = (self.screen_height - box_height) // 2

        info_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        # Draw background + border
        info_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(info_surface, (*self.colors["primary"], 230), info_surface.get_rect(), border_radius=15)
        self.display_surface.blit(info_surface, info_rect)
        pygame.draw.rect(self.display_surface, self.colors["dark"], info_rect, 2, border_radius=15)

        # Draw header bar
        header_rect = pygame.Rect(info_rect.x, info_rect.y, box_width, 40)
        pygame.draw.rect(self.display_surface, self.colors["dark"], header_rect, border_top_left_radius=15, border_top_right_radius=15)

        # Title text
        title_text = self.title_font.render(current_tutorial["title"], True, self.colors["white"])
        self.display_surface.blit(title_text, (
            header_rect.x + (header_rect.width - title_text.get_width()) // 2,
            header_rect.y + (header_rect.height - title_text.get_height()) // 2
        ))

        # ── Word-wrap description text ────────────────────────────────────────
        desc = current_tutorial["description"]
        words = desc.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.text_font.size(test_line)[0] < box_width - 40:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        y_offset = header_rect.bottom + 20
        for line in lines:
            text_surface = self.text_font.render(line, True, self.colors["text"])
            self.display_surface.blit(text_surface, (info_rect.x + 20, y_offset))
            y_offset += self.text_font.get_height() + 5

        # ── Footer indicators ─────────────────────────────────────────────────
        step_text = self.text_font.render(f"Step {self.current_step + 1}/{len(self.tutorial_steps)}", True, self.colors["text"])
        self.display_surface.blit(step_text, (
            info_rect.right - step_text.get_width() - 15,
            info_rect.bottom - step_text.get_height() - 15
        ))

        click_text = self.text_font.render("Click to continue...", True, self.colors["accent"])
        self.display_surface.blit(click_text, (
            info_rect.x + 15,
            info_rect.bottom - click_text.get_height() - 15
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # Handle click-to-advance
    # ──────────────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.next_step()
            return True

        return False