from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import pandas as pd


# =========================
# Configuration
# =========================

@dataclass(frozen=True)
class PortfolioConfig:
    initial_capital: float = 100_000.0


# =========================
# Portfolio
# =========================

class Portfolio:
    """
    Institutional-grade portfolio & accounting engine.

    Responsibilities:
    - Maintain positions and holdings
    - Process FillEvents deterministically
    - Mark-to-market on every MarketEvent
    - Produce an equity curve even with zero trades

    Non-responsibilities:
    - Signal generation
    - Order sizing logic
    - Execution simulation
    """

    def __init__(
        self,
        bars: Any,
        events: Any,
        symbol_list: List[str],
        config: Optional[PortfolioConfig] = None,
    ) -> None:

        self.bars = bars
        self.events = events
        self.symbol_list = symbol_list

        self.config = config or PortfolioConfig()
        self.initial_capital = float(self.config.initial_capital)

        # ---- Current state ----
        self.current_positions: Dict[str, int] = {s: 0 for s in symbol_list}
        self.current_holdings: Dict[str, float] = self._init_holdings()

        # ---- Historical snapshots ----
        self.all_positions: List[Dict[str, Any]] = []
        self.all_holdings: List[Dict[str, Any]] = []

        # ---- Output ----
        self.equity_curve: Optional[pd.DataFrame] = None

    # =========================
    # Initialization
    # =========================

    def _init_holdings(self) -> Dict[str, float]:
        holdings = {
            "cash": self.initial_capital,
            "commission": 0.0,
            "total": self.initial_capital,
        }
        for s in self.symbol_list:
            holdings[s] = 0.0
        return holdings

    # =========================
    # Market Data Accessors
    # =========================

    def _latest_datetime(self) -> pd.Timestamp:
        if hasattr(self.bars, "get_latest_bar_datetime"):
            return pd.Timestamp(self.bars.get_latest_bar_datetime(self.symbol_list[0]))
        return pd.Timestamp(self.bars.latest_datetime)

    def _latest_price(self, symbol: str) -> float:
        if hasattr(self.bars, "get_latest_bar_value"):
            return float(self.bars.get_latest_bar_value(symbol, "close"))
        raise AttributeError("DataHandler must expose latest close price")

    # =========================
    # Event Handlers
    # =========================

    def update_timeindex(self, market_event: Any) -> None:
        """
        Mark-to-market portfolio on each MarketEvent.
        """

        dt = self._latest_datetime()

        # ---- Positions snapshot ----
        pos_snapshot = {"datetime": dt}
        pos_snapshot.update(self.current_positions)
        self.all_positions.append(pos_snapshot)

        # ---- Holdings snapshot (MTM) ----
        hold_snapshot = {
            "datetime": dt,
            "cash": self.current_holdings["cash"],
            "commission": self.current_holdings["commission"],
            "total": 0.0,
        }

        total = hold_snapshot["cash"]

        for s in self.symbol_list:
            mkt_value = self.current_positions[s] * self._latest_price(s)
            hold_snapshot[s] = float(mkt_value)
            total += mkt_value

        hold_snapshot["total"] = float(total)
        self.all_holdings.append(hold_snapshot)

        # Sync current holdings
        for k, v in hold_snapshot.items():
            if k != "datetime":
                self.current_holdings[k] = v

    def update_fill(self, fill_event: Any) -> None:
        """
        Update portfolio from a FillEvent.
        """
        self._update_positions(fill_event)
        self._update_cash(fill_event)

    # =========================
    # Fill Accounting
    # =========================

    def _update_positions(self, fill: Any) -> None:
        qty = int(fill.quantity)
        direction = fill.direction.upper()

        if direction == "BUY":
            self.current_positions[fill.symbol] += qty
        elif direction == "SELL":
            self.current_positions[fill.symbol] -= qty
        else:
            raise ValueError("Invalid fill direction")

    def _update_cash(self, fill: Any) -> None:
        qty = int(fill.quantity)
        price = float(fill.fill_cost)
        commission = float(getattr(fill, "commission", 0.0))
        direction = fill.direction.upper()

        gross = qty * price

        if direction == "BUY":
            cash_delta = -(gross + commission)
        else:  # SELL
            cash_delta = +(gross - commission)

        self.current_holdings["cash"] += cash_delta
        self.current_holdings["commission"] += commission

    # =========================
    # Equity Curve
    # =========================

    def create_equity_curve_dataframe(self) -> pd.DataFrame:
        """
        Build equity curve from holdings history.
        """

        if not self.all_holdings:
            raise RuntimeError("No market events processed")

        df = pd.DataFrame(self.all_holdings).set_index("datetime").sort_index()

        df["returns"] = df["total"].pct_change().fillna(0.0)
        df["equity_curve"] = (1.0 + df["returns"]).cumprod()

        self.equity_curve = df
        return df
