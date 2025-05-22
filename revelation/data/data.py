import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

import pandas as pd

from revelation.data.enums import AssetClass, DataSource, FuturesContractType

# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------


class Data:
    @staticmethod
    @final
    def get_csv(path_to_file: Path, preset: dict = {}) -> pd.DataFrame:
        """
        Permette di leggere un solo file o una cartella intera di .csv
        o .txt, restituendo il/i dataframe corrispondenti.
        Consente l'utilizzo di un preset per avere dei settaggi già
        pronti.

        Per renderla più efficiente valuta anche polars.
        https://chatgpt.com/share/682defd6-4dac-8000-8a63-1211050b294d
        """
        if not path_to_file.exists():
            raise FileNotFoundError(f"Path not found: {path_to_file}")

        # ------------------------------------------------------------------
        # Copia per non mutare l'oggetto originale
        preset = {} if preset is None else preset.copy()
        tz: str | None = preset.pop("tz", None)
        out: pd.DataFrame = pd.read_csv(path_to_file, **preset)

        # localizes index if data's timezone is specified
        if tz:
            out.index = out.index.tz_localize(tz)

        return out


# class MarketData(Data):


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


class FuturesReferenceData(ReferenceData):
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
            self._RE_INDIVIDUAL
            if self.type == FuturesContractType.INDIVIDUAL
            else self._RE_CONTINUOUS
        )
        parsed = pattern.match(code)
        if not parsed:
            raise ValueError(f"Failed to parse contract code: {code}")

        self.product_code = parsed["product"]  # ex. 6E, ES, ZN

        if self.type == FuturesContractType.INDIVIDUAL:
            self.month_code = parsed["month"]  # ex. H, M, U, Z


@dataclass
class MarketData(Data):
    ohlc: dict[str, pd.DataFrame]
    # other aggregations
