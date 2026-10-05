"""Browser acceptance and visual artifacts against the running real API, no mocked data."""
from pathlib import Path
from playwright.sync_api import sync_playwright

out=Path('artifacts/screenshots');out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000');page.locator('#source').filter().wait_for()
    page.wait_for_function("document.querySelector('#source').value.length > 0")
    page.screenshot(path=str(out/'repair-studio.png'),full_page=True)
    page.locator('#run').click()
    page.get_by_text('tests passed ·',exact=False).first.wait_for(timeout=60000)
    assert page.locator('#download').is_visible()
    page.screenshot(path=str(out/'verified-repair.png'),full_page=True)
    page.locator('[data-tab="results"]').click()
    page.get_by_text('Selected model:',exact=False).wait_for()
    page.screenshot(path=str(out/'experiments.png'),full_page=True)
    page.locator('[data-tab="benchmarks"]').click()
    page.get_by_text('External challenge · QuixBugs',exact=True).wait_for()
    page.screenshot(path=str(out/'benchmarks.png'),full_page=True)
    page.locator('[data-tab="classify"]').click()
    page.locator('#trace').fill('RecursionError: maximum recursion depth exceeded')
    page.locator('#predict').click()
    page.get_by_text('Review required ·',exact=False).wait_for()
    page.set_viewport_size({'width':390,'height':844})
    page.locator('[data-tab="repair"]').click()
    page.screenshot(path=str(out/'mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    assert not errors, errors
    browser.close()
print('Desktop, mobile, navigation, real repair and abstention checked.')
