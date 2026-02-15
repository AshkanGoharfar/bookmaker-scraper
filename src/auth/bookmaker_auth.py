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
    2. Fill login credentials
    3. Submit form
    4. Extract session cookie

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
            # Launch browser with anti-detection settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            logger.debug("Browser launched with anti-detection")

            try:
                # Create page with realistic user agent and viewport
                page = await browser.new_page(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )

                # Remove webdriver property (anti-detection)
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                # Login form is on the homepage in the header
                await page.goto("https://www.bookmaker.eu/", timeout=30000)
                logger.debug("Navigated to homepage")

                # Wait for page to fully load
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                logger.debug("Page loaded")

                # Add human-like delay
                await asyncio.sleep(1)

                # Wait for the account input field to be available
                await page.wait_for_selector("input#account", state="visible", timeout=10000)
                logger.debug("Login form found")

                # Human-like typing with delays
                await page.type("input#account", self.username, delay=100)  # 100ms between keystrokes
                await asyncio.sleep(0.5)
                await page.type("input#password", self.password, delay=100)
                await asyncio.sleep(0.5)
                logger.debug("Credentials filled")

                # Click login button and wait for navigation
                await page.click("input[type='submit'][value='Login']")
                logger.debug("Login button clicked")

                # Wait for navigation after login (shorter timeout)
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                await asyncio.sleep(1)  # Extra wait for any redirects
                logger.debug("Login completed")

                cookies = await page.context.cookies()
                logger.debug(f"Found {len(cookies)} cookies after login")

                # Log cookie names for debugging
                for c in cookies:
                    logger.debug(f"Cookie: {c['name']}")

                # Look for session cookies (multiple possible names)
                session_cookie = next(
                    (c['value'] for c in cookies if c['name'] in ['session_id', 'ASP.NET_SessionId', 'ASP_NET_SessionId', 'PHPSESSID']),
                    None
                )

                if not session_cookie:
                    # If no standard session cookie, just use the first meaningful cookie
                    logger.warning("Standard session cookie not found, using first available cookie")
                    if cookies:
                        session_cookie = cookies[0]['value']
                        logger.info(f"Using cookie: {cookies[0]['name']}")
                    else:
                        raise AuthenticationError("No cookies found after login")

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
