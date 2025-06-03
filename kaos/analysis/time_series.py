import pandas as pd

# index functions ------------------------------------------------------


def _get_index(pandas_object) -> pd.Index:
    idx = pandas_object
    if isinstance(pandas_object, (pd.DataFrame, pd.Series)):
        idx = pandas_object.index
    return idx


def is_strictly_increasing(pandas_object: pd.Index | pd.DataFrame | pd.Series) -> bool:
    idx = _get_index(pandas_object)
    return idx.is_monotonic_increasing and idx.is_unique


def intersection(
    pandas_object: pd.Index | pd.DataFrame | pd.Series,
    other: pd.Index | pd.DataFrame | pd.Series,
) -> pd.Index:
    idx = _get_index(pandas_object)
    idx_other = _get_index(other)
    return idx.intersection(idx_other)


def symmetric_difference(
    pandas_object: pd.Index | pd.DataFrame | pd.Series,
    other: pd.Index | pd.DataFrame | pd.Series,
) -> pd.Index:
    idx = _get_index(pandas_object)
    idx_other = _get_index(other)
    return idx.symmetric_difference(idx_other)
