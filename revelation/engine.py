# attualmente lo scrivo col backtesting in testa
from revelation.data.data import Universe
from revelation.risk import Portfolio
from revelation.strategy import Strategy


class Engine:
    def __init__(
        self,
        universe: Universe,
        # FIXME in verita non strategy ma subclass
        strategies: list[Strategy],
        portfolio: Portfolio,
        # findings table... (potrei legarlo direttaemtne a strategy/study)
    ):

        self.universe = universe

    def run(self):
        while True:
            pass
