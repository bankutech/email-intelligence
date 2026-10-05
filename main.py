"""CLI entry point.

  python main.py auth        one-time Gmail OAuth login
  python main.py run         start the background worker (runs until Ctrl+C)
  python main.py once        run a single polling cycle and exit
  python main.py dashboard   start the read-only web dashboard
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import ConfigError, load_config
from app.utils import SecretFilter


def setup_logging(cfg) -> None:
    Path(cfg.log_dir).mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handlers = [logging.StreamHandler(), RotatingFileHandler(Path(cfg.log_dir) / "app.log", maxBytes=2_000_000, backupCount=3)]
    secret_filter = SecretFilter([cfg.gemini_api_key, cfg.notify_webhook_url])
    root = logging.getLogger()
    root.setLevel(cfg.log_level)
    for h in handlers:
        h.setFormatter(fmt)
        h.addFilter(secret_filter)
        root.addHandler(h)
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)


def build_worker(cfg):
    from app.ai.classifier import EmailClassifier, make_gemini_call
    from app.database.db import Database
    from app.gmail.actions import GmailActions
    from app.gmail.client import GmailClient
    from app.gmail.reader import GmailReader
    from app.notify import Notifier
    from app.worker import Worker

    db = Database(cfg.database_path)
    client = GmailClient(cfg.gmail_credentials_path, cfg.gmail_token_path)
    classifier = EmailClassifier(make_gemini_call(cfg.gemini_api_key, cfg.gemini_model), model=cfg.gemini_model,
                                 max_retries=cfg.llm_max_retries, base_delay=cfg.retry_base_delay)
    return Worker(cfg, db, classifier, Notifier(cfg.notify_webhook_url))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AI email automation")
    parser.add_argument("command", choices=["auth", "run", "once", "dashboard"])
    args = parser.parse_args(argv)

    try:
        cfg = load_config(require_gemini=args.command in ("run", "once"))
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    setup_logging(cfg)

    if args.command == "auth":
        from app.gmail.client import authorize
        authorize(cfg.gmail_credentials_path, cfg.gmail_token_path, cfg.google_redirect_uri)
        print(f"Authorized. Token saved to {cfg.gmail_token_path}")
        return 0
    if args.command == "dashboard":
        import uvicorn
        from app.web.api import create_app
        app = create_app(cfg)
        uvicorn.run(app, host=cfg.dashboard_host, port=cfg.dashboard_port)
        return 0

    worker = build_worker(cfg)
    if args.command == "once":
        print(f"Processed {worker.run_once()} email(s)")
        return 0
    signal.signal(signal.SIGINT, worker.stop)
    signal.signal(signal.SIGTERM, worker.stop)
    worker.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
