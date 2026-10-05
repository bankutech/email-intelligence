import sqlite3
c = sqlite3.connect(':memory:')
c.execute('CREATE TABLE emails (message_id TEXT PRIMARY KEY, user_id TEXT, processing_status TEXT, updated_at TEXT, subject TEXT)')
c.execute('CREATE TABLE classifications (id INTEGER PRIMARY KEY, message_id TEXT, category TEXT, priority TEXT, confidence REAL)')
c.execute('CREATE TABLE actions (id INTEGER PRIMARY KEY, message_id TEXT, action TEXT, detail TEXT, success INTEGER)')
print(c.execute("SELECT e.message_id, e.subject, e.processing_status AS status, e.updated_at, c.category, c.priority, c.confidence, (SELECT group_concat(a.action || CASE WHEN a.detail != '' THEN ':' || a.detail ELSE '' END, ', ') FROM actions a WHERE a.message_id = e.message_id AND a.success = 1) AS actions FROM emails e LEFT JOIN classifications c ON c.id = (SELECT MAX(id) FROM classifications WHERE message_id = e.message_id) WHERE e.processing_status NOT IN ('pending') AND e.user_id = ? ORDER BY e.updated_at DESC LIMIT ?", ('u', 50)).fetchall())
