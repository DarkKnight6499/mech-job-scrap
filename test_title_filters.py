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
    "Membrane Research Intern", "UAV Intern", "Drone Intern", "Avionics Intern",
    "Embedded Intern", "Electrical Engineering Intern", "Field Engineering Intern",
    "Applications Engineer Intern", "Software Engineer Intern - Embedded Hardware",
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
    "Aerospace Co-op",
])
def test_summer_or_undated_pass(title):
    assert kept(title)
