"""LLM classification with strict output validation.

The LLM returns text; this module turns it into a validated Classification or a safe
low-confidence fallback. The LLM can never trigger a Gmail action.
"""
from __future__ import annotations

import json
import logging
import math
import re
import time
from typing import Callable

from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models import CATEGORIES, PRIORITIES, Classification
from app.utils import retry_with_backoff, scrub_secrets

log = logging.getLogger(__name__)
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S | re.I)
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")


class InvalidLLMOutput(ValueError):
    pass


class ClassificationError(Exception):
    """The LLM could not be reached / refused. `transient` = worth retrying later without penalty."""

    def __init__(self, message: str, transient: bool):
        super().__init__(message)
        self.transient = transient


def validate_llm_output(text: str, model: str = "") -> Classification:
    """Strictly validate the LLM response. Raises InvalidLLMOutput on any deviation."""
    if not isinstance(text, str) or not text.strip():
        raise InvalidLLMOutput("empty response")
    cleaned = text.strip()
    fenced = _FENCE_RE.match(cleaned)
    if fenced:
        cleaned = fenced.group(1)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise InvalidLLMOutput(f"not valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise InvalidLLMOutput("JSON root is not an object")
    missing = {"category", "priority", "confidence", "reason"} - data.keys()
    if missing:
        raise InvalidLLMOutput(f"missing keys: {sorted(missing)}")

    category, priority = data["category"], data["priority"]
    if not isinstance(category, str) or category.strip().lower() not in CATEGORIES:
        raise InvalidLLMOutput(f"invalid category: {str(category)[:40]!r}")
    if not isinstance(priority, str) or priority.strip().lower() not in PRIORITIES:
        raise InvalidLLMOutput(f"invalid priority: {str(priority)[:40]!r}")
    conf = data["confidence"]
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not math.isfinite(conf) or not 0.0 <= conf <= 1.0:
        raise InvalidLLMOutput(f"invalid confidence: {str(conf)[:40]!r}")
    reason = data["reason"]
    if not isinstance(reason, str):
        raise InvalidLLMOutput("reason must be a string")
    reason = _CTRL_RE.sub(" ", reason).strip()[:300]

    return Classification(category=category.strip().lower(), priority=priority.strip().lower(),
                          confidence=round(float(conf), 4), reason=reason, valid=True, model=model)


def _is_transient(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int):
        if code in (400, 401, 403):
            return False  # Fatal configuration/permission error
        return code in (408, 429, 500, 502, 503, 504)
    return isinstance(exc, (TimeoutError, ConnectionError))


def make_gemini_call(api_key: str, model: str) -> Callable[[str, str], str]:
    """Return a function (system_prompt, user_prompt) -> raw text using the Gemini API."""
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field

    class EmailSchema(BaseModel):
        category: str = Field(description="urgent | important | normal | promotional | spam | meeting | academic | work")
        priority: str = Field(description="high | medium | low")
        confidence: float = Field(description="Float between 0.0 and 1.0")
        reason: str = Field(description="Short reason for classification")

    client = genai.Client(api_key=api_key)

    def call(system_prompt: str, user_prompt: str) -> str:
        resp = client.models.generate_content(
            model=model, contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, 
                response_mime_type="application/json",
                response_schema=EmailSchema,
                automatic_function_calling={"disable": True},
                temperature=0.0, max_output_tokens=1024))
        return resp.text or ""

    return call


class EmailClassifier:
    def __init__(self, llm_call: Callable[[str, str], str], model: str = "", max_retries: int = 3,
                 base_delay: float = 1.0, sleep: Callable[[float], None] = time.sleep):
        self.llm_call = llm_call
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.sleep = sleep

    def classify(self, payload: dict) -> Classification:
        user_prompt = build_user_prompt(payload)
        last_error = "unknown"
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = retry_with_backoff(
                    lambda: self.llm_call(SYSTEM_PROMPT, user_prompt), is_transient=_is_transient,
                    max_attempts=self.max_retries, base_delay=self.base_delay, sleep=self.sleep, what="LLM call")
            except Exception as exc:  # noqa: BLE001
                raise ClassificationError(scrub_secrets(f"{type(exc).__name__}: {exc}"), _is_transient(exc)) from exc
            try:
                return validate_llm_output(raw, self.model)
            except InvalidLLMOutput as exc:
                last_error = str(exc)
                log.warning("LLM output rejected (try %d/%d): %s", attempt, self.max_retries, last_error)
                if attempt < self.max_retries:
                    self.sleep(self.base_delay * (2 ** (attempt - 1)))
        # Never guess: confidence 0 forces the decision engine to AI-REVIEW.
        return Classification("unknown", "unknown", 0.0, "LLM_OUTPUT_INVALID",
                              valid=False, error=f"invalid LLM output: {last_error}", model=self.model)
