# ESPN briefings with a scheduled Codex chat

You can use a scheduled Codex chat to produce the same kind of daily briefing for
an ESPN Fantasy Football team. Codex fetches current league data and researches
news at each run, then posts the briefing in the chat.

This is an alternative workflow. The Python pipeline in this repository still
uses Sleeper and Claude; these instructions do not add an ESPN adapter to
`ff-briefing run`, change `config.toml`, or install a launchd job. The schedule is
stored in the Codex app, not in this repository. Cloning the repository does not
create it.

## Set up

1. Open a Codex chat and provide your ESPN league link and team name or team ID.
2. Ask Codex to read the league and confirm the season, team, scoring settings,
   roster, and current matchup. A league link contains `leagueId`; the selected
   team's page may also contain `teamId`.
3. Request a sample briefing and review that it describes your team correctly.
4. Ask Codex to schedule the prompt below every day at your chosen time and
   timezone, for example **7 a.m. America/Chicago**. Check the schedule shown by
   the app. America/Chicago follows Central daylight-saving changes.
5. Confirm that the app reports an active schedule and check the first scheduled
   result. Consult the app's current requirements for unattended runs; do not
   assume the schedule will execute while the app or computer is unavailable.

No Claude installation or Anthropic credentials are needed for this workflow.
Codex account access, usage limits, network access, and scheduled-task availability
still apply. See the [official scheduled-task documentation](https://learn.chatgpt.com/docs/automations?surface=app).

## Reading ESPN data

The following read-only endpoint shape returned league settings, teams, rosters,
and matchups during setup on October 27, 2026:

```text
https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/SEASON/segments/0/leagues/LEAGUE_ID?view=mSettings&view=mTeam&view=mRoster&view=mMatchup
```

Replace `SEASON` and `LEAGUE_ID` with your values. Verify the returned league ID,
season, and selected team before using the data. In the offseason, the calendar
year alone is not sufficient to choose a fantasy season.

This is an undocumented ESPN endpoint and may change. Some league data was
accessible without authentication during setup; that does not establish access
for every league or view. If access fails, report the problem rather than using
old data as if it were current. Do not paste account passwords or session cookies
into the reusable prompt or commit credentials to this repository.

The roster request does not establish the available-player pool. Waiver
recommendations require a separate current player-pool request, suitable filters
and pagination, and verification that the player is unrostered in this league.
If those checks cannot be completed, omit named waiver recommendations and state
the limitation.

## Reusable briefing prompt

Replace the bracketed fields before asking Codex to schedule this prompt:

```text
Deliver a daily fantasy football briefing in this chat for my ESPN team
[TEAM NAME], team ID [TEAM ID], league ID [LEAGUE ID]. Use America/Chicago
for dates and times.

Fetch fresh ESPN scoring settings, lineup slots, rosters, standings, the
current scoring period, and matchups. Confirm the season and team identity.
Use this read-only endpoint shape, replacing the season and league ID:
https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/SEASON/segments/0/leagues/LEAGUE_ID?view=mSettings&view=mTeam&view=mRoster&view=mMatchup
If web retrieval cannot read the JSON, use available read-only HTTP tools.
Do not assume that a new fantasy season is available merely because the
calendar year changed.

Research current injury news and rankings and link supporting sources.
Tailor recommendations to the actual scoring rules and lineup slots.
Include:
- The three most useful actions today.
- Roster injury and bye alerts.
- Start/sit suggestions, including uncertainty and relevant kickoff times.
- Verified waiver targets and plausible drops, only if a separate fresh
  player-pool request and league roster checks establish availability.
- A short matchup outlook, distinguishing projections from final results.

Emphasize changes since the previous briefing, but deliver a briefing every
day even when little changed. Never invent missing projections, player
availability, or roster data. If ESPN access fails, report the problem and
provide only independently verified news, explicitly stating that current
roster-specific analysis is unavailable.

Notify me when the briefing is ready or access fails. Generate the report
using this chat's Codex capabilities without requiring Claude or API
credentials. Advice only: do not change lineups, submit claims, propose
trades through ESPN, or send messages to other people.
```

This delivers a chat briefing. It does not create the Python pipeline's HTML
output or automatically open a browser. A native ESPN fetch stage and a Codex
synthesis client would be separate code changes if that integration is desired.
