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
        if game_ids is None:
            game_ids = list(self.markets.keys())

        if not game_ids:
            logger.warning("No game IDs provided to fetch_initial_markets")
            return {}

        logger.info(f"Fetching initial markets for {len(game_ids)} games...")

        # Fetch markets for each game ID
        async with aiohttp.ClientSession() as session:
            for game_id in game_ids:
                try:
                    await self._fetch_single_game_market(session, game_id)
                except Exception as e:
                    logger.error(f"Failed to fetch market for game {game_id}: {e}")
                    # Continue with other games even if one fails
                    continue

        logger.info(f"✅ Fetched {len(self.markets)} markets successfully")
        return self.markets.copy()

    async def _fetch_single_game_market(self, session: aiohttp.ClientSession, game_id: str) -> None:
        """
        Fetch market data for a single game using GetGameInfo API

        Args:
            session: aiohttp session to reuse
            game_id: Game ID to fetch

        Raises:
            aiohttp.ClientError: If API request fails
        """
        url = f"{self.base_url}/GetGameInfo"
        payload = {
            "Req": {
                "InParams": {
                    "GameId": game_id
                }
            }
        }

        headers = {
            "Cookie": f"ASP.NET_SessionId={self.cookie}",
            "Content-Type": "application/json"
        }

        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientError(
                    f"GetGameInfo API returned {response.status} for game {game_id}: {error_text}"
                )

            data = await response.json()
            logger.debug(f"GetGameInfo response for {game_id}: {str(data)[:200]}...")

            # Parse and cache the game data
            games = data.get("game", [])
            if games:
                game_data = games[0]  # GetGameInfo returns array with single game
                game_id_str = str(game_data.get("idgm", game_id))

                # Cache the full game data (includes Derivatives with market data)
                self.markets[game_id_str] = game_data
                logger.debug(f"Cached market for game {game_id_str}: {game_data.get('htm')} vs {game_data.get('vtm')}")
            else:
                logger.warning(f"No game data returned for game {game_id}")

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
        gid = delta_message.get('gid')
        if not gid:
            logger.warning("Delta missing gid, skipping")
            return

        gid_str = str(gid)

        # If game exists in cache, update it
        if gid_str in self.markets:
            # Merge delta into existing market
            market = self.markets[gid_str]

            # Update all fields from delta message
            for key, value in delta_message.items():
                if key == 'gid':
                    continue  # Skip gid (already used for lookup)

                if key == 'mkt':
                    # Merge market data (spread, moneyline, totals)
                    if 'mkt' not in market:
                        market['mkt'] = {}

                    # Update each market type in the delta
                    for market_type, market_data in value.items():
                        market['mkt'][market_type] = market_data
                else:
                    # Update other fields (lvg, mid, sid, lid, etc.)
                    market[key] = value

            logger.debug(f"Applied delta to existing market {gid_str}")
        else:
            # Game not in cache, create new entry from delta
            self.markets[gid_str] = delta_message.copy()
            logger.debug(f"Created new market entry from delta for game {gid_str}")

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
