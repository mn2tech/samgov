# Quick Setup Guide for itgovcon.streamlit.app

## ✅ Your Streamlit Cloud URL
**https://itgovcon.streamlit.app**

## Step 1: Streamlit Cloud Environment Variables

In your Streamlit Cloud app settings, add these **exact** environment variables:

| Variable Name | Value |
|--------------|-------|
| `GOOGLE_CLIENT_ID` | `your_client_id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | `your_client_secret` |
| `GOOGLE_REDIRECT_URI` | `https://itgovcon.streamlit.app` |

**Important**: 
- No trailing slash in the redirect URI
- Use `https://` (not `http://`)
- Copy the values exactly (no extra spaces)

## Step 2: Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized redirect URIs**, click **+ ADD URI**
6. Add exactly: `https://itgovcon.streamlit.app`
7. Click **SAVE**

**Critical**: The redirect URI must match **exactly**:
- ✅ `https://itgovcon.streamlit.app` (correct)
- ❌ `https://itgovcon.streamlit.app/` (wrong - has trailing slash)
- ❌ `http://itgovcon.streamlit.app` (wrong - missing 's' in https)
- ❌ `itgovcon.streamlit.app` (wrong - missing https://)

## Step 3: Restart Your App

After adding environment variables:
1. Go to your Streamlit Cloud dashboard
2. Click **Reboot app** or wait for auto-restart
3. Visit https://itgovcon.streamlit.app

## Step 4: Test Login

1. You should see "Sign in with Google" button
2. Click it
3. You'll be redirected to Google login
4. After logging in, you'll return to your app
5. You should see your email in the sidebar

## Troubleshooting

### Still seeing "Google OAuth not configured"?
- ✅ Check environment variables are set (no typos)
- ✅ Restart the app after adding variables
- ✅ Check variable names are exactly: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

### Getting "redirect_uri_mismatch" error?
- ✅ Verify redirect URI in Google Console is exactly: `https://itgovcon.streamlit.app`
- ✅ No trailing slash
- ✅ Must be `https://` not `http://`
- ✅ Check that `GOOGLE_REDIRECT_URI` in Streamlit Cloud matches exactly

### App not loading?
- ✅ Check Streamlit Cloud logs for errors
- ✅ Verify all dependencies installed successfully
- ✅ Make sure Python version is 3.11 or higher

## Optional: Additional Environment Variables

For full functionality, also add:

| Variable Name | Value |
|--------------|-------|
| `SAM_API_KEY` | Your SAM.gov API key |
| `OPENAI_API_KEY` | Your OpenAI API key |

These are optional - the app will work without them but with limited functionality.
