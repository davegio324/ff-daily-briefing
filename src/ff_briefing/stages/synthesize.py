import json
from datetime import date
from typing import Any

from ff_briefing.config import Config
from ff_briefing.llm.claude_cli import ClaudeCliClient
from ff_briefing.llm.seam import LLMClient
from ff_briefing.rundir import RunDir
from ff_briefing.synthesis.context import LeagueData, build_context
from ff_briefing.synthesis.prompt import PLACEHOLDER_PROMPT


def _with_details(player_ids: list[str], players: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"player_id": pid, **players.get(pid, {})} for pid in player_ids]


def _league_data(
    league: dict[str, Any], trending: dict[str, Any], players: dict[str, Any]
) -> LeagueData:
    roster = league["roster"]
    league_id = league["league_id"]
    return LeagueData(
        name=league["name"],
        roster={
            **roster,
            "starters": _with_details(roster.get("starters") or [], players),
            "players": _with_details(roster.get("players") or [], players),
            "reserve": _with_details(roster.get("reserve") or [], players),
        },
        rules={
            "scoring_settings": league["scoring_settings"],
            "roster_positions": league["roster_positions"],
        },
        waiver_schedule=league["waiver"],
        free_agents={
            kind: [
                {**entry, **players.get(entry["player_id"], {})}
                for entry in trending.get(kind, [])
                if entry["available_in"].get(league_id)
            ]
            for kind in ("add", "drop")
        },
    )


def load_inputs(
    run_dir: RunDir,
) -> tuple[list[LeagueData], list[dict[str, Any]], list[dict[str, Any]]]:
    sleeper = json.loads(run_dir.require(run_dir.sleeper_json, "fetch").read_text("utf-8"))
    leagues = [
        _league_data(league, sleeper["trending"], sleeper["players"])
        for league in sleeper["leagues"]
    ]
    items: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    if run_dir.sources_json.exists():
        sources = json.loads(run_dir.sources_json.read_text("utf-8"))
        items, notes = sources.get("items", []), sources.get("notes", [])
    return leagues, items, notes


def synthesize_with(client: LLMClient, config: Config, run_dir: RunDir, today: date) -> None:
    leagues, items, notes = load_inputs(run_dir)
    briefing = client.complete(build_context(leagues, items, notes, today), PLACEHOLDER_PROMPT)
    run_dir.briefing_md.write_text(briefing, encoding="utf-8")


def run(config: Config, run_dir: RunDir, today: date) -> None:
    synthesize_with(ClaudeCliClient(), config, run_dir, today)
