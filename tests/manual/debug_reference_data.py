"""
Debug script to test reference data loading and see actual API responses
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

async def test_routing_info(cookie: str):
    """Test GetRoutingInfo API"""
    url = "https://be.bookmaker.eu/gateway/BetslipProxy.aspx/GetRoutingInfo"
    payload = {
        "o": {
            "BORequestData": {
                "BOParameters": {
                    "BORt": {},
                    "LanguageId": "0"
                }
            }
        }
    }

    print("=" * 80)
    print("Testing GetRoutingInfo API")
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
                print(f"Headers: {dict(response.headers)}")
                print()

                text = await response.text()
                print(f"Response length: {len(text)} characters")
                print(f"First 500 characters:")
                print(text[:500])
                print()

                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"JSON parsed successfully")
                        print(f"Type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"Keys: {data.keys()}")
                            print(f"Full response (pretty printed):")
                            print(json.dumps(data, indent=2)[:2000])
                    except Exception as e:
                        print(f"Failed to parse as JSON: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

async def test_dashboard_schedule(cookie: str):
    """Test GetDashboardSchedule API"""
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

    print()
    print("=" * 80)
    print("Testing GetDashboardSchedule API")
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
                print(f"Headers: {dict(response.headers)}")
                print()

                text = await response.text()
                print(f"Response length: {len(text)} characters")
                print(f"First 500 characters:")
                print(text[:500])
                print()

                if response.status == 200:
                    try:
                        data = json.loads(text)
                        print(f"JSON parsed successfully")
                        print(f"Type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"Keys: {data.keys()}")
                            print(f"Full response (pretty printed):")
                            print(json.dumps(data, indent=2)[:2000])
                    except Exception as e:
                        print(f"Failed to parse as JSON: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

async def main():
    cookie = os.getenv("MANUAL_COOKIE")
    if not cookie:
        print("ERROR: MANUAL_COOKIE not found in .env file")
        sys.exit(1)

    print(f"Cookie (first 20 chars): {cookie[:20]}...")
    print()

    await test_routing_info(cookie)
    await test_dashboard_schedule(cookie)

if __name__ == "__main__":
    asyncio.run(main())
