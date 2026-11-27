import json

import pytest

import job_scout as js

F = json.load(open("data/config.json", encoding="utf8"))["filters"]


def reason(title):
    return js.title_filter_reason({"title": title}, F)


@pytest.mark.parametrize("title", [
    "Manufacturing Engineering Intern (Jan 2027)", "Validation Engineering Co-op (May-December)",
    "Product Engineering Co-Op, Jan-June 2027", "Mechanical Engineering Co-Op (June - December 2027)",
    "Mechanical Reliability Co-Op (July - Dec) 2027", "Process Engineering Co-Op (Jan-Aug)",
    "Reliability Co-Op (June – Dec '27) Engineering", "Mechanical Engineering Co-op (Spring/Summer 2027)",
    "Mechanical Engineering Co-op (Summer/Fall 2027)", "Mechanical Engineering Intern Spring and Summer 2027",
    "Mechanical Engineer PhD Intern", "Mechanical Engineering Intern - PhD", "Postdoctoral Mechanical Engineering Intern",
])
def test_rejected(title):
    assert reason(title) is not None


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern Summer 2027", "Mechanical Engineering Intern (May-August 2027)",
    "Mechanical Engineering Intern (May-Aug '27)", "Process Engineering Intern - MS/PhD",
    "Mechanical Engineering Intern - BS, MS or PhD", "Mechanical Engineering Intern Summer Semester 2027",
    "Mechanical Engineering Intern (June - August 2027)",
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
