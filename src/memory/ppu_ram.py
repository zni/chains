import pygame

from bitarray.util import int2ba

from memory.ram import RAM
from chr.chr_obj import CHRObj

class PPURAM(RAM):
    def __init__(self, size: int = 0x3FFF):
        super().__init__(size)
        self.surface = None

    def read_chr(self, page, tile) -> CHRObj:
        if page == 0:
            page = 0x0000
        else:
            page = 0x1000

        chr = CHRObj()
        page_slice = self.store[page:page + 0x0FFF + 1]
        # 0x0F was 16
        tile = page_slice[tile * 0x10:(tile * 0x10) + 0x0F + 1]
        plane0 = tile[0:8]
        plane1 = tile[8:]
        pixel_array = pygame.PixelArray(chr.image)

        x = 0
        y = 0
        for (pixels0, pixels1) in zip(plane0, plane1):
            ba_pixels0 = int2ba(pixels0, 8, 'little', 0)
            ba_pixels1 = int2ba(pixels1, 8, 'little', 0)
            # print(ba_pixels0, ba_pixels1)
            for (pixel0, pixel1) in zip(ba_pixels0, ba_pixels1):
                if pixel0 == 0 and pixel1 == 0:
                    pixel_array[x, y] = chr.COLOR0
                elif pixel0 == 1 and pixel1 == 0:
                    pixel_array[x, y] = chr.COLOR1
                elif pixel0 == 0 and pixel1 == 1:
                    pixel_array[x, y] = chr.COLOR2
                elif pixel0 == 1 and pixel1 == 1:
                    pixel_array[x, y] = chr.COLOR3
                x += 1
            x = 0
            y += 1
        chr.image = pygame.transform.flip(chr.image, True, False)
        return chr