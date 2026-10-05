import os
import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import BaseModel, Field

class UserSettingsPayload(BaseModel):
    confidence_threshold: float = Field(ge=0.5, le=1.0, default=0.85)
    spam_policy: str = Field(pattern=r'^(label|quarantine|spam)$', default='quarantine')
    dry_run: bool = False

from app.config import Config, load_config
from app.database.db import Database
from app.gmail.client import GmailClient, GmailAuthError
from app.web.auth import get_auth_url, exchange_code

SESSION_COOKIE = "session_token"
SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "")
if not SECRET_KEY or len(SECRET_KEY) < 32 or SECRET_KEY in ("change-me", "secret", "dev-secret", "fallback_secret_key_change_in_production"):
    raise RuntimeError("CRITICAL: SESSION_SECRET_KEY environment variable is missing, empty, or insecure. "
                       "It must be provided and cryptographically strong (at least 32 characters).")
session_signer = URLSafeTimedSerializer(SECRET_KEY)

def _validate_session_token(request: Request) -> str:
    """Decode and validate the session cookie. Does NOT check DB."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    try:
        user_id = session_signer.loads(token, max_age=86400 * 7) # 7 days
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_id

def create_app(cfg: Config, db: Database = None) -> FastAPI:
    app = FastAPI(title="AI Email Intelligence")
    db = db or Database(cfg.database_path)

    def get_current_user(request: Request) -> str:
        user_id = _validate_session_token(request)
        user = db.get_user(user_id)
        if not user or not user["token_json"]:
            raise HTTPException(status_code=401, detail="Session revoked")
        return user_id

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-eval' https://unpkg.com https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not cfg.dashboard_host.startswith("127."):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.get("/auth/google")
    def auth_google():
        url, state, code_verifier = get_auth_url(cfg)
        res = RedirectResponse(url)
        secure = not cfg.dashboard_host.startswith("127.")
        cookie_val = f"{state}|{code_verifier}" if code_verifier else state
        res.set_cookie(key="oauth_state", value=cookie_val, httponly=True, max_age=600, samesite="lax", secure=secure)
        return res

    @app.get("/auth/callback")
    def auth_callback(request: Request, response: Response):
        try:
            stored_cookie = request.cookies.get("oauth_state")
            if not stored_cookie:
                raise ValueError("Missing OAuth cookie. Please try logging in again.")
            
            parts = stored_cookie.split("|", 1)
            stored_state = parts[0]
            code_verifier = parts[1] if len(parts) > 1 else None
            
            url_state = request.query_params.get("state")
            if stored_state != url_state:
                raise ValueError("OAuth state mismatch. Please try logging in again.")
                
            token_json = exchange_code(cfg, str(request.url), stored_state, code_verifier)
            # Validate token and get user email
            client = GmailClient(cfg.gmail_credentials_path, token_json_str=token_json)
            profile = client.call(lambda s: s.users().getProfile(userId='me'))
            email = profile.get("emailAddress")
            user_id = email # Simple mapping
            
            db.upsert_user(user_id, email, token_json)
            
            res = RedirectResponse("/")
            token = session_signer.dumps(user_id)
            res.set_cookie(key=SESSION_COOKIE, value=token, httponly=True, samesite="lax", secure=not cfg.dashboard_host.startswith("127."))
            res.delete_cookie("oauth_state")
            return res
        except Exception as e:
            return HTMLResponse(f"OAuth Error: {e}", status_code=400)

    @app.post("/api/disconnect")
    def disconnect(response: Response, user_id: str = Depends(get_current_user)):
        res = JSONResponse({"success": True})
        res.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax", secure=not cfg.dashboard_host.startswith("127."))
        # Wipe token from DB to force re-auth
        db.upsert_user(user_id, user_id, "")
        return res

    @app.get("/api/me")
    def get_me(request: Request):
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return {"connected": False}
        try:
            user_id = session_signer.loads(token, max_age=86400 * 7)
        except (BadSignature, SignatureExpired):
            return {"connected": False}
        user = db.get_user(user_id)
        if not user:
            return {"connected": False}
        return {"connected": True, "email": user["email"]}

    @app.get("/api/dashboard")
    def get_dashboard(user_id: str = Depends(get_current_user)):
        return db.stats(user_id=user_id)

    @app.get("/api/emails")
    def get_emails(user_id: str = Depends(get_current_user)):
        return db.recent(user_id=user_id, limit=100)

    @app.post("/api/scan")
    def scan_emails(user_id: str = Depends(get_current_user)):
        from app.ai.classifier import EmailClassifier, make_gemini_call
        from app.gmail.client import GmailClient
        from app.notify import Notifier
        from app.worker import Worker
        try:
            classifier = EmailClassifier(make_gemini_call(cfg.gemini_api_key, cfg.gemini_model), model=cfg.gemini_model,
                                         max_retries=cfg.llm_max_retries, base_delay=cfg.retry_base_delay)
            worker = Worker(cfg, db, classifier, Notifier(cfg.notify_webhook_url))
            user = db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            count = worker.process_user(dict(user))
            return {"success": True, "processed": count}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="An internal error occurred during scanning.")

    @app.get("/api/settings")
    def get_settings(user_id: str = Depends(get_current_user)):
        user = db.get_user(user_id)
        settings = json.loads(user["settings"]) if user and user.get("settings") else {}
        return {
            "confidence_threshold": settings.get("confidence_threshold", cfg.confidence_threshold),
            "spam_policy": settings.get("spam_policy", cfg.spam_policy),
            "dry_run": settings.get("dry_run", cfg.dry_run),
            "allowed_actions": ["Add Label", "Remove Inbox"] if cfg.spam_policy != "spam" else ["Add Label", "Remove Inbox", "Mark Spam"]
        }

    @app.post("/api/settings")
    async def update_settings(request: Request, user_id: str = Depends(get_current_user)):
        data = await request.json()
        validated = UserSettingsPayload(**data)
        db.update_user_settings(user_id, validated.model_dump_json())
        return {"success": True}
        
    @app.post("/api/emails/{message_id}/review")
    async def review_email(message_id: str, request: Request, user_id: str = Depends(get_current_user)):
        data = await request.json()
        action = data.get("action") # approve, ignore, change_category
        email = db.get_email_row(message_id)
        if not email or email["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Handle logic here... For simplicity, mark as done
        db.set_status(message_id, "done")
        db.record_action(message_id, f"manual_{action}", f"User manually performed: {action}")
        return {"success": True}

    assets_path = Path("frontend/dist/assets").resolve()
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        frontend_path = Path("frontend/dist/index.html").resolve()
        if not frontend_path.exists():
            return "Frontend build not found.", 404
        return frontend_path.read_text(encoding="utf-8")

    return app
