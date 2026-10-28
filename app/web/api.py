import os
import json
import logging
import threading
import urllib.parse
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Response, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from pydantic import BaseModel, Field

from app.config import Config, load_config
from app.database.db import Database
from app.gmail.actions import GmailActions
from app.gmail.client import GmailClient, GmailAuthError
from app.models import CATEGORIES
from app.rules.decision_engine import CATEGORY_LABELS
from app.utils import utcnow_iso
from app.web.auth import get_auth_url, exchange_code

log = logging.getLogger(__name__)
_active_sync_users = set()
_active_sync_lock = threading.Lock()


class UserSettingsPayload(BaseModel):
    confidence_threshold: float = Field(ge=0.5, le=1.0, default=0.85)
    spam_policy: str = Field(pattern=r'^(label|quarantine|spam)$', default='quarantine')
    dry_run: bool = False

class ReviewEmailPayload(BaseModel):
    action: str = Field(pattern=r'^(approve|reject|dismiss|ignore|change_category)$')
    new_category: Optional[str] = None

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

def seed_demo_workspace(db: Database, user_id: str = "demo@example.com"):
    email = user_id
    db.upsert_user(user_id, email, json.dumps({"token": "demo_token"}))
    
    sample_data = [
        ("demo-1", "Urgent: Q4 Executive Strategy Meeting Rescheduled", "Sarah Connor <ceo@acme-corp.com>",
         "urgent", "high", 0.98, "Executive briefing reschedule with immediate deadline action needed.",
         ["AI-URGENT"], [], "done", "2026-10-24T09:15:00+00:00"),
         
        ("demo-2", "CS 61A: Assignment 4 Deadline Extended", "Prof. Russell <cs61a@berkeley.edu>",
         "academic", "high", 0.94, "Academic portal submission window deadline update.",
         ["AI-ACADEMIC", "AI-IMPORTANT"], [], "done", "2026-10-24T08:30:00+00:00"),
         
        ("demo-3", "Client Architecture Review: Cloud Migration", "Alex Rivera <alex.rivera@fintech-partners.com>",
         "work", "high", 0.93, "Quarterly infrastructure review proposal for enterprise client.",
         ["AI-WORK"], [], "done", "2026-10-24T08:00:00+00:00"),
         
        ("demo-4", "GitHub Enterprise: Copilot Security & Audit Updates", "GitHub Team <updates@github.com>",
         "promotional", "low", 0.92, "Monthly product update newsletter with unsubscribe header.",
         ["AI-PROMOTIONAL"], [], "done", "2026-10-24T07:45:00+00:00"),
         
        ("demo-5", "1:1 Sync: Product Architecture & System Design", "Elena Rostova <elena@nyalazone.io>",
         "meeting", "medium", 0.95, "Calendar invite sync request for bi-weekly engineering roadmap.",
         ["AI-MEETING"], [], "done", "2026-10-24T07:10:00+00:00"),
         
        ("demo-6", "Dinner catch-up this weekend in San Francisco?", "Marcus Vance <marcus.vance@gmail.com>",
         "normal", "low", 0.89, "Informal personal conversation between colleagues.",
         [], [], "done", "2026-10-24T06:30:00+00:00"),
         
        ("demo-7", "Security Alert: Verify your payment credentials immediately", "Support Center <security@bank-verify-auth92.com>",
         "spam", "high", 0.68, "Detected suspicious link target mismatch and unverified sender domain.",
         ["AI-REVIEW", "AI-SUSPICIOUS"], ["link_text_mismatch", "suspicious_sender"], "review", "2026-10-24T09:45:00+00:00"),
         
        ("demo-8", "Review requested: Advisory agreement draft terms", "Jordan Lee <jordan.lee@counsel-advisors.net>",
         "work", "medium", 0.54, "Ambiguous classification between legal contract draft and commercial inquiry; confidence 0.54 is below the 0.85 automation threshold.",
         ["AI-REVIEW"], [], "review", "2026-10-24T10:05:00+00:00"),
    ]
    
    from app.models import Email, Classification
    for mid, subj, sender, cat, prio, conf, reason, labels, flags, status, ts in sample_data:
        db.register_message(mid, user_id)
        e = Email(message_id=mid, user_id=user_id, thread_id=f"th_{mid}", sender=sender,
                  sender_email=sender.split("<")[-1].rstrip(">"), subject=subj, body=f"Email body preview for: {subj}",
                  recipients=[email], timestamp=ts, labels=["INBOX"] if status != "done" or not labels else labels)
        db.save_email_metadata(mid, e)
        db.save_classification(mid, Classification(category=cat, priority=prio, confidence=conf, reason=reason, model="gemini-2.5-flash"), flags)
        for label in labels:
            db.record_action(mid, "label", label)
        db.set_status(mid, status)

def create_app(cfg: Config, db: Database = None) -> FastAPI:
    app = FastAPI(title="Email Automata - AI Email Intelligence")
    db = db or Database(cfg.database_path)

    def get_current_user(request: Request) -> str:
        user_id = _validate_session_token(request)
        user = db.get_user(user_id)
        if not user or not user["token_json"]:
            raise HTTPException(status_code=401, detail="Session revoked")
        return user_id

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        # CSRF Guard for state-changing API requests
        if request.method in ("POST", "PUT", "DELETE", "PATCH") and request.url.path.startswith("/api/"):
            sec_fetch_site = request.headers.get("sec-fetch-site")
            if sec_fetch_site and sec_fetch_site.lower() == "cross-site":
                return JSONResponse({"detail": "Cross-site request blocked by CSRF defense."}, status_code=403)
            
            origin = request.headers.get("origin")
            if origin:
                try:
                    origin_host = urllib.parse.urlparse(origin).hostname or ""
                    req_host = (request.headers.get("host") or "").split(":")[0]
                    allowed_hosts = {req_host, "localhost", "127.0.0.1", cfg.dashboard_host.split(":")[0]}
                    if origin_host not in allowed_hosts and not origin_host.startswith("127."):
                        return JSONResponse({"detail": "Origin mismatch blocked by CSRF defense."}, status_code=403)
                except Exception:
                    pass

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        forwarded = request.headers.get("x-forwarded-proto", "").lower()
        if forwarded == "https" or request.url.scheme == "https":
            if not (cfg.dashboard_host in ("127.0.0.1", "localhost", "0.0.0.0") or cfg.dashboard_host.startswith("127.")):
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.get("/api/health")
    @app.get("/health")
    def health_check():
        db_ok = False
        try:
            db._run("SELECT 1", fetch="one")
            db_ok = True
        except Exception as exc:
            db_ok = False
            log.error("Health check database failure: %s", exc)

        status_code = 200 if db_ok else 503
        return JSONResponse(
            content={
                "status": "healthy" if db_ok else "unhealthy",
                "database": "connected" if db_ok else "disconnected",
                "timestamp": utcnow_iso(),
                "version": "1.0.0"
            },
            status_code=status_code
        )

    @app.api_route("/api/index.py", methods=["GET", "POST"])
    def vercel_entrypoint_debug(request: Request):
        return {
            "path": request.url.path,
            "scope_path": request.scope.get("path"),
            "headers": dict(request.headers)
        }


    def _is_cookie_secure(req: Request) -> bool:
        forwarded = req.headers.get("x-forwarded-proto", "").lower()
        if forwarded == "https" or req.url.scheme == "https":
            return True
        if cfg.google_redirect_uri.startswith("https://") and not (
            cfg.dashboard_host in ("127.0.0.1", "localhost", "0.0.0.0") or cfg.dashboard_host.startswith("127.")
        ):
            return True
        return False

    @app.get("/auth/google")
    @app.get("/google")
    def auth_google(request: Request):
        if not Path(cfg.gmail_credentials_path).exists():
            return HTMLResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Google Credentials Required - Email Automata</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
                        .card { background: #1e293b; padding: 2rem 2.5rem; border-radius: 1rem; max-width: 620px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
                        h1 { color: #f43f5e; margin-top: 0; font-size: 1.5rem; display: flex; align-items: center; gap: 8px; }
                        p { line-height: 1.6; color: #94a3b8; }
                        code { background: #0f172a; color: #38bdf8; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.9em; font-family: monospace; }
                        ol { color: #cbd5e1; padding-left: 1.2rem; line-height: 1.8; }
                        a { color: #38bdf8; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                        .actions { margin-top: 2rem; display: flex; gap: 12px; flex-wrap: wrap; }
                        .btn { display: inline-block; padding: 0.75rem 1.5rem; background: #2563eb; color: #fff; border-radius: 9999px; font-weight: 500; text-decoration: none; }
                        .btn-sec { background: #334155; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>&#9888; Google OAuth Credentials Missing</h1>
                        <p>The application could not find <code>credentials.json</code> on this server.</p>
                        <p>To connect your live Gmail inbox:</p>
                        <ol>
                            <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener">Google Cloud Console &rarr; Credentials</a>.</li>
                            <li>Create an <strong>OAuth client ID</strong> (Application type: <strong>Web application</strong>).</li>
                            <li>Add Authorized redirect URI: <code>http://localhost:5000/auth/callback</code> (or match your <code>GOOGLE_REDIRECT_URI</code>).</li>
                            <li>Download the client secret JSON file and rename it to <code>credentials.json</code> in this project directory.</li>
                        </ol>
                        <div class="actions">
                            <a href="/auth/demo" class="btn">Explore Interactive Demo Workspace &rarr;</a>
                            <a href="/" class="btn btn-sec">&larr; Back to Dashboard</a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                status_code=400
            )
        try:
            url, state, code_verifier = get_auth_url(cfg)
            res = RedirectResponse(url)
            # Store state in DB fallback with 15-minute TTL to survive domain mismatch (127.0.0.1 vs localhost) or third-party cookie loss
            db.save_oauth_state(state, code_verifier or "")
            
            secure = _is_cookie_secure(request)
            cookie_val = f"{state}|{code_verifier}" if code_verifier else state
            res.set_cookie(key="oauth_state", value=cookie_val, httponly=True, max_age=600, samesite="lax", secure=secure)
            return res
        except Exception as e:
            return HTMLResponse(f"OAuth Initialization Error: {e}", status_code=500)

    @app.get("/auth/demo")
    @app.get("/demo")
    def auth_demo(request: Request):
        user_id = "demo@example.com"
        user = db.get_user(user_id)
        if not user or not user["token_json"]:
            seed_demo_workspace(db, user_id)

        res = RedirectResponse("/")
        token = session_signer.dumps(user_id)
        res.set_cookie(key=SESSION_COOKIE, value=token, httponly=True, max_age=86400 * 7, samesite="lax", secure=_is_cookie_secure(request), path="/")
        return res

    @app.post("/api/demo/reset")
    @app.post("/demo/reset")
    def reset_demo_endpoint(user_id: str = Depends(get_current_user)):
        if user_id != "demo@example.com":
            raise HTTPException(status_code=403, detail="Reset is only permitted in Demo workspace")
        db.reset_demo_data(user_id)
        seed_demo_workspace(db, user_id)
        return {"success": True, "message": "Demo workspace successfully reset to initial state"}

    @app.get("/auth/callback")
    @app.get("/callback")
    def auth_callback(request: Request, response: Response):
        try:
            oauth_error = request.query_params.get("error")
            if oauth_error:
                url_state = request.query_params.get("state")
                if url_state:
                    db.consume_oauth_state(url_state)
                error_desc = request.query_params.get("error_description") or oauth_error
                return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authorization Cancelled - Email Automata</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
                        .card {{ background: #1e293b; padding: 2.25rem; border-radius: 12px; max-width: 580px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }}
                        h2 {{ color: #f59e0b; margin-top: 0; font-size: 1.35rem; }}
                        p {{ line-height: 1.6; color: #94a3b8; font-size: 0.95rem; }}
                        .error-detail {{ background: #0f172a; padding: 0.75rem 1rem; border-radius: 8px; font-family: monospace; font-size: 0.85rem; color: #fbbf24; word-break: break-all; margin: 1rem 0; border: 1px solid #292524; }}
                        .actions {{ margin-top: 1.75rem; display: flex; gap: 12px; flex-wrap: wrap; }}
                        .btn {{ display: inline-block; padding: 0.65rem 1.25rem; background: #4338ca; color: #fff; border-radius: 8px; font-weight: 500; text-decoration: none; font-size: 0.9rem; }}
                        .btn-sec {{ background: #334155; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2>Google Authorization Cancelled</h2>
                        <p>Google OAuth verification was cancelled or declined:</p>
                        <div class="error-detail">{error_desc}</div>
                        <div class="actions">
                            <a href="/auth/google" class="btn">Try Connecting Again &rarr;</a>
                            <a href="/auth/demo" class="btn btn-sec">Explore Demo Mode</a>
                        </div>
                    </div>
                </body>
                </html>
                """, status_code=200)

            url_state = request.query_params.get("state")
            if not url_state:
                raise ValueError("Missing OAuth state parameter. Please try logging in again.")

            stored_cookie = request.cookies.get("oauth_state")
            code_verifier = None
            valid_state = False

            # Check 1: Primary cookie match
            if stored_cookie:
                parts = stored_cookie.split("|", 1)
                stored_state = parts[0]
                if stored_state == url_state:
                    valid_state = True
                    code_verifier = parts[1] if len(parts) > 1 else None
                    # Clean up DB state record as well
                    db.consume_oauth_state(url_state)

            # Check 2: Database state fallback (handles 127.0.0.1 vs localhost domain separation, Safari ITP, partitioned cookies)
            if not valid_state:
                state_record = db.consume_oauth_state(url_state)
                if state_record is not None:
                    valid_state = True
                    code_verifier = state_record.get("code_verifier") or None

            if not valid_state:
                raise ValueError("Invalid, mismatched, or expired OAuth state. Please try logging in again.")
                
            token_json = exchange_code(cfg, str(request.url), url_state, code_verifier)
            # Validate token and get user email
            client = GmailClient(cfg.gmail_credentials_path, token_json_str=token_json)
            profile = client.call(lambda s: s.users().getProfile(userId='me'))
            email = profile.get("emailAddress")
            user_id = email
            
            db.upsert_user(user_id, email, token_json)
            
            # Relative redirect keeps user on their active host (127.0.0.1 or localhost or custom domain)
            res = RedirectResponse("/", status_code=303)
            token = session_signer.dumps(user_id)
            res.set_cookie(
                key=SESSION_COOKIE,
                value=token,
                httponly=True,
                max_age=86400 * 7,
                samesite="lax",
                secure=_is_cookie_secure(request),
                path="/"
            )
            res.delete_cookie("oauth_state", path="/")
            return res
        except Exception as e:
            return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Notice - Email Automata</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
                    .card {{ background: #1e293b; padding: 2.25rem; border-radius: 12px; max-width: 580px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }}
                    h2 {{ color: #f43f5e; margin-top: 0; font-size: 1.35rem; }}
                    p {{ line-height: 1.6; color: #94a3b8; font-size: 0.95rem; }}
                    .error-detail {{ background: #0f172a; padding: 0.75rem 1rem; border-radius: 8px; font-family: monospace; font-size: 0.85rem; color: #fb7185; word-break: break-all; margin: 1rem 0; border: 1px solid #292524; }}
                    .actions {{ margin-top: 1.75rem; display: flex; gap: 12px; flex-wrap: wrap; }}
                    .btn {{ display: inline-block; padding: 0.65rem 1.25rem; background: #4338ca; color: #fff; border-radius: 8px; font-weight: 500; text-decoration: none; font-size: 0.9rem; }}
                    .btn-sec {{ background: #334155; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>OAuth Authentication Notice</h2>
                    <p>Google OAuth verification could not be completed:</p>
                    <div class="error-detail">{e}</div>
                    <p>If you are testing locally, verify that your OAuth redirect URI in Google Cloud Console matches your current port and host.</p>
                    <div class="actions">
                        <a href="/auth/google" class="btn">Try Connecting Again &rarr;</a>
                        <a href="/auth/demo" class="btn btn-sec">Explore Demo Mode</a>
                    </div>
                </div>
            </body>
            </html>
            """, status_code=400)

    @app.post("/api/disconnect")
    @app.post("/disconnect")
    def disconnect(request: Request, response: Response, user_id: str = Depends(get_current_user)):
        res = JSONResponse({"success": True})
        res.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax", secure=_is_cookie_secure(request), path="/")
        db.upsert_user(user_id, user_id, "")
        return res

    @app.get("/api/me")
    @app.get("/me")
    def get_me(request: Request):
        token = request.cookies.get(SESSION_COOKIE)
        if not token:
            return {"connected": False}
        try:
            user_id = session_signer.loads(token, max_age=86400 * 7)
        except (BadSignature, SignatureExpired):
            return {"connected": False}
        user = db.get_user(user_id)
        if not user or not user["token_json"]:
            return {"connected": False}
        u = dict(user)
        is_demo = (u.get("id") == "demo@example.com")
        return {
            "connected": True,
            "email": u.get("email"),
            "is_demo": is_demo,
            "last_sync": u.get("last_successful_sync"),
            "sync_status": u.get("sync_status"),
        }

    @app.get("/api/dashboard")
    @app.get("/dashboard")
    def get_dashboard(user_id: str = Depends(get_current_user)):
        user = dict(db.get_user(user_id)) if db.get_user(user_id) else {}
        stats = db.stats(user_id=user_id)
        stats["sync_status"] = user.get("sync_status")
        stats["last_sync"] = user.get("last_successful_sync")
        return stats

    @app.get("/api/emails")
    @app.get("/emails")
    def get_emails(user_id: str = Depends(get_current_user)):
        return db.recent(user_id=user_id, limit=100)

    @app.get("/api/emails/{message_id}")
    @app.get("/emails/{message_id}")
    def get_email_details(message_id: str, user_id: str = Depends(get_current_user)):
        detail = db.get_email_detail(message_id, user_id=user_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Email not found")
        return detail

    @app.post("/api/scan")
    @app.post("/scan")
    def scan_emails(background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
        from app.ai.classifier import EmailClassifier, make_gemini_call
        from app.gmail.client import GmailClient
        from app.notify import Notifier
        from app.worker import Worker
        try:
            user = db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
                
            if user_id == "demo@example.com":
                db.update_user_sync(user_id, "success_0")
                return {"success": True, "status": "syncing"}

            with _active_sync_lock:
                if user_id in _active_sync_users:
                    return {"success": True, "status": "syncing", "message": "Scan already in progress"}
                _active_sync_users.add(user_id)

            db.update_user_sync(user_id, "syncing")
            
            def run_sync():
                try:
                    classifier = EmailClassifier(make_gemini_call(cfg.gemini_api_key, cfg.gemini_model), model=cfg.gemini_model,
                                                 max_retries=cfg.llm_max_retries, base_delay=cfg.retry_base_delay)
                    worker = Worker(cfg, db, classifier, Notifier(cfg.notify_webhook_url))
                    worker.process_user(dict(user))
                finally:
                    with _active_sync_lock:
                        _active_sync_users.discard(user_id)
                
            background_tasks.add_task(run_sync)
            return {"success": True, "status": "syncing"}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="An internal error occurred during scanning.")

    @app.get("/api/cron")
    @app.get("/cron")
    @app.post("/api/cron")
    @app.post("/cron")
    def vercel_cron_handler(request: Request):
        cron_secret = os.getenv("CRON_SECRET")
        if cron_secret:
            auth_header = request.headers.get("authorization") or ""
            if auth_header != f"Bearer {cron_secret}":
                raise HTTPException(status_code=401, detail="Unauthorized cron invocation")

        from app.ai.classifier import EmailClassifier, make_gemini_call
        from app.notify import Notifier
        from app.worker import Worker

        if not cfg.gemini_api_key:
            return {"status": "skipped", "reason": "GEMINI_API_KEY not configured"}

        users = db.get_users()
        active_users = [u for u in users if u["id"] != "demo@example.com" and u.get("token_json")]
        processed_total = 0
        errors = []

        try:
            classifier = EmailClassifier(make_gemini_call(cfg.gemini_api_key, cfg.gemini_model),
                                         model=cfg.gemini_model,
                                         max_retries=cfg.llm_max_retries,
                                         base_delay=cfg.retry_base_delay)
            worker = Worker(cfg, db, classifier, Notifier(cfg.notify_webhook_url))
            for u in active_users:
                try:
                    count = worker.process_user(dict(u))
                    processed_total += count
                except Exception as exc:
                    errors.append(f"{u['id']}: {str(exc)}")
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

        return {
            "status": "success",
            "users_synced": len(active_users),
            "emails_processed": processed_total,
            "errors": errors,
            "timestamp": utcnow_iso()
        }

    @app.get("/api/settings")
    @app.get("/settings")
    def get_settings(user_id: str = Depends(get_current_user)):
        user = db.get_user(user_id)
        u = dict(user) if user else {}
        settings = json.loads(u["settings"]) if u and u.get("settings") else {}
        return {
            "confidence_threshold": settings.get("confidence_threshold", cfg.confidence_threshold),
            "spam_policy": settings.get("spam_policy", cfg.spam_policy),
            "dry_run": settings.get("dry_run", cfg.dry_run),
            "allowed_actions": ["Add Label", "Remove Inbox"] if cfg.spam_policy != "spam" else ["Add Label", "Remove Inbox", "Mark Spam"]
        }

    @app.post("/api/settings")
    @app.post("/settings")
    async def update_settings(request: Request, user_id: str = Depends(get_current_user)):
        data = await request.json()
        validated = UserSettingsPayload(**data)
        db.update_user_settings(user_id, validated.model_dump_json())
        return {"success": True}
        
    @app.post("/api/emails/{message_id}/review")
    @app.post("/emails/{message_id}/review")
    async def review_email(message_id: str, request: Request, user_id: str = Depends(get_current_user)):
        data = await request.json()
        action = data.get("action", "approve")
        new_category = data.get("new_category")
        
        email = db.get_email_row(message_id)
        if not email or email["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Email not found")

        user = db.get_user(user_id)
        user_settings = {}
        if user and user.get("settings"):
            try:
                user_settings = json.loads(user["settings"])
            except Exception:
                user_settings = {}
        is_dry_run = user_settings.get("dry_run", cfg.dry_run)
        is_live_account = user_id != "demo@example.com" and bool(user and user.get("token_json"))

        actions_client = None
        if is_live_account:
            try:
                gmail_client = GmailClient(cfg.gmail_credentials_path, token_json_str=user["token_json"])
                actions_client = GmailActions(gmail_client, dry_run=is_dry_run)
            except Exception as exc:
                log.warning("Could not initialize Gmail client for review action: %s", exc)
        
        if action == "change_category" or (new_category and new_category.lower() in CATEGORIES):
            cat = (new_category or "normal").lower().strip()
            if cat not in CATEGORIES:
                raise HTTPException(status_code=400, detail=f"Invalid category: {new_category}")
            
            if actions_client:
                target_label = CATEGORY_LABELS.get(cat)
                if target_label:
                    try:
                        actions_client.apply(message_id, [target_label], remove_inbox=False)
                    except Exception as exc:
                        log.error("Failed to apply label in Gmail for %s: %s", message_id, exc)

            db.update_email_category(message_id, cat, f"User corrected category to {cat} via Review Queue")
            return {"success": True, "action": "change_category", "category": cat}
        elif action in ("reject", "dismiss", "ignore"):
            db.set_status(message_id, "done")
            db.record_action(message_id, "manual_dismiss", "Dismissed from review queue without modification")
            return {"success": True, "action": "dismiss"}
        else:
            detail = db.get_email_detail(message_id, user_id=user_id)
            classifications = detail.get("classifications", []) if detail else []
            cat = classifications[0]["category"] if classifications else "normal"

            if actions_client:
                target_label = CATEGORY_LABELS.get(cat)
                if target_label:
                    try:
                        actions_client.apply(message_id, [target_label], remove_inbox=False)
                    except Exception as exc:
                        log.error("Failed to apply label in Gmail on approval for %s: %s", message_id, exc)

            db.set_status(message_id, "done")
            db.record_action(message_id, "manual_approve", f"Approved by user ({cat}) in review queue")
            return {"success": True, "action": "approve"}


    frontend_dist = Path("frontend/dist").resolve()
    if not frontend_dist.exists():
        frontend_dist = (Path(__file__).resolve().parents[2] / "frontend" / "dist").resolve()

    assets_path = frontend_dist / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        frontend_path = frontend_dist / "index.html"
        if not frontend_path.exists():
            return HTMLResponse("Frontend build not found. Run 'npm --prefix frontend run build' first.", status_code=404)
        return HTMLResponse(frontend_path.read_text(encoding="utf-8"))

    return app
