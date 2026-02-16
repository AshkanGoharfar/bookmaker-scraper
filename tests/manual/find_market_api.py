"""Try different potential market API endpoints"""
import asyncio
import os
import sys
from pathlib import Path
import aiohttp
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_endpoint(session, cookie, endpoint_name, payload):
    """Test a potential API endpoint"""
    url = f"https://be.bookmaker.eu/gateway/BetslipProxy.aspx/{endpoint_name}"
    headers = {
        "Cookie": f"ASP.NET_SessionId={cookie}",
        "Content-Type": "application/json"
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=5) as response:
            data = await response.json()
            return {
                "endpoint": endpoint_name,
                "status": response.status,
                "has_data": bool(data and data not in [{}]),
                "valid": data.get("valid") if isinstance(data, dict) else None,
                "keys": list(data.keys()) if isinstance(data, dict) else None
            }
    except Exception as e:
        return {
            "endpoint": endpoint_name,
            "status": "error",
            "error": str(e)[:100]
        }

async def main():
    cookie = os.getenv("MANUAL_COOKIE")
    
    # Try different endpoint names
    endpoints_to_try = [
        ("GetMarkets", {"Req": {"InParams": {}}}),
        ("GetLines", {"Req": {"InParams": {}}}),
        ("GetOdds", {"Req": {"InParams": {}}}),
        ("GetBetslipData", {"Req": {"InParams": {}}}),
        ("GetLiveGames", {"Req": {"InParams": {}}}),
        ("GetGameLines", {"Req": {"InParams": {}}}),
        ("GetGameMarkets", {"Req": {"InParams": {}}}),
    ]
    
    print("🔍 Testing potential market API endpoints...")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        for endpoint_name, payload in endpoints_to_try:
            result = await test_endpoint(session, cookie, endpoint_name, payload)
            
            status_icon = "✅" if result.get("valid") == "1" else "❓" if result.get("status") == 200 else "❌"
            print(f"\n{status_icon} {endpoint_name}")
            print(f"   Status: {result.get('status')}")
            print(f"   Valid: {result.get('valid')}")
            print(f"   Keys: {result.get('keys')}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 70)
    print("✅ Done! Look for endpoints with valid='1' or interesting keys")

asyncio.run(main())
