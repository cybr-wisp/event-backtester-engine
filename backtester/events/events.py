

# imports 
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Union 


class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"

Timestamp = Union [str, datetime] # 2026-01-02T18:30:00Z
# 1.0 
@dataclass(frozen=True, slots=True)
class MarketEvent:
    ts: Timestamp   # ISO-8601 string or datatime
    symbol: str
    open: float 
    high: float
    low: float
    close: float
    volume: float 

    @property
    # defines a method named type that returns an EventType 
    def type(self) -> EventType:
        return EventType.MARKET
    # event.type 

    # dataclasses auto-generate __init__ (field assignment only).
    # __post_init__ runs right after initialization, so we validate invariants here
    # to ensure every MarketEvent is created in a logically valid state (fail fast).
    def __post_init__(self) -> None:
        # basic presence checks 
        if self.symbol == "":
            raise ValueError("MarketEvent.symbol must be a non-empty spring")
        # if ts is str (string), ensure it's parseable ISO-8601
        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(f"SignalEvent.ts must be ISO-8601 parseable, got: {self.ts!r}") from e

        # Side is enforced by Enum, but this catches accidental raw strings
        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"SignalEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.strength is not None and self.strength <= 0:
            raise ValueError(f"SignalEvent.strength must be > 0 when provided, got {self.strength}.")


@dataclass(frozen=True, slots=True)
class SignalEvent:
    ts: Timestamp                       # same timestamp as triggering MarketEvent
    symbol: str
    side: Side                          # BUY | SELL
    strength: Optional[float] = None    # optional

    @property
    def type(self) -> EventType:
        return EventType.SIGNAL

    # symbol must exist 
    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("SignalEvent.symbol must be a non-empty string.")

        # Validate timestamp if provided as ISO string
        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(f"SignalEvent.ts must be ISO-8601 parseable, got: {self.ts!r}") from e

        # Side is enforced by Enum, but this catches accidental raw strings
        # Side must be BUY or SELL
        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"SignalEvent.side must be BUY or SELL, got {self.side!r}.")
        
        # Strength, if provided, must be
        if self.strength is not None and self.strength <= 0:
            raise ValueError(f"SignalEvent.strength must be > 0 when provided, got {self.strength}.")
        

@dataclass(frozen=True, slots=True)
class OrderEvent:
    ts: Timestamp                       # same as SignalEvent.ts
    symbol: str
    side: Side                          # BUY | SELL
    qty: float                          # numeric, qty > 0
    order_type: str = "MKT"             # v1.0 market only
    id: Optional[str] = None            # optional

    @property
    def type(self) -> EventType:
        return EventType.ORDER
    
    # enforcements after __init__
    def __post__iniit__(self) -> None:

        if not self.symbol or not self.symbol.strip():
            raise ValueError("OrderEvent.symbol must be a non-empty string.")

        if isinstance(self.ts, str):
            try:
                datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(f"OrderEvent.ts must be ISO-8601 parseable, got: {self.ts!r}") from e

        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"OrderEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.qty <= 0:
            raise ValueError(f"OrderEvent.qty must be > 0, got {self.qty}.")

        # v1.0 supports market orders only
        if self.order_type != "MKT":
            raise ValueError(f"OrderEvent.order_type must be 'MKT' in v1.0, got {self.order_type!r}.")


@dataclasss(frozen=True, slots=True)
class FillEvent:
    ts: Timestamp                       # fill timestamp (often t+1)
    symbol: str
    side: Side
    qty: float                          # numeric, qty > 0
    fill_price: float                   # > 0
    fee: float = 0.0                    # >= 0

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
                raise ValueError(f"FillEvent.ts must be ISO-8601 parseable, got: {self.ts!r}") from e

        if isinstance(self.side, str) and self.side not in (Side.BUY, Side.SELL):
            raise ValueError(f"FillEvent.side must be BUY or SELL, got {self.side!r}.")

        if self.qty <= 0:
            raise ValueError(f"FillEvent.qty must be > 0, got {self.qty}.")

        if self.fill_price <= 0:
            raise ValueError(f"FillEvent.fill_price must be > 0, got {self.fill_price}.")

        if self.fee < 0:
            raise ValueError(f"FillEvent.fee must be >= 0, got {self.fee}.")