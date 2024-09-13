import abc

class BusMember(abc.ABC):
    @abc.abstractmethod
    def read(self, loc: int) -> int:
        return 0

    @abc.abstractmethod
    def write(self, loc:int, data:int) -> None:
        return

    @abc.abstractmethod
    def dma_transfer(self, page:int, to: "BusMember") -> None:
        return

    @abc.abstractmethod
    def nmi(self) -> None:
        return