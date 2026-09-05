"""Regression tests for the single atomic Master Core write pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from master_os.core.commands import DomainCommandBus
from master_os.core.database import MasterDatabase
from master_os.core.events import EventStore


def test_command_bus_rolls_back_event_when_reducer_fails(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "command bus", "command-bus-test")

        def broken_reducer(_db, _event, *, commit=True):
            raise RuntimeError("materialization exploded")

        bus = DomainCommandBus(db, events, reducer=broken_reducer)
        with pytest.raises(RuntimeError, match="materialization exploded"):
            bus.emit(
                "task.created",
                source.id,
                {"id": "T-ATOMIC", "title": "must not half-write"},
                dedup_key="atomic-task",
            )

        assert db.fetchone("SELECT id FROM events WHERE dedup_key='atomic-task'") is None
        assert db.fetchone("SELECT id FROM tasks WHERE id='T-ATOMIC'") is None
    finally:
        db.close()


def test_command_bus_commits_event_and_materialized_state_together(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "command bus", "command-bus-test")
        bus = DomainCommandBus(db, events)

        event = bus.emit(
            "task.created",
            source.id,
            {"id": "T-ATOMIC", "title": "one transaction"},
            dedup_key="atomic-task",
        )

        assert db.fetchone("SELECT id FROM events WHERE id=?", (event.id,)) is not None
        assert db.fetchone("SELECT title FROM tasks WHERE id='T-ATOMIC'")["title"] == "one transaction"
    finally:
        db.close()


def test_command_bus_dedup_returns_existing_event_without_replaying_reducer(tmp_path: Path):
    db = MasterDatabase(tmp_path / "master.db")
    try:
        events = EventStore(db)
        source = events.register_source("test", "command bus", "command-bus-test")
        calls: list[str] = []

        from master_os.core.reducer import apply_event

        def counting_reducer(actual_db, event, *, commit=True):
            calls.append(event.id)
            return apply_event(actual_db, event, commit=commit)

        bus = DomainCommandBus(db, events, reducer=counting_reducer)
        first = bus.emit(
            "task.created",
            source.id,
            {"id": "T-DEDUPE", "title": "once"},
            dedup_key="same-command",
        )
        second = bus.emit(
            "task.created",
            source.id,
            {"id": "T-DEDUPE", "title": "should not overwrite"},
            dedup_key="same-command",
        )

        assert second.id == first.id
        assert calls == [first.id]
        assert db.fetchone("SELECT title FROM tasks WHERE id='T-DEDUPE'")["title"] == "once"
    finally:
        db.close()
