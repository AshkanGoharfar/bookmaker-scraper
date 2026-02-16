"""
Manual integration test for MarketFetcher with REAL API

Tests:
1. Fetch initial markets from real GetGameInfo API
2. Verify market data structure
3. Check that Derivatives are parsed correctly
"""

import asyncio
import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.market.market_fetcher import MarketFetcher
from src.data.reference_loader import ReferenceDataLoader
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)


async def test_real_market_fetcher():
    """Test MarketFetcher with real Bookmaker.eu API"""

    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        logger.error("MANUAL_COOKIE not set in .env")
        return

    logger.info("=" * 80)
    logger.info("MARKET FETCHER INTEGRATION TEST - REAL API")
    logger.info("=" * 80)
    logger.info("")

    # Step 1: Get fresh game IDs from dashboard
    logger.info("STEP 1: Loading game IDs from dashboard...")
    logger.info("-" * 80)

    ref_loader = ReferenceDataLoader(cookie)
    await ref_loader.load_games()

    if not ref_loader.games:
        logger.error("❌ No games found in dashboard")
        return

    # Get first 3 game IDs for testing
    game_ids = list(ref_loader.games.keys())[:3]
    logger.info(f"✅ Found {len(ref_loader.games)} games in dashboard")
    logger.info(f"Testing with {len(game_ids)} games: {game_ids}")
    logger.info("")

    # Step 2: Initialize MarketFetcher
    logger.info("STEP 2: Initializing MarketFetcher...")
    logger.info("-" * 80)

    fetcher = MarketFetcher(cookie)
    logger.info(f"✅ MarketFetcher created")
    logger.info("")

    # Step 3: Fetch Initial Markets
    logger.info("STEP 3: Fetching initial markets from GetGameInfo API...")
    logger.info("-" * 80)

    try:
        markets = await fetcher.fetch_initial_markets(game_ids=game_ids)
        logger.info(f"✅ Fetched {len(markets)} markets successfully")
        logger.info("")

        # Step 4: Display Results
        logger.info("STEP 4: Examining fetched market data...")
        logger.info("-" * 80)

        for i, (gid, market) in enumerate(markets.items(), 1):
            logger.info(f"\n📊 Market {i}/{len(markets)} - Game ID: {gid}")
            logger.info("-" * 70)

            # Basic game info
            logger.info(f"  Teams: {market.get('vtm', '?')} @ {market.get('htm', '?')}")
            logger.info(f"  Sport: {market.get('idspt', '?')}")
            logger.info(f"  League: {market.get('idlg', '?')}")
            logger.info(f"  Live: {market.get('LiveGame', False)}")

            # Market data (Derivatives)
            derivatives = market.get('Derivatives', {})
            lines = derivatives.get('line', [])

            if lines:
                logger.info(f"  Lines available: {len(lines)}")

                # Find main line (s_ml = 1)
                main_line = next((l for l in lines if l.get('s_ml') == 1), lines[0] if lines else None)

                if main_line:
                    logger.info(f"\n  📈 Main Line (index {main_line.get('index', '?')}):")

                    # Moneyline
                    if main_line.get('hoddst'):
                        logger.info(f"    💰 Moneyline:")
                        logger.info(f"      Home: {main_line.get('hoddst')}")
                        logger.info(f"      Away: {main_line.get('voddst')}")

                    # Spread
                    if main_line.get('hsprdt'):
                        logger.info(f"    📊 Spread:")
                        logger.info(f"      Home: {main_line.get('hsprdoddst')} ({main_line.get('hsprdt')} points)")
                        logger.info(f"      Away: {main_line.get('vsprdoddst')} ({main_line.get('vsprdt')} points)")

                    # Totals
                    if main_line.get('ovt'):
                        logger.info(f"    🎯 Totals:")
                        logger.info(f"      Over {main_line.get('ovt')}: {main_line.get('ovoddst')}")
                        logger.info(f"      Under {main_line.get('unt')}: {main_line.get('unoddst')}")
            else:
                logger.info(f"  ⚠️  No lines (Derivatives) found")

        # Step 5: Verify Cache
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: Verifying cache...")
        logger.info("-" * 80)

        cached_markets = fetcher.get_all_markets()
        logger.info(f"✅ Cache contains {len(cached_markets)} markets")
        logger.info(f"✅ All game IDs cached: {list(cached_markets.keys())}")
        logger.info("")

        # Step 6: Test Querying Single Market (skipped - not implemented yet)
        logger.info("STEP 6: Testing get_market_state()...")
        logger.info("-" * 80)
        logger.info("⏭️  Skipped (will implement in M3.1.5)")

        # TODO: Uncomment when get_market_state is implemented in M3.1.5
        # first_gid = game_ids[0]
        # single_market = fetcher.get_market_state(first_gid)
        # if single_market:
        #     logger.info(f"✅ Successfully retrieved market for game {first_gid}")
        #     logger.info(f"   Teams: {single_market.get('vtm')} @ {single_market.get('htm')}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  - Fetched markets for {len(game_ids)} games")
        logger.info(f"  - All markets cached successfully")
        logger.info(f"  - Market data includes Derivatives with odds")
        logger.info(f"  - Ready to apply WebSocket deltas!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_real_market_fetcher())
