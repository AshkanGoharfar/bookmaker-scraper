"""
Market Fetcher - Fetches initial market state and applies deltas

This module handles:
1. Fetching current market state from REST API (GetGameInfo)
2. Caching markets in memory
3. Applying WebSocket deltas to update state
4. Querying full market state

Architecture:
- Uses GetGameInfo API to fetch initial odds for specific games
- Maintains in-memory cache of market data (gid -> market)
- Applies WebSocket deltas to keep state synchronized
- Provides query interface for current market state
"""

from typing import Dict, Optional, List, Any
import aiohttp
import json
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketFetcher:
    """
    Fetches and maintains market state from Bookmaker.eu

    Markets are odds for specific games (spread, moneyline, totals).
    This class:
    - Fetches initial state from REST API (GetGameInfo)
    - Applies real-time deltas from WebSocket
    - Provides query interface for current state

    Attributes:
        cookie: Session cookie for API authentication
        base_url: Base URL for Bookmaker.eu APIs
        markets: In-memory cache of market state (gid -> market data)
    """

    def __init__(self, cookie: str):
        """
        Initialize market fetcher

        Args:
            cookie: Session cookie value (e.g., "abc123")
        """
        self.cookie = cookie
        self.base_url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx"
        self.markets: Dict[str, Dict] = {}  # gid -> market data
        logger.debug("MarketFetcher initialized")

    async def fetch_initial_markets(self, game_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch initial market state from REST API (GetGameInfo)

        Calls GetGameInfo for each game ID to get full market data including:
        - Spread odds (hsprdoddst, hsprdt, vsprdoddst, vsprdt)
        - Moneyline odds (hoddst, voddst)
        - Total odds (ovoddst, ovt, unoddst, unt)
        - Multiple lines (derivatives with different indexes)

        Args:
            game_ids: List of game IDs to fetch. If None, uses games from cache.

        Returns:
            Dict of markets keyed by game ID

        Raises:
            aiohttp.ClientError: If API request fails
        """
        # TODO: Implement in next subtask (M3.1.3)
        raise NotImplementedError("fetch_initial_markets not yet implemented")

    def apply_delta(self, delta_message: Dict) -> None:
        """
        Apply WebSocket delta to update market state

        Deltas are incremental updates to odds. This method:
        1. Finds the game in cache (by gid)
        2. Updates the market data (mkt field)
        3. Creates new entry if game not in cache

        Args:
            delta_message: Parsed WebSocket message with odds update

        Example delta:
            {
                "gid": 47414947,
                "mkt": {"s": [{"h": -360, "hp": 1.5, "v": 250, "vp": -1.5}]}
            }
        """
        # TODO: Implement in M3.1.4
        raise NotImplementedError("apply_delta not yet implemented")

    def get_market_state(self, game_id: str) -> Optional[Dict]:
        """
        Get current market state for a game

        Args:
            game_id: Game ID to query

        Returns:
            Market data dict or None if not found

        Example return:
            {
                "gid": 47414947,
                "htm": "Team A",
                "vtm": "Team B",
                "derivatives": {
                    "line": [{
                        "hoddst": "-366",
                        "hsprdt": "-5.5",
                        ...
                    }]
                }
            }
        """
        # TODO: Implement in M3.1.5
        raise NotImplementedError("get_market_state not yet implemented")

    def get_all_markets(self) -> Dict[str, Dict]:
        """
        Get all cached markets

        Returns:
            Dict of all markets keyed by game ID
        """
        return self.markets.copy()
