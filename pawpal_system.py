"""PawPal+ backend logic layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

PRIORITY_RANK: Dict[str, int] = {"high": 3, "medium": 2, "low": 1}
VALID_FREQUENCIES = ("daily", "weekly", "once")


@dataclass
class CareTask:
    """A single care activity for a pet."""

    description: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "daily"
    completed: bool = False
    scheduled_time: Optional[str] = None

    @property
    def title(self) -> str:
        """Alias used by the Streamlit UI and older references."""
        return self.description

    def get_priority_rank(self) -> int:
        """Return a numeric rank for sorting tasks by priority."""
        return PRIORITY_RANK.get(self.priority.lower(), 0)

    def assign_time(self, time_slot: str) -> None:
        """Set the scheduled time for this task."""
        self.scheduled_time = time_slot

    def clear_scheduled_time(self) -> None:
        """Clear any previously assigned time before rebuilding a plan."""
        self.scheduled_time = None

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not yet completed."""
        self.completed = False

    def is_pending(self) -> bool:
        """Return True if the task still needs to be done."""
        return not self.completed

    def is_due_for_planning(self) -> bool:
        """Return True if the task should be considered for today's plan."""
        if self.completed:
            return False
        if self.frequency not in VALID_FREQUENCIES:
            return True
        return True


@dataclass
class Pet:
    """One pet and the care tasks assigned to them."""

    name: str
    species: str
    owner_name: Optional[str] = None
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet's list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> None:
        """Remove the first care task matching the description."""
        self.tasks = [task for task in self.tasks if task.description != description]

    def get_tasks(self) -> List[CareTask]:
        """Return all care tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[CareTask]:
        """Return tasks that are not yet completed."""
        return [task for task in self.tasks if task.is_pending()]


@dataclass
class Owner:
    """An owner who manages multiple pets and shared scheduling constraints."""

    name: str
    available_time_minutes: int
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def get_available_time(self) -> int:
        """Return how many minutes the owner has available today."""
        return self.available_time_minutes

    def update_preferences(self, preferences: List[str]) -> None:
        """Replace the owner's preferences."""
        self.preferences = list(preferences)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list and link it back to this owner."""
        pet.owner_name = self.name
        if not any(existing.name == pet.name for existing in self.pets):
            self.pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner."""
        return list(self.pets)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return a pet by name, or None if this owner does not have that pet."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self) -> List[Tuple[Pet, CareTask]]:
        """Return every task across all of this owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]

    def get_all_pending_tasks(self) -> List[Tuple[Pet, CareTask]]:
        """Return every incomplete task across all of this owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]


class Scheduler:
    """Plans and organizes care tasks using owner time and task priority."""

    def __init__(self) -> None:
        """Initialize empty plan state for a new scheduling run."""
        self.planned_tasks: List[CareTask] = []
        self.planned_items: List[Tuple[Pet, CareTask]] = []
        self.explanations: List[str] = []
        self.skipped_count: int = 0

    def generate_plan(self, pet: Pet, owner: Owner) -> List[CareTask]:
        """Build a daily plan for one pet using the owner's time budget."""
        self._reset_plan_state()
        self._clear_scheduled_times(owner)

        pending = [task for task in pet.get_pending_tasks() if task.is_due_for_planning()]
        sorted_tasks = self.sort_tasks_by_priority(pending)
        fitted = self.fit_tasks_to_time(sorted_tasks, owner.get_available_time())
        self._assign_time_slots(fitted)
        self.skipped_count = len(pending) - len(fitted)

        self.planned_tasks = fitted
        self.planned_items = [(pet, task) for task in fitted]
        self.explanations = self.explain_plan()
        return fitted

    def generate_plan_for_owner(self, owner: Owner) -> List[Tuple[Pet, CareTask]]:
        """Build one daily plan across all of an owner's pets."""
        self._reset_plan_state()
        self._clear_scheduled_times(owner)

        pending_items = [
            (pet, task)
            for pet, task in owner.get_all_pending_tasks()
            if task.is_due_for_planning()
        ]
        pending_tasks = [task for _, task in pending_items]
        sorted_tasks = self.sort_tasks_by_priority(pending_tasks)
        fitted = self.fit_tasks_to_time(sorted_tasks, owner.get_available_time())
        self._assign_time_slots(fitted)
        self.skipped_count = len(pending_tasks) - len(fitted)

        task_to_pet = {id(task): pet for pet, task in pending_items}
        self.planned_items = [(task_to_pet[id(task)], task) for task in fitted]
        self.planned_tasks = fitted
        self.explanations = self.explain_plan()
        return self.planned_items

    def sort_tasks_by_priority(self, tasks: List[CareTask]) -> List[CareTask]:
        """Sort tasks so higher-priority items come first."""
        return sorted(
            tasks,
            key=lambda task: (-task.get_priority_rank(), task.duration_minutes),
        )

    def fit_tasks_to_time(self, tasks: List[CareTask], minutes: int) -> List[CareTask]:
        """Select tasks that fit within the available time."""
        selected: List[CareTask] = []
        remaining = minutes

        for task in tasks:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes

        return selected

    def explain_plan(self) -> List[str]:
        """Return human-readable reasons for the planned schedule."""
        if not self.planned_items:
            return ["No tasks were scheduled. Add pending tasks or increase available time."]

        explanations: List[str] = []
        for pet, task in self.planned_items:
            time_text = task.scheduled_time or "unscheduled"
            explanations.append(
                f"{time_text} — {task.description} for {pet.name} "
                f"({task.duration_minutes} min, {task.priority} priority, "
                f"{task.frequency}): chosen because it is pending and ranked highly "
                f"within today's {len(self.planned_items)}-task plan."
            )

        skipped = self.skipped_count
        if skipped:
            explanations.append(
                f"{skipped} pending task(s) were skipped because they did not fit "
                "in the owner's available time after priority sorting."
            )

        return explanations

    def _reset_plan_state(self) -> None:
        """Clear the scheduler's stored plan, explanations, and skip count."""
        self.planned_tasks = []
        self.planned_items = []
        self.explanations = []
        self.skipped_count = 0

    def _clear_scheduled_times(self, owner: Owner) -> None:
        """Remove scheduled times from all of an owner's tasks before replanning."""
        for _, task in owner.get_all_tasks():
            task.clear_scheduled_time()

    def _assign_time_slots(
        self,
        tasks: List[CareTask],
        start_hour: int = 8,
    ) -> None:
        """Assign sequential start times to tasks beginning at the given hour."""
        current_minutes = start_hour * 60

        for task in tasks:
            hours = current_minutes // 60
            minutes = current_minutes % 60
            task.assign_time(f"{hours:02d}:{minutes:02d}")
            current_minutes += task.duration_minutes


# Alias matching common project terminology.
Task = CareTask
