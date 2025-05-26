import os
import re
from pathlib import Path
from time import asctime
from typing import Literal, overload

import pandas as pd
from dotenv import load_dotenv

from revelation.data.data import FuturesReferenceData, ReferenceData
from revelation.data.enums import AssetClass, DataProvider, MarketDataType
from revelation.data.instruments import FuturesContract, Instrument, sort_contracts
from revelation.data.symbol import Symbol
from revelation.log_utils import get_logger

# logger config
logger = get_logger(__name__)
# ----------------------------------------------------------------------
# class Universe:
#     def __init__(self, instruments: list[Instrument]):


# FIXME forse un po a cazzo ma funziona
load_dotenv()
DATA_PATH = Path(os.getenv("DATA_PATH"))


# TODO potresti renderla interna e usare DataProvider piuttosto
class CSVPreset:
    # Preset per i file "firstrate": niente header e potenziale colonna open_interest.
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
    def __init__(self, directory: Path = DATA_PATH):
        self._directory = directory
        self._market_directory = directory / "market"
        # self._reference_directory = directory / "reference" # per ora non esiste
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

    # methods ----------------------------------------------------------

    @staticmethod
    # per ora cosi, poi implementare i metodi per prendere direttamente i dati
    def get_csv(file: Path, preset: dict = {}) -> pd.DataFrame:
        """
        Permette di leggere un solo file o una cartella intera di .csv
        o .txt, restituendo il/i dataframe corrispondenti.
        Consente l'utilizzo di un preset per avere dei settaggi già
        pronti.

        Per renderla più efficiente valuta anche polars.
        https://chatgpt.com/share/682defd6-4dac-8000-8a63-1211050b294d
        """
        if not file.exists():
            raise FileNotFoundError(f"File not found: {file}")

        # ------------------------------------------------------------------
        # Copia per non mutare l'oggetto originale
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
        """
        # select the right preset base on data provider
        preset: CSVPreset = self._get_csv_preset_from_provider(provider)

        if not is_raw_data:
            raise NotImplementedError()

        # for each tf read the corresponding csv and return a dict
        dfs: dict[str, pd.DataFrame] = {}
        for tf in timeframes:
            tf_dir: str = "1d" if tf == "1day" else "1m"
            tf_pandas: str = "D" if tf == "1day" else "1min"  # == tf
            dir = (
                self.raw_directory / provider.value / firstrate_dirname(tf_dir)
            )  # FIXME
            file = dir / f"{symbol.firstrate_string}_{tf}.txt"
            dfs[tf_pandas] = self.get_csv(file, preset)

        reference_data = FuturesReferenceData.from_symbol(symbol)
        return FuturesContract(reference_data, dfs)

    def get_futures_contracts(
        self,
        directory: Path,
        provider: DataProvider,
        pattern: re.Pattern = re.compile(r".*"),
    ) -> list[FuturesContract]:

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files: list[Path] = self._list_matching_files(directory, pattern)
        if not files:
            raise ValueError(
                f"No files found matching pattern: {pattern}"
                f"\n This is the directory: {directory}"
            )
        # logger.debug(files)
        contracts = [self.get_futures_contract(file, provider) for file in files]
        sort_contracts(contracts)
        return contracts

    # TODO deve anche poter prendere dati da raw e categorizzarli
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
        # TODO forse sorted semplice non va bene, in ogni caso la funzione fa cacare
        return sorted(
            [path for path in base.iterdir() if pattern.match(path.name)],
            key=lambda p: p.stem,
        )

    # @staticmethod
    # def _collect_files(directory: Path, symbol: str = "") -> list[Path]:
    #     """R"""
    #     csv_files = list(directory.glob(f"{symbol}*.csv"))
    #     txt_files = list(directory.glob(f"{symbol}*.txt"))
    #     return sorted(csv_files + txt_files)

    # NOTE aggiungere parametro per il tipo di strumento?
    # poi verifica con isinstance, cosi da popolare correttamente referencedata

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
    # TODO aggiungi parametro format/data provider per il formato della regex
    # in base alla sorgente
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

    print(
        catalog.get_futures_contract(
            Symbol("E6-M-2024"),
            DataProvider.FIRSTRATE,
            ["1day", "1min"],
            is_raw_data=True,
        )
    )

    contracts = catalog.get_futures_contracts(
        catalog.firstrate_directory("1m"),
        provider=DataProvider.FIRSTRATE,
        pattern=pattern,
    )
    print(*contracts, sep="\n")
    print(contracts[-1].market_data)
