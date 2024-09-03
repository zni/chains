import bitarray
import bitarray.util

class FlagRegister:
    def __init__(self):
        self.sign = 0
        self.overflow = 0
        self.break_ = 0
        self.decimal = 0
        self.interrupt = 0
        self.zero = 0
        self.carry = 0

    def update_flags(self, val):
        self.sign = (0x80 & val) >> 7
        self.overflow = (0x40 & val) >> 6
        self.break_ = (0x10 & val) >> 4
        self.decimal = (0x08 & val) >> 3
        self.interrupt = (0x04 & val) >> 2
        self.zero = (0x02 & val) >> 1
        self.carry = 0x01 & val

    def update_sign(self, val):
        if val & 0x80:
            self.sign = 1
        else:
            self.sign = 0

    def update_zero(self, val):
        if val == 0:
            self.zero = 1
        else:
            self.zero = 0

    def update_carry(self, val, bit7=True):
        if bit7:
            if val & 0x80:
                self.carry = 1
            else:
                self.carry = 0
        else:
            if val & 0x01:
                self.carry = 1
            else:
                self.carry = 0

    def to_int(self):
        b = bitarray.bitarray([
            self.sign,
            self.overflow,
            0,
            self.break_,
            self.decimal,
            self.interrupt,
            self.zero,
            self.carry
        ])

        return bitarray.util.ba2int(b, signed=False)