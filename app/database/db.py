"""SQLite storage: emails, classifications, actions, processing_logs (+ small state table).

Design notes
- Gmail keeps the original email. The DB only stores metadata (no body text).
- `emails.processing_status` is the de-duplication gate: a message is claimed atomically
  (pending/failed -> processing) so it can never be processed twice.
- DB errors raise DatabaseError; callers leave the email untouched in Gmail, and the
  row is picked up again on the next cycle (stale 'processing' rows are reclaimed).
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from app.models import Classification, Email
from app.utils import scrub_secrets, utcnow_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    token_json    TEXT NOT NULL,
    settings      TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS emails (
    message_id        TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    thread_id         TEXT,
    sender            TEXT,
    recipients        TEXT,
    subject           TEXT,
    email_timestamp   TEXT,
    labels            TEXT,
    attachments       TEXT,
    processing_status TEXT NOT NULL DEFAULT 'pending',
    attempts          INTEGER NOT NULL DEFAULT 0,
    error_message     TEXT,
    first_seen_at     TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS classifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id    TEXT NOT NULL REFERENCES emails(message_id),
    timestamp     TEXT NOT NULL,
    category      TEXT NOT NULL,
    priority      TEXT NOT NULL,
    confidence    REAL NOT NULL,
    reason        TEXT,
    model         TEXT,
    rule_flags    TEXT,
    llm_valid     INTEGER NOT NULL DEFAULT 1,
    error_message TEXT
);
CREATE TABLE IF NOT EXISTS actions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id    TEXT NOT NULL REFERENCES emails(message_id),
    timestamp     TEXT NOT NULL,
    action        TEXT NOT NULL,
    detail        TEXT NOT NULL DEFAULT '',
    success       INTEGER NOT NULL,
    error_message TEXT
);
CREATE TABLE IF NOT EXISTS processing_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    timestamp  TEXT NOT NULL,
    level      TEXT NOT NULL,
    event      TEXT NOT NULL,
    detail     TEXT
);
CREATE TABLE IF NOT EXISTS state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(processing_status, attempts);
CREATE INDEX IF NOT EXISTS idx_emails_user ON emails(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_class_msg ON classifications(message_id);
CREATE INDEX IF NOT EXISTS idx_actions_msg ON actions(message_id);
CREATE INDEX IF NOT EXISTS idx_logs_msg ON processing_logs(message_id);
"""

PROCESSED_STATUSES = ("done", "review")


class DatabaseError(Exception):
    pass


class Database:
    def __init__(self, path: str, read_only: bool = False):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        try:
            self._conn = sqlite3.connect(path, timeout=30, check_same_thread=False, isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            if not read_only:
                self._conn.executescript(SCHEMA)
            else:
                self._conn.execute("PRAGMA query_only=ON")
        except sqlite3.Error as exc:
            raise DatabaseError(f"cannot open database {path}: {exc}") from exc

    # ---------------------------------------------------------------- internals
    def _run(self, sql: str, params=(), fetch: str = "none"):
        last: Optional[Exception] = None
        for attempt in range(4):
            try:
                with self._lock:
                    cur = self._conn.execute(sql, params)
                    if fetch == "all":
                        return cur.fetchall()
                    if fetch == "one":
                        return cur.fetchone()
                    return cur
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if "locked" in msg or "busy" in msg:
                    last = exc
                    time.sleep(0.2 * (2 ** attempt))
                    continue
                raise DatabaseError(str(exc)) from exc
            except sqlite3.Error as exc:
                raise DatabaseError(str(exc)) from exc
        raise DatabaseError(f"database stayed locked: {last}")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    
    # ------------------------------------------------------------------- users
    def get_users(self) -> list:
        rows = self._run("SELECT * FROM users", (), "all")
        return [dict(r) for r in rows]

    def get_user(self, user_id: str):
        return self._run("SELECT * FROM users WHERE id=?", (user_id,), "one")

    def upsert_user(self, user_id: str, email: str, token_json: str):
        now = utcnow_iso()
        self._run(
            "INSERT INTO users(id, email, token_json, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET email=excluded.email, token_json=excluded.token_json",
            (user_id, email, token_json, now)
        )
        
    def update_user_settings(self, user_id: str, settings: str):
        self._run("UPDATE users SET settings=? WHERE id=?", (settings, user_id))


    # ------------------------------------------------------------ email lifecycle
    def register_message(self, message_id: str, user_id: str) -> bool:
        """Remember a newly discovered message. Returns False if we already know it."""
        now = utcnow_iso()
        cur = self._run(
            "INSERT OR IGNORE INTO emails(message_id, user_id, processing_status, first_seen_at, updated_at) "
            "VALUES(?, ?, 'pending', ?, ?)", (message_id, user_id, now, now))
        return cur.rowcount == 1

    def claim(self, message_id: str, max_attempts: int, stale_seconds: int = 600) -> Optional[int]:
        """Atomically move pending/failed -> processing. None = not claimable (duplicate)."""
        cur = self._run(
            "UPDATE emails SET processing_status='processing', attempts=attempts+1, updated_at=? "
            "WHERE message_id=? AND ((processing_status IN ('pending','failed') AND attempts < ?) "
            "OR (processing_status='processing' AND updated_at < ?))",
            (utcnow_iso(), message_id, max_attempts, utcnow_iso(-stale_seconds)))
        if cur.rowcount != 1:
            return None
        row = self._run("SELECT attempts FROM emails WHERE message_id=?", (message_id,), "one")
        return int(row["attempts"])

    def retryable_ids_for_user(self, user_id: str, max_attempts: int, stale_seconds: int = 600, limit: int = 50) -> list:
        rows = self._run(
            "SELECT message_id FROM emails WHERE user_id=? AND ("
            "(processing_status IN ('pending','failed') AND attempts < ?) "
            "OR (processing_status='processing' AND updated_at < ?)) "
            "ORDER BY first_seen_at LIMIT ?",
            (user_id, max_attempts, utcnow_iso(-stale_seconds), limit), "all")
        return [r["message_id"] for r in rows]

    def release_attempt(self, message_id: str) -> None:
        """Do not count temporary outages (rate limit, network, auth) against an email."""
        self._run("UPDATE emails SET attempts = MAX(attempts-1, 0) WHERE message_id=?", (message_id,))

    def set_status(self, message_id: str, status: str, error: Optional[str] = None) -> None:
        self._run("UPDATE emails SET processing_status=?, error_message=?, updated_at=? WHERE message_id=?",
                  (status, scrub_secrets(error) if error else None, utcnow_iso(), message_id))

    def get_status(self, message_id: str) -> Optional[str]:
        row = self._run("SELECT processing_status FROM emails WHERE message_id=?", (message_id,), "one")
        return row["processing_status"] if row else None

    def get_email_row(self, message_id: str):
        return self._run("SELECT * FROM emails WHERE message_id=?", (message_id,), "one")

    def save_email_metadata(self, message_id: str, email: Email) -> None:
        self._run(
            "UPDATE emails SET thread_id=?, sender=?, recipients=?, subject=?, email_timestamp=?, "
            "labels=?, attachments=?, updated_at=? WHERE message_id=?",
            (email.thread_id, email.sender_email or email.sender, json.dumps(email.recipients),
             email.subject, email.timestamp, json.dumps(email.labels),
             json.dumps([{"name": a.get("name"), "type": a.get("mime_type")} for a in email.attachments]),
             utcnow_iso(), message_id))

    # ------------------------------------------------------- results and logging
    def save_classification(self, message_id: str, cls: Classification, flags: list) -> int:
        cur = self._run(
            "INSERT INTO classifications(message_id, timestamp, category, priority, confidence, reason, "
            "model, rule_flags, llm_valid, error_message) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (message_id, utcnow_iso(), cls.category, cls.priority, cls.confidence, cls.reason,
             cls.model, json.dumps(flags), 1 if cls.valid else 0,
             scrub_secrets(cls.error) if cls.error else None))
        return int(cur.lastrowid)

    def record_action(self, message_id: str, action: str, detail: str = "", success: bool = True,
                      error: Optional[str] = None) -> None:
        self._run("INSERT INTO actions(message_id, timestamp, action, detail, success, error_message) "
                  "VALUES(?,?,?,?,?,?)",
                  (message_id, utcnow_iso(), action, detail, 1 if success else 0,
                   scrub_secrets(error) if error else None))

    def log(self, message_id: Optional[str], level: str, event: str, detail: str = "") -> None:
        self._run("INSERT INTO processing_logs(message_id, timestamp, level, event, detail) VALUES(?,?,?,?,?)",
                  (message_id, utcnow_iso(), level, event, scrub_secrets(detail)))

    # ------------------------------------------------------------------- state
    def get_state(self, key: str) -> Optional[str]:
        row = self._run("SELECT value FROM state WHERE key=?", (key,), "one")
        return row["value"] if row else None

    def set_state(self, key: str, value: str) -> None:
        self._run("INSERT INTO state(key, value) VALUES(?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    # --------------------------------------------------------------- reporting
    def stats(self, user_id: str = None) -> dict:
        def one(sql, params=()):
            return self._run(sql, params, "one")[0]

        cond = "WHERE e.user_id = ?" if user_id else ""
        params = (user_id,) if user_id else ()

        latest = f"SELECT c.* FROM classifications c JOIN (SELECT c2.message_id, MAX(c2.id) AS mid FROM classifications c2 JOIN emails e ON e.message_id = c2.message_id {cond} GROUP BY c2.message_id) l ON c.id = l.mid"
        
        cats = {r["category"]: r["n"] for r in self._run(
            f"SELECT category, COUNT(*) AS n FROM ({latest}) GROUP BY category", params, "all")}
            
        return {
            "total_processed": one(f"SELECT COUNT(*) FROM emails WHERE processing_status IN ('done','review') {'AND user_id=?' if user_id else ''}", params),
            "needs_review": one(f"SELECT COUNT(*) FROM emails WHERE processing_status='review' {'AND user_id=?' if user_id else ''}", params),
            "failed": one(f"SELECT COUNT(*) FROM emails WHERE processing_status='failed' {'AND user_id=?' if user_id else ''}", params),
            "pending": one(f"SELECT COUNT(*) FROM emails WHERE processing_status IN ('pending','processing') {'AND user_id=?' if user_id else ''}", params),
            "high_priority": one(f"SELECT COUNT(*) FROM ({latest}) WHERE priority='high'", params),
            "categories": cats,
        }

    def recent(self, user_id: str = None, limit: int = 50) -> list:
        cond = "AND e.user_id = ?" if user_id else ""
        params = (user_id, limit) if user_id else (limit,)
        rows = self._run(
            f"SELECT e.message_id, e.subject, e.processing_status AS status, e.updated_at, "
            f"c.category, c.priority, c.confidence, "
            f"(SELECT group_concat(a.action || CASE WHEN a.detail != '' THEN ':' || a.detail ELSE '' END, ', ') "
            f" FROM actions a WHERE a.message_id = e.message_id AND a.success = 1) AS actions "
            f"FROM emails e LEFT JOIN classifications c "
            f"ON c.id = (SELECT MAX(id) FROM classifications WHERE message_id = e.message_id) "
            f"WHERE e.processing_status NOT IN ('pending') {cond} ORDER BY e.updated_at DESC LIMIT ?",
            params, "all")
        return [dict(r) for r in rows]
