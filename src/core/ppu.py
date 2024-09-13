import pygame

from io import BufferedReader
from typing import Literal

from bitarray import bitarray
from bitarray.util import ba2int

from exc.core import RaisedNMI
from core.bus import Bus
from core.bus_member import BusMember
from memory.oam import OAM
from memory.ppu_ram import PPURAM


class PPUCtrl:
    def __init__(self):
        self._nmi = 0
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

    @property
    def nametable_select(self) -> int:
        return (self._nametable_select_hi << 1) | self._nametable_select_lo

    @property
    def nmi(self) -> bool:
        return self._nmi == 1

    def write(self, loc:int, ctrl:int):
        self._nmi = (ctrl & 0x80) >> 7
        self.ppu = (ctrl & 0x40) >> 6
        self.height = (ctrl & 0x20) >> 5
        self.bg_select = (ctrl & 0x10) >> 4
        self.sprite_select = (ctrl & 0x08) >> 3
        self.inc_mode = (ctrl & 0x04) >> 2
        self._nametable_select(ctrl)

    def read(self, loc:int) -> int:
        register = bitarray([
            self._nmi,
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
        self._sprite_enable = 0
        self._bg_enable = 0
        self.sprite_left_col = 0
        self.bg_left_col = 0
        self.greyscale = 0

    @property
    def sprite_enable(self) -> bool:
        return self._sprite_enable == 1

    @property
    def bg_enable(self) -> bool:
        return self._bg_enable == 1

    def write(self, loc:int, val:int):
        self.blue = (val & 0x80) >> 7
        self.green = (val & 0x40) >> 6
        self.red = (val & 0x20) >> 5
        self._sprite_enable = (val & 0x10) >> 4
        self._bg_enable = (val & 0x08) >> 3
        self.sprite_left_col = (val & 0x04) >> 2
        self.bg_left_col = (val & 0x02) >> 1
        self.greyscale = (val & 0x01)

    def read(self, loc:int) -> int:
        register = bitarray([
            self.blue,
            self.green,
            self.red,
            self._sprite_enable,
            self._bg_enable,
            self.sprite_left_col,
            self.bg_left_col,
            self.greyscale
        ])

        return ba2int(register)

class PPUStatus:
    def __init__(self):
        self._vblank = 0
        self.sprite_0_hit = 0
        self.sprite_overflow = 0

    @property
    def vblank(self):
        return self._vblank == 1

    def set_vblank(self, val:Literal[1,0]):
        self._vblank = val

    def write(self, loc, val):
        return None

    def read(self, loc) -> int:
        register = bitarray([
            self._vblank,
            self.sprite_0_hit,
            self.sprite_overflow,
            0,
            0,
            0,
            0,
            0
        ])

        int_register = ba2int(register, False)

        return int_register

class PPUScroll:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.latch = False
        self.data = 0

    def read(self, loc:int) -> int:
        return self.data

    def write(self, loc:int, data:int):
        self.data = data
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
        self.addr = 0
        self.data = 0
        self.latch_addr = False
        self.inc_mode = 0

        self._ram: PPURAM

    def set_ram(self, ram: PPURAM):
        self._ram = ram

    def read(self, loc:int):
        return self.data

    def write(self, loc:int, data:int):
        self.data = data
        if loc == PPUAddressData.ADDR and not self.latch_addr:
            self.addr = (data << 8) & 0xFF00
            self.latch_addr = True
        elif loc == PPUAddressData.ADDR and self.latch_addr:
            self.addr = (data & 0x00FF) | (self.addr & 0xFF00)
            self.latch_addr = False
        elif loc == PPUAddressData.DATA and not self.latch_addr:
            self.data = data
            self._ram.write(self.addr, self.data)
            if self.inc_mode == 0:
                inc = 1
            else:
                inc = 32
            self.addr = (self.addr + inc) & 0xFFFF

    def _addr_guardrails(self) -> int:
        if self.addr < 0x2000 or self.addr > 0x3EFF:
            return 0x2000
        else:
            return self.addr

class PPU(BusMember):
    def __init__(self):
        self._cycle_seconds = 0

        self._ppuctrl = PPUCtrl()
        self._ppumask = PPUMask()
        self._ppustatus = PPUStatus()
        self._oam = OAM()
        self._ppuscroll = PPUScroll()
        self._ppuaddr = PPUAddressData()
        self._ppudata = self._ppuaddr

        self.bg_x = 0
        self.bg_y = 0

        self.scanline = 0

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

        self._ram: PPURAM
        self._bus: Bus

    def set_ram(self, val: PPURAM):
        self._ram = val

    def set_bus(self, val: Bus):
        self._bus = val

    def read(self, loc):
        if loc == 0x2002:
            self._ppuaddr.latch_addr = False
            self._ppuscroll.latch = False

        return self.mmap[loc].read(loc)

    def write(self, loc, val):
        if loc in self.mmap:
            self.mmap[loc].write(loc, val)
        else:
            self.mmap[OAM.DMA]._oam_storage.write(loc, val)

        if loc == 0x2000:
            self._ppudata.inc_mode = self._ppuctrl.inc_mode

    def load(self, rom_buffer: BufferedReader, chr_size: int = 0):
        self._ram = PPURAM(size=0x3FFF)
        self._ppuaddr.set_ram(self._ram)
        mem_loc = 0
        chr_byte : bytes = rom_buffer.read1(1)
        while chr_byte and mem_loc < chr_size:
            chr_int = int.from_bytes(chr_byte, 'little')
            self._ram.write(mem_loc, chr_int)
            mem_loc += 1
            chr_byte = rom_buffer.read1(1)

    def nmi(self) -> None:
        if self._ppustatus.vblank and self._ppuctrl.nmi:
            self._bus.nmi()

    def render(self, screen: pygame.Surface):
        if self.scanline > 240 and self.scanline <= 260:
            self.scanline += 1
            self._ppustatus.set_vblank(1)
            self.nmi()
            raise RaisedNMI()
        elif self.scanline > 260:
            self.scanline = 0
            self.bg_x = 0
            self.bg_y = 0
            self._ppustatus.sprite_0_hit = 0
            self._ppustatus.set_vblank(0)

        if self._ppuctrl.nametable_select == 0:
            nametable_slice = self._ram.store[0x2000:0x23C0]
        elif self._ppuctrl.nametable_select == 1:
            print("nametable A")
            nametable_slice = self._ram.store[0x2400:0x27C0]
        elif self._ppuctrl.nametable_select == 2:
            print("nametable B")
            nametable_slice = self._ram.store[0x2800:0x2BC0]
        elif self._ppuctrl.nametable_select == 3:
            print("nametable B")
            nametable_slice = self._ram.store[0x2C00:0x2FC0]
        else:
            raise Exception("Invalid nametable.")

        nametable_tiles = []
        if self.bg_y < 240 and self._ppumask.bg_enable:
            offset_y = (self.bg_y // 8) * 32 if self.bg_y != 0 else 0
            nametable_row = nametable_slice[offset_y:offset_y + 32]
            for tile_num in nametable_row:
                tile = self._ram.read_chr(self._ppuctrl.bg_select, tile_num)
                tile.rect.x = self.bg_x
                tile.rect.y = self.bg_y
                nametable_tiles.append(tile)

                self.bg_x += 8
                if self.bg_x >= 255:
                    self.bg_x = 0
                    break
        self.bg_y += 8
        if nametable_tiles:
            nametable_group = pygame.sprite.Group(nametable_tiles)
            nametable_group.draw(screen)
            pygame.display.flip()

        if self._ppumask.sprite_enable:
            tiles = []
            for tile in range(64):
                chr = self._oam._oam_storage.read(tile)
                tile = self._ram.read_chr(self._ppuctrl.sprite_select, chr.tile_num)
                tile.rect.x = chr.x
                tile.rect.y = chr.y
                if chr.y == self.scanline:
                    tile.image = pygame.transform.flip(
                        tile.image,
                        chr.attributes.flip_horizontal,
                        chr.attributes.flip_vertical
                    )
                    # if chr.attributes.priority != 0:
                    tiles.append(tile)
                else:
                    continue

            if tiles:
                sprite_group = pygame.sprite.Group(tiles)
                sprite_group.draw(screen)
                pygame.display.flip()

        self.scanline += 1

    def dump(self):
        print(f"NMI: {self._ppuctrl.nmi}")
        print(f"VBLANK: {self._ppustatus._vblank}")
        # self._ram.dump()
        self._oam._oam_storage.dump()

    def dma_transfer(self, page: int, to: BusMember) -> None:
        return self._ram.dma_transfer(page, to)
