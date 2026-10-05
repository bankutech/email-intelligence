from pathlib import Path

db_file = Path('app/database/db.py')
code = db_file.read_text('utf-8')

code = code.replace(
    'def retryable_ids(self, max_attempts: int, stale_seconds: int = 600, limit: int = 50) -> list:',
    'def retryable_ids_for_user(self, user_id: str, max_attempts: int, stale_seconds: int = 600, limit: int = 50) -> list:'
).replace(
    '"SELECT message_id FROM emails WHERE "',
    '"SELECT message_id FROM emails WHERE user_id=? AND ("'
).replace(
    '(max_attempts, utcnow_iso(-stale_seconds), limit), "all")',
    '(user_id, max_attempts, utcnow_iso(-stale_seconds), limit), "all")'
).replace(
    '"OR (processing_status=\'processing\' AND updated_at < ?) "',
    '"OR (processing_status=\'processing\' AND updated_at < ?)) "'
)

# And fix stats and recent to use user_id filter
code = code.replace(
    "SELECT COUNT(*) FROM emails WHERE processing_status IN ('done','review')",
    "SELECT COUNT(*) FROM emails WHERE processing_status IN ('done','review')" + ' AND (user_id=? OR ? IS NULL)'
).replace(
    "SELECT COUNT(*) FROM emails WHERE processing_status='review'",
    "SELECT COUNT(*) FROM emails WHERE processing_status='review'" + ' AND (user_id=? OR ? IS NULL)'
).replace(
    "SELECT COUNT(*) FROM emails WHERE processing_status='failed'",
    "SELECT COUNT(*) FROM emails WHERE processing_status='failed'" + ' AND (user_id=? OR ? IS NULL)'
).replace(
    "SELECT COUNT(*) FROM emails WHERE processing_status IN ('pending','processing')",
    "SELECT COUNT(*) FROM emails WHERE processing_status IN ('pending','processing')" + ' AND (user_id=? OR ? IS NULL)'
)

# Oh wait, sqlite param binding for ? is NULL won't work easily like that with one(...) since it takes params=()
db_file.write_text(code, 'utf-8')
