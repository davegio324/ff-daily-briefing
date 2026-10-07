import pytest

from ff_briefing.sleeper.client import SleeperError
from ff_briefing.sleeper.shape import (
    build_league_entry,
    build_trending,
    resolve_player,
    rostered_player_ids,
    select_user_roster,
    shape_waiver_settings,
)
from tests.sleeper.fakes import load_fixture

WAIVER_KEYS = {
    "waiver_type",
    "waiver_day_of_week",
    "waiver_clear_days",
    "daily_waivers",
    "daily_waivers_hour",
    "waiver_budget",
    "waiver_position",
    "waiver_budget_used",
}


def test_selects_roster_by_owner_id_not_by_position() -> None:
    rosters = load_fixture("rosters_L1")

    roster = select_user_roster(rosters, "1001")

    assert roster["roster_id"] == 2
    assert roster["players"] == ["p1", "p2", "p3", "pX"]


def test_selecting_roster_for_user_who_owns_none_raises() -> None:
    with pytest.raises(SleeperError, match="roster"):
        select_user_roster(load_fixture("rosters_L1"), "9999")


def test_waiver_settings_copy_league_settings_and_roster_values() -> None:
    league = load_fixture("leagues")[0]
    roster = select_user_roster(load_fixture("rosters_L1"), "1001")

    waiver = shape_waiver_settings(league, roster)

    assert waiver == {
        "waiver_type": 2,
        "waiver_day_of_week": 2,
        "waiver_clear_days": 1,
        "daily_waivers": False,
        "daily_waivers_hour": 0,
        "waiver_budget": 100,
        "waiver_position": 4,
        "waiver_budget_used": 12,
    }


def test_waiver_settings_emit_null_for_missing_fields() -> None:
    league = load_fixture("leagues")[1]
    roster = select_user_roster(load_fixture("rosters_L2"), "1001")

    waiver = shape_waiver_settings(league, roster)

    assert set(waiver) == WAIVER_KEYS
    assert waiver["waiver_type"] == 0
    assert waiver["waiver_day_of_week"] == 3
    assert waiver["waiver_clear_days"] is None
    assert waiver["waiver_budget"] is None
    assert waiver["waiver_position"] is None
    assert waiver["waiver_budget_used"] is None


def test_resolves_player_to_name_position_team_and_status() -> None:
    players = load_fixture("players")

    assert resolve_player(players, "p2") == {
        "name": "Justin Jefferson",
        "position": "WR",
        "team": "MIN",
        "status": "Active",
        "injury_status": "Questionable",
    }


def test_player_missing_from_dump_is_kept_with_null_name() -> None:
    assert resolve_player(load_fixture("players"), "pX") == {
        "name": None,
        "position": None,
        "team": None,
        "status": None,
        "injury_status": None,
    }


def test_rostered_ids_are_union_of_every_roster_in_league() -> None:
    assert rostered_player_ids(load_fixture("rosters_L1")) == ["p1", "p2", "p3", "p8", "p9", "pX"]


def test_trending_availability_is_per_league_unrostered_state() -> None:
    rostered = {"L1": {"p1"}, "L2": {"p5"}}

    trending = build_trending(
        [{"player_id": "p5", "count": 120}, {"player_id": "p7", "count": 80}], rostered
    )

    assert trending == [
        {"player_id": "p5", "count": 120, "available_in": {"L1": True, "L2": False}},
        {"player_id": "p7", "count": 80, "available_in": {"L1": True, "L2": True}},
    ]


def test_league_entry_carries_scoring_roster_and_rostered_ids() -> None:
    league = load_fixture("leagues")[0]

    entry = build_league_entry(league, load_fixture("rosters_L1"), "1001")

    assert entry["league_id"] == "L1"
    assert entry["name"] == "Sunday Funday"
    assert entry["scoring_settings"] == league["scoring_settings"]
    assert entry["roster_positions"] == league["roster_positions"]
    assert entry["roster"] == {
        "roster_id": 2,
        "starters": ["p1", "p2"],
        "players": ["p1", "p2", "p3", "pX"],
        "reserve": ["p3"],
    }
    assert entry["rostered_player_ids"] == ["p1", "p2", "p3", "p8", "p9", "pX"]
    assert set(entry["waiver"]) == WAIVER_KEYS
