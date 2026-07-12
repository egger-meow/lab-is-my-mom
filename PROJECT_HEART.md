# Professor Research OS

## Mission

Build a scalable local research repository that accepts a professor or lab webpage and produces a verified, readable research corpus.

```text
professor URL
→ crawl profile/lab/publication pages
→ identify professor-authored papers
→ resolve metadata and fetch legal full text
→ extract/translate papers
→ generate compact reading docs and diagrams
→ maintain a searchable research map
```

This is **not a runtime AI-agent product for now**. The shipped system should be deterministic crawling, storage, parsing, search, and viewing infrastructure.

Codex/Claude Code should use its own reasoning **during the build** to digest the currently fetchable papers and commit the initial study material for future reading.

## Generic product, customized first run

The architecture must support almost any professor webpage:

```bash
research-os bootstrap \
  --professor-url <URL> \
  --seed-file <optional PDF/slide/doc>
```

The first real bootstrap is customized for:

- `https://azyen0522.github.io/`
- provided `NYCU NLP Lab Intro.pdf`

Use the PDF as extra ground truth for research directions and paper context, but keep professor-specific hints in config, not hardcoded domain logic.

## Required pipeline

### 1. Professor discovery

Given a professor/lab URL:

- crawl same-site profile, lab, project, and publication pages;
- detect names, aliases, affiliations, ORCID/Scholar links;
- collect titles, authors, venues, years, DOI/arXiv IDs, PDF/code/data links;
- distinguish authored papers from merely cited or recommended papers;
- follow relevant scholarly links with bounded depth;
- preserve URL, timestamp, content hash, and extraction evidence.

Use adapters so new professors do not require crawler rewrites.

### 2. Paper resolution and fetching

Resolve and deduplicate through DOI/Crossref, arXiv, ACL Anthology, OpenAlex, Semantic Scholar, conference/publisher pages, and professor-hosted PDFs.

Never invent papers or citations. Record unresolved, inaccessible, and paywalled items explicitly.

### 3. Document processing

For each fetched paper:

- preserve the original PDF;
- extract sections, references, figures, tables, and captions;
- optionally create Traditional Chinese or bilingual reading copies;
- preserve page-level anchors for evidence links;
- record parser versions, configuration, and failures.

### 4. Build-time paper digestion

For every currently fetchable professor-authored paper, the building agent must read the full text and commit compact support docs:

```text
research/papers/<paper-id>/
├── metadata.yaml
├── source.pdf
├── README.md
├── method.md
├── experiments-and-results.md
├── limitations-and-critique.md
├── prerequisites.md
├── seminar-questions.md
└── diagrams/
    ├── method.mmd
    └── research-context.mmd
```

Keep them useful, not encyclopedic. Clearly separate:

- paper claim,
- observed result,
- author limitation,
- builder interpretation,
- unresolved question.

### 5. Professor research map

Generate:

```text
research/professor/<professor-id>/
├── profile.md
├── publication-index.md
├── research-directions.md
├── research-timeline.md
├── method-map.md
├── dataset-map.md
├── reading-order.md
└── open-questions.md
```

Connect papers through topics, methods, datasets, metrics, citations, recurring limitations, and later extensions.

### 6. Local usage

Start with CLI and files:

```bash
research-os bootstrap --professor-url <URL>
research-os refresh <professor-id>
research-os papers <professor-id>
research-os fetch <paper-id>
research-os search "<query>"
research-os report <professor-id>
```

Build a web UI only after the corpus pipeline works.

## Reuse these projects

### BabelDOC

`https://github.com/funstory-ai/BabelDOC`

Use it as an optional adapter for layout-preserving PDF translation/processing.

- isolate behind `DocumentProcessor` / `Translator` interfaces;
- prefer its supported wrapper/entry path, not unstable internal APIs;
- support subprocess or separate-service execution;
- preserve the untouched original PDF;
- keep the core pipeline functional without it;
- test formulas, tables, figures, references, and scanned PDFs;
- review AGPL-3.0 implications before distributing a combined service.

### Deep-Research-Agent

`https://github.com/CYC2002tommy/Deep-Research-Agent`

Use it as a **build-time reference/skill**, not a runtime dependency.

Borrow:

- broad discovery followed by full-text screening;
- OpenAlex/Semantic Scholar/Scopus-style provider adapters;
- DOI resolution checks;
- full-text verification before writing claims;
- separate extraction, synthesis, verification, and review stages;
- structured research-report outputs.

Do not copy rigid assumptions such as fixed paper counts, journal bans, English-only output, hardcoded folders, NotebookLM, or mandatory multi-agent execution. This project must fit computer-science conference research and remain configurable.

## Minimal implementation shape

```text
src/
├── cli/
├── config/
├── domain/
├── crawling/
├── scholarly/
├── documents/
├── extraction/
├── indexing/
├── reports/
└── providers/
```

Recommended baseline:

- Python 3.12+, `uv`
- Typer/Click, Pydantic
- SQLite
- PyMuPDF
- BeautifulSoup, Playwright only when required
- Markdown and Mermaid outputs
- optional FastAPI later

Keep external services behind interfaces. Do not add PostgreSQL, vectors, queues, or a frontend until actual usage requires them.

Important distinctions:

```text
webpage mention ≠ authored paper
paper metadata ≠ downloaded full text
paper statement ≠ builder interpretation
reported result ≠ reproduced result
```

Everything must retain provenance.

## First milestone

Deliver one end-to-end vertical slice:

1. initialize repo and SQLite;
2. import the provided NYCU lab PDF;
3. crawl Prof. An-Zi Yen's webpage;
4. build a verified profile and publication index;
5. fetch every legally accessible authored paper found;
6. process PDFs and optionally create bilingual copies with BabelDOC;
7. have the building agent digest those papers;
8. commit per-paper study docs and Mermaid diagrams;
9. commit timeline, method map, and reading order;
10. write `reports/bootstrap-an-zi-yen.md` with conflicts, missing PDFs, and failures.

## Done when

- a clean clone reproduces the crawl and index;
- authored papers are separated from unrelated links;
- metadata is deduplicated and source-backed;
- PDFs have hashes and provenance;
- unavailable papers and failures remain visible;
- each fetched paper has compact reading-support docs;
- diagrams link back to paper sections/pages;
- the research map reflects the supplied lab PDF;
- no runtime AI-agent dependency exists;
- tests cover crawling, deduplication, provenance, and one full paper path.

## Builder instruction

Inspect the two referenced repositories and supplied professor material first. Then build the smallest real vertical slice, reuse proven components behind adapters, generate the initial corpus during this build, verify important claims against full text, run one real bootstrap plus tests, record exact failures, and commit each coherent unit.

Do not burn tokens on speculative enterprise architecture. Make the corpus useful.
