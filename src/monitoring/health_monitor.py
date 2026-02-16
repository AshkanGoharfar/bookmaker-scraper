"""
Health Monitor - Production-ready monitoring and alerting

Tracks system health metrics:
- Message throughput (messages per second)
- Stale data detection (no messages received)
- Error rate monitoring (parser failures, API errors)
- Connection health (WebSocket state)
- Uptime tracking

Alerts on:
- No messages received for 60+ seconds (stale data)
- High error rate (>10% errors)
- Connection failures
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class HealthStatus(Enum):
    """Overall health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthMonitor:
    """
    Monitors system health and detects issues

    Usage:
        monitor = HealthMonitor()
        monitor.track_message()  # Call when message received
        monitor.track_error()    # Call when error occurs
        status = monitor.get_health_status()  # Check health
    """

    def __init__(
        self,
        stale_threshold_seconds: int = 60,
        error_rate_threshold: float = 0.10,
        enable_alerts: bool = True
    ):
        """
        Initialize health monitor

        Args:
            stale_threshold_seconds: Alert if no message for this many seconds
            error_rate_threshold: Alert if error rate exceeds this (0.10 = 10%)
            enable_alerts: Whether to log alerts
        """
        self.stale_threshold = stale_threshold_seconds
        self.error_rate_threshold = error_rate_threshold
        self.enable_alerts = enable_alerts

        # Metrics
        self.start_time = time.time()
        self.last_message_time: Optional[float] = None
        self.total_messages = 0
        self.total_errors = 0
        self.connection_state = ConnectionState.DISCONNECTED

        # Error tracking
        self.recent_errors: List[Dict] = []  # Last 100 errors
        self.max_recent_errors = 100

        logger.info("HealthMonitor initialized")
        logger.info(f"  Stale threshold: {stale_threshold_seconds}s")
        logger.info(f"  Error rate threshold: {error_rate_threshold * 100}%")

    def track_message(self) -> None:
        """Track that a message was received (call for every WebSocket message)"""
        self.last_message_time = time.time()
        self.total_messages += 1

    def track_error(self, error_type: str, error_message: str) -> None:
        """
        Track an error occurrence

        Args:
            error_type: Type of error (e.g., "parser_error", "api_error")
            error_message: Error details
        """
        self.total_errors += 1

        error_record = {
            "timestamp": time.time(),
            "type": error_type,
            "message": error_message
        }

        self.recent_errors.append(error_record)

        # Keep only last 100 errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)

        # Alert on high error rate
        if self.enable_alerts:
            error_rate = self.get_error_rate()
            if error_rate > self.error_rate_threshold:
                logger.warning(
                    f"⚠️  HIGH ERROR RATE: {error_rate * 100:.1f}% "
                    f"({self.total_errors} errors / {self.total_messages} messages)"
                )

    def set_connection_state(self, state: ConnectionState) -> None:
        """
        Update connection state

        Args:
            state: New connection state
        """
        old_state = self.connection_state
        self.connection_state = state

        if old_state != state:
            logger.info(f"Connection state: {old_state.value} → {state.value}")

            # Alert on connection issues
            if self.enable_alerts and state == ConnectionState.ERROR:
                logger.error("❌ Connection ERROR detected")

    def check_stale_data(self) -> bool:
        """
        Check if data is stale (no messages received recently)

        Returns:
            True if data is stale, False otherwise
        """
        if self.last_message_time is None:
            return False  # No messages yet, not considered stale

        seconds_since_last = time.time() - self.last_message_time
        is_stale = seconds_since_last > self.stale_threshold

        if is_stale and self.enable_alerts:
            logger.warning(
                f"⚠️  STALE DATA: No messages received for {seconds_since_last:.0f}s "
                f"(threshold: {self.stale_threshold}s)"
            )

        return is_stale

    def get_error_rate(self) -> float:
        """
        Calculate error rate (errors / total messages)

        Returns:
            Error rate as decimal (0.10 = 10%)
        """
        if self.total_messages == 0:
            return 0.0
        return self.total_errors / self.total_messages

    def get_messages_per_second(self) -> float:
        """
        Calculate average messages per second since start

        Returns:
            Messages per second
        """
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.total_messages / elapsed

    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds since monitor started"""
        return time.time() - self.start_time

    def get_health_status(self) -> HealthStatus:
        """
        Calculate overall health status

        Returns:
            HealthStatus enum (HEALTHY, DEGRADED, UNHEALTHY)
        """
        # Check for critical issues
        if self.connection_state == ConnectionState.ERROR:
            return HealthStatus.UNHEALTHY

        if self.connection_state == ConnectionState.DISCONNECTED:
            return HealthStatus.UNHEALTHY

        if self.check_stale_data():
            return HealthStatus.DEGRADED

        # Check error rate
        error_rate = self.get_error_rate()
        if error_rate > self.error_rate_threshold:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def get_metrics(self) -> Dict:
        """
        Get all current metrics

        Returns:
            Dict with all metrics
        """
        uptime = self.get_uptime_seconds()
        error_rate = self.get_error_rate()
        msg_per_sec = self.get_messages_per_second()
        seconds_since_last = (
            time.time() - self.last_message_time
            if self.last_message_time
            else None
        )

        return {
            "health_status": self.get_health_status().value,
            "connection_state": self.connection_state.value,
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_messages": self.total_messages,
            "total_errors": self.total_errors,
            "error_rate": error_rate,
            "error_rate_percent": f"{error_rate * 100:.2f}%",
            "messages_per_second": msg_per_sec,
            "last_message_seconds_ago": seconds_since_last,
            "is_stale": self.check_stale_data(),
            "recent_errors_count": len(self.recent_errors)
        }

    def print_status(self) -> None:
        """Print current health status to console"""
        metrics = self.get_metrics()
        status = metrics["health_status"]

        # Status emoji
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }.get(status, "❓")

        logger.info("")
        logger.info("=" * 70)
        logger.info(f"{status_emoji} HEALTH STATUS: {status.upper()}")
        logger.info("=" * 70)
        logger.info(f"Connection: {metrics['connection_state']}")
        logger.info(f"Uptime: {metrics['uptime_formatted']}")
        logger.info(f"Messages: {metrics['total_messages']} ({metrics['messages_per_second']:.1f}/sec)")
        logger.info(f"Errors: {metrics['total_errors']} ({metrics['error_rate_percent']})")

        if metrics['last_message_seconds_ago'] is not None:
            logger.info(f"Last message: {metrics['last_message_seconds_ago']:.0f}s ago")

        if metrics['is_stale']:
            logger.info("⚠️  Data is STALE!")

        logger.info("=" * 70)
        logger.info("")

    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing or manual reset)"""
        self.start_time = time.time()
        self.last_message_time = None
        self.total_messages = 0
        self.total_errors = 0
        self.recent_errors = []
        logger.info("Metrics reset")
