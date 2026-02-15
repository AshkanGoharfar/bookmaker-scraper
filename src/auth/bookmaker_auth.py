"""
Bookmaker.eu authentication module.
Handles automated login and session cookie extraction using Playwright.
"""

import asyncio
import random
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
        self.session_cookie_name: Optional[str] = None
        self.all_cookies: list = []
        logger.debug(f"BookmakerAuth initialized for user: {username}")

    async def login(self, max_retries: int = 3, stealth_mode: bool = True) -> str:
        """
        Perform automated login with retry logic and optional stealth mode.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            stealth_mode: Enable enhanced anti-detection features (default: True)

        Returns:
            Session cookie value

        Raises:
            AuthenticationError: If login fails after all retries
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Login attempt {attempt}/{max_retries}...")
                return await self._attempt_login(stealth_mode=stealth_mode)
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

    async def _attempt_login(self, stealth_mode: bool = True) -> str:
        """
        Single login attempt (extracted for retry logic).

        Args:
            stealth_mode: Enable enhanced anti-detection features

        Returns:
            Session cookie value

        Raises:
            AuthenticationError: If login fails
            ConnectionError: If network fails
            TimeoutError: If page load times out
        """
        async with async_playwright() as p:
            # Enhanced browser launch arguments
            launch_args = [
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]

            if stealth_mode:
                logger.info("🥷 Stealth mode: Enhanced anti-detection enabled")
                launch_args.extend([
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-setuid-sandbox'
                ])

            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=launch_args
            )
            logger.debug(f"Browser launched ({'stealth' if stealth_mode else 'standard'} mode)")

            try:
                # Enhanced context options for stealth
                context_options = {
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'viewport': {'width': 1920, 'height': 1080}
                }

                if stealth_mode:
                    context_options.update({
                        'locale': 'en-US',
                        'timezone_id': 'America/New_York',
                        'permissions': ['geolocation'],
                    })

                # Create page with enhanced settings
                page = await browser.new_page(**context_options)

                # Enhanced anti-detection scripts
                if stealth_mode:
                    await page.add_init_script("""
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // Override plugins to appear real
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });

                        // Override languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });

                        // Add chrome object
                        window.chrome = { runtime: {} };

                        // Override permissions
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );

                        // Hide automation
                        delete navigator.__proto__.webdriver;
                    """)
                else:
                    # Basic anti-detection
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

                if stealth_mode:
                    # Stealth: More human-like behavior
                    # Random mouse movement
                    await page.mouse.move(random.randint(100, 300), random.randint(100, 300))
                    await asyncio.sleep(random.uniform(0.3, 0.8))

                    # Click on username field (humans click before typing)
                    await page.click("input#account")
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                    # Type with random delays (humans type unevenly)
                    for char in self.username:
                        await page.keyboard.type(char)
                        await asyncio.sleep(random.uniform(0.05, 0.20))

                    await asyncio.sleep(random.uniform(0.5, 1.0))

                    # Click on password field
                    await page.click("input#password")
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                    # Type password with random delays
                    for char in self.password:
                        await page.keyboard.type(char)
                        await asyncio.sleep(random.uniform(0.05, 0.20))

                    await asyncio.sleep(random.uniform(0.5, 1.0))

                    # Random mouse movement before clicking submit
                    await page.mouse.move(random.randint(400, 600), random.randint(300, 500))
                    await asyncio.sleep(random.uniform(0.3, 0.7))

                    logger.debug("Credentials filled (stealth mode - human-like)")

                else:
                    # Standard: Fast typing
                    await page.type("input#account", self.username, delay=100)
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

                # Store all cookies for later use
                self.all_cookies = cookies

                # Log cookie names and domains for debugging
                for c in cookies:
                    logger.debug(f"Cookie: {c['name']} (domain: {c.get('domain', 'N/A')})")

                # Look for session cookies (multiple possible names)
                session_cookie_obj = next(
                    (c for c in cookies if c['name'] in ['session_id', 'ASP.NET_SessionId', 'ASP_NET_SessionId', 'PHPSESSID']),
                    None
                )

                if not session_cookie_obj:
                    # If no standard session cookie, just use the first meaningful cookie
                    logger.warning("Standard session cookie not found, using first available cookie")
                    if cookies:
                        session_cookie_obj = cookies[0]
                        logger.info(f"Using cookie: {session_cookie_obj['name']}")
                    else:
                        raise AuthenticationError("No cookies found after login")

                self.session_cookie = session_cookie_obj['value']
                self.session_cookie_name = session_cookie_obj['name']
                logger.info(f"Authentication successful (cookie: {self.session_cookie_name})")
                return session_cookie_obj['value']

            finally:
                await browser.close()

    def get_cookie_header(self) -> str:
        """
        Format session cookie for WebSocket headers with correct name.

        Returns:
            Cookie header string (e.g., "ASP_NET_SessionId=abc123")

        Raises:
            ValueError: If no session cookie available
        """
        if not self.session_cookie or not self.session_cookie_name:
            raise ValueError("No session cookie available. Call login() first.")

        return f"{self.session_cookie_name}={self.session_cookie}"

    def get_all_cookies_header(self) -> str:
        """
        Format ALL cookies for WebSocket headers (for cross-domain compatibility).

        Returns:
            Cookie header string with all cookies

        Raises:
            ValueError: If no cookies available
        """
        if not self.all_cookies:
            raise ValueError("No cookies available. Call login() first.")

        # Format all cookies as "name1=value1; name2=value2; ..."
        cookie_pairs = [f"{c['name']}={c['value']}" for c in self.all_cookies]
        return "; ".join(cookie_pairs)


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass
