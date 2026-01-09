import pandas as pd
from dataclasses import dataclass
from backtester.portfolio.portfolio import Portfolio, PortfolioConfig


@dataclass
class DummyMarketEvent:
    type: str = "MARKET"


@dataclass
class DummyFillEvent:
    symbol: str
    quantity: int
    direction: str
    fill_cost: float
    commission: float = 0.0


class DummyBars:
    def __init__(self, prices):
        self.prices = prices
        self.i = 0
        self.latest_datetime = pd.Timestamp("2026-01-01 09:30")

    def step(self):
        self.i += 1
        self.latest_datetime += pd.Timedelta(minutes=1)

    def get_latest_bar_value(self, symbol, field):
        return self.prices[symbol][min(self.i, len(self.prices[symbol]) - 1)]


def test_equity_curve_without_trades():
    bars = DummyBars({"SPY": [100, 101, 102]})
    p = Portfolio(bars, None, ["SPY"], PortfolioConfig(1000))

    for _ in range(3):
        p.update_timeindex(DummyMarketEvent())
        bars.step()

    eq = p.create_equity_curve_dataframe()
    assert (eq["total"] == 1000).all()
    assert (eq["equity_curve"] == 1.0).all()


def test_buy_and_mark_to_market():
    bars = DummyBars({"SPY": [100, 110]})
    p = Portfolio(bars, None, ["SPY"], PortfolioConfig(1000))

    p.update_fill(DummyFillEvent("SPY", 5, "BUY", 100))
    p.update_timeindex(DummyMarketEvent())

    assert p.current_positions["SPY"] == 5
    assert p.current_holdings["total"] == 1000

    bars.step()
    p.update_timeindex(DummyMarketEvent())
    assert p.current_holdings["total"] == 1050
