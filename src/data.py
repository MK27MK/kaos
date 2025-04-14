from pathlib import Path
import pandas as pd


class DataLoader:
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
        # target_format: str = "dataframe",
        preset: dict | None = None,
    ) -> pd.DataFrame:

        path: Path = Path(path)
        # symlink?
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        # empty preset if not specified
        if preset is None:
            preset = {}
        # if path.is_dir():  # TODO
        #     return

        # if target_format == "dataframe":
        out = pd.read_csv(
            path,
            **preset,
            # TODO kwargs
        )
        return out


class Instrument:
    # per ora lo lascio vuoto
    def __init__(self, sector):
        pass


class FuturesContract(Instrument):
    def __init__(
        self,
        sector,
        start_date,
        settlement_date,
    ):
        # gestisci l'ereditarieta
        super().__init__(sector)
        self.start_date = start_date
        self.settlement_date = settlement_date
        # etc


# I may actually use a list[Instrument]
# avere un unico time index anziche 3 mila tabelle
class Universe:
    pass


# devo avere la timeline dei contratti allineati per bene per strumento,
# bisogna gestire il rollover
