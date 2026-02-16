"""
Message Enricher - Enriches parsed messages with reference data

Combines parsed WebSocket messages with reference data (sports, leagues, games)
to add human-readable context.
"""

import logging
from typing import Dict, Optional
from src.data.reference_loader import ReferenceDataLoader
from src.parser.message_parser import MessageParser

logger = logging.getLogger(__name__)


class MessageEnricher:
    """Enriches parsed messages with reference data"""

    def __init__(self, reference_data: ReferenceDataLoader):
        """
        Initialize the message enricher

        Args:
            reference_data: Loaded reference data (sports, leagues, games)
        """
        self.reference_data = reference_data
        self.parser = MessageParser()

    def enrich(self, message: Dict) -> Dict:
        """
        Enrich message with human-readable data

        Takes a parsed message and adds:
        - Sport name
        - League name
        - Game name (team names)
        - Market type
        - Formatted odds data

        Args:
            message: Parsed message dict from MessageParser

        Returns:
            Enriched message dict with additional human-readable fields
        """
        # Start with original message
        enriched = message.copy()

        # Add sport name
        if 'sid' in message:
            sport_name = self.reference_data.get_sport_name(message['sid'])
            enriched['sport_name'] = sport_name

        # Add league name
        if 'lid' in message:
            league_name = self.reference_data.get_league_name(message['lid'])
            enriched['league_name'] = league_name

        # Add game info (teams)
        if 'gid' in message:
            game_info = self.reference_data.get_game_info(message['gid'])

            if game_info:
                home_team = game_info.get('htm', 'Home Team')
                away_team = game_info.get('vtm', 'Away Team')

                enriched['home_team'] = home_team
                enriched['away_team'] = away_team
                enriched['game_name'] = f"{away_team} @ {home_team}"
                enriched['is_live_game'] = game_info.get('LiveGame', False)
            else:
                # Game not found in cache - use fallback
                enriched['game_name'] = f"Game #{message['gid']}"
                logger.debug(f"Game {message['gid']} not found in reference data")

        # Add market type
        enriched['market_type'] = self.parser.infer_market_type(message)

        # Add normalized odds data
        odds_data = self.parser.extract_odds_data(message)
        if odds_data:
            enriched['odds_data'] = odds_data

        # Add live status
        enriched['is_live'] = self.parser.is_live(message)

        return enriched

    def enrich_batch(self, messages: list) -> list:
        """
        Enrich a batch of messages

        Args:
            messages: List of parsed message dicts

        Returns:
            List of enriched message dicts
        """
        return [self.enrich(msg) for msg in messages]
