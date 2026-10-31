import json
import os
import sqlite3
from pathlib import Path


def db_path() -> Path:
    return Path(os.getenv("CLOUDFORGE_DB_PATH", "./data/cloudforge.db"))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    connection.commit()
    return connection


def save_run(data: dict) -> None:
    with connect() as db:
        db.execute("INSERT INTO runs (id, data, created_at) VALUES (?, ?, ?)",
                   (data["id"], json.dumps(data), data["evaluated_at"]))
        db.commit()


def list_runs(limit: int = 20) -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT data FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)).fetchall()
    return [json.loads(row["data"]) for row in rows]
