"""AIObserve: lightweight AI cost tracking and observability for Python."""
from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

from .core import AIObserver, AIObserverConfig
from .events import AIEvent, EventType, Span, span
from .pricing import DEFAULT_CATALOG, ModelPricing, PricingCatalog
from .storage import MemoryStorage, SQLiteStorage
from .version import __version__

F = TypeVar("F", bound=Callable[..., Any])
_default_observer = AIObserver()


def configure(
    *,
    project: str | None = None,
    environment: str | None = None,
    capture_content: bool = False,
    redact_pii: bool = True,
    sample_rate: float = 1.0,
    storage: Any = None,
    pricing: PricingCatalog | None = None,
) -> AIObserver:
    """Configure the process-wide observer and return it."""
    global _default_observer
    _default_observer = AIObserver(
        AIObserverConfig(project, environment, capture_content, redact_pii, sample_rate),
        storage,
        pricing,
    )
    return _default_observer


def get_observer() -> AIObserver:
    """Return the currently configured process-wide observer."""
    return _default_observer


def record(**kwargs: Any) -> AIEvent | None:
    """Manually record one provider-neutral telemetry event."""
    return _default_observer.record(**kwargs)


def observe(
    *,
    name: str | None = None,
    provider: str = "custom",
    model: str | None = None,
    event_type: EventType = EventType.GENERATION,
    metadata: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorate a function to record its duration and success/error status."""
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with span(name or func.__name__) as current:
                    try:
                        result = await func(*args, **kwargs)
                    except Exception:
                        _default_observer.record(
                            provider=provider, model=model, event_type=EventType.ERROR,
                            status="error", latency_ms=current.latency_ms,
                            trace_id=current.trace_id, span_id=current.span_id, metadata=metadata,
                        )
                        raise
                    _default_observer.record(
                        provider=provider, model=model, event_type=event_type,
                        latency_ms=current.latency_ms, trace_id=current.trace_id,
                        span_id=current.span_id, metadata=metadata,
                    )
                    return result
            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with span(name or func.__name__) as current:
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    _default_observer.record(
                        provider=provider, model=model, event_type=EventType.ERROR,
                        status="error", latency_ms=current.latency_ms,
                        trace_id=current.trace_id, span_id=current.span_id, metadata=metadata,
                    )
                    raise
                _default_observer.record(
                    provider=provider, model=model, event_type=event_type,
                    latency_ms=current.latency_ms, trace_id=current.trace_id,
                    span_id=current.span_id, metadata=metadata,
                )
                return result
        return wrapper  # type: ignore[return-value]
    return decorator


__all__ = [
    "AIEvent", "AIObserver", "AIObserverConfig", "DEFAULT_CATALOG", "EventType",
    "MemoryStorage", "ModelPricing", "PricingCatalog", "SQLiteStorage", "Span",
    "__version__", "configure", "get_observer", "observe", "record", "span",
]
