from io import BufferedReader

from exc.core import InvalidROM

class INESHeader:
    def __init__(self, rom_buffer: BufferedReader):
        self.rom_buffer = rom_buffer
        self.prg_rom = 0
        self.chr_rom = 0
        self.magic = b""
        self.vertical_nametable = False
        self.horizontal_nametable = False

    def read(self):
        buffer = self.rom_buffer.read1(16)
        self.magic = buffer[0:4]
        if self.magic != b"NES\x1a":
            raise InvalidROM()

        self.prg_rom = buffer[4] * (16 * 1024)
        self.chr_rom = buffer[5] * (8 * 1024)

        nametable = buffer[6]
        if nametable & 0x01:
            self.vertical_nametable = True
        else:
            self.horizontal_nametable = True

        ines2 = buffer[7]
        if ines2 & 0x0C == 0x08:
            ines2_format = True
        else:
            ines2_format = False



    def dump(self):
        print(f"magic: {self.magic}")
        print(f"prg_rom: {self.prg_rom}")
        print(f"chr_rom: {self.chr_rom}")
        print(f"horiz nametable: {self.horizontal_nametable}")
        print(f"vert nametable: {self.vertical_nametable}")
