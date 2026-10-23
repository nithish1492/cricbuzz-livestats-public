
import streamlit as st
import pandas as pd

from utils.db_connection import get_connection, read_sql_query
from utils.sql_queries import QUERIES


def render():
    st.title("📊 SQL Queries Analytics")
    st.caption("Explore all 25 predefined cricket SQL questions.")

    total_queries = len(QUERIES)
    st.success(f"Total predefined queries loaded: {total_queries}")

    if total_queries == 0:
        st.error("No queries found in utils/sql_queries.py.")
        return

    # Display every query as a separate numbered option.
    query_names = [name for name, sql in QUERIES]

    st.write(f"Available questions: {total_queries}")

    selected_name = st.selectbox(
        "Choose a query",
        options=query_names,
        index=0,
        key="sql_query_selector_v2",
    )

    selected_sql = dict(QUERIES)[selected_name]

    st.subheader(selected_name)
    st.code(selected_sql, language="sql")

    if st.button("▶ Run Selected Query", type="primary"):
        try:
            with get_connection() as connection:
                result = read_sql_query(selected_sql, connection)

            st.success(f"Query completed: {len(result)} rows returned.")
            st.dataframe(
                result,
                width="stretch",
                hide_index=True,
            )

            st.download_button(
                "Download CSV",
                data=result.to_csv(index=False).encode("utf-8"),
                file_name="cricket_query_results.csv",
                mime="text/csv",
            )

        except Exception as error:
            st.error(f"Query failed: {error}")

    st.divider()
    st.subheader("Custom SQL Query")
    st.caption("Only read-only SELECT queries are permitted.")

    custom_sql = st.text_area(
        "Enter your SQL SELECT statement",
        placeholder="SELECT * FROM matches LIMIT 10",
        key="custom_sql_editor_v2",
    )

    if st.button("Run Custom Query", key="run_custom_sql_v2"):
        statement = custom_sql.strip().rstrip(";")

        # Allow one read-only SELECT or WITH statement.
        if not statement.lower().startswith(("select ", "with ")):
            st.warning("Enter a SELECT query or a read-only WITH query.")
            return

        try:
            with get_connection() as connection:
                result = read_sql_query(statement, connection)

            st.success(f"Query completed: {len(result)} rows returned.")
            st.dataframe(
                result,
                width="stretch",
                hide_index=True,
            )

        except Exception as error:
            st.error(f"Query failed: {error}")
