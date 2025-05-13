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

    out = pd.read_csv(path, **preset)

    return out
