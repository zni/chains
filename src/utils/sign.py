def to_8bit_signed(n: int) -> int:
        if n & 0x80:
            return ((~n & 0xff) + 1) * -1
        else:
            return n

def to_signed(n: int) -> int:
            return ((~n & 0xff) + 1) * -1