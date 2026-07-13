# 寶寶式完整導讀：Personalized Graph-Empowered LLM

> 導讀狀態：已核對 arXiv 9 頁全文（2602.21862v1）。

## 一句話故事

一個人重講往事時，可能講對、講錯、補充新細節，或漏掉舊事件。LLM 很會理解文字，但可能憑感覺亂補；個人知識圖譜較死板，卻能保存具體事件。GER 框架讓兩者互相檢查，再決定是否提醒或修正使用者。

## 五種事件先分清

- Consistent：新敘述與舊記錄一致。
- Inconsistent：新敘述與舊事實衝突，需要糾正。
- Additional：新增且不衝突的細節，應更新知識圖譜。
- Forgotten：舊故事有、新敘述漏掉，應提醒。
- Unforgotten：舊事件在新敘述中仍有提及。

前三類以舊故事 A 為參照檢查新故事 B；Forgotten/Unforgotten 則反向確認 A 的事件是否出現在 B。方向不同是最容易看錯的地方。

## 閱讀路線

### 第一站：第 1–3 頁，看任務與標籤轉換

作者先把五分類暫時壓成 Relevant/Irrelevant：Consistent、Inconsistent、Unforgotten 映成 Relevant；Additional、Forgotten 映成 Irrelevant。這不是說後兩者不重要，而是說它們在參考故事中找不到對應資訊。最後再由 label mapper 還原五種服務。

### 第二站：第 3–4 頁，讀 Figure 1 的三個模組

1. Base module 直接看參考故事與 query，先判 Relevant/Irrelevant。
2. Support module 同時用 KG 相似度與 LLM 找 supporting events，只取兩邊交集以降低雜訊。
3. Correction module 比較兩個判斷：一致就保留；base 說有關、support 說無關時用 rethinking prompt；反過來則把找到的 support event 交給 exploration prompt。

像寶寶版陪審團：第一人先投票、第二人拿證據、第三人處理兩票不一致。

### 第三站：第 4–6 頁，看實驗而不是只看總結

資料使用 NIR 的兩次人生故事重述。主要比較 GPT-3.5、Llama3-70B、SEEN Base/Large 與 GER。GER 在 Additional 與 Forgotten 的 recall 分別為 0.8338、0.8635；Forgotten 相對基線改善達 McNemar `p < 0.05`。但 Inconsistent 的 recall 只有 0.0417，不能說五類全面提升。

### 第四站：第 6–7 頁，看消融與錯誤分析

base module 能力主導上限；把 support 換成 ground truth 時各類明顯提升，表示瓶頸常在「證據找得準不準」。直接拿 LLM 做五分類表現較差。對 Additional/Forgotten，LLM 常把全新資訊誤認為與舊故事相關；對改寫幅度大的相同事件，又可能找不到關聯。

## 真正貢獻與風險

GER 的價值是模組可替換、無須為每次新增 lifelog 重新訓練整套模型，並把結構化個人記憶帶入修正流程。它仍是離線資料集上的 pilot：尚非可在日常生活直接運作的端到端系統，而且個人知識圖譜包含高度敏感資訊，論文明確把隱私與資料安全留為未來工作。

## 讀完自測

1. 為何 Additional 和 Forgotten 被暫時映成 Irrelevant？
2. support module 為何取 KG 與 LLM 結果的交集？
3. GER 哪些類別最成功、哪類仍明顯失敗？
4. 若真的部署，除了 F-score 還必須評估什麼？

參考答案：1. 依任務方向，它們在參考故事中沒有相符事件。2. 減少任一分類器單獨帶來的無關事件。3. Additional/Forgotten 較有改善，Inconsistent 仍弱。4. 隱私、錯誤提醒造成的傷害、延遲、更新正確性與使用者是否信任／能修正系統。

