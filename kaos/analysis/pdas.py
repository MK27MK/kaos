from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd
from kaos.analysis.enums import GapDirection


@dataclass(kw_only=True)
class ReferencePoint(ABC):
    value: float
    timestamp: pd.Timestamp
    score: float  # between 0 and 1
    ...


@dataclass(kw_only=True)
class Pda(ReferencePoint):
    @staticmethod
    @abstractmethod
    def formed(data: pd.DataFrame) -> pd.Series:
        """True if the PDA is formed, False otherwise."""
        pass

    @abstractmethod
    def is_broken(self) -> bool:
        """True if the PDA is broken, False otherwise."""
        pass

    @abstractmethod
    def is_respected(self) -> bool:
        """True if the PDA is respected, False otherwise."""
        pass


@dataclass(kw_only=True)
class Gap(Pda):
    # NOTE potrei usare price point cosi da avere due info in un'attributo(x e y)
    gap_direction: GapDirection
    level_1: float
    level_2: float

    # NOTE le wick non vengono chiuse, valuta di considerare wick in altro modo
    def is_closed(self) -> bool:
        pass

    def is_inverted(self) -> bool:
        pass


@dataclass(kw_only=True)
class Fvg(Gap):
    @staticmethod
    def _up_formed(data: pd.DataFrame) -> pd.Series:
        return (data["low"] > data["high"].shift(2)) & (
            data["close"].shift(1) > data["open"].shift(1)
        )

    @staticmethod
    def _dn_formed(data: pd.DataFrame) -> pd.Series:
        return (data["high"] < data["low"].shift(2)) & (
            data["close"].shift(1) < data["open"].shift(1)
        )

    @staticmethod
    # FIXME rename to formations?
    def formed(data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """
        Returns:
            tuple[pd.Series, pd.Series]: A tuple of two series, the
            first one is for up gaps the second one for dn gaps.
        """
        return Fvg._up_formed(data), Fvg._dn_formed(data)
