import pygame
from src.config.settings import *

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z = LAYERS['main']):
        super().__init__(groups)

        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        


class Water(Generic):
	def __init__(self, pos, frames, groups, z = LAYERS['water']):

		#animation setup
		self.is_water_source = True
		self.frames = frames
		self.frame_index = 0

		# sprite setup
		super().__init__(
				pos = pos, 
				surf = self.frames[self.frame_index], 
				groups = groups, 
				z = z)
            
		# self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)
		self.hitbox = self.rect.copy().inflate(20, 20)
        
            
	def animate(self,dt):
		self.frame_index += 4 * dt
		if self.frame_index >= len(self.frames):
			self.frame_index = 0
		self.image = self.frames[int(self.frame_index)]

	def update(self,dt):
		self.animate(dt)


class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        self.plant_type = 'flower'
        super().__init__(pos, surf, groups, z=LAYERS["main"])
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)
        self.z = self.rect.centery  # ✅ This makes them show up in world layer
		
        
class Tree(Generic):
    def __init__(self, pos, surf, groups, name):
        super().__init__(pos, surf, groups)
        self.plant_type = 'tree'
        self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)
        self.z = self.rect.centery  # ✅ Set z AFTER initializing


#class Bush(Generic):
 #   def __init__(self, pos, surf, groups):
  #      super().__init__(pos, surf, groups, z=LAYERS['trees'])
   #     self.hitbox = self.rect.copy().inflate(-10, -10)  # Bushes can have tighter collision
        
