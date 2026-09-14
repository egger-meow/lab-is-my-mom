from pathlib import Path


def test_html_contains_topic_kanban_elements():
    html_path = Path("src/master_os/web/static/index.html")
    content = html_path.read_text(encoding="utf-8")
    assert "research-kanban" in content
    assert "stage-seed" in content
    assert "stage-exploring" in content
    assert "stage-viable" in content
    assert "stage-candidate" in content
    assert "stage-selected" in content
    assert "stage-killed" in content
    assert "create-topic-seed-btn" in content
    assert "topic-detail-modal" in content


def test_app_js_contains_topic_handlers():
    js_path = Path("src/master_os/web/static/app.js")
    content = js_path.read_text(encoding="utf-8")
    assert "fetchTopics" in content
    assert "transitionTopic" in content
    assert "createTopicSeed" in content
    assert "renderTopicsKanban" in content
    assert "openTopicDetail" in content
