---
id: EPIC-001
title: Daily briefing POC pipeline
status: ready
created: 2026-10-07
---

## Goal
Prove the core pipeline end to end: Sleeper data and a handful of configured web sources are fetched, synthesized by an LLM into a league-aware daily briefing, and delivered automatically as a styled HTML page opened in the browser on the user's MacBook Pro. This is the v1 POC from the vision; it exists to show every node of the pipeline works, not to harden it.

---

## Scope In
- Config-driven Python CLI with discrete stages (fetch, synthesize, render, deliver); each stage persists its output to disk so stages can be re-run independently
- Sleeper fetch (raw API, read-only): the user's rosters, league settings for both leagues (scoring and waiver timing), and free-agent/trending player data
- Source fetch: a handful of URLs from the config, plain HTTP or RSS only
- Synthesis stage behind a swappable LLM seam (context and prompt in, text out), with one v1 implementation using the headless `claude -p` CLI on the user's subscription
- Briefing content: per-league, rules-aware, sources cited, with today's date and each league's waiver schedule given to the model so emphasis follows the waiver calendar
- Render stage: the synthesized markdown is converted into a self-contained, styled HTML file (per-league sections, clickable source links), kept on disk as the day's history
- Delivery by opening that HTML file with macOS `open`, which shows it in the default browser
- Scheduling via `launchd` on the user's Mac, with one briefing per day (skip if today's already exists)
- A source that fails to fetch is skipped and noted in the briefing; the run continues

## Scope Out
- Other LLM providers and API-key billing
- Email, Ghostty or any terminal display, GitHub Actions, or any delivery/scheduling channel other than opening an HTML file and `launchd`
- Headless-browser or JS-rendered sources, large source lists, login-gated sources
- Anything that writes to Sleeper
- Battery, sleep, and lid-closed hardening; reliability issues found while dogfooding are handled afterward, not in this epic
- Tracking advice accuracy, chat mode, richer day-aware logic
- Multi-user support

---

## Key Decisions
- **Language and config:** Python; TOML config read with the standard library `tomllib`. Secrets and local settings live in `.env`, which is gitignored.
- **Sleeper via raw API, not MCP:** the fetch is a fixed deterministic step, so the LLM does not choose tool calls.
- **Waiver schedule comes from Sleeper league settings, not config.**
- **LLM seam:** the synthesis stage is the only place that knows about a provider. It takes assembled context and a prompt and returns text. v1 implements it with `claude -p`; `ANTHROPIC_API_KEY` must be unset so the subscription is used rather than API billing.
- **Delivery:** the LLM produces markdown; a render stage converts it to a self-contained HTML file with the project's own CSS, and delivery opens it with `open`. Presentation lives in the HTML template, not in the prompt. No email or terminal display in v1.
- **Scheduling:** `launchd` user agent with a calendar interval; a run missed while the Mac was asleep fires on wake. The run is idempotent per day.
- **Source scope:** plain HTTP and RSS only; any URL that needs JS rendering is dropped rather than worked around. The user supplies the URL list.
- **Done means:** a scheduled `launchd` run executes the full pipeline unattended and the styled briefing opens in the browser. Quality and reliability beyond that are judged by the user dogfooding it, and issues found become later work.
