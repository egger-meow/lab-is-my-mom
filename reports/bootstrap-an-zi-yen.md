# Bootstrap report - An-Zi Yen

## Run evidence

- Professor page: `https://azyen0522.github.io/`; its snapshot is `.research-os/snapshots/professor.html`. The bounded same-site crawl also archived the relevant `member.html` and `projects.html` pages. URLs, fetch timestamps, hashes, and followed crawl edges are stored in `.research-os/research.db`.
- Seed: the untouched `NYCU NLP Lab Intro.pdf` is preserved at `research/seeds/NYCU NLP Lab Intro.pdf` and hashed in the database.
- Authorship rule: a publication-list entry must match a configured author alias. Project descriptions and unrelated mentions are excluded.

## Result

The July 13, 2026 crawl found 39 authored publication-list entries. Identifier-based deduplication merges the ISSR preprint and later conference-title entry, producing 38 canonical works. Thirteen full texts have source-backed public PDF routes and were fetched, hashed, extracted, and digested:

1. E-QGen - arXiv:2404.13547; 4 pages.
2. How We Refute Claims / RefuteClaim - arXiv:2401.15312; 4 pages.
3. ISSR - arXiv:2501.03462; 42 pages.
4. Paraphrase-Aligned Machine Translation - arXiv:2412.05916; 5 pages.
5. MathEDU: Feedback Generation on Problem-Solving Processes for Mathematical Learning Support - ACL Anthology 2026.eacl-long.132; 19 pages.
6. Visual Lifelog Retrieval through Captioning-Enhanced Interpretation - arXiv:2510.04010; 9 pages.
7. LED: A Dataset for Life Event Extraction from Dialogs - ACL Anthology 2023.findings-eacl.29; 15 pages.
8. RSVP: Customer Intent Detection via Agent Response Contrastive and Generative Pre-Training - ACL Anthology 2023.findings-emnlp.698 / arXiv:2310.09773; 13 pages.
9. Three Questions Concerning the Use of Large Language Models to Facilitate Mathematics Learning - ACL Anthology 2023.findings-emnlp.201; 15 pages.
10. ZARA: Improving Few-Shot Self-Rationalization for Small Language Models - ACL Anthology 2023.findings-emnlp.310 / arXiv:2305.07355; 12 pages.
11. SEEN: Structured Event Enhancement Network for Explainable Need Detection of Information Recall Assistance - ACL Anthology 2022.emnlp-main.365; 14 pages.
12. Ten Questions in Lifelog Mining and Information Recall - arXiv:2005.01535; 7 pages.
13. Unanswerable Question Correction in Question Answering over Personal Knowledge Base - AAAI 2021; 10 pages.

Each fetched paper has its PDF, extraction JSON, study notes, and Mermaid diagrams under `research/papers/<paper-id>/`. Every extraction records sorted text blocks with page-coordinate anchors plus detected figures, table data/captions, and reference text; reported results are explicitly marked as reported, not reproduced.

## Visible unresolved and unavailable records

The remaining 25 canonical works retain `fulltext_status = unresolved`. The current pipeline records high-confidence Crossref/OpenAlex metadata, direct arXiv routes, ACL PDF locations, AAAI PDFs, and project-page identifier hints. A bounded OpenAlex pass is now exhausted for all unresolved records: each has either an OpenAlex resolution or a recorded conservative title-match failure, so rerunning the command does not silently retry the same cases. Metadata-only records are not presented as downloaded or digested.

The OpenAlex-discovered ACM PDF route for *RAG-Enhanced Evidence Recommendation in Financial Legal Resolutions* was attempted but did not return a PDF to the fetcher; its fetch failure is stored in SQLite. Four titles also had no source candidate above the conservative 0.84 title-similarity threshold: *Follow-up Question Modeling for Open-Retrieval Conversations with Wh-Questions*, *Personalized Graph-Empowered Large Language Model for Proactive Information Access*, *Opportunities and challenges of explainable artificial intelligence in medicine*, and *Learning to Generate Explanation from e-Hospital Services for Medical Suggestion*.

## Reproducibility

```text
uv sync
uv run research-os bootstrap --professor-url https://azyen0522.github.io/ --seed-file "NYCU NLP Lab Intro.pdf"
uv run research-os papers an-zi-yen
uv run research-os resolve an-zi-yen --fulltext
uv run research-os fetch <paper-id>
uv run research-os process <paper-id>
```

SQLite artifact paths and checked-in extraction payloads are repository-relative, so a fresh clone does not inherit this machine's filesystem locations.

On July 13, 2026, a fresh local Git clone was verified with the checked-in fixture (`--source-file data/an-zi-yen-live.html --crawl-depth 0`): bootstrap recovered 39 raw entries and 38 canonical works, all 13 fetched artifacts resolved within the clone, no stored path was absolute, and the test suite passed (11 tests).
