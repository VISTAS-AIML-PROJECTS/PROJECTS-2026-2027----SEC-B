"""
services/dashboard.py

Stores and retrieves real application usage statistics in SQLite.
Stats start at zero and grow only from actual application events.
Does NOT invent numbers.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wrapture.db')


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            product_l REAL,
            product_w REAL,
            product_h REAL,
            is_fragile INTEGER,
            status TEXT,
            total_fits INTEGER,
            top_sku TEXT
        );

        CREATE TABLE IF NOT EXISTS material_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            predicted_class TEXT,
            confidence REAL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            role TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS review_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            reviews_analyzed INTEGER,
            positive INTEGER,
            negative INTEGER,
            neutral INTEGER
        );
    """)
    conn.commit()
    conn.close()


def record_recommendation(product_l, product_w, product_h, is_fragile, status, total_fits, top_sku):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO recommendations
           (created_at, product_l, product_w, product_h, is_fragile, status, total_fits, top_sku)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.utcnow().isoformat(), product_l, product_w, product_h,
         int(is_fragile), status, total_fits, top_sku)
    )
    conn.commit()
    conn.close()


def record_material_classification(predicted_class, confidence):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO material_classifications (created_at, predicted_class, confidence) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), predicted_class, confidence)
    )
    conn.commit()
    conn.close()


def record_review_analysis(reviews_analyzed, positive, negative, neutral):
    conn = _get_conn()
    conn.execute(
        """INSERT INTO review_analyses
           (created_at, reviews_analyzed, positive, negative, neutral)
           VALUES (?, ?, ?, ?, ?)""",
        (datetime.utcnow().isoformat(), reviews_analyzed, positive, negative, neutral)
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Return real counts from the database. All zeros if no activity yet."""
    conn = _get_conn()

    total_recommendations = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    total_material_scans  = conn.execute("SELECT COUNT(*) FROM material_classifications").fetchone()[0]
    total_review_analyses = conn.execute("SELECT COUNT(*) FROM review_analyses").fetchone()[0]

    # Material class distribution
    material_rows = conn.execute(
        "SELECT predicted_class, COUNT(*) as cnt FROM material_classifications GROUP BY predicted_class ORDER BY cnt DESC"
    ).fetchall()
    material_distribution = [{'class': r['predicted_class'], 'count': r['cnt']} for r in material_rows]

    # Recommendation status breakdown
    status_rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM recommendations GROUP BY status"
    ).fetchall()
    recommendation_statuses = {r['status']: r['cnt'] for r in status_rows}

    conn.close()

    return {
        'total_recommendations': total_recommendations,
        'total_material_scans': total_material_scans,
        'total_review_analyses': total_review_analyses,
        'material_distribution': material_distribution,
        'recommendation_statuses': recommendation_statuses,
        'note': 'All statistics are derived from actual application usage. Starts at zero.',
    }
