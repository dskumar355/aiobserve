import asyncio
import pytest

from aiobserve import configure, get_observer, observe
from aiobserve.storage import MemoryStorage


def test_decorator_records_success_and_error():
    configure(storage=MemoryStorage())

    @observe(provider="custom", model="m")
    def good():
        return "ok"

    @observe(provider="custom", model="m")
    def bad():
        raise RuntimeError("expected")

    assert good() == "ok"
    with pytest.raises(RuntimeError):
        bad()
    events = get_observer().events()
    assert len(events) == 2
    assert events[0].status == "ok"
    assert events[1].status == "error"


def test_async_decorator():
    configure(storage=MemoryStorage())

    @observe(provider="custom", model="m")
    async def work():
        return 42

    assert asyncio.run(work()) == 42
    assert get_observer().summary()["events"] == 1
