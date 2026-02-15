"""
Visual debug - opens browser window so we can see what's happening.
Run: PYTHONPATH=. poetry run python tests/manual/visual_debug.py
"""

import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def visual_debug():
    """Open browser visibly to see what's happening"""
    username = os.getenv("BOOKMAKER_USERNAME")
    password = os.getenv("BOOKMAKER_PASSWORD")

    async with async_playwright() as p:
        # Launch browser VISIBLE (not headless) and SLOW
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500  # Slow down by 500ms per action
        )
        page = await browser.new_page()

        print("Opening Bookmaker.eu...")
        await page.goto("https://www.bookmaker.eu/", timeout=30000)

        print("Waiting for page to load...")
        await page.wait_for_load_state("networkidle", timeout=15000)

        # Take screenshot
        await page.screenshot(path="logs/debug_homepage.png")
        print("Screenshot saved to logs/debug_homepage.png")

        # Check what we see
        print("\nChecking for login fields...")
        account = await page.query_selector("input#account")
        print(f"input#account found: {account is not None}")

        if account:
            print("\n✅ Login form IS visible! Attempting login...")
            try:
                await page.fill("input#account", username)
                await page.fill("input#password", password)
                print("Credentials filled, clicking login...")
                await page.click("input[type='submit'][value='Login']")
                await page.wait_for_load_state("networkidle", timeout=15000)
                print("✅ Login button clicked!")

                # Check cookies
                cookies = await page.context.cookies()
                print(f"\nFound {len(cookies)} cookies")
                for c in cookies[:5]:  # Show first 5
                    print(f"  - {c['name']}: {c['value'][:20]}...")

            except Exception as e:
                print(f"❌ Error during login: {e}")
        else:
            print("\n❌ Login form NOT visible!")
            print("The page might be geo-blocked or showing different content.")

        print("\nKeeping browser open for 20 seconds so you can inspect...")
        await asyncio.sleep(20)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(visual_debug())
