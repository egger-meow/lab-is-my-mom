# Phase 1: Research Topic & Hypothesis Elimination Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first-class Research Topic & Hypothesis Elimination core in Master OS, providing domain models, event-sourced persistence with optimistic locking, human-gated lifecycle state transitions, backward-compatible APIs, and a 6-stage Kanban board.

**Architecture:** Implement Topic, HypothesisVersion, ExplorationPolicy, EvidenceLink, and AdvisorSignal models with SQLite backing. Mutations flow strictly through `DomainCommandBus` into canonical append-only events (`topic.created`, `topic.transitioned`, etc.) and reduce to relational tables atomically. An optimistic locking mechanism (`revision` / `expected_revision`) and transition validator enforce prerequisite gates and ensure only humans can transition a topic to `selected` or `killed`.

**Tech Stack:** Python 3.11+, SQLite 3 (WAL mode), FastAPI, Vanilla JS / HTML5 Web Cockpit, Pytest.

**Spec:** [`docs/superpowers/specs/2026-09-14-topic-hypothesis-design.md`](file:///c:/IDEA/lab-is-my-mom/docs/superpowers/specs/2026-09-14-topic-hypothesis-design.md)

## Global Constraints

- **Real Data Fidelity**: NEVER use fake, synthetic, or mock data in runtime code, schemas, or database records. Test fixtures must be clearly demarcated as fixtures.
- **Authority Gate**: Agent can propose seed, propose transitions, and link candidate evidence, but CANNOT transition a topic to `selected` or `killed`. Only `actor="user"` may execute `selected` or `killed`.
- **Assertion Bypass Prevention**: Topic status and hypothesis version cannot be mutated via generic assertion projection; all state mutations MUST pass through domain commands and `DomainCommandBus`.
- **Crash-Safe & Rebuildable**: Canonical events in the `events` table are immutable. `clear_materialized_state()` must reset all topic tables, and replaying events via `apply_event()` must deterministically reconstruct the current state.
- **Optimistic Concurrency**: Any state mutation must specify `expected_revision`. Stale writes raise `ConcurrencyConflictError` (HTTP 409).
- **Additive Migration**: Existing tables and endpoints (`/api/research/context`) must remain functional without regression.

---

### Task 1: Domain Models & Database Persistence (Schema & Rebuild)

**Files:**
- Modify: `src/master_os/core/models.py`
- Modify: `src/master_os/core/database.py`
- Test: `tests/test_topic_models.py`

**Interfaces:**
- Produces:
  - Models: `Topic`, `HypothesisVersion`, `ExplorationPolicy`, `EvidenceLink`, `AdvisorSignal`, `ExperimentAttempt` dataclasses in `src/master_os/core/models.py`
  - Tables: `topics`, `hypothesis_versions`, `exploration_policies`, `evidence_links`, `advisor_signals`, `experiment_attempts` in `SCHEMA_SQL`
  - Rebuild: `clear_materialized_state()` in `database.py` updated to clear topic tables.

- [ ] **Step 1: Write failing test for Topic domain models and schema initialization**

Create `tests/test_topic_models.py`:
```python
import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.models import (
    Topic,
    HypothesisVersion,
    ExplorationPolicy,
    EvidenceLink,
    AdvisorSignal,
    generate_id,
)

def test_topic_model_instantiation():
    topic = Topic(
        id=generate_id("TP-"),
        title="Contrastive Reranking for Low-Resource NLP",
        research_question="Does contrastive reranking improve zero-shot retrieval in low-resource settings?",
        status="seed",
        revision=1,
    )
    assert topic.status == "seed"
    assert topic.revision == 1
    assert topic.is_primary is False
    assert topic.blockers == []

def test_database_schema_initializes_topic_tables(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = MasterDatabase(db_path)
    
    # Verify tables exist
    tables = [r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "topics" in tables
    assert "hypothesis_versions" in tables
    assert "exploration_policies" in tables
    assert "evidence_links" in tables
    assert "advisor_signals" in tables
    assert "experiment_attempts" in tables

def test_clear_materialized_state_clears_topic_tables(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = MasterDatabase(db_path)
    
    topic_id = generate_id("TP-")
    db.execute(
        "INSERT INTO topics (id, title, research_question, status, revision, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (topic_id, "Test Topic", "Test Question", "seed", 1, "2026-09-14T00:00:00Z", "2026-09-14T00:00:00Z"),
    )
    db.commit()
    assert db.fetchone("SELECT id FROM topics WHERE id = ?", (topic_id,)) is not None
    
    db.clear_materialized_state()
    assert db.fetchone("SELECT id FROM topics WHERE id = ?", (topic_id,)) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_topic_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Topic' from 'master_os.core.models'`

- [ ] **Step 3: Implement domain models in `src/master_os/core/models.py`**

Add dataclasses to `src/master_os/core/models.py`:
```python
@dataclass
class Topic:
    id: str
    title: str
    research_question: str
    status: str = "seed"  # seed, exploring, viable, candidate, selected, killed
    revision: int = 1
    current_hypothesis_version_id: Optional[str] = None
    is_primary: bool = False
    next_action: str = ""
    blockers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class HypothesisVersion:
    id: str
    topic_id: str
    version: int
    statement: str
    scope: str = ""
    assumptions: list[str] = field(default_factory=list)
    supersedes_id: Optional[str] = None
    source_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)


@dataclass
class ExplorationPolicy:
    id: str
    topic_id: str
    hypothesis_version_id: str
    version: int = 1
    min_viable_checks: list[str] = field(default_factory=list)
    falsification_conditions: list[dict[str, Any]] = field(default_factory=list)
    stop_conditions: list[dict[str, Any]] = field(default_factory=list)
    budget_caps: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)


@dataclass
class EvidenceLink:
    id: str
    topic_id: str
    hypothesis_version_id: str
    source_refs: list[str] = field(default_factory=list)
    finding_id: Optional[str] = None
    attempt_id: Optional[str] = None
    stance: str = "inconclusive"  # supports, contradicts, inconclusive
    validation_status: str = "under_review"  # under_review, validated, rejected, superseded
    limitations: str = ""
    reason: str = ""
    supersedes_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class AdvisorSignal:
    id: str
    source_ref: str = ""
    source_location: str = ""
    quote: str = ""
    interpretation: str = ""
    confirmation_status: str = "unconfirmed"  # unconfirmed, confirmed, rejected
    meeting_id: Optional[str] = None
    topic_id: Optional[str] = None
    hypothesis_version_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class ExperimentAttempt:
    id: str
    experiment_id: str
    packet_hash: str
    execution_status: str = "prepared"  # prepared, running, completed, failed, interrupted, cancelled
    validity_status: str = "under_review"  # under_review, valid, partially_valid, invalid
    result_artifact_id: Optional[str] = None
    retry_of: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
```

- [ ] **Step 4: Update SQLite `SCHEMA_SQL` and `clear_materialized_state` in `src/master_os/core/database.py`**

Add table definitions to `SCHEMA_SQL`:
```sql
CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    research_question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'seed',
    revision INTEGER NOT NULL DEFAULT 1,
    current_hypothesis_version_id TEXT,
    is_primary INTEGER NOT NULL DEFAULT 0,
    next_action TEXT NOT NULL DEFAULT '',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);

CREATE TABLE IF NOT EXISTS hypothesis_versions (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id),
    version INTEGER NOT NULL,
    statement TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT '',
    assumptions_json TEXT NOT NULL DEFAULT '[]',
    supersedes_id TEXT REFERENCES hypothesis_versions(id),
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hypothesis_topic ON hypothesis_versions(topic_id, version);

CREATE TABLE IF NOT EXISTS exploration_policies (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id),
    hypothesis_version_id TEXT NOT NULL REFERENCES hypothesis_versions(id),
    version INTEGER NOT NULL DEFAULT 1,
    min_viable_checks_json TEXT NOT NULL DEFAULT '[]',
    falsification_conditions_json TEXT NOT NULL DEFAULT '[]',
    stop_conditions_json TEXT NOT NULL DEFAULT '[]',
    budget_caps_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id),
    hypothesis_version_id TEXT NOT NULL REFERENCES hypothesis_versions(id),
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    finding_id TEXT REFERENCES findings(id) ON DELETE SET NULL,
    attempt_id TEXT,
    stance TEXT NOT NULL DEFAULT 'inconclusive',
    validation_status TEXT NOT NULL DEFAULT 'under_review',
    limitations TEXT NOT NULL DEFAULT '',
    reason TEXT NOT NULL DEFAULT '',
    supersedes_id TEXT REFERENCES evidence_links(id),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_links_topic ON evidence_links(topic_id, hypothesis_version_id);

CREATE TABLE IF NOT EXISTS advisor_signals (
    id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL DEFAULT '',
    source_location TEXT NOT NULL DEFAULT '',
    quote TEXT NOT NULL DEFAULT '',
    interpretation TEXT NOT NULL DEFAULT '',
    confirmation_status TEXT NOT NULL DEFAULT 'unconfirmed',
    meeting_id TEXT REFERENCES meetings(id) ON DELETE SET NULL,
    topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    hypothesis_version_id TEXT REFERENCES hypothesis_versions(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_attempts (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    packet_hash TEXT NOT NULL,
    execution_status TEXT NOT NULL DEFAULT 'prepared',
    validity_status TEXT NOT NULL DEFAULT 'under_review',
    result_artifact_id TEXT REFERENCES artifacts(id) ON DELETE SET NULL,
    retry_of TEXT REFERENCES experiment_attempts(id) ON DELETE SET NULL,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL
);
```
Add tables to `clear_materialized_state()` deletion list in `src/master_os/core/database.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_topic_models.py -v`
Expected: PASS

- [ ] **Step 6: Commit changes**

```bash
git add src/master_os/core/models.py src/master_os/core/database.py tests/test_topic_models.py
git commit -m "feat(core): add topic and hypothesis domain models and sqlite schema"
```

---

### Task 2: Domain Commands, Optimistic Locking & Transition Validation

**Files:**
- Create: `src/master_os/core/topics.py`
- Modify: `src/master_os/core/commands.py`
- Test: `tests/test_topic_commands.py`

**Interfaces:**
- Consumes: `MasterDatabase`, `DomainCommandBus`, `EventStore`, `models.Topic`, `models.HypothesisVersion`
- Produces:
  - `TopicCommandService` class with methods:
    - `create_topic_seed(title, research_question, source_refs, actor) -> Topic`
    - `add_hypothesis_version(topic_id, statement, scope, assumptions, source_refs, actor) -> HypothesisVersion`
    - `activate_hypothesis_version(topic_id, version_id, expected_revision, actor) -> Topic`
    - `revise_policy(topic_id, version_id, min_viable_checks, falsification_conditions, stop_conditions, budget_caps, actor) -> ExplorationPolicy`
    - `link_evidence(topic_id, version_id, stance, validation_status, limitations, source_refs, finding_id, actor) -> EvidenceLink`
    - `review_evidence(evidence_id, validation_status, reason, actor) -> EvidenceLink`
    - `transition_status(topic_id, target_status, expected_revision, actor, rationale) -> Topic`
    - `set_primary_topic(topic_id, actor) -> None`
  - Exceptions: `ConcurrencyConflictError`, `InvalidTransitionError`, `PermissionError`

- [ ] **Step 1: Write failing test for Topic commands and transition rules**

Create `tests/test_topic_commands.py`:
```python
import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.commands import DomainCommandBus
from master_os.core.topics import (
    TopicCommandService,
    ConcurrencyConflictError,
    InvalidTransitionError,
    PermissionDeniedError,
)

def test_create_topic_seed(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    
    topic = service.create_topic_seed(
        title="Contrastive Reranker",
        research_question="Can contrastive loss improve small cross-encoders?",
        actor="user",
    )
    assert topic.status == "seed"
    assert topic.revision == 1
    assert topic.title == "Contrastive Reranker"

def test_transition_to_exploring_requires_hypothesis_and_policy(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    
    topic = service.create_topic_seed("Topic A", "Question A", actor="user")
    
    # Should fail because no hypothesis version and policy
    with pytest.raises(InvalidTransitionError, match="requires active hypothesis"):
        service.transition_status(topic.id, target_status="exploring", expected_revision=1, actor="user")
        
    hyp = service.add_hypothesis_version(topic.id, statement="Method X improves Y", actor="user")
    service.activate_hypothesis_version(topic.id, hyp.id, expected_revision=1, actor="user")
    service.revise_policy(topic.id, hyp.id, min_viable_checks=["check_baseline"], actor="user")
    
    # Now revision is updated to 2 after hypothesis activation
    updated = service.transition_status(topic.id, target_status="exploring", expected_revision=2, actor="user")
    assert updated.status == "exploring"
    assert updated.revision == 3

def test_agent_cannot_transition_to_selected_or_killed(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    
    topic = service.create_topic_seed("Topic B", "Question B", actor="user")
    
    # Agent tries to kill or select
    with pytest.raises(PermissionDeniedError, match="Only human user"):
        service.transition_status(topic.id, target_status="killed", expected_revision=1, actor="agent:codex", rationale="I decided to kill it")
        
    with pytest.raises(PermissionDeniedError, match="Only human user"):
        service.transition_status(topic.id, target_status="selected", expected_revision=1, actor="agent:antigravity", rationale="Looks good")

def test_optimistic_locking_conflict(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    
    topic = service.create_topic_seed("Topic C", "Question C", actor="user")
    
    # Passing wrong expected_revision
    with pytest.raises(ConcurrencyConflictError, match="Revision mismatch"):
        service.transition_status(topic.id, target_status="killed", expected_revision=999, actor="user", rationale="Drop it")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_topic_commands.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'master_os.core.topics'`

- [ ] **Step 3: Implement `src/master_os/core/topics.py`**

Implement validation logic, transition matrix, optimistic locking checks, and event emission using `DomainCommandBus.emit(...)`.
Events emitted:
- `topic.created`
- `hypothesis.version_created`
- `hypothesis.activated`
- `topic.policy_revised`
- `evidence.linked`
- `evidence.reviewed`
- `topic.transitioned`
- `topic.primary_changed`

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_topic_commands.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/master_os/core/topics.py tests/test_topic_commands.py
git commit -m "feat(core): implement topic domain service with optimistic locking and transition gates"
```

---

### Task 3: Event Reducer Materialization & Deterministic Rebuild

**Files:**
- Modify: `src/master_os/core/reducer.py`
- Test: `tests/test_topic_reducer.py`

**Interfaces:**
- Consumes: Canonical `Event` objects from `events` table
- Produces: State updates in `topics`, `hypothesis_versions`, `exploration_policies`, `evidence_links`

- [ ] **Step 1: Write failing test for topic event reduction and rebuild**

Create `tests/test_topic_reducer.py`:
```python
import pytest
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.commands import DomainCommandBus
from master_os.core.topics import TopicCommandService
from master_os.core.reducer import apply_event

def test_event_reduction_and_deterministic_rebuild(tmp_path: Path):
    db = MasterDatabase(tmp_path / "test.db")
    bus = DomainCommandBus(db)
    service = TopicCommandService(db, bus)
    
    # 1. Execute flow
    topic = service.create_topic_seed("Topic R", "Question R", actor="user")
    hyp = service.add_hypothesis_version(topic.id, "Statement R", actor="user")
    service.activate_hypothesis_version(topic.id, hyp.id, expected_revision=1, actor="user")
    service.revise_policy(topic.id, hyp.id, min_viable_checks=["check_1"], actor="user")
    service.transition_status(topic.id, "exploring", expected_revision=2, actor="user")
    
    row_before = db.fetchone("SELECT * FROM topics WHERE id = ?", (topic.id,))
    assert row_before["status"] == "exploring"
    assert row_before["revision"] == 3
    
    # 2. Clear materialized state
    db.clear_materialized_state()
    assert db.fetchone("SELECT * FROM topics WHERE id = ?", (topic.id,)) is None
    
    # 3. Replay all events from event store
    all_events = db.fetchall("SELECT * FROM events ORDER BY rowid ASC")
    for ev_row in all_events:
        from master_os.core.events import EventStore
        store = EventStore(db)
        event = store._row_to_event(ev_row)
        apply_event(db, event, commit=True)
        
    row_after = db.fetchone("SELECT * FROM topics WHERE id = ?", (topic.id,))
    assert row_after is not None
    assert row_after["status"] == "exploring"
    assert row_after["revision"] == 3
    assert row_after["current_hypothesis_version_id"] == hyp.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_topic_reducer.py -v`
Expected: FAIL because `apply_event` does not handle `topic.*`, `hypothesis.*`, `evidence.*` events yet.

- [ ] **Step 3: Implement event handlers in `src/master_os/core/reducer.py`**

Add handlers in `apply_event`:
- `topic.created` -> INSERT into `topics`
- `hypothesis.version_created` -> INSERT into `hypothesis_versions`
- `hypothesis.activated` -> UPDATE `topics.current_hypothesis_version_id`, increment revision
- `topic.policy_revised` -> INSERT into `exploration_policies`
- `evidence.linked` -> INSERT into `evidence_links`
- `evidence.reviewed` -> UPDATE `evidence_links.validation_status`, reason
- `topic.transitioned` -> UPDATE `topics.status`, revision, updated_at
- `topic.primary_changed` -> UPDATE `topics.is_primary` (set all to 0 except target)

Ensure assertion bypass prevention: Do not register `topic` in `_ASSERTION_TABLES`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_topic_reducer.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/master_os/core/reducer.py tests/test_topic_reducer.py
git commit -m "feat(core): implement topic event reducers for deterministic state replay"
```

---

### Task 4: Web API & Backward Compatibility

**Files:**
- Modify: `src/master_os/web/api.py`
- Test: `tests/test_topic_api.py`

**Interfaces:**
- Endpoints:
  - `GET /api/research/topics` -> list of topics with summary (status, revision, is_primary, evidence stats)
  - `POST /api/research/topics` -> create seed
  - `GET /api/research/topics/{topic_id}` -> full detail (topic, versions, policy, evidence links, attempts)
  - `POST /api/research/topics/{topic_id}/hypotheses` -> create version
  - `POST /api/research/topics/{topic_id}/hypotheses/{version_id}/activate` -> activate
  - `POST /api/research/topics/{topic_id}/policy` -> revise policy
  - `POST /api/research/topics/{topic_id}/transition` -> transition (returns 409 on revision conflict, 403 if agent attempts selected/killed)
  - `POST /api/research/topics/{topic_id}/primary` -> set primary
  - `POST /api/research/topics/{topic_id}/evidence` -> link evidence
  - `POST /api/research/topics/{topic_id}/evidence/{evidence_id}/review` -> review evidence
  - `GET /api/research/context` -> updated to return primary topic info if available, maintaining legacy fields

- [ ] **Step 1: Write failing test for Web API endpoints**

Create `tests/test_topic_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.web.api import create_app

@pytest.fixture
def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    app = create_app(db_path=db_path)
    return TestClient(app)

def test_api_topic_lifecycle(client: TestClient):
    # 1. Create seed
    resp = client.post("/api/research/topics", json={
        "title": "API Topic",
        "research_question": "Can we test this via HTTP?",
        "actor": "user"
    })
    assert resp.status_code == 200
    topic_data = resp.json()["topic"]
    topic_id = topic_data["id"]
    assert topic_data["status"] == "seed"
    assert topic_data["revision"] == 1
    
    # 2. Add and activate hypothesis
    resp = client.post(f"/api/research/topics/{topic_id}/hypotheses", json={
        "statement": "Hypothesis via API",
        "scope": "NLP",
        "actor": "user"
    })
    hyp_id = resp.json()["hypothesis"]["id"]
    
    resp = client.post(f"/api/research/topics/{topic_id}/hypotheses/{hyp_id}/activate", json={
        "expected_revision": 1,
        "actor": "user"
    })
    assert resp.status_code == 200
    assert resp.json()["topic"]["revision"] == 2
    
    # 3. Add policy
    resp = client.post(f"/api/research/topics/{topic_id}/policy", json={
        "hypothesis_version_id": hyp_id,
        "min_viable_checks": ["unit_test"],
        "actor": "user"
    })
    assert resp.status_code == 200
    
    # 4. Transition to exploring
    resp = client.post(f"/api/research/topics/{topic_id}/transition", json={
        "target_status": "exploring",
        "expected_revision": 2,
        "actor": "user"
    })
    assert resp.status_code == 200
    assert resp.json()["topic"]["status"] == "exploring"
    
    # 5. Optimistic lock collision
    resp = client.post(f"/api/research/topics/{topic_id}/transition", json={
        "target_status": "viable",
        "expected_revision": 1,  # Stale!
        "actor": "user"
    })
    assert resp.status_code == 409

def test_api_agent_forbidden_from_selected(client: TestClient):
    resp = client.post("/api/research/topics", json={
        "title": "Topic Agent Test",
        "research_question": "Will agent be blocked?",
        "actor": "user"
    })
    topic_id = resp.json()["topic"]["id"]
    
    # Agent tries to select
    resp = client.post(f"/api/research/topics/{topic_id}/transition", json={
        "target_status": "selected",
        "expected_revision": 1,
        "actor": "agent:codex"
    })
    assert resp.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_topic_api.py -v`
Expected: FAIL with 404 Not Found on `/api/research/topics`

- [ ] **Step 3: Implement endpoints in `src/master_os/web/api.py`**

Wire the endpoints in FastAPI, map exceptions (`ConcurrencyConflictError` -> 409, `PermissionDeniedError` -> 403, `InvalidTransitionError` -> 400).
Ensure `/api/research/context` reads the primary topic if set, without altering legacy format.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_topic_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/master_os/web/api.py tests/test_topic_api.py
git commit -m "feat(web): add research topic and hypothesis elimination api endpoints"
```

---

### Task 5: Web Cockpit 6-Stage Kanban Board & Detail View

**Files:**
- Modify: `src/master_os/web/static/index.html`
- Modify: `src/master_os/web/static/app.js`
- Test: `tests/test_topic_ui.py`

**Interfaces:**
- UI views:
  - 6-Stage Kanban column layout: `seed`, `exploring`, `viable`, `candidate`, `selected`, `killed`
  - Cards show: Title, Question, Next Action, Blockers, Evidence Badge (+count / -count / ?count), Primary Badge
  - Modal: Topic Detail (hypothesis versions, policies, evidence list, transition gate checklist with disabled button if requirements not satisfied)
  - Quick action: "Create Research Seed" button.

- [ ] **Step 1: Write test for Web UI integration**

Create `tests/test_topic_ui.py` (checking HTML contains Kanban containers and app.js contains topic functions):
```python
from pathlib import Path

def test_html_contains_topic_kanban_elements():
    html_path = Path("src/master_os/web/static/index.html")
    content = html_path.read_text(encoding="utf-8")
    assert "research-kanban" in content
    assert "stage-seed" in content
    assert "stage-exploring" in content
    assert "stage-viable" in content
    assert "stage-candidate" in content
    assert "stage-selected" in content
    assert "stage-killed" in content

def test_app_js_contains_topic_handlers():
    js_path = Path("src/master_os/web/static/app.js")
    content = js_path.read_text(encoding="utf-8")
    assert "fetchTopics" in content
    assert "transitionTopic" in content
    assert "createTopicSeed" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_topic_ui.py -v`
Expected: FAIL

- [ ] **Step 3: Update `index.html` and `app.js`**

Implement Kanban HTML markup and corresponding JS fetching, rendering, card click handling, and transition validation modal in `src/master_os/web/static/`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_topic_ui.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite regression**

Run: `uv run pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 6: Commit changes**

```bash
git add src/master_os/web/static/index.html src/master_os/web/static/app.js tests/test_topic_ui.py
git commit -m "feat(web): add 6-stage topic hypothesis kanban board and detail modal to cockpit"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-14-topic-hypothesis-phase1.md`.

Two execution options:
1. **Subagent-Driven (recommended)** - Fresh subagents per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using `executing-plans`, batch execution with checkpoints.
