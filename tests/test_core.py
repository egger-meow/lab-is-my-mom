from pathlib import Path

from research_os.cli import process_pdf
from research_os.core import Store, normalize_title, parse_publications


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
