from typing import Any

from ff_briefing.sleeper.client import SleeperError

_LEAGUE_WAIVER_KEYS = (
    "waiver_type",
    "waiver_day_of_week",
    "waiver_clear_days",
    "daily_waivers",
    "daily_waivers_hour",
    "waiver_budget",
)
_ROSTER_WAIVER_KEYS = ("waiver_position", "waiver_budget_used")


def select_user_roster(rosters: list[dict[str, Any]], user_id: str) -> dict[str, Any]:
    for roster in rosters:
        if roster.get("owner_id") == user_id:
            return roster
    raise SleeperError(f"no roster owned by user {user_id} in league")


def shape_waiver_settings(league: dict[str, Any], roster: dict[str, Any]) -> dict[str, Any]:
    league_settings = league.get("settings") or {}
    roster_settings = roster.get("settings") or {}
    waiver = {key: league_settings.get(key) for key in _LEAGUE_WAIVER_KEYS}
    waiver.update({key: roster_settings.get(key) for key in _ROSTER_WAIVER_KEYS})
    return waiver


def resolve_player(players: dict[str, Any], player_id: str) -> dict[str, Any]:
    player = players.get(player_id)
    if player is None:
        return {
            "name": None,
            "position": None,
            "team": None,
            "status": None,
            "injury_status": None,
        }
    name = " ".join(p for p in (player.get("first_name"), player.get("last_name")) if p)
    return {
        "name": name or None,
        "position": player.get("position"),
        "team": player.get("team"),
        "status": player.get("status"),
        "injury_status": player.get("injury_status"),
    }


def rostered_player_ids(rosters: list[dict[str, Any]]) -> list[str]:
    ids: set[str] = set()
    for roster in rosters:
        ids.update(roster.get("players") or [])
    return sorted(ids)


def build_trending(
    entries: list[dict[str, Any]], rostered_by_league: dict[str, set[str]]
) -> list[dict[str, Any]]:
    return [
        {
            "player_id": entry["player_id"],
            "count": entry["count"],
            "available_in": {
                league_id: entry["player_id"] not in rostered
                for league_id, rostered in rostered_by_league.items()
            },
        }
        for entry in entries
    ]


def build_league_entry(
    league: dict[str, Any], rosters: list[dict[str, Any]], user_id: str
) -> dict[str, Any]:
    roster = select_user_roster(rosters, user_id)
    return {
        "league_id": league["league_id"],
        "name": league.get("name"),
        "scoring_settings": league.get("scoring_settings") or {},
        "roster_positions": league.get("roster_positions") or [],
        "waiver": shape_waiver_settings(league, roster),
        "roster": {
            "roster_id": roster["roster_id"],
            "starters": roster.get("starters") or [],
            "players": roster.get("players") or [],
            "reserve": roster.get("reserve"),
        },
        "rostered_player_ids": rostered_player_ids(rosters),
    }
