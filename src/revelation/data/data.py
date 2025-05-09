import re
from pathlib import Path

import pandas as pd

from revelation.data.enums import AssetClass, FuturesContractType, RolloverRule
from revelation.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

# ----------------------------------------------------------------------
# instruments classes
# ----------------------------------------------------------------------


class Instrument:
    def __init__(self, asset_class: AssetClass):
        pass


class FuturesContract(Instrument):

    # allows an arbitrary long product name, one char for month code and
    # 2-4 chars for year
    _RE = re.compile(
        r"^(?P<product>[A-Z0-9]+)(?P<month>[FGHJKMNQUVXZ])(?P<year>\d{2,4})$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        asset_class: AssetClass,
        contract_code: str,  # i.e. 6EM2025, ESH2020
        activation: pd.Timestamp | None = None,
        expiration: pd.Timestamp | None = None,
        # NOTE per adesso pensiamo solo a D candlestick data
        data: pd.DataFrame | None = None,
        type: FuturesContractType = FuturesContractType.INDIVIDUAL,
    ):
        super().__init__(asset_class)

        # contract code parsing ----------------------------------------
        # TODO aggiungi logica di differenziazione individual e continuous
        code = contract_code.upper()
        parsed = self._RE.match(code)
        if not parsed:
            raise ValueError(f"Failed to parse contract code: {code}")

        self.product_code: str = parsed["product"]  # ex. 6E, ES, ZN
        self.month_code: str = parsed["month"]  # ex. H, M, U, Z
        # --------------------------------------------------------------

        self.asset_class = asset_class
        self.contract_code: str = contract_code
        self.activation: pd.Timestamp = (
            activation  # NOTE mi importa meno della scadenza,
        )
        # puoi anche usare la prima riga del df/ usarlo come validazione se trovi
        # la regole ufficiale
        self.expiration: pd.Timestamp = (
            expiration
            if expiration is not None
            else self._get_expiration(parsed["year"])
        )

        self.data = data

    # helpers-----------------------------------------------------------
    def _get_expiration(self, year: str) -> pd.Timestamp:
        # NOTE ci sono eccezioni in base a prodotto, es: CAD # https://www.cmegroup.com/rulebook/CME/III/250/252/252.pdf
        # TODO valida la scadenza usando la data dell'ultima riga del df
        """Given expiry year and month code, returns contract's
        expiration date based on CME's criteria."""

        # retrieve expiry year and month as integers
        year_num = int(year)  # TODO gestisci eventuale anno a due cifre
        month_num = month_of_year(self.month_code)

        # match self.asset_class:
        #     case Currencies:
        # third wed of contract month
        first_day = pd.Timestamp(
            year=year_num, month=month_num, day=1, tz=STANDARD_TIMEZONE
        )
        pass


class FuturesProduct(Instrument):
    pass


# I may actually use a list[Instrument]
# avere un unico time index anziche 3 mila tabelle
class Universe:
    pass


# ----------------------------------------------------------------------
# helper functions
# ----------------------------------------------------------------------


# devo avere la timeline dei contratti allineati per bene per strumento,
# bisogna gestire il rollover
def sort_contracts(contracts: list[FuturesContract]) -> None:
    """
    Sorts in-place a given list of Futures contracts based on expiry year
    and month code"""

    contracts.sort(key=lambda contract: contract.expiration)


def next_timestamp(index: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp | None:
    """Given a DateTimeIndex and a Timestamp, returns the
    successive Timestamp.

    O(1) if index is sorted and unique, else O(n)"""
    if ts in index:
        pos = index.get_loc(ts)
        return index[pos + 1] if pos + 1 < len(index) else None
    return None


def merge_contracts(contracts: list[FuturesContract], rollover_rule) -> pd.DataFrame:
    """
    Contract merging changes based on the timeframe of the candle provided.
    DAILY:
    INTRADAY:
    """
    # sort contracts based on their expiry
    sort_contracts(contracts)

    continuous: FuturesContract = FuturesContract(
        asset_class=contracts[0].asset_class,
        contract_code=contracts[0].product_code + "1!",
        activation=contracts[0].activation,
        expiration=contracts[-1].expiration,
        data=pd.DataFrame(),
        type=FuturesContractType.CONTINUOUS,
    )
    for i, front in enumerate(contracts):
        # FIXME causa index out of range se non sistemi
        next: FuturesContract = contracts[i + 1]

        match rollover_rule:
            # concatenates to continuous from the day after expiration
            # to
            case RolloverRule.EXPIRY:
                raise NotImplementedError(
                    "siccome non mi serve per adesso non ci lavoro."
                )
                # finds the index immediately after front.expiration
                switch_date: pd.Timestamp = next_timestamp(
                    next.data.index, front.expiration
                )
                next_of_interest: pd.DataFrame = next.data.loc[
                    switch_date : next.expiration
                ]
                continuous.data = pd.concat([continuous.data, next_of_interest])
            case RolloverRule.OPEN_INTEREST:
                # TODO implementare regola secondo cui al crossover in OI
                # TODO si switcha, ma facendo attenzione ai fakeout.
                # su questo proposito analizza i fakeout in OI fra i vari strumenti e
                # quantomeno inserisci un primo filtro temporale (es a partire
                #  da 10 giorni da exp accetti crossover)
                pass
