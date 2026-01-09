import pandas as pd
from dataclasses import dataclass

from backtester.portfolio.portfolio import Portfolio, PortfolioConfig


@dataclass
class MarketEvent:
    type: str = "MARKET"


class DummyBars:
    def __init__(self, prices):
        self.prices = prices
        self.i = 0
        self.latest_datetime = pd.Timestamp("2026-01-01 09:30")

    def step(self):
        self.i += 1
        self.latest_datetime += pd.Timedelta(minutes=1)

    def get_latest_bar_value(self, symbol, field):
        assert field == "close"
        return self.prices[symbol][min(self.i, len(self.prices[symbol]) - 1)]


def main():
    bars = DummyBars({"SPY": [100, 101, 99, 102, 103]})
    p = Portfolio(bars=bars, events=None, symbol_list=["SPY"], config=PortfolioConfig(10_000))

    for _ in range(5):
        p.update_timeindex(MarketEvent())
        bars.step()

    eq = p.create_equity_curve_dataframe()

    print("\nDAY 4 EDGE-CASE VISUAL (NO TRADES) ✅")
    print(eq[["total", "returns", "equity_curve"]].to_string())

    # hard assertions = proof
    assert (eq["total"] == 10_000).all()
    assert (eq["equity_curve"] == 1.0).all()
    print("\n✅ Flat equity curve confirmed (no trades).")


if __name__ == "__main__":
    main()
