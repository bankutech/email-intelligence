"""Small shared helpers: time, retry with exponential backoff, secret scrubbing."""
from __future__ import annotations

import logging
import random
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

log = logging.getLogger(__name__)


def utcnow_iso(offset_seconds: float = 0) -> str:
    dt = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def retry_with_backoff(fn: Callable, *, is_transient: Callable[[Exception], bool],
                       max_attempts: int = 4, base_delay: float = 1.0, max_delay: float = 60.0,
                       sleep: Callable[[float], None] = time.sleep, what: str = "operation"):
    """Call fn(); retry only transient errors with exponential backoff + jitter."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - re-raised below if not retryable
            if attempt >= max_attempts or not is_transient(exc):
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, delay * 0.1)

            exc_str = str(exc)
            server_delay = None
            m = re.search(r"Please retry in (\d+(?:\.\d+)?)s", exc_str)
            if m:
                server_delay = float(m.group(1))
            else:
                m = re.search(r"'retryDelay':\s*'(\d+(?:\.\d+)?)s'", exc_str)
                if m:
                    server_delay = float(m.group(1))

            if server_delay is not None:
                if server_delay > max_delay:
                    log.warning("%s server requested delay %.1fs exceeds max_delay %.1fs (quota exhausted); aborting retry.",
                                what, server_delay, max_delay)
                    raise
                delay = min(max_delay, max(delay, server_delay + 1.0))
            else:
                delay = min(max_delay, delay)

            log.warning("%s failed (attempt %d/%d): %s - retrying in %.1fs",
                        what, attempt, max_attempts, scrub_secrets(exc_str), delay)
            sleep(delay)


_KEY_RE = re.compile(r"AIza[0-9A-Za-z_\-]{20,}")
_KV_RE = re.compile(r"(?i)((?:api[_-]?key|access_token|refresh_token|client_secret|authorization|bearer)[=:\s\"']+)[A-Za-z0-9_\-\.]{12,}")


def scrub_secrets(text: str, extra: Iterable[str] = ()) -> str:
    """Mask anything that looks like an API key/token before it is logged or stored."""
    for secret in extra:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = _KEY_RE.sub("[REDACTED]", text)
    return _KV_RE.sub(r"\1[REDACTED]", text)


class SecretFilter(logging.Filter):
    """Logging filter that scrubs secrets from every record."""

    def __init__(self, secrets: Iterable[str] = ()):
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub_secrets(record.getMessage(), self._secrets)
        record.args = ()
        return True


def _get_fernet(key: str):
    import base64
    import hashlib
    from cryptography.fernet import Fernet
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(digest)
    return Fernet(b64_key)


def encrypt_token(raw: str, secret_key: str) -> str:
    """Encrypt sensitive OAuth token JSON before storing in the database."""
    if not raw or not secret_key:
        return raw
    if raw.startswith("enc:"):
        return raw
    try:
        f = _get_fernet(secret_key)
        return "enc:" + f.encrypt(raw.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        log.error("Token encryption failed: %s", exc)
        return raw


def decrypt_token(stored: str, secret_key: str) -> str:
    """Decrypt token JSON read from the database; handles plaintext legacy tokens transparently."""
    if not stored or not secret_key:
        return stored
    if stored.startswith("enc:"):
        try:
            from cryptography.fernet import InvalidToken
            f = _get_fernet(secret_key)
            return f.decrypt(stored[4:].encode("utf-8")).decode("utf-8")
        except Exception as exc:
            log.error("Failed to decrypt stored token: %s", exc)
            return ""
    return stored

