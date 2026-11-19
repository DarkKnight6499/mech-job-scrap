"""Engineering internship title requirements use alternatives within required groups."""
import json
from pathlib import Path

import pytest

import job_scout as js

FILTERS = json.loads((Path(__file__).parent / "data/config.json").read_text(encoding="utf-8"))["filters"]


def job(title, **fields):
    return dict(title=title, location="Boulder, CO", **fields)


def kept(title, filters=FILTERS):
    return js.matches({"title": title, "location": "Boulder, CO"}, filters)


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern", "Mechatronics Student", "Aerospace Co-op",
    "Summer 2027 Robotics Engineer", "Controls Engineering Internship",
    "Automation Intern", "Electromechanical Intern", "Hardware Intern",
    "Design Engineering Intern", "Test Engineer Intern", "Manufacturing Engineering Intern",
    "Process Engineering Intern", "Materials Intern", "Thermal Intern", "Fluids Intern",
    "Structures Intern", "Propulsion Intern", "Systems Engineering Intern", "R&D Intern",
    "Product Development Intern", "CAD Intern", "Quality Engineering Intern",
    "Project Engineering Intern", "Reliability Intern", "Water Treatment Intern",
    "Membrane Research Intern", "UAV Intern", "Drone Intern", 
    "Field Engineering Intern",
    "Applications Engineer Intern", 
    "Control Systems Co Op", "Robotics Coop", "Product Manager Intern", "Project Management Intern", "Polymer Science Intern", "Materials Science Intern", "Fabrication Engineer Intern", "Mechanical Designer Intern", "Research and Development Intern",
])
def test_engineering_internships_pass(title):
    assert kept(title)


@pytest.mark.parametrize("title", [
    "Mechanical Engineer", "Internal Controls Analyst", "International Aerospace Engineer",
    "Student Ambassador", "Summer 2027 Marketing Intern", "Finance Intern",
    "Software Engineer Intern", "Software Design Engineer Intern", "Senior Mechanical Intern",
    "Staff Robotics Intern", "Principal Mechanical Intern",
    "Director of Aerospace", "Mechanical MBA Intern",
    "Mechanical PhD-only Intern", "Mechanical Ph.D. only Intern",
    "Sales Applications Engineer Intern", "HR Systems Engineer Intern",
])
def test_wrong_roles_fail(title):
    assert not kept(title)


def test_groups_are_optional_and_configurable():
    filters = {"title_include": ["mechanical"], "title_require_all_groups": [["student"], ["mechanical", "hardware"]]}
    assert kept("Mechanical Student", filters)
    assert not kept("Mechanical Intern", filters)
    assert kept("Mechanical Engineer", {"title_include": ["mechanical"]})
    assert not kept("Hardware Student", filters)


def test_season_marker_does_not_bypass_engineering_or_exclusions():
    assert not kept("Summer 2027 Student")
    assert not kept("Summer 2027 Senior Mechanical Engineer")


def test_engineering_aliases_do_not_match_inside_other_words():
    assert not kept("Scad Intern")
    assert not kept("International Mechanical Engineer")


def test_search_terms_use_includes_or_first_required_group(monkeypatch):
    monkeypatch.setattr(js, "TITLE_TERMS", [])
    js._load_title_terms(dict(filters=dict(title_require_all_groups=[["intern", "student"], ["mechanical"]])))
    assert js._terms(dict(search=True)) == ["intern", "student"]
    js._load_title_terms(dict(filters=dict(title_include=["hardware", "hardware", "mechanical"])))
    assert js._terms(dict(search=True)) == ["hardware", "mechanical"]


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern (Year Round)", "Co-op, Hardware Development Engineer (Jan - July 2027)",
    "Fall 2027 Mechanical Intern", "Spring Robotics Co-op", "Winter Aerospace Intern",
    "Manufacturing Engineering Semester Intern",
])
def test_non_summer_terms_fail(title):
    assert not kept(title)


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern", "Summer 2027 Materials Intern", "2027 Summer Intern - Process Engineer",
    "Aerospace Co-op", "Mechanical Intern 2026-2027", "Mechanical Intern 2027-2028",
    "Mechanical Intern Summer 2027 (class of 2028)", "Mechanical Intern Summer 2027 (graduating 2028)",
])
def test_summer_or_undated_pass(title):
    assert kept(title)


@pytest.mark.parametrize("intake", [
    "Summer/Fall 2027", "Spring & Summer 2027", "Spring/Summer 2027",
    "Summer 2027 or Fall 2027", "Winter/Summer 2027", "Summer/Autumn 2027",
    "Summer Semester 2027", "SUMMER / FALL 2027", "Spring 2028 / Summer 2027",
    "Fall 2026 / Summer 2027", "Summer2027 / Winter2027",
])
def test_summer_waives_only_season_title_exclusions(intake):
    assert kept(f"Mechanical Intern {intake}")


@pytest.mark.parametrize("intake", [
    "Spring 2027", "Fall 2027", "Winter/Spring 2027", "Fall Co-op",
    "Autumn 2027", "Semester 2027", "Winter2027/Spring2027",
])
def test_non_summer_intakes_still_reject(intake):
    assert not kept(f"Mechanical Intern {intake}")


@pytest.mark.parametrize("term", [
    "Year Round", "Year-Round", "Yearround", "Senior", "MBA Intern", "High School",
    "Jan - July", "Spring Analyst", "Fall Co-op", "Winter Research",
])
def test_summer_preserves_other_title_exclusions(term):
    filters = dict(FILTERS, title_exclude=["spring", term])
    assert not kept(f"Mechanical Intern Spring / Summer 2027 {term}", filters)


@pytest.mark.parametrize("term", [
    "spring", "fall", "autumn", "winter", "semester",
    "spring 2027", "fall 2027", "winter 2027", "autumn 2028", "fall 2026",
])
def test_default_waiver_accepts_season_words_and_season_year_entries(term):
    filters = dict(FILTERS, title_exclude=[term])
    filters.pop("season_words_waived_by_summer", None)
    assert kept(f"Mechanical Intern Summer 2027 / {term}", filters)


def test_season_waiver_list_is_configurable():
    filters = dict(FILTERS, title_exclude=["spring", "fall"], season_words_waived_by_summer=["FALL"])
    assert kept("Mechanical Intern Summer/Fall 2027", filters)
    assert not kept("Mechanical Intern Spring/Summer 2027", filters)
    assert not kept("Mechanical Intern Summer/Fall 2027", dict(filters, season_words_waived_by_summer=[]))
    filters = dict(filters, title_exclude=["fall 2027", "fall 2028"], season_words_waived_by_summer=["fall 2027"])
    assert kept("Mechanical Intern Summer 2027 / Fall 2027", filters)
    assert not kept("Mechanical Intern Summer 2027 / Fall 2028", filters)


@pytest.mark.parametrize("term", ["year round", "senior", "spring analyst", "fall co-op", "summer 2028"])
def test_waiver_list_cannot_disable_non_season_exclusions(term):
    filters = dict(FILTERS, title_exclude=[term], season_words_waived_by_summer=[term])
    assert not kept(f"Mechanical Intern Summer 2027 {term}", filters)


def test_description_summer_cannot_waive_title_exclusions():
    assert not js.matches(job("Mechanical Intern Fall 2027", desc="Summer 2027 also offered."), FILTERS)
    assert not kept("Mechanical Intern Spring Summertime 2027")


def test_summer_waiver_preserves_conditional_exclusions_and_candidate_groups():
    assert not kept("Software Engineering Intern Summer/Fall 2027")
    assert not kept("Mechanical Engineer Summer/Fall")
    assert not kept("Marketing Intern Summer/Fall 2027")
