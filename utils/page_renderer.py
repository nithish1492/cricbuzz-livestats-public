import streamlit as st

from utils.db_connection import table_counts


def render_page():
    """Render the Cricbuzz LiveStats professional home dashboard."""

    # --------------------------------------------------
    # Hero banner
    # --------------------------------------------------
    st.html(
        """
        <div style="
            padding: clamp(24px, 4vw, 46px);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 24px;
            background:
                radial-gradient(
                    circle at 90% 10%,
                    rgba(163, 230, 53, 0.13),
                    transparent 30%
                ),
                linear-gradient(
                    125deg,
                    #172a43 0%,
                    #101b2c 65%,
                    #102a38 100%
                );
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.20);
            margin-bottom: 24px;
        ">
            <div style="
                color: #a3e635;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 3px;
                margin-bottom: 18px;
            ">
                CRICKET INTELLIGENCE PLATFORM
            </div>

            <div style="
                color: #f1f5f9;
                font-size: clamp(32px, 4vw, 52px);
                line-height: 1.10;
                font-weight: 850;
                letter-spacing: -1.6px;
                max-width: 900px;
            ">
                Every match. Every metric.
                <br>
                One live workspace.
            </div>

            <div style="
                color: #b7c6d8;
                font-size: 16px;
                line-height: 1.8;
                max-width: 820px;
                margin-top: 20px;
            ">
                Real-time Cricbuzz data, player insights, SQL analytics,
                and cricket records — all together in one workspace.
            </div>

            <div style="
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 25px;
            ">
                <span style="
                    border: 1px solid rgba(163, 230, 53, 0.4);
                    border-radius: 30px;
                    padding: 8px 14px;
                    color: #d9f99d;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 1px;
                ">LIVE DATA</span>

                <span style="
                    border: 1px solid rgba(56, 189, 248, 0.4);
                    border-radius: 30px;
                    padding: 8px 14px;
                    color: #bae6fd;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 1px;
                ">SQL ANALYTICS</span>

                <span style="
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    border-radius: 30px;
                    padding: 8px 14px;
                    color: #d7e1ee;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 1px;
                ">SUPABASE DATABASE</span>
            </div>
        </div>
        """
    )

    # --------------------------------------------------
    # Dashboard metrics
    # --------------------------------------------------
    st.subheader("Your Cricket Overview")
    st.caption(
        "A snapshot of the records currently stored in your database."
    )

    try:
        counts = table_counts()

        metric_columns = st.columns(5)

        metrics = [
            ("Players", counts.get("players", 0), "Player profiles"),
            ("Matches", counts.get("matches", 0), "Match records"),
            ("Venues", counts.get("venues", 0), "Cricket venues"),
            ("Series", counts.get("series", 0), "Series records"),
            (
                "Player Stats",
                counts.get("player_match_stats", 0),
                "Scorecard records",
            ),
        ]

        for column, (label, value, description) in zip(
            metric_columns, metrics
        ):
            with column:
                st.metric(label=label, value=f"{value:,}")
                st.caption(description)

    except Exception:
        st.error("Could not load dashboard statistics.")
        st.exception(Exception("Check your database connection and table_counts()."))
        return

    # --------------------------------------------------
    # Workspace cards
    # --------------------------------------------------
    st.divider()
    st.subheader("Explore Your Workspace")
    st.caption("Choose a module from the sidebar to get started.")

    col1, col2 = st.columns(2)

    with col1:
        st.html(
            """
            <div style="
                padding: 22px;
                border: 1px solid rgba(148, 163, 184, 0.20);
                border-radius: 16px;
                background: rgba(20, 34, 56, 0.72);
                min-height: 145px;
            ">
                <div style="font-size: 25px; margin-bottom: 10px;">
                    🏏
                </div>

                <div style="
                    color: #f1f5f9;
                    font-size: 18px;
                    font-weight: 800;
                    margin-bottom: 8px;
                ">
                    Matches &amp; Player Insights
                </div>

                <div style="color: #9fb0c5; line-height: 1.7;">
                    Browse saved matches, explore player statistics,
                    and review series information.
                </div>
            </div>
            """
        )

    with col2:
        st.html(
            """
            <div style="
                padding: 22px;
                border: 1px solid rgba(148, 163, 184, 0.20);
                border-radius: 16px;
                background: rgba(20, 34, 56, 0.72);
                min-height: 145px;
            ">
                <div style="font-size: 25px; margin-bottom: 10px;">
                    📊
                </div>

                <div style="
                    color: #f1f5f9;
                    font-size: 18px;
                    font-weight: 800;
                    margin-bottom: 8px;
                ">
                    SQL Analytics &amp; Data Management
                </div>

                <div style="color: #9fb0c5; line-height: 1.7;">
                    Run predefined cricket analytics, manage player
                    records, and inspect database tables.
                </div>
            </div>
            """
        )

    # --------------------------------------------------
    # Getting started
    # --------------------------------------------------
    st.divider()
    st.subheader("Getting Started")

    st.markdown(
        """
        1. **Live Matches** — browse match records already saved.
        2. **Top Player Stats** — explore available player performance data.
        3. **SQL Queries Analytics** — run the predefined cricket queries.
        4. **Data Import** — fetch and save data from the configured Cricbuzz API.
        5. **Database Explorer** — inspect database tables and export records.
        """
    )

    st.info(
        "Data shown here comes from the connected database. "
        "Use Data Import to refresh API-sourced records."
    )
