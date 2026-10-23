"""PostgreSQL connection helpers for Cricbuzz LiveStats.

Uses DATABASE_URL from environment/.env or Streamlit secrets.
Provides a small compatibility layer for existing SQLite-style SQL placeholders.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg.rows import tuple_row

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TABLES = ("players", "matches", "venues", "series", "player_match_stats")


class HybridRow(dict):
    """Mapping row that supports both row['column'] and row[0] access."""
    def __init__(self, names, values):
        super().__init__(zip(names, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


def _hybrid_row(cursor):
    names = [column.name for column in cursor.description]
    def make_row(values):
        return HybridRow(names, values)
    return make_row


def _database_url():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        try:
            import streamlit as st
            url = str(st.secrets.get("DATABASE_URL", "")).strip()
        except Exception:
            url = ""
    if not url or "YOUR_" in url or "NEW_PASSWORD" in url:
        raise RuntimeError(
            "DATABASE_URL is missing. Set it in your local .env file or "
            "in Streamlit Community Cloud > App settings > Secrets."
        )
    return url


def _translate_sql(query):
    """Translate SQLite qmark/named parameters to psycopg placeholders."""
    # Convert named :key placeholders, but don't alter PostgreSQL :: casts.
    query = re.sub(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", query)
    # Existing project uses qmark placeholders only inside SQL statements.
    query = query.replace("?", "%s")
    return query


class CursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        if params is None:
            self._cursor.execute(_translate_sql(query))
        else:
            self._cursor.execute(_translate_sql(query), params)
        return self

    def executemany(self, query, params_seq):
        self._cursor.executemany(_translate_sql(query), params_seq)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class ConnectionAdapter:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, query, params=None):
        cursor = self._connection.cursor()
        return CursorAdapter(cursor).execute(query, params)

    def executemany(self, query, params_seq):
        cursor = self._connection.cursor()
        return CursorAdapter(cursor).executemany(query, params_seq)

    def cursor(self, *args, **kwargs):
        return CursorAdapter(self._connection.cursor(*args, **kwargs))

    def close(self):
        self._connection.close()

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._connection.__exit__(exc_type, exc_value, traceback)

    def __getattr__(self, name):
        return getattr(self._connection, name)


def get_connection():
    conn = psycopg.connect(
        _database_url(),
        sslmode="require",
        row_factory=_hybrid_row,
        autocommit=False,
    )
    return ConnectionAdapter(conn)


def read_sql_query(query, connection, params=None):
    """Run SQL with psycopg and return a pandas DataFrame."""
    cursor = connection.execute(query, params) if params is not None else connection.execute(query)
    rows = cursor.fetchall()
    columns = [column.name for column in cursor.description] if cursor.description else []
    return pd.DataFrame([dict(row) for row in rows], columns=columns)


def init_db():
    """Validate the existing Supabase schema; never recreate or wipe tables."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            """
        ).fetchall()
        existing = {row["table_name"] for row in rows}
        missing = [table for table in TABLES if table not in existing]
        if missing:
            raise RuntimeError(
                "Required Supabase tables are missing: " + ", ".join(missing)
                + ". Do not run a destructive reset; check the schema in Supabase."
            )
    return True


def table_counts():
    init_db()
    with get_connection() as conn:
        return {
            table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in TABLES
        }
