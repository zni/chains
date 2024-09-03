class INESHeader:
    def __init__(self, rom_file):
        self.rom_file = rom_file
        self.prg_rom = 0
        self.chr_rom = 0
        self.magic = ""

    def read(self):

        with open(self.rom_file, 'rb') as binary_file:
            self.magic = binary_file.read1(4)

            self.prg_rom = binary_file.read1(1)
            self.prg_rom = int.from_bytes(self.prg_rom, 'little') * (16 * 1024)

            self.chr_rom = binary_file.read1(1)
            self.chr_rom = int.from_bytes(self.chr_rom, 'little') * (8 * 1024)

        if self.magic != b"NES\x1a":
            raise RuntimeError("Not a NES ROM.")

    def dump(self):
        print(f"magic: {self.magic}")
        print(f"prg_rom: {self.prg_rom}")
        print(f"chr_rom: {self.chr_rom}")
