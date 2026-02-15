"""
Quick WebSocket test without authentication.
Tests if WebSocket connection works with provided cookie.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.websocket.stomp_client import StompClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def quick_test(cookie: str):
    """Quick test with provided cookie."""

    print("=" * 80)
    print("QUICK WEBSOCKET TEST")
    print("=" * 80)
    print()

    client = StompClient()

    try:
        print("Connecting to WebSocket...")
        await client.connect(
            url="wss://be.bookmaker.eu/gateway/handlers/RealTimeHandler.ashx?f=ws",
            cookie=cookie,
            host="WebRT",
            login="rtweb",
            passcode="rtweb"
        )

        print("✅ CONNECTED!")
        print(f"Session: {client.session_id}")
        print()

        print("Subscribing to exchange...")
        await client.subscribe(
            exchange="BetSlipRTv4Topics",
            topics=["GAME", "TNT", "l"]
        )
        print("✅ SUBSCRIBED!")
        print()

        print("Listening for messages (10 seconds)...")
        count = 0
        try:
            async for message in client.listen():
                count += 1
                print(f"✅ MESSAGE {count}: {str(message)[:100]}...")
                if count >= 3:  # Get 3 messages then stop
                    break
        except asyncio.TimeoutError:
            pass

        print()
        print(f"✅ SUCCESS! Received {count} messages")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    # Your cookie here
    cookie = input("Paste your cookie string: ").strip()

    if not cookie:
        print("No cookie provided!")
        sys.exit(1)

    asyncio.run(quick_test(cookie))
