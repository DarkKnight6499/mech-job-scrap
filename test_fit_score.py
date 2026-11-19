import json
import fit_score as fs

P = json.load(open("data/config.json", encoding="utf8"))["profile"]


def test_membrane_materials_beats_generic():
    hi, why = fs.score_row("Membrane Materials Engineering Intern Summer 2027", "Veolia", [], P)
    lo, _ = fs.score_row("Engineering Intern", "Acme", [], P)
    assert hi > lo + 25 and "membranes/filtration" in why


def test_undergrad_only_penalised_and_flagged():
    s, why = fs.score_row("Undergraduate Engineering Intern", "Acme", [], P)
    assert s < 40 and "undergrad-only" in why


def test_graduate_bonus_and_bounds():
    s, why = fs.score_row("Graduate Mechanical Engineering Intern", "Acme", [], P)
    assert "grad-level" in why and 5 <= s <= 98


def test_kw_hits_ignored():
    a, _ = fs.score_row("Engineering Intern", "Acme", ["material"], P)
    b, _ = fs.score_row("Engineering Intern", "Acme", [], P)
    assert a == b


def test_page_has_fit_columns(tmp_path, monkeypatch):
    import job_scout as js
    monkeypatch.setattr(js, "HOME", tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"profile": P}))
    row = {"id": "x:1", "company": "Veolia", "role": "Membrane Intern Summer 2027", "location": "Denver, CO", "link": "https://e.com/1",
           "posted": "2026-11-01", "state": "new", "kw_hits": [], "first_seen": "2026-11-02", "salary": "Unclear"}
    out = tmp_path / "i.html"
    js.write_queue_html([row], out)
    page = out.read_text(encoding="utf8")
    assert 'class="fit"' in page and "Insight" in page and "membranes/filtration" in page
