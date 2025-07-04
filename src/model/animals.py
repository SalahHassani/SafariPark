# ──────────────────────────────────────────────────────────────────────────────
#  animals.py – creature AI with herding, reproduction, and needs system
# ──────────────────────────────────────────────────────────────────────────────
import os
import random
import pygame
from typing import Literal, List, Optional, Tuple

from src.config.settings import *  # TILE_SIZE, LAYERS, SCREEN_WIDTH …
from src.utils.support import import_folder
from src.model.sprites import Water

# --------------------------------------------------------------------------- #
#  Animation helper (4-directional sheets for 8-way movement)                #
# --------------------------------------------------------------------------- #
DIRECTION_MAPPING = {
    "up_left": "up",
    "up_right": "up",
    "down_left": "down",
    "down_right": "down",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
}

# --------------------------------------------------------------------------- #
#  Herd behavior settings                                                    #
# --------------------------------------------------------------------------- #
HERD_RADIUS = 120          # Distance at which animals will form herds
HERD_FOLLOW_DIST = 60      # Distance to maintain from herd leader
HERD_STUCK_TIME = 1.5      # Time before considering leader stuck (seconds)

# --------------------------------------------------------------------------- #
#  Reproduction and growth settings                                          #
# --------------------------------------------------------------------------- #
INTERACTION_RADIUS = 60    # Distance for mating interaction
GESTATION_SECONDS = 200    # Pregnancy duration in game seconds
ONE_YEAR_SECONDS = 120     # Aging speed (game-time)
SMALL_SCALE_FACTOR = 0.50  # Baby size multiplier
MEDIUM_SCALE_FACTOR = 0.80 # Adolescent size multiplier

# --------------------------------------------------------------------------- #
#  Eating behavior settings                                                  #
# --------------------------------------------------------------------------- #
EATING_BONUS = {
    'grass': 1,    # Basic nutrition value
    'flower': 3,   # Higher value food
    'tree': 2,     # Medium value food
    'bush': 2      # Medium value food
}
PLANT_PREFERENCE_RADIUS = 150  # How far animals can sense plants

# --------------------------------------------------------------------------- #
#  Drinking behavior settings                                                #
# --------------------------------------------------------------------------- #
WATER_DETECTION_RADIUS = 300    # How far animals can sense water
WATER_DRINK_RADIUS = 30         # Distance needed to drink
WATER_REFILL_AMOUNT = 5         # Thirst replenished per drink action
WATER_SEARCH_COOLDOWN = 20      # Time between water searches when thirsty (seconds)

# --------------------------------------------------------------------------- #
#  Needs decay rates                                                         #
# --------------------------------------------------------------------------- #
HUNGER_DECAY_RATE = 3.0         # Seconds between hunger decreases
THIRST_DECAY_RATE = 5.0         # Seconds between thirst decreases
HEALTH_DECAY_RATE = 10.0        # Seconds between health decreases
CRITICAL_HEALTH_DECAY = 5.0     # Health loss rate when needs critical (seconds)

# --------------------------------------------------------------------------- #
#  Lifespan settings                                                        #
# --------------------------------------------------------------------------- #
HERBIVORE_LIFESPAN = 15   # Herbivores die at age 15
OMNIVORE_LIFESPAN = 20     # Omnivores die at age 16
CARNIVORE_LIFESPAN = 25    # Carnivores die at age 20

class Animal(pygame.sprite.Sprite):
    """Base class for all creatures with herding, reproduction, and needs systems."""

    DETECTION_RADIUS = 100   # Default threat detection range

    def __init__(
        self,
        name: str,
        species: str,
        age: int | float,
        pos: Tuple[float, float],
        group: pygame.sprite.Group,
        map_rect: pygame.Rect,
        price: int,
        *,
        speed: float = 40,
        scale: float = 1.0,
        body_shape: str = "normal",
        group_type: Optional[str] = None,
        gender: Optional[Literal["male", "female"]] = None,
        mother: Optional["Animal"] = None,
    ):
        super().__init__(group)

        # Basic creature information
        self.name = name
        self.species = species
        self.age = float(age)
        self.age_clock = 0.0
        self.price = price
        self.group_type = group_type or species
        self.gender = gender or random.choice(("male", "female"))
        self.mother = mother

        # Reproduction tracking
        self.is_pregnant = False
        self.gestation_timer = 0.0
        self._stored_father = None

        # Vital needs system
        self.health = 100
        self.hunger_level = 100
        self.thirst_level = 100
        self.is_alive = True

        # Spatial properties and movement
        self.pos = pygame.Vector2(pos)
        self.map_rect = map_rect
        self.direction = pygame.Vector2()
        self.speed = speed
        self.base_scale = scale
        self.scale = scale
        self.body_shape = body_shape

        # Water seeking
        self.current_water_target: Optional[pygame.Vector2] = None
        self.drink_timer = 0.0
        self.water_search_timer = 0.0
        self.is_drinking = False

        # Animation system - now includes idle animations
        self.status = "down_idle"  # Start in idle state
        self.animations = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': []
        }
        self.frame_index = 0
        self.frame_timer = 0.0
        self.import_assets(self._get_sheet_folder())
        self.image = self.animations[self.status][0]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-10, -10)

        # Collision and layering
        self.z = self.rect.centery
        self.collision_sprites = []

        # Movement behavior timers
        self.step_timer = 0.0
        self.step_duration = random.uniform(2.5, 4.5)
        self.idle = True  # Start in idle state
        self.idle_duration = 1.0
        self.idle_timer = 0.0

        # Threat response system
        self.fleeing = False
        self.flee_duration = 1.0
        self.flee_timer = 0.0

        # Needs timers
        self.hunger_timer = 0.0
        self.thirst_timer = 0.0
        self.health_timer = 0.0
        self.eat_plant_timer = 0.0

        # Edge avoidance
        self.edge_timer = 0.0
        self.edge_margin = 100

        # Herd behavior tracking
        self.herd_leader: Optional["Animal"] = None
        self._last_pos = self.pos.copy()
        self._stuck = 0.0

        # Reference to main sprite group for spawning offspring
        self._main_group = group
        self.z = LAYERS["main"]

    # --------------------------------------------------------------------- #
    #  Asset management                                                     #
    # --------------------------------------------------------------------- #
    def _get_sheet_folder(self) -> str:
        """Determine the correct asset folder based on animal type."""
        if isinstance(self, Herbivore):
            return f"herbivores/{self.species}"
        if isinstance(self, Carnivore):
            return f"carnivores/{self.species}"
        if isinstance(self, Omnivore):
            return f"omnivores/{self.species}"
        raise ValueError("Unknown animal type")

    def import_assets(self, folder: str) -> None:
        """Load animation frames with proper scaling for body shape."""
        full_base_path = os.path.join("src/assets/characters/animals", folder)
        
        # Handle variant subfolders (type_1, type_2, etc.)
        type_folder = None
        for i in range(1, 9):
            if os.path.isdir(os.path.join(full_base_path, str(i))):
                type_folder = str(random.randint(1, 8))
                break
            if os.path.isdir(os.path.join(full_base_path, f'type_{i}')):
                type_folder = f'type_{random.randint(1, 8)}'
                break
        
        if type_folder:
            folder = f"{folder}/{type_folder}"
            full_base_path = os.path.join("src/assets/characters/animals", folder)
        
        # Load animations for each direction
        found_valid = False
        for direction in ("up", "down", "left", "right"):
            full_path = os.path.join(full_base_path, direction)
            if os.path.isdir(full_path):
                frames = import_folder(full_path)
                
                # Scale based on body shape
                if self.body_shape == "fat":
                    size = (int(32 * self.scale * 1.1), int(32 * self.scale))
                elif self.body_shape == "tall":
                    size = (int(32 * self.scale), int(32 * self.scale * 1.2))
                else:
                    size = (int(32 * self.scale),) * 2
                    
                if frames:
                    # Create both moving and idle animations
                    self.animations[direction] = [
                        pygame.transform.scale(f, size) for f in frames
                    ]
                    # For idle, use first frame or create dedicated idle frames if available
                    idle_path = os.path.join(full_base_path, f"{direction}_idle")
                    if os.path.isdir(idle_path):
                        idle_frames = import_folder(idle_path)
                        self.animations[f"{direction}_idle"] = [
                            pygame.transform.scale(f, size) for f in idle_frames
                        ]
                    else:
                        # Default to first frame if no idle animation exists
                        self.animations[f"{direction}_idle"] = [self.animations[direction][0]]
                    found_valid = True
        
        # Fallback if no valid animations found
        if not found_valid:
            print(f"Warning: No valid animation folders for '{self.species}' in '{folder}'")
            self.image = pygame.Surface((32, 32))
            self.image.fill((255, 0, 0))

    # --------------------------------------------------------------------- #
    #  Utility methods                                                      #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _label_from_vector(vec: pygame.Vector2) -> str:
        """Convert movement vector to animation status label."""
        x, y = round(vec.x), round(vec.y)
        direction = {
            (-1, -1): "up_left",
            (1, -1): "up_right",
            (-1, 1): "down_left",
            (1, 1): "down_right",
            (-1, 0): "left",
            (1, 0): "right",
            (0, -1): "up",
            (0, 1): "down",
        }.get((x, y), "down")
        
        # Remove _idle suffix if present and we're moving
        return direction.split('_')[0]

    def draw_detection_range(
        self,
        surface: pygame.Surface,
        cam_offset: pygame.Vector2,
        *,
        radius: int = DETECTION_RADIUS,
    ) -> None:
        """Debug visualization for creature detection radius."""
        if not self.is_alive:
            return
        screen_r = pygame.Rect(cam_offset.x, cam_offset.y, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.rect.colliderect(screen_r):
            pygame.draw.circle(
                surface, (173, 216, 230),
                self.rect.center - cam_offset, radius, 1
            )

    # --------------------------------------------------------------------- #
    #  Collision handling                                                   #
    # --------------------------------------------------------------------- #
    def _collides_with_any(self, rect: pygame.Rect, others: list["Animal"]) -> bool:
        """Check for collisions with other animals, ignoring herd mates."""
        for other in others:
            if other is self or not other.is_alive:
                continue
            # Allow overlapping with herd members or family
            if (other.group_type == self.group_type and
                (self.herd_leader or other.herd_leader or
                 self.mother is other or other.mother is self)):
                continue
            if rect.colliderect(other.rect):
                return True
        return False
    
    def _tile_collision(self, direction: str) -> None:
        """Handle collisions with static tiles."""
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # Right collision
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:  # Left collision
                        self.hitbox.left = sprite.hitbox.right
                    self.pos.x = self.hitbox.centerx
                    self.rect.centerx = self.hitbox.centerx

                elif direction == 'vertical':
                    if self.direction.y > 0:  # Down collision
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:  # Up collision
                        self.hitbox.top = sprite.hitbox.bottom
                    self.pos.y = self.hitbox.centery
                    self.rect.centery = self.hitbox.centery

    # --------------------------------------------------------------------- #
    #  Movement system                                                      #
    # --------------------------------------------------------------------- #
    def move(self, dt: float, collision_targets: Optional[list["Animal"]] = None) -> None:
        """Handle creature movement with collision avoidance."""
        if (self.idle and not self.fleeing) or self.direction.length_squared() == 0:
            return

        self.direction = self.direction.normalize()
        dx = self.direction.x * self.speed * dt
        dy = self.direction.y * self.speed * dt

        trial = self.rect.copy()
        trial.centerx += dx
        trial.centery += dy

        blocked = collision_targets is not None and self._collides_with_any(trial, collision_targets)
        if self.map_rect.contains(trial) and not blocked:
            self.pos.x += dx
            self.pos.y += dy
            self.rect.center = self.pos
        elif self.fleeing:
            # Try alternative directions when blocked while fleeing
            for alt in (
                pygame.Vector2(self.direction.y, self.direction.x),
                pygame.Vector2(-self.direction.y, -self.direction.x),
                -self.direction,
            ):
                alt = alt.normalize()
                trial.center = self.rect.center
                trial.centerx += alt.x * self.speed * dt
                trial.centery += alt.y * self.speed * dt
                if self.map_rect.contains(trial) and (
                    collision_targets is None or not self._collides_with_any(trial, collision_targets)
                ):
                    self.direction = alt
                    self.status = self._label_from_vector(self.direction)
                    self.pos.update(
                        self.pos.x + alt.x * self.speed * dt,
                        self.pos.y + alt.y * self.speed * dt
                    )
                    self.rect.center = self.pos
                    break

        # Track if creature is stuck
        if (self.pos - self._last_pos).length_squared() < 1:
            self._stuck += dt
        else:
            self._stuck = 0.0
        self._last_pos.update(self.pos)

        # Update hitbox and handle tile collisions
        self.hitbox.center = self.pos
        self._tile_collision("horizontal")
        self._tile_collision("vertical")
        self.rect.center = self.hitbox.center
        self.pos.update(self.hitbox.center)

    def _choose_new_random_direction(self) -> None:
        """Select a new random wandering direction."""
        direction = random.choice(("up", "down", "left", "right"))
        self.status = direction
        self.direction.xy = {
            "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)
        }[direction]

    def _update_wander_pattern(self, dt: float) -> None:
        """Manage the wandering behavior cycle."""
        if self.idle:
            self.idle_timer += dt
            if self.idle_timer >= self.idle_duration:
                self.idle = False
                self._choose_new_random_direction()
                self.idle_timer = self.step_timer = 0.0
        else:
            self.step_timer += dt
            if self.step_timer >= self.step_duration:
                self.idle = True
                self.step_timer = 0.0
                self.direction.xy = (0, 0)

    def _avoid_edges(self, dt: float) -> None:
        """Steer creature away from map edges."""
        x, y = self.pos
        m = self.edge_margin
        if x < m or x > self.map_rect.width - m or y < m or y > self.map_rect.height - m:
            self.edge_timer += dt
            if self.edge_timer >= 1.0:
                self.idle = False
                self.fleeing = False
                dx = 1 if x < m else -1 if x > self.map_rect.width - m else 0
                dy = 1 if y < m else -1 if y > self.map_rect.height - m else 0
                self.direction.update(dx, dy)
                self.status = self._label_from_vector(self.direction)
                self.step_timer = self.edge_timer = 0.0
        else:
            self.edge_timer = 0.0

    # --------------------------------------------------------------------- #
    #  Herd behavior                                                        #
    # --------------------------------------------------------------------- #
    def _update_herd(self, animals: list["Animal"], dt: float) -> None:
        """Manage herd following behavior."""
        if self.type == "carnivore" or self.fleeing:
            self.herd_leader = None
            return

        # Drop leader if gone or stuck
        if self.herd_leader and (
            not self.herd_leader.is_alive or self.herd_leader._stuck > HERD_STUCK_TIME
        ):
            self.herd_leader = None

        # Find new leader if needed
        if self.herd_leader is None:
            nearest, dmin = None, float("inf")
            for o in animals:
                if (o is self or not o.is_alive or o.group_type != self.group_type or o.fleeing):
                    continue
                d = self.pos.distance_to(o.pos)
                if d < HERD_RADIUS and d < dmin:
                    nearest, dmin = o, d
            if nearest:
                self.herd_leader = nearest.herd_leader or nearest

        # Follow leader behavior
        if self.herd_leader and self.herd_leader is not self:
            vec = self.herd_leader.pos - self.pos
            if vec.length() > HERD_FOLLOW_DIST:
                self.direction = vec.normalize()
                self.status = self._label_from_vector(self.direction)
                self.idle = False
                outsiders = [a for a in animals if a.group_type != self.group_type]
                self.move(dt, outsiders)
            else:
                self.idle = self.herd_leader.idle

    # --------------------------------------------------------------------- #
    #  Reproduction system                                                  #
    # --------------------------------------------------------------------- #
    def _check_reproduction(self, animals: list["Animal"]) -> None:
        """Check for mating opportunities."""
        if self.gender != "female" or self.is_pregnant or self.type == "carnivore":
            return
            
        for other in animals:
            if (other is self or not other.is_alive or
                other.gender != "male" or
                other.group_type != self.group_type):
                continue
                
            if self.pos.distance_to(other.pos) <= INTERACTION_RADIUS:
                self.is_pregnant = True
                self.gestation_timer = GESTATION_SECONDS
                self._stored_father = other
                print(f"[PAIR] {self.name} mated with {other.name}")
                return

    def _gestate(self, dt: float, animals: list["Animal"]) -> None:
        """Handle pregnancy countdown."""
        if not self.is_pregnant:
            return
            
        self.gestation_timer -= dt
        if self.gestation_timer <= 0.0:
            self.is_pregnant = False
            self._give_birth(animals)

    def _give_birth(self, animals: list["Animal"]) -> None:
        """Create a new baby animal."""
        father = self._stored_father or self
        baby_species = random.choice((self.species, father.species))
        baby_name = f"{baby_species.split('/')[-1]}_baby_{random.randint(100,999)}"
        baby_pos = (
            self.pos.x + random.randint(-20, 20),
            self.pos.y + random.randint(-20, 20)
        )
        baby_gender = random.choice(("male", "female"))
        baby_cls = self.__class__
        
        baby = baby_cls(
            baby_name,
            baby_species,
            0,
            baby_pos,
            self._main_group,
            self.map_rect,
            price=0,
            speed=self.speed,
            scale=self.base_scale * SMALL_SCALE_FACTOR,
            body_shape="small",
            group_type=self.group_type,
            gender=baby_gender,
            mother=self,
        )
        animals.append(baby)
        print(f"[BIRTH] {self.name} had {baby_name}")

    # --------------------------------------------------------------------- #
    #  Growth system                                                        #
    # --------------------------------------------------------------------- #
    # def _update_growth(self, dt: float) -> None:
    #     """Manage aging and size changes."""
    #     self.age_clock += dt
    #     if self.age_clock >= ONE_YEAR_SECONDS:
    #         self.age += 1
    #         self.age_clock -= ONE_YEAR_SECONDS
    #         # Adjust size at growth milestones
    #         if self.age == 1:
    #             self._grow("medium", MEDIUM_SCALE_FACTOR)
    #         elif self.age == 5:
    #             self._grow("big", 1.0)
    def _update_growth(self, dt: float) -> None:
        """Manage aging and size changes, including death from old age."""
        self.age_clock += dt
        
        # Age the creature every 60 seconds (ONE_YEAR_SECONDS is already defined as 120)
        if self.age_clock >= ONE_YEAR_SECONDS / 2:  # Half of original year length = 60 seconds
            self.age += 1
            self.age_clock -= ONE_YEAR_SECONDS / 2
            print(f"[AGE] {self.name} is now age {self.age}")
            
            # Check for death from old age
            if (isinstance(self, Herbivore) and self.age >= HERBIVORE_LIFESPAN) or \
            (isinstance(self, Omnivore) and self.age >= OMNIVORE_LIFESPAN) or \
            (isinstance(self, Carnivore) and self.age >= CARNIVORE_LIFESPAN):
                print(f"[DEATH] {self.name} died of old age at {self.age}")
                self.is_alive = False
                self.kill()
                return
                
            # Adjust size at growth milestones (existing code)
            if self.age == 1:
                self._grow("medium", MEDIUM_SCALE_FACTOR)
            elif self.age == 5:
                self._grow("big", 1.0)

    def _grow(self, size_label: str, scale_factor: float) -> None:
        """Handle size changes and animation updates."""
        self.body_shape = size_label
        self.scale = self.base_scale * scale_factor
        self.import_assets(self._get_sheet_folder())
        self.image = self.animations[self.status][int(self.frame_index) % len(self.animations[self.status])]
        centre = self.rect.center
        self.rect = self.image.get_rect(center=centre)

    # --------------------------------------------------------------------- #
    #  Threat detection and response                                        #
    # --------------------------------------------------------------------- #
    def _check_threats_and_flee(self, animals: list["Animal"]) -> None:
        """Detect predators and initiate fleeing behavior."""
        if self.type == "carnivore":
            return
            
        flee_from = {
            "herbivore": ("carnivore", "omnivore"),
            "omnivore": ("carnivore",)
        }[self.type]
        
        for other in animals:
            if (other is self or not other.is_alive or
                getattr(other, "type", None) not in flee_from):
                continue
                
            if self.rect.colliderect(other.rect.inflate(self.DETECTION_RADIUS, self.DETECTION_RADIUS)):
                vec = pygame.Vector2(other.rect.center) - self.pos
                if vec.length_squared() > 0:
                    self.direction = -vec.normalize()
                    self.status = self._label_from_vector(self.direction)
                    self.fleeing = True
                    self.flee_timer = 0.0
                    self.idle = False
                    self.herd_leader = None
                    return

    # --------------------------------------------------------------------- #
    #  Plant eating behavior                                                #
    # --------------------------------------------------------------------- #
    def _should_eat_plants(self) -> bool:
        """Determine if creature should seek plants."""
        if self.type == "herbivore":
            return self.hunger_level < 80 or self.health < 90
        if self.type == "omnivore":
            return self.hunger_level < 70 and not self._should_seek_water()
        return False

    def _find_edible_plants(self) -> List[Tuple[pygame.sprite.Sprite, float]]:
        """Locate all edible plants within detection range."""
        edible_plants = []
        
        for sprite in self.collision_sprites:
            if hasattr(sprite, 'plant_type') and sprite.plant_type in EATING_BONUS:
                dist = self.pos.distance_to(pygame.Vector2(sprite.rect.center))
                if dist < PLANT_PREFERENCE_RADIUS:
                    edible_plants.append((sprite, dist))
        
        return edible_plants

    def _find_best_plant(self) -> Optional[pygame.sprite.Sprite]:
        """Select the most desirable plant to eat."""
        edible_plants = self._find_edible_plants()
        if not edible_plants:
            return None
            
        # Sort by nutrition value then distance
        edible_plants.sort(key=lambda x: (-EATING_BONUS[x[0].plant_type], x[1]))
        return edible_plants[0][0]

    def _eat_plants(self, dt: float) -> None:
        """Handle plant consumption behavior."""
        best_plant = self._find_best_plant()
        
        if best_plant:
            target_pos = pygame.Vector2(best_plant.rect.center)
            
            # If close enough to eat
            if self.pos.distance_to(target_pos) < 30:
                self.idle = True
                self.direction.xy = (0, 0)
                self.eat_plant_timer += dt
                
                if self.eat_plant_timer >= 1.0:
                    self.eat_plant_timer = 0.0
                    nutrition = EATING_BONUS[best_plant.plant_type]
                    self.hunger_level = min(100, self.hunger_level + nutrition)
                    self.thirst_level = min(100, self.thirst_level + 0.5 * nutrition)
                    self.health = min(100, self.health + 0.5 * nutrition)
                    print(f"[EAT] {self.name} ate {best_plant.plant_type} → hunger {self.hunger_level:.0f}")
            else:
                # Move toward plant
                self.idle = False
                self.direction = (target_pos - self.pos).normalize()
                self.status = self._label_from_vector(self.direction)
        else:
            # No plants found, graze randomly
            self.idle = True
            self.direction.xy = (0, 0)
            self.eat_plant_timer += dt
            if self.eat_plant_timer >= 1.0:
                self.eat_plant_timer = 0.0
                self.hunger_level = min(100, self.hunger_level + EATING_BONUS['grass'])
                self.thirst_level = min(100, self.thirst_level + 0.5)
                self.health = min(100, self.health + 0.5)
                print(f"[GRAZE] {self.name} grazed → hunger {self.hunger_level:.0f}")

    # --------------------------------------------------------------------- #
    #  Water seeking behavior                                               #
    # --------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
#  Drinking behavior settings                                                #
# --------------------------------------------------------------------------- #
    def _should_seek_water(self) -> bool:
        """Determine if creature should look for water."""
        return (self.thirst_level < 70  and self.hunger_level > 60) or self.thirst_level < 40

    def _find_nearest_water(self) -> Optional[pygame.Vector2]:
        """Find the nearest water source within detection range."""
        nearest_water = None
        min_distance = float('inf')
        
        for sprite in self.collision_sprites:
            if isinstance(sprite, Water) or getattr(sprite, 'is_water_source', False):
                water_pos = pygame.Vector2(sprite.rect.center)
                distance = self.pos.distance_to(water_pos)
                
                if distance < WATER_DETECTION_RADIUS and distance < min_distance:
                    nearest_water = water_pos
                    min_distance = distance
        
        return nearest_water

    def _seek_water(self, dt: float) -> None:
        """Improved water seeking behavior with cooldown and random movement."""
        # Check if we should search for water again
        self.water_search_timer += dt
        if self.water_search_timer < WATER_SEARCH_COOLDOWN and not self.current_water_target:
            # During cooldown, move randomly to avoid getting stuck
            if random.random() < 0.05:  # 5% chance to change direction each frame
                self._choose_new_random_direction()
            return
        
        # Reset timer if we're actively seeking or found water
        self.water_search_timer = 0.0
        
        # Find nearest water source
        water_source = self._find_nearest_water()
        
        if water_source:
            self.current_water_target = water_source
            target_pos = water_source
            distance = self.pos.distance_to(target_pos)
            
            # If close enough to drink
            if distance < WATER_DRINK_RADIUS:
                self.idle = True
                self.is_drinking = True
                self.direction.xy = (0, 0)
                self.drink_timer += dt
                
                if self.drink_timer >= 1.0:
                    self.drink_timer = 0.0
                    self.thirst_level = min(100, self.thirst_level + WATER_REFILL_AMOUNT)
                    print(f"[DRINK] {self.name} drank → thirst {self.thirst_level:.0f}")
                    
                    # Stop drinking if satisfied
                    if self.thirst_level >= 90:
                        self.is_drinking = False
                        self.current_water_target = None
            else:
                # Move toward water
                self.idle = False
                self.is_drinking = False
                self.direction = (target_pos - self.pos).normalize()
                self.status = self._label_from_vector(self.direction)
                
                # If stuck while moving toward water, try a different path
                if self._stuck > 2.0:  # If stuck for 2 seconds
                    # Try moving perpendicular to current direction
                    self.direction = pygame.Vector2(-self.direction.y, self.direction.x)
                    if random.random() < 0.5:
                        self.direction *= -1  # 50% chance to go the other way
                    self._stuck = 0.0
        else:
            # No water found - move randomly and try again later
            self.is_drinking = False
            self.current_water_target = None
            if random.random() < 0.1:  # 10% chance to change direction
                self._choose_new_random_direction()

    # --------------------------------------------------------------------- #
    #  Core update method                                                   #
    # --------------------------------------------------------------------- #
    def update(self, dt: float, animals: Optional[list["Animal"]] = None) -> None:
        """Main update loop handling all creature behaviors."""
        if not self.is_alive:
            return

        # Update needs with adjusted decay rates
        self.hunger_timer += dt
        self.thirst_timer += dt
        self.health_timer += dt
        
        # Critical health checks
        critical_decay = False
        
        if self.hunger_timer >= HUNGER_DECAY_RATE:
            self.hunger_level = max(0, self.hunger_level - 1)
            self.hunger_timer = 0.0
            if self.hunger_level <= 0:
                critical_decay = True
        
        if self.thirst_timer >= THIRST_DECAY_RATE:
            self.thirst_level = max(0, self.thirst_level - 1)
            self.thirst_timer = 0.0
            if self.thirst_level <= 0:
                critical_decay = True
                
        # Health deterioration when needs are critical
        if critical_decay and self.health_timer >= CRITICAL_HEALTH_DECAY:
            self.health = max(0, self.health - 1)
            self.health_timer = 0.0
            if self.health == 0:
                print(f"[DEATH] {self.name} died from starvation/dehydration")
                self.is_alive = False
                self.kill()
                return
        elif self.health_timer >= HEALTH_DECAY_RATE:
            self.health = max(0, self.health - 1)
            self.health_timer = 0.0

        # Growth and reproduction
        self._update_growth(dt)
        if animals:
            self._check_reproduction(animals)
            self._gestate(dt, animals)

        # Herd behavior
        if animals and not self.fleeing:
            self._update_herd(animals, dt)

        # Threat detection
        if animals:
            self._check_threats_and_flee(animals)

        # Behavior priority system:
        # 1. Flee from threats
        # 2. Seek water if thirsty
        # 3. Eat plants if hungry (except carnivores)
        # 4. Default wandering
        
        if self.fleeing:
            self.flee_timer += dt
            if self.flee_timer >= self.flee_duration:
                self.fleeing = False
            self.move(dt, animals)
        elif self._should_seek_water():
            self._seek_water(dt)
            self.move(dt, animals)
        elif self._should_eat_plants():
            self._eat_plants(dt)
            self.move(dt, animals)
        else:
            self._avoid_edges(dt)
            self._update_wander_pattern(dt)
            self.move(dt, animals)

        # Animation updates - properly handle idle states
        if self.idle or self.direction.length_squared() == 0 or self.is_drinking:
            # Use idle animation if available
            base_status = self.status.split('_')[0]  # Get base direction
            idle_status = f"{base_status}_idle"
            
            # Default to first frame if no idle animation exists
            if idle_status not in self.animations:
                idle_status = base_status
                
            frames = self.animations.get(idle_status, [])
            if frames:
                self.image = frames[int(self.frame_index) % len(frames)]
        else:
            # Regular movement animation
            frames = self.animations.get(self.status, [])
            if frames:
                frame_interval = max(0.05, 0.25 * (50 / max(10, self.speed)))
                self.frame_timer += dt
                if self.frame_timer >= frame_interval:
                    self.frame_index = (self.frame_index + 1) % len(frames)
                    self.frame_timer = 0.0
                self.image = frames[int(self.frame_index)]

    # --------------------------------------------------------------------- #
    #  Type property                                                        #
    # --------------------------------------------------------------------- #
    @property
    def type(self) -> str:
        """Return the creature's dietary type (herbivore/omnivore/carnivore)."""
        return "animal"


# =============================================================================
#  PREDATOR hierarchy (Carnivores + Omnivores)                                #
# =============================================================================
# ... (keep all your existing imports and constants) ...

class Predator(Animal):
    def __init__(
        self,
        name,
        species,
        age,
        pos,
        group,
        map_rect,
        price,
        *,
        speed: float = 40,
        scale: float = 1.0,
        body_shape: str = "normal",
        group_type: str | None = None,
        gender: Literal["male", "female"] | None = None,
        mother: Animal | None = None,
    ):
        super().__init__(
            name, species, age, pos, group, map_rect, price,
            speed=speed, scale=scale, body_shape=body_shape,
            group_type=group_type, gender=gender, mother=mother,
        )
        self.target_prey: Animal | None = None
        self.hunting_cooldown = 0.0
        self.hunt_fail_timer = 0.0

    # hunting helpers -------------------------------------------------------
    def _should_hunt(self) -> bool:
        """Determine if predator should hunt based on needs."""
        # More aggressive hunting when hungry or thirsty
        if self.hunger_level < 40 or self.thirst_level < 30:
            return True
        # Less aggressive hunting when moderately hungry
        if self.hunger_level < 70 and random.random() < 0.3:  # 30% chance to hunt
            return True
        return False

    def _find_prey(self, animals: list[Animal]) -> bool:
        """Find suitable prey and return True if found."""
        if self.target_prey and self.target_prey.is_alive and self.target_prey.health > 0:
            return True
            
        if self.hunting_cooldown > 0:
            return False

        prey_types = {
            "carnivore": ("herbivore", "omnivore"),
            "omnivore": ("herbivore",)
        }[self.type]
        
        closest, dmin = None, float("inf")
        for other in animals:
            if (other is self or not other.is_alive or 
                getattr(other, "type", None) not in prey_types):
                continue
                
            # carnivores avoid healthy bears
            if (self.type == "carnivore" and other.type == "omnivore" and
                "bear" in other.species.lower() and other.health >= 50):
                continue
                
            d = self.pos.distance_to(other.pos)
            if d < Animal.DETECTION_RADIUS * 1.5 and d < dmin:  # Increased detection range
                closest, dmin = other, d
                
        if closest:
            self.target_prey = closest
            self.hunt_fail_timer = 0.0
            return True
        return False

    def _hunt(self, prey: Animal, dt: float) -> None:
        """Execute hunting behavior."""
        if not prey or not prey.is_alive:
            self.target_prey = None
            self.hunting_cooldown = 5.0  # Cooldown after losing prey
            return
            
        # Calculate vector to prey
        vec = pygame.Vector2(prey.rect.center) - self.pos
        distance = vec.length()
        
        if distance > Animal.DETECTION_RADIUS * 2:  # Give up if prey too far
            self.target_prey = None
            self.hunting_cooldown = 10.0
            return
            
        if vec.length_squared() > 0:
            self.direction = vec.normalize()
            self.status = self._label_from_vector(self.direction)
            self.idle = False
            self.fleeing = False
            
        # Move toward prey with increased speed when close
        hunt_speed = self.speed * (1.5 if distance < 100 else 1.2)
        self.pos += self.direction * hunt_speed * dt
        self.rect.center = self.pos
        self.hitbox.center = self.pos
        
        # Track hunt failure time
        if distance < 100:  # If close but not catching
            self.hunt_fail_timer += dt
            if self.hunt_fail_timer > 5.0:  # Give up after 5 seconds of failed chasing
                self.target_prey = None
                self.hunting_cooldown = 15.0
                return
                
        # Check for successful attack
        if self.rect.colliderect(prey.rect):
            prey.health -= 15 + random.randint(0, 10)  # Variable damage
            print(f"[HUNT] {self.name} attacked {prey.name} ({prey.health} HP left)")
            
            if prey.health <= 0:
                prey.is_alive = False
                prey.kill()
                print(f"[KILL] {self.name} killed {prey.name}")
                # Full restore for kill
                self.health = 100
                self.hunger_level = 100 
                self.thirst_level = 100
                self.target_prey = None
            else:
                # Partial restore for hit
                self.hunger_level = min(100, self.hunger_level + 15)
                self.thirst_level = min(100, self.thirst_level + 10)

    # override update -------------------------------------------------------
    def update(self, dt: float, animals: list[Animal] | None = None) -> None:
        if not self.is_alive:
            return
            
        # Update cooldowns
        if self.hunting_cooldown > 0:
            self.hunting_cooldown -= dt
            
        # Update needs
        self.hunger_timer += dt
        self.thirst_timer += dt
        self.health_timer += dt
        
        if self.hunger_timer >= HUNGER_DECAY_RATE:
            self.hunger_level = max(0, self.hunger_level - 1)
            self.hunger_timer = 0.0
            
        if self.thirst_timer >= THIRST_DECAY_RATE:
            self.thirst_level = max(0, self.thirst_level - 1)
            self.thirst_timer = 0.0
            
        if self.health_timer >= HEALTH_DECAY_RATE:
            self.health = max(0, self.health - 1)
            self.health_timer = 0.0
            if self.health == 0:
                print(f"[DEATH] {self.name} died from poor condition")
                self.is_alive = False
                self.kill()
                return

        # Growth & reproduction
        self._update_growth(dt)
        if animals:
            self._check_reproduction(animals)
            self._gestate(dt, animals)

        # Check for threats (even predators can flee from bigger threats)
        if animals:
            self._check_threats_and_flee(animals)

        # Behavior priority for predators:
        # 1. Flee if threatened
        # 2. Hunt if able and hungry
        # 3. Seek water if very thirsty
        # 4. Wander normally
        
        if self.fleeing:
            self.flee_timer += dt
            if self.flee_timer >= self.flee_duration:
                self.fleeing = False
            self.move(dt, animals)
        elif self._should_hunt() and animals and self._find_prey(animals):
            self._hunt(self.target_prey, dt)
        elif self._should_seek_water():
            self._seek_water(dt)
            self.move(dt, animals)
        else:
            self._avoid_edges(dt)
            self._update_wander_pattern(dt)
            self.move(dt, animals)

        # Animation updates
        if self.idle or self.direction.length_squared() == 0:
            base_status = self.status.split('_')[0] if '_' in self.status else self.status
            idle_status = f"{base_status}_idle"
            frames = self.animations.get(idle_status, self.animations.get(base_status, []))
            if frames:
                self.image = frames[int(self.frame_index) % len(frames)]
        else:
            frames = self.animations.get(self.status, [])
            if frames:
                # Faster animation when hunting
                frame_interval = max(0.05, 0.2 * (50 / max(10, self.speed)))  
                self.frame_timer += dt
                if self.frame_timer >= frame_interval:
                    self.frame_index = (self.frame_index + 1) % len(frames)
                    self.frame_timer = 0.0
                self.image = frames[int(self.frame_index)]


class Carnivore(Predator):
    @property
    def type(self):
        return "carnivore"
        
    def _should_hunt(self) -> bool:
        """Carnivores are always looking to hunt when hungry."""
        return self.hunger_level < 80 or self.health < 90


class Omnivore(Predator):
    @property
    def type(self):
        return "omnivore"
        
    def _should_eat_plants(self) -> bool:
        """Omnivores prefer plants when available."""
        return (self.hunger_level < 70 or 
                (self.hunger_level < 90 and self._find_edible_plants()) or
                self.health < 80)
                
    def _should_hunt(self) -> bool:
        """Omnivores hunt when very hungry or when prey is easy."""
        if self.hunger_level < 40:
            return True
        if self.hunger_level < 70 and random.random() < 0.2:  # 20% chance to hunt
            return True
        return False

    def update(self, dt: float, animals: list[Animal] | None = None) -> None:
        if not self.is_alive:
            return
            
        # Update cooldowns
        if self.hunting_cooldown > 0:
            self.hunting_cooldown -= dt
            
        # Update needs
        self.hunger_timer += dt
        self.thirst_timer += dt
        self.health_timer += dt
        
        if self.hunger_timer >= HUNGER_DECAY_RATE:
            self.hunger_level = max(0, self.hunger_level - 1)
            self.hunger_timer = 0.0
            
        if self.thirst_timer >= THIRST_DECAY_RATE:
            self.thirst_level = max(0, self.thirst_level - 1)
            self.thirst_timer = 0.0
            
        if self.health_timer >= HEALTH_DECAY_RATE:
            self.health = max(0, self.health - 1)
            self.health_timer = 0.0
            if self.health == 0:
                print(f"[DEATH] {self.name} died from poor condition")
                self.is_alive = False
                self.kill()
                return

        # Growth & reproduction
        self._update_growth(dt)
        if animals:
            self._check_reproduction(animals)
            self._gestate(dt, animals)

        # Check for threats
        if animals:
            self._check_threats_and_flee(animals)

        # Behavior priority for omnivores:
        # 1. Flee if threatened
        # 2. Eat plants if available
        # 3. Hunt if hungry and no plants available
        # 4. Seek water if thirsty
        # 5. Wander normally
        
        if self.fleeing:
            self.flee_timer += dt
            if self.flee_timer >= self.flee_duration:
                self.fleeing = False
            self.move(dt, animals)
        elif self._should_eat_plants():
            self._eat_plants(dt)
        elif self._should_hunt() and animals and self._find_prey(animals):
            self._hunt(self.target_prey, dt)
        elif self._should_seek_water():
            self._seek_water(dt)
            self.move(dt, animals)
        else:
            self._avoid_edges(dt)
            self._update_wander_pattern(dt)
            self.move(dt, animals)

        # Animation updates
        if self.idle or self.direction.length_squared() == 0:
            base_status = self.status.split('_')[0] if '_' in self.status else self.status
            idle_status = f"{base_status}_idle"
            frames = self.animations.get(idle_status, self.animations.get(base_status, []))
            if frames:
                self.image = frames[int(self.frame_index) % len(frames)]
        else:
            frames = self.animations.get(self.status, [])
            if frames:
                frame_interval = max(0.05, 0.25 * (50 / max(10, self.speed)))
                self.frame_timer += dt
                if self.frame_timer >= frame_interval:
                    self.frame_index = (self.frame_index + 1) % len(frames)
                    self.frame_timer = 0.0
                self.image = frames[int(self.frame_index)]


                

class Herbivore(Animal):
    @property
    def type(self):
        return "herbivore"