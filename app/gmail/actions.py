"""The ONLY place that changes Gmail state. Deliberately tiny and allow-listed.

Allowed:  add labels named AI-* (or the system SPAM label), remove the INBOX label.
Never:    trash, delete, send, reply, forward, open links, download attachments.
"""
from __future__ import annotations

import logging

from app.gmail.client import GmailClient, GmailError

log = logging.getLogger(__name__)

ALLOWED_PREFIX = "AI-"
ALLOWED_SYSTEM_ADD = {"SPAM"}
ALLOWED_REMOVE = {"INBOX"}


def _check_label(name: str) -> None:
    if not (name.startswith(ALLOWED_PREFIX) or name in ALLOWED_SYSTEM_ADD):
        raise ValueError(f"label {name!r} is not allowed (only AI-* and SPAM)")


class GmailActions:
    def __init__(self, client: GmailClient, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run
        self._label_ids: dict = {}

    def _load_labels(self) -> None:
        resp = self.client.call(lambda s: s.users().labels().list(userId="me"))
        self._label_ids = {lbl["name"]: lbl["id"] for lbl in resp.get("labels", [])}

    def ensure_label(self, name: str) -> str:
        _check_label(name)
        if name in ALLOWED_SYSTEM_ADD:
            return name
        if name not in self._label_ids:
            self._load_labels()
        if name not in self._label_ids:
            body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
            try:
                created = self.client.call(lambda s: s.users().labels().create(userId="me", body=body))
                self._label_ids[name] = created["id"]
            except GmailError as exc:
                if exc.status != 409:          # 409 = created concurrently; reload below
                    raise
                self._load_labels()
        return self._label_ids[name]

    def apply(self, message_id: str, add_labels: list, remove_inbox: bool = False) -> bool:
        """Add AI-* labels and optionally archive out of INBOX. Returns False in dry-run."""
        for name in add_labels:
            _check_label(name)
        if self.dry_run:
            log.info("[dry-run] %s: +%s %s", message_id, add_labels, "-INBOX" if remove_inbox else "")
            return False
        add_ids = [self.ensure_label(n) for n in add_labels]
        remove_ids = ["INBOX"] if remove_inbox else []
        body = {"addLabelIds": add_ids, "removeLabelIds": remove_ids}
        self.client.call(lambda s: s.users().messages().modify(userId="me", id=message_id, body=body))
        return True
