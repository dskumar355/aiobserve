from aiobserve import AIObserver, AIObserverConfig
from aiobserve.storage import SQLiteStorage


def test_sqlite_round_trip(tmp_path):
    path = tmp_path / "events.db"
    storage = SQLiteStorage(path)
    observer = AIObserver(AIObserverConfig(project="test"), storage=storage)
    observer.record(provider="custom", model="m", input_tokens=3, output_tokens=4, metadata={"feature": "chat"})
    assert len(storage.all()) == 1
    assert storage.all()[0].metadata == {"feature": "chat"}
    storage.close()
    storage2 = SQLiteStorage(path)
    events = storage2.all()
    assert len(events) == 1
    assert events[0].input_tokens == 3
    assert events[0].project == "test"
    storage2.close()
