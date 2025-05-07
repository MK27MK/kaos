from datetime import datetime, timedelta
from enum import IntEnum

import pandas as pd

# ----------------------------------------------------------------------
# constants and enums
# ----------------------------------------------------------------------


MONTH_CODES = "FGHJKMNQUVXZ"
STANDARD_TIMEZONE = "UTC"


class DayOfWeek(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class WeekOfMonth(IntEnum):
    FIRST = 0
    SECOND = 1
    THIRD = 2
    FOURTH = 3


# ----------------------------------------------------------------------
# functions
# ----------------------------------------------------------------------


def month_of_year(month_code: str) -> int:
    """Given a futures month code, returns an int between 1 and 12
    representing the month of the year."""
    code_to_month = dict(zip(MONTH_CODES, range(1, 13)))

    try:
        return code_to_month[month_code.upper()]
    except KeyError:
        raise ValueError(
            f"Invalid month code: {month_code!r}. Must be one of {list(code_to_month.keys())}"
        )


def nth_weekday_of_month(
    year: int, month: int, weekday: DayOfWeek, week_num: WeekOfMonth
) -> pd.Timestamp:
    """Given the parameters returns the nth occurrence (4th max) of the
    specified day of week.

    NOTE any given day may occur 5 times in a month, this function handles
    up to the forth occurrence.
    """

    if weekday not in range(7):
        raise ValueError("WeekDay must be between 0-6")
    if not 0 <= week_num <= 3:
        raise ValueError("week_num must be between 0 and 3(included).")

    # ------------------------------------------------------------------
    first_of_month = pd.Timestamp(year=year, month=month, day=1, tz=STANDARD_TIMEZONE)
    return first_of_month + pd.offsets.WeekOfMonth(n=1, weekday=weekday, week=week_num)
