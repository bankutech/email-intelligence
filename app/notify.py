"""User notifications for high-priority mail. Sends only sender domain + subject, never the body."""
from __future__ import annotations

import json
import logging
import urllib.request

from app.models import Classification, Email
from app.preprocess import redact

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url

    def notify(self, email: Email, cls: Classification) -> tuple:
        """Return (success, error). Always logs; also POSTs to the webhook if configured."""
        domain = email.sender_email.split("@")[-1] if "@" in email.sender_email else "unknown"
        text = f"[{cls.priority.upper()}] {cls.category}: {redact(email.subject)[:120]} (from {domain})"
        log.warning("NOTIFY %s", text)
        if not self.webhook_url:
            return True, None
        try:
            data = json.dumps({"text": text, "content": text}).encode()
            req = urllib.request.Request(self.webhook_url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10):   # noqa: S310 - URL comes from trusted config
                pass
            return True, None
        except Exception as exc:  # noqa: BLE001 - a failed notification must not fail the email
            return False, f"webhook failed: {type(exc).__name__}"
