"""All page filters cover eager and lazy tables, including filters set before loading."""
import functools
import json
import threading
from datetime import date, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

import job_scout as js


# Test inputs
SECTIONS = {
    "main": "#q",
    "blocked": "details:not([id]) table",
    "filtered": "#filteredLazy table",
    "closed": "#closedLazy table",
}
CASES = {
    "1": dict(company="Acme", role="Mechanical Intern Summer 2027", location="Denver, CO", age=1),
    "2": dict(company="Beta", role="Electrical Intern", location="New York, NY", age=10),
    "3": dict(company="Acme", role="Mechanical Intern Summer2027", location="Jersey City, NJ", age=20),
    "4": dict(company="Beta", role="Aerospace Intern", location="Chicago, IL", age=None),
}
FILTER_CASES = [
    ("text", {"1", "3"}),
    ("title_search", {"1", "3"}),
    ("company_search", {"1", "3"}),
    ("location_search", {"1"}),
    ("colorado", {"1"}),
    ("metro", {"2", "3"}),
    ("summer", {"1", "3"}),
    ("sponsorship", {"1", "3"}),
    ("date_min", {"2", "3", "4"}),
    ("date_max", {"1", "4"}),
    ("date_na", {"1", "2", "3"}),
    ("category", {"1", "3"}),
    ("company", {"2", "4"}),
]
CHECKBOX_FILTERS = {
    "colorado": "#coloradoOnlyBox",
    "metro": "#metroOnlyBox",
    "summer": "#summerOnlyBox",
    "sponsorship": "#noSponsorshipBtn",
    "category": '[data-cat-key="cat0"]',
    "company": "#hideCompanyBox",
}
SEARCH_TERMS = {
    "text": "mechanical",
    "title_search": "title:mechanical",
    "company_search": "company:acme",
    "location_search": 'loc:"denver"',
}
SUMMER_STORAGE_CASES = [
    ({"jobScoutSummer": "only"}, True),
    ({"jobScoutSummer": "all"}, False),
    ({"jobScoutSummer": "unknown"}, False),
    ({"jobScoutSummer": "only", "jobScoutSummerOnly": "0"}, False),
    ({"jobScoutSummerOnly": "1"}, True),
]


def queue_row(section, case_id, spec):
    stamp = (date.today() - timedelta(days=spec["age"])).isoformat() if spec["age"] is not None else ""
    return dict(
        id=f"{section}:{case_id}", company=spec["company"], role=spec["role"],
        location=spec["location"], link=f"https://example.com/{case_id}", source="test",
        state="auto_blocked" if section == "blocked" else "new", kw_hits=[],
        posted="" if case_id == "3" else stamp, first_seen=stamp,
        sponsorship_status="Blocked" if section == "blocked" else (
            "No Sponsorship" if spec["company"] == "Beta" else "Unclear"),
        closed_on=date.today().isoformat() if section == "closed" else None,
    )


@pytest.fixture
def generated_page(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(js, "HOME", source)
    monkeypatch.setattr(js, "HIDE_COMPANY", "Acme")
    companies = {}
    for case_id, spec in CASES.items():
        entry = queue_row("filtered", case_id, spec)
        job = dict(entry, id=case_id, title=entry["role"], url=entry["link"])
        rows, total = js._filtered_rows([job], [], dict(title_include=["intern"], title_exclude=["intern"]))
        assert total == 1
        company = companies.setdefault(spec["company"], dict(rows=[], n=0))
        company["rows"].extend(rows)
        company["n"] += total
    (source / "filtered.json").write_text(json.dumps(dict(companies=companies)), encoding="utf-8")
    queue = [queue_row(section, case_id, spec)
             for section in ("main", "blocked", "closed") for case_id, spec in CASES.items()]
    path = tmp_path / "index.html"
    js.write_queue_html(queue, path, closed_json=tmp_path / "closed.json", filtered_json=tmp_path / "filtered.json")
    return path


@pytest.fixture
def filter_page(generated_page):
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(generated_page.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(f"http://127.0.0.1:{server.server_port}/index.html")
                yield page
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def open_sections(page):
    page.locator("details:not([id]) > summary").click()
    for section in ("filteredLazy", "closedLazy"):
        page.locator(f"#{section} > summary").click()
        page.wait_for_function("id => document.querySelectorAll('#' + id + ' tbody tr').length === 4", arg=section)


def apply_control(page, control):
    if control in SEARCH_TERMS:
        page.locator("#filterBox").fill(SEARCH_TERMS[control])
        if control == "company_search":
            page.locator("#filterSearchBtn").click()
        else:
            page.locator("#filterBox").press("Enter")
    elif control in CHECKBOX_FILTERS:
        page.locator(CHECKBOX_FILTERS[control]).check()
    elif control == "date_min":
        page.locator("#dateMin").select_option("7")
    elif control == "date_max":
        page.locator("#dateMax").select_option("7")
    elif control == "date_na":
        page.locator("#dateIncludeNA").uncheck()
    else:
        raise AssertionError(control)


def expected_by_section(control, matching):
    return {section: set(CASES) if control == "sponsorship" and section in ("blocked", "filtered") else matching
            for section in SECTIONS}


def assert_rows(page, expected):
    for section, selector in SECTIONS.items():
        actual = page.locator(f"{selector} tbody tr:visible").evaluate_all(
            "rows => rows.map(row => row.dataset.jid)")
        assert set(actual) == expected[section], section
    assert page.locator("#filterCount").inner_text() == f"showing {sum(map(len, expected.values()))} of 16"


@pytest.mark.parametrize("control,matching", FILTER_CASES)
def test_controls_cover_all_loaded_tables(filter_page, control, matching):
    open_sections(filter_page)
    apply_control(filter_page, control)
    assert_rows(filter_page, expected_by_section(control, matching))
    filter_page.locator("#filterReset").click()
    for selector in SECTIONS.values():
        assert filter_page.locator(f"{selector} tbody tr:visible").count() == len(CASES)
    assert filter_page.locator("#filterCount").inner_text() == ""
    assert filter_page.locator("#filterBox").input_value() == ""
    assert filter_page.locator("#dateMin").input_value() == "0"
    assert filter_page.locator("#dateMax").input_value() == "inf"
    assert filter_page.locator("#dateIncludeNA").is_checked()
    for selector in CHECKBOX_FILTERS.values():
        assert not filter_page.locator(selector).is_checked()
    assert filter_page.evaluate("localStorage.getItem('jobScoutSummerOnly')") == "0"


@pytest.mark.parametrize("control,matching", FILTER_CASES)
def test_loading_with_active_filter(filter_page, control, matching):
    apply_control(filter_page, control)
    for section in ("filteredLazy", "closedLazy"):
        assert not filter_page.locator(f"#{section}").evaluate("details => details.open")
        assert filter_page.locator(f"#{section} tbody tr").count() == 0
    # Search opens matching eager details, but lazy sections remain user controlled.
    if not filter_page.locator("details:not([id])").evaluate("details => details.open"):
        filter_page.locator("details:not([id]) > summary").click()
    expected = expected_by_section(control, matching)
    total = 8
    shown = len(expected["main"]) + len(expected["blocked"])
    assert filter_page.locator("#filterCount").inner_text() == f"showing {shown} of {total}"
    for section, lazy_id in (("filtered", "filteredLazy"), ("closed", "closedLazy")):
        filter_page.locator(f"#{lazy_id} > summary").click()
        filter_page.wait_for_function("id => document.querySelectorAll('#' + id + ' tbody tr').length === 4", arg=lazy_id)
        total += 4
        shown += len(expected[section])
        assert filter_page.locator("#filterCount").inner_text() == f"showing {shown} of {total}"
        assert filter_page.locator(f"#{lazy_id}").evaluate("details => details.open")
    assert_rows(filter_page, expected)
    filter_page.locator("#filterReset").click()
    assert filter_page.locator("#filteredLazy tbody tr:visible").count() == 4
    assert filter_page.locator("#closedLazy tbody tr:visible").count() == 4


def test_combined_filters_and_reload(filter_page):
    open_sections(filter_page)
    for control in ("text", "colorado", "metro", "summer", "sponsorship", "category", "date_min"):
        apply_control(filter_page, control)
    assert_rows(filter_page, {section: {"3"} for section in SECTIONS})
    apply_control(filter_page, "company")
    assert_rows(filter_page, {section: set() for section in SECTIONS})
    filter_page.reload()
    open_sections(filter_page)
    assert filter_page.locator("#summerOnlyBox").is_checked()
    assert_rows(filter_page, {section: set() for section in SECTIONS})
    filter_page.locator("#filterReset").click()
    filter_page.reload()
    open_sections(filter_page)
    assert not filter_page.locator("#summerOnlyBox").is_checked()
    assert filter_page.locator("table tbody tr:visible").count() == 16


def test_search_respects_lazy_section_toggles(filter_page):
    open_sections(filter_page)
    apply_control(filter_page, "text")
    for lazy_id in ("filteredLazy", "closedLazy"):
        filter_page.locator(f"#{lazy_id} > summary").click()
    filter_page.locator("#filterSearchBtn").click()
    for lazy_id in ("filteredLazy", "closedLazy"):
        assert not filter_page.locator(f"#{lazy_id}").evaluate("details => details.open")
    assert filter_page.locator("#filterCount").inner_text() == "showing 8 of 16"


@pytest.mark.parametrize("storage,checked", SUMMER_STORAGE_CASES)
def test_summer_storage_migration(filter_page, storage, checked):
    filter_page.evaluate("values => { localStorage.clear(); Object.entries(values).forEach(([key, value]) => localStorage.setItem(key, value)); }", storage)
    filter_page.reload()
    assert filter_page.locator("#summerOnlyBox").is_checked() == checked
    assert filter_page.evaluate("localStorage.getItem('jobScoutSummerOnly')") == ("1" if checked else "0")
    filter_page.locator("#filterReset").click()
    filter_page.reload()
    assert not filter_page.locator("#summerOnlyBox").is_checked()


def test_sidecars_have_filter_metadata(generated_page):
    filtered = json.loads((generated_page.parent / "filtered.json").read_text(encoding="utf-8"))
    closed = json.loads((generated_page.parent / "closed.json").read_text(encoding="utf-8"))
    assert "<th>Posted</th>" in filtered["head"]
    for head, rows in ((filtered["head"], filtered["rows"]), (closed["head"], "".join(closed["rows"]))):
        assert 'data-posted="' in rows
        assert 'data-first-seen="' in rows
        assert 'data-summer="1"' in rows
        assert "<th>Location</th>" in head
    assert filtered["rows"].count('data-no-sponsorship="0"') == 4
    assert 'data-no-sponsorship="1"' in "".join(closed["rows"])
    expected_date = (date.today() - timedelta(days=10)).isoformat()
    assert f'data-posted="{expected_date}"' in filtered["rows"]
    html = generated_page.read_text(encoding="utf-8")
    assert 'id="summerOnlyBox"' in html
    assert "Summer 2027 only" in html


def test_legacy_filtered_rows_remain_undated(tmp_path, monkeypatch):
    monkeypatch.setattr(js, "HOME", tmp_path)
    legacy = ["legacy", "Mechanical Intern Summer 2027", "Denver, CO", "https://example.com", "title_exclude", "intern"]
    (tmp_path / "filtered.json").write_text(json.dumps(dict(companies=dict(Acme=dict(rows=[legacy], n=1)))), encoding="utf-8")
    js._filtered_section(tmp_path / "sidecar.json")
    rows = json.loads((tmp_path / "sidecar.json").read_text(encoding="utf-8"))["rows"]
    assert 'data-posted="" data-first-seen=""' in rows
    assert 'data-summer="1" data-no-sponsorship="0"' in rows
