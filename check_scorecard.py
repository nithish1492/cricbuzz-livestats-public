import sqlite3

DATABASE_PATH = "data/cricbuzz_livestats.db"
MATCH_ID = "170720"

db = sqlite3.connect(DATABASE_PATH)

try:
    match = db.execute(
        """
        SELECT team1, team2
        FROM matches
        WHERE external_id = ?
        """,
        (MATCH_ID,),
    ).fetchone()

    if not match:
        print(f"Match {MATCH_ID} not found.")
    else:
        team1, team2 = match

        # Innings 1: Pakistan bats, Sri Lanka bowls.
        # Innings 2: Sri Lanka bats, Pakistan bowls.
        updates = [
            (team2, MATCH_ID, 1),
            (team1, MATCH_ID, 2),
        ]

        db.execute(
            """
            UPDATE player_match_stats
            SET team = ?
            WHERE match_external_id = ?
              AND innings_number = ?
              AND team IS NULL
              AND wickets IS NOT NULL
            """,
            updates[0],
        )

        db.execute(
            """
            UPDATE player_match_stats
            SET team = ?
            WHERE match_external_id = ?
              AND innings_number = ?
              AND team IS NULL
              AND wickets IS NOT NULL
            """,
            updates[1],
        )

        db.commit()

        print("Team names updated successfully!")

        rows = db.execute(
            """
            SELECT player_name, innings_number, team,
                   wickets, runs_conceded
            FROM player_match_stats
            WHERE match_external_id = ?
              AND wickets IS NOT NULL
            ORDER BY innings_number, player_name
            """,
            (MATCH_ID,),
        ).fetchall()

        print("\nUPDATED BOWLING SCORECARD")
        print("-" * 75)

        for row in rows:
            print(row)

        missing = db.execute(
            """
            SELECT COUNT(*)
            FROM player_match_stats
            WHERE match_external_id = ?
              AND wickets IS NOT NULL
              AND team IS NULL
            """,
            (MATCH_ID,),
        ).fetchone()[0]

        print(f"\nBowling records with missing teams: {missing}")

finally:
    db.close()