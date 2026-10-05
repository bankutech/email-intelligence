import sqlite3

class MockDB:
    def __init__(self):
        self._conn = sqlite3.connect(':memory:')
        self._conn.row_factory = sqlite3.Row
        self._conn.execute('CREATE TABLE emails (message_id TEXT PRIMARY KEY, user_id TEXT, processing_status TEXT, updated_at TEXT, subject TEXT)')
        self._conn.execute('CREATE TABLE classifications (id INTEGER PRIMARY KEY, message_id TEXT, category TEXT, priority TEXT, confidence REAL)')
        self._conn.execute('CREATE TABLE actions (id INTEGER PRIMARY KEY, message_id TEXT, action TEXT, detail TEXT, success INTEGER)')
    
    def _run(self, sql, params=(), fetch="none"):
        cur = self._conn.execute(sql, params)
        if fetch == "all": return cur.fetchall()
        if fetch == "one": return cur.fetchone()
        return cur

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
            "categories": cats
        }

db = MockDB()
print(db.stats("user1"))
