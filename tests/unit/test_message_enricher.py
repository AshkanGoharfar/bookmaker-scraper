"""Unit tests for MessageEnricher"""

import pytest
from src.parser.message_enricher import MessageEnricher
from src.data.reference_loader import ReferenceDataLoader
from unittest.mock import Mock


class TestMessageEnricher:
    """Test cases for MessageEnricher class"""

    def test_enrich_adds_sport_name(self):
        """Test that enrich adds sport name from reference data"""
        # Mock reference loader
        ref_loader = Mock(spec=ReferenceDataLoader)
        ref_loader.get_sport_name = Mock(return_value="Basketball")

        enricher = MessageEnricher(ref_loader)

        message = {"gid": 123, "sid": "CBB"}

        result = enricher.enrich(message)

        assert result["sport_name"] == "Basketball"
        ref_loader.get_sport_name.assert_called_once_with("CBB")

    def test_enrich_adds_league_name(self):
        """Test that enrich adds league name from reference data"""
        ref_loader = Mock(spec=ReferenceDataLoader)
        ref_loader.get_league_name = Mock(return_value="NBA")

        enricher = MessageEnricher(ref_loader)

        message = {"gid": 123, "lid": 4}

        result = enricher.enrich(message)

        assert result["league_name"] == "NBA"
        ref_loader.get_league_name.assert_called_once_with(4)

    def test_enrich_adds_game_info(self):
        """Test that enrich adds game info from reference data"""
        ref_loader = Mock(spec=ReferenceDataLoader)
        ref_loader.get_game_info = Mock(return_value={
            "htm": "Team A",
            "vtm": "Team B",
            "uuid": "abc-123"
        })

        enricher = MessageEnricher(ref_loader)

        message = {"gid": 123}

        result = enricher.enrich(message)

        assert result["home_team"] == "Team A"
        assert result["away_team"] == "Team B"
        assert result["game_name"] == "Team B @ Team A"
        ref_loader.get_game_info.assert_called_once_with(123)

    def test_enrich_handles_missing_game_info(self):
        """Test that enrich handles missing game info gracefully"""
        ref_loader = Mock(spec=ReferenceDataLoader)
        ref_loader.get_game_info = Mock(return_value=None)

        enricher = MessageEnricher(ref_loader)

        message = {"gid": 999}

        result = enricher.enrich(message)

        # Should not crash, adds fallback game name
        assert "home_team" not in result
        assert "away_team" not in result
        assert result["game_name"] == "Game #999"  # Fallback name

    def test_enrich_adds_market_type(self):
        """Test that enrich adds market type"""
        ref_loader = Mock(spec=ReferenceDataLoader)

        enricher = MessageEnricher(ref_loader)

        message = {
            "gid": 123,
            "mkt": {
                "s": [{"h": -110, "hp": 3.5}]
            }
        }

        result = enricher.enrich(message)

        assert result["market_type"] == "Point Spread"

    def test_enrich_preserves_original_fields(self):
        """Test that enrich preserves all original message fields"""
        ref_loader = Mock(spec=ReferenceDataLoader)
        ref_loader.get_sport_name = Mock(return_value="Basketball")

        enricher = MessageEnricher(ref_loader)

        message = {
            "gid": 123,
            "sid": "CBB",
            "mid": 456,
            "odd": -110
        }

        result = enricher.enrich(message)

        # Original fields preserved
        assert result["gid"] == 123
        assert result["sid"] == "CBB"
        assert result["mid"] == 456
        assert result["odd"] == -110
        # New field added
        assert result["sport_name"] == "Basketball"

    def test_enrich_works_with_minimal_message(self):
        """Test that enrich works with message containing only gid"""
        ref_loader = Mock(spec=ReferenceDataLoader)

        enricher = MessageEnricher(ref_loader)

        message = {"gid": 123}

        result = enricher.enrich(message)

        assert result["gid"] == 123
        assert "market_type" in result  # Always added
