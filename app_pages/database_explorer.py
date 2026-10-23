import streamlit as st
from utils.db_connection import get_connection, read_sql_query, table_counts

TABLES = ["players", "matches", "venues", "series", "player_match_stats"]


def render():
    st.title("🗄️ Database Explorer")
    st.caption("Explore your Supabase PostgreSQL database.")
    try:
        counts = table_counts()
        st.subheader("Database Overview")
        cols = st.columns(len(TABLES))
        for col, table in zip(cols, TABLES):
            col.metric(table.replace("_", " ").title(), counts.get(table, 0))

        st.divider()
        st.subheader("Explore Tables")
        selected_table = st.selectbox("Select a database table", TABLES, key="database_explorer_table")

        with get_connection() as conn:
            schema = read_sql_query(
                """
                SELECT column_name AS name, data_type AS type,
                       CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END AS notnull,
                       CASE WHEN is_identity = 'YES' OR column_default LIKE 'nextval%%'
                            THEN 1 ELSE 0 END AS pk
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                conn, (selected_table,)
            )
            st.subheader("Table Structure")
            if not schema.empty:
                st.dataframe(schema[["name", "type", "notnull", "pk"]], width="stretch", hide_index=True)

            limit = st.selectbox("Rows to display", [10, 25, 50, 100, "All"], index=1, key="database_explorer_limit")
            limit_sql = "" if limit == "All" else f" LIMIT {int(limit)}"
            data = read_sql_query(
                f'SELECT * FROM "{selected_table}" ORDER BY id DESC{limit_sql}',
                conn,
            )
            st.subheader(f"{selected_table.replace('_', ' ').title()} Records")
            if data.empty:
                st.info("This table has no records yet.")
            else:
                st.dataframe(data, width="stretch", hide_index=True)
                st.download_button(
                    "Download table as CSV",
                    data=data.to_csv(index=False).encode("utf-8"),
                    file_name=f"{selected_table}.csv",
                    mime="text/csv",
                )
    except Exception as exc:
        st.error("Could not load the database explorer.")
        st.exception(exc)


if __name__ == "__main__":
    render()
