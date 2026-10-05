# AI Email Intelligence

A complete web application that watches your Gmail inbox, classifies every new email with an LLM, and applies safe, reversible actions (labels, quarantine). It provides a professional web dashboard built on top of the original terminal automation engine.

## Features
- **Web Dashboard**: Professional interface with login, statistics, processing history, and detailed AI analysis logic.
- **Gmail OAuth Flow**: Easy one-click "Continue with Google" connection.
- **Automatic detection**: Uses Gmail API to discover new mail.
- **Gemini 2.5 Flash classification**: Uses Pydantic structured output for strict, reliable automation.
- **Deterministic rules**: Pre-LLM phishing checks (DMARC, suspicious links, attachments).
- **Safety boundaries**: Actions are isolated from LLM output.

## Architecture

Browser
   ↓ (Vue 3 / Tailwind)
FastAPI Backend
   ↓
Google OAuth / Gmail API
   ↓
Existing Gmail Client
   ↓
Existing Gemini Classifier
   ↓
Existing Decision Engine
   ↓
Database (SQLite)

## Setup

1. **Create Google Cloud project**
2. **Enable Gmail API** (APIs & Services → Library)
3. **Configure OAuth as External** (OAuth consent screen, add yourself as a test user)
4. **Add OAuth redirect URI**: Must exactly match `http://localhost:5000/auth/callback` (or your production URL).
5. **Create Gemini API key**: [Google AI Studio](https://aistudio.google.com/apikey)
6. **Configure `.env`**:
   ```bash
   cp .env.example .env
   # Edit .env and insert your GEMINI_API_KEY and GOOGLE_REDIRECT_URI
   ```
7. **Run application setup**:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Running the Application

**To start the Web Application:**
```bash
python main.py dashboard
```
Then visit `http://127.0.0.1:5000`. Click "Continue with Google" to connect.

**To run the terminal commands (Original Interface):**
```bash
python main.py once       # Run a single polling cycle
python main.py run        # Start the background worker (polls every POLL_INTERVAL)
```

## Testing

```bash
pytest
```
(All tests use mocked external APIs or local memory DBs and will run in milliseconds).

## Security & Limitations
- **SESSION_SECRET_KEY Requirement**: You MUST set a cryptographically secure, random string (>=32 chars) for `SESSION_SECRET_KEY` in your `.env`. If this is missing or insecure, the application will crash on startup to prevent session hijacking.
- **Production Concurrency**: By default, this application utilizes SQLite. It uses strict transaction boundaries and idempotency checks to prevent duplicate actions. However, **for high-concurrency production deployments running multiple worker/API instances**, you must migrate from SQLite to PostgreSQL to avoid `database is locked` constraints.
- **Google OAuth**: Tokens are scoped strictly per-user in the database, isolated by cryptographic sessions.
- **No Deletion**: The system uses `gmail.modify` which cannot permanently delete emails or empty the trash. All automation is reversible via Gmail's interface.
