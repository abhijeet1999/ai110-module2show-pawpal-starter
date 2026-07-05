"""Tests for PawPal+ core task, scheduling, and algorithm behavior."""

from datetime import date, timedelta

from pawpal_system import CareTask, Owner, Pet, Scheduler


def test_mark_complete_changes_task_status():
    """Completing a task should flip completed to True and pending to False."""
    task = CareTask(description="Morning walk", duration_minutes=20)

    assert task.completed is False
    assert task.is_pending() is True

    task.mark_complete()

    assert task.completed is True
    assert task.is_pending() is False


def test_add_task_increases_pet_task_count():
    """Adding a task should increase the pet's stored task list by one."""
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(description="Feed breakfast", duration_minutes=10)

    assert len(pet.get_tasks()) == 0

    pet.add_task(task)

    assert len(pet.get_tasks()) == 1
    assert pet.get_tasks()[0].description == "Feed breakfast"


def test_sort_by_time_returns_tasks_in_chronological_order():
    """sort_by_time() should order tasks earliest to latest by scheduled_time."""
    scheduler = Scheduler()
    tasks = [
        CareTask("Afternoon walk", 20, scheduled_time="14:30"),
        CareTask("Morning walk", 30, scheduled_time="08:00"),
        CareTask("Lunch feeding", 10, scheduled_time="12:15"),
    ]

    sorted_tasks = scheduler.sort_by_time(tasks)
    times = [task.scheduled_time for task in sorted_tasks]

    assert times == ["08:00", "12:15", "14:30"]


def test_daily_recurrence_creates_task_for_following_day():
    """Marking a daily task complete should create a new task due the next day."""
    pet = Pet(name="Mochi", species="dog")
    today = date(2026, 7, 4)
    task = CareTask(
        description="Feed breakfast",
        duration_minutes=10,
        frequency="daily",
        due_date=today,
    )
    pet.add_task(task)

    next_task = pet.mark_task_complete(task, today=today)

    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == today + timedelta(days=1)
    assert len(pet.get_tasks()) == 2


def test_weekly_task_completion_creates_next_occurrence():
    """Marking a weekly task complete should create a new task due in 7 days."""
    pet = Pet(name="Biscuit", species="cat")
    today = date(2026, 7, 4)
    task = CareTask(
        description="Deep clean litter box",
        duration_minutes=20,
        frequency="weekly",
        due_date=today,
    )
    pet.add_task(task)

    next_task = pet.mark_task_complete(task, today=today)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=7)


def test_once_task_does_not_create_next_occurrence():
    """One-time tasks should not create a follow-up task when completed."""
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(
        description="Annual vet visit",
        duration_minutes=60,
        frequency="once",
    )
    pet.add_task(task)

    next_task = pet.mark_task_complete(task)

    assert next_task is None
    assert len(pet.get_tasks()) == 1


def test_conflict_detection_flags_duplicate_times():
    """detect_conflicts() should warn when two tasks share the same start time."""
    scheduler = Scheduler()
    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")

    walk = CareTask("Morning walk", 30, scheduled_time="09:00")
    feeding = CareTask("Feed breakfast", 15, scheduled_time="09:00")

    warnings = scheduler.detect_conflicts([(mochi, walk), (biscuit, feeding)])

    assert len(warnings) == 1
    assert warnings[0].startswith("Warning:")
    assert "Morning walk" in warnings[0]
    assert "Feed breakfast" in warnings[0]


def test_generate_plan_sorts_scheduled_items_by_time():
    """After planning, scheduled items should appear in chronological order."""
    owner = Owner(name="Jordan", available_time_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    pet.add_task(CareTask("Feed breakfast", 10, priority="high"))
    pet.add_task(CareTask("Morning walk", 30, priority="high"))
    pet.add_task(CareTask("Play time", 20, priority="medium"))

    scheduler = Scheduler()
    plan = scheduler.generate_plan_for_owner(owner)
    time_keys = [scheduler._time_sort_key(task) for _, task in plan]

    assert time_keys == sorted(time_keys)
