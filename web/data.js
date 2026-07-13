window.RESEARCH_OS_DATA = {
  "generated_at": "2026-07-13T02:04:20.901254+00:00",
  "professor": {
    "id": "an-zi-yen",
    "name": "An-Zi Yen",
    "affiliation": "Department of Computer Science, National Yang Ming Chiao Tung University",
    "url": "https://azyen0522.github.io/"
  },
  "summary": {
    "total": 38,
    "fetched": 15,
    "unresolved": 23
  },
  "artifacts": {
    "dataset-map": {
      "path": "research\\professor\\an-zi-yen\\dataset-map.md",
      "content": "# Dataset map\n\n| Paper | Data or setting | Evidence |\n|---|---|---|\n| E-QGen | 14,422 lecture-transcript paragraphs; gold, silver, and GPT-4-augmented question pairs | E-QGen pp. 2-3 |\n| RefuteClaim | FlawCheck, extending 33,721 WatClaimCheck claims and review metadata | RefuteClaim p. 2 |\n| ISSR | 195 GSAT English-vocabulary questions from 2006-2018 | ISSR p. 16 |\n| ParaAlign Translator | WMT/MTME/WMT22 and FLORES-200 language-pair settings | ParaAlign pp. 2-3 |\n| MathEDU | 4,048 authentic student solutions with expert error annotations and teacher feedback | MathEDU pp. 2-3 |\n| CIVIL lifelog retrieval | About 63,000 NTCIR-14 Lifelog-3 images from 29 days and 10 ImageCLEF topics | CIVIL p. 3 |\n\nWebsite-only records remain deliberately unspecified until their full text is lawfully fetched and processed.\n"
    },
    "method-map": {
      "path": "research\\professor\\an-zi-yen\\method-map.md",
      "content": "# Method map\n\n| Method family | Full-text evidence | Research connection |\n|---|---|---|\n| Multitask LoRA generation | E-QGen | Lecture abstract to likely student questions, plus reference questions. |\n| Diagnosis then feedback | MathEDU | Correctness, error-step identification, then pedagogical feedback. |\n| Retrieve, aspect, flaw, explain | RefuteClaim | Explicit evidence and defect analysis for fact checking. |\n| Generate, select, self-review | ISSR | Constrained LLM quality control for assessment design. |\n| Caption then text retrieval | CIVIL lifelog retrieval | Personal memory recall from first-person images. |\n| Paraphrase then translate | ParaAlign Translator | Source-side structural alignment for machine translation. |\n"
    },
    "open-questions": {
      "path": "research\\professor\\an-zi-yen\\open-questions.md",
      "content": "# Open questions\n\n- Which of the remaining 25 works have a lawful public full text that the configured providers do not expose?\n- Can educational systems turn diagnosis into concise, correct feedback rather than fluent over-explanation?\n- Are LLM-generated flaw labels and LLM-judge scores reliable under independent expert review?\n- How should lifelog caption systems represent uncertainty and protect sensitive visual memory?\n- How can paraphrase-based translation preserve meaning in technical, legal, or medical domains?\n"
    },
    "profile": {
      "path": "research\\professor\\an-zi-yen\\profile.md",
      "content": "# An-Zi Yen\n\n- **Affiliation:** Department of Computer Science, National Yang Ming Chiao Tung University\n- **Lab URL:** https://azyen0522.github.io/\n- **Aliases used for authorship:** An-Zi Yen, A-Z Yen, 顏安孜\n- **Evidence:** `.research-os/snapshots/professor.html` (hash recorded in SQLite).\n"
    },
    "publication-index": {
      "path": "research\\professor\\an-zi-yen\\publication-index.md",
      "content": "# Publication index\n\nOnly entries whose author string matches a configured alias are included.\n\n| Year | Title | Status | IDs | Source evidence |\n|---:|---|---|---|---|\n| 2026 | Confidence-Driven Multi-Scale Model Selection for Cost-Effective NLU | fetched | doi:10.18653/v1/2026.findings-eacl.90 | https://azyen0522.github.io/ |\n| 2026 | MathEDU: Feedback Generation on Problem-Solving Processes for Mathematical Learning Support | fetched | doi:10.18653/v1/2026.eacl-long.132 | https://azyen0522.github.io/ |\n| 2025 | Follow-up Question Modeling for Open-Retrieval Conversations with Wh-Questions | unresolved | — | https://azyen0522.github.io/ |\n| 2025 | Personalized Graph-Empowered Large Language Model for Proactive Information Access | fetched | arXiv:2602.21862 | https://azyen0522.github.io/ |\n| 2025 | RAG-Enhanced Evidence Recommendation in Financial Legal Resolutions | unresolved | doi:10.1145/3701716.3715520 | https://azyen0522.github.io/ |\n| 2025 | Template-Based Financial Report Generation in Agentic and Decomposed Information Retrieval | unresolved | doi:10.1145/3726302.3730253 | https://azyen0522.github.io/ |\n| 2024 | ConvLogRecaller: Real-Time Conversational Lifelog Recaller | unresolved | doi:10.1145/3626772.3657659 | https://azyen0522.github.io/ |\n| 2024 | E-QGen: Educational Lecture Abstract-based Question Generation System | fetched | arXiv:2404.13547 | https://azyen0522.github.io/ |\n| 2024 | How We Refute Claims: Automatic Fact-Checking through Flaw Identification and Explanation | fetched | arXiv:2401.15312 | https://azyen0522.github.io/ |\n| 2024 | ISSR: Iterative Selection with Self-Review for Vocabulary Test Distractor Generation | fetched | arXiv:2501.03462 | https://azyen0522.github.io/ |\n| 2024 | MAGIC: Multi-Argument Generation with Self-Refinement for Domain Generalization in Automatic Fact-Checking | unresolved | doi:10.63317/2yyfqugvx8xo | https://azyen0522.github.io/ |\n| 2024 | Paraphrase-Aligned Machine Translation | fetched | arXiv:2412.05916 | https://azyen0522.github.io/ |\n| 2024 | Visual Lifelog Retrieval through Captioning-Enhanced Interpretation | fetched | doi:10.1109/bigdata62323.2024.10825835 | https://azyen0522.github.io/ |\n| 2023 | Citation Intent Classification and Its Supporting Evidence Extraction for Citation Graph Construction | unresolved | doi:10.1145/3583780.3614808 | https://azyen0522.github.io/ |\n| 2023 | ContributionSum: Generating Disentangled Contributions for Scientific Papers | unresolved | doi:10.1145/3583780.3615115 | https://azyen0522.github.io/ |\n| 2023 | LED: A Dataset for Life Event Extraction from Dialogs | fetched | doi:10.18653/v1/2023.findings-eacl.29 | https://azyen0522.github.io/ |\n| 2023 | Multi-Perspective Sentiment Analysis on Life Events with Sentiment Cause Identification | unresolved | doi:10.1109/wi-iat59888.2023.00010 | https://azyen0522.github.io/ |\n| 2023 | Opportunities and challenges of explainable artificial intelligence in medicine: toward causability for physicians, developers, and patients | unresolved | — | https://azyen0522.github.io/ |\n| 2023 | RSVP: Customer Intent Detection via Agent Response Contrastive and Generative Pre-Training | fetched | doi:10.18653/v1/2023.findings-emnlp.698 | https://azyen0522.github.io/ |\n| 2023 | Three Questions Concerning the Use of Large Language Models to Facilitate Mathematics Learning | fetched | doi:10.18653/v1/2023.findings-emnlp.201 | https://azyen0522.github.io/ |\n| 2023 | Visual Lifelog Retrieval: Humans and Machines Interpretation on First-Person Images | unresolved | doi:10.1007/s11042-023-14344-x | https://azyen0522.github.io/ |\n| 2023 | ZARA: Improving Few-Shot Self-Rationalization for Small Language Models | fetched | doi:10.18653/v1/2023.findings-emnlp.310 | https://azyen0522.github.io/ |\n| 2022 | Incorporating Peer Reviews and Rebuttal Counter-Arguments for Meta-Review Generation | unresolved | doi:10.1145/3511808.3557360 | https://azyen0522.github.io/ |\n| 2022 | Learning to Generate Explanation from e-Hospital Services for Medical Suggestion | unresolved | — | https://azyen0522.github.io/ |\n| 2022 | Modeling Inter Round Attack of Online Debaters for Winner Prediction | unresolved | doi:10.1145/3485447.3512006 | https://azyen0522.github.io/ |\n| 2022 | SEEN: Structured Event Enhancement Network for Explainable Need Detection of Information Recall Assistance | fetched | doi:10.18653/v1/2022.emnlp-main.365 | https://azyen0522.github.io/ |\n| 2022 | Unanswerable Question Correction and Explanation over Personal Knowledge Base | unresolved | doi:10.1145/3511808.3557717 | https://azyen0522.github.io/ |\n| 2021 | ConvLog-Miner: A Real-Time Conversational Lifelog Miner | unresolved | doi:10.24963/ijcai.2021/710 | https://azyen0522.github.io/ |\n| 2021 | Ten Questions in Lifelog Mining and Information Recall | fetched | doi:10.1145/3460426.3463607 | https://azyen0522.github.io/ |\n| 2021 | Unanswerable Question Correction in Question Answering over Personal Knowledge Base | fetched | doi:10.1609/aaai.v35i16.17678 | https://azyen0522.github.io/ |\n| 2020 | Incorporating Semantic Knowledge for Visual Lifelog Activity Recognition | unresolved | doi:10.1145/3372278.3390700 | https://azyen0522.github.io/ |\n| 2019 | Learning English-Chinese Bilingual Word Representations from Sentence-Aligned Parallel Corpus | unresolved | doi:10.1016/j.csl.2019.01.002 | https://azyen0522.github.io/ |\n| 2019 | Multimodal joint learning for personal knowledge base construction from Twitter-based lifelogs | unresolved | doi:10.1016/j.ipm.2019.102148 | https://azyen0522.github.io/ |\n| 2019 | Personal Knowledge Base Construction from Text-based Lifelogs | unresolved | doi:10.1145/3331184.3331209 | https://azyen0522.github.io/ |\n| 2018 | Detecting Personal Life Events fom Twitter by Multi-Task LSTM | unresolved | doi:10.1145/3184558.3186909 | https://azyen0522.github.io/ |\n| 2018 | Transfer of Frames from English FrameNet to Construct Chinese FrameNet: A Bilingual Corpus-Based Approach | unresolved | doi:10.63317/58vv9pbm8ze4 | https://azyen0522.github.io/ |\n| 2017 | Fusing Domain-Specific Data with General Data for In-Domain Applications | unresolved | doi:10.1145/3106426.3106473 | https://azyen0522.github.io/ |\n| 2017 | MKDS: A Medical Knowledge Discovery System Learned from Electronic Medical Records (Demonstration) | unresolved | doi:10.1007/978-3-030-03520-4_19 | https://azyen0522.github.io/ |\n"
    },
    "reading-order": {
      "path": "research\\professor\\an-zi-yen\\reading-order.md",
      "content": "# Reading order\n\n1. [E-QGen](../../papers/e-qgen-educational-lecture-abstract-based-questi-1c78636b/README.md) - a compact starting point for educational question generation and LoRA.\n2. [MathEDU](../../papers/mathedu-feedback-generation-on-problem-solving-p-59fb8b56/README.md) - student-process diagnosis, feedback reliability, and teacher evaluation.\n3. [RefuteClaim](../../papers/how-we-refute-claims-automatic-fact-checking-thr-fd880d30/README.md) - evidence, explanation, and trustworthy fact checking.\n4. [ISSR](../../papers/issr-iterative-selection-with-self-review-for-vo-9414a4f1/README.md) - iterative selection and self-review for assessment design.\n5. [CIVIL lifelog retrieval](../../papers/visual-lifelog-retrieval-through-captioning-enha-ffbd056d/README.md) - multimodal captioning for personal-memory retrieval.\n6. [ParaAlign Translator](../../papers/paraphrase-aligned-machine-translation-4b61bbb7/README.md) - bilingual alignment and efficient LLM adaptation.\n"
    },
    "research-directions": {
      "path": "research\\professor\\an-zi-yen\\research-directions.md",
      "content": "# Research directions\n\n1. Question generation and answering: knowledge-base QA, multimodal QA, and retrieval-augmented generation.\n2. Human-centered AI: proactive assistants, human-AI collaboration, user modeling, and teacher-facing support.\n3. NLP for social good: trustworthy AI, legal language processing, and social-media analysis.\n4. The supplied deck motivates educational feedback, fact checking, tool use, and cost-aware model selection.\n\nThe supplied deck is preserved at `research/seeds/NYCU NLP Lab Intro.pdf`. The retrieved papers make the education, trustworthy-AI, multimodal lifelog, and bilingual-alignment themes concrete.\n"
    },
    "research-timeline": {
      "path": "research\\professor\\an-zi-yen\\research-timeline.md",
      "content": "# Research timeline\n\n- 2017-2021: lifelog mining, personal knowledge bases, and information recall.\n- 2022-2023: explanation, citation evidence, and education-oriented LLM work.\n- 2024: fact checking, E-QGen, and multimodal lifelog retrieval.\n- 2025: distractor generation, translation alignment, and proactive information access.\n- 2026: MathEDU feedback generation and cost-aware NLU.\n"
    }
  },
  "seeds": [
    {
      "label": "NYCU NLP Lab Intro",
      "path": "research\\seeds\\NYCU NLP Lab Intro.pdf"
    }
  ],
  "papers": [
    {
      "id": "confidence-driven-multi-scale-model-selection-fo-1890ff47",
      "title": "Confidence-Driven Multi-Scale Model Selection for Cost-Effective NLU",
      "authors": "Bo-Wei Chen, Chung-Chi Chen, An-Zi Yen",
      "year": 2026,
      "venue": "” In Findings of the 19th Conference of the European Chapter of the Association for Computational Linguistics, March 24-29, 2026, Rabat, Morocco. (acceptance rate: 16.1%)",
      "status": "fetched",
      "doi": "10.18653/v1/2026.findings-eacl.90",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2026.findings-eacl.90.pdf",
          "label": "ACL Anthology official PDF",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\README.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\reading-guide-zh.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\method.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\experiments-and-results.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\limitations-and-critique.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\prerequisites.md",
        "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\README.md",
          "content": "# Confidence-Driven Multi-Scale Model Selection for Cost-Effective NLU\n\n- **Status:** full text fetched and extracted (11 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `6a404eea31204e3a3823be677c1d94a494da8b603edacfe68f23527a4f1df2f3`.\n- **Evidence anchors:** Abstract p. 1; method p. 2; results p. 2.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "reading-guide-zh": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\reading-guide-zh.md",
          "content": "# 寶寶式完整導讀：Confidence-Driven Multi-Scale Model Selection\n\n> 導讀狀態：已核對 ACL Anthology 11 頁全文。數字均為作者報告結果，未在本專案重跑實驗。\n\n## 先用一個故事懂整篇\n\n你有三位解題員：小模型便宜又快，大模型較貴但通常較可靠。每次問題都直接交給大模型很浪費；每次都交給小模型又容易答錯。作者做了一位「分流老師」：先問小模型，只有在它可能不知道或答案不可信時，才把問題往大模型送。\n\n整篇論文只是在回答一件事：**能否知道小模型什麼時候值得相信？** 作者使用兩個訊號：\n\n- `P(T)`：這個答案為真的信心，可把它想成「這次答案看起來有多穩」。\n- `P(IK)`：模型是否知道答案的機率，可把它想成「它是不是其實在熟悉的題目上」。\n\n兩者不是同一件事。模型可以很有自信地猜錯，所以只看 `P(T)` 不夠；`P(IK)` 是額外學出的自我知識分類器。\n\n## 閱讀路線\n\n### 第一站：第 1–2 頁，只抓問題與流程\n\n先看摘要與 Figure 1。不要急著看所有公式。把流程念成：小模型回答 → 檢查 `P(IK)` 與 `P(T)` → 信心足夠就留下 → 不足就升級到較大模型。你若能解釋「router 不是生成答案，而是決定由誰回答」，就可以前進。\n\n### 第二站：第 2–3 頁，分清兩種信心\n\n`P(T)` 依答案機率／提示取得；`P(IK)` 則由模型在已知正誤樣本上的表現訓練分類器。關鍵不是背公式，而是理解：前者看當下輸出，後者估計能力邊界。路由門檻越寬鬆，越多題留在小模型，成本下降，但錯誤風險增加。\n\n### 第三站：第 3–5 頁，看主實驗\n\n作者在 MMLU 上比較 LLaMA 3B、8B、70B 的串接，也測試通往 GPT-4o 的路徑。閱讀表格時先找三欄：準確率、performance drop、reduced compute cost。不要把「節省計算」讀成「速度一定同比提升」；這裡主要用模型規模／token 成本做代理指標。\n\n### 第四站：第 5–6 與 9–11 頁，看失敗與補充\n\nOOD 的 GPQA 顯示分布改變會讓 `P(IK)` 不穩。PopQA 又把任務從多選延伸到開放式問答，這時原本容易計算的 `P(T)` 不再天然成立，需要 grounding 與額外判斷。這兩段是論文最值得批判閱讀的地方。\n\n## 表格怎麼讀\n\n- Table 14：3B 的 `P(IK)` 分類器 F1 為 62.76%，8B 為 69.21%。它有用，但絕非完美裁判。\n- Table 15：8B→70B 且同時使用 `P(T)+P(IK)` 時，`P(T)` 門檻降到 50%，準確率仍為 0.8266、performance drop 1.09%、計算成本降低 39.33%。拿掉 `P(IK)` 後同門檻準確率降至 0.7455。\n- PopQA：70B 單模準確率 0.6585；8B→70B 為 0.6459，成本節省約 7%，performance drop 1.91%。這是「接近大模型但較省」，不是全面超越大模型。\n- 成本估計使用 2025 年 4 月公開 token 價格，未包含完整自架硬體、排隊與延遲成本，因此不能直接當今天的部署報價。\n\n## 真正貢獻與限制\n\n貢獻是把「答案信心」與「是否知道」合併，讓多尺度模型路由較不容易因單一信心門檻崩掉。限制包括 `P(IK)` 需要資料訓練、OOD 泛化有限、多選題的信心較容易定義，以及 compute-cost proxy 沒有完整覆蓋真實部署成本。\n\n## 讀完自測\n\n1. 為什麼高 `P(T)` 不代表模型真的知道？\n2. 門檻降低時，成本與錯誤風險各怎麼變？\n3. Table 15 為何能支持 `P(IK)` 的價值？\n4. 如果答案是自由生成文字，你會如何重新定義 `P(T)`？\n\n參考答案：1. 模型可能校準不良而自信地猜錯。2. 更多題停在小模型，成本通常降低但錯誤風險上升。3. 同門檻拿掉 `P(IK)` 時準確率下降幅度明顯增大。4. 可用語義一致性、外部證據 grounding、verifier 或多次採樣一致性，但必須另行驗證。\n\n"
        },
        "method": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\method.md",
          "content": "# Method\n\nPopulate from the extracted full text. Cite page anchors for every paper claim.\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\experiments-and-results.md",
          "content": "# Experiments and results\n\nPopulate reported setup, metrics, and results from the full text; do not label them reproduced.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\nSeparate author-stated limitations from builder interpretation.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\prerequisites.md",
          "content": "# Prerequisites\n\nList only concepts needed to read this paper.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which result is most sensitive to the evaluation design?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Input[Input] --> Method[Method from full text]\n  Method --> Output[Output]\n"
        },
        {
          "path": "research\\papers\\confidence-driven-multi-scale-model-selection-fo-1890ff47\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> Paper[This paper]\n  Paper --> Theme[Research direction]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "method first assesses P(IK) for smaller models",
          "page": 2
        },
        {
          "heading": "results suggest that the confidence estimates of the",
          "page": 2
        },
        {
          "heading": "Results with Multi-Scale Open-Source",
          "page": 3
        },
        {
          "heading": "results are presented in Table 2.5",
          "page": 3
        },
        {
          "heading": "Results with Commercial API",
          "page": 4
        },
        {
          "heading": "results. First, the results indicate the usefulness",
          "page": 5
        },
        {
          "heading": "method to OOD applications. This may be due to",
          "page": 5
        },
        {
          "heading": "Limitations",
          "page": 6
        },
        {
          "heading": "References",
          "page": 6
        },
        {
          "heading": "approach across diverse settings.",
          "page": 6
        },
        {
          "heading": "Related Work",
          "page": 7
        },
        {
          "heading": "results are summarized in Table 9.",
          "page": 9
        },
        {
          "heading": "method achieves comparable performance while",
          "page": 9
        },
        {
          "heading": "results support our claim that the proposed method",
          "page": 9
        },
        {
          "heading": "results with and without grounding. Our results are",
          "page": 9
        },
        {
          "heading": "Results with Open-ended QA",
          "page": 9
        }
      ]
    },
    {
      "id": "mathedu-feedback-generation-on-problem-solving-p-59fb8b56",
      "title": "MathEDU: Feedback Generation on Problem-Solving Processes for Mathematical Learning Support",
      "authors": "Wei-Ling Hsu, Yu-Chien Tang, An-Zi Yen",
      "year": 2026,
      "venue": "” In Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics, March 24-29, 2026, Rabat, Morocco. (acceptance rate: 20.1%)",
      "status": "fetched",
      "doi": "10.18653/v1/2026.eacl-long.132",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2026.eacl-long.132.pdf",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\README.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\reading-guide-zh.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\method.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\experiments-and-results.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\limitations-and-critique.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\prerequisites.md",
        "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\README.md",
          "content": "# MathEDU: Feedback Generation on Problem-Solving Processes for Mathematical Learning Support\n\n- **Status:** full text fetched and extracted (19 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `f9a3998f039a7145c8db23c87f0f737b6eef7705f7c7fa1a0dbe076ef70dc430`.\n- **Evidence anchors:** Abstract p. 1; method pp. 3-5; results pp. 5-8.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "reading-guide-zh": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\reading-guide-zh.md",
          "content": "# 寶寶式完整導讀：MathEDU\n\n> 導讀狀態：已核對 19 頁全文。所有結果是論文報告值，不代表本專案已重現。\n\n## 一句話故事\n\n老師看到學生答案時要做三件不同的事：判斷對錯、找到第一個出錯步驟、說出真正能幫學生改進的提示。MathEDU 的核心提醒是：**會判對錯，不等於會教。**\n\n## 先認識資料\n\n作者蒐集 4,048 份真實學生的 GRE 程度數學解題過程，其中 3,050 份正確、998 份錯誤，並由數學教育專家標記錯誤與撰寫回饋。這很重要，因為模型模擬的「假學生錯誤」未必像真人。資料依時間切成 2,836/609/603，讓模型用學生較早的答題紀錄推斷後來的表現。\n\n## 閱讀路線\n\n### 第一站：第 1–3 頁，搞懂三層任務\n\n把三層畫成樓梯：`correctness classification → error-step identification → feedback generation`。上一層成功不保證下一層成功。只答「錯」對學習幫助有限；找錯位置仍可能給出冗長或錯誤建議。\n\n### 第二站：第 3–5 頁，看資料與訓練設定\n\n作者比較 few-shot prompting、LoRA fine-tuning，以及 single-task、multi-task、end-to-end 設定；也比較輸入是否包含題目 rationale。閱讀 Equation 1 時只需知道 LoRA 不重訓全部權重，而是學一個較小的參數增量。真正要注意的是資料單位：同一學生的歷史不能隨意洩漏到測試未來。\n\n### 第三站：第 5–7 頁，逐張表問「指標測到什麼」\n\n- 對錯分類用 F-score，因正確與錯誤樣本不平衡。\n- 錯誤步驟用 exact match 與 Hausdorff distance；exact match 很嚴格，distance 補充「猜的位置離真正錯誤有多遠」。\n- 回饋生成同時用 ROUGE-L、LLM rating 與人工評估。文字相似不等於教學有效，所以人工判讀不可省略。\n\n### 第四站：第 7–9 頁，看學生差異與限制\n\n模型表現沒有隨學生程度呈現清楚單調關係。解題寫得長、方程多，可能更難定位錯誤；寫得太短，又讓回饋缺少脈絡。因此「個人化」不能只用高／中／低程度標籤代替。\n\n## 關鍵結果\n\n- single-task LoRA 加 rationale 的對錯分類 F-score 為 95.07%；o1-mini 在不含 rationale 時為 94.66%。\n- 錯誤定位仍困難：single-task 加 rationale 的 exact match 為 23.46%，顯示「最後判對錯很強」不能推論「能準確找錯步」。\n- o1-mini 的 GPT-4 回饋評分最高（4.70），但作者仍觀察到冗長、無關、措辭不精確與計算錯誤。\n\n## 不要讀錯\n\n這篇沒有證明 AI tutor 已可取代老師。學生本人沒有評估模型回饋是否真的幫助學習；資料只有 4,048 筆、限於 GRE 數學，模型與方法範圍也有限。高 ROUGE 或由另一個 LLM 給高分，不能直接等同學習成效。\n\n## 讀完自測\n\n1. 為什麼資料必須包含真實學生過程？\n2. 為什麼 F-score 95% 仍不能說模型會教數學？\n3. exact match 低而 correctness 高代表什麼？\n4. 下一個實驗最該加入誰的評估？\n\n參考答案：1. 真人錯誤分布與模型模擬錯誤不同。2. 它只衡量對錯分類。3. 模型常知道答案錯了，卻找不到具體推理斷點。4. 原本作答的學生，並測量看完回饋後是否能改正或遷移學習。\n\n"
        },
        "method": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\method.md",
          "content": "# Method\n\n## Paper claim\n\nMathEDU evaluates mathematical-learning support at three levels: answer-correctness classification, erroneous-step identification, and feedback generation (pp. 4–5). It collects authentic student solutions and teacher feedback, then compares prompting with LoRA fine-tuning under single-task, multi-task, and end-to-end formulations (pp. 3–5).\n\n## Builder interpretation\n\nThe staged task design makes an important distinction: detecting that an answer is wrong is not the same as locating the reasoning fault, and neither guarantees pedagogy-aware feedback.\n\n## Unresolved question\n\nCan a model produce concise corrective feedback without over-diagnosing a student’s valid intermediate reasoning?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe dataset has 4,048 authentic student answers, with 3,050 correct and 998 incorrect; three math-education experts annotate errors and feedback, reporting Krippendorff’s alpha 0.7818 (p. 3). The chronological split is 2,836/609/603 (p. 5).\n\nFor correctness classification, the single-task LoRA model with rationales reports F-score 95.07%; o1-mini reports 94.66% without rationale. For error identification, the single-task model with rationales reports exact match 23.46% and distance 96.43 (Table 3, p. 6).\n\nFeedback remains difficult: o1-mini reports the highest GPT-4 rating (4.70), but the paper notes verbosity and irrelevant detail; human ratings remain below the ideal 3 across models (pp. 7–8).\n\n## Evidence caveat\n\nThese scores are reported model/human evaluations, not a replication. High final-answer classification does not establish reliable feedback for every student process.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe paper finds that generated feedback is frequently verbose, misses calculation errors, misidentifies error locations, or misunderstands a student approach (pp. 7–8). The dataset is built from six students and MathQA-derived word problems (pp. 2–3).\n\n## Builder interpretation\n\nThe evidence argues for a cautious tutor role: a system should show its diagnosis and preserve teacher review rather than present fluent feedback as automatically trustworthy.\n\n## Unresolved question\n\nHow well do the labels and feedback transfer across age groups, mathematical notation habits, and classroom settings?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\prerequisites.md",
          "content": "# Prerequisites\n\n- Step-level mathematical reasoning versus final-answer grading.\n- LoRA single-task, multi-task, and end-to-end training.\n- F-score, exact-match, span distance, and the limits of automatic feedback metrics.\n- Cognitive load and why long explanations can be harmful.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which error types most expose the gap between answer grading and feedback generation?\n2. How should a tutor express uncertainty about a student’s process?\n3. Is chronological per-student splitting enough to test cross-student generalization?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Q[Problem + rationale + student process] --> C[Correctness classification]\n  Q --> E[Error-step identification]\n  C --> F[Feedback generation]\n  E --> F\n  F --> T[Teacher-like corrective feedback]\n"
        },
        {
          "path": "research\\papers\\mathedu-feedback-generation-on-problem-solving-p-59fb8b56\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Deck[NYCU deck: adaptive feedback] --> M[MathEDU]\n  M --> Dataset[Student processes + teacher feedback]\n  M --> Trust[Trustworthy educational AI]\n  M --> Eval[Diagnosis and feedback evaluation]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "Related Work",
          "page": 2
        },
        {
          "heading": "Conclusion",
          "page": 9
        },
        {
          "heading": "Limitations",
          "page": 10
        },
        {
          "heading": "References",
          "page": 10
        },
        {
          "heading": "Conclusion:",
          "page": 19
        }
      ]
    },
    {
      "id": "follow-up-question-modeling-for-open-retrieval-c-e201b983",
      "title": "Follow-up Question Modeling for Open-Retrieval Conversations with Wh-Questions",
      "authors": "Che-Wei Huang, An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2025,
      "venue": "” In Proceedings of the 24th IEEE/WIC International Conference on Web Intelligence and Intelligent Agent Technology (WI-IAT 2025), 15-18 November 2025, London, United Kingdom",
      "status": "unresolved",
      "doi": null,
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [
        {
          "url": "https://papers.ssrn.com/sol3/Delivery.cfm/5352073c-4161-4996-bcce-f3b6a449b453-MECA.pdf?abstractid=4710309&mirid=1",
          "label": "SSRN author manuscript",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\follow-up-question-modeling-for-open-retrieval-c-e201b983\\reading-guide-zh.md"
      ],
      "documents": {
        "reading-guide-zh": {
          "path": "research\\papers\\follow-up-question-modeling-for-open-retrieval-c-e201b983\\reading-guide-zh.md",
          "content": "# 預備導讀：Follow-up Question Modeling\n\n> 狀態：已核對 WI-IAT 2025 議程與 SSRN DOI `10.2139/ssrn.4710309`；SSRN 顯示 35 頁作者稿，但自動下載被交付端點阻擋。本頁不是全文精讀，取得 PDF 前不補寫實驗數字。\n\n## 目前可以確定的問題\n\n使用者詢問政府規則時，原問題可能缺少條件，系統不能立刻回答 yes/no，而要先追問 who、what、when、where、why 或 how。作者建立 WHITE-ShARC，把 conversational machine reading comprehension 放入 open-retrieval 設定，加入更多問句類型與無法回答案例，並提出 retriever → reranker → reader 流程。\n\n## PDF 到位後的閱讀路線\n\n1. 先確認 WHITE-ShARC 如何從原始規則與對話建立、資料切分是否有文件洩漏。\n2. 比較 retriever 與 reranker 的召回錯誤，避免把 reader 答錯全怪在生成模型。\n3. 分開檢查 follow-up question generation、最終 decision、span/answer generation 的指標。\n4. 逐類分析 Wh-question 與 unanswerable 案例，確認改善是否只來自模板詞。\n5. 核對 LLM 實驗使用的模型、prompt、樣本量與可重現性。\n\n## 閱讀前自問\n\n- 好的追問是「語法自然」還是「能最快排除不確定條件」？\n- open retrieval 找錯規則時，後面的 reader 再強是否有用？\n- 系統何時應追問，何時應承認沒有資料？\n\n"
        }
      },
      "diagrams": [],
      "sections": []
    },
    {
      "id": "personalized-graph-empowered-large-language-mode-79f70556",
      "title": "Personalized Graph-Empowered Large Language Model for Proactive Information Access",
      "authors": "Chia Cheng Chang, An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2025,
      "venue": "” In Proceedings of the 24th IEEE/WIC International Conference on Web Intelligence and Intelligent Agent Technology (WI-IAT 2025), 15-18 November 2025, London, United Kingdom",
      "status": "fetched",
      "doi": null,
      "arxiv_id": "2602.21862",
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/pdf/2602.21862",
          "label": "arXiv author manuscript",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\README.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\reading-guide-zh.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\method.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\experiments-and-results.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\limitations-and-critique.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\prerequisites.md",
        "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\README.md",
          "content": "# Personalized Graph-Empowered Large Language Model for Proactive Information Access\n\n- **Status:** full text fetched and extracted (9 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv 2602.21862; SHA-256 `75abf5463bd96aa572798c501d0967a3134eb4ace30e0b981c00a49da62b0fd7`.\n- **Evidence anchors:** Abstract p. 1; method p. 4; results p. 5.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "reading-guide-zh": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\reading-guide-zh.md",
          "content": "# 寶寶式完整導讀：Personalized Graph-Empowered LLM\n\n> 導讀狀態：已核對 arXiv 9 頁全文（2602.21862v1）。\n\n## 一句話故事\n\n一個人重講往事時，可能講對、講錯、補充新細節，或漏掉舊事件。LLM 很會理解文字，但可能憑感覺亂補；個人知識圖譜較死板，卻能保存具體事件。GER 框架讓兩者互相檢查，再決定是否提醒或修正使用者。\n\n## 五種事件先分清\n\n- Consistent：新敘述與舊記錄一致。\n- Inconsistent：新敘述與舊事實衝突，需要糾正。\n- Additional：新增且不衝突的細節，應更新知識圖譜。\n- Forgotten：舊故事有、新敘述漏掉，應提醒。\n- Unforgotten：舊事件在新敘述中仍有提及。\n\n前三類以舊故事 A 為參照檢查新故事 B；Forgotten/Unforgotten 則反向確認 A 的事件是否出現在 B。方向不同是最容易看錯的地方。\n\n## 閱讀路線\n\n### 第一站：第 1–3 頁，看任務與標籤轉換\n\n作者先把五分類暫時壓成 Relevant/Irrelevant：Consistent、Inconsistent、Unforgotten 映成 Relevant；Additional、Forgotten 映成 Irrelevant。這不是說後兩者不重要，而是說它們在參考故事中找不到對應資訊。最後再由 label mapper 還原五種服務。\n\n### 第二站：第 3–4 頁，讀 Figure 1 的三個模組\n\n1. Base module 直接看參考故事與 query，先判 Relevant/Irrelevant。\n2. Support module 同時用 KG 相似度與 LLM 找 supporting events，只取兩邊交集以降低雜訊。\n3. Correction module 比較兩個判斷：一致就保留；base 說有關、support 說無關時用 rethinking prompt；反過來則把找到的 support event 交給 exploration prompt。\n\n像寶寶版陪審團：第一人先投票、第二人拿證據、第三人處理兩票不一致。\n\n### 第三站：第 4–6 頁，看實驗而不是只看總結\n\n資料使用 NIR 的兩次人生故事重述。主要比較 GPT-3.5、Llama3-70B、SEEN Base/Large 與 GER。GER 在 Additional 與 Forgotten 的 recall 分別為 0.8338、0.8635；Forgotten 相對基線改善達 McNemar `p < 0.05`。但 Inconsistent 的 recall 只有 0.0417，不能說五類全面提升。\n\n### 第四站：第 6–7 頁，看消融與錯誤分析\n\nbase module 能力主導上限；把 support 換成 ground truth 時各類明顯提升，表示瓶頸常在「證據找得準不準」。直接拿 LLM 做五分類表現較差。對 Additional/Forgotten，LLM 常把全新資訊誤認為與舊故事相關；對改寫幅度大的相同事件，又可能找不到關聯。\n\n## 真正貢獻與風險\n\nGER 的價值是模組可替換、無須為每次新增 lifelog 重新訓練整套模型，並把結構化個人記憶帶入修正流程。它仍是離線資料集上的 pilot：尚非可在日常生活直接運作的端到端系統，而且個人知識圖譜包含高度敏感資訊，論文明確把隱私與資料安全留為未來工作。\n\n## 讀完自測\n\n1. 為何 Additional 和 Forgotten 被暫時映成 Irrelevant？\n2. support module 為何取 KG 與 LLM 結果的交集？\n3. GER 哪些類別最成功、哪類仍明顯失敗？\n4. 若真的部署，除了 F-score 還必須評估什麼？\n\n參考答案：1. 依任務方向，它們在參考故事中沒有相符事件。2. 減少任一分類器單獨帶來的無關事件。3. Additional/Forgotten 較有改善，Inconsistent 仍弱。4. 隱私、錯誤提醒造成的傷害、延遲、更新正確性與使用者是否信任／能修正系統。\n\n"
        },
        "method": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\method.md",
          "content": "# Method\n\nPopulate from the extracted full text. Cite page anchors for every paper claim.\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\experiments-and-results.md",
          "content": "# Experiments and results\n\nPopulate reported setup, metrics, and results from the full text; do not label them reproduced.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\nSeparate author-stated limitations from builder interpretation.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\prerequisites.md",
          "content": "# Prerequisites\n\nList only concepts needed to read this paper.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which result is most sensitive to the evaluation design?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Input[Input] --> Method[Method from full text]\n  Method --> Output[Output]\n"
        },
        {
          "path": "research\\papers\\personalized-graph-empowered-large-language-mode-79f70556\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> Paper[This paper]\n  Paper --> Theme[Research direction]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract—Since individuals may struggle to recall all life",
          "page": 1
        },
        {
          "heading": "approach into graph-based and LLM-based methods. In the",
          "page": 4
        },
        {
          "heading": "results. To address this, we transform the task from multi-",
          "page": 5
        },
        {
          "heading": "RESULTS WITH SEEN (BASE) AS THE BASE MODULE.",
          "page": 6
        },
        {
          "heading": "RESULTS OF EACH EVENT TYPE WITH DIFFERENT SUPPORT MODULES.",
          "page": 6
        },
        {
          "heading": "REFERENCES",
          "page": 8
        }
      ]
    },
    {
      "id": "rag-enhanced-evidence-recommendation-in-financia-e2e09f27",
      "title": "RAG-Enhanced Evidence Recommendation in Financial Legal Resolutions",
      "authors": "Hsiu-Hung Lee, Chung-Chi Chen, and An-Zi Yen.",
      "year": 2025,
      "venue": "” In Companion Proceedings of the ACM on Web Conference 2025 (WWW '25). Association for Computing Machinery, New York, NY, USA, 1096–1099",
      "status": "unresolved",
      "doi": "10.1145/3701716.3715520",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [
        {
          "url": "https://dl.acm.org/doi/pdf/10.1145/3701716.3715520",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\rag-enhanced-evidence-recommendation-in-financia-e2e09f27\\reading-guide-zh.md"
      ],
      "documents": {
        "reading-guide-zh": {
          "path": "research\\papers\\rag-enhanced-evidence-recommendation-in-financia-e2e09f27\\reading-guide-zh.md",
          "content": "# 預備導讀：RAG-Enhanced Evidence Recommendation in Financial Legal Resolutions\n\n> 狀態：已核對 DOI `10.1145/3701716.3715520`、ACM WWW Companion 2025 書目與 NYCU 官方摘要；完整四頁 PDF 尚未取得。本頁只整理來源可支持的事實。\n\n## 目前可以確定的問題\n\n研究不是直接預測法院勝敗，而是協助金融消費爭議的判斷者找出重要證據。作者整理台灣 25 年間 371 件有標註案例，內容包括主張、評議理由與結果；系統使用 RAG 從相似歷史案例檢索，再生成有依據、顧及時間與情境一致性的證據建議。\n\n## PDF 到位後的完整閱讀路線\n\n1. 核對 371 案來源、納入排除標準、時間切分與標註者資格。\n2. 找出「key evidence」的操作定義與標註一致性，避免把法律結論誤當證據。\n3. 拆開 retrieval 與 generation 評估：檢索到正確類案，不代表生成的證據建議正確。\n4. 檢查 temporal consistency 如何實作，是否避免用未來判決回答過去案件。\n5. 核對 baselines、metrics、人工法律專家評估與錯誤案例。\n6. 評估敏感個資、偏誤、幻覺、引用可追溯性，以及系統僅能輔助而不能代替法律判斷的邊界。\n\n## 閱讀前自問\n\n- 系統推薦的是「證據種類」、具體文件，還是生成的文字？\n- 類似案件的相似，究竟是語意相似、法條相似或爭點相似？\n- 若 RAG 引用過時或不同法域案例，介面要如何警告使用者？\n\n"
        }
      },
      "diagrams": [],
      "sections": []
    },
    {
      "id": "template-based-financial-report-generation-in-ag-4941e080",
      "title": "Template-Based Financial Report Generation in Agentic and Decomposed Information Retrieval",
      "authors": "Yong-En Tian, Yu-Chien Tang, Kuang-Da Wang, An-Zi Yen, and Wen-Chih Peng",
      "year": 2025,
      "venue": "” In Proceedings of the 48th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR '25). Association for Computing Machinery, New York, NY, USA, 2706–2710",
      "status": "unresolved",
      "doi": "10.1145/3726302.3730253",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "convlogrecaller-real-time-conversational-lifelog-c6afbdbd",
      "title": "ConvLogRecaller: Real-Time Conversational Lifelog Recaller",
      "authors": "Yuan-Chi Lee, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2024,
      "venue": "” In Proceedings of 47nd International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2024), July 14-18, 2024, Washington D.C., USA. (Demo Paper, acceptance rate: 23/47=49%)",
      "status": "unresolved",
      "doi": "10.1145/3626772.3657659",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "e-qgen-educational-lecture-abstract-based-questi-1c78636b",
      "title": "E-QGen: Educational Lecture Abstract-based Question Generation System",
      "authors": "Mao-Siang Chen and An-Zi Yen.",
      "year": 2024,
      "venue": "In Proceedings of the 33rd International Joint Conference on Artificial Intelligence (IJCAI 2024), Demonstration Track, Jeju, South Korea. (Demo Paper, acceptance rate: 60/116=51.7%)",
      "status": "fetched",
      "doi": null,
      "arxiv_id": "2404.13547",
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/abs/2404.13547",
          "label": "Lab project card links to arXiv.",
          "kind": "arxiv"
        },
        {
          "url": "https://arxiv.org/pdf/2404.13547",
          "label": "arxiv",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\README.md",
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\method.md",
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\experiments-and-results.md",
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\limitations-and-critique.md",
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\prerequisites.md",
        "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\README.md",
          "content": "# E-QGen: Educational Lecture Abstract-based Question Generation System\n\n- **Status:** full text fetched and extracted (4 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv 2404.13547; SHA-256 `ca8cd7ce766bfc1a3f380ef24730690de9a2fb2eba21b10e1f86e8ae55965f28`.\n- **Evidence anchors:** Abstract p. 1; method pp. 1-3; results p. 3.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\method.md",
          "content": "# Method\n\n## Paper claim\n\nE-QGen takes a lecture abstract and produces potential student questions so that an instructor can prepare answers or resources ahead of time (p. 1). It has two generators:\n\n1. A student-question generator, LoRA-tuned in a multitask setup.\n2. A reference-question generator for broader conceptual questions (p. 3).\n\nThe student generator uses actual timestamp-aligned questions (gold), probabilistically aligned questions (silver), and GPT-4-generated questions (platinum). The paper reports 356 gold pairs, 4,434 silver pairs, and 4,829 platinum pairs after transcript segmentation and alignment (p. 2).\n\n## Builder interpretation\n\nThe system separates two useful pedagogical functions: mimic likely student confusion and cover general concepts. That separation is more actionable for an instructor than a single generic question list.\n\n## Unresolved question\n\nDoes similarity to historical YouTube-comment questions predict usefulness for students in a live, different course?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe test split contains 300/10/46 gold pairs for training, validation, and test; silver and platinum pairs are training-only. The paper uses Vicuna-7B-v1.5 for student questions and GPT-3.5 for reference questions (p. 3).\n\nOn its multiple-candidate/multiple-reference protocol, E-QGen reports ROUGE-1/ROUGE-2/ROUGE-L/BERTScore of 0.2667/0.0866/0.2160/0.8642, above its GPT-4 comparison on the three ROUGE metrics (0.2505/0.0658/0.1967/0.8615) (Table 1, p. 3).\n\nRemoving silver or platinum fine-tuning data reduces all reported metrics; removing platinum data has the larger reported drop in ROUGE-L (0.1779 versus 0.1905 without silver data) (Table 2, p. 3).\n\n## Evidence caveat\n\nThe metrics assess textual similarity and BERTScore against held-out student questions. They do not directly establish that teachers save preparation time or that students learn more.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe work currently focuses on computer-science courses; the authors propose extending it across fields (p. 3).\n\n## Builder interpretation\n\nThe silver alignment labels and platinum GPT-4 augmentation expand a small gold set, but create a quality boundary: some training labels are inferred rather than directly observed. The report also uses best-candidate scoring across 20 generated questions, so it should not be read as the expected quality of a randomly selected output.\n\n## Unresolved question\n\nHow would a teacher-facing evaluation measure novelty, appropriateness, and preparation value without rewarding questions that merely echo the lecture abstract?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\prerequisites.md",
          "content": "# Prerequisites\n\n- Sequence-to-sequence generation and prompt-conditioned tasks.\n- LoRA fine-tuning.\n- TextTiling-style transcript segmentation.\n- Embedding cosine similarity and data-label confidence.\n- ROUGE and BERTScore; these are similarity metrics, not direct teaching outcomes.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. What evidence would show that a question is useful before a lecture, rather than merely similar to a past comment?\n2. Does selecting the best of 20 generated questions make the baseline comparison fair?\n3. Which components could transfer to non-CS courses, and which depend on the source comments?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Input[Input] --> Method[Method from full text]\n  Method --> Output[Output]\n"
        },
        {
          "path": "research\\papers\\e-qgen-educational-lecture-abstract-based-questi-1c78636b\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> Paper[This paper]\n  Paper --> Theme[Research direction]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "Experiment and Discussion",
          "page": 3
        },
        {
          "heading": "Conclusion and Future Work",
          "page": 3
        },
        {
          "heading": "References",
          "page": 4
        }
      ]
    },
    {
      "id": "how-we-refute-claims-automatic-fact-checking-thr-fd880d30",
      "title": "How We Refute Claims: Automatic Fact-Checking through Flaw Identification and Explanation",
      "authors": "Wei-Yu Kao and An-Zi Yen",
      "year": 2024,
      "venue": "” In Proceedings of the Web Conference 2024 (WWW 2024), Singapore, May 13-17, 2024. (Short Paper)",
      "status": "fetched",
      "doi": null,
      "arxiv_id": "2401.15312",
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/abs/2401.15312",
          "label": "Lab project card links to arXiv.",
          "kind": "arxiv"
        },
        {
          "url": "https://arxiv.org/pdf/2401.15312",
          "label": "arxiv",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\README.md",
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\method.md",
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\experiments-and-results.md",
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\limitations-and-critique.md",
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\prerequisites.md",
        "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\README.md",
          "content": "# How We Refute Claims: Automatic Fact-Checking through Flaw Identification and Explanation\n\n- **Status:** full text fetched and extracted (4 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv 2401.15312; SHA-256 `3722b21259651a1fdb1002bbbf346fd0e7d94509f2206c54e68686a060b95931`.\n- **Evidence anchors:** Abstract p. 1; method pp. 1-3; results pp. 3-4.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\method.md",
          "content": "# Method\n\n## Paper claim\n\nRefuteClaim frames automatic fact-checking as flaw-oriented: retrieve evidence, generate up to four evaluation aspects, identify flaws, then generate a justification (pp. 2–3). The paper groups seven flaws into explicit compatibility flaws, nuanced support/robustness flaws, and more context-heavy assumption/alternative-explanation flaws (p. 1).\n\nThe authors construct FlawCheck by extending WatClaimCheck review material and use GPT-3.5-turbo to distill expert review content into aspects and flaw labels (p. 2).\n\n## Builder interpretation\n\nAspects function as an explicit reasoning agenda between retrieval and explanation. This can make a fact-checking output easier to inspect, but its faithfulness depends on the quality of the silver labels and retrieved evidence.\n\n## Unresolved question\n\nCan the framework distinguish a truly unsupported claim from one where relevant evidence was simply not retrieved?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe experiments use Vicuna-7B-v1.5 with LoRA rank 8. Justifications are scored with ROUGE and BERTScore; Gemini Pro is used for correctness and completeness scoring because the paper states there is no existing metric for those qualities (p. 3).\n\nFor false claims, RefuteClaim-7F reports ROUGE-1 0.3266 and ROUGE-L 0.1739, versus 0.3151 and 0.1644 for the baseline. On Gemini-Pro correctness/completeness, it reports 0.5088/0.5381 versus 0.4770/0.5165 (Tables 1–2, p. 4).\n\nThe paper reports weaker justification performance for unproven claims and difficulty separating partly-false, false, and unproven classes (pp. 3–4).\n\n## Evidence caveat\n\nThese are reported automatic and model-judge scores; they are not a human replication or a proof that generated explanations are faithful to model internals.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe paper notes weaker handling of unproven claims and ambiguity between partly-false, false, and unproven labels (pp. 3–4). It leaves a classifier that connects reliably to different justification generators as future work (p. 3).\n\n## Builder interpretation\n\nFlawCheck extracts and transforms expert reviews using an LLM. That enables scale but means the supervision is not identical to direct professional annotation. Gemini Pro as a judge is useful diagnostic evidence, not an independent ground truth.\n\n## Unresolved question\n\nWould expert raters agree that generated aspects identify the decisive flaw rather than plausible but non-causal context?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\prerequisites.md",
          "content": "# Prerequisites\n\n- Dense passage retrieval and evidence ranking.\n- Claim veracity labels and fact-checking review articles.\n- Sequence-to-sequence LoRA fine-tuning.\n- ROUGE/BERTScore and the risks of LLM-as-a-judge evaluation.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Are the seven flaw types complete enough for real fact checks?\n2. What would a faithful explanation evaluation look like without a model judge?\n3. Does aspect generation improve retrieval, explanation, or only surface organization?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\diagrams\\method.mmd",
          "content": "flowchart LR\n  C[Claim] --> R[Dense evidence retriever]\n  R --> A[Aspect generator]\n  A --> F[Flaw checker]\n  R --> F\n  F --> J[Justification generator]\n  R --> J\n"
        },
        {
          "path": "research\\papers\\how-we-refute-claims-automatic-fact-checking-thr-fd880d30\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Deck[NYCU lab deck: trustworthy AI] --> R[RefuteClaim]\n  R --> F[Flaw-oriented fact checking]\n  R --> E[Evidence extraction]\n  R --> X[Explanation generation]\n"
        }
      ],
      "sections": [
        {
          "heading": "ABSTRACT",
          "page": 1
        },
        {
          "heading": "INTRODUCTION",
          "page": 1
        },
        {
          "heading": "related work, which solely considers 𝐶𝑖and 𝐸𝑖. The model does not",
          "page": 3
        },
        {
          "heading": "CONCLUSION AND FUTURE WORK",
          "page": 4
        },
        {
          "heading": "REFERENCES",
          "page": 4
        }
      ]
    },
    {
      "id": "issr-iterative-selection-with-self-review-for-vo-9414a4f1",
      "title": "ISSR: Iterative Selection with Self-Review for Vocabulary Test Distractor Generation",
      "authors": "Yu-Cheng Liu and An-Zi Yen. “ISSR: Iterative Selection with Self-Review for Vocabulary Test Distractor Generation.” arXiv preprint arXiv:2501.03462",
      "year": 2024,
      "venue": "” arXiv preprint arXiv:2501.03462 (2024). ( Link )",
      "status": "fetched",
      "doi": null,
      "arxiv_id": "2501.03462",
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/abs/2501.03462",
          "label": "Link",
          "kind": "arxiv"
        },
        {
          "url": "https://arxiv.org/pdf/2501.03462",
          "label": "arxiv",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\README.md",
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\method.md",
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\experiments-and-results.md",
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\limitations-and-critique.md",
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\prerequisites.md",
        "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\README.md",
          "content": "# ISSR: Iterative Selection with Self-Review for Vocabulary Test Distractor Generation\n\n- **Status:** full text fetched and extracted (42 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv 2501.03462; SHA-256 `97c0244e54b7dfedb7435e64f49c2709fec21a7195b4edf31a0b02728981bbfb`.\n- **Evidence anchors:** Abstract p. 1; method p. 17; results p. 19.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\method.md",
          "content": "# Method\n\n## Paper claim\n\nISSR generates vocabulary-test distractors in three stages: a candidate generator, an LLM distractor selector, and a distractor validator (pp. 13–16). The candidate generator is CDGP-CSG, a BERT-based model trained for distractor generation; rule filters remove unsuitable candidates (p. 14).\n\nThe validator is an LLM self-review step: it turns a target word and one proposed distractor into a binary-choice question. If the distractor can be selected as correct, it is rejected because the item would have multiple valid answers (p. 16).\n\n## Builder interpretation\n\nThe key design move is to use an LLM primarily for constrained selection and validation, not unconstrained bulk generation. It treats invalid test items as a quality-control problem.\n\n## Unresolved question\n\nDoes an LLM validator reliably catch semantic ambiguity for the students who will actually take the exam?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe evaluation uses 195 GSAT English vocabulary questions from 2006–2018; two are few-shot demonstrations and the other 193 are test questions (p. 16). The paper reports F-score and NDCG for up to 30 candidates.\n\nISSR reports F1@3 1.55%, F1@10 2.07%, NDCG@3 3.57%, NDCG@10 6.31%, and NDCG@30 9.82%; the version without self-review reports lower F1@3 (1.04%) and NDCG@3 (3.11%) (Table 2, p. 17).\n\nThe paper reports a 98.79% distractor-selection rate at candidate-set size 50, falling to 90.67% at size 300 (Table 5, p. 22). Selecting three distractors per round gives its best reported F1@3/NDCG@3 among the tested batch sizes (Table 7, p. 25).\n\n## Evidence caveat\n\nAbsolute retrieval-style scores are low because suitable distractors may be absent from generated candidate pools; the paper explicitly identifies candidate generation as the bottleneck (pp. 17–19).\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe authors report that combining the LLM and BERT requires more computation than similar work, and that individual binary-choice validations make generation slow (p. 26).\n\n## Builder interpretation\n\nThe self-review test asks the same class of model that selected candidates to act as a validity filter. This is a practical heuristic, but correlated failure modes could survive both stages. The evaluation is also tied to Taiwanese GSAT vocabulary items.\n\n## Unresolved question\n\nHow do teacher judgments and real learner error patterns change when ISSR distractors are used in new exams?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\prerequisites.md",
          "content": "# Prerequisites\n\n- Multiple-choice distractor validity: plausible but not correct.\n- Masked-language-model candidate generation.\n- Zero- and few-shot selection with LLMs.\n- F1 and NDCG ranking metrics.\n- The distinction between selection quality and candidate-pool coverage.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Is the self-review mechanism validation, selection, or another ranking stage?\n2. Why does a smaller selection batch help, and would that generalize beyond vocabulary tests?\n3. Which human study would best test whether rejected distractors were genuinely invalid?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Q[Stem + target word] --> G[CDGP-CSG candidate generator]\n  G --> S[LLM selector]\n  S --> V[Binary-choice self-review validator]\n  V -->|valid| O[Distractor suggestions]\n  V -->|invalid| S\n"
        },
        {
          "path": "research\\papers\\issr-iterative-selection-with-self-review-for-vo-9414a4f1\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Deck[NYCU lab deck: educational LLMs] --> I[ISSR]\n  I --> Assessment[Language assessment]\n  I --> Review[Self-review]\n  I --> HCAI[Teacher support]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Method",
          "page": 17
        },
        {
          "heading": "Results Using Different LLMs for Distractor Selection.",
          "page": 19
        },
        {
          "heading": "References",
          "page": 27
        }
      ]
    },
    {
      "id": "magic-multi-argument-generation-with-self-refine-c6b431d5",
      "title": "MAGIC: Multi-Argument Generation with Self-Refinement for Domain Generalization in Automatic Fact-Checking",
      "authors": "Wei-Yu Kao and An-Zi Yen",
      "year": 2024,
      "venue": "” In Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024), May 20-25, Torino, Italy. (Long Paper)",
      "status": "unresolved",
      "doi": "10.63317/2yyfqugvx8xo",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "paraphrase-aligned-machine-translation-4b61bbb7",
      "title": "Paraphrase-Aligned Machine Translation",
      "authors": "Ke-Ching Chang, Chung-Chi Chen, and An-Zi Yen. “Paraphrase-Aligned Machine Translation.” arXiv preprint arXiv:2412.05916",
      "year": 2024,
      "venue": "” arXiv preprint arXiv:2412.05916 (2024). ( Link )",
      "status": "fetched",
      "doi": null,
      "arxiv_id": "2412.05916",
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/abs/2412.05916",
          "label": "Link",
          "kind": "arxiv"
        },
        {
          "url": "https://arxiv.org/pdf/2412.05916",
          "label": "arxiv",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\README.md",
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\method.md",
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\experiments-and-results.md",
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\limitations-and-critique.md",
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\prerequisites.md",
        "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\README.md",
          "content": "# Paraphrase-Aligned Machine Translation\n\n- **Status:** full text fetched and extracted (5 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv 2412.05916; SHA-256 `65356c65ab90936243f1bab5c49aa9e912f4f35e687f77950089989532153351`.\n- **Evidence anchors:** Abstract p. 1; method p. 2; results pp. 3-4.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\method.md",
          "content": "# Method\n\n## Paper claim\n\nParaAlign Translator first creates source-language paraphrases that better match target-language structure, then LoRA-fine-tunes LLaMA-3-8B on original translation pairs and target-to-paraphrased-source pairs (pp. 1–2). It uses prompts for direct translation, translation fine-tuning, and paraphrasing (Table 1, p. 2).\n\nThe paper uses LLaMA-3-8B to generate paraphrased aligned pairs and sets LoRA rank to 128 in the reported experiments (pp. 2–3).\n\n## Builder interpretation\n\nThe method moves some cross-lingual structural work into a controlled source-side rewrite, making translation easier for a smaller downstream model.\n\n## Unresolved question\n\nWhen does paraphrasing preserve meaning versus introduce an error that translation metrics may not expose?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nFor resource-rich language pairs, the method reports improvements over LLaMA-3-8B in every Table-2 cell; for example Zh→En COMET/ROUGE-L rises from 79.65/47.85 to 79.90/50.67 (Table 2, p. 3). For low-resource tests, the paper reports gains for Heb→En and Swh→En but lower En→Swh scores (Table 3, p. 3).\n\nFor Zh→En, the 8B ParaAlign model reports COMET 79.90 and ROUGE-L 50.67, compared with 79.11/47.29 for ordinary fine-tuning and 80.24/50.32 for few-shot LLaMA-3-70B (Table 5, p. 4).\n\nThe data-size analysis reports that 500 paraphrased pairs underperform ordinary training on ROUGE-L, while 1,000 pairs (about 5% of the original set) reach 51.22% and stabilize thereafter (p. 4).\n\n## Evidence caveat\n\nThe results are reported using COMET and ROUGE-L. They support the stated benchmark comparisons, not a general guarantee of idiomatic translation or semantic preservation.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe paper has primarily tested English↔other-language directions, not non-English-to-non-English pairs; it explicitly leaves that generalization uncertain (p. 5).\n\n## Builder interpretation\n\nThe method relies on LLM-generated paraphrases as training data. A useful next evaluation would separately score paraphrase faithfulness and target-language naturalness, particularly where the technique lowers a low-resource direction's score.\n\n## Unresolved question\n\nCan the approach preserve terminology and style in domains where paraphrasing is constrained, such as legal or medical translation?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\prerequisites.md",
          "content": "# Prerequisites\n\n- Machine translation quality versus naturalness.\n- Source-side paraphrasing and structure alignment.\n- Instruction tuning and LoRA.\n- COMET and ROUGE-L; neither substitutes for targeted human evaluation.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. How can paraphrase faithfulness be tested before translation?\n2. Why does the approach help several directions but not En→Swh in the reported table?\n3. Is the comparison to a 70B few-shot model a fair cost-quality comparison?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\diagrams\\method.mmd",
          "content": "flowchart LR\n  S[Source sentence] --> P[LLM paraphrase aligned to target structure]\n  S --> D[Original translation pair]\n  P --> A[Paraphrase-aligned pair]\n  D --> F[LoRA fine-tuning]\n  A --> F\n  F --> T[Translation]\n"
        },
        {
          "path": "research\\papers\\paraphrase-aligned-machine-translation-4b61bbb7\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> MT[Paraphrase-Aligned MT]\n  MT --> Align[Cross-lingual structural alignment]\n  MT --> Efficient[Small-model adaptation]\n  MT --> Bilingual[English / Chinese and other pairs]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "Related Work",
          "page": 2
        },
        {
          "heading": "Experiment",
          "page": 2
        },
        {
          "heading": "Method",
          "page": 2
        },
        {
          "heading": "Method",
          "page": 3
        },
        {
          "heading": "Conclusion",
          "page": 4
        },
        {
          "heading": "experiment underscores the critical role of our ap-",
          "page": 4
        },
        {
          "heading": "Limitations",
          "page": 5
        },
        {
          "heading": "References",
          "page": 5
        }
      ]
    },
    {
      "id": "visual-lifelog-retrieval-through-captioning-enha-ffbd056d",
      "title": "Visual Lifelog Retrieval through Captioning-Enhanced Interpretation",
      "authors": "Yu-Fei Shih, An-Zi Yen, Hen-Hsen Huang, Hsin-Hsi Chen",
      "year": 2024,
      "venue": "” In Proceedings of the 2024 IEEE International Conference on Big Data (IEEE BigData 2024), December 15-18, Washington DC, USA. (Short Paper, Acceptance rate = 19.7% = 130/660)",
      "status": "fetched",
      "doi": "10.1109/bigdata62323.2024.10825835",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/pdf/2510.04010",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\README.md",
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\method.md",
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\experiments-and-results.md",
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\limitations-and-critique.md",
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\prerequisites.md",
        "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\README.md",
          "content": "# Visual Lifelog Retrieval through Captioning-Enhanced Interpretation\n\n- **Status:** full text fetched and extracted (9 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `3bd20259c3d7da50b5e4c60f7abb95890d8b467dbd9630a50d2b4f7ab210c44a`.\n- **Evidence anchors:** Abstract p. 1; method p. 1; results p. 2.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\method.md",
          "content": "# Method\n\n## Paper claim\n\nThe CIVIL system converts first-person lifelog images into captions, embeds captions and text queries in a common text space, and retrieves relevant frames (pp. 1–3). It compares single-image captions, collective captions for consecutive frames, and a merged method with fine- and coarse-grained captions (pp. 2–3).\n\n## Builder interpretation\n\nCaptioning changes retrieval from an opaque image–text similarity operation into a text-mediated pipeline that can be inspected, while adding caption hallucination and error-propagation risks.\n\n## Unresolved question\n\nHow much of the reported retrieval improvement comes from richer captions versus the choice of text embedding model?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe evaluation uses about 63,000 NTCIR-14 Lifelog-3 images from 29 days, with 10 ImageCLEF 2019 LMRT query topics; primary evaluation is average P@10 (p. 3).\n\nAfter correction for labeling/interpretation errors, four captioning methods exceed direct-image baselines; LLaVA-NeXT and LLaVA-NeXT × Video-LLaVA report corrected average P@10 of 0.78 (Table III, p. 7). A GPT-4o reranking experiment raises average P@10 from 0.58 to 0.66 and corrected P@10 from 0.72 to 0.79 (p. 6).\n\n## Evidence caveat\n\nThe corrected evaluation deliberately excludes some label-related errors, so it is diagnostic evidence rather than the only operational score.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe paper identifies contextual-image, first-person viewpoint, event-detection, object-hallucination, and label-interpretation errors. Merged captions can propagate an early summary error; GPT-4o reranking is costly (pp. 5–6).\n\n## Builder interpretation\n\nThe architecture makes captions auditable but also turns a private-memory retrieval system into one that must handle sensitive visual descriptions carefully.\n\n## Unresolved question\n\nDoes performance persist for other lifeloggers rather than the single evaluated NTCIR user?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\prerequisites.md",
          "content": "# Prerequisites\n\n- First-person lifelog retrieval and semantic gap.\n- Vision-language and video-language captioning.\n- Text embedding retrieval, P@K, cluster recall, and diversity.\n- Caption hallucination and sequence-level error propagation.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. When is a collective caption better than a fine-grained caption for memory recall?\n2. How should a lifelog system expose caption uncertainty to users?\n3. What privacy constraints should apply to stored captions and embeddings?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\diagrams\\method.mmd",
          "content": "flowchart LR\n  I[First-person image sequence] --> C[Single / collective / merged captions]\n  C --> E[Text embeddings]\n  Q[Memory query] --> E\n  E --> R[Top-K relevant frames]\n"
        },
        {
          "path": "research\\papers\\visual-lifelog-retrieval-through-captioning-enha-ffbd056d\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> V[CIVIL visual-lifelog retrieval]\n  V --> PKB[Personal knowledge / memory recall]\n  V --> Multi[Multimodal interpretation]\n  V --> IR[Text-query information retrieval]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract—People often struggle to remember specific details",
          "page": 1
        },
        {
          "heading": "method, and the merged caption method, each designed to",
          "page": 1
        },
        {
          "heading": "method uses GPT-4-turbo-vision [14] to cluster lifelog images",
          "page": 2
        },
        {
          "heading": "results and explore ways to enhance our system further.",
          "page": 2
        },
        {
          "heading": "method with the GTE-large model.",
          "page": 4
        },
        {
          "heading": "Results: Without employing diversity-promoting algorithms,",
          "page": 4
        },
        {
          "heading": "method, failed to retrieve any correct images. Conversely, in",
          "page": 4
        },
        {
          "heading": "method with BGE-M3 embeddings retrieved all 10 correct",
          "page": 4
        },
        {
          "heading": "Method Name",
          "page": 5
        },
        {
          "heading": "Method",
          "page": 7
        },
        {
          "heading": "REFERENCES",
          "page": 8
        },
        {
          "heading": "approach outperforms baseline methods that directly embed",
          "page": 8
        }
      ]
    },
    {
      "id": "citation-intent-classification-and-its-supportin-e9712fbd",
      "title": "Citation Intent Classification and Its Supporting Evidence Extraction for Citation Graph Construction",
      "authors": "Hong-Jin Tsai, An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "” In Proceedings of the 32nd ACM International Conference on Information and Knowledge Management (CIKM 2023), October 21-25, Birmingham, UK. (Full paper, acceptance rate: 24%=354/1472)",
      "status": "unresolved",
      "doi": "10.1145/3583780.3614808",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "contributionsum-generating-disentangled-contribu-cfd53bec",
      "title": "ContributionSum: Generating Disentangled Contributions for Scientific Papers",
      "authors": "Meng-Huan Liu, An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "” In Proceedings of the 32nd ACM International Conference on Information and Knowledge Management (CIKM 2023), October 21-25, Birmingham, UK. (Resource paper, acceptance rate: 27%=22/81)",
      "status": "unresolved",
      "doi": "10.1145/3583780.3615115",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "led-a-dataset-for-life-event-extraction-from-dia-a949b678",
      "title": "LED: A Dataset for Life Event Extraction from Dialogs",
      "authors": "Yi-Pei Chen, An-Zi Yen, Hen-Hsen Huang, Hideki Nakayama and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "\" In Proceedings of the 17th Conference of the European Chapter of the Association for Computational Linguistics (EACL 2023), May 2-6, Dubrovnik, Croatia. (Finding Paper)",
      "status": "fetched",
      "doi": "10.18653/v1/2023.findings-eacl.29",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2023.findings-eacl.29.pdf",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\README.md",
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\method.md",
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\experiments-and-results.md",
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\limitations-and-critique.md",
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\prerequisites.md",
        "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\README.md",
          "content": "# LED: A Dataset for Life Event Extraction from Dialogs\n\n- **Status:** full text fetched and extracted (15 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `df1bc566bcd64b028a39e6b99ad8b7b3b0203a12f314a73016e844f6a633bd22`.\n- **Evidence anchors:** Abstract p. 1; method pp. 1-3; results pp. 1-2.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\method.md",
          "content": "# Method\n\n## Paper claim\n\nLED introduces conversational life-event extraction. Each event has a verb, fine-grained class, coarse FrameNet frame, explicitness, participants with coreference, and dynamic polarity/modality/time status (pp. 1-3). The paper evaluates OpenIE, relation-extraction, and event-extraction frameworks.\n\n## Builder interpretation\n\nThe schema treats a conversation as an evolving account of a person's life rather than a bag of independently stated events. The status annotations are essential for avoiding false personal facts.\n\n## Unresolved question\n\nCan a downstream personal knowledge base express uncertainty without flattening hypothetical and negated events into facts?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe paper presents LED as the first fine-grained conversational life-event dataset and compares OpenIE, relation extraction, and event extraction baselines (pp. 1-2). Its central reported result is negative: even task-specialized information extraction systems struggle with daily, conversational life events (pp. 1-2).\n\n## Evidence caveat\n\nThis study note preserves the reported qualitative conclusion. Consult `extraction.json` and the paper tables for task-specific scores before making a numerical comparison.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nLife-event triggers can be implicit, participant mentions vary through dialogue, and event status changes across turns; the paper reports baseline difficulty with these properties (pp. 1-2).\n\n## Builder interpretation\n\nThe rich annotation is valuable but makes annotation and generalization harder. A production personal-memory system also needs consent, retention, and correction mechanisms beyond extraction accuracy.\n\n## Unresolved question\n\nHow well do English conversational annotations transfer to multilingual, code-switched, or privacy-sensitive conversations?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\prerequisites.md",
          "content": "# Prerequisites\n\n- Open-domain dialogue and coreference.\n- Event triggers, arguments, FrameNet-style event types.\n- Polarity, modality, and temporal status.\n- OpenIE, relation extraction, and event extraction.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which annotations are indispensable for a safe personal knowledge base?\n2. Should implicit events be evaluated differently from explicit triggers?\n3. How can a system let a user correct an inferred life event?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\diagrams\\method.mmd",
          "content": "flowchart LR\n  D[Dialogue] --> E[Life-event extraction]\n  E --> T[Verb, class, frame]\n  E --> P[Participants and coreference]\n  E --> S[Polarity, modality, time]\n  T --> K[Personal knowledge representation]\n  P --> K\n  S --> K\n"
        },
        {
          "path": "research\\papers\\led-a-dataset-for-life-event-extraction-from-dia-a949b678\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> L[LED]\n  L --> Dialog[Conversation understanding]\n  L --> PKB[Personal knowledge bases]\n  L --> Recall[Memory assistance]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "Related Work",
          "page": 2
        },
        {
          "heading": "results show that the existing information extrac-",
          "page": 2
        },
        {
          "heading": "limitations of each model, and urge the develop-",
          "page": 2
        },
        {
          "heading": "Conclusion",
          "page": 9
        },
        {
          "heading": "Limitations",
          "page": 9
        },
        {
          "heading": "References",
          "page": 9
        }
      ]
    },
    {
      "id": "multi-perspective-sentiment-analysis-on-life-eve-93734917",
      "title": "Multi-Perspective Sentiment Analysis on Life Events with Sentiment Cause Identification",
      "authors": "Keat Teng Swai, An-Zi Yen, Hen-Hsen Huang, Hsin-Hsi Chen",
      "year": 2023,
      "venue": "” In Proceedings of the IEEE/WIC International Conference on Web Intelligence and Intelligent Agent Technology (WI-IAT 2023), October 26-29, Venice, Italy. (Acceptance rate: 27.92%)",
      "status": "unresolved",
      "doi": "10.1109/wi-iat59888.2023.00010",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "opportunities-and-challenges-of-explainable-arti-34d07b9b",
      "title": "Opportunities and challenges of explainable artificial intelligence in medicine: toward causability for physicians, developers, and patients",
      "authors": "An-Zi Yen, Cheng-Kuang Wu and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "\" Artificial Intelligence, Machine Learning, and Deep Learning in Precision Medicine in Liver Diseases, 281-307",
      "status": "unresolved",
      "doi": null,
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "rsvp-customer-intent-detection-via-agent-respons-5508f782",
      "title": "RSVP: Customer Intent Detection via Agent Response Contrastive and Generative Pre-Training",
      "authors": "Yu-Chien Tang, Wei-Yao Wang, An-Zi Yen, and Wen-Chih Peng",
      "year": 2023,
      "venue": "” In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP 2023), December 6-10, Singapore. (Finding Paper)",
      "status": "fetched",
      "doi": "10.18653/v1/2023.findings-emnlp.698",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2023.findings-emnlp.698.pdf",
          "label": "openalex",
          "kind": "pdf"
        },
        {
          "url": "https://arxiv.org/pdf/2310.09773",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\README.md",
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\method.md",
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\experiments-and-results.md",
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\limitations-and-critique.md",
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\prerequisites.md",
        "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\README.md",
          "content": "# RSVP: Customer Intent Detection via Agent Response Contrastive and Generative Pre-Training\n\n- **Status:** full text fetched and extracted (13 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `c7b82ee5077094d2f62ea499bd4e2f24532f676615d17000d59d999f619615d1`.\n- **Evidence anchors:** Abstract p. 1; method p. 2; results p. 5.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\method.md",
          "content": "# Method\n\n## Paper claim\n\nRSVP uses agent responses during pre-training, then fine-tunes on customer intent labels. Its two self-supervised objectives are response retrieval from a candidate batch and response generation that mimics an agent answer; a contrastive loss is added during intent fine-tuning (pp. 1-3).\n\n## Builder interpretation\n\nThe approach treats agent replies as lower-cost latent supervision: a useful reply implies that the agent understood the customer's intent, even though the reply is unavailable at live inference time.\n\n## Unresolved question\n\nHow robust is the learned association when historical agent responses are incorrect, templated, or policy-driven rather than intent-specific?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nAcross two real-world customer-service datasets, the abstract reports average improvements over state-of-the-art baselines of 4.95 percentage points in accuracy, 3.4 in MRR@3, and 2.75 in MRR@5 (p. 1). The paper attributes this to response retrieval and generation pre-training rather than added public pre-training corpora (pp. 1-3).\n\n## Evidence caveat\n\nThese are the paper's reported benchmark results. They do not establish performance under live distribution shift or response-policy changes.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nThe paper notes that agent responses cannot be used directly at real-time intent-detection inference; they are training-time metadata (p. 2).\n\n## Builder interpretation\n\nHistorical agent responses can encode organizational habits and mistakes. An offline gain should be paired with audits for response quality, privacy, and intents that evolve after deployment.\n\n## Unresolved question\n\nWould the objectives remain helpful with multilingual agents or sparse, one-line responses?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\prerequisites.md",
          "content": "# Prerequisites\n\n- Task-oriented dialogue and supervised intent classification.\n- Dual-encoder response retrieval and batch contrastive loss.\n- Conditional response generation.\n- Accuracy and MRR ranking metrics.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which properties make an agent response useful supervision rather than leakage?\n2. How would noisy or automated agent responses affect pre-training?\n3. Can the retrieval and generation objectives be disentangled experimentally?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\diagrams\\method.mmd",
          "content": "flowchart LR\n  U[Customer utterance] --> R[Response retrieval pre-training]\n  U --> G[Response generation pre-training]\n  A[Historical agent response] --> R\n  A --> G\n  R --> F[Intent fine-tuning]\n  G --> F\n  F --> I[Customer intent]\n"
        },
        {
          "path": "research\\papers\\rsvp-customer-intent-detection-via-agent-respons-5508f782\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> R[RSVP]\n  R --> Dialog[Task-oriented dialogue]\n  R --> Intent[Customer intent detection]\n  R --> Pretrain[Response-based self-supervision]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "method is flexible for the intent detection prob-",
          "page": 2
        },
        {
          "heading": "Related work",
          "page": 2
        },
        {
          "heading": "Method",
          "page": 3
        },
        {
          "heading": "results are averaged over 5 different random seeds.",
          "page": 5
        },
        {
          "heading": "Results on Larger Datasets",
          "page": 6
        },
        {
          "heading": "results are shown in Table 2. We note that the ac-",
          "page": 6
        },
        {
          "heading": "Limitations",
          "page": 9
        },
        {
          "heading": "References",
          "page": 9
        },
        {
          "heading": "Conclusion",
          "page": 9
        }
      ]
    },
    {
      "id": "three-questions-concerning-the-use-of-large-lang-131918a6",
      "title": "Three Questions Concerning the Use of Large Language Models to Facilitate Mathematics Learning",
      "authors": "An-Zi Yen and Wei-Ling Hsu",
      "year": 2023,
      "venue": "” In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP 2023), December 6-10, Singapore. (Finding Paper)",
      "status": "fetched",
      "doi": "10.18653/v1/2023.findings-emnlp.201",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2023.findings-emnlp.201.pdf",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\README.md",
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\method.md",
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\experiments-and-results.md",
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\limitations-and-critique.md",
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\prerequisites.md",
        "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\README.md",
          "content": "# Three Questions Concerning the Use of Large Language Models to Facilitate Mathematics Learning\n\n- **Status:** full text fetched and extracted (15 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `d592e7bfeaf30e3c91153bfb11b7cb1d6acb5f34f7a609cb90a318bc67dc3a06`.\n- **Evidence anchors:** Abstract p. 1; framing pp. 1-2; results pp. 2, 9.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\method.md",
          "content": "# Method\n\n## Paper claim\n\nThis position paper asks three questions about using GPT-3.5 for adaptive mathematics feedback: how LLMs can help, whether they solve and explain math correctly, and whether they can understand and correct student processes (pp. 1-2).\n\n## Builder interpretation\n\nIt establishes the problem framing later operationalized by MathEDU: fluent correction is not trustworthy if the system misunderstands a valid student strategy.\n\n## Unresolved question\n\nWhich feedback evaluation best predicts learning rather than answer agreement?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nOn 1,605 MathQA questions, GPT-3.5 reports 66.54% zero-shot accuracy, 65.67% few-shot accuracy, and 66.11% chain-of-thought accuracy (Table 1, p. 2). The paper reports that GPT-3.5 can be misled by human answers and may incorrectly repair valid reasoning (p. 9).\n\n## Evidence caveat\n\nThe study is a position/pilot paper using GPT-3.5 and a small human evaluation, not a broad classroom deployment.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nOnly GPT-3.5 is evaluated; human evaluation covers 120 questions and five students answer three questions each (p. 5).\n\n## Builder interpretation\n\nThe direct warning about incorrect correction is more important than the aggregate accuracy: a tutoring system needs calibrated uncertainty and teacher oversight.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\prerequisites.md",
          "content": "# Prerequisites\n\n- Math word-problem solving and student-process feedback.\n- Zero-shot, few-shot, and chain-of-thought prompting.\n- Accuracy versus pedagogical reliability.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. When should a system abstain rather than correct a student?\n2. Why can a model solve a problem yet misread a student's solution?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\diagrams\\method.mmd",
          "content": "flowchart LR\n  S[Student solution] --> C[Correctness assessment]\n  C --> E[Error explanation]\n  E --> F[Adaptive feedback]\n  F --> R[Three research questions]\n"
        },
        {
          "path": "research\\papers\\three-questions-concerning-the-use-of-large-lang-131918a6\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  P[Position paper] --> M[MathEDU]\n  P --> A[Adaptive math feedback]\n  P --> T[Trustworthy tutoring]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "results for six MathQA question types. In this ex-",
          "page": 2
        },
        {
          "heading": "Conclusion",
          "page": 4
        },
        {
          "heading": "References",
          "page": 5
        },
        {
          "heading": "Limitations",
          "page": 5
        }
      ]
    },
    {
      "id": "visual-lifelog-retrieval-humans-and-machines-int-85bd274d",
      "title": "Visual Lifelog Retrieval: Humans and Machines Interpretation on First-Person Images",
      "authors": "An-Zi Yen, Min-Huan Fu, Wei-Hong Ang, Tai-Te Chu, Ssu-Hao Tsai, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "” Multimedia Tools and Applications. ( Link )",
      "status": "unresolved",
      "doi": "10.1007/s11042-023-14344-x",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [
        {
          "url": "https://link.springer.com/article/10.1007/s11042-023-14344-x",
          "label": "Link",
          "kind": "external"
        }
      ],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "zara-improving-few-shot-self-rationalization-for-9690fce3",
      "title": "ZARA: Improving Few-Shot Self-Rationalization for Small Language Models",
      "authors": "Wei-Lin Chen, An-Zi Yen, Cheng-Kuang Wu, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2023,
      "venue": "” In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP 2023), December 6-10, Singapore. (Finding Paper)",
      "status": "fetched",
      "doi": "10.18653/v1/2023.findings-emnlp.310",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2023.findings-emnlp.310.pdf",
          "label": "openalex",
          "kind": "pdf"
        },
        {
          "url": "https://arxiv.org/pdf/2305.07355",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\README.md",
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\method.md",
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\experiments-and-results.md",
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\limitations-and-critique.md",
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\prerequisites.md",
        "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\README.md",
          "content": "# ZARA: Improving Few-Shot Self-Rationalization for Small Language Models\n\n- **Status:** full text fetched and extracted (12 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `434f04846e10f5650c315bc41415b7824a833e8a314e680046604528490825be`.\n- **Evidence anchors:** Abstract p. 1; method p. 6; results p. 4.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\method.md",
          "content": "# Method\n\n## Paper claim\n\nZARA improves small-model self-rationalization through self-training. It maps an input, generated rationale, and predicted answer to an NLI premise/hypothesis pair; an ensemble of off-the-shelf NLI models selects plausible rationale-answer pairs for pseudo-label augmentation (pp. 2, 5).\n\n## Builder interpretation\n\nThe approach uses plausibility as a selection signal, not proof of truth. It is an efficient filter for small models but inherits NLI-mapping errors.\n\n## Unresolved question\n\nCan a common mapping schema evaluate explanation plausibility across tasks without manual task-specific design?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe paper reports state-of-the-art FEB benchmark improvements of 3.4%-5.1% task accuracy and 3.0%-5.8% on its explanation metric for small models (p. 2). It uses models in the 200M-2.7B range and validates the plausibility approximator with human and quantitative evaluations (pp. 1-2).\n\n## Evidence caveat\n\nThe result depends on the task-specific NLI mapping and pseudo-label selection; it is not a guarantee that a plausible explanation is correct.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nIf NLI mapping is difficult or inaccurate, the approximator can select noisy instances that hurt self-training (p. 9).\n\n## Builder interpretation\n\nPlausibility is necessary for readable rationale quality but insufficient for faithfulness or correctness; the method should be paired with answer verification.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\prerequisites.md",
          "content": "# Prerequisites\n\n- Few-shot self-rationalization.\n- Natural language inference and entailment/contradiction.\n- Pseudo-label self-training and confidence filtering.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. What distinguishes plausibility from explanation faithfulness?\n2. Which NLI mappings would be most fragile across tasks?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\diagrams\\method.mmd",
          "content": "flowchart LR\n  U[Unlabeled input] --> G[Small model: rationale + answer]\n  G --> N[NLI plausibility approximator]\n  N -->|high confidence| P[Pseudo rationale-answer pair]\n  P --> F[Fine-tuned self-rationalizer]\n"
        },
        {
          "path": "research\\papers\\zara-improving-few-shot-self-rationalization-for-9690fce3\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> Z[ZARA]\n  Z --> Explain[Free-text explanation]\n  Z --> Trust[Trustworthy AI]\n  Z --> Small[Accessible small models]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "results also align with the prior work (Wiegreffe",
          "page": 4
        },
        {
          "heading": "Method Model",
          "page": 6
        },
        {
          "heading": "results on the newly introduced FEB benchmark",
          "page": 7
        },
        {
          "heading": "results show our approximator is capable of reflect-",
          "page": 7
        },
        {
          "heading": "Related Work",
          "page": 8
        },
        {
          "heading": "Conclusion",
          "page": 9
        },
        {
          "heading": "Limitations",
          "page": 9
        },
        {
          "heading": "References",
          "page": 9
        }
      ]
    },
    {
      "id": "incorporating-peer-reviews-and-rebuttal-counter--32bc5041",
      "title": "Incorporating Peer Reviews and Rebuttal Counter-Arguments for Meta-Review Generation",
      "authors": "Po-Cheng Wu, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2022,
      "venue": "\" In Proceedings of the 31st ACM International Conference on Information and Knowledge Management (CIKM 2022), October 17-21, Hybrid Conference, Hosted in Atlanta, Georgia, USA",
      "status": "unresolved",
      "doi": "10.1145/3511808.3557360",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "learning-to-generate-explanation-from-e-hospital-049b151e",
      "title": "Learning to Generate Explanation from e-Hospital Services for Medical Suggestion",
      "authors": "Wei-Lin Chen, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2022,
      "venue": "\" In Proceedings of the 29th International Conference on Computational Linguistics (COLING 2022), October 12-17, Gyeongju, Republic of Korea",
      "status": "unresolved",
      "doi": null,
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "modeling-inter-round-attack-of-online-debaters-f-f81c25f5",
      "title": "Modeling Inter Round Attack of Online Debaters for Winner Prediction",
      "authors": "Fa-Hsuan Hsiao, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2022,
      "venue": "” In Proceedings of the Web Conference 2022 (WWW 2022), April 25-29, 2022. (full paper, acceptance rate=17.7%=323/1822)",
      "status": "unresolved",
      "doi": "10.1145/3485447.3512006",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "seen-structured-event-enhancement-network-for-ex-b0b9bf75",
      "title": "SEEN: Structured Event Enhancement Network for Explainable Need Detection of Information Recall Assistance",
      "authors": "You-En Lin, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2022,
      "venue": "” In Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing (EMNLP 2022), December 7-11, Abu Dhabi, the United Arab Emirates",
      "status": "fetched",
      "doi": "10.18653/v1/2022.emnlp-main.365",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\source.pdf",
      "links": [
        {
          "url": "https://aclanthology.org/2022.emnlp-main.365.pdf",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\README.md",
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\method.md",
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\experiments-and-results.md",
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\limitations-and-critique.md",
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\prerequisites.md",
        "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\README.md",
          "content": "# SEEN: Structured Event Enhancement Network for Explainable Need Detection of Information Recall Assistance\n\n- **Status:** full text fetched and extracted (14 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `97723abdeae7eb62d4e4f032c70d0ff5844cd9e55f931583962c0c634f858f15`.\n- **Evidence anchors:** Abstract p. 1; method pp. 1-5; results pp. 7-8.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\method.md",
          "content": "# Method\n\n## Paper claim\n\nSEEN compares a pre-retold and post-retold life narrative to identify consistent, inconsistent, additional, forgotten, or unforgotten events. It constructs a coreference-aware event graph, encodes it with graph attention, fuses it with a Longformer textual encoder, and selects related nodes as support evidence (pp. 1-5).\n\n## Builder interpretation\n\nThe graph is both a performance feature and an explanation interface: selected nodes can remind a user why the system thinks a memory is confused or incomplete.\n\n## Unresolved question\n\nCan the approach work without the gold event graph used in the current experiments?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result (reported; not reproduced)\n\nThe NIR dataset extends Hippocorpus with five event types for information-recall need detection (pp. 1-2). SEEN with Longformer-large reports F-score 0.6654; removing the event graph lowers it to 0.6334, the largest reported ablation drop (Table 3, p. 8). When detection is correct, support-evidence extraction F-score is 0.8095; when wrong, it is 0.6671 (Table 4, p. 8).\n\n## Evidence caveat\n\nThe paper uses gold event graphs. End-to-end extraction quality remains a future requirement.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Author limitation\n\nInconsistent events remain challenging, and the experiments use gold event graphs; the authors leave automatic event-graph construction and end-to-end deployment to future work (p. 9).\n\n## Builder interpretation\n\nProactive recall is high-impact: even useful reminders should be user-controlled because an incorrect memory correction can be intrusive or harmful.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\prerequisites.md",
          "content": "# Prerequisites\n\n- Personal knowledge graphs and event triples.\n- Coreference resolution and graph attention networks.\n- NLI-style consistency and support-evidence extraction.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. What user interface makes proactive memory correction safe?\n2. How much performance remains when event graphs are predicted rather than gold?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\diagrams\\method.mmd",
          "content": "flowchart LR\n  A[Pre-retold story] --> G[Coreference-aware event graph]\n  B[Post-retold story] --> T[Target event]\n  G --> F[Graph-text fusion]\n  T --> F\n  F --> D[Need type]\n  F --> E[Support evidence nodes]\n"
        },
        {
          "path": "research\\papers\\seen-structured-event-enhancement-network-for-ex-b0b9bf75\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Lab[NYCU NLP Lab] --> S[SEEN]\n  S --> Memory[Proactive memory assistance]\n  S --> Graph[Personal event graph]\n  S --> Explain[Support evidence]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "results of each event type. F-score is adopted as",
          "page": 7
        },
        {
          "heading": "Conclusion",
          "page": 9
        },
        {
          "heading": "Related Work",
          "page": 9
        },
        {
          "heading": "Limitations",
          "page": 10
        },
        {
          "heading": "References",
          "page": 10
        },
        {
          "heading": "Introduction to the Third Annual",
          "page": 11
        }
      ]
    },
    {
      "id": "unanswerable-question-correction-and-explanation-a65031d5",
      "title": "Unanswerable Question Correction and Explanation over Personal Knowledge Base",
      "authors": "An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2022,
      "venue": "” In Proceedings of the 31st ACM International Conference on Information and Knowledge Management (CIKM 2022), October 17-21, Hybrid Conference, Hosted in Atlanta, Georgia, USA",
      "status": "unresolved",
      "doi": "10.1145/3511808.3557717",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "convlog-miner-a-real-time-conversational-lifelog-9ba8f4ef",
      "title": "ConvLog-Miner: A Real-Time Conversational Lifelog Miner",
      "authors": "Pei-Wei Kao, An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen.",
      "year": 2021,
      "venue": "” In Proceedings of the Thirtieth International Joint Conference on Artificial Intelligence (IJCAI 2021), pages 4992-4995, Demonstration Track, Montreal, Canada",
      "status": "unresolved",
      "doi": "10.24963/ijcai.2021/710",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "ten-questions-in-lifelog-mining-and-information--b873fc16",
      "title": "Ten Questions in Lifelog Mining and Information Recall",
      "authors": "An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2021,
      "venue": "” In Proceedings of ACM International Conference on Multimedia Retrieval 2021 (ICMR 2021), August 21-24, 2021, Taipei, Taiwan",
      "status": "fetched",
      "doi": "10.1145/3460426.3463607",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\source.pdf",
      "links": [
        {
          "url": "https://arxiv.org/pdf/2005.01535",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\README.md",
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\method.md",
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\experiments-and-results.md",
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\limitations-and-critique.md",
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\prerequisites.md",
        "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\README.md",
          "content": "# Ten Questions in Lifelog Mining and Information Recall\n\n- **Status:** full text fetched and extracted (7 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `6af31f592430fd82732dca9daef987c1cfe0ae3f094000ed931db6a03572e560`.\n- **Evidence anchors:** Abstract p. 1; research agenda pp. 1-2; synthesis pp. 4-6.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\method.md",
          "content": "# Method\n\n## Paper claim\n\nThis position paper proposes an agenda for mining heterogeneous lifelogs into a personal knowledge base and using it for reactive or proactive information recall (pp. 1-2, 6). It identifies ten questions spanning event extraction, multimodal data, entity linking, retrieval timing, privacy, and ethics.\n\n## Builder interpretation\n\nThis is the conceptual spine of the lab's later LED, SEEN, CIVIL, and personal-KB QA work.\n\n## Unresolved question\n\nHow can personal knowledge be useful while remaining local, consented, and correctable?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result\n\nThis is a research agenda, not a benchmark paper. It categorizes lifelog sources into activity visual capture, multimodal creation, communication, biometrics, location, and computer activity (p. 2), and describes personal-KB links to world knowledge and information recall (pp. 4-6).\n\n## Evidence caveat\n\nIts claims are design questions and synthesis, not reproduced empirical results.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Paper limitation\n\nThe paper emphasizes privacy, ownership, access control, and the risks of cloud storage for complete digital life traces (p. 6).\n\n## Builder interpretation\n\nThe current Research OS should inherit this constraint: provenance and local files are helpful, but do not by themselves resolve consent and retention policy.\n"
        },
        "prerequisites": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\prerequisites.md",
          "content": "# Prerequisites\n\n- Lifelog sources and personal life events.\n- Personal versus world knowledge bases.\n- Reactive and proactive information recall.\n- Privacy-by-design and personal-data ownership.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. Which of the ten questions is still least solved by current LLM systems?\n2. What is the minimum viable privacy model for a personal knowledge base?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\diagrams\\method.mmd",
          "content": "flowchart LR\n  L[Heterogeneous lifelogs] --> E[Personal event extraction]\n  E --> K[Personal knowledge base]\n  K --> R[Reactive recall]\n  K --> P[Proactive recall]\n  Privacy[Privacy and ownership] --> K\n"
        },
        {
          "path": "research\\papers\\ten-questions-in-lifelog-mining-and-information--b873fc16\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Agenda[Ten Questions agenda] --> LED[LED]\n  Agenda --> SEEN[SEEN]\n  Agenda --> CIVIL[CIVIL]\n  Agenda --> QA[Personal-KB QA]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "1 Introduction",
          "page": 1
        },
        {
          "heading": "6 Conclusion",
          "page": 6
        },
        {
          "heading": "References",
          "page": 7
        }
      ]
    },
    {
      "id": "unanswerable-question-correction-in-question-ans-c228f379",
      "title": "Unanswerable Question Correction in Question Answering over Personal Knowledge Base",
      "authors": "An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2021,
      "venue": "” In Proceedings of the Thirty-Fifth AAAI Conference on Artificial Intelligence (AAAI 2021), February 2-9, 2021. (full paper, acceptance rate: 21%=1692/7911)",
      "status": "fetched",
      "doi": "10.1609/aaai.v35i16.17678",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\source.pdf",
      "links": [
        {
          "url": "https://ojs.aaai.org/index.php/AAAI/article/download/17678/17485",
          "label": "openalex",
          "kind": "pdf"
        }
      ],
      "notes": [
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\README.md",
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\method.md",
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\experiments-and-results.md",
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\limitations-and-critique.md",
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\prerequisites.md",
        "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\seminar-questions.md"
      ],
      "documents": {
        "README": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\README.md",
          "content": "# Unanswerable Question Correction in Question Answering over Personal Knowledge Base\n\n- **Status:** full text fetched and extracted (10 pages).\n- **Metadata source:** https://azyen0522.github.io/\n- **Full text:** arXiv not applicable; SHA-256 `9dbb5a0c8e2ddc7a7c103c9a2aff519ae052d9fb9753792849db78f9beac9b1e`.\n- **Evidence anchors:** Abstract p. 1; method p. 4; results p. 8.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n"
        },
        "method": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\method.md",
          "content": "# Method\n\n## Paper claim\n\nPKBQAC answers personal-KB questions when possible and otherwise corrects a question inconsistent with stored personal facts. A semantic-parsing QA stage produces candidate query graphs; if none matches the KB, a question-construction plus reinforcement-learning editing stage suggests an answerable question (pp. 1-2, 4-6).\n\n## Builder interpretation\n\nThe key product decision is to help users repair a mistaken memory rather than simply return no answer.\n\n## Unresolved question\n\nHow should a system present competing corrections without falsely asserting one memory is definitive?\n"
        },
        "experiments-and-results": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\experiments-and-results.md",
          "content": "# Experiments and results\n\n## Observed result\n\nThe paper reports that its personal-KB QA-with-correction system is effective at correcting unanswerable questions (abstract, p. 1). It uses BERT for event extraction/alignment and GraphSAGE features in query-graph scoring, then GenTagNet for construction plus editing (pp. 4-6).\n\n## Evidence caveat\n\nConsult the extracted tables for exact scores; this summary does not treat reported effectiveness as a reproduced result.\n"
        },
        "limitations-and-critique": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\limitations-and-critique.md",
          "content": "# Limitations and critique\n\n## Builder interpretation\n\nCorrecting a memory query is inherently sensitive: candidate suggestions may be useful but need uncertainty, provenance, and an easy user correction path.\n\n## Unresolved question\n\nWhat evaluation captures whether a proposed correction matches user intent rather than merely KB consistency?\n"
        },
        "prerequisites": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\prerequisites.md",
          "content": "# Prerequisites\n\n- Knowledge-base question answering and semantic parsing.\n- Query graphs, BERT alignment, and GraphSAGE.\n- Reinforcement learning and sequence tagging for question editing.\n"
        },
        "seminar-questions": {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\seminar-questions.md",
          "content": "# Seminar questions\n\n1. When should an assistant ask a clarifying question instead of generating a correction?\n2. Which personal-KB errors are most dangerous to correct automatically?\n"
        }
      },
      "diagrams": [
        {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\diagrams\\method.mmd",
          "content": "flowchart LR\n  Q[User memory question] --> G[Candidate query graphs]\n  G --> A{KB answerable?}\n  A -->|yes| O[Answer]\n  A -->|no| C[Corrected query graph]\n  C --> N[Construct and edit question]\n  N --> S[Question suggestion]\n"
        },
        {
          "path": "research\\papers\\unanswerable-question-correction-in-question-ans-c228f379\\diagrams\\research-context.mmd",
          "content": "flowchart LR\n  Agenda[Personal KB agenda] --> P[PKBQAC]\n  P --> Recall[Memory recall]\n  P --> QA[Knowledge-base QA]\n  P --> Repair[Unanswerable-question correction]\n"
        }
      ],
      "sections": [
        {
          "heading": "Abstract",
          "page": 1
        },
        {
          "heading": "Introduction",
          "page": 1
        },
        {
          "heading": "Related Work",
          "page": 2
        },
        {
          "heading": "method described above. For the query graph generation,",
          "page": 4
        },
        {
          "heading": "results show that the imbalance of different question types",
          "page": 8
        },
        {
          "heading": "Conclusion",
          "page": 8
        },
        {
          "heading": "References",
          "page": 9
        }
      ]
    },
    {
      "id": "incorporating-semantic-knowledge-for-visual-life-6e8c0bcb",
      "title": "Incorporating Semantic Knowledge for Visual Lifelog Activity Recognition",
      "authors": "Min-Huan Fu, An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2020,
      "venue": "” In Proceedings of ACM International Conference on Multimedia Retrieval 2020 (ICMR 2020), June 8-11, Dublin, Ireland",
      "status": "unresolved",
      "doi": "10.1145/3372278.3390700",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "learning-english-chinese-bilingual-word-represen-3ef05698",
      "title": "Learning English-Chinese Bilingual Word Representations from Sentence-Aligned Parallel Corpus",
      "authors": "An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2019,
      "venue": "” Computer Speech and Language , 56:52-72. ( Link )",
      "status": "unresolved",
      "doi": "10.1016/j.csl.2019.01.002",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [
        {
          "url": "https://doi.org/10.1016/j.csl.2019.01.002",
          "label": "Link",
          "kind": "doi"
        }
      ],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "multimodal-joint-learning-for-personal-knowledge-f3c4328a",
      "title": "Multimodal joint learning for personal knowledge base construction from Twitter-based lifelogs",
      "authors": "An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2019,
      "venue": "” Information Processing & Management. ( Link )",
      "status": "unresolved",
      "doi": "10.1016/j.ipm.2019.102148",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [
        {
          "url": "https://doi.org/10.1016/j.ipm.2019.102148",
          "label": "Link",
          "kind": "doi"
        }
      ],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "personal-knowledge-base-construction-from-text-b-dd9a344d",
      "title": "Personal Knowledge Base Construction from Text-based Lifelogs",
      "authors": "An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2019,
      "venue": "” In Proceedings of 42nd International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2019), July 21-25, 2019, Paris, France. (full paper, acceptance rate: 84/426)",
      "status": "unresolved",
      "doi": "10.1145/3331184.3331209",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "detecting-personal-life-events-fom-twitter-by-mu-65210806",
      "title": "Detecting Personal Life Events fom Twitter by Multi-Task LSTM",
      "authors": "An-Zi Yen, Hen-Hsen Huang and Hsin-Hsi Chen",
      "year": 2018,
      "venue": "” In Proceedings of the Web Conference 2018 (WWW 2018), poster, April 23-27, 2018, Lyon, France",
      "status": "unresolved",
      "doi": "10.1145/3184558.3186909",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "transfer-of-frames-from-english-framenet-to-cons-43d6fd81",
      "title": "Transfer of Frames from English FrameNet to Construct Chinese FrameNet: A Bilingual Corpus-Based Approach",
      "authors": "Tsung-Han Yang, Hen-Hsen Huang, An-Zi Yen and Hsin-Hsi Chen",
      "year": 2018,
      "venue": "” In Proceedings of 11th Edition of the Language Resources and Evaluation Conference (LREC 2018), May 7-12, 2018, Miyazaki, Japan, 868-872",
      "status": "unresolved",
      "doi": "10.63317/58vv9pbm8ze4",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "fusing-domain-specific-data-with-general-data-fo-77dc9f58",
      "title": "Fusing Domain-Specific Data with General Data for In-Domain Applications",
      "authors": "An-Zi Yen, Hen-Hsen Huang, and Hsin-Hsi Chen",
      "year": 2017,
      "venue": "” In Proceedings of 2017 IEEE/WIC/ACM International Conference on Web Intelligence (WI 2017), August 23-26, 2017, Leipzig, Germany, 566-572",
      "status": "unresolved",
      "doi": "10.1145/3106426.3106473",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    },
    {
      "id": "mkds-a-medical-knowledge-discovery-system-learne-9254eb5d",
      "title": "MKDS: A Medical Knowledge Discovery System Learned from Electronic Medical Records (Demonstration)",
      "authors": "Hen-Hsen Huang, An-Zi Yen and Hsin-Hsi Chen",
      "year": 2017,
      "venue": "” In Proceedings of 13th Asia Information Retrieval Societies Conference (AIRS 2017), November 22-24, 2017, Jeju island, Korea",
      "status": "unresolved",
      "doi": "10.1007/978-3-030-03520-4_19",
      "arxiv_id": null,
      "source_url": "https://azyen0522.github.io/",
      "pdf_path": null,
      "links": [],
      "notes": [],
      "documents": {},
      "diagrams": [],
      "sections": []
    }
  ],
  "discovery": {
    "candidates": [
      {
        "title": "PHI-GUARD: Compliance-Aware LLM Routing for Healthcare with Distribution-Free Safety Guarantees",
        "authors": [
          "Aman Sharma"
        ],
        "year": 2026,
        "venue": null,
        "abstract": " Healthcare organizations deploying Large Language Models face a regulatory tradeoff: route queries through cloud APIs for cost efficiency and risk exposing protected health information (PHI), or keep everything on-premises. Existing LLM routers (RouteLLM, FrugalGPT, PILOT, BaRP) optimize cost against quality-none enforce data-residency constraints. We propose PHI-GUARD, a framework that treats data sensitivity as a hard compliance constraint. We develop SafeTS (Safetyconstrained Thompson Sampling), which builds safe action sets from classifier posteriors, and CARES (Compliance-Aware Residual Envelope Scoring), which provides distribution-free safety guarantees via asymmetric conformal residuals-requiring only exchangeability, not calibration. On 30,000 MIMIC-IV clinical queries with 10,000-query MIMIC-III cross-validation, our Dis-tilBERT classifier achieves 98.4% accuracy with 97.4% T3 (PHI) recall, but 8 misclassifications exceed confidence 0.80 (max 0.997). Static routing leaks 0.92% of PHI queries. SafeTS reduces violations from 83 to 1-8 through safe action sets but cannot eliminate them. CARES is the only strategy achieving zero violations with a verified distribution-free bound (δ + 1/(n + 1) = 0.005), routing 35.6% to cloud. Classifier ablation confirms CARES maintains zero violations across all tested architectures-from DistilBERT (98.4% accuracy) to a rule-based heuristic (56.2% accuracy)-demonstrating that the guarantee adapts to classifier quality automatically. Cross-dataset evaluation confirms CARES maintains zero violations despite 11-point T3 recall degradation on MIMIC-III, while StaticILP violations increase 5.8×. End-toend validation with real API endpoints (GPT-4o-mini, Llama-3.1) confirms safety guarantees transfer to live execution. ",
        "doi": "10.36227/techrxiv.177220388.80392106/v1",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": null,
        "semantic_scholar_id": null,
        "citation_count": 0,
        "open_access": true,
        "landing_url": "https://doi.org/10.36227/techrxiv.177220388.80392106/v1",
        "oa_url": null,
        "topics": [],
        "providers": [
          "crossref"
        ],
        "provenance": [
          {
            "provider": "crossref",
            "url": "https://api.crossref.org/works?query.bibliographic=LLM+confidence+routing&rows=5&filter=from-pub-date%3A2024-01-01%2Chas-license%3Atrue"
          }
        ],
        "provider_scores": {
          "crossref": 0.6
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 3/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "有開放取用 metadata"
        ],
        "rank_score": 0.8474024390243903,
        "id": "cand-94a62693f8ece46d",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "Evaluating Log-Likelihood for Confidence Estimation in LLM-Based Multiple-Choice Question Answering",
        "authors": [
          "Christopher Boseak"
        ],
        "year": 2025,
        "venue": null,
        "abstract": " Abstract \n         Reliable deployment of large language models (LLMs) in question-answering tasks requires well-calibrated confidence estimates. This work investigates whether token-level log-likelihoods—sums of log-probabilities over answer tokens—can serve as effective confidence signals in multiple-choice question answering (MCQA). We compare three methods: (1) raw log-likelihood, (2) length-normalized loglikelihood, and (3) conventional softmax-based choice probability. Across four diverse MCQA benchmarks, we find that no single scoring method is universally best. Length normalization can significantly improve calibration but may reduce accuracy, while softmax and raw log-likelihood yield identical predictions. These results highlight important trade-offs between calibration and accuracy, and offer insights into selecting or adapting confidence measures for different tasks. Our findings inform the design of more trustworthy LLM-based QA systems and lay groundwork for broader uncertainty quantification efforts. ",
        "doi": "10.21203/rs.3.rs-7038601/v1",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": null,
        "semantic_scholar_id": null,
        "citation_count": 0,
        "open_access": true,
        "landing_url": "https://doi.org/10.21203/rs.3.rs-7038601/v1",
        "oa_url": null,
        "topics": [],
        "providers": [
          "crossref"
        ],
        "provenance": [
          {
            "provider": "crossref",
            "url": "https://api.crossref.org/works?query.bibliographic=LLM+confidence+routing&rows=5&filter=from-pub-date%3A2024-01-01%2Chas-license%3Atrue"
          }
        ],
        "provider_scores": {
          "crossref": 1.0
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 2/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "有開放取用 metadata"
        ],
        "rank_score": 0.8221007984031937,
        "id": "cand-b9aba89c269bccd7",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "A Multi-Criteria Decision Framework for Enterprise LLM Routing",
        "authors": [
          "Marcin Nowak"
        ],
        "year": 2026,
        "venue": null,
        "abstract": " The increasing use of large language models (LLMs) in enterprises creates a need for the effective selection between lower-cost models and more advanced ones. The aim of the article is to propose a multicriteria decision-making framework for prompt routing to LLMs in an enterprise environment, taking into account organizational preferences regarding cost, response quality, business risk, response time, standardization, and creativity. The study adopts a design-and-evaluation approach. In the design phase, a mechanism was developed in which prompts are assessed according to managerial routing criteria, weighted using the AHP method, and then directed to either a lower-cost or a more powerful model using the SAW method. In the evaluation phase, the solution was tested on a dataset of 100 business prompts and compared with two benchmark strategies: always cheap and always strong. The article’s contribution includes framing LLM routing as a managerial decision-support problem, operationalizing managerial routing criteria, and proposing evaluation metrics such as sufficiency rate, average cost per prompt, cost per sufficient response, and incremental cost of sufficiency gain. The results indicate that the proposed solution improves the cost–quality trade-off, while maintaining an acceptable level of response sufficiency and limiting the cost of query handling. ",
        "doi": "10.20944/preprints202604.0905.v1",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": null,
        "semantic_scholar_id": null,
        "citation_count": 0,
        "open_access": true,
        "landing_url": "https://doi.org/10.20944/preprints202604.0905.v1",
        "oa_url": null,
        "topics": [],
        "providers": [
          "crossref"
        ],
        "provenance": [
          {
            "provider": "crossref",
            "url": "https://api.crossref.org/works?query.bibliographic=LLM+confidence+routing&rows=5&filter=from-pub-date%3A2024-01-01%2Chas-license%3Atrue"
          }
        ],
        "provider_scores": {
          "crossref": 0.8
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 2/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "有開放取用 metadata"
        ],
        "rank_score": 0.7588283433133732,
        "id": "cand-df5646668eef4593",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "Trustworthy LLM-Embedding Clinical Prediction: Calibrating Confidence and Transparency for Foundation Model-Based Disease Risk Scores",
        "authors": [
          "Yunguo Yu"
        ],
        "year": 2026,
        "venue": null,
        "abstract": " Abstract \n                 Objective\n Clinical adoption of AI-driven disease prediction systems is constrained not by discriminative performance but by the absence of principled mechanisms for clinicians to assess prediction reliability and determine when to override model outputs. We developed and evaluated a calibrated composite trust scoring framework that integrates classifier confidence, embedding-space similarity to known positive cases, and objective data-richness transparency into a single score governing transparency-conditioned clinician override decisions for structured electronic health record (EHR) prediction.\nMaterials and Methods\n We evaluated the framework on the MIMIC-III cardiovascular disease cohort (43,125 admissions; 31.5% heart failure prevalence) using inference-only embeddings from three open-weight large language models (LLMs) spanning a 12-fold parameter range (Qwen3-Embedding-0.6B, Qwen2.5-3B, Qwen2.5-7B 4-bit quantized), paired with logistic regression and multilayer perceptron classifiers across three data richness levels (diagnoses only; diagnoses, medications, and procedures; all available structured data). Primary outcomes were AUROC, calibration quality (ECE, Brier score), clinician override rates, net benefit by decision curve analysis, and systematic ablation of each trust component, all evaluated on an independent held-out test set (n = 8,625).\nResults\n The full-precision Qwen2.5-3B model achieved the highest discrimination (AUROC 0.857, 95% CI 0.849–0.865; net benefit 0.120), outperforming the 4-bit quantized 7B model (AUROC 0.854) despite greater parameter count — revealing a quantization-performance tradeoff with direct implications for model selection under GPU memory constraints. The trust framework produced selective override rates contingent on both model capability and data richness (3.57% at moderate richness for the 0.6B model; 0% for larger models under default thresholds). Systematic ablation identified embedding-space similarity as the architecturally critical trust component: its removal increased override rates from 3.57% to 77–81% across all model sizes, while confidence calibration improved ECE (0.007 vs. 0.024) without meaningfully altering override behavior (3.57% vs. 3.49%).\nDiscussion\n Replacing subjective LLM self-assessed transparency with an objective data-richness measure enables reproducible, auditable override governance without generative model infrastructure. The 0% override rates observed for larger models under thresholds calibrated for the 0.6B model establish that model-specific threshold recalibration is a structural deployment requirement, not an optional adjustment.\nConclusion\n A calibrated, transparency-conditioned trust scoring framework augmenting LLM-embedding classifiers achieves discriminative accuracy and principled clinician override governance for structured EHR-based heart failure prediction. Embedding-space similarity is the architecturally dominant trust component, and model-specific threshold calibration is required before clinical deployment. ",
        "doi": "10.21203/rs.3.rs-9728440/v1",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": null,
        "semantic_scholar_id": null,
        "citation_count": 0,
        "open_access": true,
        "landing_url": "https://doi.org/10.21203/rs.3.rs-9728440/v1",
        "oa_url": null,
        "topics": [],
        "providers": [
          "crossref"
        ],
        "provenance": [
          {
            "provider": "crossref",
            "url": "https://api.crossref.org/works?query.bibliographic=LLM+confidence+routing&rows=5&filter=from-pub-date%3A2024-01-01%2Chas-license%3Atrue"
          }
        ],
        "provider_scores": {
          "crossref": 0.19999999999999996
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 2/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "有開放取用 metadata"
        ],
        "rank_score": 0.7197,
        "id": "cand-c0314e0a951fc417",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "Retrieval-augmented generation: a hybrid approach to assessing retrieved documents similarity, LLM confidence, and system stability",
        "authors": [
          "Alexander Plesovskikh"
        ],
        "year": 2025,
        "venue": null,
        "abstract": " Abstract \n                 The retrieval-augmented generation approach relies on retrieving relevant documents to enhance large language model prompts and improve model outputs. However, existing metrics like cosine similarity, precision@k, and recall@k, to name just a few, fail to account for the confidence and stability of retrieval and generation. We propose a novel approach, retrieval confidence score, and its extension, asymptotic retrieval confidence score, which combines semantic similarity, large language model confidence, and stability across multiple generations. Asymptotic retrieval confidence score potentially provides a robust approach for evaluating retrieval-augmented generation systems, possibly suggesting a better solution for combining results across retrieval, generation, and evaluation stages. ",
        "doi": "10.21203/rs.3.rs-6741053/v1",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": null,
        "semantic_scholar_id": null,
        "citation_count": 0,
        "open_access": true,
        "landing_url": "https://doi.org/10.21203/rs.3.rs-6741053/v1",
        "oa_url": null,
        "topics": [],
        "providers": [
          "crossref"
        ],
        "provenance": [
          {
            "provider": "crossref",
            "url": "https://api.crossref.org/works?query.bibliographic=LLM+confidence+routing&rows=5&filter=from-pub-date%3A2024-01-01%2Chas-license%3Atrue"
          }
        ],
        "provider_scores": {
          "crossref": 0.4
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 2/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "有開放取用 metadata"
        ],
        "rank_score": 0.6547653791130186,
        "id": "cand-cf72aac673148894",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "A Survey of Large Language Models",
        "authors": [
          "Wayne Xin Zhao",
          "Kun Zhou",
          "Junyi Li",
          "Tianyi Tang",
          "Xiaolei Wang",
          "Yupeng Hou",
          "Yingqian Min",
          "Beichen Zhang",
          "Junjie Zhang",
          "Zican Dong",
          "Yifan Du",
          "Yang Chen",
          "Yushuo Chen",
          "Zhipeng Chen",
          "Jinhao Jiang",
          "Ruiyang Ren",
          "Yifan Li",
          "Xinyu Tang",
          "Zikang Liu",
          "Peiyu Liu",
          "Jian‐Yun Nie",
          "Ji-Rong Wen",
          "Ji-Rong Wen"
        ],
        "year": 2026,
        "venue": "Frontiers of Computer Science",
        "abstract": "Abstract The rapid evolution of large language models (LLMs) has driven a transformative shift in artificial intelligence (AI), reshaping both research paradigms and practical applications. Distinguished from their predecessors by unprecedented scale and advanced capabilities, LLMs necessitate new frameworks for understanding their development, behavior, and societal impact. This survey systematically reviews recent advancements in LLM techniques across four key dimensions: (1) pre-training methodologies, which establish core model capabilities through large-scale self-supervised training, architectural innovations, and data curation strategies; (2) post-training techniques, including supervised fine-tuning and reinforcement learning, which adapt foundational models to downstream tasks and enhance their alignment and safety; (3) utilization strategies, such as in-context learning, prompt engineering, and agentic reasoning, that optimize real-world deployment and enable effective interaction with external environments; and (4) evaluation methods, encompassing benchmarks for key ability dimensions such as core language capabilities, reasoning, and safety, which support comprehensive and reliable assessment of model performance. Additionally, we identify critical research issues, including those concerning theoretical foundations, efficient scaling, alignment, and agentic capability, and highlight the open challenges they present. By synthesizing state-of-the-art insights and emerging trends, this survey aims to provide a systematic and comprehensive framework for understanding the trajectory, current limitations, and future directions of LLM progress.",
        "doi": "10.1007/s11704-026-60308-3",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": "W4362515116",
        "semantic_scholar_id": null,
        "citation_count": 1418,
        "open_access": true,
        "landing_url": "https://openalex.org/W4362515116",
        "oa_url": "https://link.springer.com/content/pdf/10.1007/s11704-026-60308-3.pdf",
        "topics": [
          "Topic Modeling",
          "Natural Language Processing Techniques"
        ],
        "providers": [
          "openalex"
        ],
        "provenance": [
          {
            "provider": "openalex",
            "url": "https://api.openalex.org/works?search=LLM+confidence+routing&per-page=5&filter=publication_year%3A2024-2026%2Copen_access.is_oa%3Atrue"
          }
        ],
        "provider_scores": {
          "openalex": 0.8
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 1/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "引用訊號 1418 次",
          "有開放取用 metadata"
        ],
        "rank_score": 0.8525017908671184,
        "id": "cand-255389898f37d201",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "Harnessing the Power of LLMs in Practice: A Survey on ChatGPT and Beyond",
        "authors": [
          "Jingfeng Yang",
          "Hongye Jin",
          "Ruixiang Tang",
          "Xiaotian Han",
          "Qizhang Feng",
          "Haoming Jiang",
          "Shaochen Zhong",
          "Bing Yin",
          "Xia Hu"
        ],
        "year": 2024,
        "venue": "ACM Transactions on Knowledge Discovery from Data",
        "abstract": "This article presents a comprehensive and practical guide for practitioners and end-users working with Large Language Models (LLMs) in their downstream Natural Language Processing (NLP) tasks. We provide discussions and insights into the usage of LLMs from the perspectives of models, data, and downstream tasks. First, we offer an introduction and brief summary of current language models. Then, we discuss the influence of pre-training data, training data, and test data. Most importantly, we provide a detailed discussion about the use and non-use cases of large language models for various natural language processing tasks, such as knowledge-intensive tasks, traditional natural language understanding tasks, generation tasks, emergent abilities, and considerations for specific tasks. We present various use cases and non-use cases to illustrate the practical applications and limitations of LLMs in real-world scenarios. We also try to understand the importance of data and the specific challenges associated with each NLP task. Furthermore, we explore the impact of spurious biases on LLMs and delve into other essential considerations, such as efficiency, cost, and latency, to ensure a comprehensive understanding of deploying LLMs in practice. This comprehensive guide aims to provide researchers and practitioners with valuable insights and best practices for working with LLMs, thereby enabling the successful implementation of these models in a wide range of NLP tasks. A curated list of practical guide resources of LLMs, regularly updated, can be found at https://github.com/Mooler0410/LLMsPracticalGuide . An LLMs evolutionary tree, editable yet regularly updated, can be found at llmtree.ai .",
        "doi": "10.1145/3649506",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": "W4392240262",
        "semantic_scholar_id": null,
        "citation_count": 462,
        "open_access": true,
        "landing_url": "https://openalex.org/W4392240262",
        "oa_url": "https://dl.acm.org/doi/pdf/10.1145/3649506",
        "topics": [
          "Artificial Intelligence in Healthcare and Education",
          "Topic Modeling",
          "Privacy-Preserving Technologies in Data"
        ],
        "providers": [
          "openalex"
        ],
        "provenance": [
          {
            "provider": "openalex",
            "url": "https://api.openalex.org/works?search=LLM+confidence+routing&per-page=5&filter=publication_year%3A2024-2026%2Copen_access.is_oa%3Atrue"
          }
        ],
        "provider_scores": {
          "openalex": 1.0
        },
        "relation": "search",
        "ranking_explanation": [
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "引用訊號 462 次",
          "有開放取用 metadata"
        ],
        "rank_score": 0.6995260588569322,
        "id": "cand-a8558c9765ed27fe",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge",
        "authors": [
          "Da-Wei Li",
          "Bohan Jiang",
          "Lili Huang",
          "Alimohammad Beigi",
          "Chengshuai Zhao",
          "Zhen Tan",
          "Amrita Bhattacharjee",
          "Yuxuan Jiang",
          "Canyu Chen",
          "Tianhao Wu",
          "Kan Shu",
          "Lu Cheng",
          "H.L. Liu"
        ],
        "year": 2025,
        "venue": null,
        "abstract": "Dawei Li, Bohan Jiang, Liangjie Huang, Alimohammad Beigi, Chengshuai Zhao, Zhen Tan, Amrita Bhattacharjee, Yuxuan Jiang, Canyu Chen, Tianhao Wu, Kai Shu, Lu Cheng, Huan Liu. Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing. 2025.",
        "doi": "10.18653/v1/2025.emnlp-main.138",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": "W4416037109",
        "semantic_scholar_id": null,
        "citation_count": 65,
        "open_access": true,
        "landing_url": "https://openalex.org/W4416037109",
        "oa_url": "https://aclanthology.org/2025.emnlp-main.138.pdf",
        "topics": [
          "Computational and Text Analysis Methods",
          "Topic Modeling",
          "Artificial Intelligence in Healthcare and Education"
        ],
        "providers": [
          "openalex"
        ],
        "provenance": [
          {
            "provider": "openalex",
            "url": "https://api.openalex.org/works?search=LLM+confidence+routing&per-page=5&filter=publication_year%3A2024-2026%2Copen_access.is_oa%3Atrue"
          }
        ],
        "provider_scores": {
          "openalex": 0.4
        },
        "relation": "search",
        "ranking_explanation": [
          "查詢詞命中 1/3",
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "引用訊號 65 次",
          "有開放取用 metadata"
        ],
        "rank_score": 0.5707531686721422,
        "id": "cand-fcd6bf1bc61502ec",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "How Johnny Can Persuade LLMs to Jailbreak Them: Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs",
        "authors": [
          "Yi Zeng",
          "Hongpeng Lin",
          "Jingwen Zhang",
          "Diyi Yang",
          "Ruoxi Jia",
          "Weiyan Shi"
        ],
        "year": 2024,
        "venue": null,
        "abstract": null,
        "doi": "10.18653/v1/2024.acl-long.773",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": "W4402671039",
        "semantic_scholar_id": null,
        "citation_count": 72,
        "open_access": true,
        "landing_url": "https://openalex.org/W4402671039",
        "oa_url": "https://aclanthology.org/2024.acl-long.773.pdf",
        "topics": [
          "Law, AI, and Intellectual Property",
          "Artificial Intelligence in Law",
          "Ethics and Social Impacts of AI"
        ],
        "providers": [
          "openalex"
        ],
        "provenance": [
          {
            "provider": "openalex",
            "url": "https://api.openalex.org/works?search=LLM+confidence+routing&per-page=5&filter=publication_year%3A2024-2026%2Copen_access.is_oa%3Atrue"
          }
        ],
        "provider_scores": {
          "openalex": 0.6
        },
        "relation": "search",
        "ranking_explanation": [
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "引用訊號 72 次",
          "有開放取用 metadata"
        ],
        "rank_score": 0.36615700886252045,
        "id": "cand-2eb831a114990c30",
        "state": "candidate",
        "imported_paper_id": null
      },
      {
        "title": "Data Augmentation using LLMs: Data Perspectives, Learning Paradigms and Challenges",
        "authors": [
          "Bosheng Ding",
          "Chengwei Qin",
          "Ruochen Zhao",
          "Tianze Luo",
          "Xinze Li",
          "Guizhen Chen",
          "Wenhan Xia",
          "Junjie Hu",
          "Anh Tuan Luu",
          "Shafiq Joty"
        ],
        "year": 2024,
        "venue": null,
        "abstract": "Bosheng Ding, Chengwei Qin, Ruochen Zhao, Tianze Luo, Xinze Li, Guizhen Chen, Wenhan Xia, Junjie Hu, Anh Tuan Luu, Shafiq Joty. Findings of the Association for Computational Linguistics: ACL 2024. 2024.",
        "doi": "10.18653/v1/2024.findings-acl.97",
        "arxiv_id": null,
        "acl_id": null,
        "openalex_id": "W4402670893",
        "semantic_scholar_id": null,
        "citation_count": 79,
        "open_access": true,
        "landing_url": "https://openalex.org/W4402670893",
        "oa_url": "https://aclanthology.org/2024.findings-acl.97.pdf",
        "topics": [
          "Semantic Web and Ontologies"
        ],
        "providers": [
          "openalex"
        ],
        "provenance": [
          {
            "provider": "openalex",
            "url": "https://api.openalex.org/works?search=LLM+confidence+routing&per-page=5&filter=publication_year%3A2024-2026%2Copen_access.is_oa%3Atrue"
          }
        ],
        "provider_scores": {
          "openalex": 0.19999999999999996
        },
        "relation": "search",
        "ranking_explanation": [
          "供應者提供相關性排序",
          "貼近教授研究主題",
          "近兩年發表",
          "引用訊號 79 次",
          "有開放取用 metadata"
        ],
        "rank_score": 0.3161444483715087,
        "id": "cand-524487fe665b4eb0",
        "state": "candidate",
        "imported_paper_id": null
      }
    ],
    "runs": [
      {
        "query": "LLM confidence routing",
        "filters": {
          "year_from": 2024,
          "year_to": null,
          "author": null,
          "venue": null,
          "topic": null,
          "open_access": true,
          "citation_min": null,
          "providers": []
        },
        "candidate_ids": [
          "cand-255389898f37d201",
          "cand-94a62693f8ece46d",
          "cand-b9aba89c269bccd7",
          "cand-df5646668eef4593",
          "cand-c0314e0a951fc417",
          "cand-a8558c9765ed27fe",
          "cand-cf72aac673148894",
          "cand-fcd6bf1bc61502ec",
          "cand-2eb831a114990c30",
          "cand-524487fe665b4eb0"
        ],
        "failures": {
          "semantic-scholar": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>"
        },
        "created_at": "2026-07-13T01:49:32+00:00"
      },
      {
        "query": "LLM confidence routing",
        "filters": {
          "year_from": 2024,
          "year_to": null,
          "author": null,
          "venue": null,
          "topic": null,
          "open_access": true,
          "citation_min": null,
          "providers": []
        },
        "candidate_ids": [
          "cand-94a62693f8ece46d",
          "cand-b9aba89c269bccd7",
          "cand-df5646668eef4593",
          "cand-c0314e0a951fc417",
          "cand-cf72aac673148894"
        ],
        "failures": {
          "openalex": "'NoneType' object has no attribute 'get'",
          "semantic-scholar": "HTTP Error 429: "
        },
        "created_at": "2026-07-13T01:49:03+00:00"
      },
      {
        "query": "LLM confidence routing",
        "filters": {
          "year_from": 2024,
          "year_to": null,
          "author": null,
          "venue": null,
          "topic": null,
          "open_access": true,
          "citation_min": null,
          "providers": []
        },
        "candidate_ids": [],
        "failures": {
          "openalex": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>",
          "semantic-scholar": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>",
          "crossref": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>",
          "arxiv": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>",
          "acl-anthology": "<urlopen error [WinError 10013] 嘗試存取通訊端被拒絕，因為存取權限不足。>"
        },
        "created_at": "2026-07-13T01:48:48+00:00"
      }
    ]
  }
};
