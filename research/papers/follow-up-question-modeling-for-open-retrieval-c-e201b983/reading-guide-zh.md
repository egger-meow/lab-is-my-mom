# 預備導讀：Follow-up Question Modeling

> 狀態：已核對 WI-IAT 2025 議程與 SSRN DOI `10.2139/ssrn.4710309`；SSRN 顯示 35 頁作者稿，但自動下載被交付端點阻擋。本頁不是全文精讀，取得 PDF 前不補寫實驗數字。

## 目前可以確定的問題

使用者詢問政府規則時，原問題可能缺少條件，系統不能立刻回答 yes/no，而要先追問 who、what、when、where、why 或 how。作者建立 WHITE-ShARC，把 conversational machine reading comprehension 放入 open-retrieval 設定，加入更多問句類型與無法回答案例，並提出 retriever → reranker → reader 流程。

## PDF 到位後的閱讀路線

1. 先確認 WHITE-ShARC 如何從原始規則與對話建立、資料切分是否有文件洩漏。
2. 比較 retriever 與 reranker 的召回錯誤，避免把 reader 答錯全怪在生成模型。
3. 分開檢查 follow-up question generation、最終 decision、span/answer generation 的指標。
4. 逐類分析 Wh-question 與 unanswerable 案例，確認改善是否只來自模板詞。
5. 核對 LLM 實驗使用的模型、prompt、樣本量與可重現性。

## 閱讀前自問

- 好的追問是「語法自然」還是「能最快排除不確定條件」？
- open retrieval 找錯規則時，後面的 reader 再強是否有用？
- 系統何時應追問，何時應承認沒有資料？

