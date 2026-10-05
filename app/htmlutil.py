"""Strip HTML to plain text and collect links (stdlib only)."""
from __future__ import annotations

import re
from html.parser import HTMLParser

_SKIP = {"script", "style", "head", "title", "noscript"}
_BREAK = {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table", "blockquote"}
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list = []
        self.links: list = []
        self._skip_depth = 0
        self._href = None
        self._anchor_text: list = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip_depth += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._anchor_text = []
        if tag in _BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "a" and self._href:
            self.links.append({"url": self._href.strip(), "text": " ".join("".join(self._anchor_text).split())})
            self._href = None
        if tag in _BREAK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self.parts.append(data)
        if self._href is not None:
            self._anchor_text.append(data)


def html_to_text(html: str) -> tuple:
    """Return (plain_text, links). Links are [{'url','text'}]."""
    parser = _Extractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # malformed HTML must never crash processing
        pass
    return normalize_whitespace("".join(parser.parts)), parser.links


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def urls_in_text(text: str) -> list:
    return [{"url": u.rstrip(".,;"), "text": ""} for u in URL_RE.findall(text)]
