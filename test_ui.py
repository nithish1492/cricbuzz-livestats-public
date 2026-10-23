
import streamlit as st

st.set_page_config(page_title="Home Page Test", layout="wide")
st.title("Home Page Diagnostic")

try:
    from utils.db_connection import init_db, table_counts

    st.write("Step 1: Database module imported successfully.")

    init_db()
    st.write("Step 2: Database initialized successfully.")

    counts = table_counts()
    st.write("Step 3: Database counts loaded successfully.")
    st.json(counts)

    from utils.page_renderer import render_page
    st.write("Step 4: Page renderer imported successfully.")

    render_page()
    st.success("Step 5: Home page rendered successfully.")

except Exception as e:
    st.error(f"Error: {type(e).__name__}: {e}")
    st.exception(e)
