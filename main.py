#!/usr/bin/env python3
"""
Bookmaker.eu Real-Time Odds Scraper - Main Demo

This is the main entry point demonstrating the complete scraper system:
- Fetches initial market state from REST API
- Connects to WebSocket for real-time odds updates
- Applies deltas to maintain full market state
- Monitors system health
- Displays enriched, human-readable odds

Usage:
    python main.py              # Run with defaults (30 seconds)
    python main.py -d 60        # Run for 60 seconds
    python main.py --duration 120  # Run for 2 minutes

Requirements:
    - Set MANUAL_COOKIE in .env file (see .env.example)
    - WebSocket URL is auto-configured for Bookmaker.eu
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.websocket.stomp_client import StompClient
from src.market.market_fetcher import MarketFetcher
from src.data.reference_loader import ReferenceDataLoader
from src.parser.message_parser import MessageParser
from src.parser.message_enricher import MessageEnricher
from src.parser.output_formatter import OutputFormatter
from src.monitoring.health_monitor import HealthMonitor, ConnectionState
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

# Configuration with sensible defaults
WEBSOCKET_URL = os.getenv(
    "WEBSOCKET_URL",
    "wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws"
)
EXCHANGE = "BetSlipRTv4Topics"
TOPICS = ["GAME", "TNT", "HB", "mrc"]


def print_banner():
    """Print welcome banner"""
    print()
    print("=" * 80)
    print("  BOOKMAKER.EU REAL-TIME ODDS SCRAPER")
    print("  Betstamp Take-Home Assignment - Ashkan Goharfar")
    print("=" * 80)
    print()


def print_system_info(cookie_set: bool, duration: int):
    """Print system configuration"""
    print("📋 CONFIGURATION")
    print("-" * 80)
    print(f"  WebSocket URL: {WEBSOCKET_URL}")
    print(f"  Session Cookie: {'✅ Configured' if cookie_set else '❌ Missing (check .env)'}")
    print(f"  Duration: {duration} seconds")
    print(f"  Features: Market State Management + Health Monitoring")
    print()


async def run_scraper(duration: int = 30):
    """
    Run the complete scraper system

    Args:
        duration: How long to run (seconds)
    """
    # Get session cookie
    cookie = os.getenv("MANUAL_COOKIE")

    if not cookie:
        logger.error("=" * 80)
        logger.error("❌ ERROR: MANUAL_COOKIE not set!")
        logger.error("=" * 80)
        logger.error("")
        logger.error("Please follow these steps:")
        logger.error("")
        logger.error("1. Copy .env.example to .env:")
        logger.error("   cp .env.example .env")
        logger.error("")
        logger.error("2. Get your session cookie:")
        logger.error("   - Go to https://www.bookmaker.eu")
        logger.error("   - Log in to your account")
        logger.error("   - Open Browser DevTools (F12)")
        logger.error("   - Go to Application/Storage → Cookies")
        logger.error("   - Copy the value of 'ASP.NET_SessionId'")
        logger.error("")
        logger.error("3. Add it to .env:")
        logger.error("   MANUAL_COOKIE=your_session_id_here")
        logger.error("")
        logger.error("4. Run again: python main.py")
        logger.error("")
        logger.error("=" * 80)
        sys.exit(1)

    print_banner()
    print_system_info(cookie_set=True, duration=duration)

    # Statistics
    messages_processed = 0
    markets_updated = 0
    sports_seen = set()
    leagues_seen = set()
    start_time = datetime.now()

    # Initialize health monitor
    health_monitor = HealthMonitor(
        stale_threshold_seconds=10,
        error_rate_threshold=0.05,
        enable_alerts=True
    )

    try:
        # =================================================================
        # STEP 1: Load Reference Data
        # =================================================================
        logger.info("STEP 1/5: Loading reference data from REST APIs...")
        logger.info("-" * 80)

        ref_loader = ReferenceDataLoader(cookie)
        await ref_loader.load_all()

        logger.info(f"✅ Loaded:")
        logger.info(f"   • {len(ref_loader.sports)} sports")
        logger.info(f"   • {len(ref_loader.leagues)} leagues")
        logger.info(f"   • {len(ref_loader.games)} scheduled games")
        logger.info("")

        # =================================================================
        # STEP 2: Initialize Market Fetcher
        # =================================================================
        logger.info("STEP 2/5: Initializing market state manager...")
        logger.info("-" * 80)

        market_fetcher = MarketFetcher(cookie)

        # Fetch initial markets for scheduled games (if any)
        if ref_loader.games:
            game_ids = list(ref_loader.games.keys())[:5]  # First 5 games
            await market_fetcher.fetch_initial_markets(game_ids=game_ids)
            logger.info(f"✅ Fetched initial state for {len(game_ids)} games")
        else:
            logger.info("ℹ️  No scheduled games found (will track live games only)")

        logger.info("")

        # =================================================================
        # STEP 3: Initialize Parser & Enricher
        # =================================================================
        logger.info("STEP 3/5: Setting up message parser...")
        logger.info("-" * 80)

        parser = MessageParser()
        enricher = MessageEnricher(ref_loader)
        formatter = OutputFormatter()

        logger.info("✅ Parser ready (JSON → Enriched Odds)")
        logger.info("")

        # =================================================================
        # STEP 4: Connect to WebSocket
        # =================================================================
        logger.info("STEP 4/5: Connecting to WebSocket...")
        logger.info("-" * 80)
        logger.info(f"URL: {WEBSOCKET_URL}")
        logger.info(f"Exchange: {EXCHANGE}")
        logger.info(f"Topics: {', '.join(TOPICS)}")
        logger.info("")

        health_monitor.set_connection_state(ConnectionState.CONNECTING)

        client = StompClient()
        await client.connect(
            url=WEBSOCKET_URL,
            cookie=cookie,
            host="WebRT",
            login="rtweb",
            passcode="rtweb",
            heartbeat=20000
        )

        health_monitor.set_connection_state(ConnectionState.CONNECTED)
        logger.info("✅ Connected to WebSocket")
        logger.info("")

        await client.subscribe(
            exchange=EXCHANGE,
            topics=TOPICS,
            sub_id="sub-0",
            use_wildcard=True
        )

        logger.info("✅ Subscribed to real-time odds feed")
        logger.info("")

        # =================================================================
        # STEP 5: Process Real-Time Updates
        # =================================================================
        logger.info("STEP 5/5: Processing real-time odds updates...")
        logger.info("-" * 80)
        logger.info(f"Duration: {duration} seconds")
        logger.info("Format: Human-readable with full context")
        logger.info("")
        logger.info("=" * 80)
        logger.info("🔴 LIVE ODDS UPDATES")
        logger.info("=" * 80)
        logger.info("")

        # Status reporting
        last_status_time = asyncio.get_event_loop().time()
        status_interval = 10  # Print health status every 10 seconds

        async def process_messages():
            nonlocal messages_processed, markets_updated, last_status_time

            async for message in client.listen():
                # Track message received
                health_monitor.track_message()
                messages_processed += 1

                # Parse message
                raw_body = message.get('raw_body', '')
                parsed = parser.parse_message(raw_body)

                if not parsed:
                    health_monitor.track_error("parser_error", "Failed to parse message")
                    continue

                # Apply delta to market state
                if 'gid' in parsed:
                    market_fetcher.apply_delta(parsed)
                    markets_updated += 1

                # Enrich with reference data
                enriched = enricher.enrich(parsed)

                # Track statistics
                if 'sport_name' in enriched:
                    sports_seen.add(enriched['sport_name'])
                if 'league_name' in enriched:
                    leagues_seen.add(enriched['league_name'])

                # Format and display (show every 3rd message to demonstrate data quality)
                if messages_processed % 3 == 0:
                    formatted = formatter.format_odds_update(enriched)
                    print(formatted)

                # Print health status periodically
                current_time = asyncio.get_event_loop().time()
                if current_time - last_status_time >= status_interval:
                    print()
                    health_monitor.print_status()
                    last_status_time = current_time

        # Run with timeout
        try:
            await asyncio.wait_for(process_messages(), timeout=duration)
        except asyncio.TimeoutError:
            logger.info("")
            logger.info("⏱️  Duration reached, shutting down...")

        await client.disconnect()
        health_monitor.set_connection_state(ConnectionState.DISCONNECTED)

        # =================================================================
        # FINAL SUMMARY
        # =================================================================
        elapsed = (datetime.now() - start_time).total_seconds()

        print()
        print("=" * 80)
        print("✅ SCRAPER SESSION COMPLETE")
        print("=" * 80)
        print()

        summary = formatter.format_summary(
            message_count=messages_processed,
            duration_seconds=int(elapsed),
            sports_seen=sports_seen,
            leagues_seen=leagues_seen
        )
        print(summary)

        print()
        print("📊 MARKET STATE SUMMARY")
        print("-" * 80)
        print(f"  Markets tracked: {len(market_fetcher.get_all_markets())}")
        print(f"  Updates applied: {markets_updated}")
        print()

        print("💡 SYSTEM CAPABILITIES DEMONSTRATED")
        print("-" * 80)
        print("  ✅ WebSocket connection with STOMP protocol")
        print("  ✅ Real-time message parsing and enrichment")
        print("  ✅ Market state management (initial + deltas)")
        print("  ✅ Health monitoring and metrics")
        print("  ✅ Human-readable output formatting")
        print()

        print("🎯 Ready for production deployment!")
        print()

    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Interrupted by user (Ctrl+C)")
        health_monitor.set_connection_state(ConnectionState.DISCONNECTED)

    except Exception as e:
        health_monitor.set_connection_state(ConnectionState.ERROR)
        health_monitor.track_error("fatal_error", str(e))
        logger.error("")
        logger.error("=" * 80)
        logger.error(f"❌ Fatal Error: {e}")
        logger.error("=" * 80)
        logger.error("", exc_info=True)
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bookmaker.eu Real-Time Odds Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Run for 30 seconds (default)
  python main.py -d 60        # Run for 60 seconds
  python main.py --duration 120  # Run for 2 minutes

For more information, see README.md
        """
    )

    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=30,
        help='Duration in seconds (default: 30)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Bookmaker Scraper v1.0.0'
    )

    args = parser.parse_args()

    # Validate duration
    if args.duration < 1:
        logger.error("Duration must be at least 1 second")
        sys.exit(1)

    if args.duration > 600:
        logger.warning("Duration > 10 minutes may consume a lot of data")

    # Run scraper
    try:
        asyncio.run(run_scraper(duration=args.duration))
    except KeyboardInterrupt:
        logger.info("Goodbye!")
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
