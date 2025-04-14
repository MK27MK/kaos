import shutil
from decimal import Decimal
from pathlib import Path

import pandas as pd

from nautilus_trader.test_kit.providers import CSVBarDataLoader

# this will be my default data directory from now on, see if you need to
# add it to env variables or something
DATA_DIR = "/home/Downloads/data"

SAMPLE_CSV = (
    "/home/mattia-carella/Downloads/data/csv/firstrate"
    "/indi_arch_fut_1d/A6_F18_1day.txt"
)
df = CSVBarDataLoader.load(
    SAMPLE_CSV,
    0,
    header=None,
    names=["open", "high", "low", "close", "volume", "oi"],
    parse_dates=True,
)
print(df.tail())
