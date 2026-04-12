from __future__ import annotations

# CLI commands. Human-readable output only — no raw JSON to stdout.
# All commands work offline except the LLM call in `checkin`.

import logging
from datetime import datetime

import click

from coach import agent, storage
from coach.config import settings
from coach.models import CheckIn, Status

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        handlers=[
            logging.FileHandler(settings.log_dir / "agent.log"),
            logging.StreamHandler(),
        ],
    )


def _render_daily_card(card) -> None:  # type: ignore[type-arg]
    click.echo(f"\n=== Daily Card — {card.date.strftime('%A, %B %d')} ===")
    click.echo(f"\n{card.motivation_note}\n")
    for i, action in enumerate(card.actions, 1):
        status_icon = {"done": "✓", "skipped": "✗", "partial": "~", "pending": "○"}.get(
            action.status.value, "○"
        )
        click.echo(
            f"  {i}. [{status_icon}] [{action.domain.value.upper()}] "
            f"{action.description} ({action.duration_minutes}min)"
        )
        if action.feedback:
            click.echo(f"       → {action.feedback}")
    click.echo()


def _render_weekly_card(card) -> None:  # type: ignore[type-arg]
    click.echo(
        f"\n=== Weekly Card — {card.week_start.strftime('%b %d')} "
        f"to {card.week_end.strftime('%b %d')} ==="
    )
    click.echo(f"\nHighlight: {card.highlight}\n")
    click.echo("Domain summaries:")
    for domain, summary in card.domain_summaries.items():
        rate = card.completion_rate.get(domain, 0)
        click.echo(f"  {domain.value.upper()} ({rate:.0%}): {summary}")
    click.echo("\nNext week focus:")
    for action in card.next_week_focus:
        click.echo(f"  · [{action.domain.value.upper()}] {action.description} ({action.duration_minutes}min)")
    click.echo()


@click.group()
def cli() -> None:
    """AI Personal Coach — your agentic learning companion."""
    _setup_logging()


@cli.command()
def checkin() -> None:
    """Submit today's check-in and receive a new card."""
    profile = storage.load_profile()
    if profile is None:
        click.echo("No profile found. Run `coach profile` to set up your profile first.")
        return

    click.echo("How did it go today? (describe what you did, how you felt, any struggles)")
    click.echo("Press Enter twice when done.\n")

    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    user_text = "\n".join(lines).strip()

    energy_str = click.prompt("Energy level today (1–5)", type=click.IntRange(1, 5))

    checkins = storage.load_recent_checkins(settings.history_window_days)
    click.echo("\nThinking...\n")

    card = agent.run(user_text=user_text, profile=profile, checkins=checkins)

    # Save check-in after card generation
    today_card = storage.load_daily_card(datetime.now())
    completed_actions = []
    if today_card:
        for action in today_card.actions:
            if action.status != Status.PENDING:
                completed_actions.append(action)

    checkin_record = CheckIn(
        date=datetime.now(),
        completed_actions=completed_actions,
        energy_level=energy_str,
        free_text=user_text,
    )
    storage.save_checkin(checkin_record)

    from coach.models import DailyCard, WeeklyCard, MilestoneCard
    if isinstance(card, DailyCard):
        _render_daily_card(card)
    elif isinstance(card, WeeklyCard):
        _render_weekly_card(card)
    else:
        click.echo(f"\n=== Milestone! ===")
        click.echo(f"Domain: {card.domain.value.upper()}")
        click.echo(f"Achievement: {card.achievement}")
        click.echo(f"Next challenge: {card.next_challenge}\n")


@cli.command()
def today() -> None:
    """Display today's DailyCard (generates one if missing)."""
    now = datetime.now()
    card = storage.load_daily_card(now)
    if card is None:
        profile = storage.load_profile()
        if profile is None:
            click.echo("No profile found. Run `coach profile` to set up your profile first.")
            return
        checkins = storage.load_recent_checkins(settings.history_window_days)
        click.echo("No card for today yet — generating one...\n")
        card = agent.run(user_text="Good morning! What should I focus on today?", profile=profile, checkins=checkins)
    _render_daily_card(card)


@cli.command()
def week() -> None:
    """Display the current WeeklyCard."""
    card = storage.load_weekly_card(datetime.now())
    if card is None:
        click.echo("No weekly card yet. Check back at the end of the week.")
        return
    _render_weekly_card(card)


@cli.command()
def profile() -> None:
    """Display the current ProfileCard."""
    p = storage.load_profile()
    if p is None:
        click.echo("No profile found. Create data/profile.json to get started.")
        return
    click.echo(f"\n=== Profile: {p.user_name} ===")
    click.echo(f"Available days: {', '.join(p.available_days)}")
    click.echo(f"Preferred session: {p.preferred_session_length}min")
    click.echo(f"Learning style: {p.learning_style}")
    click.echo("\nDomains:")
    for dp in p.domains:
        click.echo(
            f"  {dp.domain.value.upper()} | {dp.level.value} | Goal: {dp.goal} "
            f"| {dp.hours_per_week}h/week"
        )
        if dp.notes:
            click.echo(f"    Notes: {dp.notes}")
    click.echo(f"\nLast updated: {p.last_updated.strftime('%Y-%m-%d %H:%M')}\n")


@cli.command()
@click.option("--days", default=7, show_default=True, help="Number of past check-ins to show.")
def history(days: int) -> None:
    """Display past check-ins."""
    checkins = storage.load_recent_checkins(days)
    if not checkins:
        click.echo("No check-ins recorded yet.")
        return
    for ci in checkins:
        click.echo(f"\n--- {ci.date.strftime('%Y-%m-%d')} — energy {ci.energy_level}/5 ---")
        click.echo(ci.free_text[:300] + ("…" if len(ci.free_text) > 300 else ""))
        for a in ci.completed_actions:
            click.echo(f"  [{a.status.value}] {a.domain.value}: {a.description}")
    click.echo()
