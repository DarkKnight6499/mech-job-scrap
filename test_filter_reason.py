"""Audit reasons follow the same candidate and rejection logic as intake."""
import json
from pathlib import Path

import pytest

import job_scout as js
import filter_audit as fa

FILTERS = json.loads((Path(__file__).parent / "data/config.json").read_text(encoding="utf-8"))["filters"]


def test_reasons_agree_with_matches():
    for title in ("Mechanical Intern", "Senior Mechanical Intern", "Software Design Engineer Intern",
                  "Mechanical Intern Spring 2027", "Mechanical Intern Summer 2028"):
        job = dict(title=title, location="CO")
        reason = js.title_filter_reason(job, FILTERS)
        assert bool(reason) == (not js.matches(job, FILTERS))


def test_names_rule_and_ignores_non_candidates():
    assert js.title_filter_reason(dict(title="Senior Mechanical Intern"), FILTERS) == ("title_exclude", "senior")
    assert js.title_filter_reason(dict(title="Warehouse Operator"), FILTERS) is None
    assert js.title_filter_reason(dict(title="Mechanical Engineer"), FILTERS) is None


def test_filtered_rows_skip_hits_non_candidates_and_foreign_locations():
    jobs = [
        dict(id="1", title="Mechanical Intern", location="CO"),
        dict(id="2", title="Senior Mechanical Intern", location="CO"),
        dict(id="3", title="Senior Mechanical Intern", location="Toronto, Canada"),
        dict(id="4", title="Warehouse Operator", location="CO"),
    ]
    hits = [job for job in jobs if js.matches(job, FILTERS)]
    rows, total = js._filtered_rows(jobs, hits, FILTERS)
    assert [row[0] for row in rows] == ["2"] and total == 1
    assert rows[0][4] == "title_exclude"


def test_audit_flags_engineering_rule_once():
    data = {"companies": {"Acme": {"n": 2, "rows": [
        ["1", "Mechanical Intern", "CO", "u1", "title_exclude", "mechanical"],
        ["2", "Senior Mechanical Intern", "CO", "u2", "title_exclude", "senior"],
    ]}}}
    flagged, counts = fa.audit(data, set())
    assert [item[1][0] for item in flagged] == ["1"]
    assert counts == {"mechanical": 1, "senior": 1}
    assert not fa.audit(data, {"Acme:1"})[0][0][3]


@pytest.mark.parametrize("intake,expected", [
    ("Summer 2026", ("internship_year", "2026")),
    ("Summer 2028", ("internship_year", "2028")),
    ("2026-2028", ("internship_year", "2026")),
    ("2026-2027", None), ("2027-2028", None), ("2026 / 2027 / 2028", None),
    ("Summer 2027 (class of 2028)", None), ("Summer 2027 (graduating 2028)", None),
    ("Summer2027 (class of 2028)", None), ("Summer", None), ("2027", None), ("", None),
    ("Spring 2027", ("internship_season", "spring")),
    ("Fall 2027", ("internship_season", "fall")),
    ("Winter/Spring 2027", ("internship_season", "winter")),
    ("Fall Co-op", ("internship_season", "fall")),
    ("Summer/Fall 2027", None), ("Spring & Summer 2027", None),
    ("Spring/Summer 2027", None), ("Summer 2027 or Fall 2027", None),
])
def test_title_date_reasons_use_target_presence(intake, expected):
    filters = dict(internship_year=2027, internship_season="summer")
    listing = dict(title=f"Mechanical Intern {intake}", desc="Summer 2027; graduating 2028.", location="CO")
    assert js.internship_filter_reason(listing, filters) == expected
    assert js.title_filter_reason(listing, filters) == expected
    assert js.matches(listing, filters) == (expected is None)


def test_description_target_cannot_rescue_wrong_title_dates():
    filters = dict(internship_year=2027, internship_season="summer")
    assert js.internship_filter_reason(dict(title="Mechanical Intern 2028", description="Summer 2027"), filters) == (
        "internship_year", "2028")
    assert js.internship_filter_reason(dict(title="Mechanical Intern Winter 2027", description="Summer 2027"), filters) == (
        "internship_season", "winter")
