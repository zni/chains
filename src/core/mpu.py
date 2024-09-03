import time

from .modes import AddressingMode

from exc.core import IllegalAddressingMode, EndOfExecution
from memory.ram import RAM
from memory.stack import Stack
from registers.pc import ProgramCounter
from registers.status import FlagRegister

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
                (self._brk, AddressingMode.IMPLIED),
                (self._ora, AddressingMode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, AddressingMode.ZP),
                (self._asl, AddressingMode.ZP),
                (None, None),
                (self._php, AddressingMode.IMPLIED),
                (self._ora, AddressingMode.IMM),
                (self._asl, AddressingMode.ACC),
                (None, None),
                (None, None),
                (self._ora, AddressingMode.ABS),
                (self._asl, AddressingMode.ABS),
                (None, None)
            ],
            #1
            [
                (self._bpl, AddressingMode.REL),
                (self._ora, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, AddressingMode.ZPX),
                (self._asl, AddressingMode.ZPX),
                (self._clc, AddressingMode.IMPLIED),
                (self._ora, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._ora, AddressingMode.ABSX),
                (self._asl, AddressingMode.ABSX),
                (None, None)
            ],
            #2
            [
                (self._jsr, AddressingMode.ABS),
                (self._and, AddressingMode.ABSIX),
                (None, None),
                (None, None),
                (self._bit, AddressingMode.ZP),
                (self._and, AddressingMode.ZP),
                (self._rol, AddressingMode.ZP),
                (None, None),
                (self._plp, AddressingMode.IMPLIED),
                (self._and, AddressingMode.IMM),
                (self._rol, AddressingMode.ACC),
                (None, None),
                (self._bit, AddressingMode.ABS),
                (self._and, AddressingMode.ABS),
                (self._rol, AddressingMode.ABS),
                (None, None)
            ],
            #3
            [
                (self._bmi, AddressingMode.REL),
                (self._and, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._and, AddressingMode.ZPX),
                (self._rol, AddressingMode.ZPX),
                (None, None),
                (self._sec, AddressingMode.IMPLIED),
                (self._and, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._and, AddressingMode.ABSX),
                (self._rol, AddressingMode.ABSX),
                (None, None)
            ],
            #4
            [
                (self._rti, AddressingMode.IMPLIED),
                (self._eor, AddressingMode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, AddressingMode.ZP),
                (self._lsr, AddressingMode.ZP),
                (None, None),
                (self._pha, AddressingMode.IMPLIED),
                (self._eor, AddressingMode.IMM),
                (self._lsr, AddressingMode.ACC),
                (None, None),
                (self._jmp, AddressingMode.ABS),
                (self._eor, AddressingMode.ABS),
                (self._lsr, AddressingMode.ABS),
                (None, None)
            ],
            #5
            [
                (self._bvc, AddressingMode.REL),
                (self._eor, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, AddressingMode.ZPX),
                (self._lsr, AddressingMode.ZPX),
                (None, None),
                (self._cli, AddressingMode.IMPLIED),
                (self._eor, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._eor, AddressingMode.ABSX),
                (self._lsr, AddressingMode.ABSX)
            ],
            #6
            [
                (self._rts, AddressingMode.IMPLIED),
                (self._adc, AddressingMode.ABSIX),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, AddressingMode.ZP),
                (self._ror, AddressingMode.ZP),
                (None, None),
                (self._pla, AddressingMode.IMPLIED),
                (self._adc, AddressingMode.IMM),
                (self._ror, AddressingMode.ACC),
                (None, None),
                (self._jmp, AddressingMode.IND),
                (self._adc, AddressingMode.ABS),
                (self._ror, AddressingMode.ABS),
                (None, None),
            ],
            #7
            [
                (self._bvs, AddressingMode.REL),
                (self._adc, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, AddressingMode.ZPX),
                (self._ror, AddressingMode.ZPX),
                (None, None),
                (self._sei, AddressingMode.IMPLIED),
                (self._adc, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._adc, AddressingMode.ABSX),
                (self._ror, AddressingMode.ABSX),
                (None, None)
            ],
            #8
            [
                (None, None),
                (self._sta, AddressingMode.ZPIX),
                (None, None),
                (None, None),
                (self._sty, AddressingMode.ZP),
                (self._sta, AddressingMode.ZP),
                (self._stx, AddressingMode.ZP),
                (None, None),
                (self._dey, AddressingMode.IMPLIED),
                (None, None),
                (self._txa, AddressingMode.IMPLIED),
                (None, None),
                (self._sty, AddressingMode.ABS),
                (self._sta, AddressingMode.ABS),
                (self._stx, AddressingMode.ABS),
                (None, None)
            ],
            #9
            [
                (self._bcc, AddressingMode.REL),
                (self._sta, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (self._sty, AddressingMode.ZPX),
                (self._sta, AddressingMode.ZPX),
                (self._stx, AddressingMode.ZPY),
                (None, None),
                (self._tya, AddressingMode.IMPLIED),
                (self._sta, AddressingMode.ABSY),
                (self._txs, AddressingMode.IMPLIED),
                (None, None),
                (None, None),
                (self._sta, AddressingMode.ABSX),
                (None, None),
                (None, None)
            ],
            #A
            [
                (self._ldy, AddressingMode.IMM),
                (self._lda, AddressingMode.ZPIX),
                (self._ldx, AddressingMode.IMM),
                (None, None),
                (self._ldy, AddressingMode.ZP),
                (self._lda, AddressingMode.ZP),
                (self._ldx, AddressingMode.ZP),
                (None, None),
                (self._tay, AddressingMode.IMPLIED),
                (self._lda, AddressingMode.IMM),
                (self._tax, AddressingMode.IMPLIED),
                (None, None),
                (self._ldy, AddressingMode.ABS),
                (self._lda, AddressingMode.ABS),
                (self._ldx, AddressingMode.ABS),
                (None, None)
            ],
            #B
            [
                (self._bcs, AddressingMode.REL),
                (self._lda, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (self._ldy, AddressingMode.ZPX),
                (self._lda, AddressingMode.ZPX),
                (self._ldx, AddressingMode.ZPY),
                (None, None),
                (self._clv, AddressingMode.IMPLIED),
                (self._lda, AddressingMode.ABSY),
                (self._tsx, AddressingMode.IMPLIED),
                (None, None),
                (self._ldy, AddressingMode.ABSX),
                (self._lda, AddressingMode.ABSX),
                (self._ldx, AddressingMode.ABSY),
                (None, None)
            ],
            #C
            [
                (self._cpy, AddressingMode.IMM),
                (self._cmp, AddressingMode.ZPIX),
                (None, None),
                (None, None),
                (self._cpy, AddressingMode.ZP),
                (self._cmp, AddressingMode.ZP),
                (self._dec, AddressingMode.ZP),
                (None, None),
                (self._iny, AddressingMode.IMPLIED),
                (self._cmp, AddressingMode.IMM),
                (self._dex, AddressingMode.IMPLIED),
                (None, None),
                (self._cpy, AddressingMode.ABS),
                (self._cmp, AddressingMode.ABS),
                (self._dec, AddressingMode.ABS),
                (None, None)
            ],
            #D
            [
                (self._bne, AddressingMode.REL),
                (self._cmp, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._cmp, AddressingMode.ZPX),
                (self._dec, AddressingMode.ZPX),
                (None, None),
                (self._cld, AddressingMode.IMPLIED),
                (self._cmp, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._cmp, AddressingMode.ABSX),
                (self._dec, AddressingMode.ABSX),
                (None, None)
            ],
            #E
            [
                (self._cpx, AddressingMode.IMM),
                (self._sbc, AddressingMode.ZPIX),
                (None, None),
                (None, None),
                (self._cpx, AddressingMode.ZP),
                (self._sbc, AddressingMode.ZP),
                (self._inc, AddressingMode.ZP),
                (None, None),
                (self._inx, AddressingMode.IMPLIED),
                (self._sbc, AddressingMode.IMM),
                (self._nop, AddressingMode.IMPLIED),
                (None, None),
                (self._cpx, AddressingMode.ABS),
                (self._sbc, AddressingMode.ABS),
                (self._inc, AddressingMode.ABS),
                (None, None)
            ],
            #F
            [
                (self._beq, AddressingMode.REL),
                (self._sbc, AddressingMode.ZPIY),
                (None, None),
                (None, None),
                (None, None),
                (self._sbc, AddressingMode.ZPX),
                (self._inc, AddressingMode.ZPX),
                (None, None),
                (self._sed, AddressingMode.IMPLIED),
                (self._sbc, AddressingMode.ABSY),
                (None, None),
                (None, None),
                (None, None),
                (self._sbc, AddressingMode.ABSX),
                (self._inc, AddressingMode.ABSX),
                (None, None)
            ]
        ]

    def _adc(self, mode: AddressingMode):
        data = 0
        if mode == AddressingMode.ABSIX:
            (data, _) = self._mode_absix()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            data = self._data_fetch()
        elif mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        else:
            raise IllegalAddressingMode(f"ADC {mode.name}")

        self._a = self._a + data + self._flags.carry
        if self._a & 0xFF00:
            self._flags.carry = 1
            self._a = self._a & 0xFF

    def _and(self, mode: AddressingMode):
        data = 0
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            data = self._data_fetch()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"AND {mode.name}")

        self._a = (self._a & data) & 0xFF

    def _asl(self, mode: AddressingMode):
        if mode == AddressingMode.ACC:
            data = self._a
            self._a = self.__shift_left(data)
        elif mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
            shifted = self.__shift_left(data)
            self._ram.write(addr, shifted)
        elif mode == AddressingMode.ZPX:
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

    def _bcc(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BCC {mode.name}")

        if self._flags.carry == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _bcs(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BCS {mode.name}")

        if self._flags.carry == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _beq(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BEQ {mode.name}")

        if self._flags.zero == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _bit(self, mode: AddressingMode):
        if mode == mode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == mode.ZP:
            (data, addr) = self._mode_zp()
        else:
            raise IllegalAddressingMode(f"BIT {mode.name}")

        result = self._a & data
        if result == 0:
            self._flags.zero = 1
        else:
            self._flags.zero = 0

        self._flags.overflow = (result & 0x40) >> 6
        self._flags.sign = (result & 0x80) >> 7

    def _bmi(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BMI {mode.name}")

        if self._flags.sign == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _bne(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BNE {mode.name}")

        if self._flags.zero == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _bpl(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BPL {mode.name}")

        if self._flags.sign == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _brk(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"BRK {mode.name}")

        self._pc.reg += 2
        self._stack.push(self._pc.pc_hi())
        self._stack.push(self._pc.pc_lo())
        self._pc.reg -= 2
        self._stack.push(self._flags.to_int())

        self._pc.set_pc_lo(self._ram.read(0xFFFE))
        self._pc.set_pc_hi(self._ram.read(0xFFFF))

    def _bvc(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BVC {mode.name}")

        if self._flags.overflow == 0:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _bvs(self, mode: AddressingMode):
        if mode != AddressingMode.REL:
            raise IllegalAddressingMode(f"BVS {mode.name}")

        if self._flags.overflow == 1:
            displacement = self._ram.read(self._pc.reg)
            self._pc.displace_pc(self._to_signed(displacement))
        else:
            self._pc.advance_pc()

    def _clc(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"CLC {mode.name}")

        self._flags.carry = 0

    def _cld(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"CLD {mode.name}")

        self._flags.decimal = 0

    def _cli(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"CLI {mode.name}")

        self._flags.interrupt = 0

    def _clv(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"CLV {mode.name}")

        self._flags.overflow = 0

    def _cmp(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            data = self._data_fetch
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
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

    def _cpx(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
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

    def _cpy(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
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

    def _dec(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == AddressingMode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"DEC {mode.name}")

        result = data - 1
        self._ram.write(addr, result)

        self._flags.update_sign(result)
        self._flags.update_zero(result)

    def _dex(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"DEX {mode.name}")

        self._x = self._x - 1

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _dey(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"DEY {mode.name}")

        self._y = self._y - 1

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _eor(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            data = self._data_fetch()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"EOR {mode.name}")

        self._a = self._a ^ data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)


    def _inc(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == AddressingMode.ZPX:
            (data, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"INC {mode.name}")

        result = data + 1
        self._ram.write(addr, result)

        self._flags.update_sign(result)
        self._flags.update_zero(result)

    def _inx(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"INX {mode.name}")

        self._x = self._x + 1

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _iny(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"INY {mode.name}")

        self._y = self._y + 1

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _jmp(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == AddressingMode.IND:
            (_, addr) = self._mode_ind()
        else:
            raise IllegalAddressingMode(f"JMP {mode.name}")

        self._pc.reg = addr

    def _jsr(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (_, addr) = self._mode_abs()
        else:
            raise IllegalAddressingMode(f"JSR {mode.name}")

        self._stack.push(self._pc.pc_hi)
        self._stack.push(self._pc.pc_lo)
        self._pc.reg = addr

    def _lda(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            data = self._data_fetch()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"LDA {mode.name}")

        self._a = data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _ldx(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            (data, _) = self._mode_imm()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPY:
            (data, _) = self._mode_zpy()
        else:
            raise IllegalAddressingMode(f"LDX {mode.name}")

        self._x = data

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _ldy(self, mode: AddressingMode):
        if mode == AddressingMode.IMM:
            (data, _) = self._mode_imm()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        else:
            raise IllegalAddressingMode(f"LDY {mode.name}")

        self._y = data

        self._flags.update_sign(self._y)
        self._flags.update_zero(self._y)

    def _lsr(self, mode: AddressingMode):
        if mode == AddressingMode.ACC:
            data = self._a
            addr = None
        elif mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == AddressingMode.ZPX:
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

    def _nop(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"NOP {mode.name}")

        time.sleep(MPU.CYCLE * 2)

    def _ora(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            (data, _) = self._mode_imm()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (data, _) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"ORA {mode.name}")

        self._a = self._a | data

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _pha(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"PHA {mode.name}")

        self._stack.push(self._a)

    def _php(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"PHP {mode.name}")

        self._stack.push(self._flags.to_int())

    def _pla(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"PLA {mode.name}")

        self._a = self._stack.pop()

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _plp(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"PLP {mode.name}")

        self._flags.update_flags(self._stack.pop())

    def _rol(self, mode: AddressingMode):
        if mode == AddressingMode.ACC:
            data = self._a
            addr = None
        elif mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == AddressingMode.ZPX:
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


    def _ror(self, mode: AddressingMode):
        if mode == AddressingMode.ACC:
            data = self._a
            addr = None
        elif mode == AddressingMode.ABS:
            (data, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, addr) = self._mode_zp()
        elif mode == AddressingMode.ABSX:
            (data, addr) = self._mode_absx()
        elif mode == AddressingMode.ZPX:
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

    def _rti(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"RTI {mode.name}")

        self._flags.update_flags(self._stack.pop())
        self._pc.set_pc_lo(self._stack.pop())
        self._pc.set_pc_hi(self._stack.pop())

    def _rts(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"RTS {mode.name}")

        self._pc.set_pc_lo(self._stack.pop())
        self._pc.set_pc_hi(self._stack.pop())

    def _sbc(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (data, _) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (data, _) = self._mode_zp()
        elif mode == AddressingMode.IMM:
            (data, _) = self._mode_imm()
        elif mode == AddressingMode.ABSX:
            (data, _) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (data, _) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (data, _) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (data, _) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
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

    def _sec(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"SEC {mode.name}")

        self._flags.carry = 1

    def _sed(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"SED {mode.name}")

        self._flags.decimal = 1

    def _sei(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"SEI {mode.name}")

        self._flags.interrupt = 1

    def _sta(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == AddressingMode.ABSX:
            (_, addr) = self._mode_absx()
        elif mode == AddressingMode.ABSY:
            (_, addr) = self._mode_absy()
        elif mode == AddressingMode.ZPIX:
            (_, addr) = self._mode_zpix()
        elif mode == AddressingMode.ZPIY:
            (_, addr) = self._mode_zpiy()
        elif mode == AddressingMode.ZPX:
            (_, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"STA {mode.name}")

        self._ram.write(addr, self._a)


    def _stx(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == AddressingMode.ZPY:
            (_, addr) = self._mode_zpy()
        else:
            raise IllegalAddressingMode(f"STX {mode.name}")

        self._ram.write(addr, self._x)

    def _sty(self, mode: AddressingMode):
        if mode == AddressingMode.ABS:
            (_, addr) = self._mode_abs()
        elif mode == AddressingMode.ZP:
            (_, addr) = self._mode_zp()
        elif mode == AddressingMode.ZPX:
            (_, addr) = self._mode_zpx()
        else:
            raise IllegalAddressingMode(f"STY {mode.name}")

        self._ram.write(addr, self._y)

    def _tax(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"TAX {mode.name}")

        self._x = self._a

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _tay(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"TAY {mode.name}")

        self._y = self._a

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _tsx(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"TSX {mode.name}")

        self._x = self._stack.sp

        self._flags.update_sign(self._x)
        self._flags.update_zero(self._x)

    def _txa(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"TXA {mode.name}")

        self._a = self._x

        self._flags.update_sign(self._a)
        self._flags.update_zero(self._a)

    def _txs(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
            raise IllegalAddressingMode(f"TXS {mode.name}")

        self._stack.sp = self._x

        self._flags.update_sign(self._stack.sp)
        self._flags.update_zero(self._stack.sp)

    def _tya(self, mode: AddressingMode):
        if mode != AddressingMode.IMPLIED:
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

    def _to_signed(self, n) -> int:
        if n & 0x80:
            return ~0 | n
        else:
            return n

    def dump(self):
        print(f"P : 0x{self._flags.to_int():04x}")
        print(f"PC: 0x{self._pc.reg:04x}")
        print(f" A: 0x{self._a:04x}")
        print(f" X: 0x{self._x:04x}")
        print(f" Y: 0x{self._y:04x}")

    def _execute(self, trace=False):
        instruction = self._data_fetch()

        table = (instruction & 0xF0) >> 4
        entry = instruction & 0x0F
        table_block = self._lookup_table[table]
        (op, addr_mode) = table_block[entry]

        if op is None:
            raise EndOfExecution()

        if trace:
            print(op.__qualname__)

        op(addr_mode)

    def load(self, program, prg_size=0, start_load=0x8000):
        with open(program, 'rb') as binary_file:
            binary_file.seek(16)
            buffer : bytes = binary_file.read1(1)
            mem_loc = start_load
            prg_read_size = 1
            while buffer and prg_read_size < prg_size:
                self._ram.write(mem_loc, int.from_bytes(buffer, byteorder='big') & 0xFF)
                buffer = binary_file.read1(1)
                mem_loc += 1
                prg_read_size += 1

    def reset(self):
        start_lo = self._ram.read(0xFFFC)
        start_hi = self._ram.read(0xFFFD)
        start = (start_hi << 8) | (start_lo)
        print(f"start: {start:04x}")
        self._pc.reg = start
        self._a = 0
        self._x = 0
        self._y = 0

    def run(self, trace=False):
        execution_cycle = 0
        try:
            while True:
                pre = time.time()
                self._execute(trace=trace)
                post = time.time()
                elapsed = post - pre
                if MPU.CYCLE > elapsed:
                    time.sleep(MPU.CYCLE - elapsed)
                execution_cycle += 1
        except EndOfExecution:
            return execution_cycle
