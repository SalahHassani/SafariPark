import pygame
from src.config.settings import LAYERS, TILE_SIZE

SAFARI_PASS = 50

class Jeep(pygame.sprite.Sprite):
    def __init__(self, pos, path_points, end_point, groups, map_ref):
        self._layer = LAYERS['jeep']

        self.map = map_ref
        super().__init__(*groups)

        # Load directional sprites
        self.directional_sprites = {
            'up': None,
            'down': None,
            'left': None,
            'right': None
        }
        
        # Load and scale each directional sprite
        for direction in self.directional_sprites.keys():
            try:
                sprite_path = f'src/assets/graphics/jeep/{direction}.png'
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.directional_sprites[direction] = pygame.transform.scale(sprite, (TILE_SIZE + 30, TILE_SIZE + 30))
            except FileNotFoundError:
                print(f"Warning: Missing jeep sprite for direction {direction}")
                # Fallback to a default sprite if one is missing
                self.directional_sprites[direction] = pygame.Surface((64, 64), pygame.SRCALPHA)
                self.directional_sprites[direction].fill((255, 0, 0, 128))  # Red semi-transparent as fallback

        self.image = self.directional_sprites['down']
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(self.rect.center)
        self.hitbox = self.rect.inflate(-10, -10)
        self.current_direction = 'down'

        # Path following
        self.path = path_points
        self.path_index = 0
        self.forward = True
        self.speed = 60  # Reduced from 100 to 60 for slower movement

        # Tourists logic
        self.tourist_count = 0
        self.max_capacity = 4
        self.ready_to_depart = False
        self.boarding_timer = 0
        self.font = pygame.font.Font(None, 24)

        print(f"✅ Jeep initialized with {len(self.path)} path points.")
        self.end_point = pygame.Vector2(end_point)

    def draw(self, surface, offset):
        """Draw the jeep and tourist count label."""
        offset_rect = self.rect.copy()
        offset_rect.center -= offset
        surface.blit(self.image, offset_rect)

        # Draw tourist count label above jeep
        label = self.font.render(f"Tourist {self.tourist_count}/4", True, (255, 255, 255))
        label_rect = label.get_rect(center=(offset_rect.centerx, offset_rect.top - 10))
        surface.blit(label, label_rect)

    def update_direction(self, target_point):
        """Update the jeep's direction based on movement."""
        dx = target_point.x - self.pos.x
        dy = target_point.y - self.pos.y
        
        # Determine primary direction (prioritize horizontal movement)
        if abs(dx) > abs(dy):
            self.current_direction = 'right' if dx > 0 else 'left'
        else:
            self.current_direction = 'down' if dy > 0 else 'up'
        
        # Update sprite
        self.image = self.directional_sprites[self.current_direction]

    def update(self, dt):
        """Update jeep position, direction, and tourist logic."""
        # Simulate tourists arriving every 5 seconds
        if not self.ready_to_depart:
            self.boarding_timer += dt
            if self.boarding_timer >= 15:
                self.boarding_timer = 0
                self.tourist_count = min(self.tourist_count + 1, self.max_capacity)
                print(f"🧍 Tourist arrived! ({self.tourist_count}/{self.max_capacity})")

                if self.tourist_count >= self.max_capacity:
                    self.ready_to_depart = True
                    print("✅ All tourists onboard. Jeep is departing!")
            return

        if not self.path:
            return

        target = self.path[self.path_index]
        target_point = pygame.Vector2(target)
        distance = self.pos.distance_to(target_point)

        if distance > 0:
            # Update direction before moving
            self.update_direction(target_point)
            
            # Move with lerp for smooth movement
            lerp_factor = min(1, self.speed * dt / distance)
            self.pos = self.pos.lerp(target_point, lerp_factor)
            self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Check if reached current target point
        if self.pos.distance_to(target_point) < 2:
            self.pos = target_point
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.forward:
                self.path_index += 1
                if self.path_index >= len(self.path):
                    self.path_index -= 1
                    self.forward = False
            else:
                self.path_index -= 1
                start_point = pygame.Vector2(self.path[0])
                
                # Check if reached end point
                if not self.forward and self.pos.distance_to(self.end_point) < 2:
                    self.path_index = 0
                    self.forward = True
                    self.ready_to_depart = False
                    self.tourist_count = 0
                    self.map.capital = self.map.capital + 4 * SAFARI_PASS
                    print("🔁 Jeep returned to end point. Tourists unloaded. Waiting for next group.")
                    return