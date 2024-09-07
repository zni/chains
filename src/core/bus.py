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
        if loc in self.ppu.mmap and loc != self.ppu._oam.DMA:
            self.ppu.write(loc, data)
        elif loc in self.ppu.mmap and loc == self.ppu._oam.DMA:
            self.ppu.write(loc, data)
            self.prg_ram.dma_transfer(
                self.ppu._oam.dma,
                self.ppu._oam._oam_storage
            )
        else:
            self.prg_ram.write(loc, data)