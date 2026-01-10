# backtester/core/event_queue.py

from __future__ import annotations

from collections import deque
from typing import Any, Deque, Optional


class EventQueue:
    def __init__(self) -> None:
        self._q: Deque[Any] = deque()

    def put(self, event: Any) -> None:
        # optional debug:
        # print(f"PUT {event.type} {event}")
        self._q.append(event)

    def get(self) -> Optional[Any]:
        if not self._q:
            return None
        return self._q.popleft()

    def empty(self) -> bool:
        return len(self._q) == 0

    def __len__(self) -> int:
        return len(self._q)
