from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

from backtester.events import MarketEvent


class EventQueue(Protocol):
    def put(self, event: MarketEvent) -> None: ...


@dataclass(slots=True)
class DataStreamer:
    queue: EventQueue

    def push_market_events(self, source) -> int:
        """
        source must have stream_market_events() -> iterator of MarketEvent
        """
        n = 0
        for evt in source.stream_market_events():
            self.queue.put(evt)
            n += 1
        return n
