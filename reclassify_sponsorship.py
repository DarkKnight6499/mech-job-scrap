#!/usr/bin/env python3
"""Re-fetch queue descriptions and apply the current sponsorship classifier.

Default targets Unclear. --blocked targets Blocked, --opt-only migrates legacy OPT Only,
and --no-sponsorship rechecks No Sponsorship notes. Nonblocked undecided rows return to
state new, where alerts remain eligible. Applied, shortlisted and dismissed states stay
unchanged. Empty descriptions and fetch errors preserve the previous classification.

Usage: py -3 reclassify_sponsorship.py [--dry-run] [--blocked | --opt-only | --no-sponsorship] [--limit N]
"""
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_scout
import atomic_json

HOME = job_scout.HOME
DESCRIBE_WORKERS = 12


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Report what would change, write nothing")
    statuses = ap.add_mutually_exclusive_group()
    statuses.add_argument("--blocked", action="store_true", help="Re-check Blocked entries instead of Unclear ones")
    statuses.add_argument("--opt-only", action="store_true", help="Migrate legacy OPT Only entries to current statuses")
    statuses.add_argument("--no-sponsorship", action="store_true", help="Re-check No Sponsorship notes")
    ap.add_argument("--limit", type=int, default=None, help="Only check the first N selected entries (testing)")
    ap.add_argument("--ats", default=None, help="Only entries whose company uses this ats (for example oracle)")
    args = ap.parse_args()

    cfg = job_scout.load_json(HOME / "config.json", None)
    if cfg is None:
        sys.exit(f"No config at {HOME / 'config.json'}")
    company_by_name = {c["name"]: c for c in cfg["companies"]}

    queue = job_scout.load_json(HOME / "queue.json", [])
    from_status = ("OPT Only" if args.opt_only else "Blocked" if args.blocked
                   else "No Sponsorship" if args.no_sponsorship else "Unclear")
    targets = [e for e in queue if e.get("sponsorship_status") == from_status]
    if args.ats:
        targets = [e for e in targets if (company_by_name.get(e["company"]) or {}).get("ats") == args.ats]
    if args.limit:
        targets = targets[:args.limit]
    print(f"{len(targets)} entries currently {from_status}, out of {len(queue)} total")

    no_company, fetch_errors, flipped, unchanged = 0, 0, 0, 0
    sponsorship_counts = dict.fromkeys(("Blocked", "No Sponsorship", "Unclear"), 0)

    def _reclassify(entry):
        name = entry["company"]
        c = company_by_name.get(name)
        if c is None:
            return entry, None, "no_company"
        prefix = f"{name}:"
        if not entry["id"].startswith(prefix):
            return entry, None, "no_company"  # eid format changed/unexpected - skip, don't guess
        job_id = entry["id"][len(prefix):]
        job = {"id": job_id, "url": entry.get("link", ""), "site": entry.get("site")}
        try:
            text, _posted, _src = job_scout.describe(c, job)
        except Exception as e:
            return entry, None, f"error: {e}"
        if not text or not text.strip():
            return entry, None, "error: empty description; kept prior classification"
        spons, evidence = job_scout.classify_sponsorship(text)
        return entry, (spons, evidence), None

    with ThreadPoolExecutor(max_workers=DESCRIBE_WORKERS) as pool:
        futures = [pool.submit(_reclassify, e) for e in targets]
        for i, fut in enumerate(as_completed(futures), 1):
            entry, result, err = fut.result()
            if err == "no_company":
                no_company += 1
                continue
            if err is not None:
                fetch_errors += 1
                print(f"! {entry['company']} - {entry['role']}: {err}", file=sys.stderr)
                continue
            spons, evidence = result
            sponsorship_counts[spons] += 1
            new_state = "auto_blocked" if spons == "Blocked" else "new"
            moved = entry["state"] in ("new", "auto_blocked", "opt_only") and entry["state"] != new_state
            if spons != entry["sponsorship_status"] or moved:
                suffix = f" (state: {entry['state']} -> {new_state})" if moved else ""
                print(f"  {entry['company']} | {entry['role']}: {from_status} -> {spons}{suffix}")
                if not args.dry_run:
                    entry["sponsorship_status"] = spons
                    entry["sponsorship_evidence"] = evidence
                    if moved:
                        entry["state"] = new_state
                flipped += 1
            else:
                if not args.dry_run:
                    entry["sponsorship_evidence"] = evidence
                unchanged += 1
            if i % 200 == 0:
                print(f"...{i}/{len(targets)} checked")

    print(f"\n{flipped} reclassified (from {from_status}), {unchanged} unchanged, "
          f"{no_company} skipped (company not in config), {fetch_errors} fetch errors")
    print("Classified: " + ", ".join(f"{status}: {count}" for status, count in sponsorship_counts.items()))

    if args.dry_run:
        print("(dry run - queue.json not written)")
    else:
        atomic_json.write(HOME / "queue.json", queue)
        print(f"wrote {HOME / 'queue.json'}")


if __name__ == "__main__":
    main()
