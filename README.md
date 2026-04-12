# AI Personal Coach

A personal AI life coach that helps you make consistent progress across multiple learning domains — guitar, chess, coding — simultaneously.

You check in conversationally. The agent reads your history, reasons across all your domains, and produces a structured **card** (daily plan, weekly review, or milestone celebration).

---

## How it works

```
Your check-in message
       ↓
Agent reads your profile + recent history
       ↓
Produces a card (Daily / Weekly / Milestone)
       ↓
Saved to disk — ready for next session
```

---

## Quickstart

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Set up your API key (optional)

Without a key the coach runs in **dummy mode** — it returns plausible fake cards so you can explore the flow without any account.

```bash
cp .env.example .env
# then open .env and set:
# OPENAI_API_KEY=your-key-here
```

### 3. Edit your profile

Open `data/profile.json` and fill in your domains, goals, and available days:

```json
{
  "user_name": "Alex",
  "domains": [
    {
      "domain": "guitar",
      "level": "beginner",
      "goal": "Learn fingerpicking and play a full song",
      "hours_per_week": 3.0,
      "notes": "Struggles with chord transitions"
    }
  ],
  "available_days": ["monday", "wednesday", "saturday"],
  "preferred_session_length": 30,
  "learning_style": "hands-on",
  "last_updated": "2026-04-11T09:00:00"
}
```

Valid values:
- `domain` — `"guitar"`, `"chess"`, `"coding"`
- `level` — `"beginner"`, `"intermediate"`, `"advanced"`
- `learning_style` — `"hands-on"`, `"theory-first"`, `"mixed"`

### 4. Check in

```bash
coach checkin
```

Type what you did today, how it felt, any struggles. Press Enter twice to submit. The agent returns a **Daily Card** with your next 2–3 actions.

---

## CLI commands

| Command | What it does |
|---|---|
| `coach checkin` | Submit today's check-in and get a new card |
| `coach today` | Show today's card (generates one if missing) |
| `coach week` | Show the current weekly review card |
| `coach profile` | Display your profile |
| `coach history` | Show the last 7 check-ins |
| `coach history --days 14` | Show the last 14 check-ins |

---

## Card types

**Daily Card** — generated after every check-in. Contains 2–3 prioritised actions across your domains and a personalised motivation note.

**Weekly Card** — generated automatically on the day configured in `config.toml` (`week_end_day`, default Sunday) when you have at least 3 check-ins that week. Shows completion rate per domain and sets the focus for next week.

**Milestone Card** — triggered when you hit a streak (5 consecutive sessions by default) or report a personal best. Marks the achievement and sets your next challenge.

---

## Dummy mode

If `OPENAI_API_KEY` is not set, the coach uses a built-in dummy client that returns realistic fake cards. All dummy output is labelled `[DUMMY]` so you can tell it apart from real responses.

This is useful for:
- Trying out the interface before getting an API key
- Running tests without network calls
- Local development

---

## Project layout

```
ai_personal_coach/
├── coach/              # main package
│   ├── models.py       # data structures (ProfileCard, DailyCard, etc.)
│   ├── agent.py        # agent loop — reads context, calls LLM, returns card
│   ├── storage.py      # read/write JSON files
│   ├── prompts.py      # system prompt and LLM tool schemas
│   ├── cli.py          # CLI commands
│   ├── config.py       # loads config.toml and .env
│   ├── dummy.py        # fake LLM client for development
│   └── tools/          # Level 3 integrations (calendar, Todoist, Telegram, Lichess)
├── data/               # your local data (gitignored)
│   ├── profile.json
│   ├── checkins/
│   └── cards/
├── tests/
├── config.toml         # all settings (safe to commit)
└── .env                # your secrets (never committed)
```

---

## Configuration

All settings live in `config.toml`. The defaults work out of the box — only change what you need:

```toml
[coach]
week_end_day = "sunday"          # day that triggers the weekly card
preferred_session_length = 30    # used when sizing daily actions (minutes)
history_window_days = 7          # how many past check-ins the agent reads
max_daily_actions = 3            # cap on actions per daily card

[tools]
enable_calendar = false          # Google Calendar integration (Level 3)
enable_todoist  = false          # Todoist integration (Level 3)
enable_telegram = false          # Telegram bot notifications (Level 3)
enable_lichess  = false          # fetch daily chess puzzles (Level 3)
```

---

## Running tests

```bash
pytest tests/
```

Tests never call the real API — the LLM is always stubbed.
