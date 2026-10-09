from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from uuid import uuid4

@dataclass(slots=True)
class Span:
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid4().hex)
    parent_span_id: str | None = None
    start: float = field(default_factory=perf_counter)
    end: float | None = None
    status: str = "ok"
    @property
    def latency_ms(self) -> float | None:
        return None if self.end is None else (self.end - self.start) * 1000
    def finish(self, status: str = "ok") -> None:
        self.end = perf_counter(); self.status = status

@contextmanager
def span(name: str, trace_id: str | None = None, parent_span_id: str | None = None):
    item = Span(name, trace_id or uuid4().hex, parent_span_id=parent_span_id)
    try:
        yield item
    except Exception:
        item.finish("error"); raise
    else:
        item.finish()
