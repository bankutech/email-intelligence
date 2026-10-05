import re
from pathlib import Path

db_file = Path('app/database/db.py')
code = db_file.read_text('utf-8')

# Change SCHEMA
schema_new = """
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
CREATE INDEX IF NOT EXISTS idx_class_msg ON classifications(message_id);
CREATE INDEX IF NOT EXISTS idx_actions_msg ON actions(message_id);
CREATE INDEX IF NOT EXISTS idx_logs_msg ON processing_logs(message_id);
"""

code = re.sub(r'SCHEMA = (.*?)\n\nPROCESSED_STATUSES = \("done", "review"\)', f'SCHEMA = """{schema_new}"""\n\nPROCESSED_STATUSES = ("done", "review")', code, flags=re.DOTALL)

code = code.replace(
    'def register_message(self, message_id: str) -> bool:',
    'def register_message(self, message_id: str, user_id: str) -> bool:'
).replace(
    '"VALUES(?, \'pending\', ?, ?)", (message_id, now, now))',
    '"VALUES(?, ?, \'pending\', ?, ?)", (message_id, user_id, now, now))'
).replace(
    'INSERT OR IGNORE INTO emails(message_id, processing_status, first_seen_at, updated_at)',
    'INSERT OR IGNORE INTO emails(message_id, user_id, processing_status, first_seen_at, updated_at)'
)

# Also need user management
user_funcs = """
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

"""

code = code.replace('# ------------------------------------------------------------ email lifecycle', user_funcs + '\n    # ------------------------------------------------------------ email lifecycle')

code = code.replace('def stats(self) -> dict:', 'def stats(self, user_id: str = None) -> dict:')
code = code.replace('def recent(self, limit: int = 50) -> list:', 'def recent(self, user_id: str = None, limit: int = 50) -> list:')

# We need to add WHERE user_id filters to stats and recent
db_file.write_text(code, 'utf-8')
