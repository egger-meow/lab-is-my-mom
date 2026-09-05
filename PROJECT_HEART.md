# lab-is-my-mom = Master OS

## Mission

Build a local-first autonomous operating system for my entire two-year master's degree and NYCU NLP Lab life under Prof. An-Zi Yen.

This is not a todo app and not only a paper reader. It is a master's-student operating runtime that continuously turns evidence into useful research progress while minimizing manual operating labor.

```text
observe → preserve evidence → interpret → plan → execute authorized work → verify → remember
```

The student should mainly spend time on judgment, research taste, advisor interaction, and decisions that genuinely require a human.

The original Research OS remains a first-class Literature Engine. Its crawl, paper resolution, full-text processing, corpus, provenance, and professor research-map capabilities must be preserved.

---

## Core laws

### 1. Durable memory lives in Master OS, not model sessions

Agents are replaceable workers. Models and providers will change during the degree.

Durable state includes:

- append-only source/domain events;
- relational current state;
- assertions with authority/confidence;
- provenance and relation graph;
- meetings, obligations, tasks, decisions, experiments, findings, failures;
- artifacts and agent-run history.

Important history is never silently overwritten.

### 2. Evidence before truth

Preserve the distinction between:

```text
source event ≠ interpretation
paper claim ≠ reproduced result
advisor wording ≠ confirmed commitment
agent finding ≠ validated finding
activity ≠ research progress
```

High-impact semantic changes require explicit confirmation when evidence is ambiguous.

Authority precedence:

```text
user explicit decision/config
    > verified source fact
    > confirmed semantic interpretation
    > agent interpretation
    > heuristic/inference
```

### 3. Automate toil, surface judgment

Local, reversible, already-authorized work may run automatically.

The system must not silently:

- merge `main`;
- send Slack/email;
- publish externally;
- use paid or gated compute;
- reinterpret ambiguous advisor direction as confirmed truth.

Those actions remain policy/approval gated.

### 4. Crash-safe by design

The system is expected to run for two years on a personal machine and survive reboots, Windows Update, agent crashes, auth failures, and model/provider churn.

Required properties:

- SQLite WAL and deterministic current-state rebuild;
- idempotent/deduplicated event ingestion;
- canonical event + materialization transaction boundary;
- durable Agent Run queue;
- isolated worktrees;
- heartbeats and interrupted-run recovery;
- daily verified DB snapshots;
- system diagnostics and stale-runtime detection;
- boot/login autostart.

---

## Runtime architecture

```text
Slack / Email / Drive / Meetings / Papers / Git / Files / Experiments
                              │
                              ▼
                       Source Adapters
                              │
                              ▼
┌──────────────────────── MASTER CORE ────────────────────────┐
│ Append-only Event History                                  │
│ Assertions + Authority Resolution                          │
│ Relational Current State                                   │
│ Provenance / Relation Graph                                │
│ Artifact Registry                                          │
└────────────────────────────┬────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
     Master Planner      AI Scheduler      Master Critic
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                     Durable Agent Queue
                             │
                 Codex / Antigravity / future
                             │
                  isolated Git worktrees
```

The Web Cockpit answers five questions:

1. What matters now?
2. What is coming?
3. What changed?
4. What are agents doing?
5. What needs me?

---

## Agent runtime contract

Every agent receives a bounded Work Packet containing only relevant task context, permissions, acceptance criteria, expected artifacts, and known failure memory.

Agent execution is stateless from the model's perspective. Long-term memory belongs to Master OS.

Normal autonomous local path:

```text
task
 → durable queued Agent Run
 → frozen Work Packet artifact
 → isolated worktree
 → executor
 → checks / observed result
 → artifact registry
 → canonical run/task state
```

Web dispatch must return immediately with a `RUN-*` identity. Long-running agent work must not hold an HTTP request open.

Interrupted runs preserve their worktree and evidence. Recovery supports inspect, resume, fresh retry, or abandon, with lineage retained.

---

## Scheduler contract

Schedules are data, not hardcoded cron behavior.

Supported trigger families include:

- time/weekly schedule;
- interval;
- event;
- relative-to-meeting.

A scheduled routine may dispatch local autonomous work only when its autonomy policy explicitly allows it. The Supervisor pumps the durable queue independently of the Web UI.

Advisor meeting schedules must remain editable and relative routines must follow the current meeting time rather than stale hardcoded dates.

---

## Lab workflow

Machine-readable lab protocol should encode real operating rules instead of leaving PDFs passive.

Examples include:

- advisor meeting preparation and post-meeting Slack-summary obligation;
- Seminar rotation/readiness;
- OpenAI/API cost approval boundaries;
- NCHC/H100 resource warnings and container cleanup risk.

Do not invent missing graduation, course, TA, compute, or administrative requirements. Add them only from verified user/lab/university sources.

---

## Research OS / Literature Engine

Given a professor/lab URL, Research OS should continue to:

- crawl bounded professor/lab/publication sources;
- identify professor-authored papers;
- resolve and deduplicate scholarly metadata;
- fetch legally accessible full text;
- preserve PDF hashes and provenance;
- extract/process papers;
- generate useful reading support and research maps;
- keep inaccessible/unresolved items explicit rather than fabricating them.

The architecture should remain reusable for another professor URL, while professor-specific hints stay in configuration.

Important distinctions:

```text
webpage mention ≠ authored paper
paper metadata ≠ downloaded full text
paper statement ≠ builder interpretation
reported result ≠ reproduced result
```

Everything important keeps provenance.

---

## Local-first deployment

Desktop is the mothership. Phone is a remote cockpit.

Default service bind is loopback:

```bash
uv run master-os start --host 127.0.0.1 --port 8000
```

Use Tailscale Serve for remote access instead of exposing the service broadly on the LAN.

Autostart must be user-scoped and secret-free:

```bash
uv run master-os autostart install
```

Current supported startup mechanisms:

- Windows Scheduled Task on login;
- Linux user systemd.

---

## Definition of a healthy Master OS

A healthy system can:

- preserve source history and rebuild current state;
- show the current critical path and obligations;
- ingest meeting evidence without silently promoting ambiguous semantics;
- queue and execute authorized local agent jobs without blocking Web requests;
- recover interrupted runs without deleting evidence;
- keep automated snapshots fresh and integrity-checked;
- report stale supervisor/queue/artifact/backup conditions through `master-os doctor`;
- keep Research OS corpus functions intact;
- survive model/provider changes because durable memory and policy live outside the agent.

The optimization target is not maximum automation. It is **maximum useful research progress per unit of human judgment, without sacrificing provenance, reversibility, safety, or graduation reliability.**
