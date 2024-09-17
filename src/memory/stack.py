from .ram import RAM

class Stack:
    def __init__(self, ram: RAM, origin:int=0x1FF):
        self._ram = ram
        self._sp = origin

    @property
    def sp(self) -> int:
        return self._sp & 0xFF

    def set_sp(self, val:int):
        self._sp = (0x0100 | (val & 0xFF)) & 0x01FF

    def push(self, data: int):
        self._ram.store[self._sp] = data
        self._decrement_sp()

    def pop(self) -> int:
        self._increment_sp()
        data = self._ram.store[self._sp]
        return data

    def _decrement_sp(self):
        self._sp = ((self._sp - 1) & 0xFF) | 0x0100

    def _increment_sp(self):
        self._sp = ((self._sp + 1) & 0xFF) | 0x0100
