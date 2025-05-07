import re
from pathlib import Path

import pandas as pd

from revelation.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

# ----------------------------------------------------------------------
# asset classes
# ----------------------------------------------------------------------


class AssetClass:
    pass


class Currencies(AssetClass):
    pass


# ----------------------------------------------------------------------
# instruments classes
# ----------------------------------------------------------------------


class Instrument:
    # per ora lo lascio vuoto
    def __init__(self, sector):
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
        asset_class,
        contract_code: str,  # i.e. 6EM2025, ESH2020
        activation: pd.Timestamp | None = None,
        expiration: pd.Timestamp | None = None,
        data: (
            pd.DataFrame | None
        ) = None,  # NOTE per adesso pensiamo solo a D candlestick data
    ):
        # TODO gestisci l'ereditarieta
        super().__init__(asset_class)

        # contract code parsing ----------------------------------------
        code = contract_code.upper()
        parsed = self._RE.match(code)
        if not parsed:
            raise ValueError(f"Failed to parse contract code: {contract_code}")

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
        # etc

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


# TODO deve poter accettare E6_M_2924 o anche E6_M_24
def stitch_contracts(contracts: list[FuturesContract], rollover_rule) -> pd.DataFrame:
    # sort contracts based on their expiry
    # sorted_codes: list[str] = sorted(contracts.keys(), key=)
    pass
