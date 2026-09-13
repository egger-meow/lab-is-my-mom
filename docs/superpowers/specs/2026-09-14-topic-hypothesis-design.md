# Research Topic 與 Hypothesis Elimination 設計規格

日期：2026-09-14

狀態：設計草案，供實作前審閱；尚未實作。

已確認方向：Agent 準備與分析、使用者啟動 Colab、使用者決定 selected / killed。

## 1. 目的與成功定義

讓 Master OS 管理研究選題的探索、證據與投入決策。每個活躍題目應能回答：目前主張是什麼、有哪些依據、最關鍵的不確定性是什麼、下一個可負擔的驗證是什麼，以及什麼情況下停止投入。

研究選題包含科學假說驗證與資源取捨。假說不成立、目前資源不足、實驗執行失敗必須分開記錄。selected 表示人決定投入，不表示假說已被證明。

成功條件：

- 從一次選題決策可追溯到當時的假說版本、證據與原始來源。
- Colab 中斷、無效結果與重複匯入不會造成錯誤研究結論。
- Agent 能準備下一步與決策建議，但不能代替使用者選題或停止題目。
- 狀態可從事件歷史重建，不依賴模型對話記憶。
- Cockpit 與 meeting pack 能顯示研究判斷的變化，而非只列完成的任務。

## 2. 現有系統與設計選擇

目前 repo 已有以下可沿用部分：

- `src/master_os/core/models.py`：Experiment、Finding、Decision、Artifact、Assertion 等模型；Experiment 已區分 status 與 validity_status。
- `src/master_os/core/database.py`、`events.py`、`commands.py`、`reducer.py`：SQLite、事件與目前狀態。
- `src/master_os/agents/packet.py`：有權限、驗收條件、產物與 failure memory 的 AgentJobPacket。
- `src/master_os/web/api.py`：研究概覽與 `research_profile/current/topic` 單一研究題目 assertion。
- Research OS：保留為文獻與來源引擎。

選項比較：

| 選項 | 取捨 |
| --- | --- |
| Ideas 加 status | 修改少，但無法可靠處理假說版本與證據適用範圍 |
| Topic + Hypothesis + Evidence | 採用；沿用既有核心，補足研究決策關聯 |
| 全自動遠端研究平台 | 延後；調度、費用與遠端環境管理超出第一版需求 |

第一版不建置遠端 GPU 調度、Colab 背景控制、付費算力啟動、對外訊息傳送或自動選題。Notebook 是可替換執行介面，正式歷史留在 Master OS。

## 3. 領域模型

以下是新增或擴充的邏輯模型；實作須沿用現有 migration、command 與 reducer 慣例。

| 物件 | 核心欄位與責任 |
| --- | --- |
| Topic | id、title、research_question、status、revision、current_hypothesis_version_id、next_action、blockers、created_at、updated_at |
| HypothesisVersion | id、topic_id、version、statement、scope、assumptions、supersedes_id、source_refs；建立後不可覆寫 |
| ExplorationPolicy | topic_id、hypothesis_version_id、最低可行性檢查、否證條件、投入停止條件、時間與算力上限；變更有版本 |
| EvidenceLink | id、topic_id、hypothesis_version_id、source_refs、finding_id（可選）、attempt_id（可選）、stance、validation_status、limitations、supersedes_id |
| AdvisorSignal | id、meeting_id、source_ref 與原文位置、quote、interpretation、confirmation_status、topic_id、hypothesis_version_id（可選） |
| ExperimentPlan | 擴充既有 Experiment；關聯 topic_id、hypothesis_version_id、不可變 packet artifact、判定規則版本 |
| ExperimentAttempt | id、experiment_id、packet_hash、execution_status、validity_status、result_artifact_id、retry_of、開始與結束時間 |
| Decision | 沿用既有 Decision，以事件與關聯保存 actor、前後狀態、rationale、證據 ID、假說版本及取代的決策 |

Topic 可有多個歷史版本；第一版同時只有一個目前核心假說版本。需要比較不同核心主張時，建立相關聯的 Topic，避免一張卡承載無界的假說樹。

EvidenceLink 是來源對某版本主張的關係，不是另一份 Findings 資料庫。原文、論文、實驗產物由既有來源與 Artifact registry 保存；研究解讀可沿用 Finding。stance 為 supports / contradicts / inconclusive，validation_status 為 under_review / validated / rejected / superseded。

文獻中的結果只代表作者報告的主張，不等同本地重現。完整性檢查通過也不代表科學結論已驗證。可選的信心描述需附理由；第一版不以不透明的總分自動排列研究價值。

seed 只要求 title、research_question 與來源（允許標明 user idea）。其他欄位按階段要求，避免建立點子時填大表單。

## 4. 狀態與權限

```text
seed → exploring → viable → candidate → selected
任何非 killed 狀態 → killed
```

| 目標狀態 | 必要條件 |
| --- | --- |
| seed | 一句研究問題與來源 |
| exploring | 核心假說版本、下一個驗證、投入上限、適用的停止條件 |
| viable | 該版本預先指定的最低檢查通過，有已驗證的依據與已知限制 |
| candidate | viable 條件仍有效，具貢獻主張、closest work、novelty threats、成本與主要風險；advisor signal 可明確標為尚無 |
| selected | 從 candidate 由使用者明確決定，記錄範圍、理由與下一個里程碑 |
| killed | 使用者明確決定，記錄停止原因、依據與重啟條件 |

一般前進只允許相鄰階段。退回較早階段必須記錄原因；selected 的退出也須使用者決定。killed 重啟到 exploring 時要求新證據或條件變化與使用者確認，保留原 kill decision。

第一版所有正式階段變更由使用者操作；Agent 可建立 seed、補充來源、建立候選證據、提出下一步與轉移建議。為避免額外操作，使用者可在同一個「審查證據並更新階段」動作中完成相關確認。未來若開放中間階段自動轉移，必須是獨立且明確的政策設定。

任何 Topic 狀態都不可透過一般 assertion 寫入繞過轉移驗證。命令層統一檢查 actor、前置條件與 expected revision，拒絕過期畫面的衝突寫入。

selected 在第一版可同時存在多個 Topic；研究首頁另有最多一個明確設定的 primary_topic_id。選取新 primary 不會自動 kill 其他 selected Topic。

核心假說變更建立新版本。非 selected / killed Topic 啟用新版本時回到 exploring，重新評估門檻；selected / killed 的版本啟用須由使用者同時明確決定重新探索。舊證據不自動移植，新版本如沿用舊結果須建立有理由的新 EvidenceLink。

## 5. 停止條件與阻礙

停止條件分為：

- 假說否證：在指定資料、baseline、metric、容忍範圍與有效性前提下，結果不支持主張。
- 投入停止：預算、資料取得、時程或方向不適合繼續投入。

每條條件包含 id、類型、適用版本、判斷方式、證據要求與檢查結果。可機器判定的條件另含 metric、比較運算與門檻；語意條件由人判斷。

執行前凍結判定規則，看到結果後修改規則必須建立新版本並標記探索性分析，不可把它包裝成原先預設的檢驗。重複次數與容忍度由個別實驗指定，不設全域「差 5% 就淘汰」規則。

OOM、等待資料、認證失敗或 Colab 中斷先記錄為 attempt failure / blocker。達到投入上限時停止排入新的探索工作並提出決策需求，不能自動將假說判為錯誤或 Topic 設為 killed。Master OS 無法保證停止使用者已手動啟動的 Colab 工作，介面需如實呈現此限制。

## 6. Colab 實驗閉環

```text
Topic / Hypothesis
  → Agent 準備實驗與 notebook
  → Master OS 凍結 Experiment Packet
  → 使用者啟動 Colab
  → 輸出 Result Bundle
  → 使用者匯入 Master OS
  → 完整性檢查 → 有效性審查 → Evidence → 決策建議
```

### Experiment Packet v1

必填契約：schema_version、experiment_id、topic_id、hypothesis_version_id、policy_version、objective、code_ref（repository 與 commit / snapshot hash）、dataset_ref（來源、版本、split、可取得時的 checksum）、environment_ref、parameters、seeds、baseline、metrics（名稱、單位與方向）、validity_checks、decision_rules、budget、expected_artifacts。

Packet 以 canonical JSON 產生內容 hash，存入 Artifact registry。Agent 工作封包引用此 artifact；AgentRun 表示準備工作，ExperimentAttempt 表示實驗執行，兩者不可共用成功狀態。可使用合成資料驗證 notebook 接線，但產物必須標為 fixture，不能進入研究證據。

### Result Bundle v1

包含 manifest.json、metrics.json、logs 與 manifest 列出的必要產物。Manifest 必填 schema_version、experiment_id、attempt_id、packet_hash、實際 code / dataset / environment 識別、parameters、seeds、execution_status、started_at、finished_at、artifact 路徑及 hash。硬體與實際資源用量需記錄；未知用量明確標 unknown。

使用者每次重新執行建立新的 attempt_id，retry_of 指向先前 attempt。第一版不支援續跑同一 attempt；中斷後重跑視為新 attempt。Notebook 可輸出失敗或中斷結果，若來不及匯出，由使用者標記中斷，不能只憑沒有回報推定失敗或完成。

匯入流程：

1. 驗證 schema、必要檔案、hash、ID 關聯、packet hash 與執行參數；不執行 bundle 內程式。
2. 拒絕絕對路徑、目錄穿越與符號連結產物；限制上傳與解壓大小，避免意外覆寫 workspace。
3. 以 attempt_id 及 bundle hash 去重：相同內容回傳既有結果；同 ID 不同內容回報衝突，不覆寫。
4. 結果先進 staging，驗證完成後發布不可變產物，再以單一資料庫交易記錄 canonical event 與狀態。失敗交易留下的未引用產物可清理；不可留下指向未完成檔案的正式證據。
5. completed 只表示程式執行完成。基於 baseline、資料洩漏檢查、split、指標、種子與預定規則，產生有效性報告供人確認。
6. 有效性確認後建立或驗證 EvidenceLink；無法判定的結果保持 inconclusive / under_review，不自動推進 Topic。

參數偏移、缺 baseline、NaN 指標或缺必要產物的結果可保留供調查，但不能計入預定門檻的通過證據。舊版本結果仍可匯入，只連到原版本，顯示與目前假說不一致。

可沿用 Experiment validity_status：under_review / valid / partially_valid / invalid。partially_valid 僅對明確列出的檢查提供依據，不能當成整個實驗通過。ExecutionAttempt 狀態為 prepared / running / completed / failed / interrupted / cancelled；只有已觀察或使用者回報的狀態才可記錄。

## 7. Advisor、Planner 與 Cockpit

AdvisorSignal 保留原文、會議時間與來源位置，將原文與 Agent 解讀分欄。confirmation_status 為 unconfirmed / confirmed / rejected。未確認的語意不能變成承諾、選題決策或自動任務。

Meeting Pack 按 Topic 彙整：上次假說、這週新證據、仍未知的問題、成本、建議決策及要問老師的一個具體問題。Meeting 後將回饋連回相同 Topic；同來源位置與 Topic 的重複擷取需去重。

Planner 只安排已授權的工作，引用 topic_id、hypothesis_version_id 與預期產物。排序理由以重要不確定性、可辨別性、成本與截止時間呈現，不宣稱模型分數是真實研究價值。killed Topic 不再新增探索任務；既有工作保留歷史，排隊中任務需重新檢查 Topic 狀態，已執行的遠端工作不假裝已被停止。

探索上限預設建議三個 exploring，可由使用者調整。超過時提示取捨並暫停新增自動探索排程，使用者可明確覆寫；不丟棄新 seed。

Cockpit 包含：

- 六階段看板；卡片顯示核心問題、下一步、blocker 與新證據。
- Topic 詳情：假說版本、支持／反對／不確定證據、實驗、advisor signals、決策歷史。
- Needs me：待審有效性、停止條件觸發、超出投入上限、選題建議。
- Today：優先顯示值得重新判斷的題目與已授權下一步。
- 狀態變更畫面：列出必要條件、證據與缺項；拖動卡片也走相同驗證。

## 8. 事件、相容性與恢復

新增事件涵蓋 topic.created、hypothesis.version_created、hypothesis.activated、topic.policy_revised、topic.transitioned、topic.primary_changed、evidence.linked、evidence.reviewed、advisor_signal.recorded / reviewed、experiment.packet_frozen、experiment.attempt_recorded、experiment.result_imported、experiment.validity_reviewed。事件含 schema_version、actor、來源、明確時間與相關版本。

命令驗證與 canonical event / materialization 在同一交易邊界內完成；reducer 只依保存的事件資料重播，不在重建時重新呼叫模型或重算文獻結論。被取代、拒絕或撤回的證據保留歷史；撤回會讓依賴它的門檻顯示需重審，不靜默修改人的選題決策。

第一版採加法 migration，保留既有 Experiment、Finding、Decision 與研究 API。新增 Topic API 使用獨立欄位；舊 `/api/research/context` 繼續讀寫 legacy topic 文字，不隱式建立 selected 或更新 primary_topic_id。Cockpit 有 primary 時顯示 primary，否則顯示 legacy context 並提供使用者確認的「建立 seed」操作。遷移不得自動推論舊題目已被選定。

Topic 寫入介面至少提供建立、更新描述、建立／啟用假說版本、提議／執行轉移、primary 選擇、證據連結與審查、封包匯出及結果匯入。所有 mutation 都經 domain command，不能讓一般欄位 patch 改寫 status 或版本歷史。

## 9. 分階段交付與驗收

### 第一階段：選題核心

交付 Topic、版本、EvidenceLink、決策命令、事件重建、相容性與基本看板。

驗收：

- seed 可輕量建立；缺探索規則不能進 exploring，缺有效證據不能進 viable。
- Agent 無法透過任何寫入路徑將 Topic 設為 selected / killed。
- 相同 revision 的競爭更新只有一個成功，另一個收到衝突。
- 假說改版後舊證據仍可查閱，不能自動滿足新版門檻。
- 狀態重建後 Topic、版本、決策與 primary 一致。
- 既有 research context 與實驗／finding 頁面行為相容。

### 第二階段：Colab 閉環

交付 packet 與 bundle schema、notebook 範本、attempt 管理、匯入與有效性審查。

驗收：

- 用明確標示的 fixture 驗證成功、失敗、中斷、缺 baseline、參數不符及重複匯入。
- 相同 attempt 不同 bundle 產生衝突；路徑穿越與損壞 hash 被拒絕。
- 模擬匯入途中中斷，恢復後不產生半份正式證據或重複結果。
- 一次由使用者啟動的真實 Colab 執行可回傳並追溯至凍結 packet；fixture 測試不能替代這項整合驗收。
- completed 不會自行推進 viable；無效結果不會觸發科學否證。

### 第三階段：研究工作流

交付 Meeting Pack、AdvisorSignal、Planner 關聯、探索上限與 Needs me。

驗收：

- 未確認的老師語句不會變成已選題或已確認承諾。
- meeting pack 能比較前後證據，且每個引用回到原始來源。
- killed、版本過期或超額 Topic 不會被自動排入新的探索工作。
- 撤回關鍵證據會產生重審需求，但不覆寫人的決策。
- 可完整走過 seed → exploring → viable → candidate → selected，另走停止與重啟路徑並檢查歷史。

## 10. 實作前審閱重點

本規格採用以下具體預設：第一版正式狀態轉移皆由人確認；允許多個 selected、最多一個 primary；探索上限建議三個；Colab 手動啟動與匯回；不建立自動遠端算力調度。

審閱確認後，再依三個交付階段形成實作計畫。這份文件本身不代表功能、migration 或 Colab 整合已完成。
