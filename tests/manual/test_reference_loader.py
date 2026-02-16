"""
Test reference data loader with correct parsing
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.data.reference_loader import ReferenceDataLoader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_reference_loader():
    """Test reference data loading"""
    load_dotenv()

    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        logger.error("MANUAL_COOKIE not found")
        return

    logger.info("Testing ReferenceDataLoader with corrected parsing...")
    logger.info("=" * 80)

    loader = ReferenceDataLoader(cookie)
    await loader.load_all()

    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"Sports loaded: {len(loader.sports)}")
    logger.info(f"Leagues loaded: {len(loader.leagues)}")
    logger.info(f"Games loaded: {len(loader.games)}")
    logger.info("")

    if loader.sports:
        logger.info("Sample sports:")
        for i, (sid, sport) in enumerate(list(loader.sports.items())[:5]):
            logger.info(f"  {sid}: {sport['name']}")
        logger.info("")

    if loader.leagues:
        logger.info("Sample leagues:")
        for i, (lid, league) in enumerate(list(loader.leagues.items())[:5]):
            logger.info(f"  {lid}: {league['name']} (sport: {league['sport']})")
        logger.info("")

    if loader.games:
        logger.info("Sample games:")
        for i, (gid, game) in enumerate(list(loader.games.items())[:5]):
            logger.info(f"  {gid}: {game['vtm']} @ {game['htm']}")
        logger.info("")

if __name__ == "__main__":
    asyncio.run(test_reference_loader())
