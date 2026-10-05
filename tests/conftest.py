import json
import os
import sys
from pathlib import Path

import pytest

os.environ["SESSION_SECRET_KEY"] = "super-secret-test-key-32-chars-long!"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.classifier import EmailClassifier
from app.config import Config
from app.database.db import Database
from app.models import Email
from app.worker import Worker


def make_email(mid="m1", subject="Hello", body="Hi there", sender="Alice <alice@example.com>", **kw) -> Email:
    name, addr = sender.split("<")[0].strip(), sender.split("<")[-1].rstrip(">")
    e = Email(message_id=mid, thread_id="t1", sender=sender, sender_name=name, sender_email=addr,
              recipients=["me@example.org"], subject=subject, body=body,
              timestamp="2026-10-03T08:00:00+00:00", labels=["INBOX", "UNREAD"])
    for k, v in kw.items():
        setattr(e, k, v)
    return e


def llm_json(category="normal", priority="low", confidence=0.95, reason="test"):
    return json.dumps({"category": category, "priority": priority, "confidence": confidence, "reason": reason})


class FakeReader:
    def __init__(self, emails=None):
        self.emails = {e.message_id: e for e in (emails or [])}
        self.fetch_failures = []          # exceptions raised (in order) before a fetch succeeds
        self.fetch_calls = 0

    def discover(self):
        return list(self.emails), "100"

    def fetch_email(self, mid):
        self.fetch_calls += 1
        if self.fetch_failures:
            raise self.fetch_failures.pop(0)
        return self.emails[mid]


class FakeActions:
    def __init__(self):
        self.calls = []                   # (message_id, labels, remove_inbox)
        self.failures = []

    def apply(self, mid, add_labels, remove_inbox=False):
        if self.failures:
            raise self.failures.pop(0)
        self.calls.append((mid, list(add_labels), remove_inbox))
        return True


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def notify(self, email, cls):
        self.sent.append((email.message_id, cls.category))
        return True, None


@pytest.fixture
def cfg():
    return Config(retry_base_delay=0.0, max_attempts=3, database_path=":memory:")


@pytest.fixture
def db():
    return Database(":memory:")


class Harness:
    def __init__(self, cfg, db, emails, llm_outputs):
        self.reader, self.actions, self.notifier = FakeReader(emails), FakeActions(), FakeNotifier()
        self.llm_outputs = list(llm_outputs)
        self.llm_calls = 0

        def llm(system, user):
            self.llm_calls += 1
            out = self.llm_outputs[0] if len(self.llm_outputs) == 1 else self.llm_outputs.pop(0)
            if isinstance(out, Exception):
                raise out
            return out

        self.classifier = EmailClassifier(llm, "test-model", max_retries=cfg.llm_max_retries, base_delay=0,
                                          sleep=lambda s: None)
        self.worker = Worker(cfg, db, self.classifier, self.notifier, sleep=lambda s: None,
                             reader_factory=lambda c, d, l, u: self.reader,
                             actions_factory=lambda c, d: self.actions)
        self.db = db
        self.db.upsert_user("u1", "test@test.com", "{}")


@pytest.fixture
def harness(cfg, db):
    def build(emails, llm_outputs):
        return Harness(cfg, db, emails, llm_outputs)
    return build
