from __future__ import annotations

from dataclasses import dataclass
from random import random
from typing import Any

from aiobserve.events import AIEvent, EventType
from aiobserve.pricing import DEFAULT_CATALOG, PricingCatalog
from aiobserve.storage import MemoryStorage, StorageBackend


@dataclass(slots=True)
class AIObserverConfig:
    project: str | None = None
    environment: str | None = None
    capture_content: bool = False
    redact_pii: bool = True
    sample_rate: float = 1.0


class AIObserver:
    def __init__(
        self,
        config: AIObserverConfig | None = None,
        storage: StorageBackend | None = None,
        pricing: PricingCatalog | None = None,
    ) -> None:
        self.config = config or AIObserverConfig()
        self.storage = storage or MemoryStorage()
        self.pricing = pricing or DEFAULT_CATALOG
        if not 0 <= self.config.sample_rate <= 1:
            raise ValueError("sample_rate must be between 0 and 1")

    def record(
        self,
        *,
        provider: str,
        model: str | None = None,
        event_type: EventType = EventType.GENERATION,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0,
        latency_ms: float | None = None,
        status: str = "ok",
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIEvent | None:
        if self.config.sample_rate < 1 and random() >= self.config.sample_rate and status != "error":
            return None

        input_cost = output_cost = total_cost = 0.0
        currency = "USD"
        pricing = self.pricing.get(provider, model) if model else None
        cost_known = pricing is not None
        if pricing is not None:
            input_cost, output_cost, total_cost = pricing.calculate(
                input_tokens, output_tokens, cached_tokens
            )
            currency = pricing.currency

        # Do not capture content unless explicitly enabled. Callers should pass only
        # approved metadata; this SDK intentionally does not inspect prompts/responses.
        safe_metadata = dict(metadata or {})
        event = AIEvent(
            event_type=event_type,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            currency=currency,
            cost_known=cost_known,
            latency_ms=latency_ms,
            status=status,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            user_id=user_id,
            session_id=session_id,
            project=self.config.project,
            environment=self.config.environment,
            metadata=safe_metadata,
        )
        self.storage.write(event)
        return event

    def events(self) -> list[AIEvent]:
        return self.storage.all()

    def summary(self) -> dict[str, Any]:
        events = self.events()
        latencies = [event.latency_ms for event in events if event.latency_ms is not None]
        costs = [event for event in events if event.cost_known]
        currencies = {event.currency for event in costs}
        return {
            "project": self.config.project,
            "environment": self.config.environment,
            "events": len(events),
            "input_tokens": sum(event.input_tokens for event in events),
            "output_tokens": sum(event.output_tokens for event in events),
            "known_cost_events": len(costs),
            "unknown_cost_events": len(events) - len(costs),
            "total_cost": round(sum(event.total_cost for event in costs), 10) if len(currencies) <= 1 else None,
            "currency": next(iter(currencies)) if len(currencies) == 1 else ("USD" if not currencies else "MIXED"),
            "errors": sum(event.status == "error" for event in events),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        }
