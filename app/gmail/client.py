"""Authenticated Gmail API client with error mapping.

Scope is `gmail.modify`: read mail + change labels. It does NOT permit permanent deletion
and this project never sends mail.
"""
from __future__ import annotations

import logging
import os
import socket
from pathlib import Path
from typing import Callable

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
_TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
_RATE_REASONS = ("ratelimitexceeded", "userratelimitexceeded", "backenderror", "quotaexceeded")


class GmailError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class GmailTransientError(GmailError):
    """Rate limit, 5xx, network problem: safe to retry."""


class GmailAuthError(GmailError):
    """Token missing/expired/revoked: needs `python main.py auth`."""


class GmailNotFound(GmailError):
    pass


def authorize(credentials_path: str, token_path: str, redirect_uri: str = "http://localhost:8000/auth/callback") -> None:
    """Interactive one-time OAuth flow. Writes the token file."""
    from google_auth_oauthlib.flow import Flow
    import webbrowser
    import os

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    if not Path(credentials_path).exists():
        raise GmailAuthError(f"OAuth client file not found: {credentials_path}")
    
    flow = Flow.from_client_secrets_file(credentials_path, SCOPES, redirect_uri=redirect_uri)
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"\n1. Please visit this URL to authorize:\n{auth_url}\n")
    print(f"2. After authorizing, you will be redirected to a URL that starts with {redirect_uri}")
    print("3. Copy the ENTIRE URL from your browser's address bar and paste it below.")
    
    try:
        webbrowser.open(auth_url, new=1, autoraise=True)
    except Exception:
        pass
        
    auth_response = input("\nEnter the full redirect URL here: ").strip()
    flow.fetch_token(authorization_response=auth_response)
    _write_token(token_path, flow.credentials.to_json())


def _write_token(token_path: str, content: str) -> None:
    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(content)


class GmailClient:
    def __init__(self, credentials_path: str, token_path: str = None, token_json_str: str = None, on_token_refresh: Callable[[str], None] = None):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.token_json_str = token_json_str
        self.on_token_refresh = on_token_refresh
        self._service = None

    def _build_service(self):
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import json

        creds = None
        if self.token_json_str:
            creds = Credentials.from_authorized_user_info(json.loads(self.token_json_str), SCOPES)
        elif self.token_path and Path(self.token_path).exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        else:
            raise GmailAuthError("No token provided - run: python main.py auth")

        if not creds.valid:
            if creds.refresh_token:
                try:
                    creds.refresh(Request())
                    if self.on_token_refresh:
                        self.on_token_refresh(creds.to_json())
                    elif self.token_path:
                        _write_token(self.token_path, creds.to_json())
                except RefreshError as exc:
                    raise GmailAuthError(f"token refresh failed ({exc}) - run: python main.py auth") from exc
                except Exception as exc:  # network trouble while refreshing
                    raise GmailTransientError(f"token refresh unavailable: {exc}") from exc
            else:
                raise GmailAuthError("token invalid and no refresh token - run: python main.py auth")
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def service(self):
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def call(self, build_request: Callable):
        """Run `build_request(service).execute()`, mapping errors to GmailError subclasses."""
        from googleapiclient.errors import HttpError

        try:
            return build_request(self.service()).execute()
        except GmailError:
            raise
        except HttpError as exc:
            status = int(getattr(exc.resp, "status", 0) or 0)
            body = (exc.content.decode("utf-8", "ignore") if isinstance(exc.content, bytes) else str(exc.content)).lower()
            if status == 401:
                self._service = None       # force token reload next time
                raise GmailAuthError("Gmail rejected credentials (401)", status) from exc
            if status in _TRANSIENT_STATUS or (status == 403 and any(r in body for r in _RATE_REASONS)):
                raise GmailTransientError(f"Gmail temporary error {status}", status) from exc
            if status == 404:
                raise GmailNotFound("Gmail resource not found", status) from exc
            raise GmailError(f"Gmail API error {status}", status) from exc
        except (socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
            raise GmailTransientError(f"network error talking to Gmail: {exc}") from exc
