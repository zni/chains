import time

import pygame

from chr.tile import Tile
from exc.core import EndOfExecution
from core.bus import Bus
from core.mpu import MPU
from core.ppu import PPU
from header.ines import INESHeader

class System:

    def __init__(self):
        self._mpu = MPU()
        self._ppu = PPU()
        self._bus = Bus(self._mpu._ram, self._ppu)
        self._mpu.bus = self._bus

    def start(self, trace: bool = False):
        pygame.init()
        # flags = pygame.SHOWN | pygame.RESIZABLE
        screen = pygame.display.set_mode((256, 240))
        clock = pygame.time.Clock()

        self._mpu.reset()
        self._ppu._ppustatus.vblank = 1
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise EndOfExecution()

                self._mpu.execute(trace=trace)

                if self._ppu.trigger_nmi(clock.tick(60) / 1000):
                    self._mpu.nmi()
                    self._ppu.render(screen)
                    pygame.display.flip()

        except EndOfExecution:
            pass
        except KeyboardInterrupt:
            self._mpu.dump()
        except Exception as e:
            raise e
        finally:
            pygame.quit()

    def reset(self):
        self._mpu.reset()

    def load(self, rom: str):
        with open(rom, 'rb') as rom_buffer:
            header = INESHeader(rom_buffer)
            header.read()

            rom_buffer.seek(0)

            self._mpu.load(rom_buffer, header.prg_rom)
            self._ppu.load(rom_buffer, header.chr_rom)

    def dump(self):
        for n in range(0, 0x3FFF, 16):
            print(self._ppu._ram.store[n : n+16])