from kaos.data.data import Universe
from kaos.risk import Portfolio
from kaos.strategy import Strategy


class Engine:
    def __init__(
        self,
        universe: Universe,
        strategies: list[Strategy],
        portfolio: Portfolio,
        # findings table... (might as well be composed in strategy/study)
    ):

        self.universe = universe

    def run(self):
        while True:
            pass
