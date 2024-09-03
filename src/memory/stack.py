from .ram import RAM

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