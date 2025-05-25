from enum import IntEnum, auto, unique

# TODO considera di creare una BaseEnum

# time -----------------------------------------------------------------


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
class MonthOfYear(IntEnum):
    pass


# data -----------------------------------------------------------------


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
class Sector(IntEnum):
    # FOOD
    # FINANCE ...
    pass


@unique
class DataSource(IntEnum):
    FIRSTRATE = auto()
    TRADINGVIEW = auto()
    DATABENTO = auto()


@unique
class RolloverRule(IntEnum):
    EXPIRY = auto()
    OPEN_INTEREST = auto()


@unique
class FuturesContractType(IntEnum):
    INDIVIDUAL = auto()
    CONTINUOUS = auto()


@unique
class MarketDataType(IntEnum):
    OHLC = auto()
    TICK = auto()


# position -------------------------------------------------------------


@unique
class PositionSide(IntEnum):
    # NONE = auto()
    BUY = auto()
    SELL = auto()
