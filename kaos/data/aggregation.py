"""
This module contains resampling functions to create timeframes.

The type of aggregation I am interested in includes the start_time of the candle.
"""

import pandas as pd

# @dataclass(kw_only=True)
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
    label: str = 'right'
) -> pd.DataFrame:
    """
    they might give some problems with other timeframes, check them with TV
    label='left' means the start of the bar, doesnt change aggr, just the index time
    'right' funziona correttamente 1min -> 1D usando offset di 18h

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
        timeframe, label=label, closed="left", on=time_column, offset=offset
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
    # removes na rows since there are many times with 0 volume, so no data.
    return (
        sampled.dropna(subset=["open", "high", "low", "close"], how="all")
        if dropna_rows
        else sampled
    )
