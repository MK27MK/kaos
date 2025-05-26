import re
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self, final

import pandas as pd

from revelation.data.enums import AssetClass, DataProvider, FuturesContractType
from revelation.data.symbol import Symbol
from revelation.log_utils import get_logger

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

    # raw_symbol
    provider: DataProvider
    asset_class: AssetClass

    @classmethod
    @abstractmethod
    def from_symbol(cls, symbol: Symbol) -> Self:
        pass


@dataclass(kw_only=True)  # NOTE aggiunto adesso
class FuturesReferenceData(ReferenceData):
    # ------------------------------------------------------------------
    contract_code: str  # i.e. 6EM2025, ESH2020 TODO sostituire con raw_symbol?
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

        # assign values to the attributes skipped during init
        self.product_code = parsed["product"]  # ex. 6E, ES, ZN
        if self.type == FuturesContractType.INDIVIDUAL:
            self.month_code = parsed["month"]  # ex. H, M, U, Z

    @classmethod
    def from_symbol(cls, symbol: Symbol) -> Self:
        # FIXME implemento solo firstrate naming per ora, adottata la naming convention non sara più necessario
        # pieces: list[str] = symbol.split("_")
        # product_code = pieces[0]
        # month_code = pieces[1][0]
        # expiration_year = pieces[1][1:]  # NOTE inusato
        # timeframe = pieces[2]  # FIXME mettere il timeframe da qualche parte
        # contract_code = product_code + month_code + expiration_year
        # logger.warning(
        #     f"contract_code: {contract_code} va sistemato,"
        #     "va adottato lo standard a 4 cifre per la data, e la regex va aggiornata."
        # )
        return cls(
            provider=DataProvider.FIRSTRATE,
            asset_class=AssetClass.FX,
            contract_code=symbol,
            type=FuturesContractType.INDIVIDUAL,
        )


@dataclass(kw_only=True)
class MarketData(Data):
    # ohlc: dict[str, pd.DataFrame]
    # other aggregations
    pass
