from pathlib import Path
import subprocess

import pytest

from research_os import cli
from research_os.cli import crawl_same_site, process_pdf
from research_os.core import Store, normalize_title, parse_publications, relevant_same_site_links
from research_os.translation import BabelDocTranslator, TranslationUnavailable


def test_normalize_title_dedup_key():
    assert normalize_title("A Study: on NLP!") == "a study on nlp"


def test_parser_keeps_authored_entries_links_and_excludes_unrelated_mentions():
    source = """
    <ol class="publications"><h4>Conference Papers:</h4>
      <li>A. Author, An-Zi Yen (2024). “Our Paper.” In ACL. <a href="https://arxiv.org/abs/2401.00001">Link</a></li>
      <li>Other Author (2024). “Cited Paper.” In ACL.</li>
    </ol>
    <section><li>An-Zi Yen is mentioned in a project description.</li></section>
    """
    papers = parse_publications(source, "https://example.test/", ["An-Zi Yen"])
    assert len(papers) == 1
    assert papers[0].title == "Our Paper"
    assert papers[0].category == "conference-papers"
    assert papers[0].arxiv_id == "2401.00001"
    assert papers[0].links[0].href == "https://arxiv.org/abs/2401.00001"


def test_store_deduplicates_and_searches_by_provenance(tmp_path: Path):
    html = '<ol class="publications"><h4>Other Publication:</h4><li>An-Zi Yen (2024). “Fact Check.” arXiv preprint arXiv:2401.00001.</li></ol>'
    paper = parse_publications(html, "https://example.test/", ["An-Zi Yen"])[0]
    store = Store(tmp_path)
    store.upsert_papers([paper, paper])
    rows = store.papers()
    assert len(rows) == 1
    assert rows[0]["fulltext_status"] == "unresolved"
    assert store.search("Fact Check")[0]["id"] == paper.id
    store.close()


def test_source_provenance_retains_hash_timestamp_and_local_path(tmp_path: Path):
    store = Store(tmp_path)
    snapshot = tmp_path / "page.html"
    content = b"<html>verified source</html>"
    snapshot.write_bytes(content)
    store.record_source("https://example.test/", content, content_type="text/html", local_path=snapshot)
    row = store.db.execute("select url,sha256,fetched_at,local_path,status from sources").fetchone()
    assert row["url"] == "https://example.test/"
    assert len(row["sha256"]) == 64
    assert row["fetched_at"]
    assert Path(row["local_path"]) == snapshot
    assert row["status"] == "ok"
    store.close()


def test_same_site_crawl_targets_are_relevance_filtered_and_recordable(tmp_path: Path):
    source = """
    <a href="/research">Research</a>
    <a href="/news">News</a>
    <a href="https://outside.example/projects">Outside project</a>
    <a href="/publications#recent">Publications</a>
    """
    targets = relevant_same_site_links(source, "https://lab.example/")
    assert targets == ["https://lab.example/publications", "https://lab.example/research"]
    store = Store(tmp_path)
    store.record_crawl_edge("https://lab.example/", targets[0], 1)
    edge = store.db.execute("select source_url,target_url,depth,followed_at from crawl_edges").fetchone()
    assert edge["target_url"] == targets[0]
    assert edge["depth"] == 1
    assert edge["followed_at"]
    store.close()


def test_bounded_crawl_snapshots_relevant_pages_and_collects_authored_papers(tmp_path: Path, monkeypatch):
    root_url = "https://lab.example/"
    research_url = "https://lab.example/research"
    root_html = b'<a href="/research">Research</a><a href="/news">News</a>'
    research_html = b'''<ol class="publications"><h4>Conference Papers:</h4>
    <li>Collaborator, An-Zi Yen (2025). "Crawled Paper." In ACL.</li></ol>'''
    responses = {research_url: (research_html, research_url, "text/html")}
    monkeypatch.setattr(cli, "load_config", lambda root: {"aliases": ["An-Zi Yen"]})
    monkeypatch.setattr(cli, "fetch_url", lambda url: responses[url])
    store = Store(tmp_path)
    papers = crawl_same_site(tmp_path, store, root_url, root_html, "text/html", max_depth=1)
    assert [paper.title for paper in papers] == ["Crawled Paper"]
    assert store.db.execute("select count(*) from sources").fetchone()[0] == 2
    assert store.db.execute("select count(*) from crawl_edges").fetchone()[0] == 1
    assert (tmp_path / ".research-os" / "snapshots" / "professor.html").exists()
    assert len(list((tmp_path / ".research-os" / "snapshots").glob("page-*.html"))) == 1
    store.close()


def test_babeldoc_adapter_is_optional_and_uses_documented_config_cli(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.pdf"
    config = tmp_path / "babeldoc.toml"
    executable = tmp_path / "babeldoc.exe"
    source.write_bytes(b"%PDF-1.7\n")
    config.write_text("[babeldoc]\noutput = 'output'\n", encoding="utf-8")
    translator = BabelDocTranslator(str(executable))
    with pytest.raises(TranslationUnavailable):
        translator.translate(source, config)
    executable.write_bytes(b"placeholder")
    captured = {}
    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")
    monkeypatch.setattr("research_os.translation.subprocess.run", fake_run)
    result = translator.translate(source, config, timeout=12)
    assert result.return_code == 0
    assert captured["command"] == (str(executable), "--config", str(config), "--files", str(source))
    assert captured["kwargs"]["timeout"] == 12


def test_store_merges_records_with_same_external_identifier(tmp_path: Path):
    source = """
    <ol class="publications"><h4>Conference Papers:</h4>
    <li>An-Zi Yen (2025). “Final Conference Title.” arXiv preprint arXiv:2501.00001.</li>
    <h4>Other Publication:</h4><li>An-Zi Yen (2024). “Preprint Title.” arXiv preprint arXiv:2501.00001.</li>
    </ol>"""
    store = Store(tmp_path)
    store.upsert_papers(parse_publications(source, "https://example.test/", ["An-Zi Yen"]))
    assert store.deduplicate_by_identifier() == 1
    rows = store.papers()
    assert len(rows) == 1
    assert rows[0]["title"] == "Final Conference Title"
    assert store.db.execute("select count(*) from paper_aliases").fetchone()[0] == 1
    store.close()


def test_document_processing_records_page_level_text_and_provenance(tmp_path: Path):
    import pymupdf

    pdf = tmp_path / "paper.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Abstract\nA provenance test paper.")
    document.save(pdf)
    document.close()
    extracted = process_pdf(pdf)
    assert extracted["page_count"] == 1
    assert extracted["pages"][0]["page"] == 1
    assert "provenance test" in extracted["pages"][0]["text"].lower()
    assert len(extracted["sha256"]) == 64
