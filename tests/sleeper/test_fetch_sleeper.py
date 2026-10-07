from datetime import UTC, datetime

import pytest

from ff_briefing.sleeper.client import SleeperError
from ff_briefing.sleeper.fetch import fetch_sleeper
from tests.sleeper.fakes import FakeSleeperClient

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def test_output_identifies_user_season_and_every_league() -> None:
    result = fetch_sleeper("eli", FakeSleeperClient(), now=NOW)

    assert result["fetched_at"] == "2026-10-07T12:00:00+00:00"
    assert result["season"] == "2026"
    assert result["username"] == "eli"
    assert result["user_id"] == "1001"
    assert [league["league_id"] for league in result["leagues"]] == ["L1", "L2"]


def test_leagues_are_requested_for_the_season_reported_by_nfl_state() -> None:
    client = FakeSleeperClient()

    fetch_sleeper("eli", client, now=NOW)

    assert ("get_user_leagues", "1001", "2026") in client.calls


def test_trending_adds_and_drops_are_annotated_with_availability_per_league() -> None:
    result = fetch_sleeper("eli", FakeSleeperClient(), now=NOW)

    assert result["trending"]["add"] == [
        {"player_id": "p5", "count": 120, "available_in": {"L1": True, "L2": False}},
        {"player_id": "p7", "count": 80, "available_in": {"L1": True, "L2": True}},
    ]
    assert result["trending"]["drop"] == [
        {"player_id": "p6", "count": 60, "available_in": {"L1": True, "L2": False}},
    ]


def test_players_hold_only_ids_referenced_by_user_rosters_and_trending() -> None:
    result = fetch_sleeper("eli", FakeSleeperClient(), now=NOW)

    assert set(result["players"]) == {"p1", "p2", "p3", "p4", "pX", "p5", "p6", "p7"}
    assert result["players"]["p2"]["name"] == "Justin Jefferson"
    assert result["players"]["pX"]["name"] is None


def test_player_dump_is_fetched_once_and_rosters_once_per_league() -> None:
    client = FakeSleeperClient()

    fetch_sleeper("eli", client, now=NOW)

    assert client.calls.count(("get_players",)) == 1
    assert client.calls.count(("get_rosters", "L1")) == 1
    assert client.calls.count(("get_rosters", "L2")) == 1


def test_unknown_username_raises_naming_the_user() -> None:
    with pytest.raises(SleeperError, match="nobody"):
        fetch_sleeper("nobody", FakeSleeperClient(user=None), now=NOW)


def test_zero_leagues_raises_instead_of_emitting_empty_output() -> None:
    with pytest.raises(SleeperError, match="no NFL leagues"):
        fetch_sleeper("eli", FakeSleeperClient(leagues=[]), now=NOW)


@pytest.mark.parametrize(
    "failing_call",
    ["get_nfl_state", "get_user", "get_user_leagues", "get_rosters", "get_trending", "get_players"],
)
def test_client_failure_propagates_with_the_failing_request_named(failing_call: str) -> None:
    with pytest.raises(SleeperError, match=f"GET {failing_call} failed"):
        fetch_sleeper("eli", FakeSleeperClient(fail_on=failing_call), now=NOW)
