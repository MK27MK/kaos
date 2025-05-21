"""
This module contains reseampling functions to create timeframes.
pandas df resampling - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html#pandas.DataFrame.resample
pandas offset strings - (https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects)


Il tipo di aggregazione che mi interessa è con lo start_time della candela
incluso.
"""

import pandas as pd

# @dataclass
# class OHLCVOData(MarketData):


# open: float
# high: float
# low: float
# close: float
# volume: int
# open_interest: int


def subsample_ohlc(
    data: pd.DataFrame,
    *,
    timeframe: str,
    time_column: str | None = None,
    offset=None,
    dropna_rows: bool = True,
) -> pd.DataFrame:
    """
    they might give some problems with other timeframes, check them with TV
    label='left' means the start of the bar, doesnt change aggr, just the index time

    >>> series.resample('3min').sum()
    2000-01-01 00:00:00     3
    2000-01-01 00:03:00    12
    2000-01-01 00:06:00    21
    Freq: 3min, dtype: int64

    >>> series.resample('3min', label='right').sum()
    2000-01-01 00:03:00     3
    2000-01-01 00:06:00    12
    2000-01-01 00:09:00    21
    Freq: 3min, dtype: int64

    closed='left' changes data aggregation
    this changes fix the Weekly behaviour
    """

    sampled = data.resample(
        timeframe, label="left", closed="left", on=time_column, offset=offset
    ).agg(
        {
            # col    # func
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    return sampled
    # non considera il volume, rivedi
    return (
        sampled.dropna(subset=["open", "high", "low", "close"], how="all")
        if dropna_rows
        else sampled
    )
