from playwright.sync_api import sync_playwright
import time

URL = "https://wokwi.com/projects/445645684122269697"
OUT = "FASE3/reports/images/wokwi_running.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.goto(URL, wait_until="load")
    # Try clicking the start button by role/name variants
    for name in ["Start the simulation", "Start", "Run"]:
        try:
            page.get_by_role("button", name=name).click(timeout=2000)
            break
        except Exception:
            pass
    # Wait a bit for simulation to boot
    time.sleep(8)
    page.screenshot(path=OUT, full_page=True)
    print("Saved", OUT)
    browser.close()
