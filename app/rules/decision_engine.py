"""Turns a validated classification into a list of SAFE planned actions.

Pure function: no I/O, easy to test. The worker executes the plan.
Only reversible actions exist here: add AI-* labels, archive out of INBOX (quarantine), notify.
"""
from __future__ import annotations

from app.config import Config
from app.models import Classification, Decision, PlannedAction, RuleResult

CATEGORY_LABELS = {
    "urgent": "AI-URGENT", "important": "AI-IMPORTANT", "promotional": "AI-PROMOTIONAL",
    "spam": "AI-SPAM", "meeting": "AI-MEETING", "academic": "AI-ACADEMIC", "work": "AI-WORK",
}
REVIEW_LABEL = "AI-REVIEW"
SUSPICIOUS_LABEL = "AI-SUSPICIOUS"
QUARANTINE_LABEL = "AI-QUARANTINE"


def _review(rules: RuleResult, why: str) -> Decision:
    actions = [PlannedAction("add_label", REVIEW_LABEL)]
    if rules.suspicious:
        actions.append(PlannedAction("add_label", SUSPICIOUS_LABEL))
    return Decision(actions=actions, needs_review=True, summary=why)   # stays in INBOX, untouched otherwise


def decide(cls: Classification, rules: RuleResult, cfg: Config) -> Decision:
    conf = cls.confidence if cls.valid else 0.0

    if cls.category == "unknown":
        return _review(rules, "classification unknown")

    if conf < cfg.confidence_threshold:
        return _review(rules, f"confidence below threshold ({conf:.2f} < {cfg.confidence_threshold})")

    # --- confident (>= threshold) from here ---
    if cls.category == "spam":
        if cfg.spam_policy == "label":
            acts = [PlannedAction("add_label", CATEGORY_LABELS["spam"])]
        elif cfg.spam_policy == "spam":
            acts = [PlannedAction("add_label", CATEGORY_LABELS["spam"]), PlannedAction("add_label", "SPAM"),
                    PlannedAction("remove_inbox")]
        else:  # quarantine (default): reversible, never deleted
            acts = [PlannedAction("add_label", CATEGORY_LABELS["spam"]),
                    PlannedAction("add_label", QUARANTINE_LABEL), PlannedAction("remove_inbox")]
        return Decision(acts, False, f"spam handled by policy '{cfg.spam_policy}'")

    if rules.suspicious:
        # Looks malicious but the LLM labelled it as something legitimate: a human decides.
        return _review(rules, "suspicious indicators: " + ", ".join(rules.flags))

    labels: list = []
    label = CATEGORY_LABELS.get(cls.category)
    if label:
        labels.append(label)
    notify = False
    if cls.priority == "high":
        labels.append("AI-URGENT" if cls.category == "urgent" else "AI-IMPORTANT")
        notify = True
    labels = list(dict.fromkeys(labels))

    actions = [PlannedAction("add_label", n) for n in labels]
    if notify:
        actions.append(PlannedAction("notify"))
    if not actions:
        actions.append(PlannedAction("keep"))
    return Decision(actions, False, f"{cls.category}/{cls.priority} applied")
