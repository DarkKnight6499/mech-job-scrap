"""US-only evidence checks retain generic location exclusions and Workday fallback."""
import pytest

import job_scout as js
from test_title_filters import FILTERS, job


def kept(location):
    posting = job("Mechanical Intern")
    posting["location"] = location
    return js.matches(posting, FILTERS)


@pytest.mark.parametrize("location", [
    "Boulder, CO", "Denver, Colorado", "Los Angeles, CA", "Seattle, WA", "Austin, TX",
    "US-NJ-Princeton-100-Headquarters", "Office - USA - CA - Headquarters", "United States",
    "Remote - US", "Remote US", "US Remote", "Remote, U.S.", "Remote (USA)",
    "Indianapolis, IN", "Newark, DE", "Ontario, CA", "Vancouver, WA", "Dublin, OH",
    "Athens, GA", "Albuquerque, New Mexico", "Washington D.C.", "boulder, co",
    "Perth Amboy, NJ", "Georgia, United States", "Boston, MA, US, 02110",
])
def test_us_locations_kept(location):
    assert kept(location)


@pytest.mark.parametrize("location", [
    "", "Remote", "Hybrid", "Remote or hybrid", "Work in office", "Global", "Worldwide",
    "Toronto, ON", "Toronto, Canada", "London, UK", "Munich, Germany", "Bengaluru, India",
    "Sydney, Australia", "Perth, WA, AU", "Vancouver, BC", "Vancouver", "Dublin, Ireland",
    "Mexico City, Mexico", "CAN - Toronto", "IND HYDB 18-23 OB3", "CA-ON-Toronto",
    "Montreal, QC, H2B 1X9", "Paris, France", "Bogota, Colombia", "New Delhi, IN",
    "Headquarters", "Tbilisi, Georgia", "Cambridge, MA, United Kingdom",
])
def test_foreign_or_unqualified_locations_rejected(location):
    assert not kept(location)


def test_all_configured_state_names_and_codes_match():
    includes = FILTERS["locations_include"]
    for marker in ("Alaska", "Hawaii", "Rhode Island", "West Virginia", "NH", "WY", "OR", "IN"):
        assert marker in includes and kept(marker)


def test_multi_site_requires_at_least_one_us_site():
    assert kept("Toronto, Canada; Boulder, CO")
    assert kept("London, UK | Austin, TX")
    assert not kept("London, UK; Toronto, Canada")


def test_blank_location_recovers_workday_site_from_url_or_link():
    posting = job("Mechanical Intern")
    posting["location"] = ""
    for field in ("url", "link"):
        posting[field] = "https://example.wd1.myworkdayjobs.com/Careers/job/Boulder-Colorado/Intern_R1"
        assert js.matches(posting, FILTERS)
        posting[field] = "https://example.wd1.myworkdayjobs.com/Careers/job/Toronto-Canada/Intern_R1"
        assert not js.matches(posting, FILTERS)
        posting.pop(field)


def test_drop_location_filtered_keeps_us_and_acted_on_rows():
    queue = [dict(id="a", state="new", location="Remote"),
             dict(id="b", state="new", location="Boulder, CO"),
             dict(id="c", state="applied", location="Toronto, Canada")]
    counts = {}
    js._drop_location_filtered(queue, FILTERS, counts)
    assert [entry["id"] for entry in queue] == ["b", "c"]
    assert counts["location_dropped"] == 1


def test_legacy_substring_location_filters_remain_available():
    filters = dict(locations_include=[", nj"])
    assert js.matches(dict(title="Example", location="Princeton, NJ"), filters)
    assert not js.matches(dict(title="Example", location="Boston, MA"), filters)


def test_workday_rescues_us_site_hidden_behind_foreign_first_site(tmp_path, monkeypatch):
    monkeypatch.setattr(js, "MULTISITE_CACHE", tmp_path / "sites.json")
    monkeypatch.setattr(js.time, "sleep", lambda seconds: None)

    def describe(company, posting):
        posting["location"] = "Toronto, Canada; Boulder, CO"
        return "Summer 2027 opportunity.", "", ""

    monkeypatch.setattr(js, "describe", describe)
    posting = dict(id="1", title="Mechanical Intern", location="2 Locations (Toronto, Canada)")
    rescued = js._rescue_multi_site(dict(name="Acme", ats="workday"), [posting], [], FILTERS)
    assert len(rescued) == 1
    assert js.matches(rescued[0], FILTERS)
