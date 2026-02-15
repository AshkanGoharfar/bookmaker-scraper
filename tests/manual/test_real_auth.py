"""
Manual integration test for real Bookmaker.eu authentication.
This script tests against the REAL website (not mocked).

Run manually: poetry run python tests/manual/test_real_auth.py
"""

import asyncio
import os
from dotenv import load_dotenv
from src.auth.bookmaker_auth import BookmakerAuth

load_dotenv()


async def test_real_login():
    """Test login with real Bookmaker.eu credentials"""
    username = os.getenv("BOOKMAKER_USERNAME")
    password = os.getenv("BOOKMAKER_PASSWORD")

    if not username or not password:
        print("❌ ERROR: BOOKMAKER_USERNAME and BOOKMAKER_PASSWORD must be set in .env")
        return

    print(f"Testing login for user: {username}")
    print("-" * 50)

    auth = BookmakerAuth(username, password)

    try:
        cookie = await auth.login()
        print(f"✅ LOGIN SUCCESSFUL")
        print(f"Session cookie: {cookie[:20]}... (first 20 chars)")
        print(f"Cookie header: {auth.get_cookie_header()[:30]}...")

    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_real_login())
