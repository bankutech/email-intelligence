"""The 12 required scenarios, run end-to-end through Worker with fake Gmail/LLM."""
from app.gmail.client import GmailTransientError, GmailError
from tests.conftest import llm_json, make_email


def run(h):
    h.worker.run_once()
    return h


# 1 -------------------------------------------------------------------
def test_urgent_interview_email(harness):
    e = make_email(subject="Interview today at 3 PM", body="Please confirm your interview slot today at 3 PM.")
    h = run(harness([e], [llm_json("urgent", "high", 0.96, "Interview scheduled today")]))
    assert h.actions.calls == [("m1", ["AI-URGENT"], False)]
    assert h.notifier.sent == [("m1", "urgent")]
    assert h.db.get_status("m1") == "done"


# 2 -------------------------------------------------------------------
def test_assignment_deadline_email(harness):
    e = make_email(subject="Assignment 3 due tomorrow", body="Submit on the portal before 11:59 PM.")
    h = run(harness([e], [llm_json("academic", "high", 0.92)]))
    assert h.actions.calls == [("m1", ["AI-ACADEMIC", "AI-IMPORTANT"], False)]
    assert len(h.notifier.sent) == 1


# 3 -------------------------------------------------------------------
def test_normal_personal_email_stays_untouched(harness):
    h = run(harness([make_email(body="Lunch on Sunday?")], [llm_json("normal", "low", 0.9)]))
    assert h.actions.calls == []                      # no label, not moved
    assert h.notifier.sent == []
    assert h.db.get_status("m1") == "done"
    assert h.db._run("SELECT action FROM actions", (), "all")[0]["action"] == "keep_in_inbox"


# 4 -------------------------------------------------------------------
def test_promotional_email_gets_label_only(harness):
    e = make_email(subject="50% off sale", body="Huge discounts", headers={"list_unsubscribe": "<mailto:x@y.z>"})
    h = run(harness([e], [llm_json("promotional", "low", 0.97)]))
    assert h.actions.calls == [("m1", ["AI-PROMOTIONAL"], False)]


# 5 -------------------------------------------------------------------
def test_obvious_spam_is_quarantined_not_deleted(harness):
    e = make_email(subject="You won a lottery!!!", body="Claim your prize now")
    h = run(harness([e], [llm_json("spam", "low", 0.98)]))
    assert h.actions.calls == [("m1", ["AI-SPAM", "AI-QUARANTINE"], True)]
    assert h.db.get_status("m1") == "done"


def test_spam_policy_variants(cfg, db):
    from dataclasses import replace
    from app.models import Classification, RuleResult
    from app.rules.decision_engine import decide
    spam = Classification("spam", "low", 0.99, "x")
    labels = lambda d: [a.value for a in d.actions if a.kind == "add_label"]
    d = decide(spam, RuleResult(), replace(cfg, spam_policy="label"))
    assert labels(d) == ["AI-SPAM"] and not any(a.kind == "remove_inbox" for a in d.actions)
    d = decide(spam, RuleResult(), replace(cfg, spam_policy="spam"))
    assert "SPAM" in labels(d) and any(a.kind == "remove_inbox" for a in d.actions)


# 6 -------------------------------------------------------------------
PHISH = dict(
    subject="Verify your account now", body="Your account will be suspended. Verify your account at the link.",
    sender="Support <help@paypa1-secure.com>",
    links=[{"url": "http://203.0.113.9/login", "text": "www.paypal.com"}],
    headers={"auth_results": "mx.google.com; spf=fail; dkim=fail; dmarc=fail", "reply_to": "", "list_unsubscribe": "", "precedence": ""},
)


def test_phishing_disguised_as_urgent_goes_to_manual_review(harness):
    h = run(harness([make_email(**PHISH)], [llm_json("urgent", "high", 0.95, "Account problem")]))
    assert h.actions.calls == [("m1", ["AI-REVIEW", "AI-SUSPICIOUS"], False)]   # stays in inbox
    assert h.notifier.sent == []                                                # no urgent ping
    assert h.db.get_status("m1") == "review"


def test_possible_phishing_with_medium_confidence_is_not_removed(harness):
    h = run(harness([make_email(**PHISH)], [llm_json("spam", "medium", 0.72)]))
    assert h.actions.calls == [("m1", ["AI-REVIEW", "AI-SUSPICIOUS"], False)]


# 7 -------------------------------------------------------------------
def test_meeting_invitation(harness):
    e = make_email(subject="Sync on 2026-10-05 14:00", body="Invite for Monday 2026-10-05 14:00 on Meet.")
    h = run(harness([e], [llm_json("meeting", "medium", 0.9)]))
    assert h.actions.calls == [("m1", ["AI-MEETING"], False)]


# 8 -------------------------------------------------------------------
def test_work_request(harness):
    h = run(harness([make_email(subject="Please review the Q3 report")], [llm_json("work", "medium", 0.88)]))
    assert h.actions.calls == [("m1", ["AI-WORK"], False)]
    assert h.notifier.sent == []


# 9 -------------------------------------------------------------------
def test_low_and_medium_confidence_only_get_review_label(harness):
    h = harness([make_email(mid="low"), make_email(mid="mid")], [llm_json("spam", "high", 0.45), llm_json("spam", "high", 0.75)])
    h.worker.run_once()
    assert h.actions.calls == [("low", ["AI-REVIEW"], False), ("mid", ["AI-REVIEW"], False)]
    assert h.notifier.sent == []                      # no notification, no move, no delete
    assert h.db.get_status("low") == h.db.get_status("mid") == "review"


def test_confidence_threshold_boundaries():
    from app.config import Config
    from app.models import Classification, RuleResult
    from app.rules.decision_engine import decide
    cfg = Config()
    acts = lambda c: [a.value for a in decide(Classification("spam", "low", c, ""), RuleResult(), cfg).actions]
    assert acts(0.5999) == ["AI-REVIEW"] and acts(0.60) == ["AI-REVIEW"] and acts(0.8499) == ["AI-REVIEW"]
    assert "AI-QUARANTINE" in acts(0.85)


# 10 ------------------------------------------------------------------
def test_invalid_json_from_llm_is_handled_safely(harness):
    h = run(harness([make_email()], ["Sure! The category is urgent."]))
    assert h.llm_calls == 3                                    # retried LLM_MAX_RETRIES times
    assert h.actions.calls == [("m1", ["AI-REVIEW"], False)]
    row = h.db._run("SELECT * FROM classifications", (), "all")[0]
    assert row["llm_valid"] == 0 and row["confidence"] == 0.0 and "invalid" in row["error_message"]
    assert h.db.get_status("m1") == "review"


def test_llm_output_validation_rules():
    import pytest
    from app.ai.classifier import InvalidLLMOutput, validate_llm_output
    ok = validate_llm_output("```json\n" + llm_json("work", "medium", 0.8) + "\n```")
    assert ok.category == "work"
    for bad in ["", "[]", '{"category":"x"}', llm_json("banana"), llm_json("work", "urgent"),
                llm_json("work", "low", 1.5), llm_json("work", "low", -0.1),
                '{"category":"work","priority":"low","confidence":true,"reason":"r"}',
                '{"category":"work","priority":"low","confidence":"0.9","reason":"r"}',
                '{"category":"work","priority":"low","confidence":NaN,"reason":"r"}']:
        with pytest.raises(InvalidLLMOutput):
            validate_llm_output(bad)


# 11 ------------------------------------------------------------------
def test_gmail_temporary_failure_is_retried_with_backoff(harness):
    h = harness([make_email()], [llm_json("work", "medium", 0.9)])
    h.actions.failures = [GmailTransientError("429"), GmailTransientError("503")]
    h.worker.run_once()
    assert h.actions.calls == [("m1", ["AI-WORK"], False)]
    assert h.db.get_status("m1") == "done"


def test_gmail_outage_never_loses_the_email_and_recovers(harness):
    h = harness([make_email()], [llm_json("work", "medium", 0.9)])
    h.actions.failures = [GmailTransientError("503")] * 10          # outage longer than one cycle
    h.worker.run_once()
    assert h.db.get_status("m1") == "failed" and h.actions.calls == []
    assert h.db.get_email_row("m1")["attempts"] == 0                # outage not counted against the email
    h.actions.failures = []                                         # Gmail is back
    h.worker.run_once()
    assert h.db.get_status("m1") == "done" and len(h.actions.calls) == 1


def test_permanent_gmail_error_stops_after_max_attempts(harness):
    h = harness([make_email()], [llm_json("work", "medium", 0.9)])
    h.actions.failures = [GmailError("403 forbidden", 403)] * 10
    for _ in range(5):
        h.worker.run_once()
    row = h.db.get_email_row("m1")
    assert row["processing_status"] == "failed" and row["attempts"] == 3 and "forbidden" in row["error_message"]


def test_llm_outage_is_retried_later_without_losing_email(harness):
    h = harness([make_email()], [ConnectionError("down")] * 20 + [llm_json("work", "medium", 0.9)])
    h.worker.run_once()
    assert h.db.get_status("m1") == "failed" and h.actions.calls == []
    h.llm_outputs = [llm_json("work", "medium", 0.9)]
    h.worker.run_once()
    assert h.db.get_status("m1") == "done"


# 12 ------------------------------------------------------------------
def test_duplicate_email_is_processed_once(harness):
    h = harness([make_email()], [llm_json("work", "medium", 0.9)])
    h.worker.run_once()
    h.worker.run_once()                       # Gmail re-reports the same id
    assert h.worker.process_message("m1", "u1", h.reader, h.actions) is False
    assert h.llm_calls == 1 and len(h.actions.calls) == 1
    assert h.db.register_message("m1", "u1") is False
    assert h.db._run("SELECT COUNT(*) FROM emails", (), "one")[0] == 1
