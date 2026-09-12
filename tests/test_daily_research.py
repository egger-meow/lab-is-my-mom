"""Synthetic fixtures verifying research planning boundaries."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from master_os.core.database import MasterDatabase
from master_os.intelligence.daily_research import DailyResearchPlanner, task_work
from master_os.intelligence.planner import MasterPlanner


@pytest.fixture
def planner(tmp_path):
    db = MasterDatabase(tmp_path / "master.db")
    p = DailyResearchPlanner(db, tmp_path)
    source = p.events.register_source("user", "test", "test")
    p.commands.emit("meeting.scheduled", source.id, {"id": "meeting-test", "title": "Advisor", "scheduled_at": "2026-09-15T08:00:00+00:00"})
    docs = tmp_path / "data" / "documents"
    docs.mkdir(parents=True)
    (docs / "seed.txt").write_text("Compare candidate questions; topic is not selected.", encoding="utf-8")
    yield p
    db.close()


NOW = datetime(2026, 9, 13, 4, tzinfo=timezone.utc)


def proposal():
    return {"summary": "Test proposal, not research results", "tasks": [{
        "key": "compare", "title": "Compare nearest work", "question": "What overlaps?",
        "method": "Read source limitations", "deliverable": "Comparison with citations",
        "kind": "research", "scheduled_for": "2026-09-13", "estimated_minutes": 60,
        "depends_on": [], "evidence_refs": ["data/documents/seed.txt"],
    }]}


def test_plan_creates_dated_focus_and_does_not_accept_permissions(planner):
    plan = proposal()
    plan["tasks"][0].update(permissions={"costly_compute": True}, expected_artifacts=["../../secret"], status="completed")
    ids = planner.apply_plan(plan, context=planner.context(NOW), run_id="test-run")
    work = task_work(planner.db, ids[0])
    assert "permissions" not in work and "status" not in work
    assert work["expected_artifacts"] == ["research-output.md"]
    assert MasterPlanner(planner.db).get_plan(NOW).focus_action.task_id == ids[0]
    assert planner.db.fetchone("SELECT status FROM tasks WHERE id=?", (ids[0],))["status"] == "todo"


@pytest.mark.parametrize("change", ["evidence", "budget", "cycle", "future"])
def test_invalid_plan_does_not_partially_apply(planner, change):
    plan = proposal()
    task = plan["tasks"][0]
    if change == "evidence":
        task["evidence_refs"] = ["invented.txt"]
    elif change == "budget":
        planner.configure({"heavy_minutes": 30})
    elif change == "cycle":
        task["depends_on"] = ["compare"]
    else:
        task["scheduled_for"] = "2026-09-16"
    with pytest.raises(ValueError):
        planner.apply_plan(plan, context=planner.context(NOW), run_id="bad")
    assert not planner.db.fetchall("SELECT * FROM tasks")


def test_checkin_only_completes_explicit_selection_and_triggers_new_plan(planner):
    context = planner.context(NOW)
    ids = planner.apply_plan(proposal(), context=context, run_id="test")
    first = planner.request_plan(NOW)
    assert planner.request_plan(NOW, reason="manual")["task_id"] == first["task_id"]
    planner.check_in("I read some of the paper")
    assert planner.db.fetchone("SELECT status FROM tasks WHERE id=?", (ids[0],))["status"] == "todo"
    assert planner.request_plan(NOW)["task_id"] != first["task_id"]
    planner.check_in("Comparison complete", ids)
    assert planner.db.fetchone("SELECT status FROM tasks WHERE id=?", (ids[0],))["status"] == "completed"
    planner.apply_plan(proposal(), context=context, run_id="stale")
    assert planner.db.fetchone("SELECT status FROM tasks WHERE id=?", (ids[0],))["status"] == "completed"


def test_dependencies_and_future_work_are_not_todays_focus(planner):
    plan = proposal()
    later = deepcopy(plan["tasks"][0])
    later.update(key="synthesis", depends_on=["compare"], scheduled_for="2026-09-14")
    plan["tasks"].append(later)
    ids = planner.apply_plan(plan, context=planner.context(NOW), run_id="test")
    schedule = MasterPlanner(planner.db).task_schedule(ids[1], NOW)
    assert schedule["future"] and schedule["waiting_for"] == [ids[0]]
    assert not schedule["ready_today"]


def test_daily_tick_waits_for_local_time_and_catches_up(planner):
    class Dispatcher:
        def enqueue_task(self, task_id):
            return {"task_id": task_id, "status": "queued"}
    planner.configure({"enabled": True})
    assert planner.tick(datetime(2026, 9, 13, 0, tzinfo=timezone.utc), Dispatcher())["status"] == "waiting"
    assert planner.tick(NOW, Dispatcher())["status"] == "queued"


def test_research_plan_survives_rebuild_and_updates_legacy_task(planner):
    from master_os.core.reducer import rebuild_state
    source = planner.events.register_source("user", "legacy", "legacy")
    planner.commands.emit("task.created", source.id, {"id": "legacy", "title": "Meeting template"})
    plan = proposal()
    plan["tasks"][0]["existing_task_id"] = "legacy"
    planner.apply_plan(plan, context=planner.context(NOW), run_id="test")
    assert planner.db.fetchone("SELECT title FROM tasks WHERE id='legacy'")["title"] == "Compare nearest work"
    before = task_work(planner.db, "legacy")
    rebuild_state(planner.db)
    assert task_work(planner.db, "legacy") == before
    assert planner.db.fetchone("SELECT title FROM tasks WHERE id='legacy'")["title"] == "Compare nearest work"


def test_progress_api_saves_text_without_claiming_completed_work(tmp_path):
    from fastapi.testclient import TestClient
    from master_os.web.api import create_app
    db = MasterDatabase(tmp_path / 'master.db')
    with TestClient(create_app(db, tmp_path)) as client:
        result = client.post('/api/research/progress', json={'text': 'Read limitations; still checking the definition.'})
        assert result.status_code == 200
        assert result.json()['planning']['status'] == 'needs_meeting'
        status = client.get('/api/research/planning').json()
        assert status['history'][0]['text'].startswith('Read limitations')
        assert not db.fetchall('SELECT * FROM tasks')
    db.close()
