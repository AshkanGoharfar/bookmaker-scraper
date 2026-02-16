"""
Test GetGameInfo API to fetch team names for live games
"""

import asyncio
import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import aiohttp

load_dotenv()

async def test_get_game_info(game_id: str):
    """Test GetGameInfo API with a specific game ID"""
    cookie = os.getenv("MANUAL_COOKIE")
    url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx/GetGameInfo"

    payload = {
        "Req": {
            "InParams": {
                "GameId": game_id
            }
        }
    }

    print("=" * 80)
    print(f"Testing GetGameInfo API for Game ID: {game_id}")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Cookie": f"ASP.NET_SessionId={cookie}",
                "Content-Type": "application/json"
            }

            async with session.post(url, json=payload, headers=headers) as response:
                print(f"Status: {response.status}")
                print()

                if response.status == 200:
                    text = await response.text()
                    print(f"Response length: {len(text)} characters")
                    print()

                    try:
                        data = json.loads(text)
                        print("✅ JSON parsed successfully")
                        print()

                        # Pretty print the response
                        print("Full Response:")
                        print(json.dumps(data, indent=2))
                        print()

                        # Try to extract team names
                        print("=" * 80)
                        print("EXTRACTED TEAM NAMES:")
                        print("=" * 80)

                        # Try different possible structures
                        if 'd' in data:
                            d = data['d']
                            if isinstance(d, str):
                                d = json.loads(d)

                            # Look for team names in various possible locations
                            home_team = d.get('htm') or d.get('HomeTeam') or d.get('hometeam')
                            away_team = d.get('vtm') or d.get('AwayTeam') or d.get('awayteam') or d.get('VisitingTeam')

                            if home_team or away_team:
                                print(f"Home Team: {home_team}")
                                print(f"Away Team: {away_team}")
                                print(f"Game: {away_team} @ {home_team}")
                            else:
                                print("Could not find team names in standard fields")
                                print(f"Available fields: {d.keys() if isinstance(d, dict) else 'N/A'}")

                    except Exception as e:
                        print(f"❌ Error parsing response: {e}")
                        print(f"Raw text (first 500 chars): {text[:500]}")
                else:
                    error_text = await response.text()
                    print(f"❌ Request failed: {response.status}")
                    print(f"Error response: {error_text[:500]}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Test with multiple game IDs from WebSocket"""

    # These are live game IDs we saw in WebSocket messages
    test_game_ids = [
        "47464398",  # Live game from earlier test
        "47464898",  # Another live game
        "47401064",  # Dashboard game (for comparison)
    ]

    for game_id in test_game_ids:
        await test_get_game_info(game_id)
        print("\n" * 2)

if __name__ == "__main__":
    asyncio.run(main())
