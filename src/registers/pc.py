class ProgramCounter:
    def __init__(self, start=0):
        self.reg = start

    def pc_lo(self) -> int:
        return (0x00FF & self.reg)

    def pc_hi(self) -> int:
        return (0xFF00 & self.reg) >> 8

    def set_pc_lo(self, pc_lo):
        self.reg |= pc_lo

    def set_pc_hi(self, pc_hi):
        self.reg = (pc_hi << 8) | self.reg
        self.reg &= 0xFFFF

    def advance_pc(self):
        self.reg = (self.reg + 1) % 0xFFFF

    def displace_pc(self, displacement):
        self.reg = (self.reg + displacement) % 0xFFFF
