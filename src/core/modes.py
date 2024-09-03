import enum

class AddressingMode(enum.Enum):
    ABS = 0
    ABSIX = 1
    ABSX = 2
    ABSY = 3
    ABSI = 4
    ACC = 5
    IMM = 6
    IMPLIED = 7
    PCR = 8
    STACK = 9
    ZP = 10
    ZPIX = 11
    ZPX = 12
    ZPY = 13
    ZPI = 14
    ZPIY = 15
    REL = 16
    IND = 17
