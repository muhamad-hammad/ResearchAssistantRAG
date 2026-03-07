# Migration from Grok to Gemini Free API

This guide covers migrating from Grok to Google's Gemini free API both locally and on EC2.

## Why Gemini Free API?
- **Free tier:** Unlimited requests with rate limits (60 requests/minute)
- **Reliable:** Backed by Google
- **No credit card required** for free tier
- **Same code:** Uses OpenAI-compatible endpoint, minimal changes needed

## Local Setup

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy your API key

### Step 2: Update Your `.env` File

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-actual-api-key-here
GEMINI_MODEL=gemini-2.0-flash
```

Available models:
- `gemini-2.0-flash` (Latest, fastest, recommended)
- `gemini-1.5-flash` (Previous version)
- `gemini-1.5-pro` (More capable but slower)

### Step 3: Test It Locally

```bash
# Install/update dependencies
pip install -r requirements.txt

# Run your app
python -m uvicorn app.main:app --reload
```

The app should now use Gemini for LLM calls.

---

## EC2 Deployment

### Quick Summary of Changes for EC2

Instead of setting `GROK_API_KEY`, use:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
```

### Full EC2 Setup Steps

Follow the main **DEPLOY.md**, but at **Step 6 (Configure the App)**, use these settings:

```bash
nano .env
```

Then paste:
```env
DATABASE_URL=postgresql://myuser:mypassword@db:5432/research_rag
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=research_rag
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<your-random-secret-key>
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-gemini-api-key-here>
GEMINI_MODEL=gemini-2.0-flash
```

Then continue with the rest of DEPLOY.md (Step 7 onwards).

---

## Troubleshooting

### Rate Limiting
If you hit rate limits (60 req/min), the app will retry automatically with exponential backoff.

### Invalid API Key
Error: `google.auth.exceptions.DefaultCredentialsError`
- Double-check your API key is correct
- Ensure it's a **Gemini API key**, not a different Google Cloud API key

### Slow Responses
Gemini free tier has some latency. For production:
- Consider upgrading to pay-as-you-go (very cheap for education/hobby projects)
- Or switch to `gemini-1.5-flash` (faster)

### Network Issues on EC2
Make sure your EC2 security group allows **outbound HTTPS (port 443)** to Google's servers.

---

## Key Changes Made to Codebase

1. ✅ `.env.example` - Updated to show Gemini as production option
2. ✅ `.env` - Updated to use Gemini with example model
3. ✅ `app/services/llm_factory.py` - Removed Grok support, kept Gemini & Ollama
4. ✅ `DEPLOY.md` - Updated instructions to use Gemini API key

No code changes needed in your business logic — everything uses the same LLM interface!

---

## Rollback to Grok (if needed)

Simply change `.env`:
```env
LLM_PROVIDER=grok
GROK_API_KEY=xai-your-key-here
```

The code path still exists in version control if you need it.
