class RAM:
    def __init__(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size):
            self.store.append(0)

    def set_size(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size):
            self.store.append(0)

    def read(self, loc) -> int:
        try:
            return self.store[loc]
        except IndexError as e:
            raise RuntimeError("Out of bounds memory access") from e

    def write(self, loc, data):
        try:
            self.store[loc] = data
        except IndexError as e:
            raise RuntimeError("Out of bounds memory access") from e
