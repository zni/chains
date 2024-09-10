class RAM:
    def __init__(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size + 1):
            self.store.append(0x0)

    def _mirror_map(self, loc) -> int:
        if loc >= 0x0000 and loc <= 0x07FFF:
            return loc
        elif loc >= 0x0800 and loc <= 0x0FFF:
            return loc - 0x0800
        elif loc >= 0x1000 and loc <= 0x17FF:
            return loc - 0x1000
        elif loc >= 0x1800 and loc <= 0x1FFF:
            return loc - 0x1800
        else:
            return loc

        # base_slice = self.store[0x0000:0x07FF]
        # self.store[0x0800:0x0FFF] = base_slice
        # self.store[0x1000:0x17FF] = base_slice
        # self.store[0x1800:0x1FFF] = base_slice

    def set_size(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size + 1):
            self.store.append(0x0)

    def read(self, loc) -> int:
        try:
            return self.store[self._mirror_map(loc)]
        except IndexError as e:
            raise RuntimeError(f"Out of bounds read memory access {loc:04x} max {len(self.store):04x}") from e

    def write(self, loc, data):
        try:
            self.store[self._mirror_map(loc)] = data
        except IndexError as e:
            raise RuntimeError(f"Out of bounds write memory access {loc:04x} max {len(self.store):04x}") from e

    def dma_transfer(self, page, to):
        base_address = (page << 8) & 0xFF00
        end_address = base_address | 0x00FF

        to_loc = 0
        for n in range(base_address, end_address + 1):
            self.store[n] = to.store[to_loc]
            to_loc += 1
