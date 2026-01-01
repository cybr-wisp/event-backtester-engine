# backtester/core/event_queue.py
from __future__ import annotations

from queue import Queue
from typing import Any


class EventQueue:
    def __init__(self) -> None:
        self._q: Queue[Any] = Queue()

    # add an event when we call put 
    def put(self, event: Any) -> None:
        self._q.put(event)

    # take the new queue event 
    def get(self) -> Any:
        return self._q.get()

    # checks if there is anything to process -- or if the queue is empty 
    def empty(self) -> bool:
        return self._q.empty()
