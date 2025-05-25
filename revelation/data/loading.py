import os
import re
from pathlib import Path
from typing import Literal, overload

import pandas as pd
from dotenv import load_dotenv

from revelation.data.enums import MarketDataType

# class Universe:
#     def __init__(self, instruments: list[Instrument]):


# FIXME forse un po a cazzo ma funziona
load_dotenv()
DATA_PATH = Path(os.getenv("DATA_PATH"))


class CSVPresets:
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

    @overload
    def get_csvs(
        self,
        directory: Path,
        preset: dict = {},
    ) -> tuple[pd.DataFrame]: ...

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

    # @staticmethod
    # def _collect_files(directory: Path, symbol: str = "") -> list[Path]:
    #     """R"""
    #     csv_files = list(directory.glob(f"{symbol}*.csv"))
    #     txt_files = list(directory.glob(f"{symbol}*.txt"))
    #     return sorted(csv_files + txt_files)

    @staticmethod
    def _list_matching_files(directory: Path, pattern: re.Pattern) -> list[Path]:
        base = Path(directory).expanduser().resolve()
        return [path for path in base.iterdir() if pattern.match(path.name)]


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
    # TODO aggiungi parametro format/data source per il formato della regex
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


if __name__ == "__main__":
    catalog = Catalog()
    pattern = regex_pattern(
        symbols=["E6", "NQ"],
        years=[24],
        month_codes="HMUZ",
    )

    dfs = catalog.get_csvs(
        catalog._raw_directory / "csv/firstrate" / firstrate_dirname(resolution="m"),
        preset=CSVPresets.FIRSTRATE,
        pattern=pattern,
    )
    for df in dfs:
        print(df.head())
