"""Unit tests for HealthMonitor"""

import pytest
import time
from src.monitoring.health_monitor import HealthMonitor, ConnectionState, HealthStatus


class TestHealthMonitor:
    """Test cases for HealthMonitor class"""

    def test_init_creates_instance(self):
        """Test that __init__ creates HealthMonitor instance"""
        monitor = HealthMonitor()

        assert monitor.stale_threshold == 60
        assert monitor.error_rate_threshold == 0.10
        assert monitor.total_messages == 0
        assert monitor.total_errors == 0
        assert monitor.connection_state == ConnectionState.DISCONNECTED

    def test_track_message_increments_count(self):
        """Test that track_message increments message count"""
        monitor = HealthMonitor()

        monitor.track_message()
        assert monitor.total_messages == 1

        monitor.track_message()
        assert monitor.total_messages == 2

    def test_track_message_updates_last_message_time(self):
        """Test that track_message updates last message timestamp"""
        monitor = HealthMonitor()

        assert monitor.last_message_time is None

        monitor.track_message()
        assert monitor.last_message_time is not None
        assert isinstance(monitor.last_message_time, float)

    def test_track_error_increments_count(self):
        """Test that track_error increments error count"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.track_error("test_error", "Test error message")
        assert monitor.total_errors == 1

        monitor.track_error("another_error", "Another test")
        assert monitor.total_errors == 2

    def test_track_error_stores_error_record(self):
        """Test that track_error stores error details"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.track_error("parser_error", "Failed to parse JSON")

        assert len(monitor.recent_errors) == 1
        error = monitor.recent_errors[0]
        assert error["type"] == "parser_error"
        assert error["message"] == "Failed to parse JSON"
        assert "timestamp" in error

    def test_set_connection_state_updates_state(self):
        """Test that set_connection_state updates connection state"""
        monitor = HealthMonitor(enable_alerts=False)

        assert monitor.connection_state == ConnectionState.DISCONNECTED

        monitor.set_connection_state(ConnectionState.CONNECTED)
        assert monitor.connection_state == ConnectionState.CONNECTED

    def test_check_stale_data_returns_false_when_fresh(self):
        """Test that check_stale_data returns False for fresh data"""
        monitor = HealthMonitor(stale_threshold_seconds=60, enable_alerts=False)

        monitor.track_message()
        assert monitor.check_stale_data() is False

    def test_check_stale_data_returns_true_when_stale(self):
        """Test that check_stale_data returns True for stale data"""
        monitor = HealthMonitor(stale_threshold_seconds=1, enable_alerts=False)

        monitor.track_message()
        time.sleep(1.1)  # Wait longer than threshold

        assert monitor.check_stale_data() is True

    def test_check_stale_data_returns_false_when_no_messages(self):
        """Test that check_stale_data returns False when no messages yet"""
        monitor = HealthMonitor(enable_alerts=False)

        assert monitor.last_message_time is None
        assert monitor.check_stale_data() is False

    def test_get_error_rate_calculates_correctly(self):
        """Test that get_error_rate calculates error percentage"""
        monitor = HealthMonitor(enable_alerts=False)

        # 2 errors out of 10 messages = 20%
        for _ in range(10):
            monitor.track_message()

        monitor.track_error("error1", "Test")
        monitor.track_error("error2", "Test")

        error_rate = monitor.get_error_rate()
        assert error_rate == pytest.approx(0.2, 0.01)  # 20%

    def test_get_error_rate_returns_zero_when_no_messages(self):
        """Test that get_error_rate returns 0 when no messages"""
        monitor = HealthMonitor(enable_alerts=False)

        assert monitor.get_error_rate() == 0.0

    def test_get_messages_per_second(self):
        """Test that get_messages_per_second calculates throughput"""
        monitor = HealthMonitor()

        for _ in range(10):
            monitor.track_message()

        msg_per_sec = monitor.get_messages_per_second()
        assert msg_per_sec > 0  # Should be positive

    def test_get_uptime_seconds(self):
        """Test that get_uptime_seconds returns elapsed time"""
        monitor = HealthMonitor()

        time.sleep(0.1)
        uptime = monitor.get_uptime_seconds()

        assert uptime >= 0.1
        assert uptime < 1.0  # Should be less than 1 second

    def test_get_health_status_healthy(self):
        """Test that get_health_status returns HEALTHY when all is well"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.set_connection_state(ConnectionState.CONNECTED)
        monitor.track_message()

        status = monitor.get_health_status()
        assert status == HealthStatus.HEALTHY

    def test_get_health_status_unhealthy_when_disconnected(self):
        """Test that get_health_status returns UNHEALTHY when disconnected"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.set_connection_state(ConnectionState.DISCONNECTED)

        status = monitor.get_health_status()
        assert status == HealthStatus.UNHEALTHY

    def test_get_health_status_unhealthy_when_error(self):
        """Test that get_health_status returns UNHEALTHY when error state"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.set_connection_state(ConnectionState.ERROR)

        status = monitor.get_health_status()
        assert status == HealthStatus.UNHEALTHY

    def test_get_health_status_degraded_when_stale(self):
        """Test that get_health_status returns DEGRADED when data stale"""
        monitor = HealthMonitor(stale_threshold_seconds=1, enable_alerts=False)

        monitor.set_connection_state(ConnectionState.CONNECTED)
        monitor.track_message()
        time.sleep(1.1)

        status = monitor.get_health_status()
        assert status == HealthStatus.DEGRADED

    def test_get_metrics_returns_all_metrics(self):
        """Test that get_metrics returns complete metrics dict"""
        monitor = HealthMonitor(enable_alerts=False)

        monitor.set_connection_state(ConnectionState.CONNECTED)
        monitor.track_message()
        monitor.track_error("test", "test error")

        metrics = monitor.get_metrics()

        assert "health_status" in metrics
        assert "connection_state" in metrics
        assert "total_messages" in metrics
        assert "total_errors" in metrics
        assert "error_rate" in metrics
        assert "messages_per_second" in metrics
        assert "uptime_seconds" in metrics

    def test_reset_metrics_clears_all_data(self):
        """Test that reset_metrics clears all metrics"""
        monitor = HealthMonitor(enable_alerts=False)

        # Add some data
        monitor.track_message()
        monitor.track_message()
        monitor.track_error("test", "test")

        assert monitor.total_messages == 2
        assert monitor.total_errors == 1

        # Reset
        monitor.reset_metrics()

        assert monitor.total_messages == 0
        assert monitor.total_errors == 0
        assert monitor.last_message_time is None
        assert len(monitor.recent_errors) == 0
