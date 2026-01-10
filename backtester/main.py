# backtester/main.py

from __future__ import annotations

import os
import yaml

from backtester.core.event_queue import EventQueue
from backtester.data.csv_data_handler import CSVDataHandler
from backtester.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent

from backtester.execution.execution_handler import ExecutionHandler, SlippageModel, CommissionModel
from backtester.portfolio.portfolio import Portfolio
from backtester.strategy.moving_average_crossover import MovingAverageCrossStrategy
from backtester.strategy.strategy import Strategy

from backtester.analysis.metrics import compute_metrics
from backtester.analysis.plots import plot_equity_and_drawdown


def run_spy_csv(num_bars: int = 500) -> None:
    events = EventQueue()

    feed = CSVDataHandler(
        csv_path="backtester/data/SPY_1_min.csv",
        symbol="SPY",
        ts_col="date",
    )
    market_iter = feed.stream_market_events()

    strategy = MovingAverageCrossStrategy(events=events, symbol="SPY", fast=10, slow=30)

    # ----- Day 8: load tunable transaction cost + slippage models -----
    cfg: dict = {}
    try:
        with open("config.yaml", "r") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        cfg = {}

    costs = cfg.get("costs", {}) or {}
    comm_cfg = costs.get("commission", {}) or {}
    slip_cfg = costs.get("slippage", {}) or {}

    # default to old behavior if config missing keys
    commission_model = CommissionModel(**comm_cfg) if comm_cfg else CommissionModel(per_trade_fee=1.0)
    slippage_model = SlippageModel(**slip_cfg) if slip_cfg else SlippageModel(bps=0.0)

    execution = ExecutionHandler(
        events=events,
        slippage=slippage_model,
        commission=commission_model,
    )

    # optional: keep BUY cash constraint buffer in sync with config if per-trade fee provided
    est_fee = float(getattr(commission_model, "per_trade_fee", 1.0))

    portfolio = Portfolio(
        events=events,
        starting_cash=10_000.0,
        target_qty=100.0,  # long 100 shares when BUY regime
        max_qty=200.0,
        est_fee_per_trade=est_fee,
    )

    # print config summary so it's obvious runs change when costs change
    comm_model = getattr(commission_model, "model", "per_trade")
    slip_model = getattr(slippage_model, "model", "bps")
    print("\n=== Cost Model (Day 8) ===")
    print(f"Commission: model={comm_model} | per_trade_fee={getattr(commission_model, 'per_trade_fee', 0.0)} "
          f"| percent_rate={getattr(commission_model, 'percent_rate', 0.0)} | per_share_fee={getattr(commission_model, 'per_share_fee', 0.0)}")
    print(f"Slippage:   model={slip_model} | bps={getattr(slippage_model, 'bps', 0.0)} | half_spread={getattr(slippage_model, 'half_spread', 0.0)}")

    equity_points: list[float] = []
    bars_seen = 0
    last_close: float | None = None

    while bars_seen < num_bars:
        try:
            me = next(market_iter)
        except StopIteration:
            break

        events.put(me)

        while not events.empty():
            event = events.get()
            if event is None:
                break

            if event.type == EventType.MARKET:
                me = event  # type: ignore[assignment]
                assert isinstance(me, MarketEvent)

                last_close = float(me.close)
                bars_seen += 1

                # update mark-to-market prices for portfolio + execution
                portfolio.update_market_price(me.symbol, last_close)
                execution.on_market(me)

                # record equity curve row (one per bar)
                portfolio.update_timeindex(me.ts)

                # strategy reacts to market -> may emit SignalEvent
                strategy.on_market(me)

                # record equity (cash + positions MTM)
                equity_points.append(portfolio.total_value())

                qty = float(portfolio.positions.get("SPY", 0.0))
                holdings_value = qty * last_close
                total = portfolio.cash + holdings_value

                print(
                    f"[BAR {bars_seen:05d}] close={last_close:.2f} | "
                    f"cash={portfolio.cash:.2f} | SPY_qty={qty:.0f} | "
                    f"SPY_value={holdings_value:.2f} | total={total:.2f}"
                )

            elif event.type == EventType.SIGNAL:
                se = event  # type: ignore[assignment]
                assert isinstance(se, SignalEvent)
                portfolio.on_signal(se)  # Signal -> Order (with cash constraint)

            elif event.type == EventType.ORDER:
                oe = event  # type: ignore[assignment]
                assert isinstance(oe, OrderEvent)
                execution.on_order(oe)   # Order -> Fill

            elif event.type == EventType.FILL:
                fe = event  # type: ignore[assignment]
                assert isinstance(fe, FillEvent)
                portfolio.on_fill(fe)    # Fill -> cash/positions update

            else:
                raise ValueError(f"Unknown event type: {event.type}")

    if not equity_points:
        print("No bars processed.")
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

    # ----- Day 7 report + plots -----
    os.makedirs("outputs", exist_ok=True)

    equity_curve = portfolio.equity_curve_df()
    periods_per_year = 252 * 390  # 1-min US equities (regular trading hours)

    m = compute_metrics(equity_curve, periods_per_year=periods_per_year)
    plot_equity_and_drawdown(equity_curve, out_dir="outputs")

    print("\n=== Backtest Report (v1) ===")
    print(f"Total Return:   {m.total_return*100:.2f}%")
    print(f"Max Drawdown:   {m.max_drawdown*100:.2f}%")
    print(f"Volatility:     {m.volatility*100:.2f}%")
    print(f"Sharpe (rf=0):  {m.sharpe:.2f}")
    print("Saved: outputs/equity_curve.png, outputs/drawdown_curve.png")


if __name__ == "__main__":
    run_spy_csv(num_bars=500)
