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
            m = re.search(r"Please retry in (\d+(?:\.\d+)?)s", exc_str)
            if m:
                server_delay = float(m.group(1))
                delay = max(delay, server_delay + 1.0)
            else:
                m = re.search(r"'retryDelay':\s*'(\d+(?:\.\d+)?)s'", exc_str)
                if m:
                    server_delay = float(m.group(1))
                    delay = max(delay, server_delay + 1.0)
                    
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
