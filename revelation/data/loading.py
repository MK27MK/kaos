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
