# lab-is-my-mom = Master OS

Local-first autonomous operating system for my entire 2-year master's degree and NYCU NLP Lab life (Prof. An-Zi Yen).

Master OS acts as an autonomous operating runtime: observing the lab, remembering research history, distinguishing obligations from tasks, preparing advisor meetings, coordinating local coding agents (Codex / Antigravity) in isolated worktrees, tracking findings and failure memory, and surfacing critical judgments through the Master Cockpit.

The durable brain is local state and evidence. Agents are replaceable workers. Important history is append-only, current state is rebuildable, high-impact semantic changes remain approval-gated, and local authorized agent work can run autonomously.

---

## ⚡ Master OS 快速上手

### 1. 安裝與同步環境

```bash
uv sync
```

### 2. 啟動本地 Mothership

```bash
uv run master-os start --host 127.0.0.1 --port 8000
```

開啟 `http://127.0.0.1:8000/`。遠端手機存取建議用 Tailscale Serve 代理 loopback，不直接把服務暴露到整個 LAN。

Web Cockpit 集中回答五件事：

1. **What matters now?** 當前關鍵焦點、理由與下一步。
2. **What is coming?** Meeting、Seminar、Obligations 與 deadline。
3. **What changed?** Findings、Artifacts、實驗與近期變化。
4. **What are agents doing?** queued / running / completed / interrupted Agent Runs。
5. **What needs me?** 高影響語意確認、外部動作、成本與 interrupted-run recovery。

### 3. 設成開機 / 登入自動啟動

```bash
uv run master-os autostart install
uv run master-os autostart status
```

目前支援：

- Windows user-scoped Scheduled Task (`ONLOGON`)
- Linux user `systemd`

啟動命令不會把 Slack token、API key 或其他 secrets 寫進 autostart 設定。

移除：

```bash
uv run master-os autostart uninstall
```

### 4. 命令列診斷與管理

```bash
# 研究進展、Critical Path、Master Health
uv run master-os status

# DB integrity、backup freshness、supervisor heartbeat、agent queue、artifact health
uv run master-os doctor

# 手動建立一致性 SQLite snapshot
uv run master-os backup

# 從 canonical event history 重建 relational current state
uv run master-os rebuild-state

# 匯入 advisor meeting 逐字稿 / 筆記
uv run master-os meeting ingest M-20260910 path/to/transcript.txt

# 產出 Meeting Pack
uv run master-os meeting pack M-20260917

# CLI 直接執行一個已授權 autonomous task
uv run master-os dispatch T-193
```

---

## 🧠 Runtime architecture

```text
Slack / Files / Meetings / Papers / Git / Experiments
                    │
                    ▼
             source collectors
                    │
                    ▼
┌──────────────── MASTER CORE ────────────────┐
│ append-only events                         │
│ assertions + authority precedence          │
│ relational current state                   │
│ provenance / relations graph               │
│ artifact registry                          │
└───────────────────┬────────────────────────┘
                    │
       ┌────────────┼──────────────┐
       ▼            ▼              ▼
   Planner      AI Scheduler    Master Critic
       │            │
       └──────┬─────┘
              ▼
       Durable Agent Queue
              │
      Codex / future adapters
              │
      isolated Git worktrees
```

### Agent execution

Web dispatch is non-blocking:

```text
POST /api/tasks/<task>/dispatch
        ↓
 durable queued Agent Run + frozen Work Packet
        ↓
 immediate HTTP 202 + RUN-id
        ↓
 bounded background worker
        ↓
 worktree → executor → validation → artifacts → result state
```

The Supervisor also pumps durable queued runs, so queued work can continue after a restart instead of depending on one HTTP request staying alive.

Interrupted runs are preserved rather than deleted. Cockpit recovery supports inspection, resume, fresh retry, or abandon, with recovery provenance retained.

### Backups and recovery

The long-lived Supervisor creates and verifies a Master DB snapshot when no fresh snapshot exists, keeps daily backups fresh, and retains a bounded recent history. `master-os doctor` reports stale/corrupt backups and stale supervisor heartbeats.

Canonical state can be rebuilt from event history with:

```bash
uv run master-os rebuild-state
```

---

## 🔐 Autonomy boundary

Local, already-authorized work may run autonomously in isolated worktrees. The system must not silently:

- merge `main`;
- send Slack or email;
- publish externally;
- use paid / gated compute;
- turn ambiguous advisor language into confirmed research truth.

Those actions remain policy / approval gated.

---

## 📚 Research OS Engine

原有 Research OS 保持作為 Master OS 的文獻探勘與論文解析器官：

```bash
uv run research-os bootstrap --professor-url https://azyen0522.github.io/ --seed-file "NYCU NLP Lab Intro.pdf"
uv run research-os papers an-zi-yen
uv run research-os search "routing"
uv run research-os report an-zi-yen
uv run research-os dashboard an-zi-yen
```

資料庫：

- Master OS: `.master-os/master.db`
- Research OS: `.research-os/research.db`

Research OS 的 corpus / provenance 能力保留；Master OS 負責跨來源記憶、規劃、meeting workflow、agent orchestration、health、recovery 與整個碩士生 runtime。
