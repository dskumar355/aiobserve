from aiobserve import configure, record
from aiobserve.pricing import ModelPricing, PricingCatalog
from aiobserve.storage import MemoryStorage
import pytest


def test_manual_record_and_summary():
    observer = configure(project="test", environment="unit", storage=MemoryStorage())
    event = record(provider="custom", model="example", input_tokens=10, output_tokens=5, latency_ms=12)
    assert event is not None
    summary = observer.summary()
    assert summary["events"] == 1
    assert summary["input_tokens"] == 10
    assert summary["output_tokens"] == 5
    assert summary["unknown_cost_events"] == 1
    assert summary["total_cost"] == 0


def test_cost_calculation_uses_explicit_pricing():
    catalog = PricingCatalog()
    catalog.register(ModelPricing("custom", "example", input_per_million=2, output_per_million=4))
    observer = configure(storage=MemoryStorage(), pricing=catalog)
    event = observer.record(provider="custom", model="example", input_tokens=1_000_000, output_tokens=500_000)
    assert event is not None
    assert event.cost_known is True
    assert event.input_cost == 2
    assert event.output_cost == 2
    assert event.total_cost == 4
    assert observer.summary()["total_cost"] == 4


def test_cached_token_cost_and_validation():
    catalog = PricingCatalog()
    catalog.register(ModelPricing("x", "m", input_per_million=2, output_per_million=4, cached_input_per_million=0.5))
    price = catalog.calculate("x", "m", 1_000_000, 0, 200_000)
    assert price[0] == pytest.approx(1.7)
    assert price[1] == 0.0
    assert price[2] == pytest.approx(1.7)
    try:
        record(provider="custom", input_tokens=1, cached_tokens=2)
    except ValueError as exc:
        assert "cached_tokens" in str(exc)
    else:
        raise AssertionError("Expected cached token validation")
