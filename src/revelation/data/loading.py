from pathlib import Path

import pandas as pd


class CSVPresets:

    # Preset per i file "firstrate": niente header e potenziale colonna open_interest.
    PRESET_FIRSTRATE = dict(
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
    )


def read_text(path: str, preset: dict | None = None) -> pd.DataFrame:
    """
    Permette di leggere un solo file o una cartella intera di .csv
    o .txt, restituendo il/i dataframe corrispondenti.
    Consente l'utilizzo di un preset per avere dei settaggi già
    pronti.
    """

    # converts the str received to a path and check its existance
    path: Path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if preset is None:
        preset = {}

    # In case its a folder returns a list of dataframes
    if path.is_dir():
        data_files = list(path.glob("*.csv")) + list(path.glob("*.txt"))
        if not data_files:
            raise FileNotFoundError(f"No CSV or TXT files found in directory: {path}")

        out = [pd.read_csv(data_file, **preset) for data_file in data_files]
    else:
        # If path is a file, load the single CSV file
        out = pd.read_csv(path, **preset)

    return out
