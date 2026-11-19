"""Rule-based fit score (0-100) and a one-line insight for a posting against the config `profile`."""
import re

BASE = 40
LEVEL_BONUS = 6   # explicit graduate/master's wording
UG_PENALTY = 12   # undergraduate/bachelor's-only wording
TOP_N = 3


def _has(text, term):
    return re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text) is not None


def score_row(role, company, kw_hits, profile):
    """Return (score, insight) from title, company and matched keywords; no network, no description."""
    text = (role or "").lower()  # kw_hits skipped: every row matched her keywords
    hits, gaps, total = [], [], 0
    for theme in profile.get("themes", []):
        found = [t for t in theme["terms"] if _has(text, t)]
        if found:
            total += theme["weight"]
            hits.append((theme["weight"], theme["label"], found[0]))
    for rule in profile.get("company_themes", []):
        if _has((company or "").lower(), rule["company"].lower()):
            total += rule["weight"]
            hits.append((rule["weight"], rule["label"], company))
    note = []
    if any(_has(text, t) for t in profile.get("graduate_terms", [])):
        total += LEVEL_BONUS
        note.append("grad-level")
    if any(_has(text, t) for t in profile.get("undergrad_only_terms", [])):
        total -= UG_PENALTY
        gaps.append("undergrad-only wording")
    for term in profile.get("gap_terms", []):
        if _has(text, term):
            gaps.append(term)
    hits.sort(reverse=True)
    score = max(5, min(98, BASE + total))
    top = [f"{label} ({word})" for _, label, word in hits[:TOP_N]]
    parts = []
    if top:
        parts.append("Matches: " + ", ".join(top))
    else:
        parts.append("No direct match to profile themes")
    if note:
        parts.append(", ".join(note))
    if gaps:
        parts.append("Gap: " + ", ".join(gaps[:2]))
    return score, "; ".join(parts)
