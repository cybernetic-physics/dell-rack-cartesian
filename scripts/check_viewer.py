"""Exercise the real noVNC browser client across the SSH tunnel."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path("artifacts")
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1050})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale")
    page.wait_for_function("document.querySelector('#noVNC_container canvas')?.width > 100", timeout=60000)
    page.wait_for_timeout(4000)
    page.screenshot(path=str(out / "remote-viewer.png"))
    # Send a desktop shortcut and preserve both frames for inspection. This alone
    # does not assert application input; use the completed-scene interaction test.
    page.locator("#noVNC_container canvas").click(position={"x": 600, "y": 400})
    page.keyboard.press("Alt+F1")
    page.wait_for_timeout(1000)
    page.screenshot(path=str(out / "remote-input.png"))
    page.keyboard.press("Escape")
    report = {"canvas": page.locator("#noVNC_container canvas").evaluate("e=>({width:e.width,height:e.height})"),
              "errors": errors, "url": page.url}
    (out / "remote-viewer.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    browser.close()
