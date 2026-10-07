import json
from pathlib import Path
from typing import Any

from ff_briefing.sleeper.client import SleeperError

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "sleeper"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class FakeSleeperClient:
    """Fixture-backed stand-in for SleeperClient that records every call."""

    def __init__(
        self, *, user: Any = "default", leagues: Any = "default", fail_on: str | None = None
    ):
        self.calls: list[tuple[str, ...]] = []
        self._user = load_fixture("user") if user == "default" else user
        self._leagues = load_fixture("leagues") if leagues == "default" else leagues
        self._fail_on = fail_on

    def _record(self, *call: str) -> None:
        self.calls.append(call)
        if call[0] == self._fail_on:
            raise SleeperError(f"GET {call[0]} failed: boom")

    def get_nfl_state(self) -> Any:
        self._record("get_nfl_state")
        return load_fixture("state")

    def get_user(self, username: str) -> Any:
        self._record("get_user", username)
        return self._user

    def get_user_leagues(self, user_id: str, season: str) -> Any:
        self._record("get_user_leagues", user_id, season)
        return self._leagues

    def get_rosters(self, league_id: str) -> Any:
        self._record("get_rosters", league_id)
        return load_fixture(f"rosters_{league_id}")

    def get_trending(self, kind: str) -> Any:
        self._record("get_trending", kind)
        return load_fixture(f"trending_{kind}")

    def get_players(self) -> Any:
        self._record("get_players")
        return load_fixture("players")
