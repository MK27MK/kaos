import re
from abc import abstractmethod
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Self, final

import pandas as pd

from kaos.data.enums import AssetClass, DataProvider, RolloverRule
from kaos.data.symbol import Symbol
from kaos.log_utils import get_logger

# logger config
logger = get_logger(__name__)
# ----------------------------------------------------------------------


class _CustomRegex:
    # allows an arbitrary long product name, one char for month code and
    # 2-4 chars for year
    futures_individual_contract = re.compile(
        r"^(?P<product>[A-Z0-9]+)(?P<month>[FGHJKMNQUVXZ])(?P<year>\d{2,4})$",
        re.IGNORECASE,
    )
    futures_continuous_contract = re.compile(
        r"^(?P<product>[A-Z0-9]+)(?P<series>\d+)!$",
        re.IGNORECASE,
    )


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------


class Data:
    pass


@dataclass(kw_only=True)
class ReferenceData(Data):
    """
    Reference data is metadata describing instruments and entities.
    Some examples: contract size, ticker, expiration date, increment.
    https://learning.oreilly.com/library/view/financial-data-engineering/9781098159986/
    """

    symbol: Symbol  # i.e. 6E-M-2025, ES-H-2020, 6B-1-rule
    provider: DataProvider
    asset_class: AssetClass

    @classmethod
    @abstractmethod
    def from_symbol(cls, symbol: Symbol) -> Self:
        pass


@dataclass(kw_only=True)
class FuturesReferenceData(ReferenceData):
    # ------------------------------------------------------------------
    activation: pd.Timestamp | None = None
    expiration: pd.Timestamp | None = None
    product_code: str = field(init=False)
    month_code: str | None = field(init=False, default=None)  # None if continuous

    def __post_init__(self):
        self.product_code = self.symbol.product_code
        self.month_code = self.symbol.month_code

    @classmethod
    def from_symbol(cls, symbol: Symbol) -> Self:
        # FIXME hard-coded
        return cls(
            provider=DataProvider.FIRSTRATE,
            asset_class=AssetClass.FX,
            symbol=symbol,
        )


@dataclass(kw_only=True)
class ContinuousFuturesReferenceData(ReferenceData):
    product_code: str = field(init=False)
    offset: int = field(init=False)
    rollover_rule: RolloverRule
    # adjustment: ContinuousFuturesAdjustment

    def __post_init__(self):
        self.product_code = self.symbol.product_code
        # self.offset = int(str(self.symbol).split("-")[1])


@dataclass(kw_only=True)
class MarketData(Data):
    # ohlc: dict[str, pd.DataFrame]
    # other aggregations
    pass
