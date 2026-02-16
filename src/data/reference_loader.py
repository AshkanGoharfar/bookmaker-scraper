"""
Reference Data Loader - Loads sports, leagues, and games from Bookmaker REST APIs

This module fetches reference data needed to enrich WebSocket messages with
human-readable context (game names, team names, sport names, league names).
"""

import aiohttp
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ReferenceDataLoader:
    """Loads and caches reference data from Bookmaker REST APIs"""

    def __init__(self, cookie: str):
        """
        Initialize the reference data loader

        Args:
            cookie: ASP.NET_SessionId cookie value for authentication
        """
        self.cookie = cookie
        self.base_url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx"

        # Cache dictionaries
        self.sports = {}      # sid -> {"name": str, "desc": str}
        self.leagues = {}     # lid -> {"name": str, "sport": str}
        self.games = {}       # gid -> {game_info}

    async def load_all(self):
        """Load all reference data (sports, leagues, games)"""
        logger.info("Loading reference data from REST APIs...")

        await self.load_sports_and_leagues()
        await self.load_games()

        logger.info(f"✅ Loaded {len(self.sports)} sports, {len(self.leagues)} leagues, {len(self.games)} games")

    async def load_sports_and_leagues(self):
        """Load sports and leagues from GetRoutingInfo API"""
        url = f"{self.base_url}/GetRoutingInfo"
        payload = {
            "o": {
                "BORequestData": {
                    "BOParameters": {
                        "BORt": {},
                        "LanguageId": "0"
                    }
                }
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Cookie": f"ASP.NET_SessionId={self.cookie}",
                    "Content-Type": "application/json"
                }

                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"GetRoutingInfo failed: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Response: {response_text[:500]}")
                        return

                    data = await response.json()
                    logger.debug(f"GetRoutingInfo response keys: {data.keys() if isinstance(data, dict) else type(data)}")

                    # Parse sports and leagues
                    self._parse_routing_info(data)

        except Exception as e:
            logger.error(f"Error loading sports/leagues: {e}")

    def _parse_routing_info(self, data: Dict):
        """Parse GetRoutingInfo response to extract sports and leagues"""
        try:
            # GetRoutingInfo returns: {"valid": true, "routedSports": [...]}
            logger.debug(f"Parsing routing info, data type: {type(data)}, keys: {data.keys() if isinstance(data, dict) else 'N/A'}")

            if not data.get("valid"):
                logger.warning("GetRoutingInfo returned invalid=false")
                return

            routed_sports = data.get("routedSports", [])
            logger.debug(f"Found {len(routed_sports)} routed sports")

            for sport_item in routed_sports:
                # Sport info
                sport_id = sport_item.get("sportId")
                sport_desc = sport_item.get("sportDesc") or sport_item.get("sportDescEn", "Unknown Sport")

                if sport_id:
                    self.sports[sport_id] = {
                        "name": sport_desc,
                        "desc": sport_desc
                    }

                # Leagues within sport
                for league in sport_item.get("routedLeagues", []):
                    league_id = league.get("leagueId")
                    league_desc = league.get("leagueDesc") or league.get("leagueDescEn", "Unknown League")

                    if league_id:
                        self.leagues[str(league_id)] = {
                            "name": league_desc,
                            "sport": sport_id,
                            "region": league.get("region", "")
                        }

            logger.info(f"Parsed {len(self.sports)} sports, {len(self.leagues)} leagues")

        except Exception as e:
            logger.error(f"Error parsing routing info: {e}")

    async def load_games(self):
        """Load games from GetDashboardSchedule API"""
        url = f"{self.base_url}/GetDashboardSchedule"
        payload = {
            "o": {
                "BORequestData": {
                    "BOParameters": {
                        "BORt": {},
                        "LanguageId": "0",
                        "LineStyle": "E",
                        "ScheduleType": "american",
                        "LinkDeriv": "true",
                        "DashboardNextHours": "0"
                    }
                }
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Cookie": f"ASP.NET_SessionId={self.cookie}",
                    "Content-Type": "application/json"
                }

                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"GetDashboardSchedule failed: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Response: {response_text[:500]}")
                        return

                    data = await response.json()
                    logger.debug(f"GetDashboardSchedule response keys: {data.keys() if isinstance(data, dict) else type(data)}")

                    # Parse games
                    self._parse_dashboard_schedule(data)

        except Exception as e:
            logger.error(f"Error loading games: {e}")

    def _parse_dashboard_schedule(self, data: Dict):
        """Parse GetDashboardSchedule response to extract games"""
        try:
            # Response format: {"Schedule": {"Data": {"Categories": [...]}}, "valid": true}
            logger.debug(f"Parsing dashboard schedule, data type: {type(data)}, keys: {data.keys() if isinstance(data, dict) else 'N/A'}")

            if not data.get("valid"):
                logger.warning("GetDashboardSchedule returned invalid=false")
                return

            schedule_data = data.get("Schedule", {}).get("Data", {})
            categories = schedule_data.get("Categories", [])
            logger.debug(f"Found {len(categories)} categories")

            for category in categories:
                sport_id = category.get("IdSport")
                sport_name = category.get("CategoryName") or category.get("CategoryNameEn", "Unknown Sport")

                # Add sport if not already present
                if sport_id and sport_id not in self.sports:
                    self.sports[sport_id] = {
                        "name": sport_name,
                        "desc": sport_name
                    }

                # Parse leagues and games within category
                leagues = category.get("Leagues", {}).get("League", [])

                for league in leagues:
                    league_id = league.get("IdLeague")
                    league_desc = league.get("Description", "Unknown League")

                    # Add league if not already present
                    if league_id and str(league_id) not in self.leagues:
                        self.leagues[str(league_id)] = {
                            "name": league_desc,
                            "sport": sport_id
                        }

                    # Parse games within league
                    date_groups = league.get("dateGroup", [])
                    for date_group in date_groups:
                        games = date_group.get("game", [])

                        for game in games:
                            # Use idgm as primary game ID
                            game_id = game.get("idgm")
                            uuid = game.get("uuid") or game.get("ParentUUID")

                            if game_id:
                                self.games[str(game_id)] = {
                                    "gid": game_id,
                                    "uuid": uuid,
                                    "htm": game.get("htm", "Home Team"),
                                    "vtm": game.get("vtm", "Away Team"),
                                    "idlg": league_id,
                                    "idspt": sport_id,
                                    "gmdt": game.get("gmdt"),
                                    "gmtm": game.get("gmtm", ""),
                                    "LiveGame": game.get("LiveGame", False),
                                    "LiveAction": game.get("LiveAction", False)
                                }

            logger.info(f"Parsed {len(self.games)} games from {len(categories)} categories")

        except Exception as e:
            logger.error(f"Error parsing dashboard schedule: {e}")
            import traceback
            traceback.print_exc()

    def get_sport_name(self, sid: str) -> str:
        """Get sport name from sport ID"""
        sport = self.sports.get(sid, {})
        return sport.get("name", f"Sport {sid}")

    def get_league_name(self, lid: Any) -> str:
        """Get league name from league ID"""
        # Convert to string for lookup
        lid_str = str(lid)
        league = self.leagues.get(lid_str, {})
        return league.get("name", f"League {lid}")

    def get_game_info(self, gid: Any) -> Optional[Dict]:
        """Get game info from game ID"""
        # Convert to string for lookup
        gid_str = str(gid)
        return self.games.get(gid_str)
