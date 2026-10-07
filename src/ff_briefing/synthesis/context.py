import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class LeagueData:
    name: str
    roster: Any
    rules: Any
    waiver_schedule: Any
    free_agents: Any


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _league_section(league: LeagueData) -> str:
    return "\n\n".join(
        [
            f"## League: {league.name}",
            f"### Roster\n{_json(league.roster)}",
            f"### League rules\n{_json(league.rules)}",
            f"### Waiver schedule\n{_json(league.waiver_schedule)}",
            f"### Free agents and trending players\n{_json(league.free_agents)}",
        ]
    )


def _source_section(item: Mapping[str, Any]) -> str:
    title = item.get("title")
    heading = f"### {item['source_name']}: {title}" if title else f"### {item['source_name']}"
    return f"{heading}\nURL: {item['link']}\n\n{item['text']}"


def _failed_line(note: Mapping[str, Any]) -> str:
    return f"- {note['source_name']} ({note['source_url']}): {note['reason']}"


def build_context(
    leagues: Sequence[LeagueData],
    items: Sequence[Mapping[str, Any]],
    notes: Sequence[Mapping[str, Any]],
    today: date,
) -> str:
    sections = [f"# Today's date\n{today.isoformat()}"]
    sections.extend(_league_section(league) for league in leagues)
    sections.append("# Sources")
    sections.extend(_source_section(item) for item in items)
    if notes:
        sections.append("# Failed sources\n" + "\n".join(_failed_line(note) for note in notes))
    return "\n\n".join(sections) + "\n"
