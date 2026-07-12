"""Scholarly metadata providers.

Providers return candidates with their own evidence URLs. They do not claim a
paper is downloaded; that transition is made only after a legal PDF is saved
and hashed by the fetch stage.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol
from urllib.parse import quote, urlsplit

from .core import fetch_url, normalize_title


@dataclass(frozen=True)
class Resolution:
    provider: str
    evidence_url: str
    title: str
    score: float
    doi: str | None = None
    arxiv_id: str | None = None
    pdf_url: str | None = None


class Provider(Protocol):
    name: str
    def resolve(self, title: str) -> list[Resolution]: ...


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


class CrossrefProvider:
    name = "crossref"

    def resolve(self, title: str) -> list[Resolution]:
        url = "https://api.crossref.org/works?rows=5&query.bibliographic=" + quote(title)
        data, final_url, _ = fetch_url(url, timeout=10)
        items = json.loads(data)["message"]["items"]
        results = []
        for item in items:
            candidate = (item.get("title") or [""])[0]
            score = title_similarity(title, candidate)
            if score >= 0.84:
                doi = item.get("DOI")
                results.append(Resolution(self.name, final_url, candidate, score, doi=doi))
        return results


class OpenAlexProvider:
    name = "openalex"

    def resolve(self, title: str) -> list[Resolution]:
        url = "https://api.openalex.org/works?per-page=5&search=" + quote(title)
        data, final_url, _ = fetch_url(url, timeout=10)
        items = json.loads(data)["results"]
        results = []
        for item in items:
            candidate = item.get("title", "")
            score = title_similarity(title, candidate)
            if score < 0.84:
                continue
            locations = [item.get("best_oa_location") or {}, *(item.get("locations") or [])]
            pdf_url = next((location.get("pdf_url") for location in locations if location.get("pdf_url")), None)
            doi = (item.get("doi") or "").removeprefix("https://doi.org/") or None
            results.append(Resolution(self.name, item.get("id", final_url), candidate, score, doi=doi, pdf_url=pdf_url))
        return results


class ArxivProvider:
    name = "arxiv"

    def resolve(self, title: str, arxiv_id: str | None = None) -> list[Resolution]:
        if not arxiv_id:
            return []
        return [Resolution(self.name, f"https://arxiv.org/abs/{arxiv_id}", title, 1.0,
                           arxiv_id=arxiv_id, pdf_url=f"https://arxiv.org/pdf/{arxiv_id}")]


class AclAnthologyProvider:
    """Canonicalize source-backed ACL Anthology routes without web scraping."""

    name = "acl-anthology"

    def resolve_link(self, title: str, url: str) -> Resolution | None:
        parsed = urlsplit(url)
        if parsed.netloc.lower() not in {"aclanthology.org", "www.aclanthology.org"}:
            return None
        identifier = parsed.path.strip("/")
        if identifier.endswith(".pdf"):
            identifier = identifier[:-4]
        # ACL IDs are one segment. Excluding internal file paths prevents a
        # generic attachment from being promoted to a canonical publication.
        if "/" in identifier or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", identifier):
            return None
        canonical = f"https://aclanthology.org/{identifier}"
        return Resolution(self.name, canonical + "/", title, 1.0, pdf_url=canonical + ".pdf")


class SemanticScholarProvider:
    """Opt-in resolver for Semantic Scholar's public title-match endpoint."""

    name = "semantic-scholar"

    def resolve(self, title: str) -> list[Resolution]:
        fields = "title,url,externalIds,openAccessPdf"
        url = "https://api.semanticscholar.org/graph/v1/paper/search/match?query=" + quote(title) + "&fields=" + quote(fields)
        data, final_url, _ = fetch_url(url, timeout=10)
        item = json.loads(data)
        candidate = item.get("title", "")
        score = title_similarity(title, candidate)
        if score < 0.84:
            return []
        identifiers = item.get("externalIds") or {}
        pdf_url = (item.get("openAccessPdf") or {}).get("url")
        return [Resolution(self.name, item.get("url") or final_url, candidate, score,
                           doi=identifiers.get("DOI"), arxiv_id=identifiers.get("ArXiv") or identifiers.get("ARXIV"),
                           pdf_url=pdf_url)]
