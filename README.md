# AI Email Intelligence

A complete web application that watches your Gmail inbox, classifies every new email with an LLM, and applies safe, reversible actions (labels, quarantine). It provides a professional web dashboard built on top of the original terminal automation engine.

## Features
- **Web Dashboard**: Modern interface with login, metrics, processing history, manual review queue, and email inspection drawer.
- **Gmail OAuth Flow with PKCE & DB State**: One-click Google connection with database-backed state verification, automatic fallback, and denial handling.
- **Token Encryption at Rest**: OAuth tokens are encrypted using AES-CBC + HMAC-SHA256 (Fernet) before persistence in SQLite.
- **CSRF & Security Headers**: Strict Content-Security-Policy (no unsafe-inline scripts), HTTP-only Secure SameSite cookies, and Sec-Fetch-Site cross-site mutation guards.
- **Health & Monitoring**: Clean `/api/health` endpoint reporting database connectivity and application status without leaking secrets.
- **Automatic detection**: Uses Gmail API history to discover and claim new mail safely.
- **Gemini 2.5 Flash classification**: Uses Pydantic structured output for strict, reliable automation.
- **Deterministic rules**: Pre-LLM phishing and malware checks (DMARC, suspicious links, dangerous attachments).
- **Safe action boundaries**: Gmail modifications (`AI-*` labels, quarantine, inbox archive) are isolated from AI hallucinations and enforce confidence thresholds.
- **Human-in-the-Loop Review**: Emails with confidence below threshold or flagged for review can be approved or re-categorized in the Review Queue, applying live Gmail labels.

## Architecture

```
Browser (Vue 3 / Vite / Tailwind)
   ↓ (Session Cookie / CSRF Protected)
FastAPI Backend (/api/health, /api/emails, /api/stats, /api/settings)
   ↓
Google OAuth 2.0 (gmail.modify scope, Fernet encrypted at rest)
   ↓
Gmail Reader (MIME decoding, sanitization, HTML stripping)
   ↓
Pre-processing & Rules Engine (Phishing, attachments, links, redaction)
   ↓
Gemini 2.5 Flash Classifier (Pydantic schema validation)
   ↓
Decision Engine (Confidence threshold, spam policies, review queue routing)
   ↓
Safe Gmail Action (Add label, quarantine, archive inbox — no permanent deletion)
   ↓
SQLite Database (WAL mode, transactions, audit logs, idempotency lease locks)
```

## Setup

1. **Create Google Cloud project**
2. **Enable Gmail API** (APIs & Services → Library)
3. **Configure OAuth as External** (OAuth consent screen, add yourself as a test user)
4. **Add OAuth redirect URI**: Must exactly match `http://localhost:5000/auth/callback` (or your production URL).
5. **Create Gemini API key**: [Google AI Studio](https://aistudio.google.com/apikey)
6. **Configure `.env`**:
   ```bash
   cp .env.example .env
   # Edit .env and insert your GEMINI_API_KEY, SESSION_SECRET_KEY, and GOOGLE_REDIRECT_URI
   ```
7. **Run application setup**:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Running the Application

**To start the Web Application (Backend & Dashboard):**
```bash
python main.py dashboard
```
Then visit `http://127.0.0.1:5000`. Click "Continue with Google" or test the interface in read-only sandbox mode.

**To run the background worker / polling engine:**
```bash
python main.py once       # Run a single discovery and processing cycle
python main.py run        # Start the continuous worker daemon
```

## Deploying to Vercel (All-in-One Serverless)

The application is configured to deploy both the Vue 3 frontend and FastAPI backend directly to Vercel via Serverless Functions and Vercel Cron.

### 1. Prerequisites on Vercel
In your Vercel Project Settings → **Environment Variables**, configure:
- `SESSION_SECRET_KEY`: A cryptographically secure random string (minimum 32 characters).
- `GEMINI_API_KEY`: Your Google AI Studio API key.
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID (from Google Cloud Console).
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret.
- `GOOGLE_REDIRECT_URI`: Set to `https://<your-vercel-domain>.vercel.app/auth/callback` (and add this exact URL to your Google Cloud Console Authorized Redirect URIs).
- `CRON_SECRET`: (Optional) Secret key to protect the `/api/cron` background polling endpoint.
- `DATABASE_PATH`: Defaults to `/tmp/emails.db` on Vercel serverless.

### 2. Deploy via Vercel CLI
```bash
npx vercel
```
Or push your repository to GitHub/GitLab and import it into Vercel. Vercel will automatically build the Vue frontend and provision the Python serverless function at `/api/index.py`.

### 3. Vercel Cron
`vercel.json` includes automatic cron scheduling (`*/10 * * * *`) that triggers `/api/cron` every 10 minutes to discover and process new incoming emails.


## Testing

```bash
python -m pytest tests/ -v
```
All external APIs (Gmail API, Google OAuth, Gemini API) are fully mocked for deterministic unit and scenario testing.

## Security & Architecture Standards
- **Token Encryption**: Persisted OAuth tokens in the `users` table are encrypted at rest with Fernet (`TOKEN_ENCRYPTION_KEY` or `SESSION_SECRET_KEY`).
- **SESSION_SECRET_KEY Requirement**: You MUST set a cryptographically secure, random string (>=32 chars) for `SESSION_SECRET_KEY` in your `.env`. The application validates this at startup.
- **CSRF & Replay Defense**: OAuth states are single-use and expire in 15 minutes. Mutating API endpoints block `Sec-Fetch-Site: cross-site` requests.
- **Database Concurrency**: The SQLite engine runs in WAL (Write-Ahead Logging) mode with `PRAGMA busy_timeout = 5000` and lease-based atomic message claiming to prevent race conditions.
- **No Destruction**: Scopes are restricted to `gmail.modify`. The system never calls trash or delete APIs; all automation is reversible.
