from datetime import date

from ff_briefing.synthesis.context import LeagueData, build_context

TODAY = date(2026, 10, 7)


def _league(name: str, marker: str) -> LeagueData:
    return LeagueData(
        name=name,
        roster={"starters": [f"{marker}-roster"]},
        rules={"rec": f"{marker}-rules"},
        waiver_schedule={"waiver_day_of_week": f"{marker}-waiver"},
        free_agents=[{"name": f"{marker}-free-agent"}],
    )


def _item(name: str, link: str, text: str) -> dict[str, object]:
    return {"source_name": name, "link": link, "text": text}


def test_context_states_todays_date_in_iso_format() -> None:
    assert "2026-10-07" in build_context([], [], [], TODAY)


def test_each_league_gets_its_own_section_with_all_four_data_kinds() -> None:
    context = build_context([_league("Alpha", "a"), _league("Beta", "b")], [], [], TODAY)

    alpha, beta = context.split("Beta", 1)[0], context.split("Beta", 1)[1]
    for marker, section in (("a", alpha), ("b", beta)):
        for kind in ("roster", "rules", "waiver", "free-agent"):
            assert f"{marker}-{kind}" in section
    assert "b-roster" not in alpha


def test_successful_sources_appear_with_name_link_and_text() -> None:
    context = build_context(
        [],
        [_item("fantasy.example", "https://fantasy.example/p1", "Start Smith this week.")],
        [],
        TODAY,
    )

    assert "fantasy.example" in context
    assert "https://fantasy.example/p1" in context
    assert "Start Smith this week." in context


def test_failed_sources_are_listed_under_a_labeled_section_with_reason() -> None:
    notes = [
        {"source_name": "bad.example", "source_url": "https://bad.example/x", "reason": "HTTP 503"}
    ]

    context = build_context([], [], notes, TODAY)

    failed = context.split("Failed sources", 1)[1]
    assert "https://bad.example/x" in failed
    assert "HTTP 503" in failed


def test_no_sources_at_all_still_yields_context_without_failure_entries() -> None:
    context = build_context([_league("Alpha", "a")], [], [], TODAY)

    assert "Alpha" in context
    assert "https://" not in context
