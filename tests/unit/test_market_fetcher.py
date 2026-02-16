"""Unit tests for MarketFetcher"""

import pytest
from src.market.market_fetcher import MarketFetcher


class TestMarketFetcher:
    """Test cases for MarketFetcher class"""

    def test_init_creates_instance(self):
        """Test that __init__ creates MarketFetcher instance"""
        fetcher = MarketFetcher(cookie="test_cookie_123")

        assert fetcher.cookie == "test_cookie_123"
        assert fetcher.base_url == "https://be.bookmaker.eu/gateway/BetslipProxy.aspx"
        assert fetcher.markets == {}

    def test_init_stores_cookie_correctly(self):
        """Test that cookie is stored correctly"""
        fetcher = MarketFetcher(cookie="my_session_abc")

        assert fetcher.cookie == "my_session_abc"

    def test_markets_initialized_as_empty_dict(self):
        """Test that markets cache starts as empty dict"""
        fetcher = MarketFetcher("cookie")

        assert isinstance(fetcher.markets, dict)
        assert len(fetcher.markets) == 0

    def test_get_all_markets_returns_copy(self):
        """Test that get_all_markets returns a copy of markets dict"""
        fetcher = MarketFetcher("cookie")
        fetcher.markets = {"game1": {"odds": 1.5}}

        result = fetcher.get_all_markets()

        assert result == {"game1": {"odds": 1.5}}
        assert result is not fetcher.markets  # Should be a copy, not same object

    def test_get_all_markets_returns_empty_dict_initially(self):
        """Test that get_all_markets returns empty dict for new instance"""
        fetcher = MarketFetcher("cookie")

        result = fetcher.get_all_markets()

        assert result == {}
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fetch_initial_markets_calls_api_for_each_game(self):
        """Test that fetch_initial_markets calls GetGameInfo API for each game ID"""
        from unittest.mock import AsyncMock, patch
        import json

        fetcher = MarketFetcher("test_cookie")

        # Mock API response for GetGameInfo
        mock_response_data = {
            "game": [{
                "idgm": "47401065",
                "htm": "Murray State",
                "vtm": "Belmont",
                "uuid": "ABC-123",
                "idspt": "CBB",
                "idlg": "4",
                "LiveGame": True,
                "Derivatives": {
                    "line": [{
                        "s_ml": 1,
                        "hoddst": "-366",
                        "voddst": "293",
                        "hsprdoddst": "-117",
                        "hsprdt": "-5.5",
                        "vsprdoddst": "-102",
                        "vsprdt": "5.5",
                        "ovoddst": "-111",
                        "ovt": "151",
                        "unoddst": "-107",
                        "unt": "151",
                        "index": "0"
                    }]
                }
            }]
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response

            # Execute
            markets = await fetcher.fetch_initial_markets(game_ids=["47401065"])

            # Assert API was called
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "ASP.NET_SessionId=test_cookie" in call_kwargs["headers"]["Cookie"]

            # Assert market was returned
            assert "47401065" in markets
            assert markets["47401065"]["htm"] == "Murray State"
            assert markets["47401065"]["vtm"] == "Belmont"

    @pytest.mark.asyncio
    async def test_fetch_initial_markets_caches_results(self):
        """Test that fetched markets are cached in self.markets"""
        from unittest.mock import AsyncMock, patch

        fetcher = MarketFetcher("cookie")

        mock_response_data = {
            "game": [{
                "idgm": "123",
                "htm": "Team A",
                "vtm": "Team B",
                "Derivatives": {"line": [{"s_ml": 1}]}
            }]
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response

            await fetcher.fetch_initial_markets(game_ids=["123"])

            # Verify cached
            assert "123" in fetcher.markets
            assert fetcher.markets["123"]["htm"] == "Team A"

    @pytest.mark.asyncio
    async def test_fetch_initial_markets_handles_multiple_games(self):
        """Test that fetch_initial_markets can fetch multiple games"""
        from unittest.mock import AsyncMock, patch, call

        fetcher = MarketFetcher("cookie")

        # Create two different mock responses
        mock_response_1 = AsyncMock()
        mock_response_1.status = 200
        mock_response_1.json = AsyncMock(return_value={
            "game": [{"idgm": "100", "htm": "Team A", "vtm": "Team B", "Derivatives": {"line": []}}]
        })

        mock_response_2 = AsyncMock()
        mock_response_2.status = 200
        mock_response_2.json = AsyncMock(return_value={
            "game": [{"idgm": "200", "htm": "Team C", "vtm": "Team D", "Derivatives": {"line": []}}]
        })

        with patch('aiohttp.ClientSession.post') as mock_post:
            # Return different responses for each call
            mock_post.return_value.__aenter__.side_effect = [mock_response_1, mock_response_2]

            markets = await fetcher.fetch_initial_markets(game_ids=["100", "200"])

            # Should have called API twice
            assert mock_post.call_count == 2

            # Should have both games
            assert "100" in markets
            assert "200" in markets
            assert markets["100"]["htm"] == "Team A"
            assert markets["200"]["htm"] == "Team C"

    @pytest.mark.asyncio
    async def test_fetch_initial_markets_handles_api_error_gracefully(self):
        """Test that fetch_initial_markets handles API errors gracefully (logs and continues)"""
        from unittest.mock import AsyncMock, patch

        fetcher = MarketFetcher("cookie")

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response

            # Should NOT raise - should handle error gracefully
            markets = await fetcher.fetch_initial_markets(game_ids=["999"])

            # Should return empty dict (no markets fetched)
            assert markets == {}
            assert "999" not in fetcher.markets

    def test_apply_delta_not_implemented(self):
        """Test that apply_delta raises NotImplementedError (temporary)"""
        fetcher = MarketFetcher("cookie")

        with pytest.raises(NotImplementedError, match="apply_delta not yet implemented"):
            fetcher.apply_delta({"gid": 123})

    def test_get_market_state_not_implemented(self):
        """Test that get_market_state raises NotImplementedError (temporary)"""
        fetcher = MarketFetcher("cookie")

        with pytest.raises(NotImplementedError, match="get_market_state not yet implemented"):
            fetcher.get_market_state("game1")
