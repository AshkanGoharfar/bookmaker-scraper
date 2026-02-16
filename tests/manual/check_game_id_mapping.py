"""
Check if WebSocket game IDs match dashboard game IDs
"""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.websocket.stomp_client import StompClient
from src.data.reference_loader import ReferenceDataLoader
from src.parser.message_parser import MessageParser
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def check_mapping():
    """Check game ID mapping between WebSocket and dashboard"""
    load_dotenv()

    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        logger.error("MANUAL_COOKIE not found")
        return

    # Load reference data
    logger.info("Loading reference data...")
    loader = ReferenceDataLoader(cookie)
    await loader.load_all()

    logger.info(f"Loaded {len(loader.games)} games from dashboard")
    logger.info("Sample dashboard game IDs:")
    for i, (gid, game) in enumerate(list(loader.games.items())[:5]):
        logger.info(f"  GID: {gid}, UUID: {game.get('uuid')}, Teams: {game['vtm']} @ {game['htm']}")

    # Also create a UUID index
    uuid_index = {}
    for gid, game in loader.games.items():
        uuid = game.get('uuid')
        if uuid:
            uuid_index[uuid.upper()] = game

    logger.info(f"UUID index has {len(uuid_index)} entries")
    logger.info("")

    # Connect to WebSocket
    logger.info("Connecting to WebSocket...")
    client = StompClient()
    await client.connect(
        url="wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws",
        cookie=cookie,
        host="WebRT",
        login="rtweb",
        passcode="rtweb",
        heartbeat=20000
    )

    await client.subscribe(
        exchange="BetSlipRTv4Topics",
        topics=["GAME", "TNT", "HB", "mrc"],
        sub_id="sub-0",
        use_wildcard=True
    )

    logger.info("Listening for first 10 messages with game IDs...")
    logger.info("")

    parser = MessageParser()
    count = 0

    async for message in client.listen():
        raw_body = message.get('raw_body', '')
        parsed = parser.parse_message(raw_body)

        if not parsed:
            continue

        gid = parsed.get('gid')
        uuid = parsed.get('uuid')

        if gid or uuid:
            count += 1
            logger.info(f"Message #{count}:")
            logger.info(f"  WebSocket GID: {gid}")
            logger.info(f"  WebSocket UUID: {uuid}")

            # Check if GID matches dashboard
            if gid and str(gid) in loader.games:
                game = loader.games[str(gid)]
                logger.info(f"  ✅ MATCHED by GID: {game['vtm']} @ {game['htm']}")
            elif uuid and uuid.upper() in uuid_index:
                game = uuid_index[uuid.upper()]
                logger.info(f"  ✅ MATCHED by UUID: {game['vtm']} @ {game['htm']}")
            else:
                logger.info(f"  ❌ NO MATCH in dashboard")

            logger.info("")

            if count >= 10:
                break

    await client.disconnect()
    logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(check_mapping())
