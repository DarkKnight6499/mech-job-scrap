# Engineering internship scout

Finds Summer 2027 engineering internships in the USA from public ATS boards. Flags sponsorship restrictions for F-1/CPT/OPT applicants and sends new-job alerts through ntfy.

## Setup

1. Use Python 3.12. Add repository secret `NTFY_TOPIC` and subscribe to that topic in the ntfy app. Never commit the topic.
2. `data/config.json` holds `notify`, `filters`, `companies` and `keywords`. Edit `filters.title_include` and `filters.title_require_all_groups` to change which titles match. `config.example.json` shows the shape.
3. Run `python validate_config.py`, then trigger `scout.yml` manually. The hourly workflow uses 12 fetch shards and saves queue/state between runs. A missing queue starts empty.
4. In repository Settings > Pages, choose GitHub Actions. The workflow generates and publishes the `/docs` folder, including `docs/index.html`.

## Edit matching

- `title_include`: alternatives used for title matching and search-based ATS queries.
- `title_require_all_groups`: every group must match at least one term. Keep both internship markers and engineering terms.
- `title_exclude`: title exclusions, with the summer season waiver below.
- `season_words_waived_by_summer`: optional list, default `["spring", "fall", "autumn", "winter", "semester"]`. When the title contains summer, waive these exclusions, including each word followed by a year. Exact season+year entries are also supported; `[]` disables the waiver. Year-round and other exclusions remain active even if listed here.
- `title_exclude_unless`: exclude software titles unless hardware, embedded, robotics, or related terms appear in the title.
- `description_exclude`: scan title and both description fields for explicit degree-only restrictions such as PhD required, while allowing PhD preferred.
- `internship_year: 2027`, `internship_season: "summer"`: check titles only. Reject other years only when 2027 is absent. Summer passes the season check even alongside another season. No stated year or season passes; description dates never reject.
- `locations_us_only: true`: require a configured US country/state marker. Blank locations and unqualified remote roles fail. State codes should be uppercase; codes after commas or hyphens also match lowercase text. A multi-site posting passes when at least one site qualifies.
- `locations_include` / `locations_exclude`: US markers and overseas exclusions. Explicit foreign locations override state-name collisions.
- `keywords`: engineering skill tags, not an extra eligibility gate.

Validate the draft without companies:

```sh
python validate_config.py
```

Local checks:

```sh
python -m pip install pytest
python -m pytest -q
python job_scout.py --check
python job_scout.py --dry-run
python job_scout.py --queue --all --html docs/index.html
```

First run seeds the queue silently. Missing descriptions are classified as unchecked. Sponsorship flags identify explicit restrictions; silence does not establish eligibility. Optional Copy JD proxy setup is in `worker/README.md`.
