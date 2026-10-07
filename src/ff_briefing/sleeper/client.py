from typing import Any, Protocol

import httpx

from ff_briefing.errors import BriefingError

BASE_URL = "https://api.sleeper.app"
TIMEOUT_SECONDS = 30.0


class SleeperError(BriefingError):
    pass


class SleeperClient(Protocol):
    def get_nfl_state(self) -> Any: ...
    def get_user(self, username: str) -> Any: ...
    def get_user_leagues(self, user_id: str, season: str) -> Any: ...
    def get_rosters(self, league_id: str) -> Any: ...
    def get_trending(self, kind: str) -> Any: ...
    def get_players(self) -> Any: ...


class HttpSleeperClient:
    """Read-only: every request is a GET."""

    def __init__(self, http: httpx.Client | None = None) -> None:
        self._http = http or httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_SECONDS)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = self._http.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise SleeperError(f"GET {path} failed: HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise SleeperError(f"GET {path} failed: {exc}") from exc
        except ValueError as exc:
            raise SleeperError(f"GET {path} returned a non-JSON body") from exc

    def get_nfl_state(self) -> Any:
        return self._get("/v1/state/nfl")

    def get_user(self, username: str) -> Any:
        return self._get(f"/v1/user/{username}")

    def get_user_leagues(self, user_id: str, season: str) -> Any:
        return self._get(f"/v1/user/{user_id}/leagues/nfl/{season}")

    def get_rosters(self, league_id: str) -> Any:
        return self._get(f"/v1/league/{league_id}/rosters")

    def get_trending(self, kind: str) -> Any:
        return self._get(f"/v1/players/nfl/trending/{kind}", {"lookback_hours": 24, "limit": 25})

    def get_players(self) -> Any:
        return self._get("/v1/players/nfl")
