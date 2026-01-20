# How to Add OpenAI API Key

## Quick Steps

1. **Get your OpenAI API key:**
   - Visit: https://platform.openai.com/api-keys
   - Sign in (or create account)
   - Click "Create new secret key"
   - Copy the key (it starts with `sk-`)

2. **Add to `.env` file:**
   - Open `.env` file in your project root
   - Find the line: `# OPENAI_API_KEY=your_openai_key_here`
   - Uncomment it and replace with your key:
     ```
     OPENAI_API_KEY=sk-your-actual-key-here
     ```

3. **Restart Streamlit app:**
   - Stop the app (Ctrl+C)
   - Run: `streamlit run app.py`

## Current .env File Location

Your `.env` file is at: `C:\Users\kolaw\Projects\samgov\.env`

## What to Add

Replace this line:
```bash
# OPENAI_API_KEY=your_openai_key_here
```

With this (using your actual key):
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Optional: Model Selection

You can also change the model (default is gpt-4-turbo-preview):
```bash
OPENAI_MODEL=gpt-4-turbo-preview
# Or use cheaper option:
# OPENAI_MODEL=gpt-3.5-turbo
```

## Cost Considerations

- **gpt-4-turbo-preview**: More accurate, higher cost (~$0.01-0.03 per opportunity)
- **gpt-3.5-turbo**: Faster, cheaper (~$0.001-0.002 per opportunity)

For testing, `gpt-3.5-turbo` works well and is much cheaper.

## Verify It's Working

After adding the key and restarting:
1. Fetch opportunities
2. Check the scores - they should vary (not all 52.0)
3. Classification should be more accurate

## Troubleshooting

**Error: "Invalid API key"**
- Check the key starts with `sk-`
- Make sure there are no extra spaces
- Verify the key is active in OpenAI dashboard

**Error: "Insufficient quota"**
- Add payment method to OpenAI account
- Check usage limits in OpenAI dashboard

**Still using rule-based scoring?**
- Check `.env` file has the key (not commented)
- Restart the Streamlit app
- Check terminal for any error messages

---

**Note:** The app works without OpenAI (uses rule-based), but AI-powered scoring is much more accurate!
