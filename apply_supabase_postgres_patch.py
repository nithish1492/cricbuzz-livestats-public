from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / f"backup_before_supabase_patch_{datetime.now():%Y%m%d_%H%M%S}"
BACKUP.mkdir()
TOUCH = [
    "utils/db_connection.py", "app_pages/crud_operations.py",
    "app_pages/database_explorer.py", "app_pages/data_import.py",
    "app_pages/live_matches.py", "app_pages/series_explorer.py",
    "app_pages/sql_queries.py", "app_pages/top_stats.py",
    "main.py", "utils/page_renderer.py",
]
for rel in TOUCH:
    src = ROOT / rel
    if src.exists():
        dst = BACKUP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

DB_CONNECTION = '"""PostgreSQL connection helpers for Cricbuzz LiveStats.\n\nUses DATABASE_URL from environment/.env or Streamlit secrets.\nProvides a small compatibility layer for existing SQLite-style SQL placeholders.\n"""\nfrom __future__ import annotations\n\nimport os\nimport re\nfrom pathlib import Path\n\nimport pandas as pd\nimport psycopg\nfrom dotenv import load_dotenv\nfrom psycopg.rows import tuple_row\n\nROOT = Path(__file__).resolve().parents[1]\nload_dotenv(ROOT / ".env")\n\nTABLES = ("players", "matches", "venues", "series", "player_match_stats")\n\n\nclass HybridRow(dict):\n    """Mapping row that supports both row[\'column\'] and row[0] access."""\n    def __init__(self, names, values):\n        super().__init__(zip(names, values))\n        self._values = tuple(values)\n\n    def __getitem__(self, key):\n        if isinstance(key, int):\n            return self._values[key]\n        return super().__getitem__(key)\n\n\ndef _hybrid_row(cursor):\n    names = [column.name for column in cursor.description]\n    def make_row(values):\n        return HybridRow(names, values)\n    return make_row\n\n\ndef _database_url():\n    url = os.getenv("DATABASE_URL", "").strip()\n    if not url:\n        try:\n            import streamlit as st\n            url = str(st.secrets.get("DATABASE_URL", "")).strip()\n        except Exception:\n            url = ""\n    if not url or "YOUR_" in url or "NEW_PASSWORD" in url:\n        raise RuntimeError(\n            "DATABASE_URL is missing. Set it in your local .env file or "\n            "in Streamlit Community Cloud > App settings > Secrets."\n        )\n    return url\n\n\ndef _translate_sql(query):\n    """Translate SQLite qmark/named parameters to psycopg placeholders."""\n    # Convert named :key placeholders, but don\'t alter PostgreSQL :: casts.\n    query = re.sub(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)", r"%(\\1)s", query)\n    # Existing project uses qmark placeholders only inside SQL statements.\n    query = query.replace("?", "%s")\n    return query\n\n\nclass CursorAdapter:\n    def __init__(self, cursor):\n        self._cursor = cursor\n\n    def execute(self, query, params=None):\n        if params is None:\n            self._cursor.execute(_translate_sql(query))\n        else:\n            self._cursor.execute(_translate_sql(query), params)\n        return self\n\n    def executemany(self, query, params_seq):\n        self._cursor.executemany(_translate_sql(query), params_seq)\n        return self\n\n    def fetchone(self):\n        return self._cursor.fetchone()\n\n    def fetchall(self):\n        return self._cursor.fetchall()\n\n    def __iter__(self):\n        return iter(self._cursor)\n\n    def __getattr__(self, name):\n        return getattr(self._cursor, name)\n\n\nclass ConnectionAdapter:\n    def __init__(self, connection):\n        self._connection = connection\n\n    def execute(self, query, params=None):\n        cursor = self._connection.cursor()\n        return CursorAdapter(cursor).execute(query, params)\n\n    def executemany(self, query, params_seq):\n        cursor = self._connection.cursor()\n        return CursorAdapter(cursor).executemany(query, params_seq)\n\n    def cursor(self, *args, **kwargs):\n        return CursorAdapter(self._connection.cursor(*args, **kwargs))\n\n    def close(self):\n        self._connection.close()\n\n    def commit(self):\n        self._connection.commit()\n\n    def rollback(self):\n        self._connection.rollback()\n\n    def __enter__(self):\n        self._connection.__enter__()\n        return self\n\n    def __exit__(self, exc_type, exc_value, traceback):\n        return self._connection.__exit__(exc_type, exc_value, traceback)\n\n    def __getattr__(self, name):\n        return getattr(self._connection, name)\n\n\ndef get_connection():\n    conn = psycopg.connect(\n        _database_url(),\n        sslmode="require",\n        row_factory=_hybrid_row,\n        autocommit=False,\n    )\n    return ConnectionAdapter(conn)\n\n\ndef read_sql_query(query, connection, params=None):\n    """Run SQL with psycopg and return a pandas DataFrame."""\n    cursor = connection.execute(query, params) if params is not None else connection.execute(query)\n    rows = cursor.fetchall()\n    columns = [column.name for column in cursor.description] if cursor.description else []\n    return pd.DataFrame([dict(row) for row in rows], columns=columns)\n\n\ndef init_db():\n    """Validate the existing Supabase schema; never recreate or wipe tables."""\n    with get_connection() as conn:\n        rows = conn.execute(\n            """\n            SELECT table_name\n            FROM information_schema.tables\n            WHERE table_schema = \'public\'\n              AND table_type = \'BASE TABLE\'\n            """\n        ).fetchall()\n        existing = {row["table_name"] for row in rows}\n        missing = [table for table in TABLES if table not in existing]\n        if missing:\n            raise RuntimeError(\n                "Required Supabase tables are missing: " + ", ".join(missing)\n                + ". Do not run a destructive reset; check the schema in Supabase."\n            )\n    return True\n\n\ndef table_counts():\n    init_db()\n    with get_connection() as conn:\n        return {\n            table: conn.execute(f\'SELECT COUNT(*) FROM "{table}"\').fetchone()[0]\n            for table in TABLES\n        }\n'

(ROOT / "utils/db_connection.py").write_text(DB_CONNECTION, encoding="utf-8")

for rel in [
    "app_pages/crud_operations.py", "app_pages/series_explorer.py",
    "app_pages/sql_queries.py", "app_pages/top_stats.py",
]:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("pd.read_sql_query(", "read_sql_query(")
    if "from utils.db_connection import get_connection" in text:
        text = text.replace(
            "from utils.db_connection import get_connection",
            "from utils.db_connection import get_connection, read_sql_query",
        )
    path.write_text(text, encoding="utf-8")

(ROOT / "app_pages/database_explorer.py").write_text('import streamlit as st\nfrom utils.db_connection import get_connection, read_sql_query, table_counts\n\nTABLES = ["players", "matches", "venues", "series", "player_match_stats"]\n\n\ndef render():\n    st.title("🗄️ Database Explorer")\n    st.caption("Explore your Supabase PostgreSQL database.")\n    try:\n        counts = table_counts()\n        st.subheader("Database Overview")\n        cols = st.columns(len(TABLES))\n        for col, table in zip(cols, TABLES):\n            col.metric(table.replace("_", " ").title(), counts.get(table, 0))\n\n        st.divider()\n        st.subheader("Explore Tables")\n        selected_table = st.selectbox("Select a database table", TABLES, key="database_explorer_table")\n\n        with get_connection() as conn:\n            schema = read_sql_query(\n                """\n                SELECT column_name AS name, data_type AS type,\n                       CASE WHEN is_nullable = \'NO\' THEN 1 ELSE 0 END AS notnull,\n                       CASE WHEN is_identity = \'YES\' OR column_default LIKE \'nextval%%\'\n                            THEN 1 ELSE 0 END AS pk\n                FROM information_schema.columns\n                WHERE table_schema = \'public\' AND table_name = %s\n                ORDER BY ordinal_position\n                """,\n                conn, (selected_table,)\n            )\n            st.subheader("Table Structure")\n            if not schema.empty:\n                st.dataframe(schema[["name", "type", "notnull", "pk"]], width="stretch", hide_index=True)\n\n            limit = st.selectbox("Rows to display", [10, 25, 50, 100, "All"], index=1, key="database_explorer_limit")\n            limit_sql = "" if limit == "All" else f" LIMIT {int(limit)}"\n            data = read_sql_query(\n                f\'SELECT * FROM "{selected_table}" ORDER BY id DESC{limit_sql}\',\n                conn,\n            )\n            st.subheader(f"{selected_table.replace(\'_\', \' \').title()} Records")\n            if data.empty:\n                st.info("This table has no records yet.")\n            else:\n                st.dataframe(data, width="stretch", hide_index=True)\n                st.download_button(\n                    "Download table as CSV",\n                    data=data.to_csv(index=False).encode("utf-8"),\n                    file_name=f"{selected_table}.csv",\n                    mime="text/csv",\n                )\n    except Exception as exc:\n        st.error("Could not load the database explorer.")\n        st.exception(exc)\n\n\nif __name__ == "__main__":\n    render()\n', encoding="utf-8")

for rel in ["main.py", "utils/page_renderer.py", "app_pages/data_import.py", "app_pages/top_stats.py"]:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8-sig")
    for old, new in [
        ("SQLite · local-first", "Supabase PostgreSQL · persistent"),
        ("SQLite database", "Supabase PostgreSQL database"),
        ("saved to SQLite", "saved to Supabase PostgreSQL"),
        ("imported into SQLite", "imported into Supabase PostgreSQL"),
        ("data/cricbuzz_livestats.db", "Supabase PostgreSQL"),
    ]:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

req = ROOT / "requirements.txt"
if req.exists():
    lines = req.read_text(encoding="utf-8-sig").splitlines()
    if not any(line.strip().lower().startswith("psycopg") for line in lines):
        lines.append("psycopg[binary]>=3.2")
    req.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

print("Patch applied. Original files backed up to:", BACKUP)
print("Run: python -m pytest -v")
