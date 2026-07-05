"""
Data Store
-----------
Minimal JSON-file-backed store so the prototype runs with zero external
dependencies. The function signatures here map 1:1 onto what you'd call
on a Firestore collection, so swapping to real Firebase later means
editing ONLY this file (see comments below) — nothing else in the app
needs to change.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db.json")
_lock = threading.Lock()


def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump({"cases": [], "next_id": 1}, f)


def add_case(fields: Dict) -> Dict:
    """Adds a new case record and returns it (with its assigned id + timestamp)."""
    _ensure_db()
    with _lock:
        with open(DB_PATH, "r") as f:
            db = json.load(f)

        case_id = db["next_id"]
        db["next_id"] += 1

        record = {
            "id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **fields,
        }
        db["cases"].append(record)

        with open(DB_PATH, "w") as f:
            json.dump(db, f, indent=2)

        return record

    # --- To swap to Firebase Firestore later, replace the body above with:
    #     doc_ref = firestore_client.collection("cases").document()
    #     record = {"id": doc_ref.id, "timestamp": ..., **fields}
    #     doc_ref.set(record)
    #     return record


def get_all_cases() -> List[Dict]:
    _ensure_db()
    with _lock:
        with open(DB_PATH, "r") as f:
            db = json.load(f)
    return db["cases"]


def get_case(case_id: int) -> Optional[Dict]:
    for c in get_all_cases():
        if c["id"] == case_id:
            return c
    return None


def get_dashboard_stats() -> Dict:
    cases = get_all_cases()
    high = sum(1 for c in cases if c.get("priority_tier") == "High")
    medium = sum(1 for c in cases if c.get("priority_tier") == "Medium")
    low = sum(1 for c in cases if c.get("priority_tier") == "Low")
    return {
        "total": len(cases),
        "high": high,
        "medium": medium,
        "low": low,
    }
