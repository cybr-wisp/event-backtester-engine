

# imrports 
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"


@dataclass(frozen=True, slots=True)
class MarketEvent:
    symbol: str
    bar_index: Optional[int] = None

    @property
    def type(self) -> EventType:
        return EventType.MARKET


@dataclass(frozen=True, slots=True)
class SignalEvent:
    symbol: str
    direction: str  # "LONG" | "SHORT"

    @property
    def type(self) -> EventType:
        return EventType.SIGNAL


@dataclass(frozen=True, slots=True)
class OrderEvent:
    symbol: str
    side: str  # "BUY" | "SELL"
    quantity: int

    @property
    def type(self) -> EventType:
        return EventType.ORDER


@dataclass(frozen=True, slots=True)
class FillEvent:
    symbol: str
    side: str  # "BUY" | "SELL"
    quantity: int
    fill_price: float

    @property
    def type(self) -> EventType:
        return EventType.FILL
