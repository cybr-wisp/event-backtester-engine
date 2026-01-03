# backtester/core/event_queue.py

# imports 
from __future__ import annotations
from collections import deque
from queue import Queue
from typing import Deque, Optional, Any 

class EventQueue:
    def __init__(self) -> None:
        self._q = deque() # _q because it signals 'internal/private'

    # add an event when we call put 
    def put(self, event) -> None:
        print(f"PUT {event.type} {event}" )
        self._q.append(event)

    # if empty, return None
    # else pop left (popleft)
    def get(self):
        if not self._q:
            return None
        return self._q.popleft()
    
    def empty(self) -> bool:
        return len(self._q) == 0