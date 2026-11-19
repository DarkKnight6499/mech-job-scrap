"""Adjacent engineering titles are kept; non-engineering noise stays out."""
import json
from pathlib import Path

import pytest

import job_scout as js

FILTERS = json.loads((Path(__file__).parent / "data/config.json").read_text(encoding="utf-8"))["filters"]


def kept(title):
    return js.matches(dict(title=title, desc="", location="Boulder, CO"), FILTERS)


@pytest.mark.parametrize("title", [
    "FEA Intern", "CAE Simulation Intern", "CFD Intern", "Structural Analysis Intern", "Tooling Engineering Intern",
    "Metallurgy Intern", "Failure Analysis Intern", "Composites Intern", "Additive Manufacturing Intern",
    "Coatings Engineering Intern", "Water Treatment Intern", "Filtration Engineering Intern", "Process Development Intern",
    "Industrial Engineering Intern", "NPI Intern", "Metrology Intern", "Supplier Quality Engineer Intern",
    "Flight Test Intern", "GNC Intern", "UAS Engineering Intern",
    "Systems Integration Intern", "Technical Program Management Intern", "Applications Engineer Intern",
    "Motion Control Engineering Intern", "PLC Controls Intern", "Instrumentation Intern", "Physical Design Intern",
    "Product Design Intern", "Industrial Design Intern",
])
def test_adjacent_titles_kept(title):
    assert kept(title)


@pytest.mark.parametrize("title", [
    "Supply Chain Industrial Engineering Intern", "Software Engineer Intern", "Finance Intern",
    "Water Utility Billing Intern", "Procurement Intern",
])
def test_noise_still_out(title):
    assert not kept(title)
