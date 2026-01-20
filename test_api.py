"""Test SAM.gov API connection."""
import asyncio
import logging
from sam_ingestion import SAMIngestion

logging.basicConfig(level=logging.INFO)

async def test_api():
    """Test the SAM.gov API connection."""
    ingestion = SAMIngestion()
    
    try:
        print("Testing SAM.gov API connection...")
        print(f"API Key: {ingestion.api_key[:20]}..." if ingestion.api_key else "No API key")
        print(f"Base URL: {ingestion.base_url}")
        print()
        
        opportunities = await ingestion.fetch_opportunities(limit=5, days_ahead=30)
        print(f"\n[OK] Successfully fetched {len(opportunities)} opportunities!")
        
        if opportunities:
            print("\nFirst opportunity (raw data):")
            import json
            opp_data = opportunities[0] if isinstance(opportunities[0], dict) else opportunities[0].__dict__ if hasattr(opportunities[0], '__dict__') else str(opportunities[0])
            print(json.dumps(opp_data, indent=2, default=str))
            
            # Check for agency fields
            print("\n" + "="*50)
            print("Agency-related fields:")
            for key in ['fullParentPathName', 'department', 'agency', 'organizationType', 'officeAddress']:
                if key in opp_data:
                    print(f"  {key}: {opp_data[key]}")
        
    except Exception as e:
        print(f"\n[ERROR] API test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await ingestion.close()

if __name__ == "__main__":
    asyncio.run(test_api())
