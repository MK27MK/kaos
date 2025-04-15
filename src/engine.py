# attualmente lo scrivo col backtesting in testa
from data.data import Universe
from strategy import Strategy
from risk import Portfolio


class Engine:
    def __init__(
        self,
        universe: Universe,
        # in verita non stratey ma subclass
        strategy: Strategy | list[Strategy],
        portfolio: Portfolio,
        # findings table...
    ):
        pass

    def run(self):
        while True:
            pass
