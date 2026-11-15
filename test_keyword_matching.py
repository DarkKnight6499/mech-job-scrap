"""Engineering aliases and token boundaries work in either direction."""
import pytest

from keyword_matching import contains_any, contains_term, first_match


@pytest.mark.parametrize("phrase,abbreviation", [
    ("computer-aided design", "CAD"), ("research and development", "R&D"),
    ("unmanned aerial vehicle", "UAV"), ("printed circuit board", "PCB"),
    ("human-machine interface", "HMI"), ("supervisory control and data acquisition", "SCADA"),
])
def test_aliases_match_in_both_directions(phrase, abbreviation):
    assert contains_term(phrase, abbreviation)
    assert contains_term(abbreviation, phrase)
    assert contains_any(phrase, ["unrelated", abbreviation])
    assert first_match(phrase, [abbreviation]).lower() == phrase


@pytest.mark.parametrize("text,term", [("International", "intern"), ("Internal", "intern"),
                                       ("Scad", "CAD"), ("Controls", "HR")])
def test_short_terms_do_not_match_inside_words(text, term):
    assert not contains_term(text, term)
