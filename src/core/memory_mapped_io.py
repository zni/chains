import abc

class MemoryMappedIO(abc.ABC):
    @abc.abstractmethod
    def read(self, loc:int) -> int:
        return 0

    @abc.abstractmethod
    def write(self, loc:int, data:int) -> None:
        return