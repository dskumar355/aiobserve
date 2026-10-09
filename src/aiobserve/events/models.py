from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    GENERATION = "generation"
    EMBEDDING = "embedding"
    TOOL_CALL = "tool_call"
    RETRIEVAL = "retrieval"
    AGENT = "agent"
    STT = "speech_to_text"
    TTS = "text_to_speech"
    HTTP = "http"
    ERROR = "error"


@dataclass(slots=True)
class AIEvent:
    event_type: EventType
    provider: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    cost_known: bool = False
    latency_ms: float | None = None
    status: str = "ok"
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    project: str | None = None
    environment: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
        if not self.provider or not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        counts = (self.input_tokens, self.output_tokens, self.cached_tokens, self.reasoning_tokens)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts):
            raise ValueError("Token counts must be non-negative integers")
        if self.cached_tokens > self.input_tokens:
            raise ValueError("cached_tokens cannot exceed input_tokens")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if self.total_cost == 0.0 and (self.input_cost or self.output_cost):
            self.total_cost = self.input_cost + self.output_cost
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def to_dict(self) -> dict[str, Any]:
        result = {item.name: getattr(self, item.name) for item in fields(self)}
        result["event_type"] = self.event_type.value
        result["timestamp"] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AIEvent":
        data = dict(value)
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
