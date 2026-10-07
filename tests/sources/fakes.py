from collections.abc import Callable
from pathlib import Path

from ff_briefing.sources.models import FetchResponse

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sources"


def fixture_response(
    name: str, content_type: str | None = "text/html", status: int = 200
) -> FetchResponse:
    return FetchResponse(status, content_type, (FIXTURES / name).read_text(encoding="utf-8"))


def fake_get(responses: dict[str, FetchResponse | Exception]) -> Callable[[str], FetchResponse]:
    def get(url: str) -> FetchResponse:
        outcome = responses[url]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return get
