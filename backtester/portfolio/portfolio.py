# backtester/portfolio/portfolio.py

from __future__ import annotations

from typing import Any

import pandas as pd

from backtester.core.event_queue import EventQueue
from backtester.events import FillEvent, OrderEvent, OrderType, Side, SignalEvent


class Portfolio:
    """
    - Holds cash + positions
    - Converts SignalEvent -> OrderEvent using target holdings
    - Enforces cash constraint (no infinite margin)
    """

    def __init__(
        self,
        events: EventQueue,
        starting_cash: float = 10_000.0,
        target_qty: float = 100.0,
        max_qty: float = 200.0,
        est_fee_per_trade: float = 1.0,  # matches your CommissionModel default
    ) -> None:
        self.events = events
        self.cash = float(starting_cash)
        self.positions: dict[str, float] = {}
        self.last_price: dict[str, float] = {}

        self.target_qty = float(target_qty)
        self.max_qty = float(max_qty)
        self.est_fee_per_trade = float(est_fee_per_trade)

        self.history: list[dict[str, Any]] = []

    def update_market_price(self, symbol: str, price: float) -> None:
        self.last_price[symbol] = float(price)

    def total_value(self) -> float:
        total = self.cash
        for sym, qty in self.positions.items():
            px = self.last_price.get(sym)
            if px is not None:
                total += float(qty) * float(px)
        return float(total)

    def update_timeindex(self, ts) -> None:
        self.history.append(
            {
                "ts": ts,
                "equity": self.total_value(),
                "cash": float(self.cash),
            }
        )

    def equity_curve_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.history)
        df["ts"] = pd.to_datetime(df["ts"])
        df = df.set_index("ts").sort_index()
        return df

    def on_signal(self, event: SignalEvent) -> None:
        sym = event.symbol
        px = self.last_price.get(sym)
        if px is None:
            return

        current_qty = float(self.positions.get(sym, 0.0))

        # (c) Target holdings logic: LONG target_qty, otherwise flat
        desired_qty = self.target_qty if event.side == Side.BUY else 0.0
        desired_qty = max(0.0, min(desired_qty, self.max_qty))

        delta = desired_qty - current_qty
        if abs(delta) < 1e-9:
            return

        side = Side.BUY if delta > 0 else Side.SELL
        order_qty = abs(delta)

        # Prevent overselling / shorting in v1
        if side == Side.SELL:
            order_qty = min(order_qty, current_qty)
            if order_qty <= 0:
                return

        # (a) Cash constraint for BUY: clamp to affordable qty (instead of infinite margin)
        if side == Side.BUY:
            # account for a small fixed fee estimate so you don't go slightly negative
            max_affordable = (self.cash - self.est_fee_per_trade) / float(px)
            if max_affordable <= 0:
                return
            order_qty = min(order_qty, max_affordable)

            # if you want whole-share trading only, uncomment:
            # order_qty = float(int(order_qty))

            if order_qty <= 0:
                return

        self.events.put(
            OrderEvent(
                ts=event.ts,
                symbol=sym,
                side=side,
                qty=float(order_qty),
                order_type=OrderType.MKT,
            )
        )

    def on_fill(self, event: FillEvent) -> None:
        sym = event.symbol
        qty = float(event.qty)
        px = float(event.fill_price)
        fee = float(event.fee)

        current_qty = float(self.positions.get(sym, 0.0))

        if event.side == Side.BUY:
            cost = qty * px + fee
            if cost > self.cash + 1e-9:
                return  # final safety
            self.cash -= cost
            self.positions[sym] = current_qty + qty
        else:
            qty = min(qty, current_qty)  # final safety against oversell
            proceeds = qty * px - fee
            self.cash += proceeds
            self.positions[sym] = current_qty - qty
