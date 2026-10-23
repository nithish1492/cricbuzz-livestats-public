
import sqlite3
from utils.db_connection import get_connection

conn = get_connection()

try:
    cur = conn.cursor()

    print("\n1. Sample bowling records:")
    cur.execute("""
        SELECT player_name, overs_bowled, runs_conceded,
               wickets, match_external_id
        FROM player_match_stats
        WHERE overs_bowled IS NOT NULL
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(tuple(row))

    print("\n2. Records with missing player IDs:")
    cur.execute("""
        SELECT COUNT(*)
        FROM player_match_stats
        WHERE player_external_id IS NULL
    """)
    print(cur.fetchone()[0])

    print("\n3. Duplicate player-match-role records:")
    cur.execute("""
        SELECT player_external_id, match_external_id,
               raw_json, COUNT(*)
        FROM player_match_stats
        GROUP BY player_external_id, match_external_id, raw_json
        HAVING COUNT(*) > 1
        LIMIT 10
    """)
    duplicates = cur.fetchall()
    print(duplicates if duplicates else "No exact duplicates found.")

finally:
    conn.close()
