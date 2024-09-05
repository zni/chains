import time

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
        self._mpu.reset()
        self._ppu._ppustatus.vblank = 1
        try:
            while True:
                pre = time.time()
                self._mpu.execute(trace=trace)
                post = time.time()
                elapsed = post - pre
                if self._ppu.trigger_nmi(elapsed):
                    self._mpu.nmi()
        except EndOfExecution:
            pass
        except KeyboardInterrupt:
            pass

    def reset(self):
        self._mpu.reset()

    def load(self, rom: str):
        with open(rom, 'rb') as rom_buffer:
            header = INESHeader(rom_buffer)
            header.read()

            rom_buffer.seek(0)

            self._mpu.load(rom_buffer, header.prg_rom)
            self._ppu.load(rom_buffer, header.chr_rom)