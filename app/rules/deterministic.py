"""Fast, explainable checks that run BEFORE the LLM. They never call the network or open links."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.models import Email, RuleResult

RISKY_EXT = {".exe", ".scr", ".bat", ".cmd", ".com", ".js", ".jse", ".vbs", ".vbe", ".wsf", ".jar", ".msi",
             ".ps1", ".lnk", ".iso", ".img", ".hta", ".dll", ".apk", ".docm", ".xlsm", ".pptm", ".html", ".htm"}
ARCHIVE_EXT = {".zip", ".rar", ".7z"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly", "cutt.ly"}
SECOND_LEVEL = {"co", "com", "org", "net", "ac", "gov", "edu"}

_AUTH_FAIL = re.compile(r"\b(spf|dkim|dmarc)=(fail|permerror)\b", re.I)
_IP_HOST = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_DOMAIN_IN_TEXT = re.compile(r"\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.I)
_SENSITIVE = re.compile(
    r"(verify|confirm|validate|update)\s+(your\s+)?(account|password|identity|payment|billing|card)"
    r"|(enter|send|share|provide)\s+(me\s+|us\s+)?(your\s+|the\s+)?(password|otp|pin|cvv|credentials)"
    r"|account\s+(will\s+be\s+|has\s+been\s+)?(suspended|locked|closed|limited)"
    r"|gift\s*cards?|wire\s+transfer|bank\s+details", re.I)

STRONG = {"auth_fail", "link_text_mismatch", "ip_link", "punycode_link", "risky_attachment", "sensitive_request_with_link"}


def registered_domain(host: str) -> str:
    parts = [p for p in (host or "").lower().strip(".").split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    if len(parts[-1]) == 2 and parts[-2] in SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def analyze(email: Email) -> RuleResult:
    flags, hints = [], []
    h = email.headers or {}

    if _AUTH_FAIL.search(h.get("auth_results", "")):
        flags.append("auth_fail")

    from_dom = registered_domain(email.sender_email.split("@")[-1]) if "@" in email.sender_email else ""
    reply_to = h.get("reply_to", "")
    if reply_to and "@" in reply_to and from_dom and registered_domain(reply_to.split("@")[-1]) != from_dom:
        flags.append("reply_to_mismatch")

    for link in email.links:
        host = (urlparse(link["url"]).hostname or "").lower()
        if _IP_HOST.match(host):
            flags.append("ip_link")
        if "xn--" in host:
            flags.append("punycode_link")
        if host in SHORTENERS:
            flags.append("shortened_link")
        shown = _DOMAIN_IN_TEXT.search(link.get("text", "") or "")
        if shown and host and registered_domain(shown.group(1)) != registered_domain(host):
            flags.append("link_text_mismatch")

    for att in email.attachments:
        name = (att.get("name") or "").lower()
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        if ext in RISKY_EXT:
            flags.append("risky_attachment")
        elif ext in ARCHIVE_EXT:
            flags.append("archive_attachment")
        if att.get("mime_type") == "text/calendar" or ext == ".ics":
            hints.append("calendar_invite_attached")

    if _SENSITIVE.search(f"{email.subject}\n{email.body}"):
        flags.append("sensitive_request_with_link" if email.links else "sensitive_request")

    if h.get("list_unsubscribe") or (h.get("precedence", "").lower() in ("bulk", "list")):
        hints.append("bulk_mailing_list")

    flags = list(dict.fromkeys(flags))
    hints = list(dict.fromkeys(hints))
    weak = [f for f in flags if f not in STRONG]
    suspicious = any(f in STRONG for f in flags) or len(weak) >= 2
    return RuleResult(flags=flags, hints=hints, suspicious=suspicious)
