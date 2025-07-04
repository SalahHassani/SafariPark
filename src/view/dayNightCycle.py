# ──────────────────────────────────────────────────────────────────────────────
# dayNightCycle.py – UI element to handle day/night overlay, spotlights, and toggling
# ──────────────────────────────────────────────────────────────────────────────

import pygame
import math

# ──────────────────────────────────────────────────────────────────────────────
# DayNightCycle: Controls the day/night overlay, spotlights, and manual toggle
# ──────────────────────────────────────────────────────────────────────────────

class DayNightCycle:
    """
    - Draws a dark overlay with spotlights when the in-game clock is outside [5,21).
    - toggle() jumps you forward to the next 21:00 (if daytime) or next 05:00 (if nighttime).
    """

    # ──────────────────────────────────────────────────────────────────────────
    # Initialization
    # ──────────────────────────────────────────────────────────────────────────
    
    def __init__(self, map_reference, time_indicator):
        print("DayNightCycle initialized")
        self.map            = map_reference
        self.time_indicator = time_indicator
        self.display        = pygame.display.get_surface()
        self.w, self.h      = self.display.get_size()

        # thresholds
        self.HOURS_PER_DAY    = 24
        self.DAY_START_HOUR   =  5   # 05:00
        self.NIGHT_START_HOUR = 21   # 21:00

        # overlay & spotlight
        self.night_color     = (10, 20, 40, 180)
        self.spot_radius     = 20
        self.spot_fade       = 80
        self._make_spot_surface()

    # ──────────────────────────────────────────────────────────────────────────
    # Spotlight surface creation
    # ──────────────────────────────────────────────────────────────────────────
    
    def _make_spot_surface(self):
        R = self.spot_radius + self.spot_fade
        size = R * 2
        self.spot_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = R
        maxd = self.spot_radius + self.spot_fade

        for y in range(size):
            for x in range(size):
                d = math.hypot(x - center, y - center)
                if d < self.spot_radius:
                    alpha = 0
                elif d < maxd:
                    alpha = int(255 * (d - self.spot_radius) / self.spot_fade)
                else:
                    alpha = 255
                alpha = max(0, min(255, alpha))
                self.spot_surf.set_at((x, y), (*self.night_color[:3], alpha))


    # ──────────────────────────────────────────────────────────────────────────
    # Current hour retrieval
    # ──────────────────────────────────────────────────────────────────────────
    
    def get_current_hour(self):
        """Clamp day_progress to [0,1) and turn into 0–24h."""
        prog = self.time_indicator.get_day_progress() % 1.0
        return prog * self.HOURS_PER_DAY

    # ──────────────────────────────────────────────────────────────────────────
    # Daytime check
    # ──────────────────────────────────────────────────────────────────────────
    
    def is_daytime(self, hour=None):
        # your existing [5,21) test
        if hour is None:
            hour = self.get_current_hour()
        return 5 <= (hour % 24) < 21

    # ──────────────────────────────────────────────────────────────────────────
    # Night property
    # ──────────────────────────────────────────────────────────────────────────
    
    @property
    def is_night(self) -> bool:
        # now external code can call .is_night
        return not self.is_daytime()

    # ──────────────────────────────────────────────────────────────────────────
    # Manual toggle
    # ──────────────────────────────────────────────────────────────────────────
    
    def toggle(self):
        """
        If right now is day → jump forward to next 21:00 (night).
                               else → jump to next 05:00 (day).
        """
        current = self.get_current_hour()
        if self.is_daytime(current):
            target = self.NIGHT_START_HOUR
        else:
            target = self.DAY_START_HOUR

        # hours forward, always positive
        delta = (target - current) % self.HOURS_PER_DAY
        # if exactly on boundary, push a full cycle
        if delta == 0:
            delta = self.HOURS_PER_DAY

        self.time_indicator.advance_time(delta)
        new_hour = self.get_current_hour()
        print(f"Toggled: +{delta:.2f}h → now {new_hour:.2f}h, "
              f"{'Day' if self.is_daytime(new_hour) else 'Night'}")
        return not self.is_daytime(new_hour)

    # ──────────────────────────────────────────────────────────────────────────────
    # Drawing overlay & spotlights
    # ──────────────────────────────────────────────────────────────────────────
    
    def draw(self, camera_offset=None):
        if self.is_daytime():
            return

        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill(self.night_color)

        for ranger in self.map.rangers:
            sx = ranger.rect.centerx - camera_offset.x
            sy = ranger.rect.centery - camera_offset.y

            if (-self.spot_radius < sx < self.w + self.spot_radius and
                -self.spot_radius < sy < self.h + self.spot_radius):
                pos = (
                    int(sx - (self.spot_radius + self.spot_fade)),
                    int(sy - (self.spot_radius + self.spot_fade))
                )
                overlay.blit(self.spot_surf, pos, special_flags=pygame.BLEND_RGBA_MIN)

        for animal in self.map.chipped_animals:
            sx = animal.rect.centerx - camera_offset.x
            sy = animal.rect.centery - camera_offset.y

            if (-self.spot_radius < sx < self.w + self.spot_radius and
                -self.spot_radius < sy < self.h + self.spot_radius):
                pos = (
                    int(sx - (self.spot_radius + self.spot_fade)),
                    int(sy - (self.spot_radius + self.spot_fade))
                )
                overlay.blit(self.spot_surf, pos, special_flags=pygame.BLEND_RGBA_MIN)

        self.display.blit(overlay, (0, 0))