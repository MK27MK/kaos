import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

from nautilus_trader.persistence.catalog import ParquetDataCatalog

# file template
product = "E6"
month_code = "H"
year = 24
timeframe = "1day"
file_extension = ".txt"
filename = f"{product}_{month_code}{year}_{timeframe}{file_extension}"

# TODO use the same timeframe naming convention for both directory and files
sample_path = Path(os.getenv("DATA_PATH") / "csv/firstrate/indi_arch_fut_1d" / filename)
