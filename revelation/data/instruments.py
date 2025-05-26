import re
from abc import abstractmethod

import pandas as pd

from revelation.data.data import FuturesReferenceData, MarketData, ReferenceData
from revelation.data.enums import (
    AssetClass,
    DataSource,
    FuturesContractType,
    RolloverRule,
)
from revelation.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

# ----------------------------------------------------------------------
# instruments classes
# ----------------------------------------------------------------------


class Instrument:
    @abstractmethod
    def __init__(
        self,
        reference_data: ReferenceData,
        market_data: MarketData,
    ):
        self.reference_data = reference_data
        self.market_data = market_data

    @property
    def asset_class(self) -> AssetClass:
        """Asset class of the instrument."""
        return self.reference_data.asset_class

    @property
    def data_source(self) -> DataSource:
        """Source of the instrument's market data."""
        return self.reference_data.data_source


# FuturesContract ------------------------------------------------------


# TODO separa continyous e individual
# NOTE continuous sono dati sintetici, valuta separazione classi
class FuturesContract(Instrument):

    def __init__(
        self,
        reference_data: FuturesReferenceData,
        # NOTE daily obbligatori per il funzionamento attualmente
        market_data: MarketData,
    ):
        """If reference data does not provide activation and expiration dates,
        the first and last date of the index will be used instead.

        Args:
            reference_data (FuturesReferenceData): _description_
            market_data (MarketData): _description_
        """
        super().__init__(reference_data, market_data)

        # activation and expiration ------------------------------------
        # TODO rendi piu robusto
        # In case exp and act are not provided, first and last date
        # of the index will be used instead
        if self.activation is None:
            self.reference_data.activation = market_data["D"].index[0]
        if self.expiration is None:
            self.reference_data.expiration = market_data["D"].index[-1]

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def contract_code(self) -> str:
        """Contract code of the instrument (e.g. 6EM2025, ESH2020)."""
        return self.reference_data.contract_code

    @property
    def type(self) -> FuturesContractType:
        """Contract type of the instrument (e.g. INDIVIDUAL, CONTINUOUS)."""
        return self.reference_data.type

    @property
    def product_code(self) -> str:
        """Product code of the instrument (e.g. 6E, ES, ZN)."""
        return self.reference_data.product_code

    @property
    def month_code(self) -> str | None:
        """Month code of the instrument (e.g. H, M, U, Z)."""
        return self.reference_data.month_code

    @property
    def activation(self) -> pd.Timestamp | None:
        """Activation date of the instrument."""
        return self.reference_data.activation

    @property
    def expiration(self) -> pd.Timestamp | None:
        """Expiration date of the instrument."""
        return self.reference_data.expiration

    @property
    def ohlc(self) -> dict[str, pd.DataFrame]:
        """OHLC data of the instrument. It may include volume and open interest."""
        return self.market_data.ohlc

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
        return f"Futures contract: {self.contract_code}"


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


# FIXME non funziona per ora
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
        market_data={"D": pd.DataFrame()},
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
