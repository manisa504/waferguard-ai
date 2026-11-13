"""Atomic per-case state/audit/outbox persistence with optimistic concurrency."""

import json
import sqlite3
from pathlib import Path


class Conflict(Exception):
    pass


class SQLiteStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS cases "
                "(scope TEXT, id TEXT, version INTEGER, payload TEXT, "
                "PRIMARY KEY(scope,id))"
            )

    def connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def get(self, scope, case_id):
        with self.connection() as connection:
            row = connection.execute(
                "SELECT payload FROM cases WHERE scope=? AND id=?", (scope, case_id)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def create(self, case):
        try:
            with self.connection() as connection:
                connection.execute(
                    "INSERT INTO cases VALUES(?,?,?,?)",
                    (case["scope"], case["id"], case["version"], json.dumps(case)),
                )
        except sqlite3.IntegrityError as error:
            raise Conflict("Case already exists") from error

    def replace(self, case, expected):
        with self.connection() as connection:
            changed = connection.execute(
                "UPDATE cases SET version=?,payload=? WHERE scope=? AND id=? AND version=?",
                (case["version"], json.dumps(case), case["scope"], case["id"], expected),
            ).rowcount
            if changed != 1:
                raise Conflict("Case changed; refresh before deciding")

    def list(self, scope, limit=100):
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT payload FROM cases WHERE scope=? ORDER BY rowid DESC LIMIT ?",
                (scope, limit),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
