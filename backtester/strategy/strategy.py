# backtester/strategy/strategy.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backtester.core.event_queue import EventQueue
from backtester.events import MarketEvent


@dataclass
class Strategy(ABC):
    """
    Base Strategy interface.

    Concrete strategies should:
      - consume MarketEvent via on_market()
      - emit SignalEvent(s) into self.events when appropriate
    """
    events: EventQueue
    symbol: str

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Strategy.symbol must be a non-empty string.")

    @abstractmethod
    def on_market(self, event: MarketEvent) -> None:
        """
        Called once per MarketEvent. Implement your trading logic here.

        Expected behavior:
          - read event.close / event.ts
          - decide whether to emit a SignalEvent (debounced; only on regime change)
          - push it into self.events via self.events.put(...)
        """
        raise NotImplementedError
