
QUERIES = [
    (
        "Q1 - All matches",
        """SELECT external_id, series_name, description, team1, team2, winner, status
           FROM matches ORDER BY id DESC"""
    ),
    (
        "Q2 - Total matches by series",
        """SELECT COALESCE(series_name, 'Unknown') AS series_name,
                  COUNT(*) AS total_matches
           FROM matches
           GROUP BY series_name
           ORDER BY total_matches DESC"""
    ),
    (
        "Q3 - Top run scorers",
        """SELECT player_name, SUM(COALESCE(runs, 0)) AS total_runs
           FROM player_match_stats
           GROUP BY player_name
           ORDER BY total_runs DESC LIMIT 10"""
    ),
    (
        "Q4 - Top wicket takers",
        """SELECT player_name, SUM(COALESCE(wickets, 0)) AS total_wickets
           FROM player_match_stats
           GROUP BY player_name
           ORDER BY total_wickets DESC LIMIT 10"""
    ),
    (
        "Q5 - Most sixes",
        """SELECT player_name, SUM(COALESCE(sixes, 0)) AS total_sixes
           FROM player_match_stats
           GROUP BY player_name
           ORDER BY total_sixes DESC LIMIT 10"""
    ),
    (
        "Q6 - Player scorecard records",
        """SELECT player_name, match_external_id, innings_number,
                  runs, balls_faced, fours, sixes, wickets
           FROM player_match_stats
           ORDER BY runs DESC"""
    ),
    (
        "Q7 - Matches by team",
        """SELECT team, COUNT(*) AS match_count
           FROM (
               SELECT team1 AS team FROM matches WHERE team1 IS NOT NULL
               UNION ALL
               SELECT team2 AS team FROM matches WHERE team2 IS NOT NULL
           )
           GROUP BY team
           ORDER BY match_count DESC"""
    ),
    (
        "Q8 - Venue summary",
        """SELECT venue, venue_city, venue_country,
                  COUNT(*) AS match_count
           FROM matches
           GROUP BY venue, venue_city, venue_country
           ORDER BY match_count DESC"""
    ),
    (
        "Q9 - Player batting strike rate",
        """SELECT player_name,
                  ROUND(
                      100.0 * SUM(COALESCE(runs, 0)) /
                      NULLIF(SUM(COALESCE(balls_faced, 0)), 0), 2
                  ) AS calculated_strike_rate
           FROM player_match_stats
           GROUP BY player_name
           HAVING SUM(COALESCE(balls_faced, 0)) > 0
           ORDER BY calculated_strike_rate DESC"""
    ),
    (
        "Q10 - Match results",
        """SELECT series_name, description, team1, team2, winner,
                  victory_margin, victory_type, status
           FROM matches
           WHERE TRIM(COALESCE(winner, '')) <> ''
           ORDER BY match_date DESC"""
    ),
    (
        "Q11 - Matches by format",
        """SELECT COALESCE(format, 'Unknown') AS format,
                  COUNT(*) AS total_matches
           FROM matches
           GROUP BY format
           ORDER BY total_matches DESC"""
    ),
    (
        "Q12 - Player innings scores",
        """SELECT player_name, match_external_id, innings_number, runs
           FROM player_match_stats
           ORDER BY runs DESC"""
    ),
    (
        "Q13 - Highest innings scores",
        """SELECT player_name, MAX(runs) AS highest_score
           FROM player_match_stats
           WHERE runs IS NOT NULL
           GROUP BY player_name
           ORDER BY highest_score DESC LIMIT 10"""
    ),
    (
        "Q14 - Bowling economy at venues",
        """SELECT p.player_name, m.venue,
                  ROUND(AVG(p.economy_rate), 2) AS avg_economy,
                  SUM(COALESCE(p.wickets, 0)) AS total_wickets
           FROM player_match_stats p
           JOIN matches m
             ON p.match_external_id = m.external_id
           WHERE p.economy_rate IS NOT NULL
           GROUP BY p.player_name, m.venue
           ORDER BY avg_economy ASC"""
    ),
    (
        "Q15 - Player match records",
        """SELECT player_name,
                  ROUND(AVG(runs), 2) AS avg_runs,
                  COUNT(DISTINCT match_external_id) AS matches_played
           FROM player_match_stats
           GROUP BY player_name
           ORDER BY avg_runs DESC"""
    ),
    (
        "Q16 - Annual trends",
        """SELECT substr(match_date, 1, 4) AS year,
                  COUNT(*) AS total_matches
           FROM matches
           WHERE match_date IS NOT NULL AND TRIM(match_date) <> ''
           GROUP BY year
           ORDER BY year"""
    ),
    (
        "Q17 - Toss advantage",
        """SELECT toss_winner,
                  COUNT(*) AS toss_wins,
                  SUM(
                      CASE WHEN winner = toss_winner THEN 1 ELSE 0 END
                  ) AS wins_after_toss
           FROM matches
           WHERE TRIM(COALESCE(toss_winner, '')) <> ''
           GROUP BY toss_winner
           ORDER BY toss_wins DESC"""
    ),
    (
        "Q18 - Economy limited overs",
        """SELECT p.player_name,
                  ROUND(AVG(p.economy_rate), 2) AS avg_economy,
                  SUM(COALESCE(p.wickets, 0)) AS total_wickets
           FROM player_match_stats p
           JOIN matches m
             ON p.match_external_id = m.external_id
           WHERE m.format LIKE '%ODI%'
              OR m.format LIKE '%T20%'
              OR m.format LIKE '%LIMITED%'
           GROUP BY p.player_name
           HAVING AVG(p.economy_rate) IS NOT NULL
           ORDER BY avg_economy ASC"""
    ),
    (
        "Q19 - Player consistency",
        """SELECT player_name,
                  ROUND(AVG(runs), 2) AS avg_runs,
                  MAX(runs) AS highest_score,
                  MIN(runs) AS lowest_score,
                  COUNT(runs) AS recorded_scores
           FROM player_match_stats
           WHERE runs IS NOT NULL
           GROUP BY player_name
           ORDER BY avg_runs DESC"""
    ),
    (
        "Q20 - Format participation",
        """SELECT COALESCE(format, 'Unknown') AS format,
                  COUNT(*) AS match_count
           FROM matches
           GROUP BY format
           ORDER BY match_count DESC"""
    ),
    (
        "Q21 - Weighted available stats",
        """SELECT player_name,
                  SUM(COALESCE(runs, 0)) AS total_runs,
                  SUM(COALESCE(wickets, 0)) AS total_wickets,
                  SUM(COALESCE(sixes, 0)) AS total_sixes
           FROM player_match_stats
           GROUP BY player_name
           ORDER BY total_runs DESC"""
    ),
    (
        "Q22 - Head to head",
        """SELECT
                  CASE WHEN team1 <= team2 THEN team1 ELSE team2 END AS team_a,
                  CASE WHEN team1 <= team2 THEN team2 ELSE team1 END AS team_b,
                  COUNT(*) AS matches_played
           FROM matches
           WHERE team1 IS NOT NULL AND team2 IS NOT NULL
           GROUP BY team_a, team_b
           ORDER BY matches_played DESC"""
    ),
    (
        "Q23 - Recent form",
        """SELECT player_name, match_date, runs, wickets
           FROM player_match_stats
           WHERE match_date IS NOT NULL AND TRIM(match_date) <> ''
           ORDER BY match_date DESC, id DESC
           LIMIT 20"""
    ),
    (
        "Q24 - Highest individual scores",
        """SELECT player_name, match_external_id, innings_number,
                  runs AS individual_score
           FROM player_match_stats
           WHERE runs IS NOT NULL
           ORDER BY individual_score DESC
           LIMIT 10"""
    ),
    (
        "Q25 - Quarterly trend",
        """SELECT substr(match_date, 1, 4) AS year,
                  ((CAST(substr(match_date, 6, 2) AS INTEGER) - 1) / 3) + 1
                      AS quarter,
                  COUNT(*) AS total_matches
           FROM matches
           WHERE match_date IS NOT NULL
             AND length(match_date) >= 7
             AND substr(match_date, 6, 2) GLOB '[0-9][0-9]'
           GROUP BY year, quarter
           ORDER BY year, quarter"""
    ),
]
