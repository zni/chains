import getopt
import pygame
import sys

from bitarray.util import int2ba
from chr.chr_obj import CHRObj

def read_chr(rom, page, tile) -> CHRObj:
        if page == 0:
            page = 0x0000
        else:
            page = 0x1000

        chr = CHRObj()
        page_slice = rom[page:page + 0x0FFF + 1]
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

page = 0
filename = None
(opts, _) = getopt.getopt(sys.argv[1:], 'f:p:')
for (opt, arg) in opts:
    if opt == '-f':
        filename = arg
    elif opt == '-p':
        page = int(arg)


if filename is None:
    print("usage: chr_rom_viewer -f <filename> -p (0|1)")
    sys.exit(1)

rom = []
with open(filename, 'rb') as f:
    f.seek(4)
    prg_size = f.read1(1)
    prg_size = int.from_bytes(prg_size, 'little') * (16 * 1024)
    print(prg_size)
    chr_size = f.read1(1)
    chr_size = int.from_bytes(chr_size, 'little') * (8 * 1024)
    f.seek(10 + prg_size)
    for n in range(chr_size):
        byte = f.read1(1)
        if not byte:
            break
        byte = int.from_bytes(byte, 'little')

        rom.append(byte)



pygame.init()
flags = pygame.SHOWN | pygame.RESIZABLE
screen = pygame.display.set_mode((256, 240), flags=flags)
clock = pygame.time.Clock()
try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise Exception()

        screen.fill("black")
        tile = 0
        tiles = []
        x = 0
        y = 0
        for y in range(0, 240, 8):
            for x in range(0, 256, 8):
                chr = read_chr(rom, page, tile)
                chr.rect.x = x
                chr.rect.y = y
                tiles.append(chr)
                tile += 1

        sprite_group = pygame.sprite.Group(tiles)
        sprite_group.draw(screen)
        pygame.display.flip()
        clock.tick(60)
except Exception:
    pass
finally:
    pygame.quit()