import json

import pytest

import job_scout as js

F = json.load(open("data/config.json", encoding="utf8"))["filters"]


def reason(title):
    return js.title_filter_reason({"title": title}, F)


@pytest.mark.parametrize("title", [
    "Manufacturing Engineering Intern (Jan 2027)",
    "Product Engineering Co-Op, Jan-June 2027",
    "Process Engineering Co-Op (Jan-Aug)",
    "Mechanical Engineering Co-Op (August - December 2027)",
    "Mechanical Engineering Co-Op (March - August 2027)",
    "Mechanical Engineering Co-op (Spring/Summer 2027)",
    "Mechanical Engineering Intern Spring and Summer 2027",
    "Mechanical Engineer PhD Intern",
    "Mechanical Engineering Intern - PhD",
    "Postdoctoral Mechanical Engineering Intern",
])
def test_rejected(title):
    assert reason(title) is not None


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern Summer 2027", "Mechanical Engineering Intern (May-August 2027)",
    "Mechanical Engineering Intern (May-Aug '27)", "Process Engineering Intern - MS/PhD",
    "Mechanical Engineering Intern - BS, MS or PhD", "Mechanical Engineering Intern Summer Semester 2027",
    "Mechanical Engineering Intern (June - August 2027)",
    "Validation Engineering Co-op (May-December)", "Mechanical Engineering Co-Op (June - December 2027)",
    "Mechanical Reliability Co-Op (July - Dec) 2027", "Reliability Co-Op (June \u2013 Dec '27) Engineering",
    "Mechanical Engineering Co-op (Summer/Fall 2027)",
])
def test_kept(title):
    assert reason(title) is None


@pytest.mark.parametrize("location,kept", [
    ("Milton, Ontario, CA", False), ("Ontario, CA", True), ("Ontario, California", True), ("Indianapolis, Indiana", True),
])
def test_ontario(location, kept):
    assert js._location_matches(location, F) is kept


def test_drop_title_filtered_spares_marked_rows():
    queue = [{"state": s, "role": "Electrical Engineering Intern Summer 2027"}
             for s in ("new", "opt_only", "auto_blocked", "applied", "shortlisted", "dismissed")]
    queue.append({"state": "new", "role": "Mechanical Engineering Intern Summer 2027"})
    counts = {}
    js._drop_title_filtered(queue, F, counts)
    assert [e["state"] for e in queue] == ["applied", "shortlisted", "dismissed", "new"]
    assert counts["title_dropped"] == 3


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Undergraduate Intern", "Materials Engineering Intern - Bachelors",
    "Mechanical Engineering Intern (Bachelor's)", "Manufacturing Engineering Intern - Sophomore",
    "Mechanical Engineering Intern - Junior", "Post Undergraduate Mechanical Engineering Intern",
])
def test_undergrad_only_rejected(title):
    assert reason(title) == ("description_exclude", "undergrad-only title")


@pytest.mark.parametrize("title", [
    "Undergraduate/Graduate Mechanical Engineering Intern", "Mechanical Engineer Intern - BS or MS",
    "Mechanical Engineering Intern - Bachelors/Masters", "Undergrad or Grad Materials Intern",
    "Graduate Mechanical Engineering Intern",
])
def test_graduate_open_kept(title):
    assert reason(title) is None


@pytest.mark.parametrize("title", [
    "Civil Engineering Intern", "Roadway Engineering Intern", "Water Resources Intern", "Construction Engineering Intern",
    "Software Engineer Intern, Robotics", "Electrical Engineer Intern, Robotics", "Optical Engineering Intern",
    "Distribution Engineering Intern", "Digital IC Design Engineer Intern", "Project Controls Intern", "Cost Accountant Intern, Global Operations and Manufacturing",
])
def test_blatant_roles_rejected(title):
    assert reason(title) is not None


@pytest.mark.parametrize("title", [
    "Field Engineering Intern", "Water Treatment Engineering Co-op", "Mechanical Engineering Intern Water",
    "Instrumentation & Controls Engineering Intern", "Electrical/Controls Engineering Intern", "Product Management Intern",
    "Acoustic Algorithm Development Engineer Intern", "Radiation Protection Engineering Intern", "Environmental Test Engineering Intern",
])
def test_borderline_roles_kept(title):
    assert reason(title) is None


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern (U.S. Person Required)", "Systems Engineering Intern (U.S. Citizen Required)",
    "Engineering Intern Talent Pool", "Mechanical Engineering Intern Hiring Event", "Video Production Intern",
    "Advanced Packaging Intern", "Firmware Engineer Intern, Robotics",
])
def test_picked_deletions(title):
    assert reason(title) is not None


@pytest.mark.parametrize("title", [
    "Combustion Devices Intern Summer 2027", "Flight Dynamics Internship", "Quality Intern", "Operational Excellence Co-Op",
    "Intern, Production", "Tool & Die Intern", "Packaging Co-Op", "Acoustic and Vibration Technologies Intern",
    "Research Associate Intern", "Program Management Intern",
])
def test_picked_additions_match(title):
    job = {"title": title, "location": "Boulder, CO"}
    assert js.matches(job, F)


def test_company_title_rules_only_hit_that_company():
    for company, title, kept in [("Terracon", "Materials Engineering Intern", False), ("Hexcel", "Materials Engineering Intern", True),
                                 ("Granite Construction", "Engineer Intern", False),
                                 ("Granite Construction", "Mechanical Engineer Intern", True), ("Acme", "Engineer Intern", True)]:
        assert (js.title_filter_reason({"title": title}, js.company_filters(company, F)) is None) is kept, (company, title)


def test_gebze_is_not_us():
    assert not js.matches({"title": "Manufacturing Engineering Intern", "location": "GEBZE PLANT; SEKERPINAR DC"}, F)
