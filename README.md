# Research OS

Research OS is a local, deterministic research repository for professor and lab pages. The first vertical slice is configured for An-Zi Yen and the NYCU NLP Lab. It is corpus infrastructure, not a runtime AI-agent product.

## Quick start

```bash
uv sync
uv run research-os bootstrap --professor-url https://azyen0522.github.io/ --seed-file "NYCU NLP Lab Intro.pdf"
uv run research-os papers an-zi-yen
uv run research-os search "fact-checking"
uv run research-os report an-zi-yen
```

Bootstrap follows a bounded (default depth-one, maximum 12-page) set of
same-host links whose path or anchor text signals profile, lab, project,
research, paper, or publication content. Every followed edge and fetched HTML
snapshot is recorded in SQLite. For a strictly offline parser run, disable the
follow-up crawl and use the checked-in fixture:

```bash
uv run research-os bootstrap --professor-url https://azyen0522.github.io/ --source-file data/an-zi-yen-live.html --crawl-depth 0 --seed-file "NYCU NLP Lab Intro.pdf"
```

The SQLite database lives at `.research-os/research.db`. HTML snapshots, PDFs, and the supplied seed are SHA-256 hashed and retained with source URLs. PyMuPDF extracts page-level text, image counts, detected tables, and section anchors to `extraction.json`. Papers with no verified full text remain `unresolved` rather than being presented as fetched.

The current resolver handles direct arXiv routes and project-page identifier hints. Optional layout-preserving translation is isolated behind the BabelDOC CLI because BabelDOC is AGPL-3.0; no translation service or credentials are bundled or required for the core pipeline. Create a local BabelDOC TOML from its documented configuration, keep its credentials outside this repository, then opt in for a fetched paper:

```bash
uv run research-os translate <paper-id> --config path/to/local-babeldoc.toml
```

The TOML controls BabelDOC's output directory and language pair. Research OS leaves `source.pdf` untouched and writes only a credential-free `translation.json` command/provenance record beside it.
