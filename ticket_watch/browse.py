#!/usr/bin/env python3
"""Load a page once in headless Chromium and print its visible text.

For sites that only answer real browsers (e.g. SeatPick's Vercel checkpoint,
which a browser clears by running the page's own JavaScript). One load per
run; if the checkpoint doesn't clear it says so rather than retrying.
Run browser_setup.sh first.
"""
import sys

from playwright.sync_api import sync_playwright

CHROMIUM = "/opt/pw-browsers/chromium"


def main(url, wait_s=45):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path=CHROMIUM,
                              proxy={"server": "http://127.0.0.1:45133"})
        pg = b.new_context(locale="en-US", viewport={"width": 1366, "height": 900}).new_page()
        pg.goto(url, timeout=60000)
        for _ in range(wait_s // 5):
            if "Checkpoint" not in pg.title() and pg.title():
                break
            pg.wait_for_timeout(5000)
        pg.wait_for_timeout(5000)  # let listings render
        if "Checkpoint" in pg.title():
            print(f"BLOCKED: {url} stayed on the bot checkpoint")
            return 2
        print(pg.title())
        print(pg.inner_text("body"))
        b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
