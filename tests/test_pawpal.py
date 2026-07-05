"""Tests for PawPal+ core task and pet behavior."""

from pawpal_system import CareTask, Pet


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
