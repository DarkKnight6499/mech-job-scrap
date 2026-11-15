"""Offline regression tests for sponsorship re-fetches from queue rows."""
import json
import sys

import pytest

import job_scout
import reclassify_sponsorship as backfill


@pytest.mark.parametrize("dry_run", [False, True])
def test_refetch_uses_queue_link(tmp_path, monkeypatch, capsys, dry_run):
    company = {"name": "Acme", "ats": "avature", "host": "acme.example"}
    entry = dict(id="Acme:42", company="Acme", role="Analyst", state="new",
                 link="https://acme.example/careers/42", site="external",
                 sponsorship_status="Unclear", sponsorship_evidence="")
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps([entry]), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"companies": [company]}), encoding="utf-8")
    calls = []

    def fake_http(url, **kwargs):
        calls.append(url)
        return b"<html><p>U.S. citizenship is required.</p></html>"

    monkeypatch.setattr(job_scout, "http", fake_http)
    monkeypatch.setattr(backfill, "HOME", tmp_path)
    monkeypatch.setattr(sys, "argv", ["reclassify_sponsorship.py"] + (["--dry-run"] if dry_run else []))
    backfill.main()

    assert calls == [entry["link"]]
    assert "0 fetch errors" in capsys.readouterr().out
    saved = json.loads(queue_path.read_text(encoding="utf-8"))[0]
    if dry_run:
        assert saved == entry
    else:
        assert saved["sponsorship_status"] == "Blocked"
        assert saved["state"] == "auto_blocked"
        assert saved["sponsorship_evidence"]
        for key in ("id", "company", "role", "link", "site"):
            assert saved[key] == entry[key]


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("flag,status,state,text,expected_status,expected_state", [
    ("--opt-only", "OPT Only", "opt_only", "We will not sponsor visas.", "No Sponsorship", "new"),
    ("--blocked", "Blocked", "auto_blocked", "No visa sponsorship.", "No Sponsorship", "new"),
    ("--blocked", "Blocked", "auto_blocked", "Clearance not required.", "Unclear", "new"),
    ("--blocked", "Blocked", "auto_blocked", "This role is subject to ITAR.", "Unclear", "new"),
    ("--opt-only", "OPT Only", "opt_only", "F-1 students are not eligible.", "Blocked", "auto_blocked"),
    ("--no-sponsorship", "No Sponsorship", "new", "Must hold a green card.", "Blocked", "auto_blocked"),
    ("--no-sponsorship", "No Sponsorship", "new", "CPT students are welcome.", "Unclear", "new"),
    ("--no-sponsorship", "No Sponsorship", "opt_only", "We will not sponsor visas.", "No Sponsorship", "new"),
    ("--blocked", "Blocked", "applied", "We will not sponsor visas.", "No Sponsorship", "applied"),
    ("--blocked", "Blocked", "shortlisted", "No visa sponsorship.", "No Sponsorship", "shortlisted"),
    ("--opt-only", "OPT Only", "dismissed", "No visa sponsorship.", "No Sponsorship", "dismissed"),
])
def test_status_migration(tmp_path, monkeypatch, capsys, dry_run, flag, status, state, text,
                          expected_status, expected_state):
    entry = dict(id="Acme:42", company="Acme", role="Mechanical Intern", state=state,
                 link="https://acme.example/42", sponsorship_status=status,
                 sponsorship_evidence="old evidence", closed_on=None)
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps([entry]), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"companies": [{"name": "Acme"}]}), encoding="utf-8")
    monkeypatch.setattr(job_scout, "describe", lambda *args: (text, "", ""))
    monkeypatch.setattr(backfill, "HOME", tmp_path)
    monkeypatch.setattr(sys, "argv", ["reclassify_sponsorship.py", flag] + (["--dry-run"] if dry_run else []))
    backfill.main()
    saved = json.loads(queue_path.read_text(encoding="utf-8"))[0]
    output = capsys.readouterr().out
    assert "0 fetch errors" in output and "Classified:" in output
    assert f"{expected_status}: 1" in output
    if dry_run:
        assert saved == entry
    else:
        assert saved["sponsorship_status"] == expected_status
        assert saved["state"] == expected_state
        assert saved["sponsorship_evidence"] != "old evidence"
        assert saved["link"] == entry["link"] and saved["closed_on"] is None


@pytest.mark.parametrize("text", [None, "", "  "])
def test_empty_description_preserves_blocked_verdict(tmp_path, monkeypatch, capsys, text):
    entry = dict(id="Acme:42", company="Acme", role="Intern", state="auto_blocked",
                 sponsorship_status="Blocked", sponsorship_evidence="old evidence")
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps([entry]), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({"companies": [{"name": "Acme"}]}), encoding="utf-8")
    monkeypatch.setattr(job_scout, "describe", lambda *args: (text, "", ""))
    monkeypatch.setattr(backfill, "HOME", tmp_path)
    monkeypatch.setattr(sys, "argv", ["reclassify_sponsorship.py", "--blocked"])
    backfill.main()
    assert json.loads(queue_path.read_text(encoding="utf-8")) == [entry]
    assert "1 fetch errors" in capsys.readouterr().out
