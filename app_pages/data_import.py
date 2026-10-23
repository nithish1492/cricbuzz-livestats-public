
import streamlit as st

from utils.importer import (
    import_live_matches,
    import_series,
    import_scorecard,
)
from utils.db_connection import table_counts
from utils.api_client import api_configuration


def render():
    st.title("📥 Data Import")
    st.write("Fetch real Cricbuzz data and save it to SQLite.")

    # API configuration
    st.subheader("API Configuration")
    try:
        config = api_configuration()
        if config.get("configured"):
            st.success("RapidAPI configuration detected.")
        else:
            st.warning("Configure your RapidAPI key in .env.")

        st.caption(f"API base URL: {config.get('base_url', 'Unknown')}")
    except Exception as exc:
        st.error(f"API configuration error: {exc}")

    st.divider()

    # Live matches
    st.subheader("1. Live Matches")
    if st.button("Fetch & Save Live Matches", type="primary"):
        with st.spinner("Fetching live matches..."):
            try:
                count, payload = import_live_matches()
                st.success(f"Saved or updated {count} matches.")
                if isinstance(payload, dict):
                    st.json({
                        "records_saved": count,
                        "responseLastUpdated": payload.get(
                            "responseLastUpdated"
                        ),
                    })
            except Exception as exc:
                st.error(f"Live match import failed: {exc}")

    st.divider()

    # Series
    st.subheader("2. Series")
    if st.button("Fetch & Save Series"):
        with st.spinner("Fetching series..."):
            try:
                count, _payload = import_series()
                st.success(f"Saved or updated {count} series.")
            except Exception as exc:
                st.error(f"Series import failed: {exc}")

    st.divider()

    # Scorecard
    st.subheader("3. Scorecard")
    match_id = st.text_input(
        "Match ID",
        value="170720",
        placeholder="Enter a match ID from Live Matches",
        key="scorecard_match_id",
    )

    if st.button("Fetch & Save Scorecard"):
        if not match_id.strip():
            st.warning("Enter a match ID first.")
        else:
            with st.spinner("Fetching scorecard..."):
                try:
                    count, payload = import_scorecard(match_id.strip())

                    if count:
                        st.success(f"Saved {count} scorecard rows.")
                    else:
                        st.warning(
                            "No scorecard rows were recognized by the parser."
                        )

                    # Keep the API response in session state so it
                    # remains visible after Streamlit reruns.
                    st.session_state["last_scorecard_payload"] = payload
                    st.session_state["last_scorecard_match_id"] = match_id.strip()
                    st.session_state["last_scorecard_count"] = count

                except Exception as exc:
                    st.error(f"Scorecard import failed: {exc}")

    # Display the last response outside the button block.
    # This makes it persist across normal Streamlit reruns.
    if "last_scorecard_payload" in st.session_state:
        payload = st.session_state["last_scorecard_payload"]

        st.divider()
        st.subheader("Scorecard API Debug")
        st.caption(
            f"Last response for match "
            f"{st.session_state.get('last_scorecard_match_id', '')}"
        )

        if isinstance(payload, dict):
            st.write("Top-level fields:", list(payload.keys()))

            scorecards = payload.get(
                "scorecard",
                payload.get("scoreCard", []),
            )

            if isinstance(scorecards, list) and scorecards:
                first_innings = scorecards[0]

                if isinstance(first_innings, dict):
                    st.write(
                        "First innings fields:",
                        list(first_innings.keys()),
                    )

                    # Cricbuzz responses may use a list of batsmen,
                    # or a dictionary keyed by player ID.
                    batsmen = first_innings.get(
                        "batsman",
                        first_innings.get("batsmen", []),
                    )
                    bowlers = first_innings.get(
                        "bowlers",
                        first_innings.get("bowler", []),
                    )

                    if isinstance(batsmen, dict):
                        batsmen = list(batsmen.values())
                    if isinstance(bowlers, dict):
                        bowlers = list(bowlers.values())

                    if isinstance(batsmen, list) and batsmen:
                        st.markdown("#### First batsman")
                        st.json(batsmen[0], expanded=True)
                    else:
                        st.info(
                            "No direct batsman list found in the first "
                            "scorecard entry. Inspect the full JSON below."
                        )

                    if isinstance(bowlers, list) and bowlers:
                        st.markdown("#### First bowler")
                        st.json(bowlers[0], expanded=True)
            else:
                st.info(
                    "The response has no top-level scorecard list under "
                    "'scorecard' or 'scoreCard'. Inspect the full JSON."
                )

        with st.expander("View complete API response", expanded=True):
            st.json(payload, expanded=True)

    st.divider()

    # Database counts
    st.subheader("4. Database Counts")
    try:
        st.json(table_counts())
    except Exception as exc:
        st.error(f"Could not read database counts: {exc}")


if __name__ == "__main__":
    render()
