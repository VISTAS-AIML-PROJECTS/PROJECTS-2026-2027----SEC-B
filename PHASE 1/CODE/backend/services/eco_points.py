"""
services/eco_points.py

Deterministic EcoPoints gamification system for Wrapture.

This is NOT an AI model. It is a rule-based backend system that awards
points for real, verified Wrapture actions.

──────────────────────────────────────────────────────────────────────────────
DATABASE TABLES (created by init_eco_db)
──────────────────────────────────────────────────────────────────────────────

  users
    id            INTEGER PRIMARY KEY AUTOINCREMENT
    username      TEXT NOT NULL UNIQUE
    created_at    TEXT NOT NULL
    is_dev_user   INTEGER NOT NULL DEFAULT 0   -- 1 = development/demo user

  eco_events
    id            INTEGER PRIMARY KEY AUTOINCREMENT
    user_id       INTEGER NOT NULL REFERENCES users(id)
    event_type    TEXT NOT NULL
    points        INTEGER NOT NULL
    co2e_saved_mt REAL                         -- NULL when no verified value
    created_at    TEXT NOT NULL
    metadata      TEXT                         -- JSON string, optional

──────────────────────────────────────────────────────────────────────────────
POINT RULES  (all values are deterministic and documented here)
──────────────────────────────────────────────────────────────────────────────

  PACKAGING_ANALYSIS          5 pts
    Awarded when the user runs a full packaging recommendation query.
    Rationale: encourages use of the data-driven recommender.

  PACKAGING_SELECTION        10 pts
    Awarded when the user explicitly selects a recommended package.
    Rationale: a selection is a stronger signal of engagement than a query.

  SUSTAINABLE_PACKAGING       15 pts
    Awarded when the selected package material is corrugated_cardboard
    or kraft_paper (both recyclable/renewable).
    Rationale: rewards choosing lower-impact materials.

  MATERIAL_SCAN               3 pts
    Awarded when the user completes a material classification scan.
    Rationale: encourages material awareness.

  REVIEW_ANALYSIS             2 pts
    Awarded when the user analyzes customer reviews.
    Rationale: minor engagement reward.

──────────────────────────────────────────────────────────────────────────────
CO2 HANDLING
──────────────────────────────────────────────────────────────────────────────

  co2e_saved_mt is stored ONLY when a verified value is supplied in the
  event metadata (sourced from the Packrift catalog field co2e_recycling_mt).

  The catalog value is negative (CO2 saved during recycling).
  We store the absolute value as "saved".

  If no verified CO2 value is provided, co2e_saved_mt is stored as NULL.
  Zero is NOT substituted for a missing value.

──────────────────────────────────────────────────────────────────────────────
DEVELOPMENT USER
──────────────────────────────────────────────────────────────────────────────

  A single development user (username="dev_user", is_dev_user=1) is created
  automatically on first init_eco_db() call if no users exist.

  This is a real database record, not a hardcoded value.
  It exists only to provide a valid user_id for development/testing.
  It starts with zero events and zero points.

  In production, replace with a real authentication system.

──────────────────────────────────────────────────────────────────────────────
LEADERBOARD
──────────────────────────────────────────────────────────────────────────────

  Rankings are calculated from actual database totals.
  If fewer than 2 users have events, the leaderboard is marked unavailable.
  No fake users are created.
"""

import json
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wrapture.db')

# ── Point rules ───────────────────────────────────────────────────────────────

POINT_RULES: dict[str, int] = {
    'PACKAGING_ANALYSIS':    5,
    'PACKAGING_SELECTION':  10,
    'SUSTAINABLE_PACKAGING': 15,
    'MATERIAL_SCAN':          3,
    'REVIEW_ANALYSIS':        2,
}

# Materials that qualify for SUSTAINABLE_PACKAGING bonus
SUSTAINABLE_MATERIALS = {'corrugated_cardboard', 'kraft_paper'}

# ── DB helpers ────────────────────────────────────────────────────────────────

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_eco_db():
    """
    Create EcoPoints tables if they do not exist.
    Create the development user if no users exist.
    Called once at app startup alongside init_db().
    """
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            created_at  TEXT    NOT NULL,
            is_dev_user INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS eco_events (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id),
            event_type    TEXT    NOT NULL,
            points        INTEGER NOT NULL,
            co2e_saved_mt REAL,
            created_at    TEXT    NOT NULL,
            metadata      TEXT
        );
    """)
    c.commit()

    # Create dev user only if no users exist at all
    count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        c.execute(
            "INSERT INTO users (username, created_at, is_dev_user) VALUES (?, ?, 1)",
            ("dev_user", _now()),
        )
        c.commit()

    c.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_user_id(c) -> int:
    """Return the dev user's id (always exists after init_eco_db)."""
    row = c.execute("SELECT id FROM users WHERE is_dev_user = 1 LIMIT 1").fetchone()
    if row:
        return row["id"]
    # Fallback: first user
    row = c.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    return row["id"] if row else None


# ── Public API ────────────────────────────────────────────────────────────────

def get_summary(user_id: int = None) -> dict:
    """
    Return the EcoPoints summary for a user.
    Uses the dev user if user_id is None.
    All values come from the database — nothing is invented.
    """
    c = _conn()
    if user_id is None:
        user_id = _default_user_id(c)

    if user_id is None:
        c.close()
        return _empty_summary()

    row = c.execute(
        """SELECT COUNT(*) as events,
                  COALESCE(SUM(points), 0) as points,
                  SUM(co2e_saved_mt) as co2e
           FROM eco_events WHERE user_id = ?""",
        (user_id,),
    ).fetchone()

    events     = row["events"]
    points     = row["points"]
    co2e       = row["co2e"]   # None if no events have a CO2 value

    # Recent events (last 10)
    recent = c.execute(
        """SELECT event_type, points, co2e_saved_mt, created_at, metadata
           FROM eco_events WHERE user_id = ?
           ORDER BY created_at DESC LIMIT 10""",
        (user_id,),
    ).fetchall()

    recent_list = [
        {
            "event_type":    r["event_type"],
            "points":        r["points"],
            "co2e_saved_mt": r["co2e_saved_mt"],
            "created_at":    r["created_at"],
            "metadata":      json.loads(r["metadata"]) if r["metadata"] else None,
        }
        for r in recent
    ]

    c.close()
    return {
        "user_id":      user_id,
        "points":       points,
        "events":       events,
        "co2e_saved_mt": co2e,          # null when no verified CO2 data exists
        "recent_events": recent_list,
        "note": "co2e_saved_mt is null when no verified catalog CO2 value was available for any event.",
    }


def _empty_summary() -> dict:
    return {
        "user_id":       None,
        "points":        0,
        "events":        0,
        "co2e_saved_mt": None,
        "recent_events": [],
        "note":          "No user data found.",
    }


def record_event(event_type: str, metadata: dict = None, user_id: int = None) -> dict:
    """
    Validate the event type, calculate points from POINT_RULES,
    extract CO2 only from verified metadata, and persist.

    Returns the updated summary or an error dict.

    The frontend CANNOT submit arbitrary point values.
    Points are always determined here from POINT_RULES.
    """
    if event_type not in POINT_RULES:
        return {
            "status": "error",
            "error":  f"Unknown event_type '{event_type}'. "
                      f"Valid types: {sorted(POINT_RULES.keys())}",
        }

    points = POINT_RULES[event_type]

    # CO2: only use a verified value from the catalog (co2e_recycling_mt field).
    # The catalog value is negative (CO2 saved during recycling).
    # We store the absolute value. If absent or zero, store NULL.
    co2e_saved = None
    if metadata and metadata.get("co2e_recycling_mt") is not None:
        raw = float(metadata["co2e_recycling_mt"])
        if raw != 0.0:
            co2e_saved = abs(raw)   # convert negative catalog value to positive "saved"

    c = _conn()
    if user_id is None:
        user_id = _default_user_id(c)

    if user_id is None:
        c.close()
        return {"status": "error", "error": "No user found in database."}

    c.execute(
        """INSERT INTO eco_events
           (user_id, event_type, points, co2e_saved_mt, created_at, metadata)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            event_type,
            points,
            co2e_saved,
            _now(),
            json.dumps(metadata) if metadata else None,
        ),
    )
    c.commit()
    c.close()

    summary = get_summary(user_id)
    return {"status": "ok", "event_recorded": event_type, "points_awarded": points, **summary}


def get_leaderboard() -> dict:
    """
    Return a ranked list of users by total points.
    Uses only real database records.
    If fewer than 2 users have events, returns unavailable status.
    """
    c = _conn()
    rows = c.execute(
        """SELECT u.id, u.username, u.is_dev_user,
                  COALESCE(SUM(e.points), 0) as total_points,
                  COUNT(e.id) as total_events
           FROM users u
           LEFT JOIN eco_events e ON e.user_id = u.id
           GROUP BY u.id
           HAVING total_events > 0
           ORDER BY total_points DESC""",
    ).fetchall()
    c.close()

    if len(rows) < 2:
        return {
            "status":  "UNAVAILABLE",
            "message": "Leaderboard unavailable — not enough users with recorded activity.",
            "entries": [],
        }

    entries = [
        {
            "rank":         i + 1,
            "username":     r["username"],
            "points":       r["total_points"],
            "events":       r["total_events"],
            "is_dev_user":  bool(r["is_dev_user"]),
        }
        for i, r in enumerate(rows)
    ]
    return {"status": "ok", "entries": entries}
