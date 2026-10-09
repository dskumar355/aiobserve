"""Opt-in instrumentation wrapper for the official OpenAI Python client.

Usage:
    from openai import OpenAI
    from aiobserve.integrations.openai import instrument
    client = instrument(OpenAI())

The wrapper currently instruments Responses API calls. It returns the original
provider response unchanged and records telemetry best-effort.
"""
from __future__ import annotations

import inspect
from time import perf_counter
from typing import Any

from aiobserve import get_observer
from aiobserve.events import EventType


class _ResponsesProxy:
    def __init__(self, responses: Any, provider: str = "openai") -> None:
        self._responses = responses
        self._provider = provider

    def create(self, *args: Any, **kwargs: Any) -> Any:
        started = perf_counter()
        try:
            response = self._responses.create(*args, **kwargs)
        except Exception:
            self._record(kwargs, None, (perf_counter() - started) * 1000, "error")
            raise
        if inspect.isawaitable(response):
            async def finish_async() -> Any:
                try:
                    resolved = await response
                except Exception:
                    self._record(kwargs, None, (perf_counter() - started) * 1000, "error")
                    raise
                self._record(kwargs, resolved, (perf_counter() - started) * 1000, "ok")
                return resolved
            return finish_async()
        self._record(kwargs, response, (perf_counter() - started) * 1000, "ok")
        return response

    def _record(self, kwargs: dict[str, Any], response: Any, latency_ms: float, status: str) -> None:
        try:
            usage = getattr(response, "usage", None) if response is not None else None
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            input_details = getattr(usage, "input_tokens_details", None)
            cached_tokens = int(getattr(input_details, "cached_tokens", 0) or 0)
            model = getattr(response, "model", None) or kwargs.get("model")
            get_observer().record(
                provider=self._provider,
                model=model,
                event_type=EventType.ERROR if status == "error" else EventType.GENERATION,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                latency_ms=latency_ms,
                status=status,
                metadata={"operation": "responses.create"},
            )
        except Exception:
            # Telemetry must never replace a successful application response or
            # hide the original provider exception.
            return


class _ClientProxy:
    def __init__(self, client: Any, provider: str = "openai") -> None:
        self._client = client
        self._provider = provider
        self.responses = _ResponsesProxy(client.responses, provider=provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def instrument(client: Any, *, provider: str = "openai") -> Any:
    """Wrap an OpenAI-compatible client to observe Responses API calls."""
    if not hasattr(client, "responses"):
        raise TypeError("Expected a client exposing the Responses API as `.responses`")
    return _ClientProxy(client, provider=provider)
