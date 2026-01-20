"""Test the noticedesc endpoint authentication."""
import asyncio
import httpx
from config import settings

async def test_description_endpoint():
    """Test fetching description from noticedesc endpoint."""
    api_key = settings.sam_api_key
    notice_id = "ffad0dbe4d57463583bbc683b664d724"
    
    # The description URL format
    desc_url = f"https://api.sam.gov/prod/opportunities/v1/noticedesc?noticeid={notice_id}"
    
    print(f"Testing description endpoint: {desc_url}")
    print(f"API Key: {api_key[:30]}...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Method 1: Query parameter
        print("Method 1: Query parameter (api_key)")
        try:
            params = {"api_key": api_key}
            response = await client.get(desc_url, params=params)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success!")
                print(f"  Response length: {len(response.text)} chars")
                print(f"  Preview: {response.text[:200]}...")
            else:
                print(f"  [FAILED] {response.text[:300]}")
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        print()
        
        # Method 2: Header
        print("Method 2: Header (X-Api-Key)")
        try:
            headers = {"X-Api-Key": api_key}
            response = await client.get(desc_url, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  [OK] Success!")
                print(f"  Response length: {len(response.text)} chars")
                print(f"  Preview: {response.text[:200]}...")
            else:
                print(f"  [FAILED] {response.text[:300]}")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_description_endpoint())
