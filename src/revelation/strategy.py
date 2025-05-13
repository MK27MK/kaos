from abc import ABC, abstractmethod


class Strategy(ABC):  # TODO make it abc?
    @abstractmethod
    def init(self):
        pass
