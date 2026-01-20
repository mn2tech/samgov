# Fix Google OAuth 403 Error

## What the 403 Error Means

A 403 error from Google means "access denied" - this usually happens because:
1. Your OAuth app is in "Testing" mode and your email isn't added as a test user
2. The OAuth consent screen isn't properly configured
3. The app needs to be published (for production use)

## Solution: Configure OAuth Consent Screen

### Step 1: Go to OAuth Consent Screen

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to OAuth Consent Screen**
   - Click **"APIs & Services"** in the left menu
   - Click **"OAuth consent screen"**

### Step 2: Configure the Consent Screen

1. **User Type**
   - Choose **"External"** (unless you're using Google Workspace)
   - Click **"Create"**

2. **App Information**
   - **App name**: `AI Contract Finder` (or any name)
   - **User support email**: Your email address
   - **App logo**: (Optional - can skip)
   - **Application home page**: `https://itgovcon.streamlit.app`
   - **Application privacy policy link**: (Optional - can skip for now)
   - **Application terms of service link**: (Optional - can skip for now)
   - **Authorized domains**: (Leave empty for now)
   - **Developer contact information**: Your email address
   - Click **"Save and Continue"**

3. **Scopes**
   - Click **"Add or Remove Scopes"**
   - Make sure these scopes are selected:
     - ✅ `.../auth/userinfo.email`
     - ✅ `.../auth/userinfo.profile`
     - ✅ `openid`
   - Click **"Update"**
   - Click **"Save and Continue"**

4. **Test Users** (IMPORTANT!)
   - Click **"+ ADD USERS"**
   - Add your email address (the one you'll use to sign in)
   - Add any other test user emails
   - Click **"Add"**
   - Click **"Save and Continue"**

5. **Summary**
   - Review the information
   - Click **"Back to Dashboard"**

### Step 3: Publish Your App (Optional - for Production)

If you want anyone to be able to sign in (not just test users):

1. Go back to **"OAuth consent screen"**
2. At the top, you'll see **"Publishing status: Testing"**
3. Click **"PUBLISH APP"**
4. Confirm the publishing

**Note**: Publishing requires app verification if you use sensitive scopes, but for basic email/profile scopes, you can usually publish immediately.

## Quick Fix Checklist

- [ ] OAuth consent screen is configured
- [ ] Your email is added as a test user (if app is in Testing mode)
- [ ] Required scopes are added (email, profile, openid)
- [ ] App information is filled out
- [ ] Clicked "Save" on all steps

## After Fixing

1. **Wait 5-10 minutes** for changes to propagate
2. **Try signing in again** at https://itgovcon.streamlit.app
3. You should now be able to sign in with your Google account

## Alternative: Use Demo Mode

If you want to test the app without fixing OAuth:
- Use the **"Demo Mode"** on the login page
- Enter any email (e.g., `test@example.com`)
- Click **"Login (Demo)"**
- This works without Google OAuth

## Still Getting 403?

1. **Check your email is in test users list**
   - Go to OAuth consent screen → Test users
   - Make sure your email is there

2. **Check the scopes**
   - Make sure email, profile, and openid scopes are enabled

3. **Try publishing the app**
   - If you want anyone to sign in, publish the app
   - Note: This may require verification for sensitive scopes

4. **Check Google Cloud Console logs**
   - Go to APIs & Services → Dashboard
   - Check for any error messages
