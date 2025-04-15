from pathlib import Path
import pandas as pd


class Instrument:
    # per ora lo lascio vuoto
    def __init__(self, sector):
        pass


class FuturesContract(Instrument):
    def __init__(
        self,
        sector,
        start_date,
        settlement_date,
    ):
        # gestisci l'ereditarieta
        super().__init__(sector)
        self.start_date = start_date
        self.settlement_date = settlement_date
        # etc


# I may actually use a list[Instrument]
# avere un unico time index anziche 3 mila tabelle
class Universe:
    pass


# devo avere la timeline dei contratti allineati per bene per strumento,
# bisogna gestire il rollover
