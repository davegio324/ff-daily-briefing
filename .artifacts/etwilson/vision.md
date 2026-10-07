# Vision: FF Daily Briefing

> An automated daily fantasy football briefing that turns trusted sources and my real Sleeper leagues into spoon-fed, league-specific advice.

---

## Problem Statement

I follow a handful of fantasy football resources I trust, but I don't have time to read them every day and work out what they mean for my teams. The value is in the synthesis: applying that information to my actual rosters and each league's specific rules. I want that done for me, every day, without having to run anything.

---

## Product Positioning

A personal, single-user pipeline: deterministic steps gather data (my Sleeper rosters and leagues, plus a config-driven list of trusted web sources), and an LLM synthesizes it into one daily briefing. It beats reading the sources manually because it is automated, tailored to my two leagues' differing rules, and aware of where we are in the NFL week. It beats generic fantasy apps because the sources are ones I chose and trust, and the output is attributed to them.

---

## Users & Personas

- **Me (sole user):** fantasy football manager in two Sleeper leagues with different rules. Time-poor; wants conclusions handed over, not research to do. Reads the briefing from a work laptop.

---

## Core Features

- Pull my real teams and league settings from the Sleeper API (raw API, not MCP; the fetch is deterministic and doesn't need the LLM to choose calls)
- Fetch content from a config-driven list of trusted websites
- LLM synthesis of fetched data into a single daily briefing
- League-aware: recommendations account for each league's differing rules
- Day-aware: briefing focus follows the NFL calendar (e.g., waiver-focused ahead of waiver clear days)
- Source attribution: recommendations cite the sources they came from
- Fully automated: runs on a schedule with no manual invocation
- Briefing reachable from my work laptop

---

## Explicit Non-Goals

- No taking actions: read-only advice, never writes to Sleeper (no waiver claims, lineup changes, or trades)
- No web UI or app
- No multi-user support or sharing with others
- No sports other than football; no fantasy platforms other than Sleeper
- No LLM-driven tool use or MCP for data fetching in v1

---

## Product Constraints

- Must run unattended; manual runs are a failure of the product's purpose
- Must stay simple: this is a POC, so a minimal setup is preferred over robust infrastructure
- Briefing must be accessible from a work laptop (mechanism undecided)

---

## Tech Stack

- Sleeper data via raw HTTP API (settled)
- LLM for synthesis, with prompt engineering as the primary lever for output quality
- Language/runtime, scheduling, and delivery: undecided (see Open Questions)

---

## Milestones & Phasing

### v1 — End-to-End POC
- Sleeper rosters/leagues fetched
- Configured sources fetched
- LLM produces the daily briefing with source attribution, league rules, and day-of-week awareness
- Runs automatically on a schedule and is readable from my work laptop

### v2 — TBD
- Deliberately undefined; to be shaped by using v1

---

## Success Criteria

- **v1:** The pipeline runs unattended end to end and produces a daily briefing I personally judge useful. Quality is refined iteratively through prompt and source changes.
- **v2:** To be defined after v1 use.

---

## Open Questions

- Delivery channel for reaching the briefing from the work laptop
- Language and runtime
- Scheduling mechanism and where it runs
- Which sources are worth including, and whether they tolerate automated fetching
- Exact waiver clear days and times per league
- Offseason behavior
