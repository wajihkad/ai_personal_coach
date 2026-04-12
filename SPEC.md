# Life Coach Agent — Technical Specification

## Overview

A personal AI life coach that helps users learn and progress across multiple self-improvement domains (guitar, chess, coding). It acts as a **thinking partner that also acts**: it reasons across domains, maintains memory of past sessions, adapts its recommendations, and produces structured output artifacts autonomously.

---

## 1. Core Requirements

### 1.1 Agent vs. Chatbot Distinction

- The agent MUST always produce a structured artifact (card) as its primary output — never a free-form conversational reply alone.
- The agent MUST read past history (CheckIns, previous Cards) before generating any output.
- The agent MUST reason across all active domains simultaneously, not per domain in isolation.

### 1.2 Data Structures

The following dataclasses MUST be implemented exactly as specified. They are the contract between all system components.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Domain(Enum):
    GUITAR = "guitar"
    CHESS = "chess"
    CODING = "coding"

class Level(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Status(Enum):
    DONE = "done"
    SKIPPED = "skipped"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class DomainProfile:
    domain: Domain
    level: Level
    goal: str
    hours_per_week: float
    notes: str = ""

@dataclass
class Action:
    domain: Domain
    description: str
    duration_minutes: int
    status: Status = Status.PENDING
    feedback: Optional[str] = None

@dataclass
class ProfileCard:
    user_name: str
    domains: list[DomainProfile]
    available_days: list[str]
    preferred_session_length: int
    learning_style: str
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class DailyCard:
    date: datetime
    actions: list[Action]
    motivation_note: str
    generated_by_agent: bool = True

@dataclass
class WeeklyCard:
    week_start: datetime
    week_end: datetime
    domain_summaries: dict[Domain, str]
    completion_rate: dict[Domain, float]
    highlight: str
    next_week_focus: list[Action]

@dataclass
class MilestoneCard:
    date: datetime
    domain: Domain
    achievement: str
    next_challenge: str

@dataclass
class CheckIn:
    date: datetime
    completed_actions: list[Action]
    energy_level: int
    free_text: str
```

### 1.3 Agent Loop

The core loop MUST follow this sequence:

1. User submits a check-in (natural language message)
2. Agent loads `ProfileCard` from local storage
3. Agent loads the N most recent `CheckIn` records from local storage
4. Agent reasons: which domains need attention, what is the current energy level, what is overdue
5. Agent produces one of: `DailyCard`, `WeeklyCard`, or `MilestoneCard`
6. Agent persists the new card and the new `CheckIn` to local storage
7. (Level 3+) Agent optionally invokes external tools

---

## 2. Storage Requirements

- All data MUST be stored as local JSON files. No database required at any level.
- Storage layout:

```
data/
  profile.json          # ProfileCard — one per user
  checkins/
    YYYY-MM-DD.json     # one CheckIn per day
  cards/
    daily/
      YYYY-MM-DD.json
    weekly/
      YYYY-WNN.json     # ISO week number
    milestone/
      YYYY-MM-DD-{domain}.json
```

- Files MUST be human-readable and editable by hand (no binary formats).
- Loading MUST be fault-tolerant: missing files return `None`, not exceptions.
- Saving MUST be atomic: write to a temp file, then rename (avoids corrupt writes).

---

## 3. LLM Integration Requirements

- Use the `anthropic` Python SDK exclusively.
- Use Claude's structured output capability (tool use / JSON mode) to produce cards — do NOT parse free-form text.
- Each LLM call MUST include:
  - The `ProfileCard` as context
  - The last 7 `CheckIn` records (or fewer if unavailable)
  - The user's current check-in message
  - The target card schema as a tool definition
- Prompt caching MUST be applied to the static portions of the system prompt (profile, schema definitions) to reduce latency and cost.
- The agent MUST select which card type to produce based on the day of the week and available history:
  - End of week (Friday/Saturday) with at least 3 check-ins that week → `WeeklyCard`
  - Milestone condition detected → `MilestoneCard`
  - All other cases → `DailyCard`

---

## 4. DailyCard Requirements

- MUST contain 2–3 actions. Never more, never fewer (unless fewer than 2 domains are active).
- Actions MUST be distributed across domains — no two consecutive DailyCards may focus on the same single domain unless that is the only active domain.
- Each action MUST include a realistic `duration_minutes` value consistent with the user's `preferred_session_length`.
- `motivation_note` MUST reference something specific from the user's recent history — not a generic phrase.
- Actions MUST have `status = Status.PENDING` when first generated.

---

## 5. WeeklyCard Requirements

- MUST be generated when the agent detects end-of-week (configurable day, default: Sunday).
- `completion_rate` per domain MUST be computed from the actual `CheckIn` records of that week, not estimated.
- `next_week_focus` MUST prioritize domains with the lowest completion rate from the past week.
- `highlight` MUST identify the single most notable positive event from the week.

---

## 6. MilestoneCard Requirements

- Triggered automatically when any of the following conditions are met:
  - User has completed N consecutive sessions in a domain (default N=5)
  - User has reported a personal best (detected from free-text via LLM)
  - User has reached their stated domain goal (detected from free-text via LLM)
- `next_challenge` MUST suggest a concrete, domain-appropriate next step — not a generic encouragement.

---

## 7. CheckIn Requirements

- `energy_level` MUST be an integer from 1 to 5 (inclusive). Values outside this range MUST be rejected.
- `free_text` MUST be preserved exactly as entered by the user — no normalization or truncation.
- `completed_actions` MUST reference the actions from the most recent `DailyCard` where applicable.
- If the user reports partial completion, the relevant `Action` MUST be saved with `status = Status.PARTIAL` and the user's note in `feedback`.

---

## 8. CLI Interface Requirements (Level 2+)

- Entry point: `python -m coach` or `coach` (if installed as a package).
- Commands:
  - `coach checkin` — submit a new check-in interactively
  - `coach today` — display today's DailyCard (generate if missing)
  - `coach week` — display the current WeeklyCard
  - `coach profile` — display and optionally edit the ProfileCard
  - `coach history [--days N]` — display past N check-ins (default: 7)
- Output MUST be human-readable in the terminal. Use a structured text format (not raw JSON).
- All commands MUST work offline — no network calls except the LLM API call.

---

## 9. External Tool Requirements (Level 3+)

Each tool integration MUST be optional and individually togglable via config.

### 9.1 Google Calendar

- The agent MAY write a calendar event for each action in a DailyCard.
- Events MUST include: title, duration, and a description linking back to the domain goal.
- The agent MUST NOT delete or modify existing calendar events.

### 9.2 Todoist / Notion (Task List)

- The agent MAY create a task for each pending action.
- Tasks MUST be tagged with the domain name.
- Completed actions from a CheckIn MUST mark the corresponding task as done.

### 9.3 Telegram Bot

- The agent MAY send a daily morning briefing containing the DailyCard summary.
- The agent MAY send an evening nudge if no CheckIn was recorded by a configurable cutoff time (default: 20:00 local time).
- The bot MUST NOT send more than 3 messages per day to avoid notification fatigue.

### 9.4 Lichess API

- The agent MAY fetch a daily chess puzzle and include it as an action when the domain is `CHESS`.
- The puzzle link MUST be included in the action `description`.

---

## 10. Proactive Agent Requirements (Level 4)

- The agent MUST be runnable as a scheduled job (cron or equivalent).
- Morning run (configurable time, default: 08:00): generate and deliver the DailyCard if not already done.
- Evening run (configurable time, default: 20:00): send a nudge if no CheckIn exists for today.
- The agent MUST be idempotent: running it twice in the same time window MUST NOT produce duplicate cards or notifications.
- Each run MUST log its actions to a local `logs/agent.log` file with timestamps.

---

## 11. Configuration Requirements

- All configuration MUST live in a single `config.toml` file at the project root.
- The following values MUST be configurable:
  - `data_dir` — path to local storage (default: `./data`)
  - `log_dir` — path to log files (default: `./logs`)
  - `week_end_day` — day that triggers WeeklyCard (default: `"sunday"`)
  - `morning_run_time` — time for proactive morning job (default: `"08:00"`)
  - `evening_nudge_time` — time for evening nudge (default: `"20:00"`)
  - `milestone_streak_threshold` — consecutive sessions to trigger milestone (default: `5`)
  - `max_daily_actions` — max actions in a DailyCard (default: `3`)
  - `history_window_days` — how many past CheckIns to pass to the LLM (default: `7`)
  - Feature flags: `enable_calendar`, `enable_todoist`, `enable_telegram`, `enable_lichess`
- API keys MUST be stored in a `.env` file, never in `config.toml` or committed to version control.

---

## 12. Error Handling Requirements

- If the LLM API call fails, the agent MUST retry up to 3 times with exponential backoff before surfacing an error.
- If a tool integration (calendar, Telegram, etc.) fails, the agent MUST log the error and continue — tool failures MUST NOT prevent card generation.
- If `profile.json` is missing, the agent MUST prompt the user to complete onboarding before proceeding.
- All errors MUST be logged with context (timestamp, operation, error message). Stack traces MUST be written to the log file but not shown to the user by default.

---

## 13. Testing Requirements

- Each card type MUST have at least one unit test validating its structure.
- The agent loop MUST be testable without making real LLM API calls (dependency injection or mocking of the API client).
- Storage read/write MUST be testable with a temporary directory (no side effects on real data).
- At least one integration test MUST cover the full check-in → card generation → storage cycle using a stubbed LLM response.

---

## 14. Build Progression

| Level | Description | Acceptance Criteria |
|-------|-------------|---------------------|
| 1 — MVP | Python script + Claude API. Single check-in → DailyCard. Local JSON storage. | User can run a script, enter a check-in, and receive a rendered DailyCard. Card is saved to disk. |
| 2 — Memory | Agent reads past CheckIns. CLI interface. Cards adapt over time. | DailyCard references specific past events. `coach` CLI commands work. |
| 3 — Tools | Google Calendar, Todoist, Telegram, Lichess integrations (toggleable). | Each tool can be enabled/disabled independently. Agent acts without user prompting. |
| 4 — Proactive | Cron job. Morning briefing. Evening nudge. Idempotent runs. | Agent can run unattended. No duplicate cards or messages. Logs all activity. |

---

## 15. Out of Scope

The following are explicitly NOT required at any build level:

- A web UI or mobile app
- Multi-user support
- A database (SQL or NoSQL)
- Real-time collaboration
- Voice input/output
- Authentication or authorization
- Paid subscription tiers or billing
