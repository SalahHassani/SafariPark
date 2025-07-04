import random, pygame
from pygame.math import Vector2
from src.model.character import Character
from src.utils.support import import_folder

POACHER_DETECTION_RADIUS = 180
POACHER_FLEE_SPEED = 40
POACHER_NORMAL_SPEED = 30
POACHER_ATTACK_RANGE = 20
POACHER_ATTACK_DAMAGE = 10
POACHER_ATTACK_COOLDOWN = 1.0  

class Poacher(Character):
    _DIRS = ["down", "down_left", "down_right", "up", "up_left", "up_right"]
    _DIRS_8 = ["up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right"]

    def __init__(self, pos: tuple[int, int], groups, map_rect: pygame.Rect):
        super().__init__(pos, groups, map_rect)
        self._load_assets()
        self.status = "idle_spear_down"
        self.image = self.animations[self.status][0]
        self.rect = self.image.get_rect(center=pos)

        self.weapon = "spear"
        self.spear_attacking = False
        self.random_direction = Vector2()
        self.random_move_timer = 0.0
        self.idle_phase = False
        self.random_idle_timer = 0.0
        self.idle_duration = random.uniform(1.0, 2.5)

        self.dying = False
        self._death_done = False
        self._death_hold = 0.0
        self._death_pause = 1.0
        self._death_variant = "death"

        self.hunted_animals = []
        self.current_target_animal = None
        self.last_attack_time = 0.0


    def _load_assets(self):
        self.animations = {}
        base = "src/assets/characters/poacher"
        
        for d in self._DIRS_8:
            suf = "down_left" if d == "left" else "down_right" if d == "right" else d
            self.animations[f"idle_spear_{d}"] = import_folder(f"{base}/idle/spear/{suf}")
            self.animations[f"walk_spear_{d}"] = import_folder(f"{base}/walk/spear/{suf}")
            self.animations[f"spear_attack_{d}"] = import_folder(f"{base}/attack/spear_attack/{suf}")
        for variant in ("death", "death_Gun", "death_Spear"):
            lower = variant.lower()
            for d in self._DIRS:
                self.animations[f"{lower}_{d}"] = import_folder(f"{base}/death/{variant}/{d}")




    def get_direction_label(self):
        dx = int(round(self.last_direction.x))
        dy = int(round(self.last_direction.y))



    def _dir_label(self):
        dx, dy = int(round(self.last_direction.x)), int(round(self.last_direction.y))

        if dx == -1 and dy == -1: return "up_left"
        if dx == 1 and dy == -1: return "up_right"
        if dx == -1 and dy == 1: return "down_left"
        if dx == 1 and dy == 1: return "down_right"
        if dx == -1: return "down_left"
        if dx == 1: return "down_right"
        if dy == -1: return "up"
        return "down"
    










    def _set_status(self):
        if self.dying: return
        lbl = self._dir_label()

        if self.spear_attacking: self.status = f"spear_attack_{lbl}"
        elif self.direction.length_squared() > 0: self.status = f"walk_spear_{lbl}"
        else: self.status = f"idle_spear_{lbl}"
        if self.status not in self.animations:
            self.status = "idle_spear_down"


    def animate(self, dt):
        animation = self.animations.get(self.status)
        if not animation:
            return




    def _animate(self, dt):
        frames = self.animations[self.status]
        speed = 4 if self.dying else 8
        self.frame_index += speed * dt
        if self.frame_index >= len(frames):
            self.frame_index = 0
            if "spear_attack" in self.status:
                self.spear_attacking = False
            elif self.dying:
                self._death_done = True
        self.image = frames[int(self.frame_index)]






    def _should_flee(self, rangers):
        for r in rangers:
            if r.health > 0 and self.pos.distance_to(r.pos) < POACHER_DETECTION_RADIUS:
                direction = self.pos - r.pos
                return direction.normalize() if direction.length_squared() else None
        return None

    def _random_move(self, dt):
        if self.idle_phase:
            self.direction = Vector2()
            self.random_idle_timer += dt
            if self.random_idle_timer >= self.idle_duration:
                self.idle_phase = False
                self.random_idle_timer = 0.0
                self.idle_duration = random.uniform(1.0, 2.5)
        else:
            self.random_move_timer += dt
            if self.random_move_timer >= 1.5:
                self.random_move_timer = 0.0
                self.idle_phase = random.choice([True, False])
                if not self.idle_phase:
                    self.random_direction = random.choice([
                        Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1),
                        Vector2(1, 1), Vector2(-1, -1), Vector2(-1, 1), Vector2(1, -1)
                    ])
            self.direction = Vector2() if self.idle_phase else self.random_direction

    def _hunt_animals(self, animals, current_time) -> bool:
        nearest_animal = None
        min_dist = POACHER_DETECTION_RADIUS

        for animal in animals:
            if not animal.is_alive:
                continue
            dist = self.pos.distance_to(animal.pos)
            if dist < min_dist:
                min_dist = dist
                nearest_animal = animal

        if nearest_animal:
            to_animal = nearest_animal.pos - self.pos
            if to_animal.length_squared() > 0:
                self.direction = to_animal.normalize()
                self.last_direction = self.direction.copy()
            self.speed = POACHER_NORMAL_SPEED

            if min_dist < POACHER_ATTACK_RANGE:
                if current_time - self.last_attack_time > POACHER_ATTACK_COOLDOWN:
                    self.spear_attacking = True
                    self.last_attack_time = current_time
                    nearest_animal.health -= POACHER_ATTACK_DAMAGE
                    print(f"[ATTACK] {nearest_animal.name} → health: {nearest_animal.health}")

                    # Make animal flee
                    if hasattr(nearest_animal, "flee_from"):
                        nearest_animal.flee_from(self.pos)

                    if nearest_animal.health <= 0:
                        nearest_animal.is_alive = False
                        nearest_animal.kill()
                        self.hunted_animals.append(nearest_animal)
                        print(f"[KILL] Poacher killed {nearest_animal.name} ({nearest_animal.species})")
                        self.current_target_animal = None
            return True
        return False

    def take_damage(self, dmg, weapon="generic"):
        if self.dying: return
        self.health -= dmg
        if self.health <= 0:
            self._death_variant = (
                "death_Gun" if weapon == "gun" else
                "death_Spear" if weapon == "spear" else "death"
            )
            self.die()

    def die(self):
        if self.dying: return
        self.dying = True
        self.direction = Vector2()
        self.speed = 0
        self.status = f"{self._death_variant.lower()}_{self._dir_label()}"
        if self.status not in self.animations:
            self.status = f"{self._death_variant.lower()}_down"
        self.frame_index = 0
        print(f"[DEATH] Poacher died. Hunted {len(self.hunted_animals)} animals.")

    def update(self, dt, rangers=None, animals=None):
        current_time = pygame.time.get_ticks() / 1000  # Convert to seconds

        if self.dying:
            self._animate(dt)
            if self._death_done:
                self._death_hold += dt
                if self._death_hold >= self._death_pause:
                    self.kill()
            return

        flee = self._should_flee(rangers or [])
        if flee:
            self.direction = flee
            self.speed = POACHER_FLEE_SPEED
        elif animals and self._hunt_animals(animals, current_time):
            pass
        else:
            self.speed = POACHER_NORMAL_SPEED
            self._random_move(dt)

        if self.spear_attacking:
            self.speed = POACHER_NORMAL_SPEED * 2

        if self.direction.length_squared() > 0:
            self.last_direction = self.direction.copy()

        self._set_status()
        self.move(dt)
        self._animate(dt)
