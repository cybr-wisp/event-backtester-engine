# backtester/main.py

from __future__ import annotations

from backtester.core.event_queue import EventQueue
from backtester.core.dummy_components import (
    DummyStrategy,
    DummyExecutionHandler,
    Portfolio,
)
from backtester.data.csv_data_handler import CSVDataHandler
from backtester.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent


def run_day4_spy_csv(num_bars: int = 200) -> None:
    events = EventQueue()

    # REAL DATA FEED (SPY 1-min CSV)
    feed = CSVDataHandler(csv_path="backtester/data/SPY_1_min.csv", symbol="SPY")

    strategy = DummyStrategy(events=events)
    execution = DummyExecutionHandler(events=events, qty=10.0, fee=1.0)
    portfolio = Portfolio(starting_cash=10_000.0)

    # ---- Day 4 visuals: keep an equity series we can show at the end ----
    equity_points: list[float] = []

    last_close: float | None = None

    bars_seen = 0

    while bars_seen < num_bars:
    # 1) emit market events from CSV
    # stream_market_events() may emit:
    #   - one MarketEvent per call, OR
    #   - many MarketEvents (possibly the whole file) in one call.
        emitted = feed.stream_market_events()
        if emitted is False:
            break  # end of file / no more data

        # 2) drain queue (core event loop)
        while not events.empty():
            event = events.get()
            if event is None:
                break

            if event.type == EventType.MARKET:
                me: MarketEvent = event  # type: ignore

                # source of truth for mark-to-market
                last_close = float(me.close)
                bars_seen += 1

                # strategy reacts to market data
                strategy.on_market(me)

                # execution stores last price (so fills use last close)
                execution.on_market(me)

                # if we've hit our bar budget, stop cleanly
                if bars_seen >= num_bars:
                    # optional: flush remaining events so we exit cleanly
                    while not events.empty():
                        events.get()
                    break

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

    # If stream_market_events() only emits once and queue was empty,
    # loop continues and we call it again.


        # ---------------------------------------------------------------------------------
        # 2) LIVE PER-BAR VISUAL (ticker-tape accounting)
        # total = cash + position_qty * last_close
        # ---------------------------------------------------------------------------------
        if last_close is None:
            # If this happens, no MARKET event was emitted
            last_close = 0.0

        sym = "SPY"
        qty = float(portfolio.positions.get(sym, 0.0))
        holdings_value = qty * float(last_close)
        total = float(portfolio.cash) + holdings_value

        equity_points.append(total)

        print(
            f"[BAR {i:05d}] "
            f"close={float(last_close):.2f} | "
            f"cash={portfolio.cash:.2f} | "
            f"{sym}_qty={qty:.0f} | "
            f"{sym}_value={holdings_value:.2f} | "
            f"total={total:.2f}"
        )

    # ---------------------------------------------------------------------------------
    # 3) ASCII EQUITY CURVE SPARKLINE (end-of-run terminal visual)
    # ---------------------------------------------------------------------------------
    if not equity_points:
        print("\nNo bars processed — check CSV path or CSV handler.")
        return

    levels = "▁▂▃▄▅▆▇█"
    mn, mx = min(equity_points), max(equity_points)

    def spark(v: float) -> str:
        if mx == mn:
            return "▁"
        idx = int((v - mn) / (mx - mn) * (len(levels) - 1))
        idx = max(0, min(idx, len(levels) - 1))
        return levels[idx]

    print("\nEquity curve sparkline:")
    print("".join(spark(v) for v in equity_points))

    print("\nEquity curve points (last 10):")
    start = max(0, len(equity_points) - 10)
    for j in range(start, len(equity_points)):
        print(f"  bar {j:05d}: total={equity_points[j]:.2f}")


if __name__ == "__main__":
    run_day4_spy_csv(num_bars=200)
