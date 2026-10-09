from types import SimpleNamespace

from aiobserve import configure, get_observer
from aiobserve.integrations.openai import instrument
from aiobserve.storage import MemoryStorage


class FakeResponses:
    def create(self, **kwargs):
        return SimpleNamespace(
            model=kwargs["model"],
            usage=SimpleNamespace(
                input_tokens=12,
                output_tokens=8,
                input_tokens_details=SimpleNamespace(cached_tokens=2),
            ),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_wrapper_records_usage_and_returns_original_response():
    configure(storage=MemoryStorage())
    client = instrument(FakeClient())
    response = client.responses.create(model="example-model", input="hello")
    assert response.model == "example-model"
    events = get_observer().events()
    assert len(events) == 1
    assert events[0].provider == "openai"
    assert events[0].input_tokens == 12
    assert events[0].output_tokens == 8
    assert events[0].cached_tokens == 2
