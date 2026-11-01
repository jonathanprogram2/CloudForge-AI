
import json
import os
import sqlite3
from pathlib import Path

import psycopg


def database_url() -> str | None:
    """Use PostgreSQL when DATABASE_URL is configured."""
    return os.getenv("DATABASE_URL") or None


def db_path() -> Path:
    return Path(
        os.getenv("CLOUDFORGE_DB_PATH", "./data/cloudforge.db")
    )


def sqlite_connection() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    return connection


def init_postgres(connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)


def save_run(data: dict) -> None:
    url = database_url()

    if url:
        with psycopg.connect(url, connect_timeout=5) as connection:
            init_postgres(connection)

            connection.execute(
                """
                INSERT INTO runs (id, data, created_at)
                VALUES (%s, %s::jsonb, %s)
                """,
                (
                    data["id"],
                    json.dumps(data),
                    data["evaluated_at"],
                ),
            )
        return

    connection = sqlite_connection()

    try:
        connection.execute(
            """
            INSERT INTO runs (id, data, created_at)
            VALUES (?, ?, ?)
            """,
            (
                data["id"],
                json.dumps(data),
                data["evaluated_at"],
            ),
        )
        connection.commit()
    finally:
        connection.close()


def list_runs(limit: int = 20) -> list[dict]:
    url = database_url()

    if url:
        with psycopg.connect(url, connect_timeout=5) as connection:
            init_postgres(connection)

            rows = connection.execute(
                """
                SELECT data
                FROM runs
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()

            return [
                value if isinstance(value, dict)
                else json.loads(value)
                for (value,) in rows
            ]

    connection = sqlite_connection()

    try:
        rows = connection.execute(
            """
            SELECT data
            FROM runs
            ORDER BY created_at DESC, rowid DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [json.loads(row["data"]) for row in rows]
    finally:
        connection.close()
