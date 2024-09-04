from io import BufferedReader

from exc.core import InvalidROM

class INESHeader:
    def __init__(self, rom_buffer: BufferedReader):
        self.rom_buffer = rom_buffer
        self.prg_rom = 0
        self.chr_rom = 0
        self.magic = b""

    def read(self):
        self.magic = self.rom_buffer.read1(4)
        if self.magic != b"NES\x1a":
            raise InvalidROM()

        self.prg_rom = self.rom_buffer.read1(1)
        self.prg_rom = int.from_bytes(self.prg_rom, 'little') * (16 * 1024)

        self.chr_rom = self.rom_buffer.read1(1)
        self.chr_rom = int.from_bytes(self.chr_rom, 'little') * (8 * 1024)

    def dump(self):
        print(f"magic: {self.magic}")
        print(f"prg_rom: {self.prg_rom}")
        print(f"chr_rom: {self.chr_rom}")
