import json
import time
from pathlib import Path

from research_os.core import Store
from research_os import cli
from research_os.discovery import (Candidate, DiscoveryFilters, Federation,
                                   ResponseCache, deduplicate, rank_candidates)


def test_candidate_normalization_keeps_metadata_not_fulltext():
    item=Candidate("  A   Paper ",["Ada Lovelace"],2025,doi="https://doi.org/10.1/ABC",oa_url="https://x/p.pdf",open_access=True,providers=["openalex"])
    assert item.title=="A Paper" and item.doi=="10.1/abc"
    assert "fulltext" not in item.payload() and item.oa_url.endswith(".pdf")


def test_deduplication_merges_all_identifier_and_provenance_signals():
    items=[
        Candidate("Confidence Routing for LLMs",["A. Yen"],2025,doi="10.1/x",providers=["crossref"],provenance=[{"provider":"crossref","url":"c"}]),
        Candidate("Confidence Routing for LLMs",["An-Zi Yen"],2025,doi="10.1/X",arxiv_id="2501.1",providers=["openalex"],provenance=[{"provider":"openalex","url":"o"}]),
        Candidate("Confidence routing for LLMs!",["An-Zi Yen"],2025,acl_id="2025.acl.1",providers=["acl-anthology"]),
    ]
    merged=deduplicate(items)
    assert len(merged)==1
    assert merged[0].providers==["acl-anthology","crossref","openalex"]
    assert merged[0].arxiv_id=="2501.1" and merged[0].acl_id=="2025.acl.1"


def test_ranking_explains_score_in_plain_language():
    top=Candidate("LLM confidence routing",["A"],2026,citation_count=10,open_access=True,providers=["semantic-scholar"],provider_scores={"semantic-scholar":.9})
    other=Candidate("Unrelated biology",["B"],2010,providers=["crossref"])
    ranked=rank_candidates([other,top],"LLM confidence routing",["large language models routing"],[])
    assert ranked[0] is top and ranked[0].ranking_explanation
    assert any("查詢詞" in reason for reason in top.ranking_explanation)


def test_response_cache_avoids_network_and_expires(tmp_path: Path):
    cache=ResponseCache(tmp_path,ttl=60); cache.put("https://api.test/x",b'{"ok":true}')
    assert cache.get("https://api.test/x")==b'{"ok":true}'
    path=next((tmp_path/".research-os/cache/discovery").glob("*.json")); old=time.time()-120
    import os; os.utime(path,(old,old))
    assert cache.get("https://api.test/x") is None


def test_federation_tolerates_partial_failure_and_applies_filters(tmp_path: Path):
    class Good:
        name="openalex"
        def search(self,q,f,limit): return [Candidate("LLM confidence routing",["Ada"],2025,open_access=True,providers=[self.name])]
    class Bad:
        name="crossref"
        def search(self,q,f,limit): raise TimeoutError("rate limited")
    results,failures=Federation(tmp_path,[Bad(),Good()]).discover("LLM",DiscoveryFilters(year_from=2024,open_access=True))
    assert len(results)==1 and failures=={"crossref":"rate limited"}


def test_discovery_store_keeps_candidate_separate_until_import(tmp_path: Path):
    store=Store(tmp_path); item=Candidate("Candidate only",["Ada"],2025,providers=["arxiv"])
    store.record_discovery("candidate",{},[item],{})
    assert store.discovery_candidate(item.id)["state"]=="candidate"
    assert store.papers()==[]
    store.save_candidate(item.id)
    assert store.discovery_candidate(item.id)["state"]=="saved"
    store.close()


def test_explicit_import_creates_provenance_backed_unfetched_corpus_record(tmp_path: Path):
    import argparse
    item=Candidate("Import me",["Ada"],2025,doi="10.1/import",landing_url="https://example.test/work",providers=["crossref"],provenance=[{"provider":"crossref","url":"https://api.crossref.test/query"}])
    store=Store(tmp_path); store.record_discovery("import",{},[item],{}); store.close()
    args=argparse.Namespace(root=str(tmp_path),candidate_id=item.id,professor_id="test",resolve=False,fetch=False,process=False)
    assert cli.import_candidate(args)==0
    store=Store(tmp_path); candidate=store.discovery_candidate(item.id); paper=store.paper(candidate["imported_paper_id"])
    assert candidate["state"]=="imported" and paper["fulltext_status"]=="unresolved"
    links=store.db.execute("select label,url from paper_links where paper_id=?",(paper["id"],)).fetchall()
    assert any("discovery provenance" in row["label"] for row in links)
    store.close()
