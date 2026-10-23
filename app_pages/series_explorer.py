import streamlit as st
import pandas as pd
from utils.db_connection import get_connection, read_sql_query
from utils.cricbuzz import fetch_series_list,extract_series_records,sync_series

def render():
    st.title("🗓️ Series Explorer")
    if st.button("Fetch and save series"):
        try: st.success(f"Saved {sync_series(extract_series_records(fetch_series_list()))} series.")
        except Exception as e: st.error(f"Series endpoint may need verification: {e}")
    with get_connection() as c: df=read_sql_query("SELECT * FROM series ORDER BY start_date DESC",c)
    st.dataframe(df,width="stretch",hide_index=True)
