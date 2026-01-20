# Google OAuth Authentication Setup Guide

## Overview

The application now supports Google OAuth authentication for multi-tenant access. Users can sign in with their Google accounts, and the system automatically creates tenants based on email domains.

## Setup Instructions

### 1. Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select a Project**
   - Click "Select a project" → "New Project"
   - Name it (e.g., "SAM.gov Contract Finder")
   - Click "Create"

3. **Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" or "People API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - User Type: External (or Internal if using Google Workspace)
     - App name: "AI Contract Finder"
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Add "email", "profile", "openid"
     - Click "Save and Continue"
     - Test users: Add your email (for testing)
     - Click "Save and Continue"

5. **Create OAuth Client ID**
   - Application type: "Web application"
   - Name: "SAM.gov Contract Finder Web"
   - Authorized redirect URIs:
     - For local: `http://localhost:8501`
     - For production: `https://yourdomain.com`
   - Click "Create"
   - **Copy the Client ID and Client Secret**

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8501
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`

### 4. Run Database Migration

The database schema has been updated to support multi-tenancy. The tables will be created automatically on first run, but existing data needs migration:

```python
# Run this once to migrate existing profiles to default tenant
python migrate_to_multi_tenant.py
```

### 5. Test Authentication

1. Start the app:
   ```bash
   streamlit run app.py
   ```

2. You should see a login page
3. Click "Sign in with Google" or use demo mode
4. After authentication, you'll see your tenant name in the sidebar

## How It Works

### Tenant Creation

- **Automatic**: Tenants are created automatically based on email domain
- Example: `user@nm2tech.com` → Tenant: "Nm2tech Organization"
- Users with the same email domain belong to the same tenant

### Data Isolation

- Each tenant only sees:
  - Their own company profiles
  - Their own opportunity scores
  - Their own bid strategies
- Opportunities are shared (global) but scores are tenant-specific

### Demo Mode

For development/testing without Google OAuth:
- Enter any email in the demo login
- System creates tenant based on email domain
- No Google authentication required

## Production Deployment

### For Streamlit Cloud

1. Add environment variables in Streamlit Cloud settings:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (your Streamlit Cloud URL)

2. Update authorized redirect URI in Google Console:
   - Add your Streamlit Cloud URL: `https://your-app.streamlit.app`

### For Custom Domain

1. Update `GOOGLE_REDIRECT_URI` to your domain
2. Add domain to authorized redirect URIs in Google Console
3. Ensure HTTPS is enabled

## Troubleshooting

### "Google OAuth not configured"
- Check that `GOOGLE_CLIENT_ID` is set in `.env`
- Restart the Streamlit app after adding to `.env`

### "Token verification failed"
- Check that Client ID matches in `.env` and Google Console
- Ensure redirect URI matches exactly

### "Wrong issuer" error
- This is normal - Google uses different issuers
- The code handles this automatically

## Security Notes

- ✅ Client Secret should NEVER be exposed in frontend code
- ✅ Use environment variables for all secrets
- ✅ Enable HTTPS in production
- ✅ Regularly rotate OAuth credentials
- ✅ Monitor OAuth usage in Google Console

## Next Steps

- [ ] Set up Google OAuth credentials
- [ ] Add credentials to `.env`
- [ ] Test login with Google account
- [ ] Verify tenant isolation works
- [ ] Deploy to production with proper redirect URIs
