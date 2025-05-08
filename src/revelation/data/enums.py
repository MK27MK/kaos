from enum import IntEnum, unique


@unique
class DayOfWeek(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


@unique
class WeekOfMonth(IntEnum):
    FIRST = 0
    SECOND = 1
    THIRD = 2
    FOURTH = 3


@unique
class AssetClass(IntEnum):
    FX = 1
    EQUITY = 2  # STOCK
    COMMODITY = 3
    # DEBT = 4
    INDEX = 5
    CRYPTOCURRENCY = 6
    # ALTERNATIVE = 7
