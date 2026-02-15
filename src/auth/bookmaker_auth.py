"""
Bookmaker.eu authentication module.
Handles automated login and session cookie extraction using Playwright.
"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BookmakerAuth:
    """
    Handles authentication with Bookmaker.eu via browser automation.

    Uses Playwright to:
    1. Open browser
    2. Navigate to login page
    3. Fill credentials
    4. Submit form
    5. Extract session cookie

    Attributes:
        username: Bookmaker.eu username
        password: Bookmaker.eu password
        session_cookie: Extracted session cookie (after successful login)
    """

    def __init__(self, username: str, password: str):
        """
        Initialize authentication handler.

        Args:
            username: Bookmaker.eu username
            password: Bookmaker.eu password
        """
        self.username = username
        self.password = password
        self.session_cookie: Optional[str] = None
        logger.debug(f"BookmakerAuth initialized for user: {username}")

    async def login(self, max_retries: int = 3) -> str:
        """
        Perform automated login with retry logic.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Session cookie value

        Raises:
            AuthenticationError: If login fails after all retries
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Login attempt {attempt}/{max_retries}...")
                return await self._attempt_login()
            except (ConnectionError, TimeoutError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            except AuthenticationError:
                # Don't retry on auth errors (wrong credentials)
                raise

        raise AuthenticationError(f"Login failed after {max_retries} attempts") from last_error

    async def _attempt_login(self) -> str:
        """
        Single login attempt (extracted for retry logic).

        Returns:
            Session cookie value

        Raises:
            AuthenticationError: If login fails
            ConnectionError: If network fails
            TimeoutError: If page load times out
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            logger.debug("Browser launched")

            try:
                page = await browser.new_page()
                await page.goto("https://www.bookmaker.eu/login", timeout=30000)
                await page.fill("input[name='username']", self.username)
                await page.fill("input[name='password']", self.password)
                await page.click("button[type='submit']")
                await page.wait_for_url("**/home", timeout=10000)

                cookies = await page.context.cookies()
                session_cookie = next(
                    (c['value'] for c in cookies if c['name'] == 'session_id'),
                    None
                )

                if not session_cookie:
                    raise AuthenticationError("Session cookie not found")

                self.session_cookie = session_cookie
                logger.info("Authentication successful")
                return session_cookie

            finally:
                await browser.close()

    def get_cookie_header(self) -> str:
        """
        Format session cookie for WebSocket headers.

        Returns:
            Cookie header string (e.g., "session_id=abc123")

        Raises:
            ValueError: If no session cookie available
        """
        if not self.session_cookie:
            raise ValueError("No session cookie available. Call login() first.")

        return f"session_id={self.session_cookie}"


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass
