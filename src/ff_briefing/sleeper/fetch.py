from datetime import UTC, datetime
from typing import Any

from ff_briefing.sleeper.client import SleeperClient, SleeperError
from ff_briefing.sleeper.shape import build_league_entry, build_trending, resolve_player


def fetch_sleeper(
    username: str, client: SleeperClient, now: datetime | None = None
) -> dict[str, Any]:
    season = client.get_nfl_state()["league_season"]
    user = client.get_user(username)
    if not user:
        raise SleeperError(f"Sleeper user {username!r} not found")
    user_id = user["user_id"]

    leagues = client.get_user_leagues(user_id, season)
    if not leagues:
        raise SleeperError(f"no NFL leagues for user {username!r} in season {season}")

    rosters_by_league = {
        league["league_id"]: client.get_rosters(league["league_id"]) for league in leagues
    }
    league_entries = [
        build_league_entry(league, rosters_by_league[league["league_id"]], user_id)
        for league in leagues
    ]
    rostered_by_league = {
        entry["league_id"]: set(entry["rostered_player_ids"]) for entry in league_entries
    }
    trending = {
        kind: build_trending(client.get_trending(kind), rostered_by_league)
        for kind in ("add", "drop")
    }

    all_players = client.get_players()
    referenced = {pid for entry in league_entries for pid in entry["roster"]["players"]}
    referenced.update(item["player_id"] for items in trending.values() for item in items)

    return {
        "fetched_at": (now or datetime.now(UTC)).isoformat(),
        "season": season,
        "username": username,
        "user_id": user_id,
        "leagues": league_entries,
        "trending": trending,
        "players": {pid: resolve_player(all_players, pid) for pid in sorted(referenced)},
    }
