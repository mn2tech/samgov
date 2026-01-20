# Fix Google OAuth Redirect URI Mismatch

## The Problem
Error: `redirect_uri_mismatch` means the redirect URI in your OAuth request doesn't match what's configured in Google Cloud Console.

## Solution

### Step 1: Check Your Current Redirect URI

Your `.env` file has:
```
GOOGLE_REDIRECT_URI=http://localhost:8501
```

### Step 2: Add EXACT Redirect URI to Google Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", you MUST add:
   ```
   http://localhost:8501
   ```
   **Important:**
   - NO trailing slash (`/`)
   - Use `http://` (not `https://`) for localhost
   - Must be EXACTLY: `http://localhost:8501`
4. Click "SAVE"

### Step 3: Common Mistakes to Avoid

❌ **Wrong:**
- `http://localhost:8501/` (trailing slash)
- `https://localhost:8501` (https instead of http)
- `localhost:8501` (missing http://)
- `http://127.0.0.1:8501` (different format)

✅ **Correct:**
- `http://localhost:8501` (exact match)

### Step 4: Restart Streamlit

After updating Google Console:
1. Stop your Streamlit app (Ctrl+C)
2. Restart: `streamlit run app.py`
3. Try Google Sign-In again

## Alternative: Use Demo Mode

If you want to test without Google OAuth:
1. On the login page, use "Demo Mode"
2. Enter any email (e.g., `test@nm2tech.com`)
3. Click "Login (Demo)"
4. No Google authentication needed!
