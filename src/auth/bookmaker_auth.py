"""
Bookmaker.eu authentication module.
Handles automated login and session cookie extraction using Playwright.
"""

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

    async def login(self) -> str:
        """
        Perform automated login and extract session cookie.

        Returns:
            Session cookie value

        Raises:
            AuthenticationError: If login fails
            TimeoutError: If page load times out
        """
        logger.info(f"Authenticating as {self.username}...")

        try:
            async with async_playwright() as p:
                # Launch browser (headless mode)
                browser = await p.chromium.launch(headless=True)
                logger.debug("Browser launched")

                # Create new page
                page = await browser.new_page()
                logger.debug("New page created")

                # Navigate to login page
                await page.goto("https://www.bookmaker.eu/login", timeout=30000)
                logger.debug("Navigated to login page")

                # Fill credentials
                await page.fill("input[name='username']", self.username)
                await page.fill("input[name='password']", self.password)
                logger.debug("Credentials filled")

                # Submit form
                await page.click("button[type='submit']")
                logger.debug("Login form submitted")

                # Wait for successful login (redirects to home or dashboard)
                await page.wait_for_url("**/home", timeout=10000)
                logger.debug("Login successful, redirected to home")

                # Extract session cookie
                cookies = await page.context.cookies()
                session_cookie = next(
                    (c['value'] for c in cookies if c['name'] == 'session_id'),
                    None
                )

                if not session_cookie:
                    raise AuthenticationError("Session cookie not found after login")

                self.session_cookie = session_cookie
                logger.info("Authentication successful")

                await browser.close()
                return session_cookie

        except TimeoutError as e:
            logger.error(f"Login timeout: {e}")
            raise AuthenticationError(f"Login failed: Timeout") from e
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"Login failed: {str(e)}") from e

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
