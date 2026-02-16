"""Quick test to find a current game ID and test GetGameInfo"""
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.data.reference_loader import ReferenceDataLoader

load_dotenv()

async def test():
    cookie = os.getenv("MANUAL_COOKIE")
    
    # Load games from dashboard
    print("Loading games from dashboard...")
    loader = ReferenceDataLoader(cookie)
    await loader.load_games()
    
    if loader.games:
        # Get first game ID
        first_gid = list(loader.games.keys())[0]
        game = loader.games[first_gid]
        print(f"\n✅ Found game: {game['vtm']} @ {game['htm']}")
        print(f"Game ID: {first_gid}")
        print(f"UUID: {game.get('uuid')}")
        
        # Now test GetGameInfo with this ID
        import aiohttp
        import json
        
        url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx/GetGameInfo"
        payload = {"Req": {"InParams": {"GameId": first_gid}}}
        
        print(f"\n🧪 Testing GetGameInfo with fresh game ID...")
        async with aiohttp.ClientSession() as session:
            headers = {
                "Cookie": f"ASP.NET_SessionId={cookie}",
                "Content-Type": "application/json"
            }
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                print(f"\nResponse:")
                print(json.dumps(data, indent=2))
                
                # Check if it has market data
                if 'mkt' in str(data) or 'market' in str(data).lower():
                    print("\n✅ Found market/odds data!")
                else:
                    print("\n❌ No market/odds data in response")
    else:
        print("❌ No games found in dashboard")

asyncio.run(test())
