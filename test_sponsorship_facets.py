import pytest

from sponsorship_facets import facets


def test_refused_and_authorization():
    f = facets("Candidates must possess unrestricted work authorization and not require future sponsorship.")
    assert f["future_sponsorship"]["value"] == "refused" and f["current_authorization"]["value"] == "required"


def test_offered():
    f = facets("WSIB is open to candidates who may require employment-based visa sponsorship.")
    assert f["future_sponsorship"]["value"] == "offered" and "sponsorship" in f["future_sponsorship"]["quote"]


def test_clearance_and_silence():
    assert facets("Active Secret clearance required.")["citizenship"]["value"] == "clearance"
    assert all(v["value"] == "not stated" for v in facets("Mechanical analyst, strong Excel.").values())


@pytest.mark.parametrize("text", [
    "No visa sponsorship.",
    "We will not sponsor visas.",
    "We won't sponsor visas.",
    "Visa sponsorship is not available.",
    "Must be authorized to work without sponsorship.",
])
def test_refusal_is_neutral_detail(text):
    f = facets(text)
    assert f["future_sponsorship"]["value"] == "refused"
    assert f["future_sponsorship"]["quote"]
    assert f["citizenship"]["value"] == "not stated"


@pytest.mark.parametrize("text,value", [
    ("U.S. citizenship is required.", "required"),
    ("Must be a United States citizen.", "required"),
    ("Green card required.", "required"),
    ("Must be a lawful permanent resident.", "required"),
    ("Secret clearance required.", "clearance"),
    ("Top Secret clearance required.", "clearance"),
    ("Must hold TS/SCI.", "clearance"),
    ("Public Trust clearance required.", "clearance"),
    ("DoD clearance required.", "clearance"),
    ("Ability to obtain security clearance required.", "clearance"),
    ("Must be a U.S. person as defined by ITAR.", "clearance"),
    ("Export control requires permanent residency.", "required"),
])
def test_mandatory_facets_share_classifier_rules(text, value):
    detail = facets(text)["citizenship"]
    assert detail["value"] == value
    assert detail["quote"].startswith("...") and detail["quote"].endswith("...")
    if "U.S." in text:
        assert "U.S." in detail["quote"]


@pytest.mark.parametrize("text", [
    "Clearance not required.",
    "No clearance needed.",
    "Does not require U.S. citizenship.",
    "Green card holders and F-1 students are welcome.",
    "U.S. citizens, green card holders, and F-1 students are welcome.",
    "Security clearance preferred.",
    "Ability to obtain clearance a plus.",
    "Preferred qualifications: ability to obtain security clearance.",
    "Active Secret clearance is not required.",
    "ITAR training provided.",
    "Export control documentation skills preferred.",
    "Permanent work authorization required.",
    "No visa sponsorship is required for CPT applicants.",
])
def test_mentions_and_optional_statuses_do_not_claim_requirements(text):
    assert facets(text)["citizenship"] == {"value": "not stated", "quote": ""}
