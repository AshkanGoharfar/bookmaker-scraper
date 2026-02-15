"""Unit tests for BookmakerAuth"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.auth.bookmaker_auth import BookmakerAuth, AuthenticationError


class TestBookmakerAuth:
    """Test cases for BookmakerAuth class"""

    def test_init_creates_instance(self):
        """Test that __init__ creates BookmakerAuth instance"""
        auth = BookmakerAuth(username="test_user", password="test_pass")

        assert auth.username == "test_user"
        assert auth.password == "test_pass"
        assert auth.session_cookie is None

    def test_init_stores_credentials(self):
        """Test that credentials are stored correctly"""
        auth = BookmakerAuth(username="john_doe", password="secret123")

        assert auth.username == "john_doe"
        assert auth.password == "secret123"

    @pytest.mark.asyncio
    async def test_login_launches_browser(self):
        """Test that login launches Playwright browser"""
        with patch('src.auth.bookmaker_auth.async_playwright') as mock_pw:
            # Setup mocks
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock()
            mock_page.fill = AsyncMock()
            mock_page.click = AsyncMock()
            mock_page.wait_for_url = AsyncMock()
            mock_page.context.cookies = AsyncMock(return_value=[
                {'name': 'session_id', 'value': 'test_cookie_123'}
            ])

            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = AsyncMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.return_value.__aenter__.return_value = mock_playwright

            # Execute
            auth = BookmakerAuth("test_user", "test_pass")
            cookie = await auth.login()

            # Assert
            mock_playwright.chromium.launch.assert_called_once()
            assert cookie == "test_cookie_123"
            assert auth.session_cookie == "test_cookie_123"

    @pytest.mark.asyncio
    async def test_login_retries_on_transient_failure(self):
        """Test that login retries on ConnectionError"""
        with patch('src.auth.bookmaker_auth.async_playwright') as mock_pw:
            # Setup: Fail twice, succeed third time
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock(side_effect=[
                ConnectionError("Network error"),  # 1st attempt
                ConnectionError("Network error"),  # 2nd attempt
                None  # 3rd attempt succeeds
            ])
            mock_page.fill = AsyncMock()
            mock_page.click = AsyncMock()
            mock_page.wait_for_url = AsyncMock()
            mock_page.context.cookies = AsyncMock(return_value=[
                {'name': 'session_id', 'value': 'success_cookie'}
            ])

            mock_browser = AsyncMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = AsyncMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.return_value.__aenter__.return_value = mock_playwright

            # Execute
            auth = BookmakerAuth("user", "pass")
            cookie = await auth.login()

            # Assert
            assert mock_page.goto.call_count == 3  # Retried 3 times
            assert cookie == "success_cookie"

    def test_get_cookie_header_formats_correctly(self):
        """Test that cookie is formatted for headers"""
        auth = BookmakerAuth("user", "pass")
        auth.session_cookie = "abc123xyz"

        result = auth.get_cookie_header()

        assert result == "session_id=abc123xyz"

    def test_get_cookie_header_raises_when_no_cookie(self):
        """Test that ValueError is raised if no cookie"""
        auth = BookmakerAuth("user", "pass")
        # session_cookie is None

        with pytest.raises(ValueError, match="No session cookie available"):
            auth.get_cookie_header()
