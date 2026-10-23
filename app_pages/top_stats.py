
import sqlite3

import pandas as pd
import streamlit as st

from utils.db_connection import get_connection, read_sql_query


def load_player_statistics():
    """Load aggregated player statistics from imported scorecards."""
    query = """
        SELECT
            s.player_external_id AS player_id,
            MAX(
                COALESCE(NULLIF(p.full_name, ''), s.player_name)
            ) AS player_name,
            COUNT(s.id) AS innings_records,
            COUNT(DISTINCT s.match_external_id) AS matches_recorded,
            COALESCE(SUM(s.runs), 0) AS total_runs,
            COALESCE(MAX(s.runs), 0) AS highest_score,
            COALESCE(SUM(s.balls_faced), 0) AS balls_faced,
            COALESCE(SUM(s.fours), 0) AS total_fours,
            COALESCE(SUM(s.sixes), 0) AS total_sixes,
            COALESCE(SUM(s.wickets), 0) AS total_wickets,
            COALESCE(SUM(s.runs_conceded), 0) AS runs_conceded,
            COALESCE(SUM(s.overs_bowled), 0) AS overs_bowled,
            COALESCE(SUM(s.catches), 0) AS catches,
            COALESCE(SUM(s.stumpings), 0) AS stumpings
        FROM player_match_stats AS s
        LEFT JOIN players AS p
            ON p.external_id = s.player_external_id
        GROUP BY s.player_external_id
        ORDER BY total_runs DESC, player_name ASC
    """

    conn = get_connection()
    try:
        return read_sql_query(query, conn)
    finally:
        conn.close()


def prepare_statistics(players):
    """Calculate derived metrics for imported player records."""
    if players.empty:
        return players

    numeric_columns = [
        "innings_records",
        "matches_recorded",
        "total_runs",
        "highest_score",
        "balls_faced",
        "total_fours",
        "total_sixes",
        "total_wickets",
        "runs_conceded",
        "overs_bowled",
        "catches",
        "stumpings",
    ]

    for column in numeric_columns:
        players[column] = pd.to_numeric(
            players[column], errors="coerce"
        ).fillna(0)

    # Batting strike rate = runs per 100 balls faced.
    players["strike_rate"] = (
        players["total_runs"] * 100 / players["balls_faced"]
    ).where(players["balls_faced"] > 0).round(2)

    # This is not official batting average because dismissals
    # are not stored in the current database schema.
    players["runs_per_innings_record"] = (
        players["total_runs"] / players["innings_records"]
    ).where(players["innings_records"] > 0).round(2)

    # Convert cricket overs notation into actual balls.
    # Example: 3.5 means 3 overs and 5 balls, or 23 balls.
    overs = players["overs_bowled"].fillna(0).clip(lower=0)
    whole_overs = overs.apply(int)
    extra_balls = ((overs - whole_overs) * 10).round().astype(int)

    # Protect against invalid overs notation such as 3.8.
    invalid_overs = extra_balls >= 6
    if invalid_overs.any():
        st.warning(
            "Some bowling-over values contain an invalid balls component. "
            "Check the imported scorecard data for those records."
        )

    total_balls_bowled = whole_overs * 6 + extra_balls

    # Economy rate = runs conceded per 6 legal balls.
    players["bowling_economy_estimate"] = (
        players["runs_conceded"] * 6 / total_balls_bowled
    ).where(total_balls_bowled > 0).round(2)

    return players.sort_values(
        ["total_runs", "player_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def render():
    """Render the Top Player Stats dashboard."""
    st.title("🏆 Top Player Stats")
    st.caption(
        "Statistics aggregated from scorecards imported into Supabase PostgreSQL."
    )

    try:
        players = prepare_statistics(load_player_statistics())
    except (sqlite3.Error, pd.errors.DatabaseError):
        st.error(
            "Could not read player statistics from the database. "
            "Check the database connection and schema."
        )
        return
    except Exception as exc:
        st.error("Could not load player statistics.")
        st.exception(exc)
        return

    if players.empty:
        st.warning(
            "No player statistics are available yet. "
            "Open Data Import and fetch a scorecard first."
        )
        return

    players = players[
        players["player_name"].notna()
        & (players["player_name"].astype(str).str.strip() != "")
    ].copy()

    if players.empty:
        st.warning("No named players were found in the imported records.")
        return

    st.success(
        f"Loaded imported statistics for {len(players)} players."
    )

    st.info(
        "These figures cover records saved in this database, not necessarily "
        "complete career statistics. Results depend on which matches and "
        "innings have been imported."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Players with records", len(players))
    col2.metric(
        "Runs in imported records",
        int(players["total_runs"].sum()),
    )
    col3.metric(
        "Wickets in imported records",
        int(players["total_wickets"].sum()),
    )
    col4.metric(
        "Player-match appearances",
        int(players["matches_recorded"].sum()),
    )

    st.subheader("Top run scorers")
    run_leaders = players.nlargest(10, "total_runs").sort_values(
        "total_runs", ascending=True
    )
    st.bar_chart(run_leaders.set_index("player_name")["total_runs"])

    st.subheader("Highest individual scores in imported records")
    score_leaders = players.nlargest(10, "highest_score").sort_values(
        "highest_score", ascending=True
    )
    st.bar_chart(score_leaders.set_index("player_name")["highest_score"])

    st.subheader("Top wicket takers")
    wicket_leaders = players.nlargest(10, "total_wickets").sort_values(
        "total_wickets", ascending=True
    )
    st.bar_chart(wicket_leaders.set_index("player_name")["total_wickets"])

    st.subheader("Player statistics")
    st.caption(
        "Runs per innings record is not official batting average. "
        "Bowling economy is calculated from the stored overs notation; "
        "check imported data if an overs value is invalid."
    )

    display_columns = [
        "player_id",
        "player_name",
        "matches_recorded",
        "innings_records",
        "total_runs",
        "highest_score",
        "balls_faced",
        "strike_rate",
        "runs_per_innings_record",
        "total_fours",
        "total_sixes",
        "total_wickets",
        "runs_conceded",
        "overs_bowled",
        "bowling_economy_estimate",
        "catches",
        "stumpings",
    ]

    st.dataframe(
        players[display_columns],
        width="stretch",
        hide_index=True,
    )

    csv_data = players[display_columns].to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download player statistics CSV",
        data=csv_data,
        file_name="cricbuzz_player_stats.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    render()
