from utils.db_connection import get_connection

conn = get_connection()
match_id = "170720"

query = """
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN runs IS NOT NULL THEN 1 ELSE 0 END) AS batting_rows,
    SUM(CASE WHEN wickets IS NOT NULL THEN 1 ELSE 0 END) AS bowling_rows,
    SUM(CASE WHEN runs IS NOT NULL THEN runs ELSE 0 END) AS total_batting_runs,
    SUM(CASE WHEN wickets IS NOT NULL THEN wickets ELSE 0 END) AS total_bowling_wickets
FROM player_match_stats
WHERE match_external_id = ?
"""

row = conn.execute(query, (match_id,)).fetchone()

for label, value in zip(
    ["Total rows", "Batting rows", "Bowling rows",
     "Sum of batting runs", "Sum of bowling wickets"],
    row
):
    print(f"{label}: {value}")

print("\n=== BATTING RECORDS ===")

query = """
SELECT player_name, team, innings_number, runs, balls_faced
FROM player_match_stats
WHERE match_external_id = ? AND runs IS NOT NULL
ORDER BY innings_number, runs DESC
"""

for record in conn.execute(query, (match_id,)):
    print(tuple(record))

conn.close()
