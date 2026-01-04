# events.py

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Union


class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"


Timestamp = Union[str, datetime]  # e.g. "2026-01-02T18:30:00Z"


@dataclass(frozen=True, slots=True)
class MarketEvent:
    ts: Timestamp   # ISO-8601 string or datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def type(self) -> EventType:
        return EventType.MARKET

    def __post_init__(self) -> None:
        if self.symbol == "":
            raise ValueError("MarketEvent.symbol must be a non-empty string")

        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                # ✅ FIX: correct class name in error message
                raise ValueError(
                    f"MarketEvent.ts must be ISO-8601 parseable, got: {self.ts!r}"
                ) from e


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class SignalEvent:
    ts: Timestamp
    symbol: str
    side: Side
    strength: Optional[float] = None

    @property
    def type(self) -> EventType:
        return EventType.SIGNAL

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("SignalEvent.symbol must be a non-empty string.")

        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(
                    f"SignalEvent.ts must be ISO-8601 parseable, got: {self.ts!r}"
                ) from e

        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"SignalEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.strength is not None and self.strength <= 0:
            raise ValueError(
                f"SignalEvent.strength must be > 0 when provided, got {self.strength}."
            )


@dataclass(frozen=True, slots=True)
class OrderEvent:
    ts: Timestamp
    symbol: str
    side: Side
    qty: float
    order_type: str = "MKT"  # v1.0 market only
    id: Optional[str] = None

    @property
    def type(self) -> EventType:
        return EventType.ORDER

    # ✅ FIX: must be __post_init__ (not __post__init__)
    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("OrderEvent.symbol must be a non-empty string.")

        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(
                    f"OrderEvent.ts must be ISO-8601 parseable, got: {self.ts!r}"
                ) from e

        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"OrderEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.qty <= 0:
            raise ValueError(f"OrderEvent.qty must be > 0, got {self.qty}.")

        if self.order_type != "MKT":
            raise ValueError(
                f"OrderEvent.order_type must be 'MKT' in v1.0, got {self.order_type!r}."
            )


@dataclass(frozen=True, slots=True)
class FillEvent:
    ts: Timestamp
    symbol: str
    side: Side
    qty: float
    fill_price: float
    fee: float = 0.0

    @property
    def type(self) -> EventType:
        return EventType.FILL

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("FillEvent.symbol must be a non-empty string.")

        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(
                    f"FillEvent.ts must be ISO-8601 parseable, got: {self.ts!r}"
                ) from e

        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"FillEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.qty <= 0:
            raise ValueError(f"FillEvent.qty must be > 0, got {self.qty}.")

        if self.fill_price <= 0:
            raise ValueError(f"FillEvent.fill_price must be > 0, got {self.fill_price}.")

        if self.fee < 0:
            raise ValueError(f"FillEvent.fee must be >= 0, got {self.fee}.")
