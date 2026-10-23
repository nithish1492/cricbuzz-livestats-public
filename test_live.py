
import streamlit as st

st.set_page_config(page_title="Live Matches Test", layout="wide")
st.title("Live Matches Diagnostic")

try:
    from app_pages import live_matches

    st.success("Live Matches module imported successfully.")

    if callable(getattr(live_matches, "render", None)):
        st.write("The render() function exists.")
        live_matches.render()
    else:
        st.error("The module has no render() function.")

except Exception as exc:
    st.error(f"{type(exc).__name__}: {exc}")
    st.exception(exc)
