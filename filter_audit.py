"""filter_audit.py - list roles a title exclude rule hides that look like engineering internship fits, so a bad rule gets caught.

Reads data/filtered.json (written by job_scout.py run). Prints a Markdown report: flagged roles new since the last
audit, then rule counts. Run every few days; fix a bad rule in data/config.json (title_exclude_unless for a narrow exception).
"""
import argparse
import json
from pathlib import Path

from keyword_matching import contains_any

# ---- config ----
DATA = Path(__file__).resolve().parent / "data"
FILTERED_FILE = DATA / "filtered.json"
FILTERS_FILE = DATA / "config.json" if (DATA / "config.json").exists() else DATA / "config.json"
FILTERS = json.loads(FILTERS_FILE.read_text(encoding="utf-8"))["filters"]
FLAG_TERMS = [term for group in FILTERS.get("title_require_all_groups", [])[1:] for term in group]
TOP_RULES = 25
INTENTIONAL_RULES = {
    "senior", "sr", "staff", "principal", "manager", "director", "lead", "head of", "chief",
    "sales", "marketing", "hr", "human resources", "accounting", "mba", "phd-only", "phd only",
    "ph.d. only", "doctoral", "winter", "fall 2026", "spring 2027", "summer 2026", "summer 2028",
}
# ---- end config ----

ID, ROLE, LOC, LINK, KIND, TERM = range(6)  # row layout written by job_scout._filtered_rows


def audit(data, seen_ids):
    flagged, counts = [], {}
    for company, v in sorted(data.get("companies", {}).items()):
        for r in v["rows"]:
            counts[r[TERM]] = counts.get(r[TERM], 0) + 1
            key = f"{company}:{r[ID]}"
            if r[TERM] not in INTENTIONAL_RULES and contains_any(r[ROLE], FLAG_TERMS):
                flagged.append((company, r, key, key not in seen_ids))
    return flagged, counts


def render(data, flagged, counts):
    total = sum(v["n"] for v in data.get("companies", {}).values())
    new = [f for f in flagged if f[3]]
    out = [f"# Filter audit ({data.get('updated', '?')})", "",
           f"{total} roles hidden by title rules across {len(data.get('companies', {}))} companies; "
           f"{len(flagged)} look like core fits, {len(new)} new since the last audit.", ""]
    out.append("## New flagged roles (check each rule)")
    out += [f"- {c}: [{r[ROLE]}]({r[LINK]}) ({r[LOC]}) hidden by {r[KIND]}: **{r[TERM]}**" for c, r, _, _ in new] or ["- none"]
    out += ["", "## Top rules by roles hidden"]
    out += [f"- {t}: {n}" for t, n in sorted(counts.items(), key=lambda kv: -kv[1])[:TOP_RULES]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write the report here instead of stdout")
    ap.add_argument("--state", default=str(DATA / "audit_seen.json"), help="ids already reported (local, not committed)")
    args = ap.parse_args()
    data = json.loads(FILTERED_FILE.read_text(encoding="utf-8")) if FILTERED_FILE.exists() else {}
    state = Path(args.state)
    seen = set(json.loads(state.read_text(encoding="utf-8"))) if state.exists() else set()
    flagged, counts = audit(data, seen)
    report = render(data, flagged, counts)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    else:
        print(report)
    state.write_text(json.dumps(sorted(seen | {f[2] for f in flagged})), encoding="utf-8")


if __name__ == "__main__":
    main()
