"""Scholarly metadata providers.

Providers return candidates with their own evidence URLs. They do not claim a
paper is downloaded; that transition is made only after a legal PDF is saved
and hashed by the fetch stage.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol
from urllib.parse import quote

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
