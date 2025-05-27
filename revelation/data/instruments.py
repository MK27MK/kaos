import re
from abc import abstractmethod
from typing import Self

import pandas as pd

from revelation.data.data import (
    ContinuousFuturesReferenceData,
    FuturesReferenceData,
    ReferenceData,
)
from revelation.data.enums import AssetClass, DataProvider, RolloverRule
from revelation.data.symbol import Symbol
from revelation.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

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
    def provider(self) -> DataProvider:
        """Source of the instrument's market data."""
        return self.reference_data.provider


# FuturesContract ------------------------------------------------------


# TODO separa continyous e individual
# NOTE continuous sono dati sintetici, valuta separazione classi
class FuturesContract(Instrument):

    def __init__(
        self,
        reference_data: FuturesReferenceData,
        # NOTE daily obbligatori per il funzionamento attualmente
        market_data: dict[str, pd.DataFrame],
    ):
        """If reference data does not provide activation and expiration dates,
        the first and last date of the index will be used instead.

        Args:
            reference_data (FuturesReferenceData): _description_
            market_data (dict[str, pd.DataFrame]): _description_
        """
        super().__init__(reference_data, market_data)

        # activation and expiration ------------------------------------
        # TODO rendi piu robusto
        # In case exp and act are not provided, first and last date
        # of the index will be used instead
        # if not isinstance(self.reference_data, FuturesReferenceData):
        #     raise ValueError()
        if "D" not in market_data:
            raise KeyError("Daily timeframe is required.")
        if self.activation is None:
            self.reference_data.activation = market_data["D"].index[0]
        if self.expiration is None:
            self.reference_data.expiration = market_data["D"].index[-1]

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def symbol(self) -> Symbol:
        """Contract code of the instrument (e.g. 6E-M-2025, ES-H-2020)."""
        return self.reference_data.symbol

    # @property
    # def type(self) -> FuturesContractType:
    #     """Contract type of the instrument (e.g. INDIVIDUAL, CONTINUOUS)."""
    #     return self.reference_data.type

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

    # @property
    # def ohlc(self) -> dict[str, pd.DataFrame]:
    #     """OHLC data of the instrument. It may include volume and open interest."""
    #     return self.market_data.ohlc

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
        return f"Futures contract: {self.symbol}"


class ContinuousFuturesContract(Instrument):

    def __init__(
        self,
        reference_data: ContinuousFuturesReferenceData,
        # NOTE dovrei avere contracts cokme parametro?
        market_data: dict[str, pd.DataFrame],
    ):
        super().__init__(reference_data, market_data)

    @classmethod
    def from_individuals(
        cls, contracts: list[FuturesContract], rollover_rule: RolloverRule
    ) -> Self:
        sort_contracts(contracts)
        # FIXME hard-coded e precario -1-{rollover_rule}
        sym = Symbol(f"{contracts[0].product_code}-1-{rollover_rule}")
        ref = ContinuousFuturesReferenceData(
            symbol=sym,
            provider=contracts[0].provider,
            asset_class=contracts[0].asset_class,
            rollover_rule=rollover_rule,
        )
        market_data = {tf: pd.DataFrame() for tf in contracts[0].market_data.keys()}

        # the continuous starts from the beginning of the first contract
        start: pd.Timestamp = contracts[0].activation

        for i in range(len(contracts)):
            curr: FuturesContract = contracts[i]
            df = curr.market_data["D"]
            if i != 0:
                prev: FuturesContract = contracts[i - 1]

            match rollover_rule:
                case RolloverRule.EXPIRY:
                    if i != 0:
                        start = prev.expiration
                    # from the expiration day of the previous until the day prior
                    # the expiration of this one
                    slice = df[(df.index >= start) & (df.index < curr.expiration)]
                case RolloverRule.OPEN_INTEREST:
                    if i == 0:
                        continue
                    # crossover day, excluded
                    end = _ts_next_exceeds_curr(prev, curr)
                    slice = df[(df.index >= start) & (df.index <= end)]
                    start = end
                    
                case _:
                    raise ValueError("This is not a valid rule.")
            # finally perform the concatenation
            # TODO vedi come mettere 1 min data
            market_data["D"] = pd.concat([market_data["D"], slice])
        return cls(ref, market_data)


class FuturesContracts:
    def __init__(self, contracts: list[FuturesContract]):
        self._contracts = contracts

    def sort(self) -> None:
        """
        Sorts in-place a given list of Futures contracts based on product
        code and expiration."""

        self.contracts.sort(
            key=lambda contract: (contract.product_code, contract.expiration)
        )

    @property
    def contracts(self) -> list[FuturesContract]:
        return self._contracts


# ----------------------------------------------------------------------
# helper functions
# ----------------------------------------------------------------------


def _ts_next_exceeds_curr(
    curr_contract: FuturesContract,
    next_contract: FuturesContract,
    column: str = "open_interest",  #  TODO lista di colonne?
    days_to_expiration: int = 20,
) -> pd.Timestamp:
    curr_df: pd.DataFrame = curr_contract.market_data["D"]
    df: pd.DataFrame = next_contract.market_data["D"]

    # get a df comparing column inside index intersection of the two contracts
    # I take the last portion tu filter possible fakeouts
    _curr, _next = "_curr", "_next"
    oi_both = curr_df[[column]].join(
        df[[column]], lsuffix=_curr, rsuffix=_next, how="inner"
    )[-days_to_expiration:]

    crossover: pd.Series = oi_both[column + _next] > oi_both[column + _curr]
    start = crossover.idxmax()

    if not isinstance(start, pd.Timestamp):
        raise ValueError(f"Crossover date not found. Its value is {start}")
    return start


def sort_contracts(contracts: list[FuturesContract]) -> None:
    """
    Sorts in-place a given list of Futures contracts based on product
    code and expiration."""

    contracts.sort(key=lambda contract: (contract.product_code, contract.expiration))


def next_timestamp(index: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp | None:
    """Given a DateTimeIndex and a Timestamp, returns the
    successive Timestamp.

    O(1) if index is sorted and unique, else O(n)"""
    if ts in index:
        pos = index.get_loc(ts)
        return index[pos + 1] if pos + 1 < len(index) else None
    return None


# FIXME non funziona per ora
# TODO mettilo nella clase futurescontract come "continuous_from_list"
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
    ref = FuturesReferenceData(contracts)

    continuous: FuturesContract = FuturesContract(
        reference_data=contracts[0].reference_data,
        market_data={"D": pd.DataFrame()},
    )
    # NOTE considera si spostare `start_date` qui
    # dont loop over last contract bc its concatenated by previous loop
    for i in range(len(contracts) - 1):
        curr: FuturesContract = contracts[i]
        next: FuturesContract = contracts[i + 1]

        match rollover_rule:
            case RolloverRule.EXPIRY:
                # finds the index immediately after curr.expiration
                start_date: pd.Timestamp = (
                    next_timestamp(next.market_data["D"].index, curr.expiration)
                    if i != 0  # start from the beginning of the first contract
                    else curr.activation
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
