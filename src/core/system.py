import pygame

from chr.tile import Tile
from exc.core import (
    EndOfExecution,
    RaisedNMI,
    ReturnFromInterrupt,
    IllegalAddressingMode
)
from core.bus import Bus
from core.mpu import MPU
from core.ppu import PPU
from header.ines import INESHeader

class System:

    def __init__(self):
        self._mpu = MPU()
        self._ppu = PPU()
        self._bus = Bus(self._mpu, self._ppu, self._ppu.ro_mmap, self._ppu.w_mmap)
        self._mpu.set_bus(self._bus)
        self._ppu.set_bus(self._bus)

    def start(self, trace: bool = False, trace_file = None):
        pygame.init()
        flags = pygame.SHOWN | pygame.RESIZABLE | pygame.SCALED
        screen = pygame.display.set_mode((256, 240), flags=flags)

        self._mpu.reset()
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise EndOfExecution()

                for _ in range(113):
                    try:
                        self._mpu.execute(trace, trace_file)
                    except ReturnFromInterrupt:
                        print("END INTERRUPT")
                        break

                for _ in range(50):
                    try:
                        self._ppu.render(screen)
                    except RaisedNMI:
                        break

        except EndOfExecution:
            self._mpu.dump()
            self._ppu.dump()
        except KeyboardInterrupt:
            self._mpu.dump()
            self._ppu.dump()
        except IllegalAddressingMode as e:
             self._mpu.dump()
             raise e
        except Exception as e:
            raise e
        finally:
            pygame.quit()

    def load(self, rom: str):
        with open(rom, 'rb') as rom_buffer:
            header = INESHeader(rom_buffer)
            header.read()
            header.dump()

            rom_buffer.seek(0)

            self._mpu.load(rom_buffer, header.prg_rom)
            self._ppu.load(rom_buffer, header.chr_rom)
