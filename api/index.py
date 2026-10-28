from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path so app modules can be imported in Vercel Serverless
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=root_dir / ".env")
except ImportError:
    pass

# In serverless execution, the ONLY writable directory is /tmp
if not os.environ.get("DATABASE_PATH") or not os.environ.get("DATABASE_PATH", "").startswith("/tmp"):
    os.environ["DATABASE_PATH"] = "/tmp/emails.db"
if not os.environ.get("LOG_DIR") or not os.environ.get("LOG_DIR", "").startswith("/tmp"):
    os.environ["LOG_DIR"] = "/tmp/logs"

# Ensure SESSION_SECRET_KEY exists even before user configures it in Vercel project settings
if not os.environ.get("SESSION_SECRET_KEY") or len(os.environ.get("SESSION_SECRET_KEY", "").strip()) < 32:
    import secrets
    os.environ["SESSION_SECRET_KEY"] = secrets.token_hex(32)

from app.config import load_config
from app.web.api import create_app

cfg = load_config(require_gemini=False)
fastapi_app = create_app(cfg)


class VercelPathMiddleware:
    """Restores the original request path from the query parameter in Vercel serverless rewrites."""
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            query_string = scope.get("query_string", b"").decode("utf-8", "ignore")
            if "__path__=" in query_string:
                import urllib.parse
                params = urllib.parse.parse_qs(query_string)
                if "__path__" in params:
                    raw_subpath = params.pop("__path__")[0].lstrip("/")
                    # If subpath starts with auth/, map to /auth/..., otherwise map to /api/...
                    if raw_subpath.startswith("auth/"):
                        scope["path"] = f"/{raw_subpath}"
                    else:
                        scope["path"] = f"/api/{raw_subpath}"
                    scope["raw_path"] = scope["path"].encode("utf-8")
                    scope["query_string"] = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
        await self.inner_app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
