"""Title dates control intake; description exclusions also apply after enrichment."""
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
    ("Mechanical Intern", "Summer 2028."),
    ("Mechanical Intern Summer 2027", "Program runs in 2026."),
    ("Mechanical Intern", "Autumn 2027 placement."), ("Mechanical Intern", "Spring placement."),
    ("Mechanical Intern", "Summer 2027. Graduation in 2028."),
])
def test_target_or_unspecified_year_passes(title, description):
    assert kept(title, description)


@pytest.mark.parametrize("title,description", [
    ("Mechanical Intern Summer 2026", ""), ("Mechanical Intern Summer 2028", ""),
    ("Mechanical Intern Fall 2026", ""), ("Mechanical Intern Spring 2027", ""),
    ("Mechanical Intern Winter 2027", ""),
])
def test_other_years_or_seasons_fail(title, description):
    assert not kept(title, description)


def test_description_alias_dates_do_not_reject():
    assert js.matches(dict(title="Mechanical Intern", description="Summer 2028", location="CO"), FILTERS)


def test_phd_only_description_fails_but_preference_passes():
    assert not kept(description="Ph.D. required")
    assert kept(description="BS or MS students welcome; PhD preferred.")


def test_target_year_and_season_are_configurable():
    filters = dict(FILTERS, title_exclude=[], internship_year=2028, internship_season="fall")
    job = dict(title="Mechanical Intern Fall 2028", desc="Summer 2026", location="CO")
    assert js.matches(job, filters)
    assert not js.matches(dict(job, title="Mechanical Intern Summer 2028"), filters)
    assert not js.matches(dict(job, title="Mechanical Intern Fall 2027"), filters)


@pytest.mark.parametrize("description,expected", [
    ("Summer 2028.", 1), ("Summer 2027.", 1), ("", 1),
    ("Fall 2026. Graduating 2028.", 1), ("Ph.D. required", 0),
])
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


@pytest.mark.parametrize("season_year", ["Summer2026", "Summer2028", "Spring2027", "Fall2027"])
def test_compact_title_season_years_fail(season_year):
    assert not kept(title=f"Mechanical Intern {season_year}")


def test_compact_target_season_year_passes():
    assert kept(title="Mechanical Intern Summer2027")


@pytest.mark.parametrize("description,rejected", [
    ("Summer 2028 internship.", False), ("Winter 2026; graduating 2028.", False),
    ("Ph.D. required", True),
])
def test_recovered_description_only_closes_for_description_exclusions(monkeypatch, description, rejected):
    monkeypatch.setattr(js, "describe", lambda company, job: (description, "", ""))
    entry = dict(id="Acme:1", company="Acme", role="Mechanical Intern", location="CO",
                 link="https://example.com/1", posted="", state="new", closed_on=None,
                 description_status="failed", alert_pending=True)
    config = dict(filters=FILTERS, companies=[dict(name="Acme", ats="greenhouse", slug="acme")])
    js._retry_enrichment([entry], config, [])
    if rejected:
        assert entry["closed_on"] and entry["closed_reason"] == "filters"
        assert not entry["alert_pending"]
    else:
        assert entry["closed_on"] is None and entry["alert_pending"]
        assert entry["description_status"] == "ok"


@pytest.mark.parametrize("title", ["Mechanical Intern", "Mechanical Intern Summer 2027"])
@pytest.mark.parametrize("field", ["desc", "description"])
@pytest.mark.parametrize("description", [
    "Fall rotations available.", "Winter break availability.", "Spring coursework required.",
    "Autumn intake also available.", "Applications opened in 2026.", "Graduating 2028.",
    "Summer2026 and Winter2028 programs.", "Summer 2027 or Fall 2027.",
])
def test_description_seasons_and_years_do_not_reject(title, field, description):
    listing = dict(title=title, location="CO", **{field: description})
    assert js.internship_filter_reason(listing, FILTERS) is None
    assert js.title_filter_reason(listing, FILTERS) is None
    assert js.matches(listing, FILTERS)


@pytest.mark.parametrize("field", ["title", "desc", "description"])
def test_description_exclusions_still_scan_every_text_field(field):
    listing = dict(title="Mechanical Intern Summer 2027", location="CO")
    listing[field] = listing.get(field, "") + " Ph.D. required"
    assert js.internship_filter_reason(listing, FILTERS) == ("description_exclude", "ph.d. required")
    assert not js.matches(listing, FILTERS)
