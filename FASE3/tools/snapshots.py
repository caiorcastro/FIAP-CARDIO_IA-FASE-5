from playwright.sync_api import sync_playwright
import time

urls = [
    ("http://127.0.0.1:1880/ui", "FASE3/reports/images/node_red_dashboard.png"),
    ("http://127.0.0.1:1880/", "FASE3/reports/images/node_red_flow.png")
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    for url, path in urls:
        page.goto(url, wait_until="load")
        time.sleep(2)
        page.screenshot(path=path, full_page=True)
        print("Saved", path)
    browser.close()
