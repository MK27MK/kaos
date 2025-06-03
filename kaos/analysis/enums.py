from enum import IntEnum, auto, unique


@unique
class GapDirection(IntEnum):
    UP = auto()
    DN = auto()
