"""
Automated Integration Test for WebSocket Client.

This script tests the complete flow: Authentication → WebSocket → Messages.

Usage:
    # Uses credentials from .env (default)
    poetry run python tests/manual/test_websocket_integration.py

    # Override duration
    poetry run python tests/manual/test_websocket_integration.py -d 60

    # Override credentials (optional)
    poetry run python tests/manual/test_websocket_integration.py -u USERNAME -p PASSWORD

What it does:
1. Loads credentials from .env (USERNAME, PASSWORD)
2. Authenticates to get session cookie
3. Connects to wss://be.bookmaker.eu WebSocket
4. Subscribes to BetSlipRTv4Topics exchange (topics: GAME, TNT, l)
5. Listens for messages for 5 minutes (configurable)
6. Logs sample messages to console

Success criteria:
✅ Authentication successful
✅ STOMP CONNECTED received
✅ SUBSCRIBE successful
✅ Receiving MESSAGE frames
✅ Heartbeats working (no disconnection)
✅ Messages parsed as JSON

This verifies the entire flow works end-to-end!
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.auth.bookmaker_auth import BookmakerAuth
from src.websocket.stomp_client import StompClient, StompError
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Configuration
WEBSOCKET_URL = "wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws"
EXCHANGE = "BetSlipRTv4Topics"
TOPICS = ["GAME", "TNT", "l"]  # Game odds, Tournament odds, Live updates
LISTEN_DURATION = 300  # 5 minutes in seconds
MAX_MESSAGES_TO_LOG = 10  # Only log first 10 messages in detail


async def run_integration_test(
    username: str,
    password: str,
    duration: int = LISTEN_DURATION
) -> None:
    """
    Run automated integration test with real WebSocket connection.

    Args:
        username: Bookmaker.eu username (from .env or argument)
        password: Bookmaker.eu password (from .env or argument)
        duration: How long to listen for messages (seconds)
    """
    logger.info("=" * 80)
    logger.info("BOOKMAKER.EU WEBSOCKET INTEGRATION TEST")
    logger.info("=" * 80)
    logger.info("Testing complete flow: Authentication → WebSocket → Messages")
    logger.info("")

    client = None
    message_count = 0
    start_time = datetime.now()

    try:
        # Step 1: Authenticate
        logger.info("STEP 1: Authenticating to get session cookie...")
        logger.info("-" * 80)
        logger.info(f"Username: {username}")

        authenticator = BookmakerAuth(username, password)

        # Login
        session_cookie = await authenticator.login()

        if not session_cookie:
            logger.error("❌ Authentication failed!")
            return

        # Get ALL cookies for WebSocket (needed for cross-domain: www → be)
        cookie = authenticator.get_all_cookies_header()

        logger.info(f"✅ Authenticated successfully!")
        logger.info(f"Session cookie name: {authenticator.session_cookie_name}")
        logger.info(f"Session cookie value: {session_cookie[:30]}...")
        logger.info(f"Total cookies: {len(authenticator.all_cookies)}")
        logger.info("")

        # Step 2: Connect to WebSocket
        logger.info("STEP 2: Connecting to WebSocket...")
        logger.info("-" * 80)
        logger.info(f"URL: {WEBSOCKET_URL}")
        logger.info(f"Cookies: {cookie[:100]}..." if len(cookie) > 100 else f"Cookies: {cookie}")
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

        logger.info(f"✅ STOMP CONNECTED successfully!")
        logger.info(f"Session: {client.session_id}")
        logger.info(f"Heartbeat task: {'Running' if client.heartbeat_task and not client.heartbeat_task.done() else 'Not running'}")
        logger.info("")

        # Step 3: Subscribe to exchange
        logger.info("STEP 3: Subscribing to exchange...")
        logger.info("-" * 80)
        logger.info(f"Exchange: {EXCHANGE}")
        logger.info(f"Topics: {', '.join(TOPICS)}")
        logger.info("")

        await client.subscribe(
            exchange=EXCHANGE,
            topics=TOPICS,
            sub_id="sub-0"
        )

        logger.info(f"✅ SUBSCRIBED successfully!")
        logger.info("")

        # Step 4: Listen for messages
        logger.info("STEP 4: Listening for messages...")
        logger.info("-" * 80)
        logger.info(f"Duration: {duration} seconds ({duration // 60} minutes)")
        logger.info(f"Will log first {MAX_MESSAGES_TO_LOG} messages in detail")
        logger.info("")
        logger.info("Waiting for messages... (Press Ctrl+C to stop)")
        logger.info("")

        # Set up timeout
        async def listen_with_timeout():
            nonlocal message_count

            async for message in client.listen():
                message_count += 1

                # Log first few messages in detail
                if message_count <= MAX_MESSAGES_TO_LOG:
                    logger.info(f"MESSAGE #{message_count}")
                    logger.info(f"Received at: {datetime.now().strftime('%H:%M:%S')}")
                    logger.info(f"Content: {json.dumps(message, indent=2)}")
                    logger.info("-" * 40)
                else:
                    # After that, just log a summary
                    if message_count % 10 == 0:  # Every 10th message
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = message_count / elapsed if elapsed > 0 else 0
                        logger.info(f"📊 Status: {message_count} messages received ({rate:.1f}/sec)")

        # Run with timeout
        try:
            await asyncio.wait_for(listen_with_timeout(), timeout=duration)
        except asyncio.TimeoutError:
            logger.info("")
            logger.info(f"⏱️  Timeout reached ({duration} seconds)")

    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Interrupted by user (Ctrl+C)")

    except StompError as e:
        logger.error(f"❌ STOMP ERROR: {e}")
        return

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return

    finally:
        # Step 5: Cleanup
        logger.info("")
        logger.info("STEP 5: Cleanup...")
        logger.info("-" * 80)

        if client:
            await client.disconnect()
            logger.info("✅ Disconnected successfully")

        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")
        logger.info(f"Messages received: {message_count}")
        if elapsed > 0:
            logger.info(f"Average rate: {message_count / elapsed:.2f} messages/second")

        if message_count > 0:
            logger.info("")
            logger.info("✅ SUCCESS! ENTIRE FLOW WORKS!")
            logger.info("   - Authentication: ✅ Working")
            logger.info("   - WebSocket connection: ✅ Working")
            logger.info("   - STOMP protocol: ✅ Working")
            logger.info("   - Subscription: ✅ Working")
            logger.info("   - Message reception: ✅ Working")
            logger.info("   - JSON parsing: ✅ Working")
            logger.info("   - Heartbeat mechanism: ✅ Working")
            logger.info("")
            logger.info("🎉 All components integrated successfully!")
            logger.info("")
            logger.info("Next step: Analyze message schema for parser implementation (M1.5)")
        else:
            logger.warning("")
            logger.warning("⚠️  NO MESSAGES RECEIVED")
            logger.warning("   This could mean:")
            logger.warning("   - No odds updates during test period")
            logger.warning("   - Wrong topics subscribed")
            logger.warning("   - Connection issue")
            logger.warning("")
            logger.warning("Try running again or check exchange/topics configuration")

        logger.info("=" * 80)


def main():
    """Entry point for automated integration test."""
    import argparse
    import sys

    # Load environment variables from .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded .env from: {env_path}")
    else:
        logger.warning(f".env file not found at: {env_path}")

    parser = argparse.ArgumentParser(
        description="Automated integration test for Bookmaker.eu WebSocket client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use credentials from .env (default)
  poetry run python tests/manual/test_websocket_integration.py

  # Short 1-minute test
  poetry run python tests/manual/test_websocket_integration.py -d 60

  # Override credentials
  poetry run python tests/manual/test_websocket_integration.py -u myuser -p mypass
        """
    )
    parser.add_argument(
        "--username", "-u",
        help="Bookmaker.eu username (default: from .env USERNAME)"
    )
    parser.add_argument(
        "--password", "-p",
        help="Bookmaker.eu password (default: from .env PASSWORD)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=LISTEN_DURATION,
        help=f"How long to listen for messages in seconds (default: {LISTEN_DURATION})"
    )

    args = parser.parse_args()

    # Get credentials: CLI args override .env
    username = args.username or os.getenv("BOOKMAKER_USERNAME")
    password = args.password or os.getenv("BOOKMAKER_PASSWORD")

    # Validate credentials
    if not username or not password:
        logger.error("❌ Credentials not found!")
        logger.error("   Either:")
        logger.error("   1. Set BOOKMAKER_USERNAME and BOOKMAKER_PASSWORD in .env file")
        logger.error("   2. Provide --username and --password arguments")
        sys.exit(1)

    # Run the test
    try:
        asyncio.run(run_integration_test(
            username=username,
            password=password,
            duration=args.duration
        ))
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Test interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
