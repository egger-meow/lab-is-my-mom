# lab-is-my-mom = Master OS

Local-first autonomous operating system for my entire 2-year master's degree and NYCU NLP Lab life (Prof. An-Zi Yen).

Master OS acts as an autonomous operating runtime: observing the lab, remembering research history, distinguishing obligations from tasks, preparing advisor meetings, coordinating local coding agents (Codex / Antigravity) in isolated worktrees, tracking findings and failure memory, and surfacing critical judgments through the Master Cockpit.

---

## ⚡ Master OS 快速上手 (Quick Start)

### 1. 安裝與同步環境
```bash
uv sync
```

### 2. 啟動 Master OS 本地 Mothership 與 Web Cockpit
```bash
uv run master-os start --host 0.0.0.0 --port 8000
```
- 開啟瀏覽器訪問：`http://localhost:8000/` (支援手機透過 Tailscale 遠端連線)
- 介面全面繁體中文，集中回答 5 大核心問題：
  1. **當前最重要 (What matters now?)**：關鍵焦點任務、建議代理與預估時長
  2. **未來義務與死線 (What is coming?)**：下次個人 Meeting、每週一 Seminar 與生存紅線
  3. **近期變化與實驗突破 (What changed?)**：已驗證之 Findings 與實證 Artifacts
  4. **Agent 執行動態 (What are agents doing?)**：Codex 沙盒執行歷程與 AI Scheduler
  5. **等待你裁量與審批 (What needs me?)**：Post-meeting Slack 回報草稿審批、國網/API 資源防呆

### 3. 命令列診斷與管理
```bash
# 檢查研究進展、Master Health 假進度警報與關鍵路徑
uv run master-os status

# 系統健康度與資料庫完整性檢驗
uv run master-os doctor

# 建立原子性 SQLite 快照
uv run master-os backup

# 確定性自 Event 歷史還原 Current State
uv run master-os rebuild-state

# 匯入會議逐字稿 / 筆記 (自動萃取 Commitments、Obligations、Tasks 並產出 Slack 草稿)
uv run master-os meeting ingest M-20260910 path/to/transcript.txt

# 產出符合顏安孜老師規範的 3 階段個人 Meeting Pack 大綱
uv run master-os meeting pack M-20260917

# 自主派工 Codex 在獨立 Git Worktree 推進關鍵任務
uv run master-os dispatch T-193
```

---

## 📚 保留之文獻引擎 (Research OS Engine)

原有的 Research OS 保持完整功能，作為 Master OS 的文獻探勘與論文解析器官：

```bash
uv run research-os bootstrap --professor-url https://azyen0522.github.io/ --seed-file "NYCU NLP Lab Intro.pdf"
uv run research-os papers an-zi-yen
uv run research-os search "routing"
uv run research-os report an-zi-yen
uv run research-os dashboard an-zi-yen
```

資料庫分別儲存於：
- Master OS 核心資料庫：`.master-os/master.db` (Append-only Events + Assertions + Current State + Relations Graph)
- Research OS 文獻資料庫：`.research-os/research.db`

