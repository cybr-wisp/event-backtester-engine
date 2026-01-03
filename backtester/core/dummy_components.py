# backtester/dummy_components.py

from __future__ import annotations

from datetime import datetime, timezone

from backtester.core.event_queue import EventQueue
from backtester.events import MarketEvent, SignalEvent, OrderEvent, FillEvent


class DummyDataHandler:
    """
    Emits valid MarketEvent bars (OHLCV + ts) into the event queue.
    """

    def __init__(self, events: EventQueue, symbol: str = "SPY") -> None:
        self.events = events
        self.symbol = symbol

    def stream_next(self, i: int) -> None:
        # Deterministic dummy bar (respects MarketEvent constraints)
        ts = datetime.now(timezone.utc).isoformat()

        close = 100.0 + float(i)
        open_ = close
        high = close + 1.0
        low = close - 1.0
        volume = 1000.0

        self.events.put(
            MarketEvent(
                ts=ts,
                symbol=self.symbol,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )


class DummyStrategy:
    """
    Consumes MarketEvent and emits SignalEvent.
    Emits BUY/SELL alternating to prove both paths work.
    """

    def __init__(self, events: EventQueue) -> None:
        self.events = events

    def on_market(self, event: MarketEvent) -> None:
        # Simple alternating rule for Day 2
        side = "BUY" if int(event.close) % 2 == 0 else "SELL"
        self.events.put(SignalEvent(ts=event.ts, symbol=event.symbol, side=side))


class DummyExecutionHandler:
    """
    Consumes SignalEvent -> emits OrderEvent (MKT only) -> emits FillEvent.
    Uses last seen MarketEvent.close as the fill price (dummy).
    """

    def __init__(self, events: EventQueue, qty: float = 10.0, fee: float = 1.0) -> None:
        self.events = events
        self.qty = qty
        self.fee = fee
        self.last_price: float = 100.0

    def on_market(self, event: MarketEvent) -> None:
        self.last_price = event.close

    def on_signal(self, event: SignalEvent) -> None:
        # Signal -> Order
        self.events.put(
            OrderEvent(
                ts=event.ts,
                symbol=event.symbol,
                side=event.side,
                qty=self.qty,
                order_type="MKT",
            )
        )

    def on_order(self, event: OrderEvent) -> None:
        # Order -> Fill (dummy immediate fill for Day 2)
        self.events.put(
            FillEvent(
                ts=event.ts,
                symbol=event.symbol,
                side=event.side,
                qty=event.qty,
                fill_price=self.last_price,
                fee=self.fee,
            )
        )


class Portfolio:
    """
    Consumes FillEvent and updates cash/positions (very simple accounting).
    """

    def __init__(self, starting_cash: float = 10_000.0) -> None:
        self.cash = starting_cash
        self.positions: dict[str, float] = {}

    def on_fill(self, event: FillEvent) -> None:
        qty = event.qty
        cost = qty * event.fill_price

        if event.side == "BUY":
            self.cash -= cost + event.fee
            self.positions[event.symbol] = self.positions.get(event.symbol, 0.0) + qty
        else:
            self.cash += cost - event.fee
            self.positions[event.symbol] = self.positions.get(event.symbol, 0.0) - qty

        print(f"[PORTFOLIO] cash={self.cash:.2f} positions={self.positions}")
