import random
import string
import traceback

class RAM:
    def __init__(self, size: int = 0xFFFF):
        self.size = size
        self.store = []
        for _ in range(size + 1):
            self.store.append(0)

    def _mirror_map(self, loc) -> int:
        if loc >= 0x0000 and loc <= 0x07FF:
            return loc
        elif loc >= 0x0800 and loc <= 0x0FFF:
            return loc - 0x0800
        elif loc >= 0x1000 and loc <= 0x17FF:
            return loc - 0x1000
        elif loc >= 0x1800 and loc <= 0x1FFF:
            return loc - 0x1800
        else:
            return loc

    def set_size(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size + 1):
            self.store.append(0)

    def read(self, loc) -> int:
        try:
            return self.store[loc]
        except IndexError as e:
            raise RuntimeError(f"Out of bounds read memory access {loc:04x} max {len(self.store):04x}") from e

    def write(self, loc, data):
        try:
            self.store[loc] = data
        except IndexError as e:
            raise RuntimeError(f"Out of bounds write memory access {loc:04x} max {len(self.store):04x}") from e

    def dma_transfer(self, page, to):
        base_address = (page << 8) & 0xFF00
        end_address = base_address | 0x00FF

        to_loc = 0
        for n in range(base_address, end_address + 1):
            to.write(to_loc, self.store[n])
            to_loc += 1

    def dump(self, file=None) -> None:
        print(type(self).__name__, file=file)
        for n in range(0, len(self.store), 16):
            ram_slice = self.store[n : n + 16]

            print(
                f"{n:04x}",
                " ".join(f"{x:02x}" for x in ram_slice), "|",
                "".join(chr(x) if chr(x) in "".join([string.digits, string.ascii_letters, string.punctuation]) else '.' for x in ram_slice),
                file=file
            )