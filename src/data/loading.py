from pathlib import Path
import pandas as pd


class DataLoader:
    """
    Contains methods to load data from different sources.
    """

    # Preset per i file "firstrate": niente header e potenziale colonna open_interest.
    PRESET_FIRSTRATE = {
        "header": None,  # Nessuna riga di header
        # Nomi delle colonne in ordine possibile, se presente open_interest
        "names": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "open_interest",
        ],
    }

    @staticmethod
    def read(
        path: str,
        preset: dict | None = None,
    ) -> pd.DataFrame:

        path: Path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if preset is None:
            preset = {}

        if path.is_dir():
            # If the path is a directory, load all CSV and TXT files in the directory
            data_files = list(path.glob("*.csv")) + list(path.glob("*.txt"))
            if not data_files:
                raise FileNotFoundError(
                    f"No CSV or TXT files found in directory: {path}"
                )

            # Return a list of DataFrames, one for each file
            out = [pd.read_csv(data_file, **preset) for data_file in data_files]
        else:
            # If the path is a file, load the single CSV file
            out = [pd.read_csv(path, **preset)]

        return out
