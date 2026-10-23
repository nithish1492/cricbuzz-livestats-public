
import streamlit as st
import pandas as pd

from utils.db_connection import get_connection, read_sql_query


def render():
    st.title("🛠️ CRUD Operations")
    st.write("Create, read, update, and delete cricket database records.")

    tab_players, tab_matches = st.tabs(["Players", "Matches"])

    with tab_players:
        st.subheader("Player Records")

        # CREATE
        with st.expander("➕ Add Player", expanded=True):
            with st.form("add_player_form"):
                external_id = st.text_input("Player External ID")
                full_name = st.text_input("Full Name")
                country = st.text_input("Country")
                role = st.text_input("Playing Role")

                add_clicked = st.form_submit_button("Add Player")

                if add_clicked:
                    if not full_name.strip():
                        st.error("Full Name is required.")
                    else:
                        try:
                            with get_connection() as conn:
                                conn.execute(
                                    """
                                    INSERT INTO players
                                    (external_id, full_name, country, playing_role)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (
                                        external_id.strip() or None,
                                        full_name.strip(),
                                        country.strip() or None,
                                        role.strip() or None,
                                    ),
                                )
                            st.success("Player added successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not add player: {exc}")

        # READ
        try:
            with get_connection() as conn:
                players = read_sql_query(
                    """
                    SELECT id, external_id, full_name, country,
                           playing_role, batting_style, bowling_style
                    FROM players
                    ORDER BY id DESC
                    """,
                    conn,
                )

            st.dataframe(
                players,
                width="stretch",
                hide_index=True,
            )

            if not players.empty:
                player_ids = players["id"].tolist()

                # UPDATE
                st.subheader("Update Player")
                selected_id = st.selectbox(
                    "Select player ID to update",
                    player_ids,
                    key="update_player_id",
                )
                current = players[players["id"] == selected_id].iloc[0]

                with st.form("update_player_form"):
                    new_name = st.text_input(
                        "Full Name",
                        value=str(current["full_name"] or ""),
                    )
                    new_country = st.text_input(
                        "Country",
                        value=str(current["country"] or ""),
                    )
                    new_role = st.text_input(
                        "Playing Role",
                        value=str(current["playing_role"] or ""),
                    )

                    update_clicked = st.form_submit_button("Update Player")

                    if update_clicked:
                        if not new_name.strip():
                            st.error("Full Name is required.")
                        else:
                            try:
                                with get_connection() as conn:
                                    conn.execute(
                                        """
                                        UPDATE players
                                        SET full_name = ?, country = ?,
                                            playing_role = ?
                                        WHERE id = ?
                                        """,
                                        (
                                            new_name.strip(),
                                            new_country.strip() or None,
                                            new_role.strip() or None,
                                            selected_id,
                                        ),
                                    )
                                st.success("Player updated.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not update player: {exc}")

                # DELETE
                st.subheader("Delete Player")
                delete_id = st.selectbox(
                    "Select player ID to delete",
                    player_ids,
                    key="delete_player_id",
                    format_func=lambda pid: (
                        f"{pid} — "
                        f"{players.loc[players['id'] == pid, 'full_name'].iloc[0]}"
                    ),
                )

                confirm_delete = st.checkbox(
                    "I confirm that I want to delete this player.",
                    key="confirm_delete_player",
                )

                if st.button("Delete Selected Player", type="secondary"):
                    if not confirm_delete:
                        st.warning("Confirm deletion first.")
                    else:
                        try:
                            with get_connection() as conn:
                                conn.execute(
                                    "DELETE FROM players WHERE id = ?",
                                    (delete_id,),
                                )
                            st.success("Player deleted.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not delete player: {exc}")

            else:
                st.info("No player records exist yet. Add a player above.")

        except Exception as exc:
            st.error(f"Could not load players: {exc}")

    with tab_matches:
        st.subheader("Match Records")

        try:
            with get_connection() as conn:
                matches = read_sql_query(
                    """
                    SELECT id, external_id, series_name, description,
                           team1, team2, winner, status
                    FROM matches
                    ORDER BY id DESC
                    """,
                    conn,
                )

            st.dataframe(
                matches,
                width="stretch",
                hide_index=True,
            )

            st.caption(
                "Match records are shown here. Editing and deleting matches "
                "can affect linked analytics, so use Data Import to refresh "
                "API-sourced match data."
            )

        except Exception as exc:
            st.error(f"Could not load matches: {exc}")


if __name__ == "__main__":
    render()
