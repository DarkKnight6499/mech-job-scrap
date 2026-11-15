"""Only explicit eligibility exclusions block; sponsorship refusals remain actionable notes."""
import pytest

import job_scout as js

BLOCKED = [
    "Toyota does not offer support or sponsorship of job applicants for employment-based visas or any other work authorization for this role now or in the future. You must have the right to work in the United States and not require Toyota support or sponsorship for immigration-related employment (e.g., H-1B, O-1, E-3, H-1B1, TN, F-1 OPT, F-1 STEM OPT, F-1 CPT, etc.) now or in the future.",
]
NO_SPONSORSHIP = [
    "USAA does not provide visa sponsorship for this role. Please do not apply for this role if at any time (now or in the future) you will need immigration support (i.e., H-1B, TN, STEM OPT Training Plans, etc.).",
    "Candidates requiring immigration support, such as H-1B or STEM OPT, will not be considered.",
    "No support for OPT.",
    "Sponsorship Offered: No",
    "Visa Sponsorship? No",
    "Education Requirement: Bachelor degree Sponsorship: No Come Drive Innovation with Us.",
    "We hire without current or future sponsorship needs.",
    "We do not provide visa sponsorship for this role.",
    "We are unable to provide immigration support for this role.",
    "This role is not eligible for visa assistance.",
    "No immigration support is available for this position.",
    "Bachelor's degree in Engineering, STEM, or a related field. We do not provide visa sponsorship for this role.",
    "Applicants must be authorized to work in the U.S. without current or future employer support.",
    "We will not sponsor now or in the future.",
    "We won't sponsor visas.",
    "No visa sponsorship.",
    "This position is subject to ITAR. We cannot sponsor.",
    "We do not provide visa sponsorship. F-1 students are welcome.",
    "No sponsorship; OPT and CPT candidates are welcome.",
    "We do not sponsor visas and provide administrative assistance for OPT.",
    "We do not provide visa sponsorship for this role and accept STEM OPT candidates.",
    "OPT training is available. We will not sponsor visas.",
    "No sponsorship. Candidates must have permanent work authorization.",
]
HARD_BLOCKED = [
    "This position is for a government client and we can only hire US citizens.",
    "For this client engagement we will only consider U.S. citizens.",
    "We do not offer any type of employment-based immigration sponsorship for this role. Likewise, the firm will not provide any assistance or sign any documentation in support of any other form of immigration sponsorship or benefit, including optional practical training (OPT) or curricular practical training (CPT).",
    "Candidates must hold an active US Secret clearance.",
    "Access is limited to U.S. persons only under export control rules.",
    "The position requires U.S. Citizenship.",
    "Unrestricted work authorization is needed. CPT and OPT are restricted.",
    "Secret clearance is required for this position.",
    "Benefits include STEM support. We will not sponsor now or in the future. F-1 OPT and CPT candidates are not eligible.",
    "Must be a U.S. citizen. We do not sponsor visas.",
    "Active secret clearance required. No sponsorship.",
    "No sponsorship available. Candidates on STEM OPT or CPT are not considered.",
    "Applicants must be U.S. citizens.",
    "U.S. citizenship is required.",
    "This internship requires United States citizenship.",
    "US citizens only.",
    "Only U.S. citizens may apply.",
    "Candidates must be a citizen of the United States.",
    "Applicants must hold a green card.",
    "Green card holders only.",
    "Lawful permanent residency is required.",
    "Applicants must be lawful permanent residents.",
    "Permanent resident required.",
    "Candidates must hold a security clearance.",
    "Security clearance is required.",
    "Ability to obtain security clearance is required.",
    "Must be able to obtain a Secret clearance.",
    "Must have the ability to obtain an active security clearance.",
    "Top Secret clearance required.",
    "TS/SCI clearance is required.",
    "Must hold TS/SCI.",
    "Public Trust clearance required.",
    "Must obtain a Public Trust clearance.",
    "Ability to obtain Public Trust required.",
    "DoD clearance required.",
    "Current security clearance required.",
    "Must be a U.S. person as defined by ITAR.",
    'Must be a "U.S. person" as defined by ITAR.',
    "ITAR requires U.S. person status.",
    "Export-controlled work is restricted to U.S. persons.",
    "EAR export control requires U.S. citizenship or permanent residency.",
    "Due to export control, candidates must be lawful permanent residents.",
    "OPT/CPT not accepted.",
    "F-1 not eligible.",
    "F-1 students are not eligible for this internship.",
    "We do not accept OPT or CPT candidates.",
    "No clearance is needed, but U.S. citizenship is required.",
    "U.S. citizenship is not required; candidates must hold an active Secret clearance.",
    "Clearance preferred. Green card required.",
]
UNCLEAR = [
    "Sponsorship: No longer needed once you join the program.",
    "Our members are not sponsored by agencies of the United States.",
    "We will not sponsor new industry registrations for this fund.",
    "We offer visa sponsorship and immigration support for qualified candidates.",
    "Immigration support is available for the right candidate.",
    "Do not apply unless you are passionate about risk management.",
    "Please do not apply through third parties; use our careers site.",
    "Candidates must be eligible to work in the United States. We will sponsor H-1B visas where appropriate.",
    "The role supports our immigration law practice clients and does not require travel.",
    "Authorized to work in the U.S. is required; we provide relocation assistance.",
    "This role is limited to persons with an indefinite right to work in the United States.",
    "Must have permanent or ongoing work authorization in the U.S.",
    "This role is open to U.S. citizens or lawful permanent residents.",
    "To be eligible for a VIE: Be EU citizen.",
    "U.S. citizens, green card holders, and F-1 students are welcome.",
    "Must be a U.S. citizen, green card holder, or F-1 student.",
    "Clearance not required.",
    "No clearance needed.",
    "Does not require U.S. citizenship.",
    "This internship doesn't require U.S. citizenship.",
    "U.S. citizenship is not required.",
    "No U.S. citizenship required.",
    "No U.S. citizenship or permanent residency is required.",
    "No U.S. citizenship, green card, or security clearance is required.",
    "Does not require U.S. citizenship, a green card or security clearance.",
    "Green card not required.",
    "No green card required.",
    "Lawful permanent residency is not required.",
    "This role does not require a security clearance.",
    "This role does not require active Secret clearance.",
    "This role does not require the ability to obtain security clearance.",
    "Preferred: active Secret clearance.",
    "No active Secret clearance required.",
    "Active Secret clearance not required.",
    "TS/SCI clearance preferred.",
    "Public Trust clearance not required.",
    "DoD clearance is optional.",
    "Security clearance preferred.",
    "Active security clearance is preferred.",
    "Ability to obtain clearance a plus.",
    "Ability to obtain a security clearance is a plus.",
    "Preferred qualifications: ability to obtain security clearance.",
    "U.S. citizenship preferred.",
    "Green card holders preferred.",
    "Must be a U.S. person as defined by ITAR is preferred.",
    "ITAR training will be provided.",
    "This internship supports export control documentation.",
    "U.S. persons and F-1 students are eligible to apply.",
    "No OPT restrictions.",
    "No OPT/CPT restrictions.",
    "OPT/CPT candidates are accepted.",
    "F-1 students may apply.",
    "No visa sponsorship is required for CPT applicants.",
    "We will sponsor now or in the future.",
    "Must be a U.S. citizenshipper.",
    "We need military engineering experience.",
]


@pytest.mark.parametrize("text", BLOCKED)
def test_blocks_immigration_support_phrasing(text):
    assert js.classify_sponsorship(text)[0] == "Blocked"


@pytest.mark.parametrize("text", HARD_BLOCKED)
def test_hard_blocks_stay_blocked(text):
    assert js.classify_sponsorship(text)[0] == "Blocked"


@pytest.mark.parametrize("text", NO_SPONSORSHIP + [
    "Please do not apply for this role if you will need immigration support (H-1B, TN).",
    "We do not offer relocation or immigration assistance.",
])
def test_plain_no_sponsorship_is_note(text):
    assert js.classify_sponsorship(text)[0] == "No Sponsorship"


@pytest.mark.parametrize("text", UNCLEAR)
def test_benign_lookalikes_stay_unclear(text):
    assert js.classify_sponsorship(text)[0] == "Unclear"


def test_us_abbreviation_before_space_is_normalized():
    assert js.classify_sponsorship("Candidates must be authorized to work in the U.S. without sponsorship now or in the future.")[0] == "No Sponsorship"


def test_tags():
    assert js.classify_sponsorship("We will not sponsor now or in the future.")[1].startswith("[now or future]")
    status, evidence = js.classify_sponsorship("No sponsorship. Do not apply if you need H-1B or STEM OPT.")
    assert status == "No Sponsorship"
    assert "[sponsorship/support refused]" in evidence
    assert "[no STEM OPT]" not in evidence and "[student exclusion]" not in evidence
    assert js.classify_sponsorship("We do not provide sponsorship; we will not sign any documentation for OPT or CPT.")[0] == "Blocked"


def test_mizuho_refuses_stem_opt_paperwork_is_blocked():
    text = ("Applicants must be currently authorized to work in the United States on a full-time basis. Mizuho does not sponsor "
            "applicants for work visas or offer any employment-based immigration sponsorship for this position. This includes, "
            "but is not limited to, any sponsorship or administrative assistance or execution of any documentation related to "
            "F-1 (CPT/OPT/STEM OPT), TN, O-1, E-3, H-1B1 or H-1B application.")
    assert js.classify_sponsorship(text)[0] == "Blocked"


def test_will_not_participate_in_stem_opt_is_note():
    text = "PNC will not provide sponsorship for employment visas or participate in STEM OPT for this position."
    assert js.classify_sponsorship(text)[0] == "No Sponsorship"


@pytest.mark.parametrize("text,status", [
    ("Do not apply if you will need immigration sponsorship (e.g., H1B, TN, STEM OPT).", "No Sponsorship"),
    ("Do not apply if you need H1B, TN or STEM OPT.", "No Sponsorship"),
    ("We do not provide paperwork for STEM OPT.", "No Sponsorship"),
    ("No support for STEM OPT.", "No Sponsorship"),
    ("We will not participate in STEM OPT.", "No Sponsorship"),
    ("We will not sign any documentation for optional practical training.", "No Sponsorship"),
    ("We do not sponsor visas. This includes administrative assistance for STEM OPT.", "No Sponsorship"),
    ("STEM OPT candidates are not eligible.", "No Sponsorship"),
    ("No sponsorship. CPT candidates are welcome.", "No Sponsorship"),
    ("No sponsorship. International students may apply.", "No Sponsorship"),
    ("Do not apply if you need immigration support (H1B, TN, CPT).", "Blocked"),
    ("Do not apply if you hold F-1 status.", "Blocked"),
    ("Do not apply if you are an international student.", "Blocked"),
    ("International students are not eligible for this role.", "Blocked"),
    ("We do not accept international students.", "Blocked"),
    ("CPT applicants are not considered.", "Blocked"),
    ("Curricular practical training is not accepted.", "Blocked"),
    ("We do not sponsor visas. This includes administrative assistance for CPT.", "Blocked"),
    ("No sponsorship. F-1 students are not eligible.", "Blocked"),
    ("No sponsorship. U.S. citizenship is required.", "Blocked"),
])
def test_cpt_eligibility_controls_student_blocks(text, status):
    actual, evidence = js.classify_sponsorship(text)
    assert actual == status
    if status == "No Sponsorship":
        assert "[sponsorship/support refused]" in evidence
    assert "[no STEM OPT]" not in evidence


def test_student_exclusion_evidence_preserves_original_text():
    text = "No visa sponsorship. F-1 students are not eligible."
    status, evidence = js.classify_sponsorship(text)
    assert status == "Blocked"
    assert evidence.startswith("[student exclusion]")
    assert "F-1 students are not eligible" in evidence


def test_stem_opt_welcome_stays_no_sponsorship():
    text = "We do not provide visa sponsorship for this role. STEM OPT candidates are welcome to apply."
    assert js.classify_sponsorship(text)[0] == "No Sponsorship"


def test_employer_of_record_without_explicit_student_exclusion_is_note():
    text = ("Applicants must possess legal authorization to work for our company in the U.S. without the need for immigration "
            "sponsorship or otherwise serving as an employer of record for immigration employment purposes. At this time, this "
            "role is not eligible for immigration-related employment authorization sponsorship.")
    assert js.classify_sponsorship(text)[0] == "No Sponsorship"


@pytest.mark.parametrize("text", [None, "", "Mechanical internship, Summer 2027."])
def test_missing_language_is_unclear_never_allowed(text):
    assert js.classify_sponsorship(text)[0] == "Unclear"


def test_evidence_preserves_original_abbreviation_and_excerpt():
    text = "Mechanical internship. U.S. citizenship is required. Apply online."
    status, evidence = js.classify_sponsorship(text)
    assert status == "Blocked"
    assert "U.S. citizenship is required" in evidence
    assert evidence.startswith("...") and evidence.endswith("...")
