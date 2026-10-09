from collections.abc import Iterable
from threading import Lock
from aiobserve.events import AIEvent
from .base import StorageBackend
class MemoryStorage(StorageBackend):
    def __init__(self): self._events=[]; self._lock=Lock()
    def write(self,event):
        with self._lock: self._events.append(event)
    def write_many(self,events: Iterable[AIEvent]):
        with self._lock: self._events.extend(events)
    def all(self):
        with self._lock: return list(self._events)
