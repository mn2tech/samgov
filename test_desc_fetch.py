"""Test description fetching."""
import asyncio
from sam_ingestion import SAMIngestion

async def test():
    ing = SAMIngestion()
    desc_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc?noticeid=ffad0dbe4d57463583bbc683b664d724"
    desc = await ing._fetch_description(desc_url)
    print("Description fetched:", "Yes" if desc else "No")
    if desc:
        print(f"Length: {len(desc)} chars")
        print(f"Preview: {desc[:200]}...")
    await ing.close()

asyncio.run(test())
