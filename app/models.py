"""Plain data objects shared across modules."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, Field

CATEGORIES = ("urgent", "important", "normal", "promotional", "spam", "meeting", "academic", "work", "unknown")
PRIORITIES = ("high", "medium", "low", "unknown")


@dataclass
class Email:
    message_id: str
    user_id: str = ""
    thread_id: str = ""
    sender: str = ""
    sender_name: str = ""
    sender_email: str = ""
    recipients: list = field(default_factory=list)
    subject: str = ""
    body: str = ""                      # HTML already stripped
    timestamp: str = ""                 # ISO-8601 UTC
    labels: list = field(default_factory=list)
    attachments: list = field(default_factory=list)   # {"name","mime_type","size"}
    links: list = field(default_factory=list)         # {"url","text"}
    headers: dict = field(default_factory=dict)       # small subset used by rules

class AIClassificationResponse(BaseModel):
    category: str = Field(description="The predicted category of the email")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reason: str = Field(description="Detailed reason for the classification")
    priority: str = Field(default="normal", description="high, medium, or low priority")


@dataclass
class Classification:
    category: str
    priority: str
    confidence: float
    reason: str
    valid: bool = True                  # False = LLM output was unusable (fallback)
    error: Optional[str] = None
    model: str = ""


@dataclass
class RuleResult:
    flags: list = field(default_factory=list)
    hints: list = field(default_factory=list)
    suspicious: bool = False


@dataclass
class PlannedAction:
    kind: str                           # add_label | remove_inbox | notify | keep
    value: str = ""


@dataclass
class Decision:
    actions: list = field(default_factory=list)
    needs_review: bool = False
    summary: str = ""
