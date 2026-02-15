"""
Helper script to inspect the Bookmaker.eu login page structure.
Opens browser in non-headless mode so we can see the page and find correct selectors.

Run: PYTHONPATH=. poetry run python tests/manual/inspect_login_page.py
"""

import asyncio
from playwright.async_api import async_playwright


async def inspect_login_page():
    """Inspect login page to find correct form field selectors"""
    async with async_playwright() as p:
        # Launch browser in NON-headless mode (visible)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Opening Bookmaker.eu login page...")
        await page.goto("https://www.bookmaker.eu/login", timeout=30000)

        print("\nPage opened! Waiting 30 seconds for you to inspect...")
        print("Please look at the page and find the login form field names/IDs")

        # Wait 30 seconds for manual inspection
        await asyncio.sleep(30)

        # Try to get page content
        print("\nTrying to find input fields...")
        inputs = await page.query_selector_all("input")
        print(f"Found {len(inputs)} input fields")

        for i, input_elem in enumerate(inputs):
            name = await input_elem.get_attribute("name")
            id_attr = await input_elem.get_attribute("id")
            type_attr = await input_elem.get_attribute("type")
            placeholder = await input_elem.get_attribute("placeholder")

            print(f"\nInput {i+1}:")
            print(f"  name: {name}")
            print(f"  id: {id_attr}")
            print(f"  type: {type_attr}")
            print(f"  placeholder: {placeholder}")

        print("\n\nPress Enter to close browser...")
        input()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_login_page())
