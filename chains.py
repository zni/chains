import enum
import getopt
import sys
import time

import bitarray
import bitarray.util

class IllegalAddressingMode(Exception):
    pass

class Mode(enum.Enum):
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

class RAM:
    def __init__(self, size=0xFFFF):
        self.store = []
        for _ in range(size):
            self.store.append(0)

    def read(self, loc):
        try:
            return self.store[loc]
        except IndexError as e:
            raise RuntimeError("Out of bounds memory access") from e

    def write(self, loc, data):
        try:
            self.store[loc] = data
        except IndexError as e:
            raise RuntimeError("Out of bounds memory access") from e

class Stack:
    def __init__(self, ram: RAM, origin:int=256):
        self._ram = ram
        self.sp = origin

    def push(self, data: int):
        self._ram.write(self.sp, data)
        self.sp += 1

    def pop(self) -> int:
        self.sp -= 1
        return self._ram.read(self.sp)

class MPU:

    CYCLE = 0.0006

    def __init__(self):
        self._pc = ProgramCounter()
        self._a = 0
        self._x = 0
        self._y = 0
        self._flags = FlagRegister()
        self._ram = RAM()
        self._stack = Stack(self._ram)

        # https://en.wikipedia.org/wiki/MOS_Technology_6502#Instruction_table
        self._lookup_table = [
            #0
            [
                (self._brk, Mode.IMPLIED),
                (self._ora, Mode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, Mode.ZP),
                (self._asl, Mode.ZP),
                (None, None),
                (self._php, Mode.IMPLIED),
                (self._ora, Mode.IMM),
                (self._asl, Mode.ACC),
                (None, None),
                (None, None),
                (self._ora, Mode.ABS),
                (self._asl, Mode.ABS),
                (None, None)
            ],
            #1
            [
                (self._bpl, Mode.REL),
                (self._ora, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, Mode.ZPX),
                (self._asl, Mode.ZPX),
                (self._clc, Mode.IMPLIED),
                (self._ora, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, Mode.ABSX),
                (self._asl, Mode.ABSX),
                (None, None)
            ],
            #2
            [
                (self._jsr, Mode.ABS),
                (self._and, Mode.ABSIX),
                (None, None),
                (None, None),
                (self._bit, Mode.ZP),
                (self._and, Mode.ZP),
                (self._rol, Mode.ZP),
                (None, None),
                (self._plp, Mode.IMPLIED),
                (self._and, Mode.IMM),
                (self._rol, Mode.ACC),
                (None, None),
                (self._bit, Mode.ABS),
                (self._and, Mode.ABS),
                (self._rol, Mode.ABS),
                (None, None)
            ],
            #3
            [
                (self._bmi, Mode.REL),
                (self._and, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._and, Mode.ZPX),
                (self._rol, Mode.ZPX),
                (None, None),
                (self._sec, Mode.IMPLIED),
                (self._and, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._and, Mode.ABSX),
                (self._rol, Mode.ABSX),
                (None, None)
            ],
            #4
            [
                (self._rti, Mode.IMPLIED),
                (self._eor, Mode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, Mode.ZP),
                (self._lsr, Mode.ZP),
                (None, None),
                (self._pha, Mode.IMPLIED),
                (self._eor, Mode.IMM),
                (self._lsr, Mode.ACC),
                (None, None),
                (self._jmp, Mode.ABS),
                (self._eor, Mode.ABS),
                (self._lsr, Mode.ABS),
                (None, None)
            ],
            #5
            [
                (self._bvc, Mode.REL),
                (self._eor, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, Mode.ZPX),
                (self._lsr, Mode.ZPX),
                (None, None),
                (self._cli, Mode.IMPLIED),
                (self._eor, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, Mode.ABSX),
                (self._lsr, Mode.ABSX)
            ],
            #6
            [
                (self._rts, Mode.IMPLIED),
                (self._adc, Mode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, Mode.ZP),
                (self._ror, Mode.ZP),
                (None, None),
                (self._pla, Mode.IMPLIED),
                (self._adc, Mode.IMM),
                (self._ror, Mode.ACC),
                (None, None),
                (self._jmp, Mode.IND),
                (self._adc, Mode.ABS),
                (self._ror, Mode.ABS),
                (None, None),
            ],
            #7
            [
                (self._bvs, Mode.REL),
                (self._adc, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, Mode.ZPX),
                (self._ror, Mode.ZPX),
                (None, None),
                (self._sei, Mode.IMPLIED),
                (self._adc, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, Mode.ABSX),
                (self._ror, Mode.ABSX),
                (None, None)
            ],
            #8
            [
                (None, None),
                (self._sta, Mode.ZPIX),
                (None, None),
                (None, None),
                (self._sty, Mode.ZP),
                (self._sta, Mode.ZP),
                (self._stx, Mode.ZP),
                (None, None),
                (self._dey, Mode.IMPLIED),
                (None, None),
                (self._txa, Mode.IMPLIED),
                (None, None),
                (self._sty, Mode.ABS),
                (self._sta, Mode.ABS),
                (self._stx, Mode.ABS),
                (None, None)
            ],
            #9
            [
                (self._bcc, Mode.REL),
                (self._sta, Mode.ZPIY),
                (None, None),
                (None, None),
                (self._sty, Mode.ZPX),
                (self._sta, Mode.ZPX),
                (self._stx, Mode.ZPY),
                (None, None),
                (self._tya, Mode.IMPLIED),
                (self._sta, Mode.ABSY),
                (self._txs, Mode.IMPLIED),
                (None, None),
                (None, None),
                (self._sta, Mode.ABSX),
                (None, None),
                (None, None)
            ],
            #A
            [
                (self._ldy, Mode.IMM),
                (self._lda, Mode.ZPIX),
                (self._ldx, Mode.IMM),
                (None, None),
                (self._ldy, Mode.ZP),
                (self._lda, Mode.ZP),
                (self._ldx, Mode.ZP),
                (None, None),
                (self._tay, Mode.IMPLIED),
                (self._lda, Mode.IMM),
                (self._tax, Mode.IMPLIED),
                (None, None),
                (self._ldy, Mode.ABS),
                (self._lda, Mode.ABS),
                (self._ldx, Mode.ABS),
                (None, None)
            ],
            #B
            [
                (self._bcs, Mode.REL),
                (self._lda, Mode.ZPIY),
                (None, None),
                (None, None),
                (self._ldy, Mode.ZPX),
                (self._lda, Mode.ZPX),
                (self._ldx, Mode.ZPY),
                (None, None),
                (self._clv, Mode.IMPLIED),
                (self._lda, Mode.ABSY),
                (self._tsx, Mode.IMPLIED),
                (None, None),
                (self._ldy, Mode.ABSX),
                (self._lda, Mode.ABSX),
                (self._ldx, Mode.ABSY),
                (None, None)
            ],
            #C
            [
                (self._cpy, Mode.IMM),
                (self._cmp, Mode.ZPIX),
                (None, None),
                (None, None),
                (self._cpy, Mode.ZP),
                (self._cmp, Mode.ZP),
                (self._dec, Mode.ZP),
                (None, None),
                (self._iny, Mode.IMPLIED),
                (self._cmp, Mode.IMM),
                (self._dex, Mode.IMPLIED),
                (None, None),
                (self._cpy, Mode.ABS),
                (self._cmp, Mode.ABS),
                (self._dec, Mode.ABS),
                (None, None)
            ],
            #D
            [
                (self._bne, Mode.REL),
                (self._cmp, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._cmp, Mode.ZPX),
                (self._dec, Mode.ZPX),
                (None, None),
                (self._cld, Mode.IMPLIED),
                (self._cmp, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._cmp, Mode.ABSX),
                (self._dec, Mode.ABSX),
                (None, None)
            ],
            #E
            [
                (self._cpx, Mode.IMM),
                (self._sbc, Mode.ZPIX),
                (None, None),
                (None, None),
                (self._cpx, Mode.ZP),
                (self._sbc, Mode.ZP),
                (self._inc, Mode.ZP),
                (None, None),
                (self._inx, Mode.IMPLIED),
                (self._sbc, Mode.IMM),
                (self._nop, Mode.IMPLIED),
                (None, None),
                (self._cpx, Mode.ABS),
                (self._sbc, Mode.ABS),
                (self._inc, Mode.ABS),
                (None, None)
            ],
            #F
            [
                (self._beq, Mode.REL),
                (self._sbc, Mode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._sbc, Mode.ZPX),
                (self._inc, Mode.ZPX),
                (None, None),
                (self._sed, Mode.IMPLIED),
                (self._sbc, Mode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._sbc, Mode.ABSX),
                (self._inc, Mode.ABSX),
                (None, None)
            ]
        ]

    def _adc(self, mode: Mode):
        data = 0
        if mode == Mode.ABSIX:
            (data, _) = self._mode_absix()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        elif mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        else:
            raise IllegalAddressingMode(f"ADC {mode.name}")

        self._a = self._a + data + self._flags.carry
        if self._a & 0xFF00:
            self._flags.carry = 1
            self._a = self._a & 0xFF

    def _and(self, mode: Mode):
        data = 0
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"AND {mode.name}")

        self._a = (self._a & data) & 0xFF

    def _asl(self, mode: Mode):
        if mode == Mode.ACC:
            data = self._a
            self._a = self.__shift_left(data)
        elif mode == Mode.ABS:
            (data, addr) = self._mode_abs()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
            shifted = self.__shift_left(data)
            self._ram.write(addr, data)
        else:
            raise IllegalAddressingMode(f"ASL {mode.name}")

    def __shift_left(self, data):
        shifted = data << 1
        if 0x100 & shifted:
            shifted &= 0xFF
            self._flags.carry = 1
        else:
            shifted &= 0xFF
        return shifted

    def _bcc(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BCC {mode.name}")

        if self._flags.carry == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _bcs(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BCS {mode.name}")

        if self._flags.carry == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _beq(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BEQ {mode.name}")

        if self._flags.zero == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _bit(self, mode: Mode):
        pass

    def _bmi(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BMI {mode.name}")

        if self._flags.sign == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _bne(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BNE {mode.name}")

        if self._flags.zero == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _bpl(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BPL {mode.name}")

        if self._flags.sign == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _brk(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"BRK {mode.name}")

        self._pc.reg += 2
        self._stack.push(self._pc.pc_hi())
        self._stack.push(self._pc.pc_lo())
        self._pc.reg -= 2
        self._stack.push(self._flags.to_int())

        self._pc.set_pc_lo(self._ram.read(0xFFFE))
        self._pc.set_pc_hi(self._ram.read(0xFFFF))

    def _bvc(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BVC {mode.name}")

        if self._flags.overflow == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _bvs(self, mode: Mode):
        if mode != Mode.REL:
            raise IllegalAddressingMode(f"BVS {mode.name}")

        if self._flags.overflow == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(displacement)
        else:
            self._pc.advance_pc()

    def _clc(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"CLC {mode.name}")

        self._flags.carry = 0

    def _cld(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"CLD {mode.name}")

        self._flags.decimal = 0

    def _cli(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"CLI {mode.name}")

        self._flags.interrupt = 0

    def _clv(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"CLV {mode.name}")

        self._flags.overflow = 0

    def _cmp(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"CMP {mode.name}")

        result = self._a - data
        if result == 0:
            self._flags.zero = 1
        else:
            self._flags.zero = 0

        if result & 0x80:
            self._flags.sign = 1
        else:
            self._flags.sign = 0

        if self._a >= data:
            self._flags.carry = 1
        else:
            self._flags.carry = 0

    def _cpx(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        else:
            raise IllegalAddressingMode(f"CPX {mode.name}")

        result = self._x - data
        if result == 0:
            self._flags.zero = 1
        else:
            self._flags.zero = 0

        if result & 0x80:
            self._flags.sign = 1
        else:
            self._flags.sign = 0

        if self._x >= data:
            self._flags.carry = 1
        else:
            self._flags.carry = 0

    def _cpy(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        else:
            raise IllegalAddressingMode(f"CPX {mode.name}")

        result = self._y - data
        if result == 0:
            self._flags.zero = 1
        else:
            self._flags.zero = 0

        if result & 0x80:
            self._flags.sign = 1
        else:
            self._flags.sign = 0

        if self._y >= data:
            self._flags.carry = 1
        else:
            self._flags.carry = 0

    def _dec(self, mode: Mode):
        if mode == Mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"DEC {mode.name}")

        result = data - 1
        self._ram.write(addr, result)

        self._flags.update_sign(result)
        self._flags.update_zero(result)

    def _dex(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"DEX {mode.name}")

        self._x = self._x - 1

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _dey(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"DEY {mode.name}")

        self._y = self._y - 1

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _eor(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"EOR {mode.name}")

        self._a = self._a ^ data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)


    def _inc(self, mode: Mode):
        if mode == Mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"INC {mode.name}")

        result = data + 1
        self._ram.write(addr, result)

        self._flags.update_sign(result)
        self._flags.update_zero(result)

    def _inx(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"INX {mode.name}")

        self._x = self._x + 1

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _iny(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"INY {mode.name}")

        self._y = self._y + 1

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _jmp(self, mode: Mode):
        if mode == Mode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == Mode.IND:
            (_, addr) = self._mode_ind()
        else:
            raise IllegalAddressingMode(f"JMP {mode.name}")

        self._pc.reg = addr

    def _jsr(self, mode: Mode):
        if mode == Mode.ABS:
            (_, addr) = self._mode_abs()
        else:
            raise IllegalAddressingMode(f"JSR {mode.name}")

        self._stack.push(self._pc.pc_hi)
        self._stack.push(self._pc.pc_lo)
        self._pc.reg = addr

    def _lda(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            data = self._data_fetch()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"LDA {mode.name}")

        self._a = data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _ldx(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            (data, _) = self._mode_imm()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPY:
            (data, _) = self._mode_zpy()
        else:
            raise IllegalAddressingMode(f"LDX {mode.name}")

        self._x = data

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _ldy(self, mode: Mode):
        if mode == Mode.IMM:
            (data, _) = self._mode_imm()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        else:
            raise IllegalAddressingMode(f"LDY {mode.name}")

        self._y = data

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _lsr(self, mode: Mode):
        if mode == Mode.ACC:
            data = self._a
            addr = None
        elif mode == Mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"LSR {mode.name}")

        self._flags.update_carry(data, bit7=False)
        data = data >> 1
        self._flags.update_sign(data)
        self._flags.update_zero(data)

        if addr is not None:
            self._ram.write(addr, data)
        else:
            self._a = data

    def _nop(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"NOP {mode.name}")

        time.sleep(MPU.CYCLE * 2)

    def _ora(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            (data, _) = self._mode_imm()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"ORA {mode.name}")

        self._a = self._a | data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _pha(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"PHA {mode.name}")

        self._stack.push(self._a)

    def _php(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"PHP {mode.name}")

        self._stack.push(self._flags.to_int())

    def _pla(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"PLA {mode.name}")

        self._a = self._stack.pop()

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _plp(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"PLP {mode.name}")

        self._flags.update_flags(self._stack.pop())

    def _rol(self, mode: Mode):
        if mode == Mode.ACC:
            data = self._a
            addr = None
        elif mode == Mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"ROL {mode.name}")

        current_carry = self._flags.carry
        self._flags.update_carry(data)
        data = 0xFF & (data << 1)
        data |= current_carry

        if addr is not None:
            self._ram.write(addr, data)
        else:
            self._a = data


    def _ror(self, mode: Mode):
        if mode == Mode.ACC:
            data = self._a
            addr = None
        elif mode == Mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == Mode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == Mode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"ROR {mode.name}")

        current_carry = self._flags.carry
        self._flags.update_carry(data, bit7=False)
        data = 0xFF & (data >> 1)
        data |= (current_carry << 7)

        if addr is not None:
            self._ram.write(addr, data)
        else:
            self._a = data

    def _rti(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"RTI {mode.name}")

        self._flags.update_flags(self._stack.pop())
        self._pc.set_pc_lo(self._stack.pop())
        self._pc.set_pc_hi(self._stack.pop())

    def _rts(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"RTS {mode.name}")

        self._pc.set_pc_lo(self._stack.pop())
        self._pc.set_pc_hi(self._stack.pop())

    def _sbc(self, mode: Mode):
        if mode == Mode.ABS:
            (data, _) = self._mode_abs()
        elif mode == Mode.ZP:
            (data, _) = self._mode_zp()
        elif mode == Mode.IMM:
            (data, _) = self._mode_imm()
        elif mode == Mode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == Mode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"SBC {mode.name}")

        # TODO Revisit
        self._a = self._a - data - self._flags.carry

        self._flags.update_sign(self._a)
        # TODO self._flags.update_overflow(self._a)
        self._flags.update_zero(self._a)
        self._flags.update_carry(self._a)

        self._a &= 0xFF

    def _sec(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"SEC {mode.name}")

        self._flags.carry = 1

    def _sed(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"SED {mode.name}")

        self._flags.decimal = 1

    def _sei(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"SEI {mode.name}")

        self._flags.interrupt = 1

    def _sta(self, mode: Mode):
        if mode == Mode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == Mode.ABSX:
            (_, addr) = self._mode_absx()
        elif mode == Mode.ABSY:
            (_, addr) = self._mode_absy()
        elif mode == Mode.ZPIX:
            (_, addr) = self._mode_zpix()
        elif mode == Mode.ZPIY:
            (_, addr) = self._mode_zpiy()
        elif mode == Mode.ZPX:
            (_, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"STA {mode.name}")

        self._ram.write(addr, self._a)


    def _stx(self, mode: Mode):
        if mode == Mode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == Mode.ZPY:
            (_, addr) = self._mode_zpy()
        else:
            raise IllegalAddressingMode(f"STX {mode.name}")

        self._ram.write(addr, self._x)

    def _sty(self, mode: Mode):
        if mode == Mode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == Mode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == Mode.ZPX:
            (_, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"STY {mode.name}")

        self._ram.write(addr, self._y)

    def _tax(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TAX {mode.name}")

        self._x = self._a

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _tay(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TAY {mode.name}")

        self._y = self._a

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _tsx(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TSX {mode.name}")

        self._x = self._stack.sp

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _txa(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TXA {mode.name}")

        self._a = self._x

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _txs(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TXS {mode.name}")

        self._stack.sp = self._x

        self._flags.update_sign(self._stack.sp)
        self._flags.update_zero(self._stack.sp)

    def _tya(self, mode: Mode):
        if mode != Mode.IMPLIED:
            raise IllegalAddressingMode(f"TYA {mode.name}")

        self._a = self._y

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _absix_fetch(self):
        addr = self._ram.read(self._pc.reg)
        self._pc.advance_pc()
        addr += self._x
        return addr

    def _data_fetch(self):
        data = self._ram.read(self._pc.reg)
        self._pc.advance_pc()
        return data

    def _zpage_addr_fetch(self):
        addr = self._ram.read(self._pc.reg)
        self._pc.advance_pc()
        return addr

    def _addr_fetch(self):
        addr_hi = self._ram.read(self._pc.reg)
        self._pc.advance_pc()
        addr_lo = self._ram.read(self._pc.reg)
        self._pc.advance_pc()
        addr = (addr_hi << 4) | (addr_lo)
        return addr

    def _mode_imm(self):
        data = self._data_fetch()
        return (data, None)

    def _mode_absix(self):
        addr = self._absix_fetch()
        ind_addr = self._ram.read(addr)
        data = self._ram.read(ind_addr)
        return (data, ind_addr)

    def _mode_zp(self):
        addr = self._zpage_addr_fetch()
        data = self._ram.read(addr)
        return (data, addr)

    def _mode_abs(self):
        addr = self._addr_fetch()
        data = self._ram.read(addr)
        return (data, addr)

    def _mode_ind(self):
        addr = self._addr_fetch()
        ind_addr = self._ram.read(addr)
        return (None, ind_addr)

    def _mode_zpiy(self):
        addr = self._zpage_addr_fetch()
        ind_addr = self._ram.read(addr)
        data = self._ram.read(ind_addr + self._y)
        return (data, ind_addr + self._y)

    def _mode_absx(self):
        addr = self._addr_fetch()
        data = self._ram.read(addr + self._x)
        return (data, addr + self._x)

    def _mode_absy(self):
        addr = self._addr_fetch()
        data = self._ram.read(addr + self._y)
        return (data, addr + self._y)

    def _mode_zpx(self):
        addr = self._zpage_addr_fetch()
        data = self._ram.read(addr + self._x)
        return (data, addr + self._x)

    def _mode_zpy(self):
        addr = self._zpage_addr_fetch()
        data = self._ram.read(addr + self._y)
        return (data, addr + self._y)

    def _mode_zpix(self):
        ind_addr = self._zpage_addr_fetch()
        addr = self._ram.read(ind_addr + self._x)
        data = self._ram.read(addr)
        return (data, addr)

    def _dump(self):
        print(f"PC: {self._pc}")
        print(f"A: 0x{self._a:04x}")
        print(f"X: 0x{self._x:04x}")
        print(f"Y: 0x{self._y:04x}")

    def _execute(self):
        instruction = self._data_fetch()

        table = (instruction & 0xF0) >> 4
        entry = instruction & 0x0F
        table_block = self._lookup_table[table]
        (op, addr_mode) = table_block[entry]

        if op is None:
            raise RuntimeError("Invalid operation")

        op(addr_mode)

    def load(self, program):
        with open(program, 'rb') as binary_file:
            buffer : bytes = binary_file.read1(size=1)
            mem_loc = 0
            while buffer is not None:
                self._ram.write(mem_loc, int(buffer) & 0xFF)
                buffer = binary_file.read1(size=1)
                mem_loc += 1

    def run(self):
        execution_cycle = 0
        while execution_cycle < 0xFFFF:
            pre = time.time()
            self._execute()
            post = time.time()
            elapsed = post - pre
            if MPU.CYCLE > elapsed:
                time.sleep(MPU.CYCLE - elapsed)
            execution_cycle += 1

        return execution_cycle

def main():
    (opts, _) = getopt.getopt(sys.argv[1:], 'f:')

    program = None
    for (opt, arg) in opts:
        if opt == 'f':
            program = arg

    if program is None:
        raise RuntimeError("No program specified")

    c = MPU()
    c.load(program)
    t0 = time.time()
    cycles = c.run()
    t1 = time.time()
    print(f'Performed {cycles} execution cycles in {t1 - t0:.08f} seconds')

if __name__ == '__main__':
    main()
