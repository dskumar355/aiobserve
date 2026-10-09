from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from aiobserve.events import AIEvent
from .base import StorageBackend


class SQLiteStorage(StorageBackend):
    """SQLite event storage suitable for local development and small workloads."""

    def __init__(self, path: str | Path = "aiobserve.db") -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )"""
        )
        self._conn.commit()

    def write(self, event: AIEvent) -> None:
        self.write_many([event])

    def write_many(self, events: Iterable[AIEvent]) -> None:
        rows = [(event.event_id, json.dumps(event.to_dict(), default=str)) for event in events]
        with self._conn:
            self._conn.executemany(
                "INSERT OR REPLACE INTO events (event_id, payload) VALUES (?, ?)", rows
            )

    def all(self) -> list[AIEvent]:
        rows = self._conn.execute("SELECT payload FROM events ORDER BY rowid").fetchall()
        return [AIEvent.from_dict(json.loads(row["payload"])) for row in rows]

    def close(self) -> None:
        self._conn.close()
