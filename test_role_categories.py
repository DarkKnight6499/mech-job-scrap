"""Queue category chips expose engineering disciplines through embedded JSON."""
import json
import re

import pytest

import job_scout as js


def page_categories():
    script = js._extra_script()
    start = script.index("var CATEGORIES = ") + len("var CATEGORIES = ")
    return json.loads(script[start:script.index(";\n", start)])


def categories_for(title):
    return {category["label"] for category in page_categories()
            if any(re.search(r"\b" + re.escape(term) + r"\b", title, re.I) for term in category["terms"])}


@pytest.mark.parametrize("title,category", [
    ("Mechanical Engineering Intern", "Mechanical"), ("Aerospace Intern", "Aerospace"),
    ("Robotics Controls Intern", "Robotics/Controls"), ("Manufacturing Intern", "Manufacturing/Process"),
    ("Test Engineer Intern", "Test/Quality"), ("Systems Engineering Intern", "Systems"),
    ("Embedded Hardware Intern", "Electrical/Embedded"), ("Membrane Materials Intern", "Materials/Water"),
])
def test_engineering_categories(title, category):
    assert category in categories_for(title)


def test_category_labels():
    assert {category["label"] for category in page_categories()} == {
        "Mechanical", "Aerospace", "Robotics/Controls", "Manufacturing/Process",
        "Test/Quality", "Systems", "Electrical/Embedded", "Materials/Water", "Other (no category)",
    }


def test_word_boundaries_and_multiple_categories():
    assert categories_for("Scad Intern") == set()
    assert categories_for("Aerospace Hardware Intern") == {"Aerospace", "Electrical/Embedded"}
