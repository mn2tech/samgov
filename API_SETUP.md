# SAM.gov Get Opportunities Public API Setup

## Which API to Use

Our application uses the **"SAM.gov Get Opportunities Public API"** (the public one shown in the top section of the API documentation page).

**NOT** the "Opportunity Management API" (bottom section) - that's for authorized users to submit/manage opportunities.

## Getting Your API Key

1. **Visit the API Documentation:**
   - Go to: https://open.gsa.gov/api/opportunities-api/
   - Or navigate from: https://open.gsa.gov/ → APIs → Opportunities

2. **Click "View API Documentation"** on the "Get Opportunities Public API" section

3. **Register for an API Key:**
   - **For Production:** Request a public API key in the Account Details page on SAM.gov
   - **For Alpha/Testing:** Request a public API key on alpha.sam.gov
   - Note: Request limits per day are based on your role (federal, non-federal, or general)
   - The key will be used to authenticate your requests

## Current Configuration

Our app is configured to use:
- **Production Endpoint:** `https://api.sam.gov/opportunities/v2/search`
- **Alpha Endpoint (for testing):** `https://api-alpha.sam.gov/opportunities/v2/search`
- **Base URL:** `https://api.sam.gov/opportunities/v2` (we append `/search` automatically)

## Adding Your API Key

Once you have your API key:

1. **Create or edit `.env` file** in the project root:
   ```bash
   SAM_API_KEY=your_actual_api_key_here
   SAM_API_BASE_URL=https://api.sam.gov/opportunities/v2
   ```
   
   **For Alpha/Testing environment:**
   ```bash
   SAM_API_BASE_URL=https://api-alpha.sam.gov/opportunities/v2
   ```

2. **Restart the application:**
   ```bash
   streamlit run app.py
   ```

## API Parameters We Use

The app automatically filters for IT-focused opportunities using:

- **NAICS Codes:** 541511, 541512, 541513, 541519, 518210, 541330, 541690
- **Keywords:** AI, machine learning, data analytics, cloud, cybersecurity, DevOps, etc.
- **Date Range:** Configurable (default: 30 days ahead)
- **Active Only:** Yes

## Testing Without API Key

The app works perfectly without an API key for testing:
- Uses mock data (3 sample opportunities)
- Uses rule-based classification and scoring
- Full UI functionality available

## API Rate Limits

Be aware that SAM.gov APIs have rate limits. The app handles this gracefully:
- If rate limited, it will fall back to mock data
- Errors are logged but don't crash the app

## Troubleshooting

**Issue:** "No opportunities returned"
- **Solution:** Check API key is correct, verify endpoint URL, or use mock data mode

**Issue:** "401 Unauthorized"
- **Solution:** Verify your API key is valid and active

**Issue:** "403 Forbidden"
- **Solution:** Check if your API key has the correct permissions for the Opportunities API

---

**Note:** The exact endpoint structure may vary. If you encounter issues, check the official API documentation for the current endpoint format.
