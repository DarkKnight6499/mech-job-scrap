"""Summer intake checks apply to title, listing descriptions and enriched descriptions."""
import argparse
import json
from pathlib import Path

import pytest

import job_scout as js

FILTERS = json.loads((Path(__file__).parent / "data/config.json").read_text(encoding="utf-8"))["filters"]


def kept(title="Mechanical Intern", description=""):
    return js.matches(dict(title=title, desc=description, location="Boulder, CO"), FILTERS)


@pytest.mark.parametrize("title,description", [
    ("Mechanical Intern Summer 2027", ""), ("Mechanical Intern", "Summer 2027 opportunity."),
    ("Mechanical Intern 2027", ""), ("Mechanical Intern", ""), ("Mechanical Intern", "Summer opportunity."),
])
def test_target_or_unspecified_year_passes(title, description):
    assert kept(title, description)


@pytest.mark.parametrize("title,description", [
    ("Mechanical Intern Summer 2026", ""), ("Mechanical Intern Summer 2028", ""),
    ("Mechanical Intern Fall 2026", ""), ("Mechanical Intern Spring 2027", ""),
    ("Mechanical Intern Winter 2027", ""), ("Mechanical Intern", "Summer 2028."),
    ("Mechanical Intern Summer 2027", "Program runs in 2026."),
    ("Mechanical Intern", "Autumn 2027 placement."), ("Mechanical Intern", "Spring placement."),
    ("Mechanical Intern", "Summer 2027. Graduation in 2028."),
])
def test_other_years_or_seasons_fail(title, description):
    assert not kept(title, description)


def test_description_alias_is_checked():
    assert not js.matches(dict(title="Mechanical Intern", description="Summer 2028", location="CO"), FILTERS)


def test_phd_only_description_fails_but_preference_passes():
    assert not kept(description="Ph.D. required")
    assert kept(description="BS or MS students welcome; PhD preferred.")


def test_target_year_and_season_are_configurable():
    filters = dict(FILTERS, internship_year=2028, internship_season="fall")
    job = dict(title="Mechanical Intern", desc="Fall 2028", location="CO")
    assert js.matches(job, filters)
    assert not js.matches(dict(job, desc="Summer 2028"), filters)


@pytest.mark.parametrize("description,expected", [("Summer 2028.", 0), ("Summer 2027.", 1), ("", 1)])
def test_enriched_description_checked_before_queue_and_alert(monkeypatch, description, expected):
    notifications = []
    monkeypatch.setattr(js, "notify", lambda *args: notifications.append(args) or True)
    job = dict(id="1", title="Mechanical Intern", location="Boulder, CO", url="https://example.com/1", posted="")
    queue, state, ids = [], {}, set()
    counts = dict(matched=0, queued=0, blocked=0, reposts=0, alerted=0)
    js._process_company(
        dict(name="Acme", ats="greenhouse"), "Acme", [job], {"1": description},
        False, [job], True, set(), state, queue, ids, [],
        dict(filters=FILTERS, notify={}), argparse.Namespace(dry_run=False), counts,
    )
    assert len(queue) == len(notifications) == counts["matched"] == expected
    assert state["Acme"] == ["1"]


def test_summer_page_marker():
    assert js._SUMMER_2027_RE.search("Mechanical Intern Summer 2027")
    assert not js._SUMMER_2027_RE.search("Mechanical Intern Spring 2027")


@pytest.mark.parametrize("description", ["Summer2026", "Summer2028", "Spring2027", "Fall2027"])
def test_compact_season_years_fail(description):
    assert not kept(description=description)


def test_compact_target_season_year_passes():
    assert kept(description="Summer2027")


def test_recovered_description_closes_wrong_season_and_cancels_alert(monkeypatch):
    monkeypatch.setattr(js, "describe", lambda company, job: ("Summer 2028 internship.", "", ""))
    entry = dict(id="Acme:1", company="Acme", role="Mechanical Intern", location="CO",
                 link="https://example.com/1", posted="", state="new", closed_on=None,
                 description_status="failed", alert_pending=True)
    config = dict(filters=FILTERS, companies=[dict(name="Acme", ats="greenhouse", slug="acme")])
    js._retry_enrichment([entry], config, [])
    assert entry["closed_on"] and entry["closed_reason"] == "filters"
    assert not entry["alert_pending"]
