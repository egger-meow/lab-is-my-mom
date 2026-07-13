from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

from .core import Link, Publication, Store, fetch_url, normalize_title, parse_publications, relevant_same_site_links, sha256_bytes, utc_now
from .discovery import Candidate, DiscoveryFilters, Federation, rank_candidates, deduplicate
from .providers import AclAnthologyProvider, ArxivProvider, CrossrefProvider, OpenAlexProvider, SemanticScholarProvider
from .translation import BabelDocTranslator, TranslationUnavailable


def load_config(root: Path, professor_id: str | None = None) -> dict:
    configs = sorted((root / "config" / "professors").glob("*.toml"))
    for path in configs:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
        if professor_id is None or config["id"] == professor_id:
            return config
    raise SystemExit(f"no professor config found for {professor_id or 'bootstrap'}")


def snapshot(root: Path, name: str, data: bytes) -> Path:
    destination = root / ".research-os" / "snapshots" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def crawl_same_site(root: Path, store: Store, start_url: str, initial_data: bytes, initial_content_type: str,
                    max_depth: int = 1, max_pages: int = 12) -> list[Publication]:
    """Crawl a small, auditable set of relevant same-site HTML pages."""
    pages: list[tuple[str, bytes, str, int]] = [(start_url, initial_data, initial_content_type, 0)]
    visited: set[str] = set()
    publications: list[Publication] = []
    config = load_config(root)
    while pages and len(visited) < max_pages:
        page_url, data, content_type, depth = pages.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        filename = "professor.html" if depth == 0 else f"page-{hashlib.sha256(page_url.encode()).hexdigest()[:12]}.html"
        local = snapshot(root, filename, data)
        store.record_source(page_url, data, content_type=content_type, local_path=local)
        text = data.decode("utf-8", "replace")
        publications.extend(parse_publications(text, page_url, config["aliases"]))
        if depth >= max_depth or content_type not in {"text/html", "application/xhtml+xml"}:
            continue
        for target in relevant_same_site_links(text, page_url):
            if target in visited or any(queued[0] == target for queued in pages) or len(visited) + len(pages) >= max_pages:
                continue
            store.record_crawl_edge(page_url, target, depth + 1)
            try:
                child_data, final_url, child_type = fetch_url(target)
                pages.append((final_url, child_data, child_type, depth + 1))
            except Exception as error:
                store.record_source(target, b"", content_type="text/html", local_path=None, status="failed", error=str(error))
                store.record_failure("crawl", target, str(error))
    return publications


def import_seed(root: Path, seed_file: str | None) -> Path | None:
    if not seed_file:
        return None
    source = Path(seed_file)
    if not source.is_absolute():
        source = root / source
    if not source.exists():
        return None
    destination = root / "research" / "seeds" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def bootstrap(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root)
    store = Store(root)
    store.upsert_professor(config["id"], config["name"], args.professor_url, config["affiliation"], config["aliases"])
    seed = import_seed(root, args.seed_file or config.get("seed_file"))
    if seed:
        data = seed.read_bytes()
        store.record_source(f"file:{seed.name}", data, content_type="application/pdf", local_path=seed)
    try:
        if args.source_file:
            data = Path(args.source_file).read_bytes()
            final_url, content_type = args.professor_url, "text/html"
        else:
            data, final_url, content_type = fetch_url(args.professor_url)
        publications = crawl_same_site(root, store, final_url, data, content_type,
                                       max_depth=getattr(args, "crawl_depth", 1))
        store.upsert_papers(publications)
        store.apply_paper_hints(config.get("paper_hints", []))
        store.deduplicate_by_identifier()
    except Exception as error:
        store.record_source(args.professor_url, b"", content_type="text/html", local_path=None, status="failed", error=str(error))
        store.record_failure("crawl", args.professor_url, str(error))
        publications = []
    write_research_map(root, store, config, seed)
    print(json.dumps({"professor": config["id"], "publications": len(publications), "database": str(store.db_path)}, ensure_ascii=False))
    store.close()
    return 0


def candidate_pdf_urls(row) -> list[str]:
    urls: list[str] = []
    if row["arxiv_id"]:
        urls.append(f"https://arxiv.org/pdf/{row['arxiv_id']}")
    return urls


def fetch_paper(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    store = Store(root)
    row = store.paper(args.paper_id)
    if not row:
        raise SystemExit(f"unknown paper id: {args.paper_id}")
    urls = candidate_pdf_urls(row)
    urls.extend(link[0] for link in store.db.execute("SELECT url FROM paper_links WHERE paper_id=? AND kind='pdf'", (row["id"],)).fetchall())
    if not urls:
        store.record_failure("resolve", row["id"], "No legal full-text URL was found in the source-backed metadata.")
        print(f"{row['id']}: unresolved (no direct legal PDF URL)")
        store.close()
        return 1
    for url in urls:
        try:
            data, final_url, content_type = fetch_url(url)
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"expected PDF, received {content_type}")
            paper_dir = root / "research" / "papers" / row["id"]
            paper_dir.mkdir(parents=True, exist_ok=True)
            path = paper_dir / "source.pdf"
            path.write_bytes(data)
            store.record_source(final_url, data, content_type=content_type, local_path=path)
            store.update_pdf(row["id"], path, data)
            config = load_config(root)
            write_research_map(root, store, config, root / "research" / "seeds" / Path(config["seed_file"]).name)
            print(f"{row['id']}: fetched {path}")
            store.close()
            return 0
        except Exception as error:
            store.record_failure("fetch", url, str(error))
    print(f"{row['id']}: unavailable")
    store.close()
    return 1


def process_pdf(path: Path) -> dict:
    import pymupdf

    document = pymupdf.open(path)
    pages = []
    figures = []
    extracted_tables = []
    references = []
    in_references = False
    for index, page in enumerate(document):
        blocks = page.get_text("blocks", sort=True)
        text_blocks = [block for block in blocks if block[6] == 0 and block[4].strip()]
        text = "\n".join(block[4].strip() for block in text_blocks)
        anchored_blocks = [{"bbox": [round(value, 2) for value in block[:4]], "text": block[4].strip(), "number": block[5]}
                           for block in text_blocks]
        figure_captions = [line.strip() for line in text.splitlines() if re.match(r"^(?:figure|fig\.)\s*\d+\b", line.strip(), re.I)]
        table_captions = [line.strip() for line in text.splitlines() if re.match(r"^table\s*\d+\b", line.strip(), re.I)]
        figures.extend({"page": index + 1, "caption": caption} for caption in figure_captions)
        tables = []
        try:
            tables = [table.extract() for table in page.find_tables().tables]
        except Exception:
            pass
        extracted_tables.extend({"page": index + 1, "index": number + 1,
                                 "caption": table_captions[number] if number < len(table_captions) else None,
                                 "rows": table}
                                for number, table in enumerate(tables))
        for block in anchored_blocks:
            for line in (line.strip() for line in block["text"].splitlines() if line.strip()):
                if re.match(r"^references\b", line, re.I):
                    in_references = True
                    continue
                if in_references:
                    references.append({"page": index + 1, "bbox": block["bbox"], "text": line})
        image_count = sum(1 for block in page.get_text("dict")["blocks"] if block["type"] == 1)
        pages.append({"page": index + 1, "text": text, "blocks": anchored_blocks, "images": image_count,
                      "figure_captions": figure_captions, "table_captions": table_captions, "tables": tables})
    return {"source": str(path), "sha256": sha256_bytes(path.read_bytes()), "page_count": len(document),
            "parser_version": getattr(pymupdf, "VersionBind", "unknown"),
            "config": {"text": "blocks-sort-with-bbox", "tables": "find_tables", "captions": "regex-v1"},
            "pages": pages, "figures": figures, "tables": extracted_tables, "references": references}


def infer_sections(pages: list[dict]) -> list[dict]:
    headings = re_compile = __import__("re").compile(r"^(?:[0-9]+(?:\.[0-9]+)*\s+)?(?:abstract|introduction|related work|method|approach|experiment|results|conclusion|limitations|references)\b", __import__("re").I)
    result = []
    for page in pages:
        for line in page["text"].splitlines():
            if headings.match(line.strip()):
                result.append({"heading": line.strip(), "page": page["page"]})
    return result


def process_paper(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); store = Store(root); row = store.paper(args.paper_id)
    if not row or not row["pdf_path"]:
        raise SystemExit("paper has no fetched PDF; run fetch first")
    try:
        source_path = store.resolve_path(row["pdf_path"])
        payload = process_pdf(source_path)
        payload["source"] = store.relative_path(source_path)
        payload["sections"] = infer_sections(payload["pages"])
        output = source_path.parent / "extraction.json"
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        store.record_document(row["id"], source_path, payload, output)
        write_paper_scaffold(root, row, payload)
        config = load_config(root)
        write_research_map(root, store, config, root / "research" / "seeds" / Path(config["seed_file"]).name)
        print(f"{row['id']}: processed {payload['page_count']} pages")
        return 0
    except Exception as error:
        store.record_failure("process", row["id"], str(error)); raise
    finally:
        store.close()


def translate_paper(args: argparse.Namespace) -> int:
    """Optionally create a BabelDOC output while preserving the source PDF."""
    root = Path(args.root).resolve()
    store = Store(root)
    row = store.paper(args.paper_id)
    if not row or not row["pdf_path"]:
        store.close()
        raise SystemExit("paper has no fetched PDF; run fetch first")
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    translator = BabelDocTranslator(args.executable)
    try:
        source_path = store.resolve_path(row["pdf_path"])
        result = translator.translate(source_path, config_path, timeout=args.timeout)
    except (TranslationUnavailable, ValueError) as error:
        store.record_failure("translate", row["id"], str(error))
        store.close()
        print(f"{row['id']}: BabelDOC unavailable ({error})")
        return 1
    provenance = {
        "engine": "BabelDOC CLI",
        "source_pdf": row["pdf_path"],
        "source_sha256": row["pdf_sha256"],
        "config_sha256": sha256_bytes(config_path.read_bytes()),
        "command": list(result.command),
        "return_code": result.return_code,
        "output_note": "BabelDOC output is controlled by the caller-provided TOML config; config contents are intentionally not stored.",
    }
    output = store.resolve_path(row["pdf_path"]).parent / "translation.json"
    output.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result.return_code:
        store.record_failure("translate", row["id"], result.stderr[-1000:] or "BabelDOC returned a non-zero status")
        store.close()
        print(f"{row['id']}: BabelDOC failed (exit {result.return_code})")
        return 1
    store.close()
    print(f"{row['id']}: BabelDOC completed; provenance at {output}")
    return 0


def page_anchor(payload: dict, heading: str) -> str:
    for section in payload.get("sections", []):
        if heading.lower() in section["heading"].lower():
            return f"p. {section['page']}"
    return "page anchor pending"


def write_paper_scaffold(root: Path, row, payload: dict) -> None:
    paper_dir = root / "research" / "papers" / row["id"]; diagrams = paper_dir / "diagrams"; diagrams.mkdir(parents=True, exist_ok=True)
    metadata = {key: row[key] for key in ("id", "title", "authors", "year", "venue", "arxiv_id", "doi", "source_url", "pdf_sha256")}
    (paper_dir / "metadata.yaml").write_text("\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()) + "\n", encoding="utf-8")
    write_if_absent(paper_dir / "README.md", f"# {row['title']}\n\n- **Status:** full text fetched and extracted ({payload['page_count']} pages).\n- **Metadata source:** {row['source_url']}\n- **Full text:** arXiv {row['arxiv_id'] or 'not applicable'}; SHA-256 `{row['pdf_sha256']}`.\n- **Evidence anchors:** Abstract {page_anchor(payload, 'abstract')}; method {page_anchor(payload, 'method')}; results {page_anchor(payload, 'result')}.\n\nThe companion notes distinguish paper claims from builder interpretation and unresolved questions.\n")
    placeholders = {
        "method.md": "# Method\n\nPopulate from the extracted full text. Cite page anchors for every paper claim.\n",
        "experiments-and-results.md": "# Experiments and results\n\nPopulate reported setup, metrics, and results from the full text; do not label them reproduced.\n",
        "limitations-and-critique.md": "# Limitations and critique\n\nSeparate author-stated limitations from builder interpretation.\n",
        "prerequisites.md": "# Prerequisites\n\nList only concepts needed to read this paper.\n",
        "seminar-questions.md": "# Seminar questions\n\n1. Which result is most sensitive to the evaluation design?\n",
    }
    for name, text in placeholders.items():
        target = paper_dir / name
        if not target.exists(): target.write_text(text, encoding="utf-8")
    write_if_absent(diagrams / "method.mmd", "flowchart LR\n  Input[Input] --> Method[Method from full text]\n  Method --> Output[Output]\n")
    write_if_absent(diagrams / "research-context.mmd", "flowchart LR\n  Lab[NYCU NLP Lab] --> Paper[This paper]\n  Paper --> Theme[Research direction]\n")


def write_if_absent(path: Path, text: str) -> None:
    """Keep curated research-map notes intact during routine refreshes."""
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def write_research_map(root: Path, store: Store, config: dict, seed: Path | None) -> None:
    base = root / "research" / "professor" / config["id"]; base.mkdir(parents=True, exist_ok=True)
    papers = store.papers()
    (base / "profile.md").write_text(f"# {config['name']}\n\n- **Affiliation:** {config['affiliation']}\n- **Lab URL:** {config['professor_url']}\n- **Aliases used for authorship:** {', '.join(config['aliases'])}\n- **Evidence:** `.research-os/snapshots/professor.html` (hash recorded in SQLite).\n", encoding="utf-8")
    lines = ["# Publication index", "", "Only entries whose author string matches a configured alias are included.", "", "| Year | Title | Status | IDs | Source evidence |", "|---:|---|---|---|---|"]
    for paper in papers:
        identifiers = ", ".join(v for v in (f"arXiv:{paper['arxiv_id']}" if paper['arxiv_id'] else None, f"doi:{paper['doi']}" if paper['doi'] else None) if v) or "—"
        lines.append(f"| {paper['year'] or '—'} | {paper['title']} | {paper['fulltext_status']} | {identifiers} | {paper['source_url']} |")
    (base / "publication-index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    seed_note = f"The supplied deck is preserved at `{seed.relative_to(root)}`." if seed else "The configured seed file was not found."
    write_if_absent(base / "research-directions.md", f"# Research directions\n\n1. Question generation and answering.\n2. Human-centered AI.\n3. NLP for social good.\n\n{seed_note}\n")
    write_if_absent(base / "research-timeline.md", "# Research timeline\n\n- 2017-2021: lifelog mining and information recall.\n- 2022-2023: explanation, citation evidence, and education-oriented LLM work.\n- 2024-2026: fact checking, question generation, proactive access, and cost-aware NLU.\n")
    write_if_absent(base / "method-map.md", "# Method map\n\nCurated after full-text processing.\n")
    write_if_absent(base / "dataset-map.md", "# Dataset map\n\nCurated after full-text processing.\n")
    write_if_absent(base / "reading-order.md", "# Reading order\n\nCurated after full-text processing.\n")
    write_if_absent(base / "open-questions.md", "# Open questions\n\nCurated after full-text processing.\n")


def list_papers(args: argparse.Namespace) -> int:
    store = Store(Path(args.root).resolve())
    for row in store.papers(): print(f"{row['id']}\t{row['year'] or '—'}\t{row['fulltext_status']}\t{row['title']}")
    store.close(); return 0


def search(args: argparse.Namespace) -> int:
    store = Store(Path(args.root).resolve())
    for row in store.search(args.query): print(f"{row['id']}\t{row['year'] or '—'}\t{row['title']}")
    store.close(); return 0


def refresh(args: argparse.Namespace) -> int:
    config = load_config(Path(args.root).resolve(), args.professor_id)
    args.professor_url = config["professor_url"]; args.seed_file = None; args.source_file = None; args.crawl_depth = 1
    return bootstrap(args)


def resolve(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve(); store = Store(root)
    if args.semantic_scholar:
        providers = (SemanticScholarProvider(),)
    else:
        providers = (OpenAlexProvider(),) if args.fulltext else (CrossrefProvider(), OpenAlexProvider())
    acl = AclAnthologyProvider()
    resolved = 0
    if args.semantic_scholar:
        candidates = [row for row in store.papers() if row["fulltext_status"] == "unresolved"
                      and not store.db.execute("SELECT 1 FROM resolutions WHERE paper_id=? AND provider='semantic-scholar'", (row["id"],)).fetchone()
                      and not store.db.execute("SELECT 1 FROM failures WHERE subject=? AND stage='resolve:semantic-scholar'", (row["id"],)).fetchone()]
    elif args.fulltext:
        candidates = [row for row in store.papers() if row["fulltext_status"] == "unresolved" and not store.db.execute("SELECT 1 FROM resolutions WHERE paper_id=? AND provider='openalex'", (row["id"],)).fetchone() and not store.db.execute("SELECT 1 FROM failures WHERE subject=? AND stage='resolve'", (row["id"],)).fetchone()]
    else:
        candidates = [row for row in store.papers() if not row["arxiv_id"] and not row["doi"]]
    if args.limit:
        candidates = candidates[:args.limit]
    for row in candidates:
        matched = False
        if not store.db.execute("SELECT 1 FROM resolutions WHERE paper_id=? AND provider=?", (row["id"], acl.name)).fetchone():
            for (url,) in store.db.execute("SELECT url FROM paper_links WHERE paper_id=?", (row["id"],)).fetchall():
                candidate = acl.resolve_link(row["title"], url)
                if candidate:
                    store.record_resolution(row["id"], candidate)
                    resolved += 1
                    matched = True
                    break
        for provider in providers:
            if matched:
                break
            try:
                matches = provider.resolve(row["title"])
                for candidate in matches:
                    store.record_resolution(row["id"], candidate); resolved += 1
                    matched = True
                if matches:
                    break
            except Exception as error:
                store.record_failure("resolve:" + provider.name, row["id"], str(error))
        if not matched:
            stage = "resolve:semantic-scholar" if args.semantic_scholar else "resolve"
            store.record_failure(stage, row["id"], "No source candidate met the 0.84 normalized-title similarity threshold.")
    config = load_config(root, args.professor_id)
    store.deduplicate_by_identifier()
    write_research_map(root, store, config, root / "research" / "seeds" / Path(config["seed_file"]).name)
    store.close(); print(f"recorded {resolved} resolutions"); return 0


def report(args: argparse.Namespace) -> int:
    path = Path(args.root).resolve() / "reports" / f"bootstrap-{args.professor_id}.md"
    print(path.read_text(encoding="utf-8") if path.exists() else f"report not found: {path}")
    return 0


def _discovery_filters(args: argparse.Namespace) -> DiscoveryFilters:
    return DiscoveryFilters(args.year_from, args.year_to, args.author, args.venue, args.topic,
                            args.open_access, args.citation_min, tuple(args.provider or ()))


def _professor_topics(root: Path, professor_id: str) -> list[str]:
    path = root / "research" / "professor" / professor_id / "research-directions.md"
    return path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []


def discover(args: argparse.Namespace) -> int:
    root=Path(args.root).resolve(); store=Store(root); filters=_discovery_filters(args)
    candidates,failures=Federation(root).discover(args.query,filters,args.limit)
    candidates=rank_candidates(candidates,args.query,_professor_topics(root,args.professor_id),store.papers())
    store.record_discovery(args.query,filters.__dict__,candidates,failures)
    output={"kind":"live-discovery-candidates","query":args.query,"count":len(candidates),"failures":failures,"results":[c.payload() for c in candidates]}
    print(json.dumps(output,ensure_ascii=False,indent=2)); store.close()
    return 0 if candidates else 1


def _candidate_from_payload(item: dict) -> Candidate:
    fields={name:item.get(name) for name in Candidate.__dataclass_fields__}
    return Candidate(**fields)


def expand(args: argparse.Namespace) -> int:
    root=Path(args.root).resolve(); store=Store(root); source=store.discovery_candidate(args.paper_id); corpus=store.paper(args.paper_id)
    if not source and not corpus: raise SystemExit(f"unknown corpus paper or candidate: {args.paper_id}")
    relations={x for x in ("references","citations","similar") if getattr(args,x)}
    if not relations: raise SystemExit("select at least one of --references, --citations, or --similar")
    federation=Federation(root); discovered=[]; failures={}
    for adapter in federation.adapters:
        if not hasattr(adapter,"expand"): continue
        if source and adapter.name=="openalex": identifier=source.get("openalex_id")
        elif source and adapter.name=="semantic-scholar": identifier=source.get("semantic_scholar_id") or ("DOI:"+source["doi"] if source.get("doi") else None) or ("ARXIV:"+source["arxiv_id"] if source.get("arxiv_id") else None)
        elif corpus is not None and adapter.name=="semantic-scholar": identifier=("DOI:"+corpus["doi"] if corpus["doi"] else None) or ("ARXIV:"+corpus["arxiv_id"] if corpus["arxiv_id"] else None)
        else: identifier=None
        if not identifier: continue
        try: discovered.extend(adapter.expand(identifier,relations,args.limit))
        except Exception as error: failures[adapter.name]=str(error)
    candidates=rank_candidates(deduplicate(discovered),source["title"] if source else corpus["title"],_professor_topics(root,args.professor_id),store.papers())
    store.record_discovery(f"expand:{args.paper_id}",{"relations":sorted(relations)},candidates,failures)
    if source:
        for item in candidates: store.record_candidate_relation(args.paper_id,item.id,item.relation,item.providers)
    print(json.dumps({"kind":"expansion-candidates","source":args.paper_id,"count":len(candidates),"failures":failures,"results":[x.payload() for x in candidates]},ensure_ascii=False,indent=2)); store.close()
    return 0 if candidates else 1


def import_candidate(args: argparse.Namespace) -> int:
    root=Path(args.root).resolve(); store=Store(root); item=store.discovery_candidate(args.candidate_id)
    if not item: raise SystemExit(f"unknown discovery candidate: {args.candidate_id}")
    if item.get("imported_paper_id"):
        print(json.dumps({"candidate":args.candidate_id,"state":"imported","paper_id":item["imported_paper_id"]})); store.close(); return 0
    evidence="discovery candidate " + args.candidate_id
    if item.get("doi"): evidence += "; doi: " + item["doi"]
    links=[]
    for url,label in ((item.get("landing_url"),"candidate landing page"),(item.get("oa_url"),"open-access location (metadata only)")):
        if url: links.append(Link(url,label))
    publication=Publication(item["title"],", ".join(item.get("authors") or []),item.get("year"),item.get("venue"),"discovery-import",item.get("landing_url") or (item.get("provenance") or [{}])[0].get("url",f"candidate:{args.candidate_id}"),evidence,tuple(links))
    store.upsert_papers([publication]); row=store.db.execute("SELECT id FROM papers WHERE normalized_title=?",(normalize_title(publication.title),)).fetchone(); imported_id=row["id"]
    store.db.execute("UPDATE papers SET doi=COALESCE(doi,?),arxiv_id=COALESCE(arxiv_id,?),updated_at=? WHERE id=?",(item.get("doi"),item.get("arxiv_id"),utc_now(),imported_id))
    for provenance in item.get("provenance") or []:
        store.db.execute("INSERT OR IGNORE INTO paper_links(paper_id,url,label,kind) VALUES(?,?,?,?)",(imported_id,provenance["url"],"discovery provenance: "+provenance["provider"],"external"))
    store.db.commit(); store.mark_candidate_imported(args.candidate_id,imported_id); store.close()
    # Pipeline stages remain opt-in: importing metadata never implies full text.
    status={"candidate":args.candidate_id,"state":"imported","paper_id":imported_id,"fulltext":"not-fetched"}
    if args.resolve:
        ns=argparse.Namespace(root=str(root),professor_id=args.professor_id,limit=None,fulltext=True,semantic_scholar=False); resolve(ns)
    if args.fetch:
        fetch_paper(argparse.Namespace(root=str(root),paper_id=imported_id))
    if args.process:
        process_paper(argparse.Namespace(root=str(root),paper_id=imported_id))
    print(json.dumps(status,ensure_ascii=False)); return 0


def save_discovery_candidate(args: argparse.Namespace) -> int:
    store=Store(Path(args.root).resolve()); saved=store.save_candidate(args.candidate_id); store.close()
    print(json.dumps({"candidate":args.candidate_id,"state":"saved" if saved else "not-found"})); return 0 if saved else 1


def dashboard_payload(root: Path, professor_id: str) -> dict:
    """Produce a portable, read-only view model for the static research dashboard."""
    store = Store(root)
    try:
        config = load_config(root, professor_id)
        papers = []
        def artifact(path: Path) -> dict | None:
            if not path.exists():
                return None
            return {"path": str(path.relative_to(root)), "content": path.read_text(encoding="utf-8", errors="replace")}
        for row in store.papers():
            paper_dir = Path("research") / "papers" / row["id"]
            links = [{"url": link["url"], "label": link["label"], "kind": link["kind"]}
                     for link in store.db.execute("SELECT url,label,kind FROM paper_links WHERE paper_id=? ORDER BY kind,url", (row["id"],))]
            documents = {}
            for name in ("README.md", "reading-guide-zh.md", "method.md", "experiments-and-results.md", "limitations-and-critique.md", "prerequisites.md", "seminar-questions.md"):
                item = artifact(root / paper_dir / name)
                if item: documents[name.removesuffix(".md")] = item
            diagrams = [item for path in sorted((root / paper_dir / "diagrams").glob("*.mmd")) if (item := artifact(path))]
            extraction_path = root / paper_dir / "extraction.json"
            sections = []
            if extraction_path.exists():
                try: sections = json.loads(extraction_path.read_text(encoding="utf-8")) .get("sections", [])
                except (json.JSONDecodeError, UnicodeDecodeError): pass
            papers.append({
                "id": row["id"], "title": row["title"], "authors": row["authors"],
                "year": row["year"], "venue": row["venue"], "status": row["fulltext_status"],
                "doi": row["doi"], "arxiv_id": row["arxiv_id"], "source_url": row["source_url"],
                "pdf_path": row["pdf_path"], "links": links,
                "notes": [item["path"] for item in documents.values()], "documents": documents,
                "diagrams": diagrams, "sections": sections,
            })
        professor_dir = root / "research" / "professor" / config["id"]
        professor_artifacts = {}
        for path in sorted(professor_dir.glob("*.md")):
            if item := artifact(path): professor_artifacts[path.stem] = item
        seed_path = root / "research" / "seeds" / "NYCU NLP Lab Intro.pdf"
        return {
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
            "professor": {"id": config["id"], "name": config["name"], "affiliation": config["affiliation"], "url": config["professor_url"]},
            "summary": {"total": len(papers), "fetched": sum(p["status"] == "fetched" for p in papers), "unresolved": sum(p["status"] != "fetched" for p in papers)},
            "artifacts": professor_artifacts,
            "seeds": [{"label": "NYCU NLP Lab Intro", "path": str(seed_path.relative_to(root))}] if seed_path.exists() else [],
            "papers": papers,
            "discovery": {
                "candidates": store.discovery_candidates(),
                "runs": [{"query": row["query"], "filters": json.loads(row["filters_json"]),
                          "candidate_ids": json.loads(row["candidate_ids_json"]), "failures": json.loads(row["failures_json"]),
                          "created_at": row["created_at"]}
                         for row in store.db.execute("SELECT * FROM discovery_runs ORDER BY id DESC LIMIT 20")],
            },
        }
    finally:
        store.close()


def export_dashboard(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dashboard_payload(root, args.professor_id)
    output.write_text("window.RESEARCH_OS_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print(output)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="research-os")
    parser.add_argument("--root", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    boot = commands.add_parser("bootstrap"); boot.add_argument("--professor-url", required=True); boot.add_argument("--seed-file"); boot.add_argument("--source-file"); boot.add_argument("--crawl-depth", type=int, default=1); boot.set_defaults(func=bootstrap)
    refresh_parser = commands.add_parser("refresh"); refresh_parser.add_argument("professor_id"); refresh_parser.set_defaults(func=refresh)
    papers = commands.add_parser("papers"); papers.add_argument("professor_id", nargs="?"); papers.set_defaults(func=list_papers)
    fetch = commands.add_parser("fetch"); fetch.add_argument("paper_id"); fetch.set_defaults(func=fetch_paper)
    resolver = commands.add_parser("resolve"); resolver.add_argument("professor_id"); resolver.add_argument("--limit", type=int); resolver.add_argument("--fulltext", action="store_true", help="query OpenAlex for lawful open-access PDF locations"); resolver.add_argument("--semantic-scholar", action="store_true", help="opt in to Semantic Scholar title-match fallback; API may rate limit unauthenticated requests"); resolver.set_defaults(func=resolve)
    process = commands.add_parser("process"); process.add_argument("paper_id"); process.set_defaults(func=process_paper)
    translate = commands.add_parser("translate"); translate.add_argument("paper_id"); translate.add_argument("--config", required=True, help="local BabelDOC TOML; not copied into the corpus"); translate.add_argument("--executable", default="babeldoc"); translate.add_argument("--timeout", type=int, default=3600); translate.set_defaults(func=translate_paper)
    query = commands.add_parser("search"); query.add_argument("query"); query.set_defaults(func=search)
    discovery = commands.add_parser("discover", help="query live scholarly metadata providers; results remain candidates")
    discovery.add_argument("query"); discovery.add_argument("--professor-id", default="an-zi-yen"); discovery.add_argument("--limit", type=int, default=20)
    discovery.add_argument("--year-from",type=int); discovery.add_argument("--year-to",type=int); discovery.add_argument("--author"); discovery.add_argument("--venue"); discovery.add_argument("--topic")
    discovery.add_argument("--open-access",action="store_true"); discovery.add_argument("--citation-min",type=int); discovery.add_argument("--provider",action="append",choices=["openalex","semantic-scholar","crossref","arxiv","acl-anthology"]); discovery.set_defaults(func=discover)
    expansion=commands.add_parser("expand",help="find candidate references, citations, or similar papers")
    expansion.add_argument("paper_id"); expansion.add_argument("--references",action="store_true"); expansion.add_argument("--citations",action="store_true"); expansion.add_argument("--similar",action="store_true"); expansion.add_argument("--limit",type=int,default=20); expansion.add_argument("--professor-id",default="an-zi-yen"); expansion.set_defaults(func=expand)
    importer=commands.add_parser("import",help="promote one candidate into the permanent corpus")
    importer.add_argument("candidate_id"); importer.add_argument("--professor-id",default="an-zi-yen"); importer.add_argument("--resolve",action="store_true"); importer.add_argument("--fetch",action="store_true"); importer.add_argument("--process",action="store_true"); importer.set_defaults(func=import_candidate)
    saver=commands.add_parser("save-candidate"); saver.add_argument("candidate_id"); saver.set_defaults(func=save_discovery_candidate)
    report_parser = commands.add_parser("report"); report_parser.add_argument("professor_id"); report_parser.set_defaults(func=report)
    dashboard = commands.add_parser("dashboard", help="export the corpus data consumed by web/index.html")
    dashboard.add_argument("professor_id", nargs="?", default="an-zi-yen")
    dashboard.add_argument("--output", default="web/data.js")
    dashboard.set_defaults(func=export_dashboard)
    return args.func(args) if (args := parser.parse_args()).func else 1


if __name__ == "__main__":
    raise SystemExit(main())
