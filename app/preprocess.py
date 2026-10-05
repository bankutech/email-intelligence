"""Build the minimal, redacted payload that is sent to the LLM."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.htmlutil import normalize_whitespace
from app.models import Email, RuleResult

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
_CODE_RE = re.compile(r"(?i)\b(otp|one[- ]time|verification code|passcode|password|pin|cvv|code)\b([^\d\n]{0,20})(\d{4,8})\b")
_LONG_NUM_RE = re.compile(r"\b(?:\d[ -]?){12,19}\b")                 # cards, Aadhaar-like ids
_PHONE_RE = re.compile(r"(?<![\w.])\+?\d[\d\s().-]{8,}\d(?![\w])")
_DATE_LIKE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")


def _phone_sub(m: re.Match) -> str:
    text = m.group(0)
    if _DATE_LIKE.match(text) or len(re.sub(r"\D", "", text)) < 10:
        return text                      # keep dates / short numbers (meeting times, years)
    return "[PHONE]"


def _url_sub(m: re.Match) -> str:
    host = urlparse(m.group(0)).hostname or "unknown"
    return f"[link:{host}]"


def redact(text: str) -> str:
    """Remove personal data the classifier does not need (emails, phones, card numbers, codes, full URLs)."""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _URL_RE.sub(_url_sub, text)
    text = _CODE_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}[CODE]", text)
    text = _LONG_NUM_RE.sub("[NUMBER]", text)
    return _PHONE_RE.sub(_phone_sub, text)


def _clean_body(body: str, max_chars: int) -> str:
    lines = [ln for ln in body.splitlines() if not ln.lstrip().startswith(">")]   # drop quoted replies
    text = redact(normalize_whitespace("\n".join(lines)))
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + " ...[truncated]"
    return text


def link_domains(email: Email, limit: int = 10) -> list:
    hosts = []
    for link in email.links:
        host = (urlparse(link["url"]).hostname or "").lower()
        if host and host not in hosts:
            hosts.append(host)
    return hosts[:limit]


def build_llm_payload(email: Email, rules: RuleResult, max_chars: int) -> dict:
    sender_domain = email.sender_email.split("@")[-1] if "@" in email.sender_email else ""
    return {
        "from_name": redact(email.sender_name)[:80],
        "from_domain": sender_domain,
        "subject": redact(email.subject)[:300],
        "received": email.timestamp,
        "recipient_count": len(email.recipients),
        "attachments": [{"name": redact(a.get("name", ""))[:80], "type": a.get("mime_type", "")}
                        for a in email.attachments][:10],
        "link_domains": link_domains(email),
        "automated_checks": rules.flags + rules.hints,
        "body": _clean_body(email.body, max_chars),
    }
