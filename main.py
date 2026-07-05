"""Demo script to verify PawPal+ scheduling logic in the terminal."""

from datetime import date

from cli_format import (
    format_explanations_block,
    format_priority_queue_table,
    format_schedule_table,
    format_section_header,
    format_status_label,
    format_task_table,
    format_warnings_block,
    task_type_emoji,
)
from pawpal_system import CareTask, Owner, Pet, Scheduler


def demo_priority_scheduling() -> None:
    """Show how the scheduler ranks tasks by priority before assigning time slots."""
    owner = Owner(name="Alex", available_time_minutes=30)
    scheduler = Scheduler()
    pet = Pet(name="Luna", species="dog")
    owner.add_pet(pet)

    pet.add_task(CareTask("Brush coat", 15, priority="low"))
    pet.add_task(CareTask("Give meds", 10, priority="high"))
    pet.add_task(CareTask("Morning walk", 25, priority="medium"))
    pet.add_task(CareTask("Feed breakfast", 10, priority="high"))

    pending = pet.get_pending_tasks()
    print(format_priority_queue_table(pending, scheduler, "Step 1: Priority queue (High → Low)"))

    plan = scheduler.generate_plan_for_owner(owner)
    print(
        format_schedule_table(
            owner,
            plan,
            title="Step 2: Daily plan (time order — high-priority tasks scheduled first)",
        )
    )

    print(format_section_header("Step 3: Same plan sorted by priority, then time"))
    for pet_item, task in scheduler.sort_items_by_priority_then_time(plan):
        print(
            f"  {task_type_emoji(task.description)} {task.description:<22} "
            f"| {task.scheduled_time or '—':<8} | {task.duration_minutes:>2} min"
        )

    if scheduler.skipped_count:
        print(
            f"\n  Note: {scheduler.skipped_count} lower-priority task(s) skipped — "
            f"only {owner.get_available_time()} minutes available."
        )

    print("\n" + "=" * 72 + "\n")


def demo_weekly_rescheduling() -> None:
    """Show formatted output when a weekly task is completed and rescheduled."""
    scheduler = Scheduler()
    pet = Pet(name="Biscuit", species="cat")
    today = date(2026, 7, 4)

    pet.add_task(
        CareTask(
            description="Deep clean litter box",
            duration_minutes=20,
            priority="medium",
            frequency="weekly",
            due_date=today,
        )
    )

    task = pet.get_tasks()[0]
    print(format_section_header("Weekly task rescheduling demo"))
    print(format_task_table([(pet, task)], "Before completion"))

    next_task = pet.mark_task_complete(task, today=today)
    rows = [(pet, task)]
    if next_task:
        rows.append((pet, next_task))

    print(format_task_table(rows, "After completion (original done, next weekly instance created)"))
    if next_task:
        print(
            f"  Next occurrence: {task_type_emoji(next_task.description)} "
            f"{next_task.description} due {next_task.due_date} "
            f"({format_status_label(next_task.completed)})"
        )
    print("\n" + "=" * 72 + "\n")


def main() -> None:
    demo_priority_scheduling()
    demo_weekly_rescheduling()

    owner = Owner(name="Jordan", available_time_minutes=90)
    scheduler = Scheduler()

    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

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
            f"Recurring task created: {task_type_emoji(next_feed.description)} "
            f"'{next_feed.description}' due on {next_feed.due_date}\n"
        )

    all_tasks = owner.get_all_tasks()

    print(format_task_table(all_tasks, "All tasks (added out of order)"))
    print(
        format_task_table(
            scheduler.filter_tasks(all_tasks, completed=False),
            "Filter: pending tasks only",
        )
    )
    print(
        format_task_table(
            scheduler.filter_tasks(all_tasks, pet_name="Mochi"),
            "Filter: Mochi tasks only",
        )
    )
    print(
        format_task_table(
            scheduler.filter_tasks(all_tasks, pet_name="Mochi", completed=False),
            "Filter: Mochi's pending tasks",
        )
    )

    plan = scheduler.generate_plan_for_owner(owner)
    print(format_schedule_table(owner, plan))
    print(format_explanations_block(scheduler.explain_plan()))

    shuffled = [
        CareTask("Afternoon walk", 20, scheduled_time="14:30"),
        CareTask("Morning walk", 30, scheduled_time="08:00"),
        CareTask("Lunch feeding", 10, scheduled_time="12:15"),
        CareTask("Evening meds", 5, scheduled_time="18:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(shuffled)

    print(format_section_header("Sort by time demo (tasks added out of order)"))
    for task in sorted_tasks:
        print(f"  {task.scheduled_time} — {task_type_emoji(task.description)} {task.description}")

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
    overlapping_items = [(overlap_mochi, walk), (overlap_biscuit, feeding)]
    print(format_warnings_block(scheduler.detect_conflicts(overlapping_items)))

    next_slot = scheduler.find_next_available_slot(overlapping_items, duration_minutes=20)
    print(format_section_header("Next available slot demo"))
    if next_slot:
        print(f"  Earliest 20-minute gap with no overlap: {next_slot}")
    else:
        print("  No open slot found before end of day.")

    print(format_section_header("Persistence demo"))
    owner.save_to_json("data.json")
    reloaded = Owner.load_from_json("data.json")
    print(f"  Saved and reloaded owner '{reloaded.name}' with {len(reloaded.get_pets())} pet(s).")


if __name__ == "__main__":
    main()
