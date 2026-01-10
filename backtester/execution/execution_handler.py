# backtester/execution/execution_handler.py

from __future__ import annotations
from dataclasses import dataclass

from backtester.core.event_queue import EventQueue
from backtester.events import MarketEvent, OrderEvent, FillEvent, Side, OrderType


@dataclass(frozen=True)
class CommissionModel:
    """
    Commission model supporting:
    - per_trade: fixed fee per trade (your v1 behavior)
    - percent: percent of notional (e.g., 0.0005 = 5 bps)
    - per_share: fee per share (e.g., 0.005 = half cent/share)
    """
    model: str = "per_trade"        # "per_trade" | "percent" | "per_share"

    # keep backward-compat with your current main.py
    per_trade_fee: float = 1.0

    # new knobs
    percent_rate: float = 0.0       # e.g. 0.0005 = 5 bps of notional
    per_share_fee: float = 0.0      # e.g. 0.005 dollars per share

    def calculate(self, qty: float, price: float) -> float:
        q = abs(float(qty))
        p = float(price)

        if self.model == "per_trade":
            return float(self.per_trade_fee)

        if self.model == "percent":
            # percent of notional traded
            return float(q * p * float(self.percent_rate))

        if self.model == "per_share":
            return float(q * float(self.per_share_fee))

        # unknown model -> no fee
        return 0.0


@dataclass(frozen=True)
class SlippageModel:
    """
    Slippage model supporting:
    - bps: +/- bps on mid price (BUY pays more, SELL receives less)
    - spread: half-spread in dollars (BUY +half_spread, SELL -half_spread)

    Backward compatible: SlippageModel(bps=0.0) still works.
    """
    model: str = "bps"              # "bps" | "spread"

    # backward compatible field
    bps: float = 0.0                # 1 bp = 0.01%

    # new knob
    half_spread: float = 0.0        # dollars

    def apply(self, side: Side, price: float) -> float:
        px = float(price)

        if self.model == "spread":
            hs = float(self.half_spread)
            return px + hs if side == Side.BUY else px - hs

        # default: bps
        adj = float(self.bps) / 10_000.0
        return px * (1.0 + adj) if side == Side.BUY else px * (1.0 - adj)


class ExecutionHandler:
    """
    Converts OrderEvent -> FillEvent.
    Market orders fill at last seen close (plus slippage).
    Limit orders fill if condition met (simple v1).
    """

    def __init__(
        self,
        events: EventQueue,
        slippage: SlippageModel | None = None,
        commission: CommissionModel | None = None,
    ) -> None:
        self.events = events
        self.slippage = slippage or SlippageModel(model="bps", bps=0.0)
        self.commission = commission or CommissionModel(model="per_trade", per_trade_fee=1.0)
        self.last_price: dict[str, float] = {}

    def on_market(self, event: MarketEvent) -> None:
        self.last_price[event.symbol] = float(event.close)

    def on_order(self, event: OrderEvent) -> None:
        sym = event.symbol
        if sym not in self.last_price:
            # no price yet; skip
            return

        px = self.last_price[sym]

        # Limit logic (v1):
        if event.order_type == OrderType.LMT:
            lp = float(event.limit_price)  # validated in __post_init__
            if event.side == Side.BUY and px > lp:
                return  # not fillable yet
            if event.side == Side.SELL and px < lp:
                return  # not fillable yet
            fill_px = lp
        else:
            fill_px = px

        fill_px = float(self.slippage.apply(event.side, float(fill_px)))
        fee = float(self.commission.calculate(event.qty, fill_px))

        self.events.put(
            FillEvent(
                ts=event.ts,
                symbol=event.symbol,
                side=event.side,
                qty=float(event.qty),
                fill_price=float(fill_px),
                fee=float(fee),
            )
        )
