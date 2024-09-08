import getopt
import pygame
import sys

from chr.tile import Tile

page = 0
filename = None
(opts, _) = getopt.getopt(sys.argv[1:], 'f:p:')
for (opt, arg) in opts:
    if opt == '-f':
        filename = arg
    elif opt == '-p':
        page = arg


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

        x = 0
        y = 0

        if page == '0':
            r = range(0x0000, 0x0FFF, 16)
        else:
            r = range(0x1000, 0x1FFF, 16)

        for n in r:
            tile = Tile(rom[n if n != 0 else n+1:n+16])
            tile.draw(screen, x, y)
            x += 8
            if x >= 256:
                x = 0
                y += 8

            if y >= 240:
                break

        pygame.display.flip()
except Exception:
    pass
finally:
    pygame.quit()