from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DB_PATH = Path("compliancegraph.db")


@contextmanager
def connect(db_path: Path | str = DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                input_json TEXT NOT NULL,
                normalized_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )


def save_scan(scan_id: str, raw_input: dict[str, Any], normalized: dict[str, Any], result: dict[str, Any]) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO scans (id, input_json, normalized_json, result_json)
            VALUES (?, ?, ?, ?)
            """,
            (scan_id, json.dumps(raw_input), json.dumps(normalized), json.dumps(result)),
        )


def get_scan(scan_id: str) -> dict[str, Any] | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "input": json.loads(row["input_json"]),
        "normalized": json.loads(row["normalized_json"]),
        "result": json.loads(row["result_json"]),
    }
