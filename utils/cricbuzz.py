import json
from datetime import datetime, timezone

from .api_client import (
    fetch_live_matches as api_live,
    fetch_livescore as api_score,
    fetch_scorecard as api_card,
    fetch_series_list as api_series,
)
from .db_connection import get_connection


# =========================================================
# API FUNCTIONS
# =========================================================

def fetch_live_matches():
    return api_live()


def fetch_livescore(match_id):
    return api_score(match_id)


def fetch_scorecard(match_id):
    return api_card(match_id)


def fetch_series_list():
    return api_series()


# =========================================================
# HELPERS
# =========================================================

def _date(value):
    if value in (None, ""):
        return None

    try:
        number = int(float(value))

        if number > 10_000_000_000:
            number //= 1000

        return datetime.fromtimestamp(
            number, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

    except (ValueError, TypeError, OSError, OverflowError):
        return str(value)


def _number(value):
    if value in (None, "", "-"):
        return None

    try:
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return None


def _first_number(player, *keys):
    for key in keys:
        value = _number(player.get(key))
        if value is not None:
            return value

    return None


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)

    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _player_name(player):
    return (
        player.get("name")
        or player.get("fullName")
        or player.get("playerName")
        or player.get("nickname")
    )


def _player_id(player):
    value = (
        player.get("id")
        or player.get("batId")
        or player.get("bowlId")
        or player.get("playerId")
    )

    return str(value) if value is not None else None


def _team_name(value):
    if isinstance(value, dict):
        return (
            value.get("teamName")
            or value.get("name")
            or value.get("team")
            or value.get("batTeamName")
            or value.get("bowlTeamName")
        )

    if isinstance(value, str):
        return value.strip() or None

    return None


def _innings_number(value, fallback):
    try:
        return int(value)
    except (ValueError, TypeError):
        return fallback


def _find_team_name(innings, role):
    if role == "bat":
        keys = (
            "batteam",
            "batTeam",
            "batTeamDetails",
            "batteamdetails",
            "batTeamName",
            "batteamname",
        )
    else:
        keys = (
            "bowlteam",
            "bowlTeam",
            "bowlTeamDetails",
            "bowlteamdetails",
            "bowlTeamName",
            "bowlteamname",
        )

    for key in keys:
        name = _team_name(innings.get(key))
        if name:
            return name

    return None


def _player_list(innings, *keys):
    """Return the first valid player list for a category."""
    for key in keys:
        value = innings.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            # Some API versions use a dictionary keyed by player ID.
            return list(value.values())

    return []


def _safe_json(value):
    return json.dumps(value, ensure_ascii=False, default=str)


# =========================================================
# LIVE MATCH EXTRACTION
# =========================================================

def extract_match_records(payload):
    rows = []

    if not isinstance(payload, dict):
        return rows

    for group in payload.get("typeMatches", []):
        if not isinstance(group, dict):
            continue

        category = group.get("matchType")

        for series_group in group.get("seriesMatches", []):
            if not isinstance(series_group, dict):
                continue

            wrapper = series_group.get("seriesAdWrapper")
            if not isinstance(wrapper, dict):
                continue

            for item in wrapper.get("matches", []):
                if not isinstance(item, dict):
                    continue

                info = item.get("matchInfo", {})
                if not isinstance(info, dict):
                    continue

                match_id = info.get("matchId")
                if match_id is None:
                    continue

                team1 = info.get("team1") or {}
                team2 = info.get("team2") or {}
                venue = info.get("venueInfo") or {}

                series_id = info.get(
                    "seriesId", wrapper.get("seriesId")
                )

                rows.append({
                    "external_id": str(match_id),
                    "series_external_id": (
                        str(series_id)
                        if series_id is not None else None
                    ),
                    "series_name": info.get(
                        "seriesName", wrapper.get("seriesName")
                    ),
                    "description": info.get("matchDesc"),
                    "team1": team1.get("teamName"),
                    "team2": team2.get("teamName"),
                    "winner": info.get("winner"),
                    "venue": venue.get("ground"),
                    "venue_city": venue.get("city"),
                    "venue_country": venue.get("country"),
                    "match_date": _date(info.get("startDate")),
                    "format": info.get("matchFormat") or category,
                    "status": info.get("status"),
                    "toss_winner": info.get("tossWinner"),
                    "toss_decision": info.get("tossDecision"),
                    "victory_margin": info.get("victoryMargin"),
                    "victory_type": info.get("victoryType"),
                    "raw_state": (
                        info.get("state")
                        or info.get("stateTitle")
                        or category
                    ),
                })

    return rows


def sync_matches(rows):
    saved = 0

    with get_connection() as connection:
        for row in rows:
            connection.execute(
                """
                INSERT INTO matches (
                    external_id, series_external_id, series_name,
                    description, team1, team2, winner, venue,
                    venue_city, venue_country, match_date, format,
                    status, toss_winner, toss_decision,
                    victory_margin, victory_type, raw_state
                )
                VALUES (
                    :external_id, :series_external_id, :series_name,
                    :description, :team1, :team2, :winner, :venue,
                    :venue_city, :venue_country, :match_date, :format,
                    :status, :toss_winner, :toss_decision,
                    :victory_margin, :victory_type, :raw_state
                )
                ON CONFLICT(external_id) DO UPDATE SET
                    series_external_id = COALESCE(
                        excluded.series_external_id,
                        matches.series_external_id
                    ),
                    series_name = COALESCE(
                        excluded.series_name, matches.series_name
                    ),
                    description = COALESCE(
                        excluded.description, matches.description
                    ),
                    team1 = COALESCE(excluded.team1, matches.team1),
                    team2 = COALESCE(excluded.team2, matches.team2),
                    winner = COALESCE(excluded.winner, matches.winner),
                    venue = COALESCE(excluded.venue, matches.venue),
                    venue_city = COALESCE(
                        excluded.venue_city, matches.venue_city
                    ),
                    venue_country = COALESCE(
                        excluded.venue_country, matches.venue_country
                    ),
                    match_date = COALESCE(
                        excluded.match_date, matches.match_date
                    ),
                    format = COALESCE(excluded.format, matches.format),
                    status = COALESCE(excluded.status, matches.status),
                    toss_winner = COALESCE(
                        excluded.toss_winner, matches.toss_winner
                    ),
                    toss_decision = COALESCE(
                        excluded.toss_decision, matches.toss_decision
                    ),
                    victory_margin = COALESCE(
                        excluded.victory_margin, matches.victory_margin
                    ),
                    victory_type = COALESCE(
                        excluded.victory_type, matches.victory_type
                    ),
                    raw_state = COALESCE(
                        excluded.raw_state, matches.raw_state
                    )
                """,
                row,
            )

            if row.get("venue"):
                connection.execute(
                    """
                    INSERT INTO venues (name, city, country)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name, city, country) DO NOTHING
                    """,
                    (
                        row["venue"],
                        row.get("venue_city"),
                        row.get("venue_country"),
                    ),
                )

            saved += 1

    return saved


# =========================================================
# SERIES EXTRACTION
# =========================================================

def extract_series_records(payload):
    records = []
    seen = set()

    for item in _walk(payload):
        series_id = item.get("seriesId", item.get("id"))
        name = item.get("seriesName", item.get("name"))

        if (
            series_id is None
            or not name
            or "matchId" in item
            or str(series_id) in seen
        ):
            continue

        seen.add(str(series_id))

        records.append({
            "external_id": str(series_id),
            "name": str(name),
            "host_country": item.get("hostCountry"),
            "match_type": item.get("matchType"),
            "start_date": _date(
                item.get("startDt", item.get("startDate"))
            ),
            "end_date": _date(
                item.get("endDt", item.get("endDate"))
            ),
            "planned_matches": _number(item.get("totalMatches")),
        })

    return records


def sync_series(rows):
    saved = 0

    with get_connection() as connection:
        for row in rows:
            connection.execute(
                """
                INSERT INTO series (
                    external_id, name, host_country, match_type,
                    start_date, end_date, planned_matches
                )
                VALUES (
                    :external_id, :name, :host_country, :match_type,
                    :start_date, :end_date, :planned_matches
                )
                ON CONFLICT(external_id) DO UPDATE SET
                    name = excluded.name,
                    host_country = COALESCE(
                        excluded.host_country, series.host_country
                    ),
                    match_type = COALESCE(
                        excluded.match_type, series.match_type
                    ),
                    start_date = COALESCE(
                        excluded.start_date, series.start_date
                    ),
                    end_date = COALESCE(
                        excluded.end_date, series.end_date
                    ),
                    planned_matches = COALESCE(
                        excluded.planned_matches, series.planned_matches
                    )
                """,
                row,
            )

            saved += 1

    return saved


# =========================================================
# SCORECARD EXTRACTION
# =========================================================

def _extract_scorecard_rows(match_id, payload, match_info):
    """
    Parse Cricbuzz hscard responses.

    Batting and bowling are saved as separate role-specific rows.
    The original player payload is retained in raw_json.
    """
    rows = []

    if not isinstance(payload, dict):
        return rows

    scorecards = payload.get("scorecard", payload.get("scoreCard", []))

    if not isinstance(scorecards, list):
        return rows

    for index, innings in enumerate(scorecards, start=1):
        if not isinstance(innings, dict):
            continue

        innings_number = _innings_number(
            innings.get("inningsid", innings.get("inningsId")),
            index,
        )

        batting_team = _find_team_name(innings, "bat")
        bowling_team = _find_team_name(innings, "bowl")

        if not batting_team or not bowling_team:
            for child in _walk(innings):
                if child is innings:
                    continue

                if not batting_team:
                    batting_team = _find_team_name(child, "bat")

                if not bowling_team:
                    bowling_team = _find_team_name(child, "bowl")

        batsmen = _player_list(innings, "batsman", "batsmen")
        bowlers = _player_list(innings, "bowler", "bowlers")

        # Batting records
        for player in batsmen:
            if not isinstance(player, dict):
                continue

            name = _player_name(player)
            if not name:
                continue

            runs = _first_number(player, "runs", "batRuns")
            balls = _first_number(
                player, "balls", "ballsFaced", "batBalls"
            )
            fours = _first_number(player, "fours", "batFours")
            sixes = _first_number(player, "sixes", "batSixes")
            strike_rate = _first_number(
                player, "strkrate", "strikeRate", "batStrikeRate"
            )

            rows.append({
                "match_external_id": str(match_id),
                "player_external_id": _player_id(player),
                "player_name": str(name),
                "team": (
                    _team_name(player.get("teamName"))
                    or batting_team
                ),
                "format": match_info[1],
                "match_date": match_info[0],
                "innings_number": innings_number,
                "runs": runs,
                "balls_faced": balls,
                "fours": fours,
                "sixes": sixes,
                "strike_rate": strike_rate,
                "wickets": None,
                "runs_conceded": None,
                "overs_bowled": None,
                "economy_rate": None,
                "batting_position": _first_number(
                    player, "battingPosition", "position"
                ),
                "catches": _first_number(player, "catches"),
                "stumpings": _first_number(player, "stumpings"),
                "raw_json": _safe_json({
                    "role": "batting",
                    "innings_number": innings_number,
                    "player": player,
                }),
            })

        # Bowling records
        for player in bowlers:
            if not isinstance(player, dict):
                continue

            name = _player_name(player)
            if not name:
                continue

            # Cricbuzz commonly returns overs as a string, e.g. "10".
            # Store the supplied notation; do not convert overs to balls
            # or treat the decimal portion as a fraction of an over.
            overs_value = player.get(
                "overs",
                player.get("oversBowled", player.get("bowlOvs")),
            )
            overs = _number(overs_value)

            wickets = _first_number(
                player, "wickets", "wkts", "bowlWkts"
            )
            runs_conceded = _first_number(
                player,
                "runs",
                "runsConceded",
                "conceded",
                "bowlRuns",
            )
            economy = _first_number(
                player, "economy", "economyRate", "bowlEcon"
            )

            rows.append({
                "match_external_id": str(match_id),
                "player_external_id": _player_id(player),
                "player_name": str(name),
                "team": (
                    _team_name(player.get("teamName"))
                    or bowling_team
                ),
                "format": match_info[1],
                "match_date": match_info[0],
                "innings_number": innings_number,
                "runs": None,
                "balls_faced": None,
                "fours": None,
                "sixes": None,
                "strike_rate": None,
                "wickets": wickets,
                "runs_conceded": runs_conceded,
                "overs_bowled": overs,
                "economy_rate": economy,
                "batting_position": None,
                "catches": _first_number(player, "catches"),
                "stumpings": _first_number(player, "stumpings"),
                "raw_json": _safe_json({
                    "role": "bowling",
                    "innings_number": innings_number,
                    "player": player,
                    "overs_original": overs_value,
                }),
            })

    return rows


def sync_scorecard(match_id, payload):
    # Read match metadata from the existing match record.
    with get_connection() as connection:
        match = connection.execute(
            """
            SELECT match_date, format
            FROM matches
            WHERE external_id = ?
            LIMIT 1
            """,
            (str(match_id),),
        ).fetchone()

    match_info = (
        (match[0], match[1])
        if match is not None
        else (None, None)
    )

    rows = _extract_scorecard_rows(
        match_id, payload, match_info
    )

    # Never erase valid records if the response cannot be parsed.
    if not rows:
        return 0

    with get_connection() as connection:
        # Replace the imported scorecard for this match atomically.
        connection.execute(
            """
            DELETE FROM player_match_stats
            WHERE match_external_id = ?
            """,
            (str(match_id),),
        )

        for row in rows:
            connection.execute(
                """
                INSERT INTO player_match_stats (
                    match_external_id, player_external_id, player_name,
                    team, format, match_date, innings_number,
                    runs, balls_faced, fours, sixes, strike_rate,
                    wickets, runs_conceded, overs_bowled, economy_rate,
                    batting_position, catches, stumpings, raw_json
                )
                VALUES (
                    :match_external_id, :player_external_id, :player_name,
                    :team, :format, :match_date, :innings_number,
                    :runs, :balls_faced, :fours, :sixes, :strike_rate,
                    :wickets, :runs_conceded, :overs_bowled, :economy_rate,
                    :batting_position, :catches, :stumpings, :raw_json
                )
                """,
                row,
            )

            player_id = row["player_external_id"]

            if player_id:
                connection.execute(
                    """
                    INSERT INTO players (external_id, full_name)
                    VALUES (?, ?)
                    ON CONFLICT(external_id) DO UPDATE SET
                        full_name = excluded.full_name
                    """,
                    (player_id, row["player_name"]),
                )

    return len(rows)


# =========================================================
# EXPORTS USED BY OTHER PROJECT MODULES
# =========================================================

__all__ = [
    "fetch_live_matches",
    "fetch_livescore",
    "fetch_scorecard",
    "fetch_series_list",
    "extract_match_records",
    "sync_matches",
    "extract_series_records",
    "sync_series",
    "sync_scorecard",
]
