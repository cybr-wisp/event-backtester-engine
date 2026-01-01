from __future__ import annotations

from dataclasses import dataclass

from backtester.events import MarketEvent, SignalEvent, FillEvent, EventType
from backtester.core.event_queue import EventQueue


class DummyDataHandler:
    def __init__(self, events: EventQueue, symbol: str = "SPY") -> None:
        self.events = events
        self.symbol = symbol

    def stream_next(self, bar_index: int) -> None:
        # Pretend we received a new bar
        self.events.put(MarketEvent(symbol=self.symbol, bar_index=bar_index))


class DummyStrategy:
    def __init__(self, events: EventQueue) -> None:
        self.events = events

    def on_market(self, event: MarketEvent) -> None:
        # Emit a signal every even bar_index (easy to debug)
        if event.bar_index is not None and event.bar_index % 2 == 0:
            self.events.put(SignalEvent(symbol=event.symbol, direction="LONG"))


class DummyExecutionHandler:
    def __init__(self, events: EventQueue, quantity: int = 10, fill_price: float = 100.0) -> None:
        self.events = events
        self.quantity = quantity
        self.fill_price = fill_price

    def on_signal(self, event: SignalEvent) -> None:
        side = "BUY" if event.direction == "LONG" else "SELL"
        self.events.put(
            FillEvent(
                symbol=event.symbol,
                side=side,
                quantity=self.quantity,
                fill_price=self.fill_price,
            )
        )


class Portfolio:
    def __init__(self, starting_cash: float = 10_000.0) -> None:
        self.cash = starting_cash
        self.positions: dict[str, int] = {}

    def on_fill(self, event: FillEvent) -> None:
        qty = event.quantity
        cost = qty * event.fill_price

        if event.side == "BUY":
            self.cash -= cost
            self.positions[event.symbol] = self.positions.get(event.symbol, 0) + qty
        else:
            self.cash += cost
            self.positions[event.symbol] = self.positions.get(event.symbol, 0) - qty

        print(f"[PORTFOLIO] cash={self.cash:.2f} positions={self.positions}")
