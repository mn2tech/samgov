# Where to Add Google OAuth Configuration

## Location 1: Streamlit Cloud Environment Variables

### Step-by-Step:

1. **Go to Streamlit Cloud Dashboard**
   - Visit: https://share.streamlit.io/
   - Sign in with your account

2. **Select Your App**
   - Click on your app: `itgovcon` (or whatever you named it)

3. **Go to Settings**
   - Click on the **"⚙️ Settings"** button (usually in the top right or in the app menu)

4. **Add Environment Variables**
   - Scroll down to **"Secrets"** or **"Environment Variables"** section
   - Click **"Add new secret"** or **"Edit secrets"**
   - Add these three secrets one by one:

   ```
   GOOGLE_CLIENT_ID = your_client_id_here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET = your_client_secret_here
   GOOGLE_REDIRECT_URI = https://itgovcon.streamlit.app
   ```

5. **Save**
   - Click **"Save"** or **"Deploy"**
   - The app will automatically restart

### Visual Guide:
```
Streamlit Cloud Dashboard
  └── Your App (itgovcon)
      └── Settings (⚙️)
          └── Secrets / Environment Variables
              ├── GOOGLE_CLIENT_ID = [paste your client ID]
              ├── GOOGLE_CLIENT_SECRET = [paste your client secret]
              └── GOOGLE_REDIRECT_URI = https://itgovcon.streamlit.app
```

---

## Location 2: Google Cloud Console (Authorized Redirect URI)

### Step-by-Step:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Select Your Project**
   - Click the project dropdown at the top
   - Select the project where you created your OAuth credentials

3. **Navigate to Credentials**
   - Click **"APIs & Services"** in the left menu
   - Click **"Credentials"**

4. **Edit Your OAuth Client**
   - Find your OAuth 2.0 Client ID (the one you're using for this app)
   - Click on it to edit

5. **Add Authorized Redirect URI**
   - Scroll down to **"Authorized redirect URIs"** section
   - Click **"+ ADD URI"**
   - Enter exactly: `https://itgovcon.streamlit.app`
   - **Important**: No trailing slash, must be `https://`

6. **Save**
   - Click **"SAVE"** at the bottom

### Visual Guide:
```
Google Cloud Console
  └── Your Project
      └── APIs & Services
          └── Credentials
              └── OAuth 2.0 Client ID (click to edit)
                  └── Authorized redirect URIs
                      └── + ADD URI
                          └── https://itgovcon.streamlit.app
```

---

## Quick Checklist

### ✅ Streamlit Cloud (Environment Variables)
- [ ] `GOOGLE_CLIENT_ID` = your client ID
- [ ] `GOOGLE_CLIENT_SECRET` = your client secret  
- [ ] `GOOGLE_REDIRECT_URI` = `https://itgovcon.streamlit.app`

### ✅ Google Cloud Console (Redirect URI)
- [ ] Added `https://itgovcon.streamlit.app` to Authorized redirect URIs
- [ ] No trailing slash
- [ ] Using `https://` (not `http://`)

---

## After Adding Both:

1. **Restart your Streamlit Cloud app** (it should auto-restart after saving secrets)
2. **Wait 1-2 minutes** for the app to redeploy
3. **Visit** https://itgovcon.streamlit.app
4. **Test** the "Sign in with Google" button

---

## Troubleshooting

### Can't find "Secrets" in Streamlit Cloud?
- Look for **"Environment Variables"** or **"App Settings"**
- Some versions call it **"Secrets"** in the left sidebar

### Can't find "Credentials" in Google Console?
- Make sure you're in the correct project
- Look under **"APIs & Services"** → **"Credentials"**
- If you don't see it, you may need to enable the API first

### Still getting errors?
- Make sure both locations are configured
- Wait a few minutes after saving (changes take time to propagate)
- Check that the redirect URI matches exactly (no trailing slash)
