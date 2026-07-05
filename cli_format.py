"""Terminal formatting helpers for PawPal+ CLI output."""

from __future__ import annotations

from typing import List, Tuple

from tabulate import tabulate

from pawpal_system import CareTask, Owner, Pet, Scheduler

# ANSI color codes for terminal status indicators
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
DIM = "\033[2m"

SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "other": "🐾"}
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
FREQUENCY_EMOJI = {"daily": "🔁", "weekly": "📅", "once": "1️⃣"}

TASK_KEYWORDS: List[Tuple[str, str]] = [
    ("walk", "🚶"),
    ("feed", "🍽️"),
    ("breakfast", "🍽️"),
    ("lunch", "🥣"),
    ("med", "💊"),
    ("meds", "💊"),
    ("bath", "🛁"),
    ("groom", "✂️"),
    ("brush", "🪮"),
    ("play", "🎾"),
    ("litter", "🧹"),
    ("vet", "🏥"),
    ("sleep", "😴"),
]


def task_type_emoji(description: str) -> str:
    """Return an emoji hint based on keywords in the task description."""
    lower = description.lower()
    for keyword, emoji in TASK_KEYWORDS:
        if keyword in lower:
            return emoji
    return "📋"


def format_priority_label(priority: str, *, color: bool = True) -> str:
    """Return a color-coded priority label with emoji."""
    emoji = PRIORITY_EMOJI.get(priority.lower(), "⚪")
    if not color:
        return f"{emoji} {priority}"
    color_code = {"high": RED, "medium": YELLOW, "low": GREEN}.get(priority.lower(), "")
    return f"{emoji} {color_code}{priority}{RESET}"


def format_status_label(completed: bool, *, color: bool = True) -> str:
    """Return a color-coded completion status."""
    if completed:
        return f"{GREEN}✅ Done{RESET}" if color else "✅ Done"
    return f"{YELLOW}⏳ Pending{RESET}" if color else "⏳ Pending"


def format_frequency_label(frequency: str) -> str:
    """Return frequency with a small emoji indicator."""
    emoji = FREQUENCY_EMOJI.get(frequency.lower(), "📋")
    return f"{emoji} {frequency}"


def format_section_header(title: str) -> str:
    """Return a bold, colored section heading."""
    return f"\n{BOLD}{CYAN}{title}{RESET}\n{'=' * len(title)}"


def format_schedule_table(
    owner: Owner,
    plan: List[Tuple[Pet, CareTask]],
    title: str = "PawPal+ | Today's Schedule",
) -> str:
    """Build a tabulate table for the daily schedule."""
    lines = [format_section_header(title), f"Owner: {owner.name}"]
    lines.append(
        f"Time available today: {owner.get_available_time()} minutes\n"
    )

    if not plan:
        lines.append(f"{YELLOW}No tasks scheduled.{RESET}")
        return "\n".join(lines)

    rows = []
    total_minutes = 0
    for pet, task in plan:
        total_minutes += task.duration_minutes
        rows.append(
            [
                task.scheduled_time or "—",
                f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}",
                f"{task_type_emoji(task.description)} {task.description}",
                f"{task.duration_minutes} min",
                format_priority_label(task.priority),
            ]
        )

    lines.append(
        tabulate(
            rows,
            headers=["Time", "Pet", "Task", "Duration", "Priority"],
            tablefmt="rounded_outline",
        )
    )

    remaining = owner.get_available_time() - total_minutes
    lines.append(
        f"\n{DIM}Summary:{RESET} {len(plan)} task(s) · "
        f"{GREEN}{total_minutes} min used{RESET} · "
        f"{CYAN}{remaining} min remaining{RESET}"
    )
    return "\n".join(lines)


def format_task_table(
    items: List[Tuple[Pet, CareTask]],
    title: str,
) -> str:
    """Build a tabulate table for a filtered task list."""
    lines = [format_section_header(title)]

    if not items:
        lines.append(f"{DIM}  (none){RESET}")
        return "\n".join(lines)

    rows = []
    for pet, task in items:
        rows.append(
            [
                task.scheduled_time or "—",
                f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}",
                f"{task_type_emoji(task.description)} {task.description}",
                format_priority_label(task.priority),
                format_frequency_label(task.frequency),
                format_status_label(task.completed),
                str(task.due_date),
            ]
        )

    lines.append(
        tabulate(
            rows,
            headers=["Time", "Pet", "Task", "Priority", "Frequency", "Status", "Due"],
            tablefmt="rounded_outline",
        )
    )
    return "\n".join(lines)


def format_priority_queue_table(
    tasks: List[CareTask],
    scheduler: Scheduler,
    title: str,
) -> str:
    """Build a tabulate table showing priority ranking before scheduling."""
    lines = [format_section_header(title)]

    rows = []
    for index, task in enumerate(scheduler.sort_tasks_by_priority(tasks), start=1):
        rows.append(
            [
                index,
                format_priority_label(task.priority),
                f"{task.duration_minutes} min",
                f"{task_type_emoji(task.description)} {task.description}",
            ]
        )

    lines.append(
        tabulate(
            rows,
            headers=["Rank", "Priority", "Duration", "Task"],
            tablefmt="rounded_outline",
        )
    )
    return "\n".join(lines)


def format_warnings_block(warnings: List[str], title: str = "Schedule warnings") -> str:
    """Return conflict warnings with a red header."""
    lines = [format_section_header(title)]
    if not warnings:
        lines.append(f"{GREEN}  No conflicts detected.{RESET}")
        return "\n".join(lines)

    for warning in warnings:
        lines.append(f"{RED}  ⚠️  {warning}{RESET}")
    return "\n".join(lines)


def format_explanations_block(explanations: List[str]) -> str:
    """Return numbered plan explanations."""
    if not explanations:
        return ""

    lines = [format_section_header("Why this plan")]
    for index, line in enumerate(explanations, start=1):
        lines.append(f"  {index}. {line}")
    return "\n".join(lines)
