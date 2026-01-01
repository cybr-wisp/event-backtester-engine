from __future__ import annotations

from backtester.core.event_queue import EventQueue
from backtester.core.dummy_components import (
    DummyDataHandler,
    DummyStrategy,
    DummyExecutionHandler,
    Portfolio,
)
from backtester.events import EventType


def run(n_bars: int = 6) -> None:
    events = EventQueue()

    data = DummyDataHandler(events, symbol="SPY")
    strategy = DummyStrategy(events)
    execution = DummyExecutionHandler(events, quantity=10, fill_price=100.0)
    portfolio = Portfolio(starting_cash=10_000.0)

    for i in range(n_bars):
        print(f"\n=== TICK {i} ===")
        data.stream_next(i)

        # Drain the queue for this tick
        while not events.empty():
            event = events.get()
            print("[EVENT]", event.type, event)

            if event.type == EventType.MARKET:
                strategy.on_market(event)
            elif event.type == EventType.SIGNAL:
                execution.on_signal(event)
            elif event.type == EventType.FILL:
                portfolio.on_fill(event)
            else:
                raise ValueError(f"Unhandled event type: {event.type}")


if __name__ == "__main__":
    run()
