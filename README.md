# AIObserve

**Lightweight, provider-neutral AI cost tracking and observability for Python.**

AIObserve is an early-stage open-source SDK for recording model usage, estimating costs from explicitly configured pricing, and tracking request latency and errors. The core has no mandatory third-party dependencies and supports in-memory or SQLite storage.

> **Alpha notice:** APIs and integrations may change. AIObserve does not currently fetch live pricing automatically. Unknown model prices are reported as unknown rather than guessed.

## Install

```bash
pip install aiobserve
```

For the optional OpenAI integration:

```bash
pip install "aiobserve[openai]"
```

## Quick start: manual tracking

```python
from aiobserve import configure, record, get_observer
from aiobserve.pricing import ModelPricing, PricingCatalog

pricing = PricingCatalog()
pricing.register(ModelPricing(
    provider="openai",
    model="your-model-name",
    input_per_million=1.00,   # Replace with current provider pricing.
    output_per_million=4.00,  # Replace with current provider pricing.
))

configure(project="support-agent", environment="production", pricing=pricing)
record(
    provider="openai",
    model="your-model-name",
    input_tokens=1000,
    output_tokens=500,
    latency_ms=820,
)
print(get_observer().summary())
```

Prices above are illustrative only. Confirm the current rates with your provider and configure the correct currency and token categories before using cost reports for billing decisions.

## OpenAI Responses API instrumentation

```python
from openai import OpenAI
from aiobserve import configure, get_observer
from aiobserve.integrations.openai import instrument

configure(project="my-app", environment="development")
client = instrument(OpenAI())
response = client.responses.create(
    model="your-supported-model",
    input="Explain observability in one sentence.",
)
print(response.output_text)
print(get_observer().summary())
```

The adapter records response usage and elapsed time when the provider response exposes them. The provider response is returned unchanged. Telemetry errors are swallowed so monitoring does not replace the application's result. Streaming and full async-client support are not yet guaranteed.

## Storage

In-memory storage is the default. To persist events locally:

```python
from aiobserve import configure, get_observer
from aiobserve.storage import SQLiteStorage

configure(project="my-app", storage=SQLiteStorage("aiobserve.db"))
```

SQLite is intended for local development and small workloads. Call `get_observer().storage.close()` when shutting down if using SQLite.

## Cost semantics

- Costs are estimates based on the `PricingCatalog` supplied by your application.
- Unknown prices are not treated as verified zero-cost events; summary output separates known and unknown cost events.
- Cached input tokens can have a separately configured rate.
- Currency conversion is not automatic. Do not sum costs across currencies as if they were the same currency.
- Provider invoices remain the source of truth for actual billing.

## Privacy

AIObserve does not automatically capture prompt or response content. Pass only metadata you are comfortable storing. Avoid putting secrets, raw personal information, or conversation content in metadata. `capture_content` and `redact_pii` are configuration placeholders in this alpha release and should not be interpreted as a complete PII-redaction implementation.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -v
python -m build
python -m twine check dist/*
```

## Roadmap

- [x] Provider-neutral event model and manual recording
- [x] Configurable pricing catalog
- [x] In-memory and SQLite storage
- [x] Function decorator for latency and error tracking
- [x] Initial OpenAI Responses API wrapper
- [ ] Thorough async and streaming support
- [ ] Anthropic and Gemini adapters
- [ ] Trace aggregation and agent/tool spans
- [ ] PII redaction and privacy controls
- [ ] OTLP exporter and hosted dashboard

## License

MIT
