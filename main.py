
import importlib
import streamlit as st

from utils.db_connection import init_db, table_counts
from utils.page_renderer import render_page


# --------------------------------------------------
# Page configuration — must be first Streamlit command
# --------------------------------------------------
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
)


# --------------------------------------------------
# Database initialization
# --------------------------------------------------
try:
    init_db()
except Exception as exc:
    st.error("Database initialization failed.")
    st.exception(exc)
    st.stop()


# --------------------------------------------------
# Application pages
# --------------------------------------------------
PAGES = {
    "Home": None,
    "Live Matches": "app_pages.live_matches",
    "Top Player Stats": "app_pages.top_stats",
    "SQL Queries Analytics": "app_pages.sql_queries",
    "CRUD Operations": "app_pages.crud_operations",
    "Series Explorer": "app_pages.series_explorer",
    "Data Import": "app_pages.data_import",
    "Database Explorer": "app_pages.database_explorer",
}


# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------
with st.sidebar:
    st.markdown("## 🏏 Cricbuzz")
    st.caption("LIVESTATS · ANALYTICS")
    st.divider()

    choice = st.radio(
        "Navigation",
        options=list(PAGES.keys()),
        label_visibility="collapsed",
        key="main_navigation",
    )


    st.divider()

    try:
        counts = table_counts()
        players = counts.get("players", 0)
        matches = counts.get("matches", 0)

        st.caption(f"{players} players · {matches} matches")
    except Exception as exc:
        st.warning(f"Database counts unavailable: {exc}")

    st.caption("Supabase PostgreSQL · persistent")


# --------------------------------------------------
# Render selected page
# --------------------------------------------------
if choice == "Home":
    try:
        render_page()
    except Exception as exc:
        st.error("Could not render the Home page.")
        st.exception(exc)

else:
    module_name = PAGES[choice]

    try:
        module = importlib.import_module(module_name)

        # Different page modules may expose different function names.
        page_function = getattr(module, "render_page", None)

        if not callable(page_function):
            page_function = getattr(module, "render", None)

        if callable(page_function):
            page_function()
        else:
            st.error(
                f"The page '{choice}' does not define a callable "
                "render() or render_page() function."
            )

    except Exception as exc:
        st.error(f"Could not open the '{choice}' page.")
        st.exception(exc)
