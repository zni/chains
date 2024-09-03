class RAM:
    def __init__(self, size=0xFFFF):
        self.store = []
        for _ in range(size + 1):
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
