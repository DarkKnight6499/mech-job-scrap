"""Offline coverage for sponsorship notes in intake, alerts, CLI output and page filters."""
import argparse
import json

import pytest

import job_scout as js


@pytest.mark.parametrize("text,status,blocked", [
    ("No visa sponsorship.", "No Sponsorship", False),
    ("We will not sponsor visas. CPT students welcome.", "No Sponsorship", False),
    ("Clearance not required.", "Unclear", False),
    ("Must be a U.S. citizen.", "Blocked", True),
    ("Must hold an active Secret clearance.", "Blocked", True),
    ("OPT/CPT not accepted.", "Blocked", True),
    ("Do not apply if you will need immigration sponsorship (e.g., H1B, TN, STEM OPT).", "No Sponsorship", False),
    ("We will not sign documentation for STEM OPT.", "No Sponsorship", False),
    ("No sponsorship. Do not apply if you need CPT.", "Blocked", True),
    ("F-1 students are not eligible.", "Blocked", True),
    ("International students are not considered.", "Blocked", True),
])
def test_intake_alerts_unless_explicitly_blocked(monkeypatch, text, status, blocked):
    sent = []
    monkeypatch.setattr(js, "notify", lambda cfg, entry, dry: sent.append(entry) or True)
    job = dict(id="42", title="Mechanical Intern Summer 2027", location="CO", url="https://acme.example/42")
    queue, state, queued_ids = [], {}, set()
    counts = dict(matched=0, blocked=0, queued=0, alerted=0, reposts=0)
    js._process_company(
        dict(name="Acme", ats="greenhouse"), "Acme", [job], {"42": text}, False,
        [job], True, set(), state, queue, queued_ids, [], dict(filters={}, notify={}),
        argparse.Namespace(dry_run=False), counts,
    )
    assert len(queue) == 1 and queue[0]["sponsorship_status"] == status
    assert queue[0]["state"] == ("auto_blocked" if blocked else "new")
    assert len(sent) == counts["alerted"] == counts["queued"] == int(not blocked)
    assert counts["blocked"] == int(blocked)
    assert counts.get("no_sponsorship", 0) == int(status == "No Sponsorship")
    if status == "No Sponsorship":
        assert "[sponsorship/support refused]" in queue[0]["sponsorship_evidence"]


def queue_entry(status="No Sponsorship", state="new"):
    return dict(id="Acme:42", company="Acme", role="Mechanical Intern Summer 2027", location="CO",
                link="https://acme.example/42", state=state, sponsorship_status=status,
                sponsorship_evidence="...No visa sponsorship <provided>...", kw_hits=[], closed_on=None)


@pytest.mark.parametrize("status,state", [("No Sponsorship", "new"), ("OPT Only", "opt_only")])
def test_page_note_filter_counts_and_evidence(tmp_path, status, state):
    output = tmp_path / "jobs.html"
    js.write_queue_html([queue_entry(status, state)], output)
    page = output.read_text(encoding="utf-8")
    assert 'class="sponsorship-note"' in page
    assert 'title="...No visa sponsorship &lt;provided&gt;..."' in page
    assert 'data-no-sponsorship="1"' in page
    assert 'id="noSponsorshipBtn"' in page and "Hide No Sponsorship (1)" in page
    assert "No Sponsorship (1): employer sponsorship refused; alerts enabled." in page
    assert "Blocked (0)" in page and "Unclear (0)" in page
    assert "jobScoutHideNoSponsorship" in page
    assert "No H1B" not in page and 'data-spons="Blocked"' not in page


def test_page_counts_each_status(tmp_path):
    entries = [queue_entry(), queue_entry("Blocked", "auto_blocked"), queue_entry("Unclear")]
    output = tmp_path / "jobs.html"
    js.write_queue_html(entries, output)
    page = output.read_text(encoding="utf-8")
    assert "No Sponsorship (1)" in page and "Blocked (1)" in page and "Unclear (1)" in page
    assert 'data-spons="Blocked"' in page


@pytest.mark.parametrize("status,state", [("No Sponsorship", "new"), ("OPT Only", "opt_only")])
def test_default_cli_queue_includes_sponsorship_note(tmp_path, monkeypatch, capsys, status, state):
    entry = queue_entry(status, state)
    (tmp_path / "queue.json").write_text(json.dumps([entry]), encoding="utf-8")
    monkeypatch.setattr(js, "HOME", tmp_path)
    js.cmd_queue(argparse.Namespace(all=False, days=None, json=False, html=None))
    assert "spons No Sponsorship" in capsys.readouterr().out
