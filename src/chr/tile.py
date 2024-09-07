from bitarray.util import int2ba
from pygame.pixelarray import PixelArray
from pygame.color import Color

class Tile:
    COLOR0 = Color(0, 0, 0, 0)
    COLOR1 = Color(100, 100, 100)
    COLOR2 = Color(150, 150, 150)
    COLOR3 = Color(200, 200, 200)

    def __init__(self, slice=[]):
        self.slice = slice

    def draw(self, surface, x_offset, y_offset):
        if not self.slice:
            return None

        plane0 = self.slice[0:7]
        plane1 = self.slice[8:16]
        pixel_array = PixelArray(surface)

        x = x_offset
        y = y_offset
        for (pixels0, pixels1) in zip(plane0, plane1):
            ba_pixels0 = int2ba(pixels0, 8, 'little', 0)
            ba_pixels1 = int2ba(pixels1, 8, 'little', 0)
            for (pixel0, pixel1) in zip(ba_pixels0, ba_pixels1):
                if pixel0 == 0 and pixel1 == 0:
                    pixel_array[x, y] = Tile.COLOR0
                elif pixel0 == 1 and pixel1 == 0:
                    pixel_array[x, y] = Tile.COLOR1
                elif pixel0 == 0 and pixel1 == 1:
                    pixel_array[x, y] = Tile.COLOR2
                elif pixel0 == 1 and pixel1 == 1:
                    pixel_array[x, y] = Tile.COLOR3
                x += 1
            x = x_offset
            y += 1

        return (x, y)
