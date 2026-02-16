"""
Output Formatter - Formats enriched messages for console display

Creates human-readable, formatted output from enriched WebSocket messages.
"""

from typing import Dict
from datetime import datetime


class OutputFormatter:
    """Formats enriched messages for console output"""

    @staticmethod
    def format_odds_update(msg: Dict) -> str:
        """
        Format enriched message as human-readable string

        Args:
            msg: Enriched message dict from MessageEnricher

        Returns:
            Multi-line formatted string ready for console output
        """
        lines = []

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Header: Sport - League
        sport = msg.get('sport_name', 'Unknown Sport')
        league = msg.get('league_name', 'Unknown League')

        # Add emoji for sport type (optional, for visual appeal)
        sport_emoji = OutputFormatter._get_sport_emoji(sport)

        lines.append(f"[{timestamp}] {sport_emoji} {sport} - {league}")

        # Separator
        lines.append("━" * 70)

        # Game info
        game_name = msg.get('game_name', f"Game #{msg.get('gid', 'Unknown')}")
        lines.append(f"Game: {game_name}")

        # Add UUID for reference (if needed for debugging)
        if msg.get('uuid'):
            lines.append(f"  UUID: {msg['uuid'][:8]}...")  # First 8 chars

        # Market type
        market_type = msg.get('market_type', 'Unknown Market')
        lines.append(f"Market: {market_type}")

        # Odds details (market-specific formatting)
        odds_data = msg.get('odds_data')
        if odds_data:
            OutputFormatter._format_odds_section(lines, odds_data)
        else:
            # Fallback: display raw market data if available
            if 'mkt' in msg:
                lines.append(f"  Raw odds data: {msg['mkt']}")

        # Status indicators
        status_line = []

        if msg.get('is_live'):
            status_line.append("🔴 LIVE")

        if msg.get('is_live_game'):
            if not msg.get('is_live'):  # Don't duplicate
                status_line.append("⚽ Live Game")

        if status_line:
            lines.append(f"Status: {' | '.join(status_line)}")

        # Footer separator
        lines.append("━" * 70)

        return "\n".join(lines)

    @staticmethod
    def _format_odds_section(lines: list, odds_data: Dict):
        """Format the odds section based on market type"""

        if odds_data['type'] == 'spread':
            # Point Spread
            home_odds = odds_data.get('home_odds') or 'N/A'
            home_points = odds_data.get('home_points') or 0
            away_odds = odds_data.get('away_odds') or 'N/A'
            away_points = odds_data.get('away_points') or 0

            # Handle None values in formatting
            home_odds_str = str(home_odds) if home_odds != 'N/A' else 'N/A'
            away_odds_str = str(away_odds) if away_odds != 'N/A' else 'N/A'

            lines.append(f"  Home: {home_odds_str:>4} ({home_points:+.1f} points)")
            lines.append(f"  Away: {away_odds_str:>4} ({away_points:+.1f} points)")

        elif odds_data['type'] == 'moneyline':
            # Moneyline
            home_odds = odds_data.get('home_odds') or 'N/A'
            away_odds = odds_data.get('away_odds') or 'N/A'

            # Handle None values in formatting
            home_odds_str = str(home_odds) if home_odds != 'N/A' else 'N/A'
            away_odds_str = str(away_odds) if away_odds != 'N/A' else 'N/A'

            lines.append(f"  Home: {home_odds_str:>4}")
            lines.append(f"  Away: {away_odds_str:>4}")

        elif odds_data['type'] == 'totals':
            # Over/Under
            over_odds = odds_data.get('over_odds') or 'N/A'
            over_points = odds_data.get('over_points') or 0
            under_odds = odds_data.get('under_odds') or 'N/A'
            under_points = odds_data.get('under_points') or 0

            # Handle None values in formatting
            over_odds_str = str(over_odds) if over_odds != 'N/A' else 'N/A'
            under_odds_str = str(under_odds) if under_odds != 'N/A' else 'N/A'

            lines.append(f"  Over {over_points}: {over_odds_str:>4}")
            lines.append(f"  Under {under_points}: {under_odds_str:>4}")

    @staticmethod
    def _get_sport_emoji(sport_name: str) -> str:
        """Get emoji for sport type"""
        sport_lower = sport_name.lower()

        emoji_map = {
            'basketball': '🏀',
            'football': '🏈',
            'soccer': '⚽',
            'baseball': '⚾',
            'hockey': '🏒',
            'tennis': '🎾',
            'martial': '🥊',  # Mixed Martial Arts
            'mma': '🥊',
            'boxing': '🥊',
            'golf': '⛳',
            'cricket': '🏏',
            'volleyball': '🏐',
            'rugby': '🏉',
        }

        for keyword, emoji in emoji_map.items():
            if keyword in sport_lower:
                return emoji

        return '🎯'  # Default emoji

    @staticmethod
    def format_summary(message_count: int, duration_seconds: int, sports_seen: set, leagues_seen: set) -> str:
        """
        Format a summary of received messages

        Args:
            message_count: Total messages processed
            duration_seconds: Duration of session
            sports_seen: Set of sport names seen
            leagues_seen: Set of league names seen

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("SESSION SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Duration: {duration_seconds} seconds")
        lines.append(f"Total Messages: {message_count}")
        lines.append(f"Messages/Second: {message_count / duration_seconds:.1f}")
        lines.append(f"Sports Seen: {len(sports_seen)}")
        lines.append(f"Leagues Seen: {len(leagues_seen)}")

        if sports_seen:
            lines.append(f"\nSports: {', '.join(sorted(sports_seen))}")

        if leagues_seen and len(leagues_seen) <= 10:
            lines.append(f"Leagues: {', '.join(sorted(leagues_seen))}")

        lines.append("=" * 70)

        return "\n".join(lines)

    @staticmethod
    def format_compact(msg: Dict) -> str:
        """
        Format message in compact single-line format

        Useful for high-volume message streams where full formatting
        would be too verbose.

        Args:
            msg: Enriched message dict

        Returns:
            Single-line formatted string
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        game = msg.get('game_name', f"Game {msg.get('gid', '?')}")
        market = msg.get('market_type', '?')
        sport = msg.get('sport_name', '?')

        live = "🔴" if msg.get('is_live') else ""

        return f"[{timestamp}] {live} {sport} | {game} | {market}"
