# backtester/main.py

from __future__ import annotations

from backtester.core.event_queue import EventQueue
from backtester.core.dummy_components import DummyDataHandler, DummyStrategy, DummyExecutionHandler, Portfolio
from backtester.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent


def run_day2_dummy(num_bars: int = 6) -> None:
    events = EventQueue()

    feed = DummyDataHandler(events=events, symbol="SPY")
    strategy = DummyStrategy(events=events)
    execution = DummyExecutionHandler(events=events, qty=10.0, fee=1.0)
    portfolio = Portfolio(starting_cash=10_000.0)

    for i in range(num_bars):
        # 1) feed market events
        feed.stream_next(i)

        # 2) drain queue (core event loop)
        while not events.empty():
            event = events.get()
            if event is None:
                break

            if event.type == EventType.MARKET:
                me: MarketEvent = event  # type: ignore
                # strategy reacts to market data
                strategy.on_market(me)
                # execution stores last price (so fills use last close)
                execution.on_market(me)

            elif event.type == EventType.SIGNAL:
                se: SignalEvent = event  # type: ignore
                execution.on_signal(se)

            elif event.type == EventType.ORDER:
                oe: OrderEvent = event  # type: ignore
                execution.on_order(oe)

            elif event.type == EventType.FILL:
                fe: FillEvent = event  # type: ignore
                portfolio.on_fill(fe)

            else:
                raise ValueError(f"Unknown event type: {event.type}")

        print(f"[END BAR {i}] cash={portfolio.cash:.2f} positions={portfolio.positions}\n")


if __name__ == "__main__":
    run_day2_dummy(num_bars=6)
