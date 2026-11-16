import job_scout as js


def test_unsupported_name_links_only_http():
    assert 'href="https://a.com/x?y=1&amp;z=2"' in js._uns_name({"name": "A", "url": "https://a.com/x?y=1&z=2"})
    assert "<a" not in js._uns_name({"name": "B", "url": "javascript:alert(1)"})
    assert js._uns_name({"name": "C<>"}) == "C&lt;&gt;"


def test_page_lists_unsupported_with_links(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(js, "HOME", tmp_path)
    (tmp_path / "unsupported.json").write_text(json.dumps(
        {"companies": [{"name": "Tesla", "reason": "blocks bots", "url": "https://www.tesla.com/careers"}]}))
    out = tmp_path / "index.html"
    js.write_queue_html([], out)
    page = out.read_text(encoding="utf8")
    assert 'id="unsupported"' in page and 'href="https://www.tesla.com/careers"' in page
