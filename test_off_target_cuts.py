import json
import pytest
import job_scout as js

F = json.load(open("data/config.json", encoding="utf8"))["filters"]


def reason(title):
    return js.title_filter_reason({"title": title, "description": ""}, F)


@pytest.mark.parametrize("title", [
    "Electrical Engineering Intern", "Embedded Software Intern Summer 2027", "Avionics Intern", "Analog Design Engineering Intern",
    "Geotechnical Intern", "Structural Intern", "Transportation Planning Intern", "EHS Intern Summer 2027",
    "ASIC Engineer Intern", "Software Engineer Intern Summer 2027",
])
def test_off_target_titles_cut(title):
    assert reason(title) is not None


@pytest.mark.parametrize("title", [
    "Mechanical Engineering Intern Summer 2027", "Structural Analysis Intern", "Mechatronics Intern",
    "Electromechanical Engineering Intern", "Robotics Software Intern", "Materials Engineering Intern",
    "Aerospace Structural Engineering Intern",
])
def test_mechanical_titles_kept(title):
    assert reason(title) is None
