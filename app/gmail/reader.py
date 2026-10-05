"""Detect new mail (history API + polling fallback) and parse messages into Email objects."""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

from app.gmail.client import GmailClient, GmailNotFound
from app.htmlutil import html_to_text, normalize_whitespace, urls_in_text
from app.models import Email

log = logging.getLogger(__name__)



# --------------------------------------------------------------------- parsing
def _decode(data: str) -> str:
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return raw.decode("utf-8", errors="replace")


def _walk(part: dict, plain: list, html: list, attachments: list) -> None:
    mime = (part.get("mimeType") or "").lower()
    body = part.get("body") or {}
    filename = part.get("filename") or ""
    if filename:
        attachments.append({"name": filename, "mime_type": mime, "size": int(body.get("size") or 0)})
    elif mime == "text/plain" and body.get("data"):
        plain.append(_decode(body["data"]))
    elif mime == "text/html" and body.get("data"):
        html.append(_decode(body["data"]))
    elif mime == "text/calendar":
        attachments.append({"name": "invite.ics", "mime_type": mime, "size": int(body.get("size") or 0)})
    for sub in part.get("parts") or []:
        _walk(sub, plain, html, attachments)


def parse_message(raw: dict) -> Email:
    """Convert a Gmail `format=full` message into an Email. Pure function (no network)."""
    payload = raw.get("payload") or {}
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", []) if "name" in h}

    plain, html, attachments = [], [], []
    _walk(payload, plain, html, attachments)

    links = []
    if html:
        text_from_html, html_links = html_to_text("\n".join(html))
        links.extend(html_links)
    else:
        text_from_html = ""
    plain_text = normalize_whitespace("\n".join(plain))
    body = plain_text or text_from_html
    if plain_text:
        links.extend(urls_in_text(plain_text))
    seen, unique_links = set(), []
    for link in links:
        key = (link["url"], link.get("text", ""))
        if link["url"].lower().startswith(("http://", "https://")) and key not in seen:
            seen.add(key)
            unique_links.append(link)

    name, addr = parseaddr(headers.get("from", ""))
    recipients = [a for _, a in getaddresses([headers.get("to", ""), headers.get("cc", "")]) if a]

    ts = ""
    if raw.get("internalDate"):
        ts = datetime.fromtimestamp(int(raw["internalDate"]) / 1000, tz=timezone.utc).isoformat()
    elif headers.get("date"):
        try:
            ts = parsedate_to_datetime(headers["date"]).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            ts = ""

    return Email(
        message_id=raw["id"], thread_id=raw.get("threadId", ""),
        sender=headers.get("from", ""), sender_name=name, sender_email=addr.lower(),
        recipients=recipients, subject=headers.get("subject", ""), body=body, timestamp=ts,
        labels=list(raw.get("labelIds", [])), attachments=attachments, links=unique_links,
        headers={
            "reply_to": parseaddr(headers.get("reply-to", ""))[1].lower(),
            "list_unsubscribe": headers.get("list-unsubscribe", ""),
            "auth_results": headers.get("authentication-results", ""),
            "precedence": headers.get("precedence", ""),
        },
    )


# ------------------------------------------------------------------- discovery
class GmailReader:
    def __init__(self, client: GmailClient, db, lookback_days: int = 1, user_id: str = ""):
        self.client = client
        self.db = db
        self.lookback_days = lookback_days
        self.user_id = user_id
        self._history_key = f"gmail_history_id_{user_id}" if user_id else "gmail_history_id"

    def discover(self) -> tuple:
        """Return (new_message_ids, newest_history_id).

        Uses the Gmail history API from the stored historyId. On first run (or if the stored id
        expired, which Gmail reports as 404) it falls back to listing recent inbox mail.
        """
        stored = self.db.get_state(self._history_key)
        if not stored:
            profile = self.client.call(lambda s: s.users().getProfile(userId="me"))
            return self._list_recent(), str(profile["historyId"])
        try:
            return self._history(stored)
        except GmailNotFound:
            log.warning("Stored historyId expired; falling back to a recent-mail scan")
            profile = self.client.call(lambda s: s.users().getProfile(userId="me"))
            return self._list_recent(), str(profile["historyId"])

    def _history(self, start_id: str) -> tuple:
        ids, newest, token = [], start_id, None
        while True:
            resp = self.client.call(lambda s: s.users().history().list(
                userId="me", startHistoryId=start_id, historyTypes=["messageAdded"],
                labelId="INBOX", pageToken=token))
            for rec in resp.get("history", []):
                for added in rec.get("messagesAdded", []):
                    msg = added.get("message", {})
                    labels = msg.get("labelIds")
                    if msg.get("id") and (labels is None or "INBOX" in labels):
                        ids.append(msg["id"])
            newest = str(resp.get("historyId", newest))
            token = resp.get("nextPageToken")
            if not token:
                break
        return list(dict.fromkeys(ids)), newest

    def _list_recent(self) -> list:
        ids, token = [], None
        query = f"in:inbox newer_than:{self.lookback_days}d"
        while len(ids) < 500:
            resp = self.client.call(lambda s: s.users().messages().list(
                userId="me", q=query, maxResults=100, pageToken=token))
            ids.extend(m["id"] for m in resp.get("messages", []))
            token = resp.get("nextPageToken")
            if not token:
                break
        return list(dict.fromkeys(ids))

    def fetch_email(self, message_id: str) -> Email:
        raw = self.client.call(lambda s: s.users().messages().get(userId="me", id=message_id, format="full"))
        return parse_message(raw)
