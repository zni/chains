import pygame

from bitarray.util import int2ba

from memory.ram import RAM
from chr.chr_obj import CHRObj

class PPURAM(RAM):
    def __init__(self, size: int = 0x3FFF):
        super().__init__(size)
        self.surface = None

    def _mirror_nametables(self, loc:int) -> int:
        if loc >= 0x3000 and loc <= 0x3EFF:
            loc = loc - 0x1000
        return loc

    def read_chr(self, page:int, tile:int, plane:int) -> CHRObj:
        address = page << 12
        address |= (tile << 4)

        chr = CHRObj()
        plane0 = []
        plane0.append(self.store[address | plane])

        plane1 = []
        address |= 1 << 3
        plane1.append(self.store[address | plane])

        chr = CHRObj()
        pixel_array = pygame.PixelArray(chr.image)

        x = 0
        y = 0
        for (pixels0, pixels1) in zip(plane0, plane1):
            ba_pixels0 = int2ba(pixels0, 8, 'big', 0)
            ba_pixels1 = int2ba(pixels1, 8, 'big', 0)
            for (pixel0, pixel1) in zip(ba_pixels0, ba_pixels1):
                if pixel0 == 0 and pixel1 == 0:
                    pixel_array[x, y] = chr.COLOR0 # type: ignore
                elif pixel0 == 1 and pixel1 == 0:
                    pixel_array[x, y] = chr.COLOR1 # type: ignore
                elif pixel0 == 0 and pixel1 == 1:
                    pixel_array[x, y] = chr.COLOR2 # type: ignore
                elif pixel0 == 1 and pixel1 == 1:
                    pixel_array[x, y] = chr.COLOR3 # type: ignore
                x += 1
            x = 0
            y += 1
        return chr

    def read(self, loc: int) -> int:
        try:
            return self.store[loc]
        except IndexError as e:
            raise RuntimeError(f"Out of bounds read memory access {loc:04x} max {len(self.store):04x}") from e

    def write(self, loc:int, data:int):
        try:
            self.store[loc] = data
        except IndexError as e:
            raise RuntimeError(f"Out of bounds write memory access {loc:04x} max {len(self.store):04x}") from e