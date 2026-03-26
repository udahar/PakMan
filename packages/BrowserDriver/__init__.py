"""
BrowserDriver
Headless browser control for AI agents. Playwright (preferred) or Selenium fallback.

Quick start:
    from BrowserDriver import BrowserDriver

    # Context manager (auto-start/stop)
    with BrowserDriver(headless=True) as b:
        b.goto("https://news.ycombinator.com")
        print(b.title())
        print(b.text("span.titleline")[:500])
        b.click("a.morelink")
        sc = b.screenshot()

    # Scrape and extract full snapshot
    with BrowserDriver() as b:
        b.goto("https://example.com")
        snap = b.snapshot()
        print(snap.title, snap.url, len(snap.text))

    # Force a specific backend
    b = BrowserDriver(backend="selenium")
    b.start()
    b.goto("https://google.com")
    b.fill("textarea[name=q]", "AntiGrav AI")
    b.press("textarea[name=q]", "Enter")
    b.wait_for("h3")
    print(b.text("h3"))
    b.stop()

Dependencies:
    pip install playwright && playwright install chromium  (preferred)
    pip install selenium  (fallback — requires chromedriver on PATH)
"""
from .driver import BrowserDriver, PageResult

__version__ = "0.1.0"
__all__ = ["BrowserDriver", "PageResult"]
