"""
BrowserDriver - driver.py
Headless browser control for AI agents using Playwright (preferred) or
Selenium as fallback. Zero broken imports — deps are optional.

Usage:
    from BrowserDriver import BrowserDriver

    driver = BrowserDriver()
    driver.start()

    page = driver.goto("https://example.com")
    title = driver.title()
    text = driver.text("h1")
    driver.click("button#submit")
    driver.fill("input#email", "test@example.com")
    screenshot = driver.screenshot()   # bytes

    driver.stop()
"""
import base64
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class PageResult:
    url: str = ""
    title: str = ""
    text: str = ""
    html: str = ""
    screenshot_b64: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


class BrowserDriver:
    """
    Unified AI browser agent. Tries Playwright first, falls back to Selenium.

    Args:
        headless:   Run without a visible window (default: True).
        timeout:    Default element wait timeout in seconds.
        backend:    "playwright" | "selenium" | "auto" (default: "auto").
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 10.0,
        backend: str = "auto",
    ):
        self.headless = headless
        self.timeout = timeout
        self.backend = backend
        self._driver: Any = None
        self._page: Any = None
        self._pw: Any = None      # playwright instance
        self._browser: Any = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> str:
        """Start the browser. Returns the backend name actually used."""
        if self.backend in ("playwright", "auto"):
            try:
                return self._start_playwright()
            except ImportError:
                if self.backend == "playwright":
                    raise
        if self.backend in ("selenium", "auto"):
            return self._start_selenium()
        raise RuntimeError(f"Unknown backend: {self.backend!r}")

    def stop(self) -> None:
        """Close the browser."""
        try:
            if self._driver:
                self._driver.quit()
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    # ── Navigation ────────────────────────────────────────────────────────────

    def goto(self, url: str, wait_until: str = "domcontentloaded") -> "BrowserDriver":
        """Navigate to a URL."""
        if self._page:
            self._page.goto(url, wait_until=wait_until,
                            timeout=int(self.timeout * 1000))
        elif self._driver:
            self._driver.get(url)
        return self

    def title(self) -> str:
        if self._page:
            return self._page.title()
        if self._driver:
            return self._driver.title
        return ""

    def current_url(self) -> str:
        if self._page:
            return self._page.url
        if self._driver:
            return self._driver.current_url
        return ""

    # ── Interaction ───────────────────────────────────────────────────────────

    def click(self, selector: str) -> None:
        if self._page:
            self._page.click(selector, timeout=int(self.timeout * 1000))
        elif self._driver:
            self._driver.find_element("css selector", selector).click()

    def fill(self, selector: str, value: str) -> None:
        if self._page:
            self._page.fill(selector, value)
        elif self._driver:
            el = self._driver.find_element("css selector", selector)
            el.clear()
            el.send_keys(value)

    def press(self, selector: str, key: str) -> None:
        if self._page:
            self._page.press(selector, key)

    def wait_for(self, selector: str) -> None:
        if self._page:
            self._page.wait_for_selector(selector, timeout=int(self.timeout * 1000))
        else:
            time.sleep(1)

    # ── Extraction ────────────────────────────────────────────────────────────

    def text(self, selector: str = "body") -> str:
        if self._page:
            try:
                return self._page.inner_text(selector)
            except Exception:
                return ""
        if self._driver:
            try:
                return self._driver.find_element("css selector", selector).text
            except Exception:
                return ""
        return ""

    def html(self, selector: str = "html") -> str:
        if self._page:
            try:
                return self._page.inner_html(selector)
            except Exception:
                return ""
        if self._driver:
            return self._driver.page_source
        return ""

    def screenshot(self) -> bytes:
        """Take a screenshot and return raw PNG bytes."""
        if self._page:
            return self._page.screenshot()
        if self._driver:
            return base64.b64decode(self._driver.get_screenshot_as_base64())
        return b""

    def snapshot(self) -> PageResult:
        """Capture full page state including screenshot."""
        sc = self.screenshot()
        return PageResult(
            url=self.current_url(),
            title=self.title(),
            text=self.text()[:5000],
            screenshot_b64=base64.b64encode(sc).decode() if sc else "",
        )

    def evaluate(self, js: str) -> Any:
        """Run JavaScript in the page context."""
        if self._page:
            return self._page.evaluate(js)
        if self._driver:
            return self._driver.execute_script(js)
        return None

    # ── Backends ──────────────────────────────────────────────────────────────

    def _start_playwright(self) -> str:
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        return "playwright"

    def _start_selenium(self) -> str:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self._driver = webdriver.Chrome(options=opts)
        self._driver.implicitly_wait(self.timeout)
        return "selenium"
