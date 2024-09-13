from typing import Dict, Callable

from core.bus_member import BusMember
from memory.oam import OAM

class Bus:
    def __init__(self, mpu: BusMember, ppu: BusMember, mmap: Dict[int, Callable]):
        self.mpu = mpu
        self.ppu = ppu
        self.mmap = mmap

    def read(self, loc:int) -> int:
        loc = self._mirror_map_ppu(loc)

        if loc in self.mmap:
            return self.ppu.read(loc)
        else:
            return self.mpu.read(loc)

    def _mirror_map_ppu(self, loc:int) -> int:
        if loc >= 0x2008 and loc <= 0x3FFF:
            return ((loc % 0x2000) % 8) | 0x2000
        else:
            return loc

    def write(self, loc:int, data:int) -> None:
        loc = self._mirror_map_ppu(loc)
        if loc in self.mmap and loc != OAM.DMA:
            self.ppu.write(loc, data)
        elif loc in self.mmap and loc == OAM.DMA:
            self.ppu.write(loc, data)
            self.mpu.dma_transfer(
                self.ppu.read(OAM.DMA),
                self.ppu
            )
        else:
            self.mpu.write(loc, data)

    def nmi(self) -> None:
        self.mpu.nmi()