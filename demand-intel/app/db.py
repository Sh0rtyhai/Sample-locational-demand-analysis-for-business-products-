"""SQLite storage. Raw readings are stored immutable with full provenance;
scores are computed from them and also persisted for reproducibility."""

import json
import os
import sqlite3
import threading

_lock = threading.Lock()
_conn = None


def init(db_path: str):
    global _conn
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _conn = sqlite3.connect(db_path, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.executescript("""
    CREATE TABLE IF NOT EXISTS raw_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adapter TEXT NOT NULL,          -- trends | dosm | maps
        product_id TEXT NOT NULL,
        state_id TEXT NOT NULL,
        factor_id TEXT NOT NULL,        -- search | buying | saturation | competition
        value REAL,                     -- native adapter value (NULL if collect failed)
        week TEXT NOT NULL,             -- ISO date of the Monday of the reading week
        collected_at TEXT NOT NULL,     -- UTC timestamp of collection
        is_mock INTEGER NOT NULL DEFAULT 0,
        note TEXT
    );
    CREATE TABLE IF NOT EXISTS scores (
        product_id TEXT NOT NULL,
        state_id TEXT NOT NULL,
        computed_at TEXT NOT NULL,
        composite REAL NOT NULL,
        confidence TEXT NOT NULL,
        coverage REAL NOT NULL,
        breakdown TEXT NOT NULL,        -- JSON: per-factor score + weight + provenance
        PRIMARY KEY (product_id, state_id, computed_at)
    );
    CREATE TABLE IF NOT EXISTS run_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT,
        detail TEXT
    );
    """)
    _conn.commit()


def execute(sql, params=()):
    with _lock:
        _conn.execute(sql, params)
        _conn.commit()


def query(sql, params=()):
    with _lock:
        return _conn.execute(sql, params).fetchall()


def insert_reading(adapter, product_id, state_id, factor_id, value, week, is_mock, note=""):
    from datetime import datetime, timezone
    execute(
        "INSERT INTO raw_readings (adapter, product_id, state_id, factor_id, value, week, collected_at, is_mock, note) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (adapter, product_id, state_id, factor_id, value, week,
         datetime.now(timezone.utc).isoformat(timespec="seconds"), int(is_mock), note),
    )


def latest_reading(adapter, product_id, state_id, factor_id):
    rows = query(
        "SELECT value, is_mock, week, collected_at, note FROM raw_readings "
        "WHERE adapter=? AND product_id=? AND state_id=? AND factor_id=? AND value IS NOT NULL "
        "ORDER BY week DESC LIMIT 1",
        (adapter, product_id, state_id, factor_id),
    )
    return dict(rows[0]) if rows else None
