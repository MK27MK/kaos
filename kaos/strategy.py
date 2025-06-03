from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def init(self):
        pass
