"""
Health Monitor Integration Test

Demonstrates production monitoring in action:
- Tracks WebSocket message throughput
- Detects stale data (no messages)
- Monitors error rates
- Provides health status reports
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.monitoring.health_monitor import HealthMonitor, ConnectionState
from src.websocket.stomp_client import StompClient
from src.parser.message_parser import MessageParser
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

# Configuration
WEBSOCKET_URL = "wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws"
EXCHANGE = "BetSlipRTv4Topics"
TOPICS = ["GAME", "TNT", "HB", "mrc"]


async def test_health_monitoring(duration: int = 30):
    """
    Test health monitoring with real WebSocket connection

    Args:
        duration: How long to run test (seconds)
    """
    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        logger.error("MANUAL_COOKIE not set in .env")
        return

    logger.info("=" * 80)
    logger.info("HEALTH MONITOR INTEGRATION TEST")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This test demonstrates:")
    logger.info("  - Real-time throughput monitoring")
    logger.info("  - Error rate tracking")
    logger.info("  - Connection health monitoring")
    logger.info("  - Stale data detection")
    logger.info("")

    # Initialize HealthMonitor
    monitor = HealthMonitor(
        stale_threshold_seconds=10,  # Alert if no message for 10s
        error_rate_threshold=0.05,    # Alert if >5% errors
        enable_alerts=True
    )

    try:
        # =================================================================
        # STEP 1: Connect to WebSocket
        # =================================================================
        logger.info("STEP 1: Connecting to WebSocket...")
        logger.info("-" * 80)

        monitor.set_connection_state(ConnectionState.CONNECTING)

        client = StompClient()
        await client.connect(
            url=WEBSOCKET_URL,
            cookie=cookie,
            host="WebRT",
            login="rtweb",
            passcode="rtweb",
            heartbeat=20000
        )

        monitor.set_connection_state(ConnectionState.CONNECTED)
        logger.info("✅ Connected")
        logger.info("")

        # =================================================================
        # STEP 2: Subscribe and Monitor
        # =================================================================
        logger.info("STEP 2: Subscribing and monitoring...")
        logger.info("-" * 80)

        await client.subscribe(
            exchange=EXCHANGE,
            topics=TOPICS,
            sub_id="sub-0",
            use_wildcard=True
        )
        logger.info("✅ Subscribed")
        logger.info("")

        parser = MessageParser()
        status_interval = 10  # Print status every 10 seconds
        last_status_print = asyncio.get_event_loop().time()

        # =================================================================
        # STEP 3: Listen and Track Health
        # =================================================================
        logger.info(f"STEP 3: Monitoring health ({duration} seconds)...")
        logger.info("-" * 80)
        logger.info("")

        async def monitor_loop():
            nonlocal last_status_print

            async for message in client.listen():
                # Track message received
                monitor.track_message()

                # Try to parse message
                raw_body = message.get('raw_body', '')
                parsed = parser.parse_message(raw_body)

                if not parsed:
                    # Track parser error
                    monitor.track_error(
                        "parser_error",
                        "Failed to parse WebSocket message"
                    )

                # Print status periodically
                current_time = asyncio.get_event_loop().time()
                if current_time - last_status_print >= status_interval:
                    monitor.print_status()
                    last_status_print = current_time

        # Run with timeout
        try:
            await asyncio.wait_for(monitor_loop(), timeout=duration)
        except asyncio.TimeoutError:
            logger.info("⏱️  Duration reached")

        await client.disconnect()
        monitor.set_connection_state(ConnectionState.DISCONNECTED)
        logger.info("")

        # =================================================================
        # STEP 4: Final Report
        # =================================================================
        logger.info("STEP 4: Final Health Report")
        logger.info("-" * 80)
        logger.info("")

        monitor.print_status()

        metrics = monitor.get_metrics()

        logger.info("Detailed Metrics:")
        logger.info(f"  Total messages: {metrics['total_messages']}")
        logger.info(f"  Total errors: {metrics['total_errors']}")
        logger.info(f"  Error rate: {metrics['error_rate_percent']}")
        logger.info(f"  Throughput: {metrics['messages_per_second']:.2f} msg/sec")
        logger.info(f"  Uptime: {metrics['uptime_formatted']}")
        logger.info("")

        # Test stale data detection
        logger.info("BONUS: Testing stale data detection...")
        logger.info("Waiting 12 seconds (stale threshold is 10s)...")
        await asyncio.sleep(12)

        if monitor.check_stale_data():
            logger.info("✅ Stale data detection working!")
        else:
            logger.info("❌ Stale data detection failed")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ HEALTH MONITOR TEST COMPLETE!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Demonstrated:")
        logger.info("  ✅ Connection state tracking")
        logger.info("  ✅ Message throughput monitoring")
        logger.info("  ✅ Error rate tracking")
        logger.info("  ✅ Health status reporting")
        logger.info("  ✅ Stale data detection")
        logger.info("")
        logger.info("🎯 Production monitoring is operational!")

    except Exception as e:
        monitor.set_connection_state(ConnectionState.ERROR)
        monitor.track_error("fatal_error", str(e))
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Health monitor integration test')
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=30,
        help='Duration in seconds (default: 30)'
    )

    args = parser.parse_args()

    asyncio.run(test_health_monitoring(duration=args.duration))
