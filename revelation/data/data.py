import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from revelation.data.enums import (
    AssetClass,
    DataSource,
    FuturesContractType,
    RolloverRule,
)
from revelation.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------


class Data(ABC):
    pass


@dataclass
class ReferenceData(Data):
    """
    Reference data is metadata describing instruments and entities.
    Some examples: contract size, ticker, expiration date, increment.
    https://learning.oreilly.com/library/view/financial-data-engineering/9781098159986/
    """

    source: DataSource
    asset_class: AssetClass
    # porta activation cazzi e mazzi qui
    # TODO classe FuturesReferenceData?


# ----------------------------------------------------------------------
# instruments classes
# ----------------------------------------------------------------------


class Instrument:
    @abstractmethod
    def __init__(
        self,
        reference_data: ReferenceData,
        market_data: dict[str, pd.DataFrame],
    ):
        self.reference_data = reference_data
        self.market_data = market_data

    @property
    def asset_class(self) -> AssetClass:
        """Asset class of the instrument."""
        return self.reference_data.asset_class

    @property
    def source(self) -> DataSource:
        """Source of the instrument's market data."""
        return self.reference_data.source


class FuturesContract(Instrument):

    # allows an arbitrary long product name, one char for month code and
    # 2-4 chars for year
    _RE_INDIVIDUAL = re.compile(
        r"^(?P<product>[A-Z0-9]+)(?P<month>[FGHJKMNQUVXZ])(?P<year>\d{2,4})$",
        re.IGNORECASE,
    )
    _RE_CONTINUOUS = re.compile(
        r"^(?P<product>[A-Z0-9]+)(?P<series>\d+)!$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        reference_data: ReferenceData,
        # NOTE daily obbligatori per il funzionamento attualmente
        market_data: dict[str, pd.DataFrame],
        contract_code: str,  # i.e. 6EM2025, ESH2020
        type: FuturesContractType = FuturesContractType.INDIVIDUAL,
        activation: pd.Timestamp | None = None,
        expiration: pd.Timestamp | None = None,
    ):
        super().__init__(reference_data, market_data)

        # contract code parsing ----------------------------------------
        # TODO aggiungi logica di differenziazione individual e continuous
        code = contract_code.upper()
        pattern = (
            self._RE_INDIVIDUAL
            if type == FuturesContractType.INDIVIDUAL
            else self._RE_CONTINUOUS
        )
        parsed = pattern.match(code)
        if not parsed:
            raise ValueError(f"Failed to parse contract code: {code}")

        self.product_code: str = parsed["product"]  # ex. 6E, ES, ZN
        self.contract_code: str = contract_code  # i.e. 6EM2025, ESH2020

        # NOTE valuta di inizializzarlo a None
        if type == FuturesContractType.INDIVIDUAL:
            self.month_code: str = parsed["month"]  # ex. H, M, U, Z

        # expiration and activation ------------------------------------
        # TODO rendi piu robusto
        self.activation: pd.Timestamp = (
            activation
            if isinstance(activation, pd.Timestamp)
            else market_data["D"].index[0]
        )
        self.expiration: pd.Timestamp = (
            expiration
            if isinstance(expiration, pd.Timestamp)
            else market_data["D"].index[-1]
        )

    # ------------------------------------------------------------------
    # methods
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # magic methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return self.contract_code


# I may actually use a list[Instrument]
# avere un unico time index anziche 3 mila tabelle
# class Universe:
#     def __init__(self, instruments: list[Instrument]):


# ----------------------------------------------------------------------
# helper functions
# ----------------------------------------------------------------------


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


def merge_contracts(contracts: list[FuturesContract], rollover_rule) -> FuturesContract:
    """
    Contract merging changes based on the timeframe of the candle provided.
    DAILY:
    INTRADAY:

    ## Returns
    A FuturesContract object with continuous data
    """
    # sort contracts based on their expiry
    sort_contracts(contracts)

    continuous: FuturesContract = FuturesContract(
        reference_data=contracts[0].reference_data,
        contract_code=contracts[0].product_code + "1!",
        activation=contracts[0].activation,
        expiration=contracts[-1].expiration,
        market_data=pd.DataFrame(),
        type=FuturesContractType.CONTINUOUS,
    )
    # NOTE considera si spostare `start_date` qui
    # dont loop over last contract bc its concatenated by previous loop
    for i in range(len(contracts) - 1):
        front: FuturesContract = contracts[i]
        next: FuturesContract = contracts[i + 1]

        match rollover_rule:
            case RolloverRule.EXPIRY:
                # finds the index immediately after front.expiration
                start_date: pd.Timestamp = (
                    next_timestamp(next.market_data["D"].index, front.expiration)
                    if i != 0  # start from the beginning of the first contract
                    else front.activation
                )
                # TODO separa EXPIRY_BEFORE e EXPIRY_AFTER
                # concatenates to continuous from the day after expiration to
                # the next expiration
                continuous.market_data = pd.concat(
                    [
                        continuous.market_data,
                        next.market_data["D"].loc[start_date : next.expiration],
                    ]
                )
            case RolloverRule.OPEN_INTEREST:
                # TODO implementare regola secondo cui al crossover in OI
                # TODO si switcha, ma facendo attenzione ai fakeout.
                # su questo proposito analizza i fakeout in OI fra i vari strumenti e
                # quantomeno inserisci un primo filtro temporale (es a partire
                #  da 10 giorni da exp accetti crossover)
                raise NotImplementedError("")

    return continuous
