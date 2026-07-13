"""Federated, metadata-only academic discovery.

Discovery candidates are deliberately separate from permanent corpus papers.
No adapter downloads full text; an OA URL is metadata until the fetch command
validates and stores a PDF.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable

from .core import USER_AGENT, normalize_title


def _clean_doi(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I).strip().lower() or None


def _year(value: Any) -> int | None:
    try:
        year = int(value)
        return year if 1000 <= year <= 3000 else None
    except (TypeError, ValueError):
        return None


def _authors(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        return [x.strip() for x in re.split(r"\s*(?:,|;| and )\s*", values) if x.strip()]
    result = []
    for item in values:
        if isinstance(item, str): result.append(item.strip())
        elif isinstance(item, dict):
            result.append((item.get("name") or " ".join(filter(None, [item.get("given"), item.get("family")]))).strip())
    return [x for x in result if x]


@dataclass
class Candidate:
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    acl_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None
    citation_count: int | None = None
    open_access: bool = False
    landing_url: str | None = None
    oa_url: str | None = None
    topics: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    provenance: list[dict[str, str]] = field(default_factory=list)
    provider_scores: dict[str, float] = field(default_factory=dict)
    relation: str = "search"
    ranking_explanation: list[str] = field(default_factory=list)
    rank_score: float = 0.0

    def __post_init__(self) -> None:
        self.title = re.sub(r"\s+", " ", self.title or "").strip()
        self.doi = _clean_doi(self.doi)
        self.authors = _authors(self.authors)
        self.providers = sorted(set(self.providers))

    @property
    def id(self) -> str:
        identity = self.doi or self.arxiv_id or self.acl_id or normalize_title(self.title)
        return "cand-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]

    def payload(self) -> dict[str, Any]:
        value = asdict(self); value["id"] = self.id
        return value


@dataclass(frozen=True)
class DiscoveryFilters:
    year_from: int | None = None
    year_to: int | None = None
    author: str | None = None
    venue: str | None = None
    topic: str | None = None
    open_access: bool = False
    citation_min: int | None = None
    providers: tuple[str, ...] = ()


class ResponseCache:
    def __init__(self, root: Path, ttl: int = 86400) -> None:
        self.path = root / ".research-os" / "cache" / "discovery"
        self.path.mkdir(parents=True, exist_ok=True); self.ttl = ttl

    def get(self, key: str) -> bytes | None:
        path = self.path / (hashlib.sha256(key.encode()).hexdigest() + ".json")
        if path.exists() and time.time() - path.stat().st_mtime <= self.ttl:
            try: return json.loads(path.read_text(encoding="utf-8"))["body"].encode("latin1")
            except (OSError, KeyError, json.JSONDecodeError): return None
        return None

    def put(self, key: str, body: bytes) -> None:
        path = self.path / (hashlib.sha256(key.encode()).hexdigest() + ".json")
        path.write_text(json.dumps({"url": key, "cached_at": datetime.now(timezone.utc).isoformat(), "body": body.decode("latin1")}), encoding="utf-8")


class HttpClient:
    def __init__(self, cache: ResponseCache, min_interval: float = .12) -> None:
        self.cache, self.min_interval, self.last = cache, min_interval, {}

    def get(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        if cached := self.cache.get(url): return cached
        host = urllib.parse.urlsplit(url).netloc
        interval = 3.0 if host == "export.arxiv.org" else 1.0 if host == "api.semanticscholar.org" else self.min_interval
        delay = interval - (time.monotonic() - self.last.get(host, 0))
        if delay > 0: time.sleep(delay)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, text/html", **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=18) as response: body = response.read()
        except urllib.error.HTTPError as error:
            if error.code != 429: raise
            time.sleep(min(10.0, float(error.headers.get("Retry-After", "1") or 1)))
            with urllib.request.urlopen(request, timeout=18) as response: body = response.read()
        self.last[host] = time.monotonic(); self.cache.put(url, body); return body


def _abstract_from_index(index: dict[str, list[int]] | None) -> str | None:
    if not index: return None
    words = sorted(((position, word) for word, positions in index.items() for position in positions))
    return " ".join(word for _, word in words)


class OpenAlexDiscovery:
    name = "openalex"
    def __init__(self, http: HttpClient): self.http = http
    def search(self, query: str, f: DiscoveryFilters, limit: int) -> list[Candidate]:
        filters=[]
        if f.year_from or f.year_to: filters.append(f"publication_year:{f.year_from or 1000}-{f.year_to or datetime.now().year}")
        if f.open_access: filters.append("open_access.is_oa:true")
        if f.citation_min is not None: filters.append(f"cited_by_count:>{max(0, f.citation_min-1)}")
        params={"search":query,"per-page":str(limit)}
        if filters: params["filter"]=",".join(filters)
        url="https://api.openalex.org/works?"+urllib.parse.urlencode(params)
        items=json.loads(self.http.get(url)).get("results",[]); out=[]
        for rank,x in enumerate(items):
            ids=x.get("ids") or {}; oa=x.get("open_access") or {}; loc=x.get("best_oa_location") or {}
            source=((x.get("primary_location") or {}).get("source") or {})
            out.append(Candidate(x.get("title") or "", [a.get("author",{}).get("display_name","") for a in x.get("authorships",[])], _year(x.get("publication_year")), source.get("display_name"), _abstract_from_index(x.get("abstract_inverted_index")), ids.get("doi") or x.get("doi"), ids.get("arxiv"), None, (x.get("id") or "").rsplit("/",1)[-1] or None, citation_count=x.get("cited_by_count"), open_access=bool(oa.get("is_oa")), landing_url=x.get("id"), oa_url=loc.get("pdf_url") or oa.get("oa_url"), topics=[t.get("display_name","") for t in x.get("topics",[])], providers=[self.name], provenance=[{"provider":self.name,"url":url}], provider_scores={self.name:1-rank/max(1,len(items))}))
        return out

    def expand(self, identifier: str, relations: set[str], limit: int) -> list[Candidate]:
        work=json.loads(self.http.get("https://api.openalex.org/works/"+urllib.parse.quote(identifier,safe="")))
        ids=[]
        if "references" in relations: ids += work.get("referenced_works") or []
        if "similar" in relations: ids += work.get("related_works") or []
        results=[]
        if ids:
            url="https://api.openalex.org/works?"+urllib.parse.urlencode({"filter":"openalex:"+"|".join(x.rsplit("/",1)[-1] for x in ids[:limit]),"per-page":str(limit)})
            results += self._parse_expand(url, relations)
        if "citations" in relations:
            wid=(work.get("id") or identifier).rsplit("/",1)[-1]; url=f"https://api.openalex.org/works?filter=cites:{wid}&per-page={limit}"
            results += self._parse_expand(url, {"citations"})
        return results

    def _parse_expand(self,url,relations):
        data=json.loads(self.http.get(url)); out=[]
        for x in data.get("results",[]):
            ids=x.get("ids") or {}; oa=x.get("open_access") or {}; loc=x.get("best_oa_location") or {}
            source=((x.get("primary_location") or {}).get("source") or {})
            out.append(Candidate(x.get("title") or "",[a.get("author",{}).get("display_name","") for a in x.get("authorships",[])],_year(x.get("publication_year")),source.get("display_name"),_abstract_from_index(x.get("abstract_inverted_index")),ids.get("doi"),ids.get("arxiv"),openalex_id=(x.get("id") or "").rsplit("/",1)[-1],citation_count=x.get("cited_by_count"),open_access=bool(oa.get("is_oa")),landing_url=x.get("id"),oa_url=loc.get("pdf_url"),providers=[self.name],provenance=[{"provider":self.name,"url":url}],relation="/".join(sorted(relations))))
        return out


class SemanticScholarDiscovery:
    name="semantic-scholar"
    fields="paperId,title,authors,year,venue,abstract,externalIds,citationCount,openAccessPdf,url,fieldsOfStudy"
    def __init__(self,http): self.http=http
    def search(self,q,f,limit):
        p={"query":q,"limit":str(limit),"fields":self.fields}
        if f.year_from or f.year_to: p["year"]=f"{f.year_from or ''}-{f.year_to or ''}".strip("-")
        if f.open_access: p["openAccessPdf"]=""
        url="https://api.semanticscholar.org/graph/v1/paper/search?"+urllib.parse.urlencode(p)
        headers={"x-api-key":os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}
        return [self._candidate(x,url,i,limit) for i,x in enumerate(json.loads(self.http.get(url,headers)).get("data",[]))]
    def _candidate(self,x,url,rank=0,total=1,relation="search"):
        ids=x.get("externalIds") or {}; pdf=x.get("openAccessPdf") or {}
        return Candidate(x.get("title") or "",[a.get("name","") for a in x.get("authors",[])],_year(x.get("year")),x.get("venue"),x.get("abstract"),ids.get("DOI"),ids.get("ArXiv"),ids.get("ACL"),semantic_scholar_id=x.get("paperId"),citation_count=x.get("citationCount"),open_access=bool(pdf.get("url")),landing_url=x.get("url"),oa_url=pdf.get("url"),topics=x.get("fieldsOfStudy") or [],providers=[self.name],provenance=[{"provider":self.name,"url":url}],provider_scores={self.name:1-rank/max(1,total)},relation=relation)
    def expand(self,identifier,relations,limit):
        headers={"x-api-key":os.environ["SEMANTIC_SCHOLAR_API_KEY"]} if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else {}; out=[]
        for relation in relations & {"references","citations"}:
            url=f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(identifier,safe=':')}/{relation}?limit={limit}&fields={urllib.parse.quote(self.fields)}"
            for x in json.loads(self.http.get(url,headers)).get("data",[]):
                item=x.get("citedPaper") if relation=="references" else x.get("citingPaper")
                if item: out.append(self._candidate(item,url,relation=relation))
        if "similar" in relations:
            url=f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{urllib.parse.quote(identifier,safe=':')}?limit={limit}&fields={urllib.parse.quote(self.fields)}"
            for item in json.loads(self.http.get(url,headers)).get("recommendedPapers",[]):
                out.append(self._candidate(item,url,relation="similar"))
        return out


class CrossrefDiscovery:
    name="crossref"
    def __init__(self,http): self.http=http
    def search(self,q,f,limit):
        p={"query.bibliographic":q,"rows":str(limit)}; filters=[]
        if f.year_from: filters.append(f"from-pub-date:{f.year_from}-01-01")
        if f.year_to: filters.append(f"until-pub-date:{f.year_to}-12-31")
        if f.open_access: filters.append("has-license:true")
        if filters:p["filter"]=",".join(filters)
        if f.author:p["query.author"]=f.author
        if f.venue:p["query.container-title"]=f.venue
        url="https://api.crossref.org/works?"+urllib.parse.urlencode(p); items=json.loads(self.http.get(url))["message"]["items"]
        out=[]
        for i,x in enumerate(items):
            date=(x.get("published") or x.get("published-online") or {}).get("date-parts",[[None]])[0]
            links=x.get("link") or []; oa=next((l.get("URL") for l in links if l.get("content-type")=="application/pdf"),None)
            out.append(Candidate((x.get("title") or [""])[0],x.get("author"),_year(date[0] if date else None),(x.get("container-title") or [None])[0],re.sub("<[^>]+>"," ",x.get("abstract") or "") or None,x.get("DOI"),citation_count=x.get("is-referenced-by-count"),open_access=bool(x.get("license") or oa),landing_url=x.get("URL"),oa_url=oa,providers=[self.name],provenance=[{"provider":self.name,"url":url}],provider_scores={self.name:1-i/max(1,len(items))}))
        return out


class ArxivDiscovery:
    name="arxiv"
    def __init__(self,http): self.http=http
    def search(self,q,f,limit):
        terms=[f'all:"{q}"']
        if f.author:terms.append(f'au:"{f.author}"')
        p={"search_query":" AND ".join(terms),"start":"0","max_results":str(limit),"sortBy":"relevance"}
        url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode(p); root=ET.fromstring(self.http.get(url)); ns={"a":"http://www.w3.org/2005/Atom"}; out=[]
        for i,e in enumerate(root.findall("a:entry",ns)):
            aid=(e.findtext("a:id","",ns).rsplit("/",1)[-1]).split("v")[0]; published=e.findtext("a:published","",ns)
            out.append(Candidate(e.findtext("a:title","",ns),[a.findtext("a:name","",ns) for a in e.findall("a:author",ns)],_year(published[:4]),"arXiv",e.findtext("a:summary",None,ns),arxiv_id=aid,open_access=True,landing_url=f"https://arxiv.org/abs/{aid}",oa_url=f"https://arxiv.org/pdf/{aid}",topics=[c.get("term","") for c in e.findall("a:category",ns)],providers=[self.name],provenance=[{"provider":self.name,"url":url}],provider_scores={self.name:1-i/max(1,limit)}))
        return out


class _ACLSearchParser(HTMLParser):
    def __init__(self): super().__init__(); self.in_h5=False; self.href=None; self.text=[]; self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag in {"h5","h4"}: self.in_h5=True
        if self.in_h5 and tag=="a": self.href=dict(attrs).get("href"); self.text=[]
    def handle_data(self,data):
        if self.href:self.text.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href:
            href=self.href; title=" ".join(self.text).strip(); m=re.search(r"/([A-Za-z0-9][A-Za-z0-9.-]+)/?$",href)
            if title and m:self.items.append((title,m.group(1),href))
            self.href=None
        if tag in {"h5","h4"}:self.in_h5=False


class ACLAnthologyDiscovery:
    name="acl-anthology"
    def __init__(self,http):self.http=http
    def search(self,q,f,limit):
        # The Anthology has no remote JSON search API. Its public search page is
        # metadata-only; authoritative per-paper XML is fetched for matches.
        url="https://aclanthology.org/search/?"+urllib.parse.urlencode({"q":q}); parser=_ACLSearchParser(); parser.feed(self.http.get(url).decode("utf-8","replace")); out=[]
        for title,aid,href in parser.items[:limit]:
            canonical=urllib.parse.urljoin("https://aclanthology.org",href)
            out.append(Candidate(title,year=_year(re.match(r"(20\d{2})",aid).group(1)) if re.match(r"(20\d{2})",aid) else None,venue="ACL Anthology",acl_id=aid,open_access=True,landing_url=canonical,oa_url=canonical.rstrip("/")+".pdf",providers=[self.name],provenance=[{"provider":self.name,"url":url}],provider_scores={self.name:1-len(out)/max(1,limit)}))
        return out


def _same_author_year(a: Candidate,b: Candidate) -> bool:
    if not a.year or a.year != b.year or not a.authors or not b.authors:return False
    left={normalize_title(x).split()[-1] for x in a.authors if normalize_title(x)}; right={normalize_title(x).split()[-1] for x in b.authors if normalize_title(x)}
    return bool(left & right) and SequenceMatcher(None,normalize_title(a.title),normalize_title(b.title)).ratio() >= .82


def deduplicate(items: Iterable[Candidate]) -> list[Candidate]:
    merged=[]
    for item in items:
        match=next((x for x in merged if (item.doi and x.doi==item.doi) or (item.arxiv_id and x.arxiv_id==item.arxiv_id) or (item.acl_id and x.acl_id==item.acl_id) or normalize_title(x.title)==normalize_title(item.title) or _same_author_year(x,item)),None)
        if not match: merged.append(item); continue
        for field_name in ("doi","arxiv_id","acl_id","openalex_id","semantic_scholar_id","year","venue","abstract","landing_url","oa_url","citation_count"):
            if getattr(match,field_name) in (None,"") and getattr(item,field_name) not in (None,""):setattr(match,field_name,getattr(item,field_name))
        match.providers=sorted(set(match.providers+item.providers)); match.provenance += [p for p in item.provenance if p not in match.provenance]
        match.provider_scores.update(item.provider_scores); match.open_access |= item.open_access
        match.authors=match.authors or item.authors; match.topics=sorted(set(match.topics+item.topics))
    return merged


def rank_candidates(items: list[Candidate],query: str,professor_topics: Iterable[str],corpus: Iterable[Any]) -> list[Candidate]:
    q=set(normalize_title(query).split()); topics=set(normalize_title(" ".join(professor_topics)).split()); corpus_rows=list(corpus); now=datetime.now().year
    for item in items:
        words=set(normalize_title(" ".join([item.title,item.abstract or "",*item.topics])).split()); relevance=len(q&words)/max(1,len(q)); semantic=max(item.provider_scores.values(),default=0); prof=len(topics&words)/max(1,min(8,len(topics)))
        related=max((SequenceMatcher(None,normalize_title(item.title),normalize_title(r["title"])).ratio() for r in corpus_rows),default=0); recency=max(0,1-(now-(item.year or now))/12); citations=math.log1p(item.citation_count or 0)/10
        item.rank_score=.31*relevance+.16*semantic+.18*prof+.13*related+.09*recency+.08*min(1,citations)+.05*item.open_access
        exp=[]
        if relevance:exp.append(f"查詢詞命中 {len(q&words)}/{len(q)}")
        if semantic:exp.append("供應者提供相關性排序")
        if prof:exp.append("貼近教授研究主題")
        if related>.55:exp.append("與既有語料庫論文相近")
        if item.year and now-item.year<=2:exp.append("近兩年發表")
        if item.citation_count:exp.append(f"引用訊號 {item.citation_count} 次")
        if item.open_access:exp.append("有開放取用 metadata")
        if len(item.providers)>1:exp.append(f"{len(item.providers)} 個來源交叉確認")
        item.ranking_explanation=exp or ["metadata 與基本書目訊號相符"]
    return sorted(items,key=lambda x:(x.rank_score,x.year or 0),reverse=True)


def apply_filters(items: Iterable[Candidate], f: DiscoveryFilters) -> list[Candidate]:
    """Apply canonical filters after merging, including provider gaps."""
    output=[]
    for x in items:
        hay_topics=normalize_title(" ".join([x.title,x.abstract or "",*x.topics]))
        if f.year_from and (not x.year or x.year < f.year_from): continue
        if f.year_to and (not x.year or x.year > f.year_to): continue
        if f.author and normalize_title(f.author) not in normalize_title(" ".join(x.authors)): continue
        if f.venue and normalize_title(f.venue) not in normalize_title(x.venue or ""): continue
        if f.topic and normalize_title(f.topic) not in hay_topics: continue
        if f.open_access and not x.open_access: continue
        if f.citation_min is not None and (x.citation_count is None or x.citation_count < f.citation_min): continue
        if f.providers and not set(f.providers).intersection(x.providers): continue
        output.append(x)
    return output


class Federation:
    def __init__(self,root:Path,adapters=None):
        http=HttpClient(ResponseCache(root)); self.adapters=adapters or [OpenAlexDiscovery(http),SemanticScholarDiscovery(http),CrossrefDiscovery(http),ArxivDiscovery(http),ACLAnthologyDiscovery(http)]
    def discover(self,query:str,filters:DiscoveryFilters,limit=20):
        all_items=[]; failures={}
        for provider in self.adapters:
            if filters.providers and provider.name not in filters.providers:continue
            try:all_items.extend(provider.search(query,filters,limit))
            except Exception as error:failures[provider.name]=str(error)
        return apply_filters(deduplicate(all_items),filters),failures
