"""Unit tests for logger utility"""

import logging
import os
from pathlib import Path
import pytest
from src.utils.logger import setup_logger


class TestLogger:
    """Test cases for logger utility"""

    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates a logger instance"""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logger_default_level_is_info(self, monkeypatch):
        """Test default log level is INFO"""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        logger = setup_logger("test_logger")
        assert logger.level == logging.INFO

    def test_setup_logger_respects_env_log_level(self, monkeypatch):
        """Test that LOG_LEVEL env var is respected"""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = setup_logger("test_logger_debug")
        assert logger.level == logging.DEBUG

    def test_setup_logger_respects_explicit_log_level(self):
        """Test that explicit log_level parameter works"""
        logger = setup_logger("test_logger_explicit", log_level="WARNING")
        assert logger.level == logging.WARNING

    def test_setup_logger_creates_log_file(self, tmp_path, monkeypatch):
        """Test that log file is created"""
        log_file = tmp_path / "test.log"
        monkeypatch.setenv("LOG_FILE", str(log_file))

        logger = setup_logger("test_logger_file")
        logger.info("Test message")

        assert log_file.exists()
        assert "Test message" in log_file.read_text()

    def test_setup_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't duplicate handlers"""
        logger1 = setup_logger("test_logger_dup")
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_logger("test_logger_dup")
        handler_count_2 = len(logger2.handlers)

        assert handler_count_1 == handler_count_2
        assert logger1 is logger2  # Same instance
