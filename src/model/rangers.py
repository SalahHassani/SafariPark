# rangers.py
# ╔════════════════════════════════════════════════════════════════════╗
# ║  Ranger & ControllableRanger                                       ║
# ║  • AI rangers patrol → chase → attack Poachers.                    ║
# ║  • A ControllableRanger is the *exact* same class, but the flag    ║
# ║    `controllable=True` tells the shared update-logic to read       ║
# ║    keyboard input instead of running the AI branch.               ║
# ╚════════════════════════════════════════════════════════════════════╝

from __future__ import annotations
import pygame
from pygame.math import Vector2

from src.model.character import Character
from src.model.poacher   import Poacher
from src.utils.support   import import_folder
from src.config.settings import *

# ───────────────────────────── CONSTANTS ──────────────────────────────
RANGER_DETECTION_RADIUS = 180          # gun range & chase radius
RANGER_SPEAR_RANGE      = 50           # spear attack range
RANGER_CHASE_SPEED      = 60
RANGER_NORMAL_SPEED     = 40

GUN_DAMAGE              = 20           # HP taken from Poacher per gun hit
SPEAR_DAMAGE            = 10           # HP taken from Poacher per spear hit
# ───────────────────────────────────────────────────────────────────────



class Ranger(Character):
    WEAPON_TYPES         = ['normal', 'gun', 'spear']
    current_weapon_index = 0        
    COUNT = 1    

    # ─────────────────────────── INIT ────────────────────────────
    def __init__(
        self,
        pos: tuple[int, int],
        group: pygame.sprite.Group,
        map_rect: pygame.Rect,
        collision_sprites: pygame.sprite.Group,
        controllable: bool = False
    ) -> None:

        super().__init__(pos, group, map_rect)
        
        self.name = f"Ranger_{Ranger.COUNT}" 
        Ranger.COUNT += 1                     

        # ── gameplay state ───────────────────────────────────────
        self.collision_sprites = collision_sprites
        self.controllable      = controllable
        self.weapon            = self.WEAPON_TYPES[self.current_weapon_index]
        self.shooting          = False
        self.spear_attacking   = False
        self.status            = 'idle_normal_down'
        self._damage_done_this_anim = False   # “one hit per anim” flag

        # ── sprite visuals ───────────────────────────────────────
        self._import_assets()
        self.image  = self.animations[self.status][self.frame_index]
        self.rect   = self.image.get_rect(center=pos)
        self.z      = LAYERS['main']
        self.hitbox = self.rect.copy().inflate(-10, -10)

    # ──────────────────────── ASSET LOADING ───────────────────────
    
    
    def _import_assets(self) -> None:
        self.animations: dict[str, list[pygame.Surface]] = {}
        dirs = [
            'up', 'down', 'left', 'right',
            'left_down', 'left_up', 'right_down', 'right_up'
        ]
        for weapon in self.WEAPON_TYPES:
            for d in dirs:
                suf = f'{d}_down' if d in ('left', 'right') else d
                base = f'src/assets/characters/ranger'
                self.animations[f'idle_{weapon}_{d}'] = import_folder(f'{base}/idle/{weapon}/{suf}')
                self.animations[f'walk_{weapon}_{d}'] = import_folder(f'{base}/walk/{weapon}/{suf}')
        for atk in ('shooting', 'spear_attack'):
            for d in dirs:
                path = f'src/assets/characters/ranger/attack/{atk}/{d}'
                self.animations[f'{atk}_{d}'] = import_folder(path)

    # ───────────────────── DIRECTION LABEL (for anim key) ────────────
    def _dir_label(self) -> str:
        dx, dy = int(round(self.last_direction.x)), int(round(self.last_direction.y))
        if   dx == -1 and dy == 0: return 'left'
        elif dx ==  1 and dy == 0: return 'right'
        elif dy == -1:
            return 'left_up'   if dx == -1 else 'right_up'   if dx == 1 else 'up'
        elif dy ==  1:
            return 'left_down' if dx == -1 else 'right_down' if dx == 1 else 'down'
        return 'down'




    # ─────────────────────── STATE & ANIMATION ───────────────────────
    def _set_status(self) -> None:
        label = self._dir_label()
        if   self.spear_attacking: self.status = f'spear_attack_{label}'
        elif self.shooting       : self.status = f'shooting_{label}'
        elif self.direction.length_squared() > 0:
            self.last_direction = self.direction.copy()
            self.status = f'walk_{self.weapon}_{label}'
        else:
            self.status = f'idle_{self.weapon}_{label}'



    def _animate(self, dt: float) -> None:
        frames = self.animations[self.status]
        self.frame_index += 8 * dt
        if self.frame_index >= len(frames):
            self.frame_index = 0
            if 'spear_attack' in self.status or 'shooting' in self.status:
                # attack animation finished → reset flags
                self.spear_attacking = self.shooting = False
                self._damage_done_this_anim = False
        self.image = frames[int(self.frame_index)]






    # ────────────────────── PLAYER INPUT HANDLER ─────────────────────
    def _handle_player_input(self, dt: float) -> None:
        keys  = pygame.key.get_pressed()
        ctrl  = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # cycle weapon with Z / X
        if ctrl and keys[pygame.K_z]:
            Ranger.current_weapon_index = (Ranger.current_weapon_index - 1) % len(self.WEAPON_TYPES)
            pygame.time.wait(150)
        if ctrl and keys[pygame.K_x]:
            Ranger.current_weapon_index = (Ranger.current_weapon_index + 1) % len(self.WEAPON_TYPES)
            pygame.time.wait(150)

        # movement
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN]  - keys[pygame.K_UP]
        self.direction.xy = dx, dy
        if dx != 0 or dy != 0:
            self.groups()[0].reset_to_follow()
        if dx and dy:
            self.direction /= 1.4142

        # attack on Ctrl + A while standing
        if self.direction.length_squared() == 0 and ctrl and keys[pygame.K_a]:
            if self.weapon == 'gun':
                self._trigger_shoot()
            elif self.weapon == 'spear':
                self._trigger_spear()

    # ─────────────────────── WEAPON ACTIONS ─────────────────────────
    def _sync_weapon_choice(self) -> None:
        self.weapon = self.WEAPON_TYPES[self.current_weapon_index]

    def _trigger_shoot(self) -> None:
        if not self.shooting and self.weapon == 'gun':
            self.shooting = True
            self.frame_index = 0
            self._damage_done_this_anim = False

    def _trigger_spear(self) -> None:
        if not self.spear_attacking and self.weapon == 'spear':
            self.spear_attacking = True
            self.frame_index = 0
            self._damage_done_this_anim = False

    # ───────────────────── DAMAGE APPLICATION ──────────────────────
    def _deal_damage(self, poachers: list[Poacher]) -> None:
        if self._damage_done_this_anim:
            return

        if self.shooting:
            for p in poachers:
                if p.health > 0 and self.pos.distance_to(p.pos) < RANGER_DETECTION_RADIUS:
                    p.take_damage(GUN_DAMAGE)
            self._damage_done_this_anim = True

        elif self.spear_attacking:
            for p in poachers:
                if p.health > 0 and self.pos.distance_to(p.pos) < RANGER_SPEAR_RANGE:
                    p.take_damage(SPEAR_DAMAGE)
            self._damage_done_this_anim = True

    # ──────────────────────── AI HELPERS ───────────────────────────
    def _vector_to_nearest(self, poachers: list[Poacher]) -> Vector2 | None:
        nearest, best_d2 = None, RANGER_DETECTION_RADIUS ** 2
        for p in poachers:
            if p.health <= 0:
                continue
            d2 = self.pos.distance_squared_to(p.pos)
            if d2 < best_d2:
                nearest, best_d2 = p, d2
        if nearest:
            v = nearest.pos - self.pos
            return v.normalize() if v.length_squared() else None
        return None

    def _spear_reachable(self, poachers: list[Poacher]) -> bool:
        return any(p.health > 0 and self.pos.distance_to(p.pos) < RANGER_SPEAR_RANGE
                   for p in poachers)

    # ───────────────────────── MOVEMENT w/ COLLISION ───────────────

    # def collision(self, direction):
    #     for sprite in self.collision_sprites.sprites():
    #         if sprite.hitbox.colliderect(self.hitbox):
    #             if direction == 'horizontal':
    #                 if self.direction.x > 0:  # moving right
    #                     self.hitbox.right = sprite.hitbox.left
    #                 elif self.direction.x < 0:  # moving left
    #                     self.hitbox.left = sprite.hitbox.right
    #                 self.pos.x = self.hitbox.centerx
    #                 self.rect.centerx = self.hitbox.centerx

    #             elif direction == 'vertical':
    #                 if self.direction.y > 0:  # moving down
    #                     self.hitbox.bottom = sprite.hitbox.top
    #                 elif self.direction.y < 0:  # moving up
    #                     self.hitbox.top = sprite.hitbox.bottom
    #                 self.pos.y = self.hitbox.centery
    #                 self.rect.centery = self.hitbox.centery


    def _move_and_resolve(self, dt: float) -> None:
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()

        # horizontal
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self._resolve_collision('horizontal')
        self.rect.centerx = self.hitbox.centerx

        # vertical
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self._resolve_collision('vertical')
        self.rect.centery = self.hitbox.centery

    def _resolve_collision(self, axis: str) -> None:
        for tile in self.collision_sprites.sprites():
            if tile.hitbox.colliderect(self.hitbox):
                if axis == 'horizontal':
                    if self.direction.x > 0:  self.hitbox.right  = tile.hitbox.left
                    if self.direction.x < 0:  self.hitbox.left   = tile.hitbox.right
                    self.pos.x = self.hitbox.centerx
                else:
                    if self.direction.y > 0:  self.hitbox.bottom = tile.hitbox.top
                    if self.direction.y < 0:  self.hitbox.top    = tile.hitbox.bottom
                    self.pos.y = self.hitbox.centery

    # ────────────────────────── UPDATE LOOP ───────────────────────
    def update(self, dt: float, poachers: list[Poacher] | None = None) -> None:
        self._sync_weapon_choice()

        # 1) player vs. AI inputs
        if self.controllable:
            self._handle_player_input(dt)
        else:
            if poachers:
                vec = self._vector_to_nearest(poachers)
                if vec:
                    # chase
                    self.direction = vec
                    self.speed     = RANGER_CHASE_SPEED
                    # auto-attack
                    if self.weapon == 'spear' and self._spear_reachable(poachers):
                        self._trigger_spear()
                    elif self.weapon == 'gun' and not self.shooting:
                        self._trigger_shoot()
                else:
                    self.speed = RANGER_NORMAL_SPEED
                    self.patrol_input(dt)      # no target → patrol
            else:
                self.speed = RANGER_NORMAL_SPEED
                self.patrol_input(dt)

        # 2) apply damage (once per anim cycle)
        if poachers:
            self._deal_damage(poachers)

        # 3) housekeeping
        self._set_status()
        self._move_and_resolve(dt)
        self._animate(dt)

# ╔═════════════════════════════════════════════════════════════════╗
# ║                PLAYER-CONTROLLED SUBCLASS                      ║
# ╚═════════════════════════════════════════════════════════════════╝
class ControllableRanger(Ranger):
    def __init__(self, pos, group, map_rect, collision_sprites):
        super().__init__(pos, group, map_rect, collision_sprites, controllable=True)
        self.z = self.rect.centery




# class ControllableRanger(Ranger):
#     def __init__(self, pos, groups, map_rect, collision_sprites):
#         super().__init__(pos, groups, map_rect, collision_sprites)
#         self.controllable = True  # This line makes sure .input() is called...
#         self.z = self.rect.centery

#     def input(self, dt):
#         keys = pygame.key.get_pressed()
#         ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

#         if ctrl and keys[pygame.K_z]:
#             self.cycle_weapon_style()
#             pygame.time.wait(150)
#         if ctrl and keys[pygame.K_x]:
#             Ranger.current_weapon_index = (Ranger.current_weapon_index + 1) % len(Ranger.WEAPON_TYPES)
#             pygame.time.wait(150)

#         if not self.shooting and not self.spear_attacking:
#             dx, dy = 0, 0
#             if keys[pygame.K_LEFT]: dx = -1
#             elif keys[pygame.K_RIGHT]: dx = 1
#             if keys[pygame.K_UP]: dy = -1
#             elif keys[pygame.K_DOWN]: dy = 1

#             self.direction.xy = dx, dy
#             if dx != 0 and dy != 0:
#                 self.direction /= 1.4142

#             if self.direction.magnitude() == 0:
#                 if ctrl and keys[pygame.K_a]:
#                     if self.weapon == 'gun':
#                         self.trigger_shoot()
#                     elif self.weapon == 'spear':
#                         self.trigger_spear_attack()
