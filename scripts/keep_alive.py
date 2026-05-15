"""
scripts/keep_alive.py

Playwright automation that opens the MoneyWise AI Streamlit app and waits
for it to fully render.  Used by GitHub Actions every 6 hours to prevent
Streamlit Community Cloud from putting the app to sleep due to inactivity.

Environment variables (set as GitHub Actions secrets / env):
    STREAMLIT_APP_URL    Public URL of the deployed app  (REQUIRED)
    KEEP_ALIVE_WAIT_MS   Extra ms to hold after render   (default: 8000)

Usage:
    playwright install chromium --with-deps
    python scripts/keep_alive.py
"""

import asyncio
import os
import sys

# ── Configuration from environment ────────────────────────────────────────────
STREAMLIT_APP_URL  = os.environ.get("STREAMLIT_APP_URL", "").strip()
KEEP_ALIVE_WAIT_MS = int(os.environ.get("KEEP_ALIVE_WAIT_MS", "8000"))

# Selector that Streamlit always renders when the app is ready
_ST_APP_SELECTOR   = "[data-testid='stApp']"
_PAGE_TIMEOUT_MS   = 90_000   # 90 s total navigation timeout
_RENDER_TIMEOUT_MS = 60_000   # 60 s for Streamlit root element to appear


async def run() -> None:
    """Main async entry-point — open the app, wait, close cleanly."""

    # ── Pre-flight checks ──────────────────────────────────────────────────────
    if not STREAMLIT_APP_URL:
        print(
            "[KeepAlive] ❌  STREAMLIT_APP_URL is not set.\n"
            "            Add it as a GitHub Actions secret (Settings → Secrets → Actions).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[KeepAlive] Target URL  : {STREAMLIT_APP_URL}")
    print(f"[KeepAlive] Extra wait  : {KEEP_ALIVE_WAIT_MS} ms")
    print("[KeepAlive] Launching Chromium (headless)…")

    # Late import so the module is importable even when Playwright isn't installed
    from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError  # noqa: PLC0415

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(
            # Mimic a real browser so Streamlit Cloud doesn't block the request
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
                "MoneyWiseKeepAlive/1.0"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()

        try:
            # ── Step 1: Navigate ───────────────────────────────────────────────
            print("[KeepAlive] Navigating to app…")
            response = await page.goto(
                STREAMLIT_APP_URL,
                wait_until="domcontentloaded",
                timeout=_PAGE_TIMEOUT_MS,
            )
            http_status = response.status if response else "N/A"
            print(f"[KeepAlive] HTTP status : {http_status}")

            # ── Step 2: Wait for Streamlit root element ────────────────────────
            print("[KeepAlive] Waiting for Streamlit app element…")
            try:
                await page.wait_for_selector(
                    _ST_APP_SELECTOR,
                    state="visible",
                    timeout=_RENDER_TIMEOUT_MS,
                )
                print("[KeepAlive] ✅ Streamlit app element is visible")
            except PWTimeoutError:
                # App might still be in wake-up spinner state — that's fine.
                # The HTTP request itself already prevents sleep.
                print(
                    "[KeepAlive] ⚠️  Streamlit root selector not found within timeout.\n"
                    "            The app is likely waking up — the ping was still received."
                )

            # ── Step 3: Extra dwell time ───────────────────────────────────────
            print(f"[KeepAlive] Holding for additional {KEEP_ALIVE_WAIT_MS} ms…")
            await page.wait_for_timeout(KEEP_ALIVE_WAIT_MS)

            # ── Step 4: Report & close ─────────────────────────────────────────
            title = await page.title()
            print(f"[KeepAlive] Page title  : {title!r}")
            print("[KeepAlive] ✅ Keep-alive ping complete.")

        except Exception as exc:
            print(f"[KeepAlive] ❌ Unexpected error: {exc}", file=sys.stderr)
            await context.close()
            await browser.close()
            sys.exit(1)

        finally:
            await context.close()
            await browser.close()
            print("[KeepAlive] Browser closed cleanly.")


if __name__ == "__main__":
    asyncio.run(run())
