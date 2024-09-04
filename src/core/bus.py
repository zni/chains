from core.ppu import PPU
from memory.ram import RAM

class Bus:
    def __init__(self, prg_ram:RAM, ppu:PPU):
        self.prg_ram = prg_ram
        self.ppu = ppu

    def read(self, loc:int) -> int:
        if loc in self.ppu.mmap.keys():
            return self.ppu.read(loc)
        else:
            return self.prg_ram.read(loc)

    def write(self, loc:int, data:int):
        if loc in self.ppu.mmap.keys():
            self.ppu.write(loc, data)
        else:
            self.prg_ram.write(loc, data)