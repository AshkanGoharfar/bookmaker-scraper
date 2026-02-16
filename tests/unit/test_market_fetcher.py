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
    async def test_fetch_initial_markets_not_implemented(self):
        """Test that fetch_initial_markets raises NotImplementedError (temporary)"""
        fetcher = MarketFetcher("cookie")

        with pytest.raises(NotImplementedError, match="fetch_initial_markets not yet implemented"):
            await fetcher.fetch_initial_markets()

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
