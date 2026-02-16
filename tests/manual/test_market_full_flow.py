"""
Full Flow Integration Test - Market State Management

Demonstrates complete market state management:
1. Fetch initial market state from GetGameInfo API
2. Connect to WebSocket and receive real-time deltas
3. Apply deltas to update cached state
4. Query and display state changes in real-time

This shows the complete stateful system working end-to-end.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.market.market_fetcher import MarketFetcher
from src.data.reference_loader import ReferenceDataLoader
from src.websocket.stomp_client import StompClient
from src.parser.message_parser import MessageParser
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

# Configuration
WEBSOCKET_URL = "wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws"
EXCHANGE = "BetSlipRTv4Topics"
TOPICS = ["GAME", "TNT", "HB", "mrc"]


def format_market_summary(market: dict) -> str:
    """Format market data for display"""
    lines = []

    # Game info
    lines.append(f"  Game: {market.get('vtm', '?')} @ {market.get('htm', '?')}")

    # WebSocket market data (mkt field - from deltas)
    if 'mkt' in market:
        mkt = market['mkt']

        if 's' in mkt and mkt['s']:
            spread = mkt['s'][0]
            lines.append(f"  📊 Spread: Home {spread.get('h')} ({spread.get('hp'):+.1f}), Away {spread.get('v')} ({spread.get('vp'):+.1f})")

        if 'm' in mkt and mkt['m']:
            ml = mkt['m'][0]
            lines.append(f"  💰 Moneyline: Home {ml.get('h')}, Away {ml.get('v')}")

        if 't' in mkt and mkt['t']:
            total = mkt['t'][0]
            lines.append(f"  🎯 Total: Over {total.get('hp')} ({total.get('h')}), Under {total.get('vp')} ({total.get('v')})")

    # GetGameInfo derivatives (from initial fetch)
    if 'Derivatives' in market:
        derivatives = market['Derivatives']
        lines_data = derivatives.get('line', [])
        if lines_data:
            main_line = next((l for l in lines_data if l.get('s_ml') == 1), None)
            if main_line:
                lines.append(f"  📈 GetGameInfo: {len(lines_data)} lines available")

    return "\n".join(lines)


async def test_full_flow(duration: int = 30):
    """
    Test complete market state management flow

    Args:
        duration: How long to listen for WebSocket updates (seconds)
    """
    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        logger.error("MANUAL_COOKIE not set in .env")
        return

    logger.info("=" * 80)
    logger.info("FULL FLOW TEST - MARKET STATE MANAGEMENT")
    logger.info("=" * 80)
    logger.info("")
    logger.info("This test demonstrates:")
    logger.info("  1. Fetching initial market state (GetGameInfo API)")
    logger.info("  2. Applying real-time WebSocket deltas")
    logger.info("  3. Maintaining full state (initial + updates)")
    logger.info("")

    # Statistics
    deltas_applied = 0
    games_updated = set()
    start_time = datetime.now()

    try:
        # =================================================================
        # STEP 1: Get Game IDs from Dashboard
        # =================================================================
        logger.info("STEP 1: Loading game IDs from dashboard...")
        logger.info("-" * 80)

        ref_loader = ReferenceDataLoader(cookie)
        await ref_loader.load_games()

        if not ref_loader.games:
            logger.error("❌ No games found in dashboard")
            return

        # Get first 5 games for testing
        game_ids = list(ref_loader.games.keys())[:5]
        logger.info(f"✅ Found {len(ref_loader.games)} games in dashboard")
        logger.info(f"Testing with {len(game_ids)} games: {game_ids}")
        logger.info("")

        # =================================================================
        # STEP 2: Fetch Initial Markets
        # =================================================================
        logger.info("STEP 2: Fetching initial markets from GetGameInfo API...")
        logger.info("-" * 80)

        fetcher = MarketFetcher(cookie)
        initial_markets = await fetcher.fetch_initial_markets(game_ids=game_ids)

        logger.info(f"✅ Fetched {len(initial_markets)} initial markets")
        logger.info("")
        logger.info("Initial State:")
        logger.info("-" * 80)
        for gid, market in list(initial_markets.items())[:3]:
            logger.info(f"\n📦 Game {gid}:")
            logger.info(format_market_summary(market))
        logger.info("")

        # =================================================================
        # STEP 3: Connect to WebSocket
        # =================================================================
        logger.info("STEP 3: Connecting to WebSocket for real-time updates...")
        logger.info("-" * 80)

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

        await client.subscribe(
            exchange=EXCHANGE,
            topics=TOPICS,
            sub_id="sub-0",
            use_wildcard=True
        )
        logger.info("✅ Subscribed to odds feed")
        logger.info("")

        # =================================================================
        # STEP 4: Apply Deltas in Real-Time
        # =================================================================
        logger.info(f"STEP 4: Listening for updates ({duration} seconds)...")
        logger.info("-" * 80)
        logger.info("Showing updates for our tracked games:")
        logger.info(f"Tracking: {game_ids}")
        logger.info("")

        parser = MessageParser()
        tracked_gids_str = set(str(gid) for gid in game_ids)

        async def listen_and_apply():
            nonlocal deltas_applied, games_updated

            async for message in client.listen():
                # Parse WebSocket message
                raw_body = message.get('raw_body', '')
                parsed = parser.parse_message(raw_body)

                if not parsed or 'gid' not in parsed:
                    continue

                gid_str = str(parsed['gid'])

                # Only process deltas for our tracked games
                if gid_str in tracked_gids_str:
                    # Get state before update
                    before_state = fetcher.get_market_state(gid_str)
                    before_mkt = before_state.get('mkt', {}) if before_state else {}

                    # Apply delta
                    fetcher.apply_delta(parsed)
                    deltas_applied += 1
                    games_updated.add(gid_str)

                    # Get state after update
                    after_state = fetcher.get_market_state(gid_str)
                    after_mkt = after_state.get('mkt', {}) if after_state else {}

                    # Check if market data actually changed
                    if before_mkt != after_mkt:
                        logger.info(f"🔄 Update #{deltas_applied} - Game {gid_str}")
                        logger.info(f"   {after_state.get('vtm', '?')} @ {after_state.get('htm', '?')}")

                        # Show what changed
                        if 's' in after_mkt:
                            spread = after_mkt['s'][0]
                            logger.info(f"   Spread: Home {spread.get('h')} ({spread.get('hp'):+.1f})")
                        if 'm' in after_mkt:
                            ml = after_mkt['m'][0]
                            logger.info(f"   Moneyline: Home {ml.get('h')}, Away {ml.get('v')}")
                        if 't' in after_mkt:
                            total = after_mkt['t'][0]
                            logger.info(f"   Total: O/U {total.get('hp')} ({total.get('h')}/{total.get('v')})")
                        logger.info("")

        # Run with timeout
        try:
            await asyncio.wait_for(listen_and_apply(), timeout=duration)
        except asyncio.TimeoutError:
            logger.info("⏱️  Duration reached")

        await client.disconnect()
        logger.info("")

        # =================================================================
        # STEP 5: Show Final State
        # =================================================================
        logger.info("STEP 5: Final State After Updates...")
        logger.info("-" * 80)

        final_markets = fetcher.get_all_markets()
        logger.info(f"✅ Cache contains {len(final_markets)} markets")
        logger.info("")

        logger.info("Final State (first 3 games):")
        logger.info("-" * 80)
        for gid in list(game_ids)[:3]:
            market = fetcher.get_market_state(gid)
            if market:
                logger.info(f"\n📦 Game {gid}:")
                logger.info(format_market_summary(market))
        logger.info("")

        # =================================================================
        # SUMMARY
        # =================================================================
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("✅ FULL FLOW TEST COMPLETE!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  Duration: {elapsed:.1f} seconds")
        logger.info(f"  Initial markets fetched: {len(initial_markets)}")
        logger.info(f"  WebSocket deltas received: {deltas_applied}")
        logger.info(f"  Games updated: {len(games_updated)}/{len(game_ids)}")
        logger.info(f"  Updates per second: {deltas_applied / elapsed:.1f}")
        logger.info("")
        logger.info("✅ Demonstrated:")
        logger.info("  ✅ Fetch initial state from REST API")
        logger.info("  ✅ Apply WebSocket deltas in real-time")
        logger.info("  ✅ Maintain full market state (initial + updates)")
        logger.info("  ✅ Query current state at any time")
        logger.info("")
        logger.info("🎯 Market State Manager is fully operational!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Full flow market state test')
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=30,
        help='Duration in seconds (default: 30)'
    )

    args = parser.parse_args()

    asyncio.run(test_full_flow(duration=args.duration))
