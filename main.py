"""Demo script to verify PawPal+ scheduling logic in the terminal."""

from typing import List, Tuple

from pawpal_system import CareTask, Owner, Pet, Scheduler


def format_schedule(
    owner: Owner,
    plan: List[Tuple[Pet, CareTask]],
) -> str:
    """Return a readable, column-aligned schedule for the terminal."""
    lines: List[str] = []
    divider = "-" * 72

    lines.append("PawPal+ | Today's Schedule")
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


def format_explanations(explanations: List[str]) -> str:
    """Return a short, readable explanation section."""
    if not explanations:
        return ""

    lines = ["", "Why this plan:", "-" * 72]
    for index, line in enumerate(explanations, start=1):
        lines.append(f"{index}. {line}")
    return "\n".join(lines)


def main() -> None:
    owner = Owner(name="Jordan", available_time_minutes=90)

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")

    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    mochi.add_task(
        CareTask(
            description="Morning walk",
            duration_minutes=30,
            priority="high",
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
    biscuit.add_task(
        CareTask(
            description="Clean litter box",
            duration_minutes=15,
            priority="medium",
            frequency="daily",
        )
    )
    biscuit.add_task(
        CareTask(
            description="Play session",
            duration_minutes=20,
            priority="low",
            frequency="weekly",
        )
    )

    scheduler = Scheduler()
    plan = scheduler.generate_plan_for_owner(owner)

    print(format_schedule(owner, plan))
    print(format_explanations(scheduler.explain_plan()))


if __name__ == "__main__":
    main()
