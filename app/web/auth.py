import os
from google_auth_oauthlib.flow import Flow
from app.config import Config
from app.gmail.client import SCOPES, _write_token

def get_web_flow(cfg: Config, state: str = None) -> Flow:
    if cfg.dashboard_host.startswith('127.') or cfg.dashboard_host == 'localhost':
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
    flow.fetch_token(authorization_response=request_url)
    return flow.credentials.to_json()
