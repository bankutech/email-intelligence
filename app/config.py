"""Configuration loaded from environment variables (.env supported). Nothing is hardcoded."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional at import time
    load_dotenv = None

SPAM_POLICIES = ("label", "quarantine", "spam")


class ConfigError(ValueError):
    pass


def _get_bool(env, name, default):
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_num(env, name, default, cast, lo, hi):
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        val = cast(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc
    if not (lo <= val <= hi):
        raise ConfigError(f"{name} must be between {lo} and {hi}, got {val}")
    return val


@dataclass(frozen=True)
class Config:
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"
    gemini_api_key: str = field(default="", repr=False)
    gemini_model: str = "gemini-2.5-flash"
    poll_interval: int = 60
    confidence_threshold: float = 0.85
    review_threshold: float = 0.60
    database_path: str = "data/emails.db"
    spam_policy: str = "quarantine"
    dry_run: bool = False
    max_attempts: int = 5
    initial_lookback_days: int = 1
    max_body_chars: int = 4000
    llm_max_retries: int = 3
    retry_base_delay: float = 1.0
    notify_webhook_url: str = field(default="", repr=False)
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 5000
    dashboard_show_subject: bool = True
    log_dir: str = "logs"
    log_level: str = "INFO"
    google_redirect_uri: str = "http://localhost:5000/auth/callback"


def load_config(env: Optional[Mapping[str, str]] = None, require_gemini: bool = True) -> Config:
    if env is None:
        if load_dotenv is not None:
            load_dotenv()
        env = os.environ

    def s(name, default):
        v = env.get(name)
        return v.strip() if v and v.strip() else default

    cfg = Config(
        gmail_credentials_path=s("GMAIL_CREDENTIALS_PATH", "credentials.json"),
        gmail_token_path=s("GMAIL_TOKEN_PATH", "token.json"),
        gemini_api_key=s("GEMINI_API_KEY", ""),
        gemini_model=s("GEMINI_MODEL", "gemini-2.5-flash"),
        poll_interval=_get_num(env, "POLL_INTERVAL", 60, int, 5, 86400),
        confidence_threshold=_get_num(env, "CONFIDENCE_THRESHOLD", 0.85, float, 0.0, 1.0),
        review_threshold=_get_num(env, "REVIEW_THRESHOLD", 0.60, float, 0.0, 1.0),
        database_path=s("DATABASE_PATH", "data/emails.db"),
        spam_policy=s("SPAM_POLICY", "quarantine").lower(),
        dry_run=_get_bool(env, "DRY_RUN", False),
        max_attempts=_get_num(env, "MAX_ATTEMPTS", 5, int, 1, 50),
        initial_lookback_days=_get_num(env, "INITIAL_LOOKBACK_DAYS", 1, int, 1, 30),
        max_body_chars=_get_num(env, "MAX_BODY_CHARS", 4000, int, 200, 50000),
        llm_max_retries=_get_num(env, "LLM_MAX_RETRIES", 3, int, 1, 10),
        retry_base_delay=_get_num(env, "RETRY_BASE_DELAY", 1.0, float, 0.0, 60.0),
        notify_webhook_url=s("NOTIFY_WEBHOOK_URL", ""),
        dashboard_host=s("DASHBOARD_HOST", "127.0.0.1"),
        dashboard_port=_get_num(env, "DASHBOARD_PORT", 5000, int, 1, 65535),
        dashboard_show_subject=_get_bool(env, "DASHBOARD_SHOW_SUBJECT", True),
        log_dir=s("LOG_DIR", "logs"),
        log_level=s("LOG_LEVEL", "INFO").upper(),
        google_redirect_uri=s("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/callback"),
    )
    if cfg.spam_policy not in SPAM_POLICIES:
        raise ConfigError(f"SPAM_POLICY must be one of {SPAM_POLICIES}, got {cfg.spam_policy!r}")
    if cfg.review_threshold > cfg.confidence_threshold:
        raise ConfigError("REVIEW_THRESHOLD must be <= CONFIDENCE_THRESHOLD")
    if require_gemini and not cfg.gemini_api_key:
        raise ConfigError("GEMINI_API_KEY is not set (put it in .env or the environment)")
    return cfg
