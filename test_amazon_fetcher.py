"""Offline Amazon API tests using a saved search response and mocked HTTP."""
import json
from pathlib import Path
import urllib.error
from urllib.parse import parse_qs, urlsplit
from unittest import mock

import pytest

import job_scout as js
import validate_config as vc


# Test configuration.
SAMPLE_PATH = Path(__file__).resolve().parent / "fixtures" / "amazon_search_sample.json"
COMPANY = dict(name="Amazon", ats="amazon", search=["intern", "internship", "co-op"],
               country="USA", max_per_term=200)
DETAIL_HTML = ('<html><script>{"datePosted":"2026-11-14"}</script><style>hidden</style>'
               '<body><p>Build &amp; test.</p><h2>Basic qualifications</h2><p>Engineering degree.</p>'
               '<h2>Preferred qualifications</h2><p>CAD experience.</p></body></html>')


@pytest.fixture(autouse=True)
def no_live_http(monkeypatch):
    monkeypatch.setattr(js, "TITLE_TERMS", [])
    with mock.patch.object(js, "http", side_effect=AssertionError("HTTP must be mocked")):
        yield


@pytest.fixture
def sample():
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


def search_http(pages, calls):
    def fake(url, **kwargs):
        parsed = urlsplit(url)
        assert parsed.scheme == "https" and parsed.netloc == "www.amazon.jobs"
        assert parsed.path == "/en/search.json"
        query = parse_qs(parsed.query, keep_blank_values=True)
        assert set(query) == {"base_query", "country", "result_limit", "offset", "sort"}
        assert query["result_limit"] == ["100"] and query["sort"] == ["recent"]
        assert query["country"] == ["USA"]
        key = (query["base_query"][0], int(query["offset"][0]))
        calls.append(key)
        return pages[key]
    return fake


def test_sample_parsing_and_fetch_company_contract(sample):
    payload = dict(sample, hits=len(sample["jobs"]))
    calls = []
    with mock.patch.object(js, "http", search_http({("intern", 0): payload}, calls)):
        name, jobs, complete, error = js.fetch_company(dict(COMPANY, search=["intern"]))
    assert (name, complete, error) == ("Amazon", True, None)
    assert calls == [("intern", 0)] and len(jobs) == 4
    assert [job["id"] for job in jobs] == [row["id_icims"] for row in sample["jobs"]]
    assert jobs[0]["id"] == "10605141"
    assert jobs[0]["title"] == "Data Center Infrastructure Engineer Intern, Summer 2027 - East"
    assert jobs[0]["location"] == "Herndon, Virginia, USA"
    assert jobs[0]["url"] == "https://www.amazon.jobs" + sample["jobs"][0]["job_path"]
    assert jobs[0]["posted"] == "2026-11-14" and jobs[-1]["posted"] == "2026-11-13"


def test_merge_across_terms_by_icims_id(sample):
    rows = sample["jobs"]
    pages = {("intern", 0): dict(hits=3, jobs=[rows[0], rows[0], rows[1]]),
             ("internship", 0): dict(hits=2, jobs=[dict(rows[0], title="Duplicate"), rows[2]]),
             ("co-op", 0): dict(hits=2, jobs=[rows[2], rows[3]])}
    calls = []
    with mock.patch.object(js, "http", search_http(pages, calls)):
        jobs, complete = js.amazon(COMPANY)
    assert complete and len(jobs) == 4
    assert calls == [(term, 0) for term in COMPANY["search"]]
    assert [job["id"] for job in jobs] == [row["id_icims"] for row in rows]
    assert jobs[0]["title"] == rows[0]["title"]


@pytest.mark.parametrize("total,ceiling,expected_count,complete,offsets", [
    (205, 200, 200, False, [0, 100]),
    (200, 200, 200, True, [0, 100]),
    (150, 125, 125, False, [0, 100]),
    (150, 200, 150, True, [0, 100]),
    (0, 200, 0, True, [0]),
])
def test_pagination_and_ceiling(sample, total, ceiling, expected_count, complete, offsets):
    rows = [dict(sample["jobs"][0], id_icims=str(i)) for i in range(total)]
    pages = {("intern", offset): dict(hits=total, jobs=rows[offset:offset + 100]) for offset in offsets}
    calls = []
    with mock.patch.object(js, "http", search_http(pages, calls)):
        jobs, actual_complete = js.amazon(dict(COMPANY, search=["intern"], max_per_term=ceiling))
    assert len(jobs) == expected_count and actual_complete is complete
    assert [offset for term, offset in calls] == offsets
    assert [job["id"] for job in jobs] == [str(i) for i in range(expected_count)]


def test_duplicate_page_from_previous_term_does_not_stop_pagination(sample):
    rows = [dict(sample["jobs"][0], id_icims=str(i)) for i in range(105)]
    pages = {("intern", 0): dict(hits=100, jobs=rows[:100]),
             ("internship", 0): dict(hits=105, jobs=rows[:100]),
             ("internship", 100): dict(hits=105, jobs=rows[100:])}
    calls = []
    with mock.patch.object(js, "http", search_http(pages, calls)):
        jobs, complete = js.amazon(dict(COMPANY, search=["intern", "internship"]))
    assert complete and len(jobs) == 105 and calls[-1] == ("internship", 100)


def test_one_capped_term_keeps_merged_result_incomplete(sample):
    rows = [dict(sample["jobs"][0], id_icims=str(i)) for i in range(100)]
    pages = {("intern", 0): dict(hits=101, jobs=rows),
             ("internship", 0): dict(hits=1, jobs=sample["jobs"][:1])}
    calls = []
    with mock.patch.object(js, "http", search_http(pages, calls)):
        jobs, complete = js.amazon(dict(COMPANY, search=["intern", "internship"], max_per_term=100))
    assert not complete and len(jobs) == 101 and len(calls) == 2


def test_premature_empty_page_is_incomplete(sample):
    calls = []
    pages = {("intern", 0): sample, ("intern", 4): dict(hits=sample["hits"], jobs=[])}
    with mock.patch.object(js, "http", search_http(pages, calls)):
        jobs, complete = js.amazon(dict(COMPANY, search=["intern"]))
    assert len(jobs) == 4 and not complete
    assert calls == [("intern", 0), ("intern", 4)]


@pytest.mark.parametrize("posted,expected", [
    ("November 14, 2026", "2026-11-14"), ("January 1, 2027", "2027-01-01"),
    ("February 30, 2026", ""), ("not a date", ""), (None, ""),
])
def test_date_parsing_and_location_fallback(sample, posted, expected):
    row = dict(sample["jobs"][0], posted_date=posted, normalized_location=None)
    with mock.patch.object(js, "http", return_value=dict(hits=1, jobs=[row])):
        jobs, complete = js.amazon(dict(COMPANY, search=["intern"]))
    assert complete and jobs[0]["posted"] == expected
    assert jobs[0]["location"] == "US, VA, Herndon"


def test_description_includes_all_search_text_without_detail_fetch(sample):
    row = sample["jobs"][0]
    with mock.patch.object(js, "http", return_value=dict(hits=1, jobs=[row])) as request:
        jobs, complete = js.amazon(dict(COMPANY, search=["intern"]))
        text, posted, source = js.describe(COMPANY, jobs[0])
    assert complete and request.call_count == 1
    assert (posted, source) == ("", "")
    assert "Shape what comes next" in text
    assert "Knowledge of Power Systems, Fluid Dynamics, or Thermodynamics" in text
    assert "Experience using a variety of web-based and other software tools" in text
    assert text.index("Shape what comes next") < text.index("Knowledge of Power Systems")
    assert text.index("Knowledge of Power Systems") < text.index("Experience using a variety")
    assert "<br" not in text and "<a " not in text and "<p>" not in text


def test_describe_queue_row_fetches_detail_text():
    with mock.patch.object(js, "http", return_value=DETAIL_HTML.encode()) as request:
        result = js.describe(COMPANY, dict(id="10605141"))
    assert result == ("Build & test. Basic qualifications Engineering degree. Preferred qualifications CAD experience.",
                      "2026-11-14", "exact")
    request.assert_called_once_with("https://www.amazon.jobs/en/jobs/10605141", raw=True, timeout=40)


def test_registration_validation_and_sharding():
    assert js.FETCH["amazon"] is js.amazon and vc.REQUIRED_FIELDS["amazon"] == ()
    assert vc.validate({"companies": [dict(name="Amazon", ats="amazon")]}, []) == ([], [])
    assert vc.validate({"companies": [COMPANY]}, []) == ([], [])
    assert js._fetch_cost(COMPANY) == 6
    assert js.shard_companies([COMPANY], 0, 2) == [COMPANY]
    assert js.shard_companies([COMPANY], 1, 2) == []


@pytest.mark.parametrize("status,expected", [(200, True), (404, False), (410, False), (429, True), (500, True)])
def test_liveness_detail_probe(status, expected):
    error = urllib.error.HTTPError(js.AMAZON_JOB_URL, status, "error", {}, None)
    kwargs = {"return_value": DETAIL_HTML.encode()} if status == 200 else {"side_effect": error}
    with mock.patch.object(js, "http", **kwargs) as request:
        assert js._still_listed(COMPANY, dict(id="Amazon:10605141")) is expected
    request.assert_called_once_with("https://www.amazon.jobs/en/jobs/10605141", raw=True, timeout=40)


def test_liveness_keeps_search_miss_open_when_detail_is_live(monkeypatch):
    row = dict(id="Amazon:10605141", company="Amazon", state="new", closed_on=None,
               last_seen_live="2020-01-01", miss_count=js.CLOSE_AFTER_MISSES - 1)
    counts = dict(closed=0, reopened=0)
    monkeypatch.setattr(js, "_still_listed_budgeted", lambda company, entry: True)
    js._update_liveness("Amazon", [dict(id="other")], True, [row], counts, COMPANY)
    assert row["closed_on"] is None and row["miss_count"] == 0 and counts["closed"] == 0
