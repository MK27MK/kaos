import os
import re
from pathlib import Path
from time import asctime
from typing import Literal, overload

import pandas as pd
from dotenv import load_dotenv

from kaos.data.data import FuturesReferenceData, ReferenceData
from kaos.data.enums import AssetClass, DataProvider, MarketDataType
from kaos.data.instruments import FuturesContract, Instrument, sort_contracts
from kaos.data.symbol import Symbol
from kaos.log_utils import get_logger

# logger config
logger = get_logger(__name__)
# ----------------------------------------------------------------------
# class Universe:
#     def __init__(self, instruments: list[Instrument]):


# TODO merge it with DataProvider, making it a class instead of an enum
class CSVPreset:
    # Preset "firstrate": no header and possible open_interest column
    FIRSTRATE = dict(
        header=None,
        names=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "open_interest",
        ],
        parse_dates=["timestamp"],
        index_col="timestamp",
        tz="America/New_York",
        # All data is in US Eastern Timezone (ie EST/EDT depending
        # on the time of year) except for crypto data which is in UTC.
        # https://firstratedata.com/about/FAQ
    )


# ----------------------------------------------------------------------
# Catalog
# ----------------------------------------------------------------------

"6E-M-2024.CME"
"{product_code}-{month_code}-{year}-{multiplier}"


class Catalog:
    def __init__(self, directory: Path = Path("~/data").expanduser()):
        self._directory = directory
        self._market_directory = directory / "market"
        # self._reference_directory = directory / "reference" # NOTE might not need it
        # put the reference data in the market directory? create a link to it?
        self._fundamental_directory = directory / "fundamental"
        self._raw_directory = directory / "raw"

    # properties -------------------------------------------------------

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def market_directory(self) -> Path:
        return self._market_directory

    @property
    def fundamental_directory(self) -> Path:
        return self._fundamental_directory

    @property
    def raw_directory(self) -> Path:
        return self._raw_directory

    # ------------------------------------------------------------------
    # methods
    # ------------------------------------------------------------------

    @staticmethod
    def get_csv(file: Path, preset: dict = {}) -> pd.DataFrame:
        """
        Reads a single .csv/.txt file and returns the corresponding DataFrame.
        Allows the use of a preset for ready-made settings.

        For improved performance with large files, consider using polars.
        """
        if not file.exists():
            raise FileNotFoundError(f"File not found: {file}")

        # ------------------------------------------------------------------
        # creates a copy instead of changing the original object
        preset = {} if preset is None else preset.copy()
        tz: str | None = preset.pop("tz", None)
        out: pd.DataFrame = pd.read_csv(file, **preset)

        # localizes index if data's timezone is specified
        if tz:
            out.index = out.index.tz_localize(tz)

        return out

    def get_csvs(
        self,
        directory: Path,
        preset: dict = {},
        pattern: re.Pattern = re.compile(r".*"),
    ) -> tuple[pd.DataFrame]:

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files: list[Path] = self._list_matching_files(directory, pattern)
        if not files:
            print(f"No files found matching pattern: {pattern}")

        return tuple(self.get_csv(file, preset) for file in files)

    def get_futures_contract(
        self,
        symbol: Symbol,
        provider: DataProvider,
        timeframes: list[str],
        is_raw_data: bool,
    ) -> FuturesContract:
        """
        Generates a FuturesContract object, allowing for multiple
        timeframes.
        Rn use 1day and 1min ad tfs
        """
        # select the right preset base on data provider
        preset: CSVPreset = self._get_csv_preset_from_provider(provider)

        if not is_raw_data:
            raise NotImplementedError()

        # for each tf read the corresponding csv and return a dict
        dfs: dict[str, pd.DataFrame] = {}
        for tf in timeframes:
            tf_pandas, file = self._path_in_raw_data(symbol, provider, tf)
            dfs[tf_pandas] = self.get_csv(file, preset)
            # create symbol column, useful for continuous contracts, NOTE: consider moving this elsewhere
            dfs[tf_pandas].insert(0, "symbol", value=(symbol))

        reference_data = FuturesReferenceData.from_symbol(symbol)
        return FuturesContract(reference_data, dfs)

    def get_futures_contracts(
        self,
        symbols: list[Symbol],
        provider: DataProvider,
        timeframes: list[str],
        is_raw_data: bool,
    ) -> list[FuturesContract]:
        """Rn use 1day and 1min ad tfs"""

        if not is_raw_data:
            raise NotImplementedError()
        # logger.debug(files)
        contracts = [
            self.get_futures_contract(symbol, provider, timeframes, is_raw_data)
            for symbol in symbols
        ]
        sort_contracts(contracts)
        return contracts

    # @staticmethod
    # get_tradingview(symbol: str, timeframe)

    # TODO: should also be able to fetch data from raw and categorize it
    def write(self):
        pass

    # private methods --------------------------------------------------

    # def _get_timeframes(self, timeframes: list[str]) -> dict[str, pd.DataFrame]:
    @staticmethod
    def _get_csv_preset_from_provider(provider: DataProvider) -> CSVPreset:
        match provider:
            case DataProvider.FIRSTRATE:
                preset = CSVPreset.FIRSTRATE
            case _:
                raise ValueError(f"Unhandled data provider: {provider}")

        return preset

    @staticmethod
    def _list_matching_files(directory: Path, pattern: re.Pattern) -> list[Path]:
        base = Path(directory).expanduser().resolve()
        return sorted(
            [path for path in base.iterdir() if pattern.match(path.name)],
            key=lambda p: p.stem,
        )

    def _path_in_raw_data(self, symbol: Symbol, provider: DataProvider, timeframe: str):
        dir = self.raw_directory / provider.value
        daily_aliases = ("1day", "1d", "d")
        tf_pandas: str = "D" if timeframe.lower() in daily_aliases else "1min"  # == tf

        if provider == DataProvider.FIRSTRATE:
            tf_dir: str = "1d" if timeframe.lower() in daily_aliases else "1m"
            dir /= firstrate_dirname(tf_dir)
        file = dir / f"{symbol.firstrate_string}_{timeframe}.txt"
        return tf_pandas, file

    # @staticmethod
    # def _collect_files(directory: Path, symbol: str = "") -> list[Path]:
    #     """R"""
    #     csv_files = list(directory.glob(f"{symbol}*.csv"))
    #     txt_files = list(directory.glob(f"{symbol}*.txt"))
    #     return sorted(csv_files + txt_files)

    def firstrate_directory(self, timeframe: Literal["1d", "1m"]) -> Path:
        return self.raw_directory / "csv/firstrate" / firstrate_dirname(timeframe)


# ----------------------------------------------------------------------
# functions
# ----------------------------------------------------------------------


def regex_pattern(
    symbols: list[str],
    years: list[int],
    month_codes: str,
) -> re.Pattern:
    # TODO add a parameter for format/data provider to adjust the regex format
    # based on the data source
    sym = "|".join(map(re.escape, symbols))
    year = "|".join(f"{y:02d}" for y in years)
    month = f"[{re.escape(month_codes)}]"

    pattern = rf"^({sym})_({month})({year}).*"

    return re.compile(pattern, re.IGNORECASE)


def firstrate_dirname(timeframe: Literal["1d", "1m"]) -> str:
    dirname = f"indi_arch_fut_{timeframe}"
    return dirname


def firstrate_filename(
    product: str = "E6",
    month_code: str = "H",
    year: int = 2024,
    timeframe: Literal["1d", "1m"] = "1d",
    extension: str = ".txt",
) -> str:
    filename = f"{product}_{month_code}{year % 2000}_{timeframe}{extension}"
    return filename


# ----------------------------------------------------------------------
# demonstration
# ----------------------------------------------------------------------


if __name__ == "__main__":
    catalog = Catalog()
    pattern = regex_pattern(symbols=["E6", "NQ"], years=[23, 24], month_codes="HMUZ")
    timeframes = ["1day", "1min"]
    es_hmuz_2020 = [Symbol(f"ES-{m}-2020") for m in "HMUZ"]

    print(
        catalog.get_futures_contract(
            Symbol("E6-M-2024"),
            DataProvider.FIRSTRATE,
            timeframes,
            is_raw_data=True,
        )
    )

    contracts = catalog.get_futures_contracts(
        es_hmuz_2020,
        provider=DataProvider.FIRSTRATE,
        timeframes=timeframes,
        is_raw_data=True,
    )
    print(*contracts, sep="\n")
