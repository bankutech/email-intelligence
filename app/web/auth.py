import os
import urllib.parse
from google_auth_oauthlib.flow import Flow
from app.config import Config
from app.gmail.client import SCOPES, _write_token

def get_web_flow(cfg: Config, state: str = None) -> Flow:
    if cfg.dashboard_host.startswith('127.') or cfg.dashboard_host in ('localhost', '0.0.0.0') or cfg.google_redirect_uri.startswith('http://'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    elif 'OAUTHLIB_INSECURE_TRANSPORT' in os.environ:
        del os.environ['OAUTHLIB_INSECURE_TRANSPORT']
    return Flow.from_client_secrets_file(
        cfg.gmail_credentials_path, 
        SCOPES, 
        redirect_uri=cfg.google_redirect_uri,
        state=state
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
