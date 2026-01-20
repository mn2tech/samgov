"""Test different SAM.gov API authentication methods."""
import asyncio
import httpx
import logging
from config import settings

logging.basicConfig(level=logging.DEBUG)

async def test_auth_methods():
    """Test different authentication methods."""
    api_key = settings.sam_api_key
    base_url = settings.sam_api_base_url
    
    if not api_key:
        print("[ERROR] No API key found in config")
        return
    
    print(f"Testing API key: {api_key[:30]}...")
    print(f"Base URL: {base_url}\n")
    
    # Test parameters
    params = {
        "limit": 1,
        "postedFrom": "01/18/2026",
        "postedTo": "02/18/2026",
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Method 1: Query parameter (api_key)
        print("Method 1: Query parameter (api_key)")
        try:
            test_params = params.copy()
            test_params["api_key"] = api_key
            response = await client.get(f"{base_url}/search", params=test_params)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success with query parameter!")
                data = response.json()
                print(f"  Opportunities: {len(data.get('opportunitiesData', data.get('data', [])))}")
            else:
                print(f"  [FAILED] Error: {response.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        print()
        
        # Method 2: Header (X-Api-Key)
        print("Method 2: Header (X-Api-Key)")
        try:
            headers = {"X-Api-Key": api_key}
            response = await client.get(f"{base_url}/search", params=params, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success with header!")
                data = response.json()
                print(f"  Opportunities: {len(data.get('opportunitiesData', data.get('data', [])))}")
            else:
                print(f"  [FAILED] Error: {response.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        print()
        
        # Method 3: Header (api_key)
        print("Method 3: Header (api_key)")
        try:
            headers = {"api_key": api_key}
            response = await client.get(f"{base_url}/search", params=params, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success with header!")
                data = response.json()
                print(f"  Opportunities: {len(data.get('opportunitiesData', data.get('data', [])))}")
            else:
                print(f"  [FAILED] Error: {response.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        print()
        
        # Method 4: Authorization header
        print("Method 4: Authorization header (Bearer)")
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(f"{base_url}/search", params=params, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success with Authorization header!")
                data = response.json()
                print(f"  Opportunities: {len(data.get('opportunitiesData', data.get('data', [])))}")
            else:
                print(f"  [FAILED] Error: {response.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_methods())
