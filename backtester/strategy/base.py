# backtester/strategy/base.py

from __future__ import annotations
from abc import ABC, abstractmethod

from backtester.core.event_queue import EventQueue
from backtester.events import MarketEvent


class Strategy(ABC):
    def __init__(self, events: EventQueue) -> None:
        self.events = events

    @abstractmethod
    def on_market(self, event: MarketEvent) -> None:
        raise NotImplementedError
