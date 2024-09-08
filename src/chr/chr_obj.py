import pygame
from pygame.color import Color

class CHRObj(pygame.sprite.Sprite):
    COLOR0 = Color(0, 0, 0, 0)
    COLOR1 = Color(100, 100, 100)
    COLOR2 = Color(150, 150, 150)
    COLOR3 = Color(200, 200, 200)

    def __init__(self):
        super().__init__()
        self.image = pygame.surface.Surface([8, 8])
        self.rect = self.image.get_rect()
