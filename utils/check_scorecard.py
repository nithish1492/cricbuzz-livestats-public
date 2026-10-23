
from utils.db_connection import get_connection

conn = get_connection()

print("Rows by type:")
query = """
SELECT
    CASE
        WHEN runs IS NOT NULL THEN 'Batting'
        WHEN wickets IS NOT NULL THEN 'Bowling'
        ELSE 'Other'
    END AS record_type,
    COUNT(*)
FROM player_match_stats
WHERE match_external_id = ?
GROUP BY record_type
"""

for row in conn.execute(query, ("170720",)):
    print(tuple(row))

print("\nSample records:")
query = """
SELECT player_name, innings_number, runs, balls_faced,
       wickets, runs_conceded
FROM player_match_stats
WHERE match_external_id = ?
LIMIT 10
"""

for row in conn.execute(query, ("170720",)):
    print(tuple(row))

conn.close()
