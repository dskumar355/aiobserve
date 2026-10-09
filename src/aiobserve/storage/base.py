from abc import ABC, abstractmethod
from collections.abc import Iterable
from aiobserve.events import AIEvent
class StorageBackend(ABC):
    @abstractmethod
    def write(self, event: AIEvent) -> None: ...
    @abstractmethod
    def write_many(self, events: Iterable[AIEvent]) -> None: ...
    @abstractmethod
    def all(self) -> list[AIEvent]: ...
