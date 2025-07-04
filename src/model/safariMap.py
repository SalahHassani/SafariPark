import os, sys
from random import randint, choice

import pygame
from pytmx.util_pygame import load_pygame

from src.config.settings import *
from src.model.rangers import Ranger, ControllableRanger
from src.model.sprites import *
from src.model.animals import Carnivore, Herbivore, Omnivore, Animal
from src.model.poacher import Poacher
from src.utils.support import import_folder
from src.utils.sound_manager import play_background_music
from src.view.storeUI import StoreUI
from src.view.pauseMenu import PauseMenu
from src.view.timeIndicator import TimeIndicator
from src.view.dayNightCycle import DayNightCycle
from src.model.jeep import Jeep


class Map:
    """Manages the terrain, all entities, and overlay UI for a single level."""

    def __init__(self, difficulty: str, game_reference=None):
        # ── Surfaces / Fonts ─────────────────────────────────────────
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 24)

        # ── Economy & Stats ─────────────────────────────────────────
        self.visitor_count = 0
        self.capital = 10_000

        # ── Icons ───────────────────────────────────────────────────
        self.icon_poacher = pygame.image.load('src/assets/images/icons/poacher.png').convert_alpha()
        self.icon_visitor = pygame.image.load('src/assets/images/icons/tourist.png').convert_alpha()
        self.icon_animal  = pygame.image.load('src/assets/images/icons/animal.png').convert_alpha()
        self.icon_ranger  = pygame.image.load('src/assets/images/icons/ranger.png').convert_alpha()
        self.icon_capital = pygame.image.load('src/assets/images/icons/capital.png').convert_alpha()
        self.day_night_icon = pygame.image.load("src/assets/ui/day-night.png").convert_alpha()
        self.day_night_icon = pygame.transform.scale(self.day_night_icon, (40, 40))
        self.day_night_rect = pygame.Rect(60, 10, 40, 40)

        # Day/Night toggle icon
        self.icon_day_night = pygame.image.load('src/assets/ui/day-night.png').convert_alpha()
        self.icon_day_night = pygame.transform.scale(self.icon_day_night, (40, 40))
        self.day_night_rect = self.icon_day_night.get_rect(topleft=(60, 10))

        # ── Helpers / UI ────────────────────────────────────────────
        self.difficulty = difficulty.lower()
        self.jeep_start = None
        self.time_indicator = TimeIndicator(difficulty)
        self.pause_menu     = PauseMenu(10, 10, 40, 40, "Pause", self.font, (0, 0, 0), game_reference)
        self.store_ui       = StoreUI(self)
        self.paused         = False
        self.store_ui = StoreUI(self)
        self.store_ui.generate_animal_store_items()
        self.day_night_cycle = DayNightCycle(self, self.time_indicator)
        self.chip_enabled = False
        self.chipped_animals = set()
        self.chipping_ui_open = False
        self.unchipped_animals_to_show = []
        self.selected_chip_index = 0
        self.pending_placement = None
        self.placement_confirm_rect = None
        self.placement_cancel_rect = None
        self.placement_mode = None 
        self.placement_buttons = {} 
        self.placement_preview = None

        # ── Map Graphics ────────────────────────────────────────────
        self.tmx = f"src/assets/maps/{self.difficulty}_map.tmx"
        self.png = f"src/assets/maps/{self.difficulty}_map.png"
        if not (os.path.exists(self.tmx) and os.path.exists(self.png)):
            raise FileNotFoundError(f"Missing map files for difficulty '{difficulty}'")
        self.tmx_items  = load_pygame(self.tmx)
        self.map_surface = pygame.image.load(self.png).convert_alpha()
        self.map_rect    = self.map_surface.get_rect(topleft=(0, 0))

        # ── Master Sprite Group And Collision Sprites ──────────────────────────────────────
        self.all_sprites = CameraGroup(self.map_rect.width, self.map_rect.height)
        self.collision_sprites = pygame.sprite.Group()

        # ── Poacher Timing ──────────────────────────────────────────
        self.poachers           = [] 
        self.poacher_timer      = 0.0
        self.poacher_add_time   = 60.0
        self.poacher_remove_time = 100.0

        # ── Animal Collections ──────────────────────────────────────
        self.herbivores = []
        self.carnivores = []
        self.omnivores  = []
        self.animals    = []

        # ── Build World ─────────────────────────────────────────────
        self._setup_tiles_and_deco()
        self._spawn_entities()

        # ── Win & loss condition ────────────────────────────────────
        self.win_streak_months = 0
        
        difficulty_levels = {
            'easy':    {'months': 3,  'visitors': 80,  'herbivores': 20, 'carnivores': 10, 'capital': 15000},
            'medium':  {'months': 6,  'visitors': 100, 'herbivores': 30, 'carnivores': 15, 'capital': 20000},
            'hard':    {'months': 12, 'visitors': 120, 'herbivores': 40, 'carnivores': 20, 'capital': 35000}
        }
        self.win_conditions = difficulty_levels[self.difficulty]
        self.game_result = None  # 'win' or 'loss'
        self.result_time = 0
        self.new_game_requested = False

        
        # ── Background Music or voices ────────────────────────────────────
        play_background_music()


    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def add_animal(
        self,
        cls,
        name: str,
        species: str,
        age: int,
        pos: tuple[int, int],
        price: int,
        *,
        speed: float = 40,
        scale: float = 1.0,
        body_shape: str = "normal",
        collision_sprites = None,
        group_type: str | None = None,
        gender: str = None
    ) -> Animal:
        """Central helper to create an animal, track it and add to the right lists."""

        a = cls(
            name, species, age, pos,
            self.all_sprites, self.map_rect, price,
            speed=speed, scale=scale, body_shape=body_shape,
            group_type=group_type, gender=gender
        )

        # Assign tile collision group here 
        a.collision_sprites = self.collision_sprites

        self.animals.append(a)
        if   isinstance(a, Herbivore):  self.herbivores.append(a)
        elif isinstance(a, Carnivore):  self.carnivores.append(a)
        elif isinstance(a, Omnivore):   self.omnivores.append(a)
        return a

    # ─────────────────────────────────────────────────────────────
    # Static map layers
    # ─────────────────────────────────────────────────────────────
    def _setup_tiles_and_deco(self):
        # House layers
        for layer in ['house_floor', 'house_walls']:
            for x, y, surf in self.tmx_items.get_layer_by_name(layer).tiles():
                Generic(
                    (x * TILE_SIZE, y * TILE_SIZE),
                    surf,
                    self.all_sprites,
                    LAYERS['house_floor']
                )

        # Fences
        for x, y, surf in self.tmx_items.get_layer_by_name('fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)

        # Road
        self.road_positions = []

       # Road tiles (visible + path)
        # Load road tile positions for the Jeep path
        if 'roadtiles' in self.tmx_items.layernames:
            for obj in self.tmx_items.get_layer_by_name('roadtiles'):
                if hasattr(obj, 'x') and hasattr(obj, 'y'):
                    x = int(obj.x + obj.width // 2)
                    y = int(obj.y + obj.height // 2)
                    self.road_positions.append((x, y))

            print(f"✅ Loaded {len(self.road_positions)} roadtiles from Tiled.")
        else:
            print("❌ 'roadtiles' layer missing from Tiled map!")

        # THEN: Render the roadtiles so they appear on screen
        if 'roadtiles' in self.tmx_items.layernames:
            for x, y, surf in self.tmx_items.get_layer_by_name('roadtiles').tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, z=LAYERS['road'])  # visual display
        #path for the jeep
        self.jeep_path = []
        self.jeep_end_point = None

        for obj in self.tmx_items.get_layer_by_name('jeep_path'):
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                point = (int(obj.x), int(obj.y))
                self.jeep_path.append(point)
                if getattr(obj, "name", "") == "EndPoint":
                    self.jeep_end_point = point
            print(f"✅ Loaded {len(self.jeep_path)} jeep path points.")
        else:
            print("❌ 'jeep_path' layer missing from Tiled map!")
        
        
        
        # Water tiles (animated)
        water_frames = import_folder('src/assets/graphics/water')  # Fixed path
        for x, y, surf in self.tmx_items.get_layer_by_name('water').tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)

        # Trees
        for obj in self.tmx_items.get_layer_by_name('trees'):
            if obj.name == 'big':
                Tree((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites], obj.name)
            elif obj.name == 'small':
                Tree((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites], obj.name)
            #elif obj.name == 'bush':
            #    Bush((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])
                
        # Wildflowers
        for obj in self.tmx_items.get_layer_by_name('flowers'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # Collision tiles (invisible walls)
        for x, y, _ in self.tmx_items.get_layer_by_name('hit').tiles():
            invisible_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)  # fully transparent
            collider = Generic(
                pos=(x * TILE_SIZE, y * TILE_SIZE),
                surf=invisible_surface,
                groups=[self.collision_sprites],
                z=LAYERS['main']  # use proper z, doesn’t matter since it's invisible
            )
            collider.hitbox = collider.rect.copy().inflate(-10, -10)  # adjust for finer collision

        # Mushrooms
        for obj in self.tmx_items.get_layer_by_name('mushrooms'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # Collision tiles (debug color)
        for x, y, _ in self.tmx_items.get_layer_by_name('hit').tiles():
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surface.fill("blue")  # makes collision tiles visible for testing
            tile = Generic((x * TILE_SIZE, y * TILE_SIZE), surface, self.collision_sprites)
            tile.hitbox = tile.rect.copy()  # ensure the hitbox exists

        # Player spawn
        # for obj in self.tmx_items.get_layer_by_name('player_spawn'):
        #     if obj.name == 'Player':
        #         self.player = Ranger((obj.x, obj.y), self.all_sprites, self.map_rect, self.collision_sprites)

        # Ground base image (optional backdrop)
        Generic(
            pos=(0, 0),
            surf=pygame.image.load(self.png).convert_alpha(),  # Fixed path
            groups=self.all_sprites,
            z=LAYERS['grass']
        )
        Generic((0, 0), self.map_surface, self.all_sprites, LAYERS["grass"])
        for layer in ("house_floor", "house_walls", "fence", "tiles"):
            for x, y, surf in self.tmx_items.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS["house_floor"])
        water_frames = import_folder("src/assets/graphics/water")

        for x, y, _ in self.tmx_items.get_layer_by_name("water").tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)

        for deco in ("flowers","mushrooms"):
            for obj in self.tmx_items.get_layer_by_name(deco):
                WildFlower((obj.x, obj.y), obj.image, [self.all_sprites])
                
        # Trees
        for obj in self.tmx_items.get_layer_by_name('trees'):
            if obj.name == 'big':
                Tree((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites], obj.name)
            elif obj.name == 'small':
                Tree((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites], obj.name)
            #elif obj.name == 'bush':
            #    Bush((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])


            # TILE-BASED road path
            if 'roadtiles' in self.tmx_items.layernames:
                for x, y, _ in self.tmx_items.get_layer_by_name('roadtiles').tiles():
                    world_x = x * TILE_SIZE + TILE_SIZE // 2
                    world_y = y * TILE_SIZE + TILE_SIZE // 2
                    self.road_positions.append((world_x, world_y))

                print(f"✅ Built path from {len(self.road_positions)} roadtiles.")
            else:
                print("❌ 'roadtiles' layer missing!")
    # ─────────────────────────────────────────────────────────────
    # Dynamic entities
    # ─────────────────────────────────────────────────────────────
    def _spawn_entities(self):
        # Find the player spawn position from Tiled map
        player_spawn = None
        for obj in self.tmx_items.get_layer_by_name("player_spawn"):
            if obj.name == "Player":
                player_spawn = (obj.x, obj.y)
                break  # Stop after first match
        # ── Rangers ───────────────────────────────────────────────
        self.rangers = []

        # 1. Use spawn position from map if found
        if player_spawn:
            ranger = ControllableRanger(player_spawn, self.all_sprites, self.map_rect, self.collision_sprites)
        else:
            # fallback to default position if not set
            ranger = ControllableRanger((740, 660), self.all_sprites, self.map_rect, self.collision_sprites)

        self.rangers.append(ranger)
        self.ranger = ranger  # Set as active

        # 2. Add the other (non-controllable) rangers as usual
        self.rangers.append(Ranger((1200, 660), self.all_sprites, self.map_rect, self.collision_sprites))
        self.rangers.append(Ranger((700,  720), self.all_sprites, self.map_rect, self.collision_sprites))
        self.rangers.append(Ranger((1350, 760), self.all_sprites, self.map_rect, self.collision_sprites))
        self.rangers.append(Ranger((1700,1250), self.all_sprites, self.map_rect, self.collision_sprites))
        self.current_ranger_index = 0

        # ── Herbivores ───────────────────────────────────────────
        self.add_animal(Herbivore, "Daisy",   "cow",       7, (1150,1140), price=150, speed=40, scale=1.1, body_shape="fat",    group_type="cow",    gender="female")
        self.add_animal(Herbivore, "Daisy2",  "cow",       3, (1130,1130), price=150, speed=40, scale=1.1, body_shape="normal", group_type="cow",    gender="female")
        self.add_animal(Herbivore, "Daisy3",  "cow",       2, (1120,1150), price=150, speed=40, scale=1.1, body_shape="fat",    group_type="cow",    gender="male")
        self.add_animal(Herbivore, "Daisy4",  "cow",       2, (1200,1210), price=150, speed=40, scale=1.1, body_shape="normal", group_type="cow",    gender="female")
        self.add_animal(Herbivore, "Daisy5",  "cow",       4, (1110,1120), price=150, speed=40, scale=1.1, body_shape="fat",    group_type="cow",    gender="male")

        self.add_animal(Herbivore, "Bambi",   "deer",      2, (1300, 950), price=120, speed=60, scale=1.0, body_shape="tall",   group_type="deer",   gender="female")
        self.add_animal(Herbivore, "Nanny",   "goat",      4, (1400,1000), price=130, speed=50, scale=0.9, body_shape="normal", group_type="goat",   gender="female")
        self.add_animal(Herbivore, "Wooly",   "sheep",     3, (1450,1050), price=100, speed=45, scale=1.0, body_shape="fat",    group_type="sheep",  gender="male")
        self.add_animal(Herbivore, "Clucky",  "hen",       2, (1500,1100), price=50,  speed=70, scale=0.5, body_shape="normal", group_type="chicken",gender="female")
        self.add_animal(Herbivore, "Rooster", "cock",      3, (1520,1080), price=60,  speed=70, scale=0.6, body_shape="normal", group_type="chicken",gender="male")

        self.add_animal(Herbivore, "Trotter", "pig",       4, (1600,1150), price=140, speed=35, scale=1.2, body_shape="fat",    group_type="pig",    gender="male")
        self.add_animal(Herbivore, "Blaze",   "horse",     5, (1650,1200), price=200, speed=65, scale=1.3, body_shape="tall",   group_type="horse",  gender="female")

        self.add_animal(Herbivore, "Fluffy",  "rabbit",    2, (1700,1250), price=30,  speed=80, scale=0.4, body_shape="normal", group_type="rabbit", gender="female")
        self.add_animal(Herbivore, "Thumper", "rabbit",    2, (1750,1300), price=30,  speed=80, scale=0.4, body_shape="normal", group_type="rabbit", gender="male")

        self.add_animal(Herbivore, "Buffy",   "buffalo/3", 5, (1800,1350), price=170, speed=30, scale=1.5, body_shape="fat",    group_type="buffalo",gender="female")
        self.add_animal(Herbivore, "Oxie",    "musk ox/5", 2, (1850,1300), price=180, speed=28, scale=1.6, body_shape="fat",    group_type="musk_ox", gender="male")
        self.add_animal(Herbivore, "Oxie2",   "musk ox/2", 4, (1830,1200), price=180, speed=28, scale=1.6, body_shape="fat",    group_type="musk_ox", gender="female")
        self.add_animal(Herbivore, "Oxie3",   "musk ox/3", 5, (1450,1500), price=180, speed=28, scale=1.6, body_shape="fat",    group_type="musk_ox", gender="female")
        self.add_animal(Herbivore, "Oxie4",   "musk ox/4", 6, (1750,1200), price=180, speed=28, scale=1.6, body_shape="fat",    group_type="musk_ox", gender="male")
        self.add_animal(Herbivore, "Oxie5",   "musk ox/4", 2, (1800,1400), price=180, speed=28, scale=1.6, body_shape="fat",    group_type="musk_ox", gender="female")


        # ── Carnivores ─────────────────────────────────────────────
        self.add_animal(Carnivore, "Simba",    "cub",      5, ( 900, 900), price=300, speed=55, scale=1.0, body_shape="normal", group_type="lion",  gender="male")
        self.add_animal(Carnivore, "Whiskers", "cat",      2, ( 950, 950), price=200, speed=65, scale=0.6, body_shape="normal", group_type="cat",   gender="female")
        self.add_animal(Carnivore, "Buddy",    "puppy",    1, ( 970, 980), price=120, speed=60, scale=0.7, body_shape="normal", group_type="dog",   gender="male")
        self.add_animal(Carnivore, "Alpha",    "wolf/2",   7, (1000, 600), price=350, speed=60, scale=1.0, body_shape="normal", group_type="wolf",  gender="female")
        self.add_animal(Carnivore, "Shadow",   "jackals/3",4, (1050, 620), price=260, speed=62, scale=1.1, body_shape="normal", group_type="jackal",gender="male")
        self.add_animal(Carnivore, "Fang",     "tigers/5", 6, (1100, 650), price=400, speed=50, scale=1.2, body_shape="fat",    group_type="tiger", gender="male")
        self.add_animal(Carnivore, "Cleo",     "lioness/2",5, (1150, 670), price=380, speed=55, scale=1.1, body_shape="normal", group_type="lion",  gender="female")


        # ── Omnivores ──────────────────────────────────────────────
        self.add_animal(Omnivore, "Grizzly",  "bears/1",  8, (1200, 700), price=400, speed=35, scale=1.5, body_shape="fat",    group_type="bear",   gender="male")
        self.add_animal(Omnivore, "Perry",    "beavers/2",5, (1250, 720), price=220, speed=45, scale=0.9, body_shape="fat",    group_type="beaver", gender="female")
        self.add_animal(Omnivore, "Bandit",   "raccoons/3",3,(1300, 740), price=180, speed=55, scale=0.8, body_shape="normal", group_type="raccoon",gender="male")
        self.add_animal(Omnivore, "Balu",     "bear cubs/4",2,(1350,760),price=150, speed=50, scale=1.0, body_shape="fat",    group_type="bear",   gender="female")
        self.add_animal(Omnivore, "Rollo",    "boars/6",   4,(1400, 780), price=190, speed=48, scale=1.1, body_shape="fat",    group_type="boar",   gender="male")
        self.add_animal(Omnivore, "Stretch",  "giraffe/2", 6,(1430, 810), price=350, speed=40, scale=1.6, body_shape="tall",   group_type="giraffe",gender="female")
        self.add_animal(Omnivore, "Stretch2", "giraffe/2", 6,(1480, 830), price=350, speed=40, scale=1.6, body_shape="tall",   group_type="giraffe",gender="male")
        self.add_animal(Omnivore, "Stretch3", "giraffe/2", 6,(1450, 850), price=350, speed=40, scale=1.6, body_shape="tall",   group_type="giraffe",gender="female")
        self.add_animal(Omnivore, "Stretch4", "giraffe/2", 6,(1490, 700), price=350, speed=40, scale=1.6, body_shape="tall",   group_type="giraffe",gender="male")

        # ── Jeep ───────────────────────────────────────────────
        for obj in self.tmx_items.objects:
            if obj.name == "JeepStart":
                x = int(obj.x + obj.width // 2)
                y = int(obj.y + obj.height // 2)
                print(f"🚙 Spawning Jeep at tile: ({x}, {y})")
                self.jeep_start = (x, y)
                self.jeep = Jeep((x, y), self.jeep_path, self.jeep_end_point, [self.all_sprites], map_ref=self)
    # ─────────────────────────────────────────────────────────────
    # Gameplay loop
    # ─────────────────────────────────────────────────────────────
    def switch_ranger(self):
        pygame.time.wait(150)
        old = self.rangers[self.current_ranger_index]
        pos = old.pos
        old.kill()
        self.rangers[self.current_ranger_index] = Ranger(pos, self.all_sprites, self.map_rect, self.collision_sprites)

        self.current_ranger_index = (self.current_ranger_index + 1) % len(self.rangers)

        new = self.rangers[self.current_ranger_index]
        pos = new.pos
        new.kill()
        ctrl = ControllableRanger(pos, self.all_sprites, self.map_rect, self.collision_sprites)
        self.rangers[self.current_ranger_index] = ctrl
        self.ranger = ctrl
        self.all_sprites.reset_to_follow()

    def run(self, dt: float, events):
        adjusted_dt = dt * self.time_indicator.time_multiplier
        self.all_sprites.handle_mouse_drag(events)
        self.display_surface.fill("black")
        self.all_sprites.custom_draw(self.ranger)
        

        self.paused = self.pause_menu.menu_open
        if not self.paused:
            self.time_indicator.update(dt)

            # ── Update & prune animals ─────────────────────────────
            for a in self.animals[:]:
                a.update(adjusted_dt, self.animals)
                if not a.is_alive:
                    self.animals.remove(a)
                    try:
                        if isinstance(a, Herbivore):
                            self.herbivores.remove(a)
                        elif isinstance(a, Carnivore):
                            self.carnivores.remove(a)
                        elif isinstance(a, Omnivore):
                            self.omnivores.remove(a)
                    except ValueError:
                            print(f"[WARN] Tried to remove {a.name} from specific list but it was not found (since it was only added in animals list not sublists).")


            # ── Update everything else ─────────────────────────────
            for s in self.all_sprites:
                # if not isinstance(s, Animal):
                #     s.update(adjusted_dt)

                #     for s in self.all_sprites:
                if isinstance(s, Ranger):
                    s.update(adjusted_dt, self.poachers)
                elif not isinstance(s, Animal):
                    s.update(adjusted_dt)

                if isinstance(s, Jeep):
                    s.update(adjusted_dt)
                    s.draw(self.display_surface, self.all_sprites.offset)

            self.all_sprites.handle_mouse_drag(events, allow_dragging=not bool(self.placement_mode))

            if pygame.key.get_pressed()[pygame.K_TAB]:
                self.switch_ranger()

            ################################################################################
            # ── Poacher Logic ─────────────────────────────────────            
            self.poacher_timer += adjusted_dt
            if self.poacher_timer >= self.poacher_add_time:
                self.spawn_poacher()
                self.poacher_timer = 0.0

            # ──────────────────────────────────────────────────────────────
            # 1) remove DEAD poachers (health ≤ 0)               NEW
            # 2) remove EXPIRED poachers (spawned too long ago)  unchanged
            # ──────────────────────────────────────────────────────────────
            alive_poachers: list[Poacher] = []
            for p in self.poachers:
                if p.health <= 0:
                    p.die()                               
                    continue                             

                # 2) over lifetime limit ?
                lifetime_ms = pygame.time.get_ticks() - p.spawn_time
                if lifetime_ms >= self.poacher_remove_time * 1000:
                    p.kill()
                    continue

                # otherwise: still alive & inside lifetime – keep it
                alive_poachers.append(p)

            self.poachers = alive_poachers
            ################################################################################

        # ── Always draw overlays ──────────────────────────────────
        self.day_night_cycle.draw(self.all_sprites.offset)
        self.time_indicator.draw(self.display_surface)
        self.pause_menu.draw(self.display_surface)
        self.display_surface.blit(self.day_night_icon, self.day_night_rect)
        self.store_ui.draw()
        self.draw_minimap()
        self.draw_stats_bar()
        self.display_surface.blit(self.icon_day_night, self.day_night_rect)

        ################################################################################
        # # ── Draw detection ranges ──────────────────────────────────
        # for animal in self.animals:
        #     animal.draw_detection_range(self.display_surface, self.all_sprites.offset)

        # for ranger in self.rangers:
        #     ranger.draw_detection_range(self.display_surface, self.all_sprites.offset)

        # for poacher in self.poachers:
        #     poacher.draw_detection_range(self.display_surface, self.all_sprites.offset)

        for poacher in self.poachers:
            poacher.update(adjusted_dt, self.rangers, self.animals)
        ################################################################################

        # ── Always check game end conditions ──────────────────────
        self.check_win_loss(adjusted_dt)
        self.draw_game_result()
        # Check game over click
        if self.game_result:
            time_since_result = pygame.time.get_ticks() - self.result_time
            if time_since_result > 1000:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.new_game_btn.collidepoint(event.pos):
                            self.new_game_requested = True 
                        elif self.quit_btn.collidepoint(event.pos):
                            pygame.quit()
                            sys.exit()
                
        # ---- LIVE PLACEMENT PREVIEW ----
        if self.placement_mode:
            preview_img = self.placement_mode["image"].copy()
            preview_img.set_alpha(128)
            iw, ih = preview_img.get_size()

            # Use locked target if available, otherwise follow mouse
            if self.placement_mode["target"] is not None:
                world_x, world_y = self.placement_mode["target"]
            else:
                mx, my = pygame.mouse.get_pos()
                world_x = mx + self.all_sprites.offset.x
                world_y = my + self.all_sprites.offset.y

            screen_x = world_x - self.all_sprites.offset.x
            screen_y = world_y - self.all_sprites.offset.y

            self.placement_mode["preview_pos"] = (world_x, world_y)

            self.display_surface.blit(preview_img, (screen_x, screen_y))

            # Only show buttons if target is locked
            if self.placement_mode["target"] is not None:
                font = pygame.font.SysFont(None, 28)
                place_rect = pygame.Rect(screen_x, screen_y + ih + 10, 120, 40)
                cancel_rect = pygame.Rect(screen_x + 140, screen_y + ih + 10, 120, 40)

                pygame.draw.rect(self.display_surface, (80, 160, 100), place_rect, border_radius=8)
                pygame.draw.rect(self.display_surface, (30, 90, 60), place_rect, 2, border_radius=8)
                pygame.draw.rect(self.display_surface, (160, 80, 80), cancel_rect, border_radius=8)
                pygame.draw.rect(self.display_surface, (90, 30, 30), cancel_rect, 2, border_radius=8)

                place_text = font.render("Place Here", True, (255, 255, 255))
                cancel_text = font.render("Cancel", True, (255, 255, 255))
                self.display_surface.blit(place_text, place_text.get_rect(center=place_rect.center))
                self.display_surface.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

                self.placement_buttons["place"] = place_rect
                self.placement_buttons["cancel"] = cancel_rect

            else:
                # Optional tooltip before locking
                font = pygame.font.SysFont(None, 24)
                tooltip = font.render("Double-click to place item", True, (255, 255, 255))
                self.display_surface.blit(tooltip, (screen_x + iw // 2, screen_y - 25))


        # ---- CLICK HANDLING ----
        self.last_click_time = getattr(self, 'last_click_time', 0)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.placement_mode:
                    # Double-click detection to lock placement
                    now = pygame.time.get_ticks()
                    if now - self.last_click_time < 300:
                        if self.placement_mode["target"] is None:
                            # Lock to the position shown in the last preview
                            if "preview_pos" in self.placement_mode:
                                self.placement_mode["target"] = self.placement_mode["preview_pos"]

                    self.last_click_time = now

                    # If placement is locked, handle confirm/cancel
                    if self.placement_mode["target"] is not None:
                        place_btn = self.placement_buttons.get("place")
                        cancel_btn = self.placement_buttons.get("cancel")

                        if place_btn and place_btn.collidepoint(event.pos):
                            from src.model.sprites import Generic
                            pos = self.placement_mode["target"]
                            # Generic(pos, self.placement_mode["image"], self.all_sprites, z=LAYERS['main'])
                            # self.capital -= self.placement_mode["price"]

                            if self.placement_mode["type"] == 'tree' or self.placement_mode["type"] == 'flower':
                                Tree(pos, self.placement_mode["image"], [self.all_sprites, self.collision_sprites], "big")
                            elif self.placement_mode["type"] == 'pond':
                                water_frames = import_folder("src/assets/graphics/water")
                                Water(pos, water_frames, [self.all_sprites, self.collision_sprites], z=LAYERS["main"])

                            #elif obj.name == 'bush':
                            #    Bush(pos), self.placement_mode["image"], [self.all_sprites, self.collision_sprites])
                            else:
                                Generic(pos, self.placement_mode["image"], self.all_sprites, z=LAYERS['main'])
                                self.capital -= self.placement_mode["price"]
        

                            # Reset target to allow placing again
                            self.placement_mode["target"] = None
                            self.placement_buttons = {}

                        elif cancel_btn and cancel_btn.collidepoint(event.pos):
                            self.placement_mode = None
                            self.placement_buttons = {}

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def spawn_poacher(self):
        margin = 100
        x = randint(margin, self.map_rect.width  - margin)
        y = randint(margin, self.map_rect.height - margin)
        p = Poacher((x, y), self.all_sprites, self.map_rect)
        p.spawn_time = pygame.time.get_ticks()
        self.poachers.append(p)

    def toggle_day_night(self):
        """Toggle between day and night modes"""
        print("Map.toggle_day_night called")
        is_night = self.day_night_cycle.toggle()
        return is_night
    
    def draw_placement_prompt(self, events):
        mouse = pygame.mouse.get_pos()
        screen = self.display_surface
        font = pygame.font.SysFont(None, 28)
        colors = self.store_ui.colors  # reuse same palette

        w, h = 360, 140
        x, y = (SCREEN_WIDTH - w) // 2, SCREEN_HEIGHT - h - 30
        rect = pygame.Rect(x, y, w, h)

        pygame.draw.rect(screen, colors["item_bg"], rect, border_radius=10)
        pygame.draw.rect(screen, colors["dark_foliage"], rect, 2, border_radius=10)

        txt = font.render("Click on map to place item", True, colors["white"])
        screen.blit(txt, (x + (w - txt.get_width()) // 2, y + 20))

        # Buttons
        place_btn = pygame.Rect(x + 40, y + 70, 120, 35)
        cancel_btn = pygame.Rect(x + 200, y + 70, 120, 35)

        pygame.draw.rect(screen, colors["accent"], place_btn, border_radius=8)
        pygame.draw.rect(screen, colors["dark_foliage"], cancel_btn, border_radius=8)

        screen.blit(font.render("Place Here", True, colors["white"]), place_btn.move(15, 5))
        screen.blit(font.render("Cancel", True, colors["white"]), cancel_btn.move(25, 5))

        self.placement_buttons = {"place": place_btn, "cancel": cancel_btn}

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if place_btn.collidepoint(event.pos):
                    self.spawn_placement_item()
                elif cancel_btn.collidepoint(event.pos):
                    self.placement_mode = None
                    
    def spawn_placement_item(self):
        if not self.placement_mode or "target" not in self.placement_mode:
            print("No placement target selected.")
            return

        map_x, map_y = self.placement_mode["target"]
        image = self.placement_mode["image"]
        price = self.placement_mode["price"]

        from src.model.sprites import Generic
        Generic((map_x, map_y), image, self.all_sprites, z=LAYERS["main"])
        self.capital -= price
        self.placement_mode = None

    def draw_minimap(self):
        mini_w, mini_h = 250, 250
        mini = pygame.Surface((mini_w, mini_h), pygame.SRCALPHA)
        mini.fill((30, 30, 30, 180))

        sx, sy = mini_w / self.map_rect.width, mini_h / self.map_rect.height

        # Show animals:
        visible_animals = self.animals if not self.day_night_cycle.is_night else self.chipped_animals
        for a in visible_animals:
            pygame.draw.circle(mini, (0, 200, 0), (int(a.rect.centerx * sx), int(a.rect.centery * sy)), 2)

        # Show rangers
        for idx, r in enumerate(self.rangers):
            color = (255, 0, 0) if idx == self.current_ranger_index else (220, 220, 220)
            pygame.draw.circle(mini, color, (int(r.rect.centerx * sx), int(r.rect.centery * sy)), 3)

        # Camera view rectangle
        offset_x = self.all_sprites.offset.x
        offset_y = self.all_sprites.offset.y

        view = pygame.Rect(
            int(offset_x * sx),
            int(offset_y * sy),
            int(SCREEN_WIDTH * sx),
            int(SCREEN_HEIGHT * sy)
        )

        view = pygame.Rect(int(offset_x * sx), int(offset_y * sy), int(SCREEN_WIDTH * sx), int(SCREEN_HEIGHT * sy))
        pygame.draw.rect(mini, (255, 255, 0), view, 2)

        # Draw border
        pygame.draw.rect(mini, (255, 255, 255), mini.get_rect(), 2)

        # ── Blit to screen
        minimap_pos = (10, SCREEN_HEIGHT - mini_h - 10)
        self.minimap_rect = pygame.Rect(minimap_pos, (mini_w, mini_h))  # <-- Store rect for click detection
        self.display_surface.blit(mini, minimap_pos)

        # ── Handle click on minimap
        if pygame.mouse.get_pressed()[0]:  # left click
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.minimap_rect.collidepoint(mouse_x, mouse_y):
                rel_x = (mouse_x - self.minimap_rect.left) / mini_w
                rel_y = (mouse_y - self.minimap_rect.top) / mini_h
                map_x = rel_x * self.map_rect.width
                map_y = rel_y * self.map_rect.height

                # Set camera offset to center on clicked point
                self.all_sprites.offset.x = max(0, min(map_x - SCREEN_WIDTH // 2, self.map_rect.width - SCREEN_WIDTH))
                self.all_sprites.offset.y = max(0, min(map_y - SCREEN_HEIGHT // 2, self.map_rect.height - SCREEN_HEIGHT))

                self.all_sprites.manual_override = True  # Activate manual drag mode

    def draw_stats_bar(self):
        """Draws the top-right stats bar showing visitors, animals, rangers, poachers, and capital."""
        font = pygame.font.Font(None, 28)
        BLACK = (0, 0, 0)

        icon_size = 25      
        icon_spacing = 5 
        padding = 6     
        y = 6     
        bar_height = 40
        border_radius = 12

        stat_items = [
            (self.icon_visitor, self.visitor_count, 40),
            (self.icon_animal, len(self.animals), 40),
            (self.icon_ranger, len(self.rangers), 40),
            (self.icon_poacher, len(self.poachers), 40),
            (self.icon_capital, self.capital, 70)
        ]

        bar_width = sum(icon_size + icon_spacing + extra for _, _, extra in stat_items) + padding * 2
        stat_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)

        # Draw rounded rectangle background
        pygame.draw.rect(stat_surface, (255, 255, 255, 120), 
                        (0, 0, bar_width, bar_height), 
                        border_radius=border_radius)

        # Draw each icon and its value
        start_x = padding
        for icon, value, extra in stat_items:
            scaled_icon = pygame.transform.scale(icon, (icon_size, icon_size))
            stat_surface.blit(scaled_icon, (start_x, y))
            text_surface = font.render(str(value), True, BLACK)
            stat_surface.blit(text_surface, (start_x + icon_size + 2, y + 3))
            start_x += icon_size + icon_spacing + extra

        # Blit to screen
        screen_width = self.display_surface.get_width()
        self.display_surface.blit(stat_surface, (screen_width - bar_width - padding, 10))


    def buy_item(self, item_type, animal_type=None, item_price=None):
        decor_image_map = {
            "pond": "Water",
            "flower": "flower",
            "tree": "tree",
            "bush": "bush"
        }

        prices = {
            "chip": 50,
            "jeep": 500,
            "pond": 100,
            "flower": 10,
            "tree": 50,
            "bush": 25
        }

        if item_type != "animal" and item_type not in prices:
            print(f"Unknown item type: {item_type}")
            return False

        if item_price is None and item_type == 'animal':
            print(f"[ERROR] item_price is None for animal: {animal_type}")
            return False

        price = item_price if item_price is not None else prices[item_type]
        # print(f"$$$$$$$$$$$$$$$$$$$$$$$$$$$ {price} ^^^^^^^^^^^^^^^^^^^^^^ {self.capital} $$$$$$$$$$$$$$$$$$$$$$$$$$$")
        if self.capital < price:
            print(f"[DEBUG] Capital: {self.capital}, Required: {price}, Type: {item_type}")
            print(f"Not enough capital to buy {item_type}")
            return False

        if item_type == 'animal':
            pos = (randint(500, 1500), randint(500, 1500))
            species_map = {
                "cow": "cow",
                "deer": "deer",
                "goat": "goat",
                "sheep": "sheep",
                "hen": "hen",
                "cock": "cock",
                "pig": "pig",
                "horse": "horse",
                "rabbit": "rabbit",
                "buffalo": "buffalo/3",
                "musk ox": "musk ox/4",
                "cub": "cub",
                "cat": "cat",
                "puppy": "puppy",
                "wolf": "wolf/2",
                "jackals": "jackals/3",
                "tigers": "tigers/5",
                "lioness": "lioness/2",
                "bears": "bears/1",
                "beavers": "beavers/2",
                "raccoons": "raccoons/3",
                "bear cubs": "bear cubs/4",
                "boars": "boars/6",
                "giraffe": "giraffe/2"
            }

            species_key = animal_type.lower()
            species = species_map.get(species_key, "deer")

            if species_key in ["cub", "cat", "puppy", "wolf", "jackals", "tigers", "lioness"]:
                self.add_animal(Carnivore, f"Newbie_{species_key}",   f"{species_key}",       5, pos, price=price, speed=40, scale=1.1, body_shape="Normal",    group_type=f"{species_key}",    gender="female")
                # animal = Carnivore("Newbie", species, 3, pos, self.all_sprites, self.map_rect, price=price)
                # self.carnivores.append(animal)
            elif species_key in ["bears", "beavers", "raccoons", "bear cubs", "boars", "giraffe"]:
                self.add_animal(Omnivore, f"Newbie_{species_key}",   f"{species_key}",       4, pos, price=price, speed=35, scale=1.1, body_shape="Normal",    group_type=f"{species_key}",    gender="female")
                # animal = Omnivore("Newbie", species, 3, pos, self.all_sprites, self.map_rect, price=price)
                # self.omnivores.append(animal)
            else:
                self.add_animal(Herbivore, f"Newbie_{species_key}",   f"{species_key}",       3, pos, price=price, speed=30, scale=1.1, body_shape="Normal",    group_type=f"{species_key}",    gender="female")
                # animal = Herbivore("Newbie", species, 3, pos, self.all_sprites, self.map_rect, price=price)
                # self.herbivores.append(animal)

            # self.animals.append(animal)
            self.capital -= price
            return True

        elif item_type == 'chip':
            self.unchipped_animals_to_show = [a for a in self.animals if a not in self.chipped_animals]

            if not self.unchipped_animals_to_show:
                print("All animals already chipped!")
                return False

            self.chipping_ui_open = True
            print("Opened chipping UI")
            return True
        
        elif item_type in decor_image_map:
            image_name = decor_image_map[item_type]
            image_path = f"src/assets/graphics/environment/{image_name}.png"
            try:
                image = pygame.image.load(image_path).convert_alpha()
                # IMPROVED: Initialize placement mode with cursor-following behavior
                self.placement_mode = {
                    "type": item_type,
                    "image": image,
                    "price": price,
                    "target": None,  # Will be continuously updated to follow cursor
                    "locked": False  # Will be set to True after first click
                }
                self.placement_buttons = {}
                self.store_ui.menu_open = False  # Close store UI when entering placement mode
                return None
            except Exception as e:
                print(f"Error loading {item_type}: {e}")
                return False

        elif item_type == 'ranger':
            ranger = Ranger((1000, 1000), self.all_sprites, self.map_rect, self.collision_sprites)
            self.rangers.append(ranger)
            self.capital -= price
            return True

        return False
    
    def check_win_loss(self, dt):
        if self.game_result is not None:
            return

        # Loss: bankruptcy
        if self.capital <= 0:
            print("💀 Game Over: You went bankrupt.")
            self.end_game("loss")
            return

        # Loss: no animals
        if len(self.herbivores) + len(self.carnivores) + len(self.omnivores) == 0:
            print("💀 Game Over: All animals are extinct.")
            self.end_game("loss")
            return

        # Win check (monthly)
        if not hasattr(self, "month_timer"):
            self.month_timer = 0

        self.month_timer += dt
        if self.month_timer >= 10:
            self.month_timer = 0

            cond = self.win_conditions
            if (self.visitor_count >= cond['visitors'] and
                len(self.herbivores) >= cond['herbivores'] and
                len(self.carnivores) >= cond['carnivores'] and
                self.capital >= cond['capital']):
                self.win_streak_months += 1

                        # Deduct ranger salaries here
                for ranger in self.rangers:
                    self.capital -= 200  
                    print(f"Paid 200 to ranger: {ranger.name}")
                    if self.capital <= 0:
                        print("💀 Game Over:=> Can not pay salaries to rangers.")
                        self.end_game("loss")
                        return
                print(f"✅ Month passed with all thresholds met ({self.win_streak_months}/{cond['months']})")
                
            else:
                print("❌ Win condition failed this month. Streak reset.")
                self.win_streak_months = 0

            if self.win_streak_months >= cond['months']:
                print("🎉 Congratulations! You won the game!")
                self.end_game("win")

    def end_game(self, result):
        self.game_result = result  # 'win' or 'loss'
        self.result_time = pygame.time.get_ticks()
        self.all_sprites.manual_override = True  # Freeze camera follow
        self.paused = True  # Pause game updates
        
    def draw_game_result(self):
        if not self.game_result:
            return

        screen = self.display_surface
        width, height = 400, 200
        x = (SCREEN_WIDTH - width) // 2
        y = (SCREEN_HEIGHT - height) // 2
        box_rect = pygame.Rect(x, y, width, height)

        # THEME SWITCH
        if self.game_result == "win":
            # Green theme
            bg_color = (34, 60, 34)           # dark green
            border_color = (50, 200, 100)     # bright green
            title_color = (100, 255, 100)     # lime green
            btn_color = (0, 120, 60)          # button green
            btn_hover = (20, 160, 80)
        else:
            # Red theme
            bg_color = (46, 26, 26)
            border_color = (178, 34, 34)
            title_color = (255, 76, 76)
            btn_color = (139, 0, 0)
            btn_hover = (165, 42, 42)

        # Draw background
        pygame.draw.rect(screen, bg_color, box_rect, border_radius=20)
        pygame.draw.rect(screen, border_color, box_rect, 2, border_radius=20)

        # Title
        title_font = pygame.font.SysFont(None, 48)
        title_text = "You Win!" if self.game_result == "win" else "Game Over"
        title_surf = title_font.render(title_text, True, title_color)
        screen.blit(title_surf, (box_rect.centerx - title_surf.get_width() // 2, box_rect.y + 30))

        # Buttons
        btn_width, btn_height = 150, 50
        spacing = 30
        start_x = box_rect.centerx - btn_width - spacing // 2
        start_y = box_rect.bottom - btn_height - 30

        self.new_game_btn = pygame.Rect(start_x, start_y, btn_width, btn_height)
        self.quit_btn = pygame.Rect(start_x + btn_width + spacing, start_y, btn_width, btn_height)

        for btn, text in [(self.new_game_btn, "Start New Game"), (self.quit_btn, "Quit")]:
            color = btn_hover if btn.collidepoint(pygame.mouse.get_pos()) else btn_color
            pygame.draw.rect(screen, color, btn, border_radius=12)
            pygame.draw.rect(screen, border_color, btn, 2, border_radius=12)

            font = pygame.font.SysFont(None, 28)
            label = font.render(text, True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=btn.center))


class CameraGroup(pygame.sprite.Group):
    """SpriteGroup with camera offset / drawing order, drag-to-scroll, and auto-follow support."""

    def __init__(self, map_width: int, map_height: int):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
        self.map_width, self.map_height = map_width, map_height
        self.dragging = False
        self.last_mouse_pos = pygame.Vector2()
        self.manual_override = False  # Enables drag-scroll override

    def handle_mouse_drag(self, events, allow_dragging=True):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and allow_dragging:
                self.dragging = True
                self.manual_override = True
                self.last_mouse_pos = pygame.Vector2(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                current_mouse_pos = pygame.Vector2(event.pos)
                delta = self.last_mouse_pos - current_mouse_pos
                self.offset += delta
                self.last_mouse_pos = current_mouse_pos

                # Clamp to bounds
                self.offset.x = max(0, min(self.offset.x, self.map_width - SCREEN_WIDTH))
                self.offset.y = max(0, min(self.offset.y, self.map_height - SCREEN_HEIGHT))

    def reset_to_follow(self):
        """Disable drag override and re-center camera on ranger."""
        self.manual_override = False

    def custom_draw(self, ranger: pygame.sprite.Sprite):
        if not self.manual_override:
            self.offset.x = ranger.rect.centerx - SCREEN_WIDTH // 2
            self.offset.y = ranger.rect.centery - SCREEN_HEIGHT // 2
            self.offset.x = max(0, min(self.offset.x, self.map_width - SCREEN_WIDTH))
            self.offset.y = max(0, min(self.offset.y, self.map_height - SCREEN_HEIGHT))

        for sprite in sorted(self.sprites(), key=lambda s: getattr(s, 'z', s.rect.centery)):
            offset_rect = sprite.rect.copy()
            offset_rect.center -= self.offset
            self.display_surface.blit(sprite.image, offset_rect)

