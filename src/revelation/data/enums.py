from enum import IntEnum, auto, unique


@unique
class DayOfWeek(IntEnum):
    MON = 0
    TUE = auto()
    WED = auto()
    THU = auto()
    FRI = auto()
    SAT = auto()
    SUN = auto()


@unique
class WeekOfMonth(IntEnum):
    FIRST = 0
    SECOND = auto()
    THIRD = auto()
    FOURTH = auto()


@unique
class AssetClass(IntEnum):
    FX = auto()
    EQUITY = auto()  # STOCK
    COMMODITY = auto()
    # DEBT =auto()
    INDEX = auto()
    CRYPTOCURRENCY = auto()
    # ALTERNATIVE =auto()


@unique
class RolloverRule(IntEnum):
    EXPIRY = auto()
    OPEN_INTEREST = auto()


@unique
class FuturesContractType(IntEnum):
    INDIVIDUAL = auto()
    CONTINUOUS = auto()
