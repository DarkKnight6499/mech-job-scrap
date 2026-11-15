"""Additive sponsorship detail: three separate facets, each with the JD quote that supports it.

Does not replace job_scout.classify_sponsorship (the source for Blocked / No Sponsorship / Unclear);
this only explains *why*. Facet values: current_authorization: required | not stated;
future_sponsorship: offered | refused | not stated; citizenship: required | clearance | not stated.
"""
import re

from job_scout import sponsorship_requirement

# --- config ---
CONTEXT = 70  # characters of quote kept on each side of a match
PATTERNS = {
    "current_authorization": [
        ("required", r"(must|required to|need to|should) (be |currently be )?(legally |lawfully )?(authorized|eligible|permitted) to work"
                     r"|(u\.?s\.?|united states) work authorization (is )?required|unrestricted work authorization"),
    ],
    "future_sponsorship": [
        ("refused", r"(will not|won'?t|unable to|cannot|can'?t|not able to|does not|do not|not) (provide |offer |consider )?(visa |employment[- ]based |immigration )?sponsor"
                    r"|\bno\s+(?:visa\s+)?sponsorship\b(?!\s+(?:is\s+)?(?:needed|required|restrictions?)\b)"
                    r"|\bnot eligible for (?:visa )?sponsorship\b"
                    r"|without (the need for )?(current or future |now or in the future )?(visa |employer )?sponsorship"
                    r"|not require (future |current |visa )*sponsorship|sponsorship (is )?not available"),
        ("offered", r"eligible for visa sponsorship|(open to|consider(s|ing)?|welcomes?) (candidates|applicants)[^.]{0,60}sponsorship"
                    r"|visa sponsorship (is )?(available|offered|provided)|will sponsor|can sponsor|sponsorship (is )?available"),
    ],
}
# --- end config ---


def facets(text):
    """Return {facet: {"value": str, "quote": str}} for every facet; quote is empty when not stated."""
    text = text or ""
    out = {}
    for facet, rules in PATTERNS.items():
        out[facet] = {"value": "not stated", "quote": ""}
        for value, rx in rules:
            m = re.search(rx, text or "", re.I)
            if m:
                s, e = max(0, m.start() - CONTEXT), min(len(text), m.end() + CONTEXT)
                out[facet] = {"value": value, "quote": "..." + re.sub(r"\s+", " ", text[s:e]).strip() + "..."}
                break
    value, match = sponsorship_requirement(text)
    quote = ""
    if match:
        s, e = max(0, match.start() - CONTEXT), min(len(text), match.end() + CONTEXT)
        quote = "..." + re.sub(r"\s+", " ", text[s:e]).strip() + "..."
    out["citizenship"] = {"value": value or "not stated", "quote": quote}
    return out


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(facets(open(sys.argv[1], encoding="utf-8", errors="replace").read()), indent=1))
