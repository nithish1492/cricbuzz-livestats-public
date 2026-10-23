import pandas as pd
import streamlit as st

from utils.db_connection import get_connection


def render():
    """Render saved match records with search and CSV export."""
    st.title("🏏 Live Matches")
    st.caption("Matches imported from the Cricbuzz API.")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("🔄 Refresh Database View", width="stretch"):
            st.rerun()

    with col2:
        search = st.text_input(
            "Search matches",
            placeholder="Search by team, series, or match description",
        )

    try:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM matches ORDER BY id DESC"
            ).fetchall()
            df = pd.DataFrame([dict(row) for row in rows])
        finally:
            conn.close()

        if df.empty:
            st.warning(
                "No matches are saved yet. Open **Data Import** and fetch "
                "live matches first."
            )
            return

        if search.strip():
            searchable = df.fillna("").astype(str)
            mask = searchable.apply(
                lambda column: column.str.contains(
                    search.strip(), case=False, regex=False
                )
            ).any(axis=1)
            df = df.loc[mask]

        st.success(f"{len(df)} match record(s) found.")

        st.dataframe(df, width="stretch", hide_index=True)

        st.download_button(
            "⬇️ Download matches as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="cricbuzz_matches.csv",
            mime="text/csv",
        )

    except Exception as exc:
        st.error("Could not load matches from the local database.")
        st.exception(exc)
