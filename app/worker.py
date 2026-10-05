"""Background worker: discover -> fetch -> rules -> LLM -> decide -> act -> log."""
from __future__ import annotations

import logging
import time
from typing import Callable

from app.ai.classifier import ClassificationError, EmailClassifier
from app.config import Config
from app.database.db import Database, DatabaseError
from app.gmail.client import GmailAuthError, GmailError, GmailNotFound, GmailTransientError, GmailClient
from app.models import Classification, Email
from app.preprocess import build_llm_payload
from app.rules.decision_engine import decide
from app.rules.deterministic import analyze
from app.utils import retry_with_backoff, scrub_secrets
from app.gmail.reader import GmailReader
from app.gmail.actions import GmailActions

log = logging.getLogger(__name__)
HISTORY_KEY = "gmail_history_id_{user_id}"
STALE_SECONDS = 600
SKIP_LABELS = {"SENT", "DRAFT", "SPAM", "TRASH"}

class Worker:
    def __init__(self, cfg: Config, db: Database, classifier: EmailClassifier, notifier,
                 sleep: Callable[[float], None] = time.sleep,
                 reader_factory: Callable = None,
                 actions_factory: Callable = None):
        self.cfg, self.db = cfg, db
        self.classifier, self.notifier, self.sleep = classifier, notifier, sleep
        self._stop = False
        self.reader_factory = reader_factory or (lambda c, d, d_l, u_id: GmailReader(c, d, d_l, user_id=u_id))
        self.actions_factory = actions_factory or (lambda c, dry: GmailActions(c, dry_run=dry))

    def stop(self, *_args) -> None:
        self._stop = True

    def run_forever(self) -> None:
        log.info("Worker started (poll every %ss, dry_run=%s)", self.cfg.poll_interval, self.cfg.dry_run)
        while not self._stop:
            try:
                self.run_once()
            except Exception:
                log.exception("Unexpected error in worker cycle")
            for _ in range(int(self.cfg.poll_interval)):
                if self._stop:
                    break
                self.sleep(1)
        log.info("Worker stopped")

    def run_once(self) -> int:
        users = self.db.get_users()
        total_processed = 0
        for user in users:
            if self._stop:
                break
            try:
                total_processed += self.process_user(user)
            except Exception:
                log.exception(f"Unexpected error processing user {user['id']}")
        return total_processed

    def _gmail(self, fn, what):
        return retry_with_backoff(fn, is_transient=lambda e: isinstance(e, GmailTransientError),
                                  max_attempts=4, base_delay=self.cfg.retry_base_delay, sleep=self.sleep, what=what)

    def process_user(self, user: dict) -> int:
        user_id = user["id"]
        def on_refresh(new_token: str):
            self.db.upsert_user(user_id, user["email"], new_token)
            
        client = GmailClient(self.cfg.gmail_credentials_path, token_json_str=user["token_json"], on_token_refresh=on_refresh)
        reader = self.reader_factory(client, self.db, self.cfg.initial_lookback_days, user_id)
        actions = self.actions_factory(client, self.cfg.dry_run)
        
        # Discover
        try:
            stored_history_id = user.get("gmail_history_id")
            ids, history_id = self._gmail(lambda: reader.discover(stored_history_id), "Gmail discovery")
            new = sum(1 for mid in ids if self.db.register_message(mid, user_id))
            if history_id and history_id != stored_history_id:
                self.db.update_user_history(user_id, history_id)
            if new:
                log.info("Discovered %d new email(s) for user %s", new, user_id)
            self.db.update_user_sync(user_id, f"success_{new}")
        except GmailAuthError as exc:
            log.warning("Gmail auth error for user %s: %s", user_id, scrub_secrets(str(exc)))
            self.db.update_user_sync(user_id, "auth_error", str(exc))
            return 0
        except GmailError as exc:
            log.error("Gmail discovery failed for user %s: %s", user_id, scrub_secrets(str(exc)))
            self.db.update_user_sync(user_id, "error", str(exc))
            return 0

        # Process
        count = 0
        message_ids = self.db.retryable_ids_for_user(user_id, self.cfg.max_attempts, STALE_SECONDS)
        for message_id in message_ids:
            if self._stop:
                break
            try:
                if self.process_message(message_id, user_id, reader, actions):
                    count += 1
            except GmailAuthError:
                break
            except Exception:
                log.exception("Unexpected error on %s", message_id)
        return count

    def process_message(self, message_id: str, user_id: str, reader, actions) -> bool:
        attempts = self.db.claim(message_id, self.cfg.max_attempts, STALE_SECONDS)
        if attempts is None:
            return False
        final_attempt = attempts >= self.cfg.max_attempts
        self.db.log(message_id, "INFO", "claimed", f"attempt {attempts}")

        try:
            email = self._gmail(lambda: reader.fetch_email(message_id), "Gmail fetch")
        except GmailNotFound:
            self.db.set_status(message_id, "skipped", "message no longer exists")
            return False
        except GmailError as exc:
            self._fail(message_id, "fetch", exc, count=not isinstance(exc, (GmailTransientError, GmailAuthError)))
            if isinstance(exc, GmailAuthError):
                raise
            return False

        email.user_id = user_id
        self.db.save_email_metadata(message_id, email)
        if "INBOX" not in email.labels or SKIP_LABELS & set(email.labels):
            self.db.set_status(message_id, "skipped", "not an inbox message")
            self.db.log(message_id, "INFO", "skipped", "not in inbox or is sent/draft/spam/trash")
            return False

        rules = analyze(email)
        payload = build_llm_payload(email, rules, self.cfg.max_body_chars)
        try:
            cls = self.classifier.classify(payload)
        except ClassificationError as exc:
            if exc.transient or not final_attempt:
                self._fail(message_id, "classify", exc, count=not exc.transient)
                return False
            cls = Classification("unknown", "low", 0.0, "Classification unavailable; manual review needed",
                                 valid=False, error=str(exc))
        self.db.save_classification(message_id, cls, rules.flags)
        if not cls.valid:
            self.db.log(message_id, "WARNING", "llm_invalid", cls.error or "")

        decision = decide(cls, rules, self.cfg)
        try:
            self._execute(message_id, email, cls, decision, actions)
        except GmailError as exc:
            self._fail(message_id, "action", exc, count=not isinstance(exc, (GmailTransientError, GmailAuthError)))
            if isinstance(exc, GmailAuthError):
                raise
            return False

        status = "review" if decision.needs_review else "done"
        self.db.set_status(message_id, status)
        self.db.log(message_id, "INFO", "completed", f"{cls.category}/{cls.priority} conf={cls.confidence:.2f} -> {decision.summary}")
        return True

    def _execute(self, message_id: str, email: Email, cls: Classification, decision, actions) -> None:
        add = [a.value for a in decision.actions if a.kind == "add_label"]
        remove_inbox = any(a.kind == "remove_inbox" for a in decision.actions)
        suffix = " (dry-run)" if self.cfg.dry_run else ""

        if add or remove_inbox:
            self._gmail(lambda: actions.apply(message_id, add, remove_inbox), "Gmail label update")
            for label in add:
                self.db.record_action(message_id, "label", label + suffix)
            if remove_inbox:
                self.db.record_action(message_id, "archive_from_inbox", "INBOX removed" + suffix)
        elif any(a.kind == "keep" for a in decision.actions):
            self.db.record_action(message_id, "keep_in_inbox", suffix.strip())

        if any(a.kind == "notify" for a in decision.actions):
            ok, err = self.notifier.notify(email, cls)
            self.db.record_action(message_id, "notify", "", ok, err)

    def _fail(self, message_id: str, stage: str, exc: Exception, count: bool) -> None:
        msg = scrub_secrets(f"{stage}: {type(exc).__name__}: {exc}")
        try:
            self.db.set_status(message_id, "failed", msg)
            if not count:
                self.db.release_attempt(message_id)
            self.db.log(message_id, "ERROR", f"{stage}_failed", msg)
        except DatabaseError as db_exc:
            log.error("Could not record failure for %s: %s", message_id, db_exc)
