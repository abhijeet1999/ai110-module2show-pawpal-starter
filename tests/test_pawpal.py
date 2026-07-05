"""Tests for PawPal+ core task and pet behavior."""

from datetime import date, timedelta

from pawpal_system import CareTask, Pet, Scheduler


def test_mark_complete_changes_task_status():
    task = CareTask(description="Morning walk", duration_minutes=20)

    assert task.completed is False
    assert task.is_pending() is True

    task.mark_complete()

    assert task.completed is True
    assert task.is_pending() is False


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(description="Feed breakfast", duration_minutes=10)

    assert len(pet.get_tasks()) == 0

    pet.add_task(task)

    assert len(pet.get_tasks()) == 1
    assert pet.get_tasks()[0].description == "Feed breakfast"


def test_daily_task_completion_creates_next_occurrence():
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


def test_detect_conflicts_for_same_start_time():
    scheduler = Scheduler()
    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")

    walk = CareTask("Morning walk", 30, scheduled_time="09:00")
    feeding = CareTask("Feed breakfast", 15, scheduled_time="09:00")

    warnings = scheduler.detect_conflicts([(mochi, walk), (biscuit, feeding)])

    assert len(warnings) == 1
    assert "Warning:" in warnings[0]
    assert "Morning walk" in warnings[0]
    assert "Feed breakfast" in warnings[0]


