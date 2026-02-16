"""
Message Parser - Parses WebSocket STOMP messages

Extracts JSON data from STOMP MESSAGE frames and infers market types
from the message structure.
"""

import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class MessageParser:
    """Parses WebSocket messages and extracts betting data"""

    @staticmethod
    def parse_message(raw_body: str) -> Optional[Dict]:
        """
        Extract JSON from STOMP MESSAGE frame body

        Args:
            raw_body: Raw message body from STOMP frame (may contain JSON array + null terminator)

        Returns:
            Parsed message dict, or None if parsing fails
        """
        try:
            # Remove null terminator and whitespace
            clean_body = raw_body.rstrip('\x00\n\r ')

            if not clean_body:
                return None

            # Parse as JSON (usually an array with one message)
            parsed = json.loads(clean_body)

            # If it's a list, return first item
            if isinstance(parsed, list):
                return parsed[0] if parsed else None

            # If it's already a dict, return it
            if isinstance(parsed, dict):
                return parsed

            return None

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning(f"Failed to parse message: {e}")
            return None

    @staticmethod
    def parse_batch(raw_body: str) -> List[Dict]:
        """
        Parse batch of messages (JSON array)

        Args:
            raw_body: Raw message body that may contain multiple messages

        Returns:
            List of parsed message dicts
        """
        try:
            clean_body = raw_body.rstrip('\x00\n\r ')

            if not clean_body:
                return []

            parsed = json.loads(clean_body)

            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                return []

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse batch: {e}")
            return []

    @staticmethod
    def infer_market_type(message: Dict) -> str:
        """
        Infer market type from message structure

        The market type is determined by which key exists in the 'mkt' object:
        - 's' = Spread (point spread)
        - 'm' = Moneyline
        - 't' = Totals (over/under)

        Args:
            message: Parsed message dict

        Returns:
            Human-readable market type string
        """
        if 'mkt' not in message:
            # No market data - might be a status update
            return "Status Update"

        mkt = message['mkt']

        # Check which market type is present
        if 's' in mkt:
            return "Point Spread"
        elif 'm' in mkt:
            return "Moneyline"
        elif 't' in mkt:
            return "Total Points (Over/Under)"
        else:
            return "Other Market"

    @staticmethod
    def extract_odds_data(message: Dict) -> Optional[Dict]:
        """
        Extract odds data from market structure

        Returns a normalized dict with home/away odds and points (if applicable)

        Args:
            message: Parsed message dict

        Returns:
            Dict with odds data, or None if not available
        """
        if 'mkt' not in message:
            return None

        mkt = message['mkt']
        market_type = MessageParser.infer_market_type(message)

        if 's' in mkt and mkt['s']:
            # Spread market
            spread = mkt['s'][0]
            return {
                "type": "spread",
                "home_odds": spread.get('h'),
                "home_points": spread.get('hp'),
                "away_odds": spread.get('v'),
                "away_points": spread.get('vp'),
                "status": spread.get('s')
            }

        elif 'm' in mkt and mkt['m']:
            # Moneyline market
            ml = mkt['m'][0]
            return {
                "type": "moneyline",
                "home_odds": ml.get('h'),
                "away_odds": ml.get('v'),
                "status": ml.get('s')
            }

        elif 't' in mkt and mkt['t']:
            # Totals market
            total = mkt['t'][0]
            return {
                "type": "totals",
                "over_odds": total.get('h'),
                "over_points": total.get('hp'),
                "under_odds": total.get('v'),
                "under_points": total.get('vp'),
                "status": total.get('s')
            }

        return None

    @staticmethod
    def is_live(message: Dict) -> bool:
        """Check if the game is live"""
        # lvg == 2 means live game
        return message.get('lvg') == 2
