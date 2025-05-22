import os
from pathlib import Path
from typing import Literal

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


def _collect_files(directory: Path) -> list[Path]:
    """Restituisce tutti i .csv e .txt presenti nella dir (non ricorsivo)."""
    csv_files = list(directory.glob("*.csv"))
    txt_files = list(directory.glob("*.txt"))
    return sorted(csv_files + txt_files)


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
