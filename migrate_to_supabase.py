import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql

ROOT = Path(__file__).resolve().parent
SQLITE_PATH = ROOT / "data" / "cricbuzz_livestats.db"

TABLES = [
    "players",
    "matches",
    "venues",
    "series",
    "player_match_stats",
]


def main():
    load_dotenv(ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")

    if not database_url or "YOUR_" in database_url:
        raise RuntimeError(
            "Set your real DATABASE_URL in .env first."
        )

    if not SQLITE_PATH.exists():
        raise FileNotFoundError(
            f"Local database not found: {SQLITE_PATH}"
        )

    with sqlite3.connect(SQLITE_PATH) as source:
        source.row_factory = sqlite3.Row

        with psycopg.connect(database_url) as target:
            with target.cursor() as cursor:
                for table in TABLES:
                    columns = [
                        row["name"]
                        for row in source.execute(
                            f'PRAGMA table_info("{table}")'
                        )
                    ]
                    rows = source.execute(
                        f'SELECT * FROM "{table}"'
                    ).fetchall()

                    column_sql = sql.SQL(", ").join(
                        sql.Identifier(c) for c in columns
                    )
                    placeholders = sql.SQL(", ").join(
                        sql.Placeholder() for _ in columns
                    )
                    query = sql.SQL(
                        "INSERT INTO {} ({}) VALUES ({}) "
                        "ON CONFLICT DO NOTHING"
                    ).format(
                        sql.Identifier(table),
                        column_sql,
                        placeholders,
                    )

                    cursor.executemany(
                        query,
                        [tuple(row) for row in rows],
                    )
                    print(f"{table}: processed {len(rows)} rows")

                for table in TABLES:
                    cursor.execute(
                        """
                        SELECT setval(
                            pg_get_serial_sequence(%s, 'id'),
                            COALESCE(MAX(id), 1),
                            MAX(id) IS NOT NULL
                        )
                        FROM {}
                        """.format(
                            sql.Identifier(table).as_string(
                                cursor.connection
                            )
                        ),
                        (f"public.{table}",),
                    )

            with target.cursor() as cursor:
                print("\nSupabase row counts:")
                for table in TABLES:
                    cursor.execute(
                        sql.SQL("SELECT COUNT(*) FROM {}").format(
                            sql.Identifier(table)
                        )
                    )
                    print(f"{table}: {cursor.fetchone()[0]}")

    print("\nMigration completed successfully.")


if __name__ == "__main__":
    main()
