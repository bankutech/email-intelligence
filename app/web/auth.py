import base64
import json
import logging
import os
import urllib.parse
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from app.config import Config
from app.gmail.client import SCOPES, _write_token

log = logging.getLogger(__name__)


def has_google_credentials(cfg: Config) -> bool:
    """Check if Google OAuth credentials are provided via environment or filesystem."""
    if cfg.google_client_id and cfg.google_client_secret:
        return True
    if cfg.google_credentials_json:
        return True
    if cfg.gmail_credentials_path and Path(cfg.gmail_credentials_path).exists():
        return True
    return False


def get_web_flow(cfg: Config, state: str = None) -> Flow:
    if cfg.dashboard_host.startswith('127.') or cfg.dashboard_host in ('localhost', '0.0.0.0') or cfg.google_redirect_uri.startswith('http://'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    elif 'OAUTHLIB_INSECURE_TRANSPORT' in os.environ:
        del os.environ['OAUTHLIB_INSECURE_TRANSPORT']

    # 1. Direct environment variables (Recommended for Vercel / serverless / cloud)
    if cfg.google_client_id and cfg.google_client_secret:
        client_config = {
            "web": {
                "client_id": cfg.google_client_id,
                "client_secret": cfg.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [cfg.google_redirect_uri],
            }
        }
        return Flow.from_client_config(
            client_config,
            SCOPES,
            redirect_uri=cfg.google_redirect_uri,
            state=state,
        )

    # 2. Raw JSON string or base64 encoded credentials JSON in environment
    if cfg.google_credentials_json:
        raw = cfg.google_credentials_json.strip()
        try:
            client_config = json.loads(raw)
        except Exception:
            try:
                client_config = json.loads(base64.b64decode(raw).decode("utf-8"))
            except Exception as exc:
                raise ValueError(f"Invalid GOOGLE_CREDENTIALS_JSON format: {exc}") from exc
        return Flow.from_client_config(
            client_config,
            SCOPES,
            redirect_uri=cfg.google_redirect_uri,
            state=state,
        )

    # 3. Local file credentials.json
    if cfg.gmail_credentials_path and Path(cfg.gmail_credentials_path).exists():
        return Flow.from_client_secrets_file(
            cfg.gmail_credentials_path, 
            SCOPES, 
            redirect_uri=cfg.google_redirect_uri,
            state=state
        )

    raise ValueError(
        "Google OAuth credentials missing. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, "
        "or provide GOOGLE_CREDENTIALS_JSON, or place credentials.json in the workspace."
    )

def get_auth_url(cfg: Config) -> tuple[str, str, str]:
    flow = get_web_flow(cfg)
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url, state, getattr(flow, 'code_verifier', None)

def exchange_code(cfg: Config, request_url: str, state: str, code_verifier: str = None) -> str:
    flow = get_web_flow(cfg, state=state)
    if code_verifier:
        flow.code_verifier = code_verifier
    
    # Normalize request_url to match flow.redirect_uri scheme/host/path
    # while preserving query params (?code=...&state=...).
    # This prevents redirect_uri_mismatch when running behind reverse proxies (Render / Vercel)
    # or when the user lands on 127.0.0.1 vs localhost.
    parsed_req = urllib.parse.urlparse(request_url)
    parsed_redir = urllib.parse.urlparse(cfg.google_redirect_uri)
    normalized_url = urllib.parse.urlunparse((
        parsed_redir.scheme,
        parsed_redir.netloc,
        parsed_redir.path,
        parsed_req.params,
        parsed_req.query,
        parsed_req.fragment
    ))
    flow.fetch_token(authorization_response=normalized_url)
    return flow.credentials.to_json()
