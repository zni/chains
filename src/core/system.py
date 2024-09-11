import time

import pygame

from chr.tile import Tile
from exc.core import EndOfExecution, ReturnFromInterrupt
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
        self.warmup = False

    def start(self, trace: bool = False, step: bool = False):
        pygame.init()
        flags = pygame.SHOWN | pygame.RESIZABLE #| pygame.SCALED
        screen = pygame.display.set_mode((256, 240), flags=flags)

        self._mpu.reset()
        self._ppu._ppustatus.vblank = 0
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise EndOfExecution()

                for _ in range(113):
                    try:
                        self._mpu.execute(trace=trace)
                    except ReturnFromInterrupt:
                        break

                self.nmi(trace)

                self._ppu.render(screen)

                self.nmi(trace)


        except EndOfExecution:
            pass
        except KeyboardInterrupt:
            self._mpu.dump()
            self._ppu.dump()
        except Exception as e:
            raise e
        finally:
            pygame.quit()

    def nmi(self, trace):
        if self._ppu.trigger_nmi():
            self._mpu.nmi()
            while True:
                try:
                    self._mpu.execute(trace=trace)
                except ReturnFromInterrupt:
                    pass
                finally:
                    break

    def reset(self):
        self._mpu.reset()

    def load(self, rom: str):
        with open(rom, 'rb') as rom_buffer:
            header = INESHeader(rom_buffer)
            header.read()
            header.dump()

            rom_buffer.seek(0)

            self._mpu.load(rom_buffer, header.prg_rom)
            self._ppu.load(rom_buffer, header.chr_rom)
