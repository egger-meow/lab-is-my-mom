from pathlib import Path
from master_os.core.database import MasterDatabase
from master_os.core.artifacts import ArtifactRegistry
from master_os.documents import save_document, list_documents


def test_save_document_stores_file_with_date_prefix_and_registers_artifact(tmp_path: Path):
    db_path = tmp_path / ".master-os" / "master.db"
    db = MasterDatabase(db_path)
    artifacts = ArtifactRegistry(db, repo_root=tmp_path)

    sample_content = b"%PDF-1.4 sample presentation slide bytes"
    result = save_document(
        repo_root=tmp_path,
        file_name="presentation_advisor.pdf",
        content=sample_content,
        date_str="2026-09-11",
        artifacts=artifacts,
    )

    expected_path = tmp_path / "data" / "documents" / "2026-09-11_presentation_advisor.pdf"
    assert expected_path.exists()
    assert expected_path.read_bytes() == sample_content

    assert result["filename"] == "2026-09-11_presentation_advisor.pdf"
    assert result["date"] == "2026-09-11"
    assert result["size_bytes"] == len(sample_content)
    assert result["artifact_id"] is not None

    # Check artifact registration
    art_row = db.fetchone("SELECT * FROM artifacts WHERE id = ?", (result["artifact_id"],))
    assert art_row is not None
    assert art_row["artifact_type"] == "document"
    assert art_row["path"] == "data/documents/2026-09-11_presentation_advisor.pdf"

    db.close()


def test_save_document_avoids_duplicate_date_prefix(tmp_path: Path):
    sample_content = b"%PDF-1.4 sample material"
    result = save_document(
        repo_root=tmp_path,
        file_name="2026-09-11_presentation_advisor.pdf",
        content=sample_content,
        date_str="2026-09-11",
    )

    expected_path = tmp_path / "data" / "documents" / "2026-09-11_presentation_advisor.pdf"
    assert expected_path.exists()
    assert result["filename"] == "2026-09-11_presentation_advisor.pdf"


def test_list_documents_returns_sorted_by_date(tmp_path: Path):
    doc_dir = tmp_path / "data" / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)

    (doc_dir / "2026-07-05_lab_intro.pdf").write_bytes(b"intro")
    (doc_dir / "2026-09-11_slides.pdf").write_bytes(b"slides")
    (doc_dir / "2026-09-03_notice.pdf").write_bytes(b"notice")

    docs = list_documents(repo_root=tmp_path)
    assert len(docs) == 3
    # Sorted newest first
    assert docs[0]["filename"] == "2026-09-11_slides.pdf"
    assert docs[0]["date"] == "2026-09-11"
    assert docs[1]["filename"] == "2026-09-03_notice.pdf"
    assert docs[1]["date"] == "2026-09-03"
    assert docs[2]["filename"] == "2026-07-05_lab_intro.pdf"
    assert docs[2]["date"] == "2026-07-05"


def test_cli_document_add_and_list(tmp_path: Path, monkeypatch, capsys):
    import master_os.cli as cli

    db_path = tmp_path / ".master-os" / "master.db"
    monkeypatch.setattr(cli, "get_paths", lambda: (tmp_path, db_path))

    # Create a source file to add
    src_file = tmp_path / "my_slides.pdf"
    src_file.write_bytes(b"%PDF-1.4 my presentation")

    # Call CLI document add
    monkeypatch.setattr(cli.sys, "argv", ["master-os", "document", "add", str(src_file), "--date", "2026-09-11"])
    cli.main()

    add_output = capsys.readouterr().out
    assert "成功儲存文件: 2026-09-11_my_slides.pdf" in add_output

    # Call CLI document list
    monkeypatch.setattr(cli.sys, "argv", ["master-os", "document", "list"])
    cli.main()

    list_output = capsys.readouterr().out
    assert "2026-09-11_my_slides.pdf" in list_output


def test_save_document_extracts_text_and_generates_agent_prompt(tmp_path: Path):
    from master_os.documents import generate_document_agent_prompt
    import pymupdf

    # Create a small real 1-page PDF using pymupdf
    pdf_doc = pymupdf.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 72), "NYCU NLP Lab Meeting Presentation:\n1. Completed baseline training.\n2. Must register for seminar by Friday.")
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    result = save_document(
        repo_root=tmp_path,
        file_name="slides.pdf",
        content=pdf_bytes,
        date_str="2026-09-11",
    )

    assert result["pages"] == 1
    assert result["chars"] > 0
    assert "MuPDF C++" in result["engine"]

    # Check that raw extracted text file exists
    txt_path = tmp_path / "data" / "documents" / "2026-09-11_slides.pdf.txt"
    assert txt_path.exists()
    extracted_text = txt_path.read_text(encoding="utf-8")
    assert "Completed baseline training" in extracted_text
    assert "Must register for seminar by Friday" in extracted_text

    # Generate Agent Prompt
    prompt = generate_document_agent_prompt(tmp_path, "2026-09-11_slides.pdf")
    assert "Completed baseline training" in prompt
    assert "Must register for seminar by Friday" in prompt
    assert "Master OS" in prompt
    assert "tasks" in prompt.lower()
    assert "obligations" in prompt.lower()


def test_ingest_document_preserves_evidence_without_inventing_tasks_or_runs(tmp_path: Path):
    from master_os.documents import ingest_document_to_db
    import pymupdf

    db_path = tmp_path / ".master-os" / "master.db"
    db = MasterDatabase(db_path)

    # Create a real PDF with NYCU Lab rules
    doc_dir = tmp_path / "data" / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = doc_dir / "2026-09-11_rules.pdf"

    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((50, 72), "NYCU NLP Lab 規定：\n1. 請填寫實驗室通訊錄表單：https://forms.gle/jdK46y6fkVEjtkQe8\n2. 請使用 NYCU email 註冊 Slack。\n3. 每週一參加 Lab Seminar。")
    pdf.save(str(pdf_path))
    pdf.close()

    res = ingest_document_to_db(tmp_path, "2026-09-11_rules.pdf", db=db)
    assert res["obligations_created"] == 0
    assert res["tasks_created"] == 0
    assert res["run_id"] is None
    assert res["event_id"]

    # Verify obligations and tasks exist in database
    obs = db.fetchall("SELECT * FROM obligations")
    tasks = db.fetchall("SELECT * FROM tasks")
    runs = db.fetchall("SELECT * FROM agent_runs")

    assert not obs
    assert not tasks
    assert not runs
    assert db.fetchone("SELECT id FROM events WHERE event_type='research.document_imported'")

    db.close()


def test_cli_document_ingest(tmp_path: Path, monkeypatch, capsys):
    import master_os.cli as cli
    import pymupdf

    db_path = tmp_path / ".master-os" / "master.db"
    db = MasterDatabase(db_path)
    db.close()

    monkeypatch.setattr(cli, "get_paths", lambda: (tmp_path, db_path))

    doc_dir = tmp_path / "data" / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = doc_dir / "2026-09-11_notice.pdf"

    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((50, 72), "NYCU NLP Lab: 請填寫實驗室通訊錄表單建立通訊錄 https://forms.gle/jdK46y6fkVEjtkQe8")
    pdf.save(str(pdf_path))
    pdf.close()

    monkeypatch.setattr(cli.sys, "argv", ["master-os", "document", "ingest", "2026-09-11_notice.pdf"])
    cli.main()

    out = capsys.readouterr().out
    assert "PyMuPDF C++ 解析完成" in out
    assert "寫入本地 DB" in out
    assert "成功更新" in out


