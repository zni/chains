from typing import Literal

from memory.ram import RAM

class OAMAttributes:
    def __init__(self, data):
        self._flip_vert = (data & 0x80) >> 7
        self._flip_horz = (data & 0x40) >> 6
        self._priority  = (data & 0x20) >> 5
        self._palette   = (data & 0x03)

    @property
    def flip_vertical(self) -> bool:
        return self._flip_vert == 1

    @property
    def flip_horizontal(self) -> bool:
        return self._flip_horz == 1

    @property
    def priority(self) -> Literal[0,1]:
        return self._priority

    @property
    def palette(self) -> int:
        return self._palette

class OAMEntry:
    def __init__(self):
        self.y = 0
        self.tile_num = 0
        self.attributes : OAMAttributes
        self.x = 0

class OAMRAM(RAM):
    def __init__(self):
        super().__init__(255)

    def read(self, loc) -> OAMEntry:
        oam_entry = OAMEntry()
        oam_loc = loc * 4

        oam_entry.y = self.store[oam_loc]
        oam_entry.tile_num = self.store[oam_loc + 1]
        oam_entry.attributes = OAMAttributes(self.store[oam_loc + 2])
        oam_entry.x = self.store[oam_loc + 3]

        return oam_entry

    def write(self, loc, data):
        self.store[loc] = data

class OAM:
    ADDR = 0x2003
    DATA = 0x2004
    DMA = 0x4014

    def __init__(self):
        self._oam_storage = OAMRAM()
        self.latch = False

        self.addr = 0
        self.data = 0
        self.dma = 0

    def read(self, loc:int) -> int:
        if loc == OAM.ADDR:
            return 0

        if loc == OAM.DATA:
            return self._oam_storage.store[self.addr]

        if loc == OAM.DMA:
            return self.dma

        return 0

    def write(self, loc:int, data:int):
        self.latch = False
        if loc == OAM.ADDR:
            self.addr = data
        elif loc == OAM.DATA:
            self._oam_storage.write(self.addr, data)
            self.addr += 1
        elif loc == OAM.DMA:
            self.latch = True
            self.dma = data
