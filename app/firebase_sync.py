"""Firestore synchronization service for AI Email Automation.

Syncs processed emails, classifications, and system stats directly into Cloud Firestore
via Google's REST API without requiring heavy external dependencies.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
import requests

log = logging.getLogger(__name__)

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "project-192c1548-1872-422c-a26")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyD67JCKwoUKvBJyoL7Let29Y_7lfw5uvZE")
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"


def to_firestore_value(val: Any) -> Dict[str, Any]:
    """Convert Python primitive/nested type into Firestore typed field format."""
    if val is None:
        return {"nullValue": None}
    if isinstance(val, bool):
        return {"booleanValue": val}
    if isinstance(val, int):
        return {"integerValue": str(val)}
    if isinstance(val, float):
        return {"doubleValue": val}
    if isinstance(val, str):
        return {"stringValue": val}
    if isinstance(val, (list, tuple)):
        return {"arrayValue": {"values": [to_firestore_value(v) for v in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {str(k): to_firestore_value(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def to_firestore_doc(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dict of fields into Firestore document object."""
    return {"fields": {str(k): to_firestore_value(v) for k, v in data.items() if v is not None}}


def sync_email_to_firestore(email_data: dict) -> bool:
    """Save or update an email document in the 'emails' collection in Firestore."""
    mid = email_data.get("message_id")
    if not mid or not FIREBASE_API_KEY:
        return False
    try:
        cls_list = email_data.get("classifications") or []
        first_cls = cls_list[0] if (isinstance(cls_list, list) and len(cls_list) > 0) else {}

        category = email_data.get("category") or first_cls.get("category") or "unknown"
        priority = email_data.get("priority") or first_cls.get("priority") or "normal"
        confidence = float(email_data.get("confidence") or first_cls.get("confidence") or 0.0)
        reason = email_data.get("reason") or first_cls.get("reason") or ""
        model = email_data.get("model") or first_cls.get("model") or "gemini-3.5-flash-lite"

        clean_data = {
            "message_id": mid,
            "subject": email_data.get("subject") or "No Subject",
            "sender_email": email_data.get("sender_email") or email_data.get("sender") or "",
            "category": category,
            "priority": priority,
            "confidence": confidence,
            "reason": reason,
            "status": email_data.get("status") or email_data.get("processing_status") or "processed",
            "email_timestamp": email_data.get("email_timestamp") or "",
            "updated_at": email_data.get("updated_at") or "",
            "labels": email_data.get("labels") if isinstance(email_data.get("labels"), list) else [],
            "actions": email_data.get("actions") or "",
            "model": model,
        }
        url = f"{FIRESTORE_URL}/emails/{mid}?key={FIREBASE_API_KEY}"
        resp = requests.patch(url, json=to_firestore_doc(clean_data), timeout=5)
        if resp.status_code == 200:
            log.debug("Successfully synced email %s to Firestore", mid)
            return True
        log.warning("Firestore sync for email %s returned %d: %s", mid, resp.status_code, resp.text)
        return False
    except Exception as exc:
        log.warning("Firestore email sync failed: %s", exc)
        return False


def sync_stats_to_firestore(stats_data: dict) -> bool:
    """Save overview aggregate stats to Firestore document 'stats/overview'."""
    if not FIREBASE_API_KEY:
        return False
    try:
        clean_stats = {
            "total_emails": int(stats_data.get("total_emails") or 0),
            "processed": int(stats_data.get("processed") or 0),
            "review_count": int(stats_data.get("review_count") or 0),
            "urgent_count": int(stats_data.get("urgent_count") or 0),
            "automated_count": int(stats_data.get("automated_count") or 0),
            "automation_rate": float(stats_data.get("automation_rate") or 0.0),
            "categories": stats_data.get("categories") if isinstance(stats_data.get("categories"), dict) else {},
            "last_synced_at": email_timestamp_now(),
        }
        url = f"{FIRESTORE_URL}/stats/overview?key={FIREBASE_API_KEY}"
        resp = requests.patch(url, json=to_firestore_doc(clean_stats), timeout=5)
        return resp.status_code == 200
    except Exception as exc:
        log.warning("Firestore stats sync failed: %s", exc)
        return False


def email_timestamp_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def sync_all_to_firestore(db, user_id: Optional[str] = None) -> int:
    """Sync all existing recent emails and overview stats from the local SQLite database to Firestore."""
    count = 0
    try:
        stats = db.stats(user_id=user_id)
        sync_stats_to_firestore(stats)
        recent_emails = db.recent(user_id=user_id, limit=200)
        for item in recent_emails:
            if sync_email_to_firestore(item):
                count += 1
        log.info("Synced %d emails to Firestore for user %s", count, user_id or "all")
    except Exception as exc:
        log.warning("Bulk sync to Firestore failed: %s", exc)
    return count
