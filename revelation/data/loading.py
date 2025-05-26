import os
import re
from pathlib import Path
from time import asctime
from typing import Literal, overload

import pandas as pd
from dotenv import load_dotenv

from revelation.data.data import FuturesReferenceData, ReferenceData
from revelation.data.enums import AssetClass, DataSource, MarketDataType
from revelation.data.instruments import FuturesContract, Instrument, sort_contracts
from revelation.log_utils import get_logger

# logger config
logger = get_logger(__name__)
# ----------------------------------------------------------------------
# class Universe:
#     def __init__(self, instruments: list[Instrument]):


# FIXME forse un po a cazzo ma funziona
load_dotenv()
DATA_PATH = Path(os.getenv("DATA_PATH"))


# TODO potresti renderla interna e usare DataSource piuttosto
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


class Catalog:
    def __init__(self, directory: Path = DATA_PATH):
        self._directory = directory
        self._market_directory = directory / "market"
        # self._reference_directory = directory / "reference" # per ora non esiste
        # put the reference data in the market directory? create a link to it?
        self._fundamental_directory = directory / "fundamental"
        self._raw_directory = directory / "raw"

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
        self, file: Path, data_source: DataSource
    ) -> FuturesContract:

        # select the right preset base on data data_source
        preset = self._get_csv_preset_from_data_source(data_source)

        df = self.get_csv(file, preset)
        reference_data = FuturesReferenceData.from_string(file.stem)
        timeframe: str = "D" if "1day" in file.stem else "1min"  # FIXME
        return FuturesContract(reference_data, {timeframe: df})

    def get_futures_contracts(
        self,
        directory: Path,
        data_source: DataSource,
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
        contracts = [self.get_futures_contract(file, data_source) for file in files]
        sort_contracts(contracts)
        return contracts

    # TODO deve anche poter prendere dati da raw e categorizzarli
    def write(self):
        pass

    # private methods --------------------------------------------------

    @staticmethod
    def _get_csv_preset_from_data_source(data_source: DataSource) -> CSVPreset:
        match data_source:
            case DataSource.FIRSTRATE:
                preset = CSVPreset.FIRSTRATE
            case _:
                raise ValueError(f"Unhandled data data_source: {data_source}")

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


# ----------------------------------------------------------------------
# functions
# ----------------------------------------------------------------------


def regex_pattern(
    symbols: list[str],
    years: list[int],
    month_codes: str,
    extension: list[str] = [".csv", ".txt"],
    timeframe: str = "1min",
) -> re.Pattern:
    # TODO aggiungi parametro format/data data_source per il formato della regex
    # in base alla sorgente
    sym = "|".join(map(re.escape, symbols))
    year = "|".join(f"{y:02d}" for y in years)
    month = f"[{re.escape(month_codes)}]"
    ext = "|".join(ext.lstrip(".").lower() for ext in extension)

    pattern = rf"^({sym})_({month})({year})_({timeframe})\.({ext})$"
    return re.compile(pattern, re.IGNORECASE)


def firstrate_dirname(
    multiplier: str = "1", resolution: Literal["d", "m"] = "d"
) -> str:
    dirname = f"indi_arch_fut_{multiplier}{resolution}"
    return dirname


def firstrate_filename(
    product: str = "E6",
    month_code: str = "H",
    year: int = 2024,
    multiplier: str = "1",
    resolution: str = "day",
    extension: str = ".txt",
) -> str:
    filename = (
        f"{product}_{month_code}{year % 2000}_{multiplier}{resolution}{extension}"
    )
    return filename


# ----------------------------------------------------------------------
# demonstration
# ----------------------------------------------------------------------


if __name__ == "__main__":
    catalog = Catalog()
    pattern = regex_pattern(
        symbols=["E6"], years=[24], month_codes="HMUZ", timeframe="1day"
    )
    daily_dir = (
        catalog._raw_directory / "csv/firstrate" / firstrate_dirname(resolution="d")
    )

    print(
        catalog.get_futures_contract(
            daily_dir / firstrate_filename(), DataSource.FIRSTRATE
        )
    )
    dfs = catalog.get_futures_contracts(
        daily_dir,
        data_source=DataSource.FIRSTRATE,
        pattern=pattern,
    )
    print(dfs)
    # for df in dfs:
    #     print(df.head())
