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

import os
from app.models import Classification, Email
from app.utils import scrub_secrets, utcnow_iso, encrypt_token, decrypt_token

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    token_json    TEXT NOT NULL,
    settings      TEXT NOT NULL DEFAULT '{}',
    gmail_history_id TEXT,
    last_successful_sync TEXT,
    sync_status   TEXT,
    sync_error    TEXT,
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
CREATE TABLE IF NOT EXISTS oauth_states (
    state         TEXT PRIMARY KEY,
    code_verifier TEXT,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_oauth_states_created ON oauth_states(created_at);
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
    def __init__(self, path: str, read_only: bool = False, encryption_key: Optional[str] = None):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._encryption_key = encryption_key if encryption_key is not None else (
            os.environ.get("TOKEN_ENCRYPTION_KEY") or os.environ.get("SESSION_SECRET_KEY", "")
        )
        try:
            self._conn = sqlite3.connect(path, timeout=30, check_same_thread=False, isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            try:
                self._conn.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                pass
            self._conn.execute("PRAGMA foreign_keys=ON")
            if not read_only:
                self._conn.executescript(SCHEMA)
                try:
                    self._conn.execute("ALTER TABLE users ADD COLUMN gmail_history_id TEXT")
                    self._conn.execute("ALTER TABLE users ADD COLUMN last_successful_sync TEXT")
                    self._conn.execute("ALTER TABLE users ADD COLUMN sync_status TEXT")
                    self._conn.execute("ALTER TABLE users ADD COLUMN sync_error TEXT")
                except sqlite3.OperationalError:
                    pass
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
        result = []
        for r in rows:
            d = dict(r)
            if d.get("token_json") and self._encryption_key:
                d["token_json"] = decrypt_token(d["token_json"], self._encryption_key)
            result.append(d)
        return result

    def get_user(self, user_id: str):
        row = self._run("SELECT * FROM users WHERE id=?", (user_id,), "one")
        if not row:
            return None
        d = dict(row)
        if d.get("token_json") and self._encryption_key:
            d["token_json"] = decrypt_token(d["token_json"], self._encryption_key)
        return d

    def upsert_user(self, user_id: str, email: str, token_json: str):
        now = utcnow_iso()
        stored_token = encrypt_token(token_json, self._encryption_key) if (self._encryption_key and token_json) else token_json
        self._run(
            "INSERT INTO users(id, email, token_json, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET email=excluded.email, token_json=excluded.token_json",
            (user_id, email, stored_token, now)
        )
        
    def update_user_settings(self, user_id: str, settings: str):
        self._run("UPDATE users SET settings=? WHERE id=?", (settings, user_id))

    def update_user_history(self, user_id: str, history_id: str):
        self._run("UPDATE users SET gmail_history_id=? WHERE id=?", (history_id, user_id))

    def update_user_sync(self, user_id: str, status: str, error: str = None):
        if status and status.startswith("success"):
            self._run("UPDATE users SET sync_status=?, last_successful_sync=?, sync_error=NULL WHERE id=?", 
                      (status, utcnow_iso(), user_id))
        else:
            self._run("UPDATE users SET sync_status=?, sync_error=? WHERE id=?", 
                      (status, error, user_id))


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
            "ORDER BY rowid DESC LIMIT ?",
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
            
        priorities = {r["priority"]: r["n"] for r in self._run(
            f"SELECT priority, COUNT(*) AS n FROM ({latest}) GROUP BY priority", params, "all")}

        total_proc = one(f"SELECT COUNT(*) FROM emails WHERE processing_status IN ('done','review') {'AND user_id=?' if user_id else ''}", params)
        needs_rev = one(f"SELECT COUNT(*) FROM emails WHERE processing_status='review' {'AND user_id=?' if user_id else ''}", params)
        
        avg_row = self._run(f"SELECT AVG(confidence) AS avg_c FROM ({latest})", params, "one")
        avg_conf = round(float(avg_row["avg_c"]), 3) if avg_row and avg_row["avg_c"] is not None else 0.0
        
        auto_count = max(total_proc - needs_rev, 0)
        auto_rate = round((auto_count / total_proc * 100), 1) if total_proc > 0 else 100.0

        return {
            "total_processed": total_proc,
            "needs_review": needs_rev,
            "failed": one(f"SELECT COUNT(*) FROM emails WHERE processing_status='failed' {'AND user_id=?' if user_id else ''}", params),
            "pending": one(f"SELECT COUNT(*) FROM emails WHERE processing_status IN ('pending','processing') {'AND user_id=?' if user_id else ''}", params),
            "high_priority": one(f"SELECT COUNT(*) FROM ({latest}) WHERE priority='high'", params),
            "categories": cats,
            "priorities": priorities,
            "avg_confidence": avg_conf,
            "automated_count": auto_count,
            "automation_rate": auto_rate,
        }

    def recent(self, user_id: str = None, limit: int = 100) -> list:
        cond = "AND e.user_id = ?" if user_id else ""
        params = (user_id, limit) if user_id else (limit,)
        rows = self._run(
            f"SELECT e.message_id, e.subject, e.processing_status AS status, e.updated_at, "
            f"e.sender AS sender_email, e.email_timestamp, e.labels, e.attachments, "
            f"c.category, c.priority, c.confidence, c.reason, c.rule_flags, c.model, "
            f"(SELECT group_concat(a.action || CASE WHEN a.detail != '' THEN ':' || a.detail ELSE '' END, ', ') "
            f" FROM actions a WHERE a.message_id = e.message_id AND a.success = 1) AS actions "
            f"FROM emails e LEFT JOIN classifications c "
            f"ON c.id = (SELECT MAX(id) FROM classifications WHERE message_id = e.message_id) "
            f"WHERE e.processing_status NOT IN ('pending') {cond} ORDER BY COALESCE(e.email_timestamp, e.updated_at) DESC LIMIT ?",
            params, "all")
        result = []
        for r in rows:
            d = dict(r)
            for k in ("rule_flags", "labels", "attachments"):
                if d.get(k) and isinstance(d[k], str):
                    try:
                        d[k] = json.loads(d[k])
                    except Exception:
                        d[k] = []
                elif not d.get(k):
                    d[k] = []
            result.append(d)
        return result

    def get_email_detail(self, message_id: str, user_id: str = None) -> Optional[dict]:
        cond = "AND user_id = ?" if user_id else ""
        params = (message_id, user_id) if user_id else (message_id,)
        row = self._run(f"SELECT * FROM emails WHERE message_id=? {cond}", params, "one")
        if not row:
            return None
        d = dict(row)
        for k in ("labels", "attachments", "recipients"):
            if d.get(k) and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except Exception:
                    d[k] = []
            elif not d.get(k):
                d[k] = []
        # Classifications history
        clist = self._run("SELECT * FROM classifications WHERE message_id=? ORDER BY id DESC", (message_id,), "all")
        d["classifications"] = [dict(c) for c in clist]
        for c in d["classifications"]:
            if c.get("rule_flags") and isinstance(c["rule_flags"], str):
                try:
                    c["rule_flags"] = json.loads(c["rule_flags"])
                except Exception:
                    c["rule_flags"] = []
        # Actions history
        alist = self._run("SELECT * FROM actions WHERE message_id=? ORDER BY id ASC", (message_id,), "all")
        d["actions_history"] = [dict(a) for a in alist]
        # Logs
        llist = self._run("SELECT * FROM processing_logs WHERE message_id=? ORDER BY id ASC", (message_id,), "all")
        d["logs"] = [dict(l) for l in llist]
        return d

    def update_email_category(self, message_id: str, new_category: str, detail: str = "") -> None:
        now = utcnow_iso()
        latest = self._run("SELECT * FROM classifications WHERE message_id=? ORDER BY id DESC LIMIT 1", (message_id,), "one")
        prio = latest["priority"] if latest else "normal"
        model = latest["model"] if latest else "manual"
        reason = f"Human review: {detail or 'Category updated by user'}"
        self._run(
            "INSERT INTO classifications(message_id, timestamp, category, priority, confidence, reason, model, rule_flags, llm_valid) "
            "VALUES(?, ?, ?, ?, 1.0, ?, ?, '[]', 1)",
            (message_id, now, new_category, prio, reason, model)
        )
        self.set_status(message_id, "done")
        self.record_action(message_id, "manual_category_change", f"Category corrected to {new_category}")

    def reset_demo_data(self, user_id: str = "demo@example.com") -> None:
        demo_mids = [r["message_id"] for r in self._run("SELECT message_id FROM emails WHERE user_id=?", (user_id,), "all")]
        for mid in demo_mids:
            self._run("DELETE FROM processing_logs WHERE message_id=?", (mid,))
            self._run("DELETE FROM actions WHERE message_id=?", (mid,))
            self._run("DELETE FROM classifications WHERE message_id=?", (mid,))
        self._run("DELETE FROM emails WHERE user_id=?", (user_id,))
        self.upsert_user(user_id, user_id, json.dumps({"token": "demo_token"}))

    def save_oauth_state(self, state: str, code_verifier: str = "") -> None:
        """Store OAuth state and PKCE verifier with auto-cleanup of states older than 15 minutes."""
        now = utcnow_iso()
        import datetime
        cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        self._run("DELETE FROM oauth_states WHERE created_at < ?", (cutoff,))
        self._run(
            "INSERT OR REPLACE INTO oauth_states(state, code_verifier, created_at) VALUES(?, ?, ?)",
            (state, code_verifier or "", now)
        )

    def consume_oauth_state(self, state: str) -> Optional[dict]:
        """Validate and atomically consume (delete) a state to prevent replay attacks.
        Returns dict with code_verifier if valid, or None if expired or not found.
        """
        import datetime
        row = self._run("SELECT code_verifier, created_at FROM oauth_states WHERE state=?", (state,), "one")
        if not row:
            return None
        self._run("DELETE FROM oauth_states WHERE state=?", (state,))
        try:
            created_dt = datetime.datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            age = (datetime.datetime.now(datetime.timezone.utc) - created_dt).total_seconds()
            if age > 900:  # 15 minutes TTL
                return None
        except Exception:
            pass
        return {"code_verifier": row["code_verifier"]}
