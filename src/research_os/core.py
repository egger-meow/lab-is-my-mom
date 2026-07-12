"""Core deterministic infrastructure for Research OS.

The module deliberately keeps the network, persistence, parsing, and document
processing boundaries explicit.  It does not call an LLM at runtime.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


USER_AGENT = "research-os/0.2 (+local deterministic corpus builder)"
RELEVANT_PAGE_TERMS = ("publication", "paper", "research", "project", "profile", "people", "person", "lab", "about")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def paper_id(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{normalized[:48]}-{hashlib.sha1(title.encode('utf-8')).hexdigest()[:8]}"


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def fetch_url(url: str, timeout: int = 30) -> tuple[bytes, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.geturl(), response.headers.get_content_type()


@dataclass(frozen=True)
class Link:
    href: str
    text: str


@dataclass(frozen=True)
class Publication:
    title: str
    authors: str
    year: int | None
    venue: str | None
    category: str
    source_url: str
    evidence: str
    links: tuple[Link, ...] = ()

    @property
    def id(self) -> str:
        return paper_id(self.title)

    @property
    def arxiv_id(self) -> str | None:
        corpus = " ".join([self.evidence, *(link.href for link in self.links)])
        match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})|arXiv:([0-9]{4}\.[0-9]{4,5})", corpus, re.I)
        return next((value for value in match.groups() if value), None) if match else None

    @property
    def doi(self) -> str | None:
        match = re.search(r"(?:doi\.org/|doi:\s*)(10\.\d{4,9}/[-._;()/:a-z0-9]+)", self.evidence, re.I)
        return match.group(1).rstrip(". ,)") if match else None


class LabPageParser(HTMLParser):
    """Small HTML parser tailored to semantic publication lists, not a site."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._publication_list_depth = 0
        self._in_heading = False
        self._heading_parts: list[str] = []
        self._category = "other"
        self._li_depth = 0
        self._li_parts: list[str] = []
        self._li_links: list[Link] = []
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []
        self.entries: list[tuple[str, str, tuple[Link, ...]]] = []
        self.all_links: list[Link] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "ol" and "publications" in (attributes.get("class") or "").split():
            self._publication_list_depth += 1
        elif tag == "h4" and self._publication_list_depth:
            self._in_heading, self._heading_parts = True, []
        elif tag == "li" and self._publication_list_depth:
            if not self._li_depth:
                self._li_parts, self._li_links = [], []
            self._li_depth += 1
        elif tag == "a":
            href = attributes.get("href")
            if href:
                self._anchor_href = urllib.parse.urljoin(self.base_url, href)
                self._anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "ol" and self._publication_list_depth:
            self._publication_list_depth -= 1
        elif tag == "h4" and self._in_heading:
            heading = " ".join(self._heading_parts).strip().lower()
            self._category = re.sub(r"\s+", "-", heading.rstrip(":")) or "other"
            self._in_heading = False
        elif tag == "a" and self._anchor_href:
            link = Link(self._anchor_href, " ".join(self._anchor_parts).strip())
            self.all_links.append(link)
            if self._li_depth:
                self._li_links.append(link)
            self._anchor_href = None
        elif tag == "li" and self._li_depth:
            self._li_depth -= 1
            if not self._li_depth:
                raw = re.sub(r"\s+", " ", " ".join(self._li_parts)).strip()
                self.entries.append((self._category, raw, tuple(self._li_links)))

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_parts.append(data)
        if self._li_depth:
            self._li_parts.append(data)
        if self._anchor_href:
            self._anchor_parts.append(data)


class LinkCollector(HTMLParser):
    """Collect anchors without interpreting them as publications."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[Link] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href = urllib.parse.urljoin(self.base_url, href)
                self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            self.links.append(Link(self._href, " ".join(self._text).strip()))
            self._href = None


def relevant_same_site_links(source: str, source_url: str) -> list[str]:
    """Return deterministic, de-fragmented navigation targets worth crawling.

    The predicate is intentionally conservative: it follows only pages on the
    exact host whose URL path or anchor text advertises professor/lab research
    content.  Scholarly links are preserved as paper links, not crawled as lab
    pages.
    """
    origin = urllib.parse.urlsplit(source_url)
    parser = LinkCollector(source_url)
    parser.feed(source)
    targets: set[str] = set()
    for link in parser.links:
        parsed = urllib.parse.urlsplit(link.href)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != origin.netloc:
            continue
        normalized = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))
        haystack = f"{parsed.path} {link.text}".lower()
        if normalized != source_url and any(term in haystack for term in RELEVANT_PAGE_TERMS):
            targets.add(normalized)
    return sorted(targets)


def _extract_title(raw: str) -> str | None:
    quoted = re.search(r"[\"“]([^\"”]+)[\"”]", raw)
    if quoted:
        return quoted.group(1).strip().rstrip(".")
    # E-QGen is unquoted on the source page.  Take text after author/year and
    # before the venue marker as a conservative fallback.
    after_year = re.split(r"\b(?:19|20)\d{2}\s*\)?\.\s*", raw, maxsplit=1)
    if len(after_year) == 2:
        candidate = re.split(r"\s+In\s+Proceedings\b|\s+arXiv\s+preprint\b", after_year[1], maxsplit=1)[0]
        candidate = candidate.strip(" .")
        return candidate or None
    return None


def _extract_authors(raw: str) -> str:
    match = re.match(r"(.+?)(?:\s*\(?\b(?:19|20)\d{2}\b\)?\.)", raw)
    return match.group(1).strip() if match else ""


def _extract_year(raw: str) -> int | None:
    match = re.search(r"\b(19|20)\d{2}\b", raw)
    return int(match.group(0)) if match else None


def _extract_venue(raw: str, title: str) -> str | None:
    tail = raw.split(title, 1)[-1].strip(" .")
    if not tail:
        return None
    return re.sub(r"\s+", " ", tail)[:500]


def parse_publications(source: str, source_url: str, aliases: Iterable[str]) -> list[Publication]:
    aliases_lower = tuple(alias.lower() for alias in aliases)
    by_title: dict[str, Publication] = {}
    # Some hand-authored lab pages contain an unclosed <li>. Scan each explicit
    # publication <ol> by its next <li> / </ol> boundary instead of relying on
    # browser DOM recovery, which would otherwise swallow later entries.
    lists = re.findall(r"<ol\b[^>]*\bclass=[\"'][^\"']*\bpublications\b[^\"']*[\"'][^>]*>(.*?)(?=</ol>)", source, re.I | re.S)
    entries: list[tuple[str, str, tuple[Link, ...]]] = []
    for listing in lists:
        category = "other"
        tokens = re.split(r"(?=<(?:h4|li)\b)", listing, flags=re.I)
        for token in tokens:
            if re.match(r"\s*<h4\b", token, re.I):
                heading = re.sub(r"<[^>]+>", " ", token)
                category = re.sub(r"\s+", "-", html.unescape(heading).strip().lower().rstrip(":"))
                continue
            if not re.match(r"\s*<li\b", token, re.I):
                continue
            links = tuple(Link(urllib.parse.urljoin(source_url, href), re.sub(r"<[^>]+>", " ", text).strip())
                          for href, text in re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", token, re.I | re.S))
            raw = re.sub(r"<[^>]+>", " ", token)
            raw = re.sub(r"\s+", " ", html.unescape(raw)).strip()
            entries.append((category or "other", raw, links))
    for category, raw, links in entries:
        authors = _extract_authors(raw)
        if not authors or not any(alias in authors.lower() for alias in aliases_lower):
            continue
        title = _extract_title(raw)
        if not title:
            continue
        pub = Publication(title=title, authors=authors, year=_extract_year(raw), venue=_extract_venue(raw, title),
                          category=category, source_url=source_url, evidence=raw, links=links)
        key = normalize_title(title)
        # Prefer an entry containing a direct scholarly identifier.
        if key not in by_title or (pub.arxiv_id or pub.doi) and not (by_title[key].arxiv_id or by_title[key].doi):
            by_title[key] = pub
    return sorted(by_title.values(), key=lambda p: (p.year or 0, p.title), reverse=True)


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.db_path = root / ".research-os" / "research.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sources (
          id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, fetched_at TEXT NOT NULL,
          sha256 TEXT NOT NULL, content_type TEXT, local_path TEXT, status TEXT NOT NULL, error TEXT
        );
        CREATE TABLE IF NOT EXISTS professors (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, affiliation TEXT NOT NULL,
          aliases_json TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS papers (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, normalized_title TEXT UNIQUE NOT NULL,
          authors TEXT NOT NULL, year INTEGER, venue TEXT, category TEXT NOT NULL, source_url TEXT NOT NULL,
          evidence TEXT NOT NULL, arxiv_id TEXT, doi TEXT, fulltext_status TEXT NOT NULL DEFAULT 'unresolved',
          pdf_path TEXT, pdf_sha256 TEXT, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS paper_links (
          paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE, url TEXT NOT NULL,
          label TEXT, kind TEXT NOT NULL, UNIQUE(paper_id, url)
        );
        CREATE TABLE IF NOT EXISTS paper_aliases (
          paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE, title TEXT NOT NULL,
          source_url TEXT NOT NULL, evidence TEXT NOT NULL, UNIQUE(paper_id, title, source_url)
        );
        CREATE TABLE IF NOT EXISTS documents (
          paper_id TEXT PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE, source_path TEXT NOT NULL,
          sha256 TEXT NOT NULL, pages INTEGER NOT NULL, extracted_path TEXT NOT NULL,
          parser_name TEXT NOT NULL, parser_version TEXT NOT NULL, config_json TEXT NOT NULL, processed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS failures (
          id INTEGER PRIMARY KEY, stage TEXT NOT NULL, subject TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS crawl_edges (
          source_url TEXT NOT NULL, target_url TEXT NOT NULL, depth INTEGER NOT NULL, followed_at TEXT NOT NULL,
          UNIQUE(source_url, target_url)
        );
        CREATE TABLE IF NOT EXISTS resolutions (
          paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE, provider TEXT NOT NULL,
          evidence_url TEXT NOT NULL, candidate_title TEXT NOT NULL, score REAL NOT NULL, doi TEXT,
          arxiv_id TEXT, pdf_url TEXT, resolved_at TEXT NOT NULL,
          UNIQUE(paper_id, provider, evidence_url)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS paper_search USING fts5(paper_id UNINDEXED, title, authors, venue, evidence);
        """)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def record_source(self, url: str, data: bytes, *, content_type: str, local_path: Path | None, status: str = "ok", error: str | None = None) -> None:
        self.db.execute("""INSERT INTO sources(url,fetched_at,sha256,content_type,local_path,status,error)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET fetched_at=excluded.fetched_at,sha256=excluded.sha256,
        content_type=excluded.content_type,local_path=excluded.local_path,status=excluded.status,error=excluded.error""",
                        (url, utc_now(), sha256_bytes(data), content_type, str(local_path) if local_path else None, status, error))
        self.db.commit()

    def record_failure(self, stage: str, subject: str, message: str) -> None:
        self.db.execute("INSERT INTO failures(stage,subject,message,created_at) VALUES(?,?,?,?)", (stage, subject, message, utc_now()))
        self.db.commit()

    def record_crawl_edge(self, source_url: str, target_url: str, depth: int) -> None:
        self.db.execute("""INSERT INTO crawl_edges(source_url,target_url,depth,followed_at)
        VALUES(?,?,?,?) ON CONFLICT(source_url,target_url) DO UPDATE SET depth=excluded.depth,followed_at=excluded.followed_at""",
                        (source_url, target_url, depth, utc_now()))
        self.db.commit()

    def upsert_professor(self, professor_id: str, name: str, url: str, affiliation: str, aliases: list[str]) -> None:
        self.db.execute("""INSERT INTO professors VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,url=excluded.url,affiliation=excluded.affiliation,aliases_json=excluded.aliases_json""",
                        (professor_id, name, url, affiliation, json.dumps(aliases, ensure_ascii=False), utc_now()))
        self.db.commit()

    def upsert_papers(self, publications: Iterable[Publication]) -> None:
        for pub in publications:
            self.db.execute("""INSERT INTO papers(id,title,normalized_title,authors,year,venue,category,source_url,evidence,arxiv_id,doi,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(normalized_title) DO UPDATE SET authors=excluded.authors,
            year=excluded.year,venue=excluded.venue,category=excluded.category,source_url=excluded.source_url,
            evidence=excluded.evidence,arxiv_id=COALESCE(excluded.arxiv_id,papers.arxiv_id),doi=COALESCE(excluded.doi,papers.doi),updated_at=excluded.updated_at""",
                            (pub.id, pub.title, normalize_title(pub.title), pub.authors, pub.year, pub.venue, pub.category,
                             pub.source_url, pub.evidence, pub.arxiv_id, pub.doi, utc_now()))
            row = self.db.execute("SELECT id FROM papers WHERE normalized_title=?", (normalize_title(pub.title),)).fetchone()
            for link in pub.links:
                kind = "arxiv" if "arxiv.org" in link.href else "doi" if "doi.org" in link.href else "external"
                self.db.execute("INSERT OR IGNORE INTO paper_links(paper_id,url,label,kind) VALUES(?,?,?,?)", (row["id"], link.href, link.text, kind))
            self.db.execute("DELETE FROM paper_search WHERE paper_id=?", (row["id"],))
            self.db.execute("INSERT INTO paper_search(paper_id,title,authors,venue,evidence) VALUES(?,?,?,?,?)",
                            (row["id"], pub.title, pub.authors, pub.venue or "", pub.evidence))
        self.db.commit()

    def apply_paper_hints(self, hints: Iterable[dict[str, str]]) -> None:
        """Apply professor-configured identifiers discovered on project pages.

        Hints are configuration, not parser rules: each carries the page URL
        which supplied the identifier, so this remains auditable and reusable.
        """
        for hint in hints:
            title_key = normalize_title(hint["title"])
            row = self.db.execute("SELECT id FROM papers WHERE normalized_title=?", (title_key,)).fetchone()
            if not row:
                continue
            arxiv_id = hint.get("arxiv_id")
            if arxiv_id:
                url = f"https://arxiv.org/abs/{arxiv_id}"
                self.db.execute("UPDATE papers SET arxiv_id=COALESCE(arxiv_id,?),updated_at=? WHERE id=?", (arxiv_id, utc_now(), row["id"]))
                self.db.execute("INSERT OR IGNORE INTO paper_links(paper_id,url,label,kind) VALUES(?,?,?,?)", (row["id"], url, hint.get("evidence", "project-page hint"), "arxiv"))
        self.db.commit()

    def paper(self, paper_id_value: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM papers WHERE id=?", (paper_id_value,)).fetchone()

    def papers(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM papers ORDER BY year DESC, title").fetchall()

    def search(self, query: str) -> list[sqlite3.Row]:
        phrase = '"' + query.replace('"', '""') + '"'
        return self.db.execute("SELECT p.* FROM paper_search s JOIN papers p ON p.id=s.paper_id WHERE paper_search MATCH ? ORDER BY p.year DESC,p.title", (phrase,)).fetchall()

    def update_pdf(self, paper_id_value: str, path: Path, data: bytes, status: str = "fetched") -> None:
        self.db.execute("UPDATE papers SET fulltext_status=?,pdf_path=?,pdf_sha256=?,updated_at=? WHERE id=?",
                        (status, str(path), sha256_bytes(data), utc_now(), paper_id_value))
        self.db.commit()

    def record_resolution(self, paper_id_value: str, resolution) -> None:
        self.db.execute("""INSERT OR REPLACE INTO resolutions(paper_id,provider,evidence_url,candidate_title,score,doi,arxiv_id,pdf_url,resolved_at)
        VALUES(?,?,?,?,?,?,?,?,?)""", (paper_id_value, resolution.provider, resolution.evidence_url, resolution.title,
                                         resolution.score, resolution.doi, resolution.arxiv_id, resolution.pdf_url, utc_now()))
        self.db.execute("UPDATE papers SET doi=COALESCE(doi,?),arxiv_id=COALESCE(arxiv_id,?),updated_at=? WHERE id=?",
                        (resolution.doi, resolution.arxiv_id, utc_now(), paper_id_value))
        if resolution.pdf_url:
            self.db.execute("INSERT OR IGNORE INTO paper_links(paper_id,url,label,kind) VALUES(?,?,?,?)",
                            (paper_id_value, resolution.pdf_url, resolution.provider, "pdf"))
        self.db.commit()

    def deduplicate_by_identifier(self) -> int:
        """Merge records that independent metadata identifies as the same work."""
        merged = 0
        for column in ("arxiv_id", "doi"):
            groups = self.db.execute(f"SELECT {column} AS value FROM papers WHERE {column} IS NOT NULL GROUP BY {column} HAVING count(*) > 1").fetchall()
            for group in groups:
                rows = self.db.execute(f"SELECT * FROM papers WHERE {column}=? ORDER BY (fulltext_status!='fetched'), (category='other-publication'), id", (group["value"],)).fetchall()
                primary, duplicates = rows[0], rows[1:]
                for duplicate in duplicates:
                    self.db.execute("INSERT OR IGNORE INTO paper_aliases(paper_id,title,source_url,evidence) VALUES(?,?,?,?)",
                                    (primary["id"], duplicate["title"], duplicate["source_url"], duplicate["evidence"]))
                    self.db.execute("INSERT OR IGNORE INTO paper_links(paper_id,url,label,kind) SELECT ?,url,label,kind FROM paper_links WHERE paper_id=?", (primary["id"], duplicate["id"]))
                    self.db.execute("INSERT OR IGNORE INTO resolutions(paper_id,provider,evidence_url,candidate_title,score,doi,arxiv_id,pdf_url,resolved_at) SELECT ?,provider,evidence_url,candidate_title,score,doi,arxiv_id,pdf_url,resolved_at FROM resolutions WHERE paper_id=?", (primary["id"], duplicate["id"]))
                    if primary["fulltext_status"] != "fetched" and duplicate["fulltext_status"] == "fetched":
                        self.db.execute("UPDATE papers SET fulltext_status=?,pdf_path=?,pdf_sha256=? WHERE id=?", (duplicate["fulltext_status"], duplicate["pdf_path"], duplicate["pdf_sha256"], primary["id"]))
                    doc = self.db.execute("SELECT 1 FROM documents WHERE paper_id=?", (primary["id"],)).fetchone()
                    if not doc:
                        self.db.execute("UPDATE documents SET paper_id=? WHERE paper_id=?", (primary["id"], duplicate["id"]))
                    self.db.execute("DELETE FROM paper_search WHERE paper_id=?", (duplicate["id"],))
                    self.db.execute("DELETE FROM papers WHERE id=?", (duplicate["id"],))
                    merged += 1
        self.db.commit()
        return merged

    def record_document(self, paper_id_value: str, source_path: Path, payload: dict, extracted_path: Path) -> None:
        self.db.execute("""INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(paper_id) DO UPDATE SET
        source_path=excluded.source_path,sha256=excluded.sha256,pages=excluded.pages,extracted_path=excluded.extracted_path,
        parser_name=excluded.parser_name,parser_version=excluded.parser_version,config_json=excluded.config_json,processed_at=excluded.processed_at""",
                        (paper_id_value, str(source_path), payload["sha256"], payload["page_count"], str(extracted_path),
                         "PyMuPDF", payload["parser_version"], json.dumps(payload["config"]), utc_now()))
        self.db.commit()
