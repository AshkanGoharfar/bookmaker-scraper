"""
Inspect the actual structure of game data from GetDashboardSchedule
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

async def inspect_games():
    """Get and inspect game structure"""
    cookie = os.getenv("MANUAL_COOKIE")
    url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx/GetDashboardSchedule"
    payload = {
        "o": {
            "BORequestData": {
                "BOParameters": {
                    "BORt": {},
                    "LanguageId": "0",
                    "LineStyle": "E",
                    "ScheduleType": "american",
                    "LinkDeriv": "true",
                    "DashboardNextHours": "0"
                }
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        headers = {
            "Cookie": f"ASP.NET_SessionId={cookie}",
            "Content-Type": "application/json"
        }

        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()

            # Navigate to first game
            categories = data.get("Schedule", {}).get("Data", {}).get("Categories", [])

            if categories:
                print("=" * 80)
                print("FIRST CATEGORY")
                print("=" * 80)
                first_category = categories[0]
                print(f"Category: {first_category.get('CategoryName')}")
                print(f"Sport ID: {first_category.get('IdSport')}")
                print()

                leagues = first_category.get("Leagues", {}).get("League", [])
                if leagues:
                    print("=" * 80)
                    print("FIRST LEAGUE")
                    print("=" * 80)
                    first_league = leagues[0]
                    print(f"League: {first_league.get('Description')}")
                    print(f"League ID: {first_league.get('IdLeague')}")
                    print()

                    date_groups = first_league.get("dateGroup", [])
                    if date_groups:
                        print("=" * 80)
                        print("FIRST DATE GROUP")
                        print("=" * 80)
                        first_date_group = date_groups[0]
                        print(f"Date: {first_date_group.get('date')}")
                        print()

                        games = first_date_group.get("game", [])
                        if games:
                            print("=" * 80)
                            print("FIRST GAME - COMPLETE STRUCTURE")
                            print("=" * 80)
                            first_game = games[0]
                            print(json.dumps(first_game, indent=2))
                            print()
                            print("=" * 80)
                            print("GAME KEYS")
                            print("=" * 80)
                            for key in sorted(first_game.keys()):
                                value = first_game[key]
                                # Print short summary of value
                                if isinstance(value, str):
                                    print(f"  {key}: \"{value[:50]}...\"" if len(str(value)) > 50 else f"  {key}: \"{value}\"")
                                elif isinstance(value, (int, float, bool)):
                                    print(f"  {key}: {value}")
                                elif isinstance(value, dict):
                                    print(f"  {key}: {{...}} (dict with keys: {list(value.keys())})")
                                elif isinstance(value, list):
                                    print(f"  {key}: [...] (list with {len(value)} items)")
                                else:
                                    print(f"  {key}: {type(value)}")

if __name__ == "__main__":
    asyncio.run(inspect_games())
