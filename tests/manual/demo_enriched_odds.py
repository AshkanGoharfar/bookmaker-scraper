"""
Enriched Odds Feed Demo - Human-Readable Real-Time Odds Updates

This script demonstrates the complete enriched message parser that:
1. Loads reference data (sports, leagues, games) from REST APIs
2. Connects to WebSocket and receives real-time odds deltas
3. Enriches messages with human-readable context
4. Prints formatted, professional odds updates

Usage:
    poetry run python tests/manual/demo_enriched_odds.py
    poetry run python tests/manual/demo_enriched_odds.py -d 60  # 60 seconds

What makes this "enriched":
- ✅ Game IDs → Team names ("Lakers @ Celtics")
- ✅ Sport IDs → Sport names ("Basketball")
- ✅ League IDs → League names ("NBA")
- ✅ Market types inferred ("Point Spread", "Moneyline", "Totals")
- ✅ Professional formatting with emojis and separators
- ✅ Live game indicators
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.websocket.stomp_client import StompClient
from src.data.reference_loader import ReferenceDataLoader
from src.parser.message_parser import MessageParser
from src.parser.message_enricher import MessageEnricher
from src.parser.output_formatter import OutputFormatter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Configuration
WEBSOCKET_URL = "wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws"
EXCHANGE = "BetSlipRTv4Topics"
TOPICS = ["GAME", "TNT", "HB", "mrc"]  # Focus on betting-related topics


async def run_enriched_demo(cookie: str, duration: int = 60):
    """
    Run enriched odds feed demo

    Args:
        cookie: ASP.NET_SessionId cookie value
        duration: How long to run the demo (seconds)
    """
    logger.info("=" * 80)
    logger.info("ENRICHED REAL-TIME ODDS FEED - DEMO")
    logger.info("=" * 80)
    logger.info("")

    # Statistics
    message_count = 0
    sports_seen = set()
    leagues_seen = set()
    start_time = datetime.now()

    try:
        # Step 1: Load Reference Data
        logger.info("STEP 1: Loading reference data from REST APIs...")
        logger.info("-" * 80)

        reference_loader = ReferenceDataLoader(cookie)
        await reference_loader.load_all()

        logger.info(f"✅ Loaded:")
        logger.info(f"   - {len(reference_loader.sports)} sports")
        logger.info(f"   - {len(reference_loader.leagues)} leagues")
        logger.info(f"   - {len(reference_loader.games)} games")
        logger.info("")

        # Step 2: Initialize Parser Components
        logger.info("STEP 2: Initializing message parser...")
        logger.info("-" * 80)

        parser = MessageParser()
        enricher = MessageEnricher(reference_loader)
        formatter = OutputFormatter()

        logger.info("✅ Parser components ready")
        logger.info("")

        # Step 3: Connect to WebSocket
        logger.info("STEP 3: Connecting to WebSocket...")
        logger.info("-" * 80)
        logger.info(f"URL: {WEBSOCKET_URL}")
        logger.info(f"Exchange: {EXCHANGE}")
        logger.info(f"Topics: {', '.join(TOPICS)}")
        logger.info("")

        client = StompClient()

        await client.connect(
            url=WEBSOCKET_URL,
            cookie=cookie,
            host="WebRT",
            login="rtweb",
            passcode="rtweb",
            heartbeat=20000
        )
        logger.info("✅ Connected to WebSocket")
        logger.info("")

        # Step 4: Subscribe
        logger.info("STEP 4: Subscribing to odds feed...")
        logger.info("-" * 80)

        await client.subscribe(
            exchange=EXCHANGE,
            topics=TOPICS,
            sub_id="sub-0",
            use_wildcard=True  # Get ALL messages
        )

        logger.info("✅ Subscribed successfully")
        logger.info("")

        # Step 5: Listen and Process
        logger.info("STEP 5: Listening for odds updates...")
        logger.info("-" * 80)
        logger.info(f"Duration: {duration} seconds")
        logger.info("Formatting: Human-readable with enrichment")
        logger.info("")
        logger.info("=" * 80)
        logger.info("")

        # Listen for messages with timeout
        async def listen_with_timeout():
            logger.info("Starting to listen for messages...")
            message_received_count = 0

            async for message in client.listen():
                nonlocal message_count
                message_received_count += 1

                # Debug: log every message
                if message_received_count % 10 == 0:
                    logger.info(f"Received {message_received_count} raw messages so far...")

                message_count += 1

                logger.debug(f"Received message #{message_count}: {message.keys() if isinstance(message, dict) else type(message)}")

                # Parse message
                raw_body = message.get('raw_body', '')
                logger.debug(f"Raw body length: {len(raw_body)}, first 100 chars: {raw_body[:100]}")

                parsed = parser.parse_message(raw_body)
                if not parsed:
                    logger.debug(f"Failed to parse message #{message_count}")
                    continue

                # Enrich with reference data
                enriched = enricher.enrich(parsed)

                # Track statistics
                if 'sport_name' in enriched:
                    sports_seen.add(enriched['sport_name'])
                if 'league_name' in enriched:
                    leagues_seen.add(enriched['league_name'])

                # Format and print
                formatted = formatter.format_odds_update(enriched)
                print(formatted)
                print()  # Blank line between messages

                # Progress indicator every 50 messages
                if message_count % 50 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = message_count / elapsed
                    logger.info(f"📊 {message_count} messages | {rate:.1f} msg/sec | {len(sports_seen)} sports | {len(leagues_seen)} leagues")

        # Run with timeout
        try:
            await asyncio.wait_for(listen_with_timeout(), timeout=duration)
        except asyncio.TimeoutError:
            logger.info("")
            logger.info("⏱️  Duration reached, stopping...")
        await client.disconnect()

        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        summary = formatter.format_summary(
            message_count=message_count,
            duration_seconds=int(elapsed),
            sports_seen=sports_seen,
            leagues_seen=leagues_seen
        )
        print(summary)

        logger.info("")
        logger.info("✅ Demo complete!")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


def main():
    """Main entry point"""
    # Load environment
    load_dotenv()

    # Parse arguments
    parser = argparse.ArgumentParser(description='Enriched odds feed demo')
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=60,
        help='Duration in seconds (default: 60)'
    )
    parser.add_argument(
        '--compact',
        action='store_true',
        help='Use compact single-line format'
    )

    args = parser.parse_args()

    # Get cookie from environment
    cookie = os.getenv("MANUAL_COOKIE")

    if not cookie:
        logger.error("❌ MANUAL_COOKIE not found in .env file!")
        logger.error("Please set MANUAL_COOKIE in your .env file")
        sys.exit(1)

    logger.info("Using manual cookie mode...")
    logger.info("")

    # Run demo
    asyncio.run(run_enriched_demo(
        cookie=cookie,
        duration=args.duration
    ))


if __name__ == "__main__":
    main()
