"""Region chips combine with OR and keep rows with any qualifying site."""
import pytest

import job_scout as js


# Test inputs
LOCATIONS = {
    1: "Denver, CO",
    2: "Boulder, Colorado",
    3: "Aurora, IL",
    4: "Chicago co-op campus",
    5: "New York, NY",
    6: "Albany, NY; New York, NY",
    7: "Buffalo, NY | Jersey City, NJ",
    8: "Albany, NY",
    9: "Chicago, IL; Golden, CO, US",
    10: "Chicago, IL | fOrT cOlLiNs",
    11: "Aurora, CO",
    12: "Aurora, OH",
    13: "Aurora, NY",
    14: "Aurora",
    15: "Bogota, co",
    16: "Chicago CO-op campus",
    17: "Remote CO",
    18: "Aurora, IL | Bogota, co",
}
COLORADO_IDS = {1, 2, 9, 10, 11, 17}
METRO_IDS = {5, 6, 7, 13}
COLORADO_CITIES = (
    "colorado", "denver", "boulder", "golden", "littleton", "lone tree",
    "englewood", "lakewood", "centennial", "westminster", "broomfield",
    "louisville", "longmont", "loveland", "fort collins", "greeley",
    "colorado springs", "pueblo", "arvada", "thornton", "castle rock",
    "berthoud", "parker", "highlands ranch", "Aurora, Colorado",
)


def row(i, location):
    return dict(
        id=f"Acme:{i}", company="Acme", role=f"Risk Analyst {i}",
        location=location, link=f"https://example.com/{i}", source="test",
        state="new", first_seen="2026-11-01", posted="2026-11-01", kw_hits=[],
        sponsorship_status="Allowed", sponsorship_evidence="", closed_on=None,
    )


def test_generated_html_contains_both_region_ids(tmp_path):
    page_path = tmp_path / "index.html"
    js.write_queue_html([row(1, LOCATIONS[1])], str(page_path))
    html = page_path.read_text(encoding="utf-8")
    assert 'id="metroOnlyBox"' in html
    assert 'id="coloradoOnlyBox"' in html


@pytest.fixture
def region_page(tmp_path):
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    rows = [row(i, location) for i, location in LOCATIONS.items()]
    rows.extend(row(i, city.upper()) for i, city in enumerate(COLORADO_CITIES, start=100))
    page_path = tmp_path / "index.html"
    js.write_queue_html(rows, str(page_path))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(page_path.as_uri())
            yield page
        finally:
            browser.close()


def visible_roles(page):
    return set(page.evaluate("""() => Array.from(document.querySelectorAll('table tbody tr'))
        .filter(tr => !tr.classList.contains('hidden-by-location'))
        .map(tr => tr.textContent.match(/Risk Analyst [0-9]+/)[0])"""))


@pytest.mark.parametrize("metro,colorado", [(False, True), (True, False), (True, True), (False, False)])
def test_region_chips_use_or_and_any_site(region_page, metro, colorado):
    region_page.locator("#metroOnlyBox").set_checked(metro)
    region_page.locator("#coloradoOnlyBox").set_checked(colorado)
    city_ids = set(range(100, 100 + len(COLORADO_CITIES)))
    expected = set()
    if metro:
        expected.update(METRO_IDS)
    if colorado:
        expected.update(COLORADO_IDS | city_ids)
    if not (metro or colorado):
        expected = set(LOCATIONS) | city_ids
    assert visible_roles(region_page) == {f"Risk Analyst {i}" for i in expected}
    chip = region_page.locator("label", has=region_page.locator("#coloradoOnlyBox"))
    assert chip.get_attribute("title") == "Colorado locations only"
    assert chip.inner_text().strip() == "Colorado only"


@pytest.mark.parametrize("metro,colorado", [(False, True), (True, False), (True, True)])
def test_region_chips_restore_and_reset(region_page, metro, colorado):
    region_page.locator("#metroOnlyBox").set_checked(metro)
    region_page.locator("#coloradoOnlyBox").set_checked(colorado)
    expected = visible_roles(region_page)
    region_page.reload()
    assert region_page.locator("#metroOnlyBox").is_checked() == metro
    assert region_page.locator("#coloradoOnlyBox").is_checked() == colorado
    assert visible_roles(region_page) == expected
    region_page.locator("#expReset").click()
    assert not region_page.locator("#metroOnlyBox").is_checked()
    assert not region_page.locator("#coloradoOnlyBox").is_checked()
    assert region_page.evaluate("localStorage.getItem('jobScoutMetroOnly')") == "0"
    assert region_page.evaluate("localStorage.getItem('jobScoutColoradoOnly')") == "0"
    region_page.reload()
    assert not region_page.locator("#metroOnlyBox").is_checked()
    assert not region_page.locator("#coloradoOnlyBox").is_checked()
    assert len(visible_roles(region_page)) == len(LOCATIONS) + len(COLORADO_CITIES)
