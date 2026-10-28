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

# Configure serverless writable paths if running on Vercel
if os.environ.get("VERCEL"):
    if not os.environ.get("DATABASE_PATH"):
        os.environ["DATABASE_PATH"] = "/tmp/emails.db"
    if not os.environ.get("LOG_DIR"):
        os.environ["LOG_DIR"] = "/tmp/logs"

from app.config import load_config
from app.web.api import create_app

cfg = load_config(require_gemini=False)
app = create_app(cfg)
