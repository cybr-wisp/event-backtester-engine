# backtester/strategy/moving_average_crossover.py

from __future__ import annotations
from collections import deque

from backtester.core.event_queue import EventQueue
from backtester.events import MarketEvent, SignalEvent, Side
from backtester.strategy.strategy import Strategy


class MovingAverageCrossStrategy(Strategy):
    """
    Long-only MA crossover:
      - fast > slow => BUY signal
      - fast <= slow => SELL signal
    Debounced: emits only when side changes.
    """

    def __init__(
        self,
        events: EventQueue,
        symbol: str,
        fast: int = 10,
        slow: int = 30,
    ) -> None:
        if fast >= slow:
            raise ValueError("fast must be < slow")

        super().__init__(events=events, symbol=symbol)

        self.fast_n = fast
        self.slow_n = slow

        self.prices = deque(maxlen=slow)
        self.last_side: Side | None = None

    def _sma(self, n: int) -> float:
        vals = list(self.prices)[-n:]
        return sum(vals) / float(n)

    def on_market(self, event: MarketEvent) -> None:
        if event.symbol != self.symbol:
            return

        self.prices.append(float(event.close))
        if len(self.prices) < self.slow_n:
            return

        fast = self._sma(self.fast_n)
        slow = self._sma(self.slow_n)

        side = Side.BUY if fast > slow else Side.SELL

        # Debounce: only emit on flip
        if self.last_side is None or side != self.last_side:
            self.events.put(SignalEvent(ts=event.ts, symbol=event.symbol, side=side))
            self.last_side = side
