"""Check noVNC animation with no keyboard/mouse input (catches idle freezes)."""
import argparse
import io
import json
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=20)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    samples, differences, errors = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale")
        page.wait_for_function("document.querySelector('#noVNC_container canvas')?.width === 1600")
        page.wait_for_timeout(3000)
        canvas = page.locator("#noVNC_container canvas")
        previous = None
        for index in range(5):
            if index:
                page.wait_for_timeout(args.seconds * 1000 / 4)
            # Canvas-only capture, no interaction or focus changes.
            data = canvas.screenshot(path=str(args.output / f"frame-{index}.png"))
            frame = Image.open(io.BytesIO(data)).convert("RGB")
            width, height = frame.size
            # Exclude controls, clock and camera toolbar; inspect the 3D view.
            crop = frame.crop((int(width*.06), int(height*.13),
                               int(width*.68), int(height*.64)))
            if previous is not None:
                differences.append(ImageChops.difference(previous, crop).getbbox() is not None)
            previous = crop
            with urllib.request.urlopen("http://127.0.0.1:18080/live-state.json?t=" + str(time.time()), timeout=10) as response:
                samples.append({"wall_time": time.time(), "state": json.load(response)})
        browser.close()
    passed = (all(differences) and not errors
              and samples[-1]["state"]["time"] > samples[0]["state"]["time"]
              and all(s["state"]["playing"] and s["state"]["transfer"]["error"] is None
                      for s in samples))
    report = {"passed": passed, "no_input": True, "seconds": args.seconds,
              "viewport_changed_each_sample": differences, "errors": errors, "samples": samples}
    (args.output / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
