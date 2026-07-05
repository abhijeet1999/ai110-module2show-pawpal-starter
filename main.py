"""Demo script to verify PawPal+ scheduling logic in the terminal."""

from typing import List, Tuple

from pawpal_system import CareTask, Owner, Pet, Scheduler


def format_schedule(
    owner: Owner,
    plan: List[Tuple[Pet, CareTask]],
    title: str = "PawPal+ | Today's Schedule",
) -> str:
    """Return a readable, column-aligned schedule for the terminal."""
    lines: List[str] = []
    divider = "-" * 72

    lines.append(title)
    lines.append(divider)
    lines.append(f"Owner: {owner.name}")
    lines.append(f"Time available today: {owner.get_available_time()} minutes")
    lines.append("")

    if not plan:
        lines.append("No tasks scheduled.")
        return "\n".join(lines)

    header = f"{'TIME':<8} {'PET':<10} {'TASK':<24} {'DURATION':<10} {'PRIORITY':<8}"
    lines.append(header)
    lines.append(divider)

    total_minutes = 0
    for pet, task in plan:
        total_minutes += task.duration_minutes
        lines.append(
            f"{task.scheduled_time or '—':<8} "
            f"{pet.name:<10} "
            f"{task.description:<24} "
            f"{task.duration_minutes} min{'':<4} "
            f"{task.priority:<8}"
        )

    remaining = owner.get_available_time() - total_minutes
    lines.append(divider)
    lines.append(
        f"Summary: {len(plan)} task(s) scheduled · "
        f"{total_minutes} min used · {remaining} min remaining"
    )

    return "\n".join(lines)


def format_task_list(items: List[Tuple[Pet, CareTask]], title: str) -> str:
    """Return a compact list of pet/task rows for filter demos."""
    lines = [title, "-" * 72]
    if not items:
        lines.append("  (none)")
        return "\n".join(lines)

    for pet, task in items:
        status = "done" if task.completed else "pending"
        time_text = task.scheduled_time or "—"
        lines.append(
            f"  {time_text} | {pet.name} | {task.description} | "
            f"{status} | due {task.due_date}"
        )
    return "\n".join(lines)


def format_explanations(explanations: List[str]) -> str:
    """Return a short, readable explanation section."""
    if not explanations:
        return ""

    lines = ["", "Why this plan:", "-" * 72]
    for index, line in enumerate(explanations, start=1):
        lines.append(f"{index}. {line}")
    return "\n".join(lines)


def format_warnings(warnings: List[str], title: str = "Schedule warnings") -> str:
    """Return conflict warnings for terminal output."""
    if not warnings:
        return f"{title}\n" + "-" * 72 + "\n  No conflicts detected."

    lines = [title, "-" * 72]
    lines.extend(f"  {warning}" for warning in warnings)
    return "\n".join(lines)


def main() -> None:
    owner = Owner(name="Jordan", available_time_minutes=90)
    scheduler = Scheduler()

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Add tasks out of chronological/priority order on purpose.
    biscuit.add_task(
        CareTask(
            description="Play session",
            duration_minutes=20,
            priority="low",
            frequency="weekly",
        )
    )
    mochi.add_task(
        CareTask(
            description="Morning walk",
            duration_minutes=30,
            priority="high",
            frequency="daily",
        )
    )
    biscuit.add_task(
        CareTask(
            description="Clean litter box",
            duration_minutes=15,
            priority="medium",
            frequency="daily",
        )
    )
    mochi.add_task(
        CareTask(
            description="Feed breakfast",
            duration_minutes=10,
            priority="high",
            frequency="daily",
        )
    )
    mochi.add_task(
        CareTask(
            description="Evening meds",
            duration_minutes=5,
            priority="high",
            frequency="daily",
        )
    )
    feed_task = mochi.get_tasks()[1]
    next_feed = mochi.mark_task_complete(feed_task)
    if next_feed is not None:
        print(
            f"Recurring task created: '{next_feed.description}' "
            f"due on {next_feed.due_date}"
        )
        print()

    all_tasks = owner.get_all_tasks()

    print(format_task_list(all_tasks, "All tasks (added out of order)"))
    print()
    print(
        format_task_list(
            scheduler.filter_tasks(all_tasks, completed=False),
            "Filter: pending tasks only",
        )
    )
    print()
    print(
        format_task_list(
            scheduler.filter_tasks(all_tasks, pet_name="Mochi"),
            "Filter: Mochi tasks only",
        )
    )
    print()
    print(
        format_task_list(
            scheduler.filter_tasks(all_tasks, pet_name="Mochi", completed=False),
            "Filter: Mochi's pending tasks",
        )
    )

    plan = scheduler.generate_plan_for_owner(owner)

    print()
    print(format_schedule(owner, plan))
    print(format_explanations(scheduler.explain_plan()))

    # Demonstrate sort_by_time on tasks with manually shuffled times.
    shuffled = [
        CareTask("Afternoon walk", 20, scheduled_time="14:30"),
        CareTask("Morning walk", 30, scheduled_time="08:00"),
        CareTask("Lunch feeding", 10, scheduled_time="12:15"),
        CareTask("Evening meds", 5, scheduled_time="18:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(shuffled)

    print()
    print("Sort by time demo (tasks added out of order):")
    print("-" * 72)
    for task in sorted_tasks:
        print(f"  {task.scheduled_time} — {task.description}")

    print()
    print("Conflict detection demo (two tasks scheduled at 09:00):")
    print("-" * 72)

    overlap_mochi = Pet(name="Mochi", species="dog")
    overlap_biscuit = Pet(name="Biscuit", species="cat")

    walk = CareTask(
        description="Morning walk",
        duration_minutes=30,
        priority="high",
        scheduled_time="09:00",
    )
    feeding = CareTask(
        description="Feed breakfast",
        duration_minutes=15,
        priority="high",
        scheduled_time="09:00",
    )
    overlap_mochi.add_task(walk)
    overlap_biscuit.add_task(feeding)

    overlapping_items = [(overlap_mochi, walk), (overlap_biscuit, feeding)]
    conflict_warnings = scheduler.detect_conflicts(overlapping_items)
    print(format_warnings(conflict_warnings))


if __name__ == "__main__":
    main()
