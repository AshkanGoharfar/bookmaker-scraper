"""Unit tests for MessageParser"""

import pytest
from src.parser.message_parser import MessageParser


class TestMessageParser:
    """Test cases for MessageParser class"""

    def test_parse_message_parses_valid_json_array(self):
        """Test that parse_message parses valid JSON array"""
        parser = MessageParser()

        raw_body = '[{"gid": 123, "mid": 456}]\x00\n'

        result = parser.parse_message(raw_body)

        assert result is not None
        assert result["gid"] == 123
        assert result["mid"] == 456

    def test_parse_message_returns_first_element(self):
        """Test that parse_message returns first element of array"""
        parser = MessageParser()

        raw_body = '[{"id": 1}, {"id": 2}]\x00\n'

        result = parser.parse_message(raw_body)

        assert result["id"] == 1  # First element

    def test_parse_message_handles_null_terminator(self):
        """Test that parse_message strips null terminator"""
        parser = MessageParser()

        raw_body = '[{"test": "value"}]\x00'

        result = parser.parse_message(raw_body)

        assert result is not None
        assert result["test"] == "value"

    def test_parse_message_returns_none_for_invalid_json(self):
        """Test that parse_message returns None for invalid JSON"""
        parser = MessageParser()

        raw_body = 'not valid json'

        result = parser.parse_message(raw_body)

        assert result is None

    def test_parse_message_returns_none_for_empty_array(self):
        """Test that parse_message returns None for empty array"""
        parser = MessageParser()

        raw_body = '[]\x00\n'

        result = parser.parse_message(raw_body)

        assert result is None

    def test_infer_market_type_identifies_spread(self):
        """Test that infer_market_type identifies spread markets"""
        parser = MessageParser()

        message = {
            "gid": 123,
            "mkt": {
                "s": [{"h": -110, "hp": 3.5}]
            }
        }

        result = parser.infer_market_type(message)

        assert result == "Point Spread"

    def test_infer_market_type_identifies_moneyline(self):
        """Test that infer_market_type identifies moneyline markets"""
        parser = MessageParser()

        message = {
            "gid": 123,
            "mkt": {
                "m": [{"h": -180, "v": 160}]
            }
        }

        result = parser.infer_market_type(message)

        assert result == "Moneyline"

    def test_infer_market_type_identifies_totals(self):
        """Test that infer_market_type identifies totals markets"""
        parser = MessageParser()

        message = {
            "gid": 123,
            "mkt": {
                "t": [{"h": -110, "hp": 215.5}]
            }
        }

        result = parser.infer_market_type(message)

        assert result == "Total Points (Over/Under)"

    def test_infer_market_type_returns_status_update_for_no_mkt(self):
        """Test that infer_market_type returns Status Update when no mkt field"""
        parser = MessageParser()

        message = {"gid": 123}

        result = parser.infer_market_type(message)

        assert result == "Status Update"

    def test_infer_market_type_returns_other_market_for_unknown_type(self):
        """Test that infer_market_type returns Other Market for unknown market types"""
        parser = MessageParser()

        message = {
            "gid": 123,
            "mkt": {
                "x": [{"unknown": "field"}]
            }
        }

        result = parser.infer_market_type(message)

        assert result == "Other Market"
