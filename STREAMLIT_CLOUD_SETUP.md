# Streamlit Cloud Deployment Guide

## Quick Setup Checklist

### 1. Environment Variables in Streamlit Cloud

Go to your Streamlit Cloud app settings and add these environment variables:

```
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=https://your-app-name.streamlit.app
```

**Important**: Replace `your-app-name` with your actual Streamlit Cloud app name.

### 2. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized redirect URIs**, add:
   - `https://your-app-name.streamlit.app` (your Streamlit Cloud URL)
   - Make sure it matches exactly (including `https://` and no trailing slash)

### 3. Other Environment Variables (Optional but Recommended)

```
SAM_API_KEY=your_sam_gov_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Verify Configuration

After adding the environment variables:

1. **Restart your Streamlit Cloud app** (if it's already running)
2. Visit your app URL
3. You should see:
   - ✅ "Sign in with Google" button (if OAuth is configured)
   - ✅ Or demo mode login (if OAuth is not configured)

### 5. Testing

1. Click "Sign in with Google"
2. You'll be redirected to Google's login page
3. After logging in, you'll be redirected back to your app
4. You should see your email and tenant name in the sidebar

## Troubleshooting

### "Google OAuth not configured" warning
- ✅ Check that `GOOGLE_CLIENT_ID` is set in Streamlit Cloud settings
- ✅ Restart the app after adding environment variables
- ✅ Make sure there are no extra spaces in the environment variable values

### "redirect_uri_mismatch" error
- ✅ Check that the redirect URI in Google Console **exactly matches** your Streamlit Cloud URL
- ✅ Must include `https://` (not `http://`)
- ✅ No trailing slash
- ✅ Example: `https://itgovcon.streamlit.app` (not `https://itgovcon.streamlit.app/`)

### "Token verification failed"
- ✅ Verify that `GOOGLE_CLIENT_ID` in Streamlit Cloud matches the Client ID in Google Console
- ✅ Check that the redirect URI matches exactly

### App not loading
- ✅ Check Streamlit Cloud logs for errors
- ✅ Verify all required dependencies are in `requirements.txt`
- ✅ Make sure Python version is compatible (3.11+ recommended)

## Next Steps

Once OAuth is working:
1. ✅ Test login with your Google account
2. ✅ Create your first company profile
3. ✅ Fetch opportunities from SAM.gov
4. ✅ Test the AI scoring and bid assistance features

## Security Notes

- 🔒 Never commit `.env` files to Git
- 🔒 Keep your Client Secret secure
- 🔒 Use HTTPS in production (Streamlit Cloud provides this automatically)
- 🔒 Regularly rotate OAuth credentials
