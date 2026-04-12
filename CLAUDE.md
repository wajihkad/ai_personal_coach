# CLAUDE.md — AI Personal Coach

This file defines the rules, conventions, and constraints that govern all development in this repository. Read this before making any change.

---

## Project Overview

An agentic AI life coach built in Python. Users check in conversationally; the agent reads their history, reasons across multiple learning domains, and produces structured output cards (Daily, Weekly, Milestone). The full specification lives in [SPEC.md](SPEC.md).

---

## Language & Runtime

- Python 3.12+. No other language.
- Use standard library where possible. Prefer fewer dependencies over convenience wrappers.
- `pyproject.toml` is the single source of truth for dependencies and project metadata. Do not use `setup.py` or `requirements.txt`.
- Virtual environment lives in `.venv/` at the project root. Never commit it.

---

## Project Layout

```
ai_personal_coach/
├── CLAUDE.md
├── SPEC.md
├── README.md
├── pyproject.toml
├── config.toml              # user-editable config (committed with safe defaults)
├── .env.example             # template for secrets — committed
├── .env                     # actual secrets — NEVER committed
├── coach/                   # main package
│   ├── __init__.py
│   ├── __main__.py          # entry point: `python -m coach`
│   ├── models.py            # all dataclasses and enums (Domain, Level, Status, cards, CheckIn)
│   ├── storage.py           # read/write JSON to data/
│   ├── agent.py             # agent loop: loads context, calls LLM, returns a card
│   ├── prompts.py           # all system prompts and tool schemas
│   ├── cli.py               # CLI commands (checkin, today, week, profile, history)
│   ├── config.py            # loads config.toml and .env
│   └── tools/               # Level 3 integrations (one file per tool)
│       ├── __init__.py
│       ├── calendar.py
│       ├── todoist.py
│       ├── telegram.py
│       └── lichess.py
├── data/                    # local storage — gitignored
│   ├── profile.json
│   ├── checkins/
│   └── cards/
├── logs/                    # agent run logs — gitignored
└── tests/
    ├── conftest.py
    ├── test_models.py
    ├── test_storage.py
    ├── test_agent.py
    └── test_cli.py
```

Do not create files outside this layout without a good reason. If you add a new module, update this layout in CLAUDE.md.

---

## Models (`coach/models.py`)

- All dataclasses and enums live exclusively in `models.py`. Do not define data structures elsewhere.
- The dataclass definitions in `SPEC.md § 1.2` are the authoritative contract. Do not change field names, types, or defaults without updating the spec first.
- `Domain`, `Level`, `Status` are `Enum` subclasses. Always use enum members in code — never raw strings like `"guitar"`.
- Do not add ORM mixins, validators, or serialization methods to the dataclasses. Serialization belongs in `storage.py`.

---

## Storage (`coach/storage.py`)

- All reads return `None` (not exceptions) when a file is missing.
- All writes are atomic: write to a `.tmp` file, then `os.replace()` into the target path.
- Serialize `datetime` as ISO 8601 strings. Serialize `Enum` members by `.value`. Deserialize back on load.
- File naming conventions (from SPEC.md § 2):
  - CheckIns: `data/checkins/YYYY-MM-DD.json`
  - DailyCards: `data/cards/daily/YYYY-MM-DD.json`
  - WeeklyCards: `data/cards/weekly/YYYY-WNN.json`
  - MilestoneCards: `data/cards/milestone/YYYY-MM-DD-{domain}.json`
- Never call storage functions from inside `models.py` or `prompts.py`.

---

## Agent (`coach/agent.py`)

- The agent loop MUST follow the sequence in `SPEC.md § 1.3` exactly.
- Load `ProfileCard` + last N `CheckIn` records before every LLM call. N is read from `config.toml` (`history_window_days`, default 7).
- Card type selection logic (from SPEC.md § 3):
  - End of `week_end_day` with ≥ 3 check-ins that week → `WeeklyCard`
  - Milestone condition detected → `MilestoneCard`
  - All other cases → `DailyCard`
- The LLM MUST be called via a thin wrapper that supports dependency injection — pass the client as a parameter so tests can substitute a stub without monkey-patching.
- Retry failed API calls up to 3 times with exponential backoff (1s, 2s, 4s). Surface a clear error after the third failure.
- Tool integrations (calendar, Todoist, etc.) are called after the card is generated and saved. A tool failure MUST NOT prevent the card from being returned.

---

## LLM & Prompts (`coach/prompts.py`)

- Use the `openai` Python SDK. No other LLM client library.
- Use Claude's tool-use feature to produce structured card output. Do not parse free-form text.
- Define one tool schema per card type (`daily_card_tool`, `weekly_card_tool`, `milestone_card_tool`).
- Apply prompt caching (`"cache_control": {"type": "ephemeral"}`) to the static parts of every request: the system prompt and the ProfileCard block. Do not cache the user's check-in message.
- All prompt strings live in `prompts.py`. No f-string prompts scattered across other modules.

---

## Configuration (`coach/config.py`)

- `config.toml` holds all non-secret configuration. It is committed to the repo with safe defaults.
- `.env` holds API keys and secrets. It is gitignored. `.env.example` documents every required key.
- `config.py` exposes a single `Settings` object (dataclass or simple namespace) loaded at import time. All other modules import from `config.py` — never read `config.toml` or `os.environ` directly elsewhere.
- Required config keys (see SPEC.md § 11):
  `data_dir`, `log_dir`, `week_end_day`, `morning_run_time`, `evening_nudge_time`,
  `milestone_streak_threshold`, `max_daily_actions`, `history_window_days`,
  `enable_calendar`, `enable_todoist`, `enable_telegram`, `enable_lichess`

---

## CLI (`coach/cli.py`)

- Use the `click` library for CLI. Do not use `argparse`.
- Commands: `checkin`, `today`, `week`, `profile`, `history`
- Output MUST be human-readable terminal text. Do not dump raw JSON to stdout.
- All commands MUST work with no network access except the LLM API call.
- Entry point: `python -m coach` (via `coach/__main__.py`) or the `coach` script defined in `pyproject.toml`.

---

## Tool Integrations (`coach/tools/`)

- Each integration is a single file with a single public function (e.g. `create_calendar_events(card: DailyCard) -> None`).
- Every integration MUST be guarded by its feature flag from `config.py`. If the flag is off, the function returns immediately without error.
- Integrations MUST NOT import from each other.
- Credentials are read from `.env` via `config.py`. Never hardcode or log credentials.

---

## Testing

- Test files live in `tests/`. Mirror the package structure: `test_models.py` tests `models.py`, etc.
- Use `pytest`. No other test framework.
- LLM API calls MUST be stubbed in tests. Inject a fake client; never call the real API in tests.
- Storage tests MUST use `tmp_path` (pytest fixture) — never read or write `data/` during tests.
- Every card type MUST have a test that validates its structure against the spec.
- At least one integration test covers: check-in → agent → card saved to disk (with stubbed LLM).
- Run tests with: `pytest tests/`

---

## Code Style

- Format with `ruff format`. Lint with `ruff check`. Both run in CI.
- Type-annotate all function signatures. Use `from __future__ import annotations` at the top of every file.
- No `print()` in library code (`coach/` package). Use `logging` with the module logger (`logger = logging.getLogger(__name__)`).
- Logs go to `logs/agent.log` with timestamps. User-facing output goes through the CLI layer only.
- Do not add docstrings to functions whose purpose is obvious from the name and signature. Add them only where the logic is non-trivial.
- Do not leave commented-out code in commits.

---

## Git

- Branch naming: `feat/<short-description>`, `fix/<short-description>`, `chore/<short-description>`.
- Commit messages follow Conventional Commits: `feat: ...`, `fix: ...`, `chore: ...`, `test: ...`, `docs: ...`.
- Never commit: `.env`, `data/`, `logs/`, `.venv/`, `__pycache__/`, `*.pyc`.
- The `.gitignore` must cover all of the above before the first non-trivial commit.

---

## Build Levels

Implement in order. Do not start Level N+1 until Level N passes its acceptance criteria.

| Level | Scope | Acceptance Criteria |
|-------|-------|---------------------|
| 1 — MVP | `models.py`, `storage.py`, `agent.py`, `prompts.py`, single script | User runs script, enters check-in, gets a rendered DailyCard, card saved to disk |
| 2 — Memory + CLI | `cli.py`, `config.py`, history context in agent | All 5 CLI commands work; DailyCard references past events |
| 3 — Tools | `tools/` integrations, feature flags | Each tool toggled independently; agent acts without user prompting |
| 4 — Proactive | Cron/scheduler, idempotent runs, logging | Agent runs unattended, no duplicate cards or messages, all runs logged |

---

## What Not To Do

- Do not add a web UI, database, or multi-user support — these are out of scope (SPEC.md § 15).
- Do not use `requests` directly — use `httpx` for any HTTP calls (async-compatible).
- Do not add features beyond the current build level.
- Do not catch bare `Exception` — catch specific exception types.
- Do not store secrets in `config.toml`, code, or comments.
- Do not generate free-form text as the agent's primary output — always produce a structured card.
