import re
from abc import abstractmethod
from typing import Self

import pandas as pd
from numpy import roll

from kaos.analysis.time_series import is_strictly_increasing
from kaos.data.data import (
    ContinuousFuturesReferenceData,
    FuturesReferenceData,
    ReferenceData,
)
from kaos.data.enums import AssetClass, DataProvider, RolloverRule
from kaos.data.symbol import Symbol
from kaos.time_utils import MONTH_CODES, STANDARD_TIMEZONE, month_of_year

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


class FuturesContract(Instrument):

    def __init__(
        self,
        reference_data: FuturesReferenceData,
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
        # TODO make it more robust
        # In case exp and act are not provided, first and last date
        # of the index will be used instead
        # if not isinstance(self.reference_data, FuturesReferenceData):
        #     raise ValueError()
        if "D" not in market_data:
            raise KeyError("Daily timeframe is currently required.")
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
        # NOTE some products are different, ex: CAD # https://www.cmegroup.com/rulebook/CME/III/250/252/252.pdf
        # TODO validate expiry using df'last Index
        """Given expiry year and month code, returns contract's
        expiration date based on CME's criteria."""

        # retrieve expiry year and month as integers
        year_num = int(year)  # TODO handle 2-digit year
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

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def symbol(self) -> Symbol:
        """Contract code of the instrument (e.g. 6E-M-2025, ES-H-2020)."""
        return self.reference_data.symbol

    @property
    def product_code(self) -> str:
        """Product code of the instrument (e.g. 6E, ES, ZN)."""
        return self.reference_data.product_code

    # ------------------------------------------------------------------
    # methods
    # ------------------------------------------------------------------

    @classmethod
    def _roll_dates(
        contracts: list[FuturesContract], rollover_rule: RolloverRule
    ) -> list[pd.Timestamp]:
        roll_dates: list[pd.Timestamp] = []

        # iterate until penultimate, which will be shown until the end of its available data
        for i in range(len(contracts) - 1):
            curr_c: FuturesContract = contracts[i]
            next_c: FuturesContract = contracts[i + 1]

            match rollover_rule:
                case RolloverRule.EXPIRY:
                    end = curr_c.expiration
                case RolloverRule.OPEN_INTEREST:
                    end = _ts_contract_exceeds_other(curr_c, next_c)
                case _:
                    raise ValueError("This is not a valid rule.")

            roll_dates.append(end)

        return roll_dates

    @classmethod
    def _concat_individuals(
        contracts: list[FuturesContract], roll_dates: list[pd.Timestamp]
    ) -> pd.DataFrame:
        slices = []

        contracts.insert(0, contracts[0].activation)
        # TODO do it two times, one for daily and the other for 1min
        for i in range(len(roll_dates) - 1):
            start = roll_dates[i]
            end = roll_dates[i + 1]
            df = contracts[i].market_data["D"]

            slice_c = df[(df.index >= start) & (df.index < end)]
            slices.append(slice_c)
            start = end
        slices.append(contracts[-1].market_data["D"][start:])

        return pd.concat(slices)

    @classmethod
    def from_individuals(
        cls, contracts: list[FuturesContract], rollover_rule: RolloverRule
    ) -> Self:
        sort_contracts(contracts)
        # FIXME hard-coded -1-{rollover_rule.value}
        sym = Symbol(f"{contracts[0].product_code}-1-{rollover_rule.value}")
        ref = ContinuousFuturesReferenceData(
            symbol=sym,
            provider=contracts[0].provider,
            asset_class=contracts[0].asset_class,
            rollover_rule=rollover_rule,
        )
        # market_data = {tf: pd.DataFrame() for tf in contracts[0].market_data.keys()}
        roll_dates: list[pd.Timestamp] = cls._roll_dates(contracts, rollover_rule)
        concatenated: pd.DataFrame = cls._concat_individuals(contracts, roll_dates)
        market_data = ...

        # TODO move it to tests
        if not is_strictly_increasing(market_data["D"].index):
            raise ValueError(
                "Continuous index is not strictly increasing."
                "Something may be wrong in the calculation."
            )
        return cls(ref, market_data)


# class FuturesContracts:
#     def __init__(self, contracts: list[FuturesContract]):
#         self._contracts = contracts

#     def sort(self) -> None:
#         """
#         Sorts in-place a given list of Futures contracts based on product
#         code and expiration."""

#         self.contracts.sort(
#             key=lambda contract: (contract.product_code, contract.expiration)
#         )

#     @property
#     def contracts(self) -> list[FuturesContract]:
#         return self._contracts


# ----------------------------------------------------------------------
# helper functions
# ----------------------------------------------------------------------


def _ts_contract_exceeds_other(
    curr_contract: FuturesContract,
    next_contract: FuturesContract,
    column: str = "open_interest",  #  TODO list[str]?
    days_to_expiration: int = 20,
    occurrence: int = 2,  # avoids lookahead bias
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
    # TODO handle IndexError
    start = crossover[crossover].index[occurrence - 1]

    if not isinstance(start, pd.Timestamp):
        raise ValueError(f"Crossover date not found. Its value is {start}")
    return start


def sort_contracts(contracts: list[FuturesContract]) -> None:
    """
    Sorts in-place a given list of Futures contracts based on product
    code and expiration."""

    contracts.sort(key=lambda contract: (contract.product_code, contract.expiration))


# def next_timestamp(index: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp | None:
#     """Given a DateTimeIndex and a Timestamp, returns the
#     successive Timestamp.

#     O(1) if index is sorted and unique, else O(n)"""
#     if ts in index:
#         pos = index.get_loc(ts)
#         return index[pos + 1] if pos + 1 < len(index) else None
#     return None
