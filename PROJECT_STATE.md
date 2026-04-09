# Project State

This file is the canonical handoff note for the next agent working in this repository.

Use it for current-state guidance only. Stable architecture, coding rules, and skill conventions live in `AGENTS.md` and `CLAUDE.md`.

## Session Start Checklist

For the next agent entering this repository:

1. Read `AGENTS.md` or `CLAUDE.md` first.
2. Read this file before making any repo-wide decision.
3. Verify current library state from `data/papers/`, `data/index.db`, and `data/topic_model/`.
4. Do not infer the current architecture from `memory/`, static web exports, or old notes without verification.

## What Is Canonical

- The real library state lives in:
  - `data/papers/` for per-paper source data (`meta.json`, `paper.md`, optional `notes.md`)
  - `data/index.db` for registry / search / citation index state
  - `data/topic_model/` for BERTopic outputs and `roadmap.md`
- The current-library overview is generated dynamically by `scholaraio/services/explore_service.py`.
- `scholaraio/web/public/site-data/` is an exported static snapshot for the web UI, not the source of truth.
- User-facing drafts, reports, and scratch outputs should go under `workspace/`, not the repo root.

## Current Architectural Reality

- Explore now targets the current local library only.
- The old external `data/explore/...` silo is not part of the active architecture and should not be reintroduced casually.
- Skills are defined canonically in `.claude/skills/` and exposed to other agents through symlinks such as `.agents/skills` and `skills/`.
- Per-paper long-lived analysis belongs in `data/papers/<dir>/notes.md`, not in `memory/`.

## Do

- Read `AGENTS.md` or `CLAUDE.md` first, then read this file before making repo-wide decisions.
- Treat `data/papers/`, `data/index.db`, and `data/topic_model/` as the primary evidence when describing the current library.
- Use `workspace/` for generated reports, reviews, and one-off outputs.
- Sync `AGENTS.md` and `CLAUDE.md` when changing cross-agent project instructions.
- Verify historical notes before trusting them.
- If you think the project architecture changed recently, verify it from code, not from memory.

## Don't

- Do not treat `memory/` as authoritative project state.
- Do not treat `scholaraio/web/public/site-data/` as canonical library data.
- Do not restore the old `data/explore/` design unless the user explicitly wants that architecture back.
- Do not leave transient experiment files, rating JSONs, or parsing scratch outputs in the repo root.
- Do not assume paper claims are facts; keep the critical academic stance described in `AGENTS.md` / `CLAUDE.md`.
- Do not confidently describe "the current library" from stale handoff notes alone.

## About `memory/`

- `memory/` is best treated as optional human or agent scratch space.
- It may contain useful historical context, but new agents are not guaranteed to read it automatically.
- If something in `memory/` matters long-term, migrate the durable part either into:
  - `PROJECT_STATE.md` for repo-level current-state guidance, or
  - `data/papers/<dir>/notes.md` for paper-specific findings.
