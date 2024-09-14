import pygame

from io import BufferedReader
from typing import Literal, List

from bitarray import bitarray
from bitarray.util import ba2int

from exc.core import RaisedNMI
from core.bus import Bus
from core.bus_member import BusMember
from core.memory_mapped_io import MemoryMappedIO
from memory.oam import OAM
from memory.ppu_ram import PPURAM, CHRObj
from utils.memdump import memdump


class PPUCtrl(MemoryMappedIO):
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

    def write(self, loc:int, data:int):
        print("PPUCtrl:", f"{data:08b}")
        self._nmi = (data & 0x80) >> 7
        self.ppu = (data & 0x40) >> 6
        self.height = (data & 0x20) >> 5
        self.bg_select = (data & 0x10) >> 4
        self.sprite_select = (data & 0x08) >> 3
        self.inc_mode = (data & 0x04) >> 2
        self._nametable_select(data)

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

class PPUMask(MemoryMappedIO):
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

    def rendering_enabled(self) -> bool:
        return self.sprite_enable and self.bg_enable

    def write(self, loc:int, data:int):
        self.blue = (data & 0x80) >> 7
        self.green = (data & 0x40) >> 6
        self.red = (data & 0x20) >> 5
        self._sprite_enable = (data & 0x10) >> 4
        self._bg_enable = (data & 0x08) >> 3
        self.sprite_left_col = (data & 0x04) >> 2
        self.bg_left_col = (data & 0x02) >> 1
        self.greyscale = (data & 0x01)

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

class PPUStatus(MemoryMappedIO):
    def __init__(self, ppu:"PPU"):
        self._vblank = 0
        self.sprite_0_hit = 0
        self.sprite_overflow = 0
        self.ppu = ppu

    @property
    def vblank(self):
        return self._vblank == 1

    def set_vblank(self, val:Literal[1,0]):
        self._vblank = val

    def write(self, loc, val):
        return None

    def read(self, loc) -> int:
        self.ppu.w = False

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
        if self.vblank:
            self.set_vblank(0)

        return int_register

class PPUScroll(MemoryMappedIO):
    def __init__(self, ppu:"PPU"):
        self.ppu = ppu

    def read(self, loc:int) -> int:
        return 0

    def write(self, loc:int, data:int):
        self.data = data
        # Set X
        if not self.ppu.w:
            self.ppu.t = 0
            self.ppu.t = data & 0xF8
            self.ppu.x = data & 0x07
            self.ppu.w = True
        # Set Y
        else:
            coarse_y = (data & 0xF8) << 5
            fine_y = (data & 0x07) << 12
            self.ppu.t |= fine_y | coarse_y
            self.ppu.w = False

class PPUAddressData(MemoryMappedIO):
    ADDR = 0x2006
    DATA = 0x2007

    def __init__(self, ppu:"PPU"):
        self.data = 0
        self.data_buffer = 0
        self.latch_addr = False
        self.ppu = ppu

        self._ram: PPURAM

    def set_ram(self, ram: PPURAM):
        self._ram = ram

    def read(self, loc:int) -> int:
        if loc != PPUAddressData.DATA:
            return 0

        if self.ppu.v >= 0x3F00:
            self.data_buffer = self._ram.read(self.ppu.v)
            data = self._ram.read(self.ppu.v)
        else:
            data = self.data_buffer
            self.data_buffer = self._ram.read(self.ppu.v)

        if (not self.ppu._ppumask.bg_enable and not self.ppu._ppumask.sprite_enable) or (240 < self.ppu.scanline <= 260):
            self.increment_address()
        else:
            self.increment_coarse_address()
        return data

    def write(self, loc:int, data:int):
        self.data = data
        if loc == PPUAddressData.ADDR and not self.ppu.w:
            self.ppu.t |= (data << 8) & 0x3F00
            self.ppu.w = True
        elif loc == PPUAddressData.ADDR and self.ppu.w:
            self.ppu.t = (data & 0x00FF) | (self.ppu.t & 0x3F00)
            self.ppu.v = self.ppu.t
            self.ppu.w = False
        elif loc == PPUAddressData.DATA:
            # print("WRITE PPUDATA")
            self._ram.write(self.ppu.v, self.data)
            self.increment_address()

    def increment_address(self) -> None:
        if self.ppu._ppuctrl.inc_mode == 0:
            self.ppu.v += 1
            self.ppu.v &= 0x3FFF
        else:
            self.ppu.v += 32
            self.ppu.v &= 0x3FFF

    def increment_coarse_address(self) -> None:
        self.coarse_x_inc()
        self.coarse_y_inc()

    def coarse_y_inc(self):
        if ((self.ppu.v & 0x7000) != 0x7000):
            self.ppu.v += 0x1000
        else:
            self.ppu.v &= ~0x7000
            y = (self.ppu.v & 0x03E0) >> 5
            if y == 29:
                self.ppu.v = 0
                self.ppu.v ^= 0x0800
            elif y == 31:
                y = 0
            else:
                y += 1
            self.ppu.v = (self.ppu.v & ~0x03E0) | (y << 5)

    def coarse_x_inc(self):
        if ((self.ppu.v & 0x001F) == 31):
            self.ppu.v &= ~0x001F
            self.ppu.v ^= 0x0400
        else:
            self.ppu.v += 1


class PPU(BusMember):
    def __init__(self):
        self._cycle_seconds = 0

        self._ppuctrl = PPUCtrl()
        self._ppumask = PPUMask()
        self._ppustatus = PPUStatus(self)
        self._oam = OAM()
        self._ppuscroll = PPUScroll(self)
        self._ppuaddr = PPUAddressData(self)
        self._ppudata = self._ppuaddr

        self.v = 0
        self.t = 0
        self.x = 0
        self.w = False

        self.scanline = 0

        self.nmi_triggered = False

        # Read-only memory map
        self.ro_mmap = {
            0x2002: self._ppustatus,
            0x2004: self._oam,
            # 0x2007: self._ppudata,
        }

        # Write-only memory map
        self.w_mmap = {
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
        return self.ro_mmap[loc].read(loc)

    def write(self, loc, val):
        if loc in self.w_mmap:
            self.w_mmap[loc].write(loc, val)
        else:
            self.w_mmap[OAM.DMA]._oam_storage.write(loc, val)

        if loc == 0x2000:
            print("NMI:", self._ppuctrl.nmi)

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
        if self._ppustatus.vblank and self._ppuctrl.nmi and not self.nmi_triggered:
            self.nmi_triggered = True
            self._bus.nmi()
            raise RaisedNMI()

    def dma(self):
        return self._oam.dma

    def render(self, screen: pygame.Surface):
        if 240 < self.scanline <= 260:
            self.scanline += 1
            self._ppustatus.set_vblank(1)
            self.nmi()
        elif self.scanline > 260:
            if self._ppumask.rendering_enabled():
                self.v = self.t
                pygame.display.flip()

            self.scanline = 0
            self.nmi_triggered = False
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



        if self.scanline < 240 and self._ppumask.bg_enable:
            offset_y = (self.scanline // 8) * 32 if self.scanline != 0 else 0
            nametable_row = nametable_slice[offset_y:offset_y + 32]
            x_pos = 0
            nametable_tiles: List[CHRObj] = []
            for tile_num in nametable_row:
                tile = self._ram.read_chr(self._ppuctrl.bg_select, tile_num, (self.scanline % 8))
                tile.rect.x = x_pos
                tile.rect.y = self.scanline

                nametable_tiles.append(tile)
                x_pos += 8
                self._ppudata.coarse_x_inc()
                if x_pos >= 255:
                    self._ppudata.coarse_y_inc()
                    break

            for nametable_tile in nametable_tiles:
                screen.blit(nametable_tile.image, nametable_tile.rect)

        if self.scanline < 240 and self._ppumask.sprite_enable:
            tiles: List[CHRObj] = []
            for tile in range(64):
                chr = self._oam._oam_storage.read(tile)
                tile = self._ram.read_chr(self._ppuctrl.sprite_select, chr.tile_num, (self.scanline % 8))
                tile.rect.x = chr.x
                tile.rect.y = chr.y
                if chr.y == self.scanline:
                    tile.image = pygame.transform.flip(
                        tile.image,
                        chr.attributes.flip_horizontal,
                        chr.attributes.flip_vertical
                    )
                    tiles.append(tile)
                else:
                    continue

            for tile in tiles:
                screen.blit(tile.image, tile.rect)

        self.scanline += 1

    def dump(self):
        print(f"NMI: {self._ppuctrl.nmi}")
        print(f"VBLANK: {self._ppustatus._vblank}")
        self._ram.dump()
        self._oam._oam_storage.dump()

    def dma_transfer(self, page: int, to: BusMember) -> None:
        return self._ram.dma_transfer(page, to)
