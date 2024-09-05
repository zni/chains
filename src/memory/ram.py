class RAM:
    def __init__(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size + 1):
            self.store.append(0)

    def set_size(self, size: int = 0xFFFF):
        self.store = []
        for _ in range(size + 1):
            self.store.append(0)

    def read(self, loc) -> int:
        try:
            return self.store[loc]
        except IndexError as e:
            raise RuntimeError(f"Out of bounds read memory access {loc:04x}") from e

    def write(self, loc, data):
        try:
            self.store[loc] = data
        except IndexError as e:
            raise RuntimeError(f"Out of bounds write memory access {loc:04x}") from e
