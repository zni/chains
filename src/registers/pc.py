class ProgramCounter:
    def __init__(self, start=0):
        self.reg = start

    def pc_lo(self) -> int:
        return (0x00FF & self.reg)

    def pc_hi(self) -> int:
        return (0xFF00 & self.reg) >> 8

    def set_pc_lo(self, pc_lo: int):
        self.reg = (self.reg & 0xFF00) | (pc_lo & 0xFF)

    def set_pc_hi(self, pc_hi: int):
        self.reg = (pc_hi << 8) | (self.reg & 0xFF)
        self.reg &= 0xFFFF

    def advance_pc(self):
        self.reg = (self.reg + 1) & 0xFFFF

    def displace_pc(self, displacement):
        self.advance_pc()
        self.reg = (self.reg + displacement)
