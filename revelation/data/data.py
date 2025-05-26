import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

import pandas as pd

from revelation.data.enums import AssetClass, DataSource, FuturesContractType


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


@dataclass
class ReferenceData(Data):
    """
    Reference data is metadata describing instruments and entities.
    Some examples: contract size, ticker, expiration date, increment.
    https://learning.oreilly.com/library/view/financial-data-engineering/9781098159986/
    """

    source: DataSource
    asset_class: AssetClass


@dataclass  # NOTE aggiunto adesso
class FuturesReferenceData(ReferenceData):
    # ------------------------------------------------------------------
    contract_code: str  # i.e. 6EM2025, ESH2020
    type: FuturesContractType = FuturesContractType.INDIVIDUAL
    activation: pd.Timestamp | None = None
    expiration: pd.Timestamp | None = None
    product_code: str = field(init=False)
    month_code: str | None = field(init=False, default=None)  # None if continuous

    def __post_init__(self):
        # TODO aggiungi logica di differenziazione individual e continuous
        # contract code parsing
        code = self.contract_code.upper()
        pattern = (
            _CustomRegex.futures_individual_contract
            if self.type == FuturesContractType.INDIVIDUAL
            else _CustomRegex.futures_continuous_contract
        )
        parsed = pattern.match(code)
        if not parsed:
            raise ValueError(f"Failed to parse contract code: {code}")

        self.product_code = parsed["product"]  # ex. 6E, ES, ZN

        if self.type == FuturesContractType.INDIVIDUAL:
            self.month_code = parsed["month"]  # ex. H, M, U, Z


@dataclass
class MarketData(Data):
    # ohlc: dict[str, pd.DataFrame]
    # other aggregations
    pass
