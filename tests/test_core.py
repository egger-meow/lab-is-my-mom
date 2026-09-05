from pathlib import Path
import json
import sqlite3

from research_os.core import Store, relevant_same_site_links


def test_store_initializes_schema(tmp_path: Path):
    store = Store(tmp_path)
    tables = {
        row["name"]
        for row in store.db.execute("select name from sqlite_master where type='table'").fetchall()
    }
    assert {"sources", "professors", "papers", "paper_sources"}.issubset(tables)
    store.close()


def test_store_source_roundtrip(tmp_path: Path):
    store = Store(tmp_path)
    content = b"<html><title>Lab</title></html>"
    snapshot = tmp_path / "page.html"
    snapshot.write_bytes(content)
    store.record_source("https://example.test/", content, content_type="text/html", local_path=snapshot)
    row = store.db.execute("select url,sha256,fetched_at,local_path,status from sources").fetchone()
    assert row["url"] == "https://example.test/"
    assert len(row["sha256"]) == 64
    assert row["fetched_at"]
    assert row["local_path"] == "page.html"
    assert store.resolve_path(row["local_path"]) == snapshot
    assert row["status"] == "ok"
    store.close()


def test_store_migrates_absolute_artifact_paths_to_workspace_relative(tmp_path: Path):
    store = Store(tmp_path)
    artifact = tmp_path / "research" / "paper.pdf"
    artifact.parent.mkdir()
    artifact.write_bytes(b"%PDF-1.7")
    store.db.execute(
        "INSERT INTO sources(url,fetched_at,sha256,content_type,local_path,status) VALUES(?,?,?,?,?,?)",
        ("file:legacy.pdf", "now", "0" * 64, "application/pdf", str(artifact), "ok"),
    )
    store.db.commit()
    store.close()
    migrated = Store(tmp_path)
    row = migrated.db.execute("select local_path from sources where url='file:legacy.pdf'").fetchone()
    # Persist portable POSIX-style relative paths regardless of the OS running tests.
    assert row["local_path"].replace("\\", "/") == "research/paper.pdf"
    assert migrated.resolve_path(row["local_path"]) == artifact
    migrated.close()


def test_same_site_crawl_targets_are_relevance_filtered_and_recordable(tmp_path: Path):
    source = """
    <a href="/research">Research</a>
    <a href="/news">News</a>
    <a href="https://outside.example/projects">Outside project</a>
    <a href="/publications#recent">Publications</a>
    """
    targets = relevant_same_site_links(source, "https://lab.example/")
    assert "https://lab.example/research" in targets
    assert "https://lab.example/publications" in targets
    assert "https://lab.example/news" not in targets
    assert not any("outside.example" in target for target in targets)
