from io import BufferedReader

from bitarray import bitarray
from bitarray.util import ba2int

from memory.ram import RAM


class PPUCtrl:
    def __init__(self):
        self.nmi = 0
        self.ppu = 0
        self.height = 0
        self.bg_select = 0
        self.sprite_select = 0
        self.inc_mode = 0
        self._nametable_select_hi = 0
        self._nametable_select_lo = 0

    def _nametable_select(self, nt:int):
        nt &= 0x03
        self._nametable_select_hi = (nt & 0x02) >> 1
        self._nametable_select_lo = nt & 0x01

    def write(self, loc:int, ctrl:int):
        self.nmi = (ctrl & 0x80) >> 7
        self.ppu = (ctrl & 0x40) >> 6
        self.height = (ctrl & 0x20) >> 5
        self.bg_select = (ctrl & 0x10) >> 4
        self.sprite_select = (ctrl & 0x08) >> 3
        self.inc_mode = (ctrl & 0x04) >> 2
        self._nametable_select(ctrl)

    def read(self, loc:int) -> int:
        register = bitarray([
            self.nmi,
            self.ppu,
            self.height,
            self.bg_select,
            self.sprite_select,
            self.inc_mode,
            self._nametable_select_hi,
            self._nametable_select_lo
        ])

        return ba2int(register)

class PPUMask:
    def __init__(self):
        self.blue = 0
        self.green = 0
        self.red = 0
        self.sprite_enable = 0
        self.bg_enable = 0
        self.sprite_left_col = 0
        self.bg_left_col = 0
        self.greyscale = 0

    def write(self, loc:int, val:int):
        self.blue = (val & 0x80) >> 7
        self.green = (val & 0x40) >> 6
        self.red = (val & 0x20) >> 5
        self.sprite_enable = (val & 0x10) >> 4
        self.bg_enable = (val & 0x08) >> 3
        self.sprite_left_col = (val & 0x04) >> 2
        self.bg_left_col = (val & 0x02) >> 1
        self.greyscale = (val & 0x01)

    def read(self, loc:int) -> int:
        register = bitarray([
            self.blue,
            self.green,
            self.red,
            self.sprite_enable,
            self.bg_enable,
            self.sprite_left_col,
            self.bg_left_col,
            self.greyscale
        ])

        return ba2int(register)

class PPUStatus:
    def __init__(self):
        self.vblank = 1
        self.sprite_0_hit = 0
        self.sprite_overflow = 0

    def write(self, loc, val):
        return None

    def read(self, loc) -> int:
        register = bitarray([
            self.vblank,
            self.sprite_0_hit,
            self.sprite_overflow,
            0,
            0,
            0,
            0,
            0
        ])

        return ba2int(register, False)

class OAM:
    ADDR = 0x2003
    DATA = 0x2004
    DMA = 0x4014

    def __init__(self):
        self._oam_storage = RAM(256)
        self.latch = False

        self.addr = 0
        self.data = 0
        self.dma = 0

    def read(self, loc:int) -> int:
        if loc == OAM.ADDR:
            return 0

        if loc == OAM.DATA:
            return self._oam_storage.read(self.addr)

        if loc == OAM.DMA:
            return 0

    def write(self, loc:int, data:int):
        if loc == OAM.ADDR:
            input("OAMADDR break")
            self.addr = data
        elif loc == OAM.DATA:
            input("OAMDATA break")
            self._oam_storage.write(self.addr, data)
            self.addr += 1
        elif loc == OAM.DMA:
            input("OAMDMA break")
            self.dma = data

class PPUScroll:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.latch = False

    def read(self, loc:int) -> int:
        return 0

    def write(self, loc:int, data:int):
        if not self.latch:
            self.x = data
            self.latch = True
        else:
            self.y = data
            self.latch = False

class PPUAddressData:
    ADDR = 0x2006
    DATA = 0x2007

    def __init__(self):
        self._ram = None
        self.addr = 0
        self.data = 0
        self.latch_addr = False

    def set_ram(self, ram):
        self._ram = ram

    def read(self, loc:int):
        return 0

    def write(self, loc:int, data:int):
        if loc == PPUAddressData.ADDR and not self.latch_addr:
            self.addr = (data << 8) & 0xFF00
            self.latch_addr = True
        elif loc == PPUAddressData.ADDR and self.latch_addr:
            self.addr = (data & 0x00FF) | (self.addr & 0xFF00)
            self.latch_addr = False
        elif loc == PPUAddressData.DATA and not self.latch_addr:
            self.data = data
            print(f"PPUAddressData writing to {self.addr:04x}: {self.data:04x}")
            self._ram.write(self.addr, self.data)
            self.addr += 1

class PPU:

    NTSC = 0.0167

    def __init__(self):
        self._ram = None
        self._cycle_seconds = 0

        self._ppuctrl = PPUCtrl()
        self._ppumask = PPUMask()
        self._ppustatus = PPUStatus()
        self._oam = OAM()
        self._ppuscroll = PPUScroll()
        self._ppuaddr = PPUAddressData()
        self._ppudata = self._ppuaddr

        self.mmap = {
            0x2000: self._ppuctrl,
            0x2001: self._ppumask,
            0x2002: self._ppustatus,
            0x2003: self._oam,
            0x2004: self._oam,
            0x2005: self._ppuscroll,
            0x2006: self._ppuaddr,
            0x2007: self._ppudata,
            0x4014: self._oam
        }

    def read(self, loc):
        return self.mmap[loc].read(loc)

    def write(self, loc, val):
        self.mmap[loc].write(loc, val)

    def load(self, rom_buffer: BufferedReader, chr_size: int = 0):
        self._ram = RAM(size=0x3FFF)
        self._ppuaddr.set_ram(self._ram)

        mem_loc = 0
        chr_byte : bytes = rom_buffer.read1(1)
        while chr_byte and mem_loc < chr_size:
            chr_int = int.from_bytes(chr_byte, 'little')
            self._ram.write(mem_loc, chr_int)
            mem_loc += 1

    def trigger_nmi(self, cycle_seconds:float) -> bool:
        self._cycle_seconds += cycle_seconds
        if self._cycle_seconds >= PPU.NTSC and self._ppuctrl.nmi == 1:
            self._cycle_seconds = 0
            self._ppuctrl.nmi = 0
            self._ppustatus.vblank = 1
            return True
        else:
            return False