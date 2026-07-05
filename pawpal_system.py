"""PawPal+ backend logic layer."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PRIORITY_RANK: Dict[str, int] = {"high": 3, "medium": 2, "low": 1}
VALID_PRIORITIES = ("high", "medium", "low")
VALID_FREQUENCIES = ("daily", "weekly", "once")


@dataclass
class CareTask:
    """A single care activity for a pet.

    Priority must be one of: ``high``, ``medium``, or ``low`` (see ``VALID_PRIORITIES``).
    """

    description: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "daily"
    completed: bool = False
    scheduled_time: Optional[str] = None
    due_date: date = field(default_factory=date.today)

    @property
    def title(self) -> str:
        """Alias used by the Streamlit UI and older references."""
        return self.description

    def get_priority_rank(self) -> int:
        """Return a numeric rank for sorting tasks by priority (High=3, Medium=2, Low=1)."""
        return PRIORITY_RANK.get(self.priority.lower(), 0)

    def normalize_priority(self) -> None:
        """Coerce unknown priority labels to medium."""
        if self.priority.lower() not in PRIORITY_RANK:
            self.priority = "medium"

    def assign_time(self, time_slot: str) -> None:
        """Set the scheduled time for this task."""
        self.scheduled_time = time_slot

    def clear_scheduled_time(self) -> None:
        """Clear any previously assigned time before rebuilding a plan."""
        self.scheduled_time = None

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_due_date(self, from_date: Optional[date] = None) -> Optional[date]:
        """Calculate the next due date using timedelta (daily +1 day, weekly +7 days)."""
        base_date = from_date or date.today()
        if self.frequency == "daily":
            return base_date + timedelta(days=1)
        if self.frequency == "weekly":
            return base_date + timedelta(days=7)
        return None

    def create_next_occurrence(self, from_date: Optional[date] = None) -> Optional[CareTask]:
        """Create a fresh incomplete task copy scheduled for the next recurrence."""
        next_due = self.next_due_date(from_date)
        if next_due is None:
            return None

        return CareTask(
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            due_date=next_due,
        )

    def mark_incomplete(self) -> None:
        """Mark this task as not yet completed."""
        self.completed = False

    def is_pending(self) -> bool:
        """Return True if the task still needs to be done."""
        return not self.completed

    def is_due_for_planning(self, today: Optional[date] = None) -> bool:
        """Return True when an incomplete task is due on or before the given date."""
        if self.completed:
            return False
        if self.frequency == "once":
            return True

        check_date = today or date.today()
        return self.due_date <= check_date


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

    def mark_task_complete(
        self, task: CareTask, today: Optional[date] = None
    ) -> Optional[CareTask]:
        """Complete a task and auto-create the next daily or weekly occurrence."""
        task.mark_complete()
        next_task = task.create_next_occurrence(today)
        if next_task is not None:
            self.add_task(next_task)
        return next_task


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

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Serialize this owner, pets, and tasks to a JSON file."""
        path = Path(filepath)
        path.write_text(
            json.dumps(_owner_to_dict(self), indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def load_from_json(filepath: str = "data.json") -> Owner:
        """Rebuild an Owner graph from a JSON file created by save_to_json()."""
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        return _owner_from_dict(data)


class Scheduler:
    """Plans and organizes care tasks using owner time and task priority."""

    def __init__(self) -> None:
        """Initialize empty plan state for a new scheduling run."""
        self.planned_tasks: List[CareTask] = []
        self.planned_items: List[Tuple[Pet, CareTask]] = []
        self.explanations: List[str] = []
        self.skipped_count: int = 0
        self.conflicts: List[str] = []

    def generate_plan(self, pet: Pet, owner: Owner, today: Optional[date] = None) -> List[CareTask]:
        """Build a daily plan for one pet using the owner's time budget."""
        self._reset_plan_state()
        self._clear_scheduled_times(owner)

        pending = [
            task
            for task in pet.get_pending_tasks()
            if task.is_due_for_planning(today)
        ]
        sorted_tasks = self.sort_tasks_by_priority(pending)
        fitted = self.fit_tasks_to_time(sorted_tasks, owner.get_available_time())
        self._assign_time_slots(fitted)
        self.skipped_count = len(pending) - len(fitted)

        self.planned_tasks = self.sort_by_time(fitted)
        self.planned_items = [(pet, task) for task in self.planned_tasks]
        self.conflicts = self.detect_conflicts(self.planned_items)
        self.explanations = self.explain_plan()
        return self.planned_tasks

    def generate_plan_for_owner(
        self, owner: Owner, today: Optional[date] = None
    ) -> List[Tuple[Pet, CareTask]]:
        """Build one daily plan across all of an owner's pets."""
        self._reset_plan_state()
        self._clear_scheduled_times(owner)

        pending_items = [
            (pet, task)
            for pet, task in owner.get_all_pending_tasks()
            if task.is_due_for_planning(today)
        ]
        pending_tasks = [task for _, task in pending_items]
        sorted_tasks = self.sort_tasks_by_priority(pending_tasks)
        fitted = self.fit_tasks_to_time(sorted_tasks, owner.get_available_time())
        self._assign_time_slots(fitted)
        self.skipped_count = len(pending_tasks) - len(fitted)

        task_to_pet = {id(task): pet for pet, task in pending_items}
        self.planned_items = [(task_to_pet[id(task)], task) for task in fitted]
        self.planned_items = self.sort_items_by_time(self.planned_items)
        self.planned_tasks = [task for _, task in self.planned_items]
        self.conflicts = self.detect_conflicts(self.planned_items)
        self.explanations = self.explain_plan()
        return self.planned_items

    def sort_tasks_by_priority(self, tasks: List[CareTask]) -> List[CareTask]:
        """Sort tasks by priority rank first, then by shorter duration as a tiebreaker."""
        return sorted(
            tasks,
            key=lambda task: (-task.get_priority_rank(), task.duration_minutes),
        )

    def sort_tasks_by_priority_then_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Sort tasks by priority (High before Low), then by scheduled time (earliest first)."""
        return sorted(
            tasks,
            key=lambda task: (-task.get_priority_rank(), self._time_sort_key(task)),
        )

    def sort_by_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Sort tasks by scheduled_time (HH:MM) using a lambda key converted to minutes."""
        return sorted(tasks, key=lambda task: self._time_sort_key(task))

    def sort_items_by_time(
        self, items: List[Tuple[Pet, CareTask]]
    ) -> List[Tuple[Pet, CareTask]]:
        """Sort scheduled pet-task pairs chronologically for display in the daily plan."""
        return sorted(items, key=lambda item: self._time_sort_key(item[1]))

    def sort_items_by_priority_then_time(
        self, items: List[Tuple[Pet, CareTask]]
    ) -> List[Tuple[Pet, CareTask]]:
        """Sort pet-task pairs by priority first, then by scheduled time."""
        return sorted(
            items,
            key=lambda item: (-item[1].get_priority_rank(), self._time_sort_key(item[1])),
        )

    def filter_tasks(
        self,
        items: List[Tuple[Pet, CareTask]],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Tuple[Pet, CareTask]]:
        """Filter tasks by optional pet name and/or completion status without modifying data."""
        filtered = items

        if pet_name is not None:
            filtered = [(pet, task) for pet, task in filtered if pet.name == pet_name]

        if completed is not None:
            filtered = [(pet, task) for pet, task in filtered if task.completed == completed]

        return filtered

    def fit_tasks_to_time(self, tasks: List[CareTask], minutes: int) -> List[CareTask]:
        """Select tasks that fit within the available time."""
        selected: List[CareTask] = []
        remaining = minutes

        for task in tasks:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes

        return selected

    def detect_conflicts(self, items: List[Tuple[Pet, CareTask]]) -> List[str]:
        """Detect overlapping time ranges and return warning strings without raising errors."""
        warnings: List[str] = []
        scheduled: List[Tuple[Pet, CareTask, Tuple[int, int]]] = []

        for pet, task in items:
            time_range = self._task_time_range(task)
            if time_range is not None:
                scheduled.append((pet, task, time_range))

        for index, (pet_a, task_a, (start_a, end_a)) in enumerate(scheduled):
            for pet_b, task_b, (start_b, end_b) in scheduled[index + 1 :]:
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        "Warning: "
                        f"'{task_a.description}' for {pet_a.name} "
                        f"({self._format_clock(start_a)}–{self._format_clock(end_a)}) overlaps with "
                        f"'{task_b.description}' for {pet_b.name} "
                        f"({self._format_clock(start_b)}–{self._format_clock(end_b)})."
                    )

        return warnings

    def find_next_available_slot(
        self,
        items: List[Tuple[Pet, CareTask]],
        duration_minutes: int,
        start_hour: int = 8,
        end_hour: int = 22,
    ) -> Optional[str]:
        """Return the earliest HH:MM start time where a task fits without overlapping."""
        busy_ranges: List[Tuple[int, int]] = []
        for _, task in items:
            time_range = self._task_time_range(task)
            if time_range is not None:
                busy_ranges.append(time_range)

        busy_ranges.sort(key=lambda time_range: time_range[0])

        cursor = start_hour * 60
        day_end = end_hour * 60

        for start, end in busy_ranges:
            if cursor + duration_minutes <= start:
                return self._format_clock(cursor)
            cursor = max(cursor, end)

        if cursor + duration_minutes <= day_end:
            return self._format_clock(cursor)

        return None

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

        explanations.extend(self.conflicts)
        return explanations

    def _reset_plan_state(self) -> None:
        """Clear the scheduler's stored plan, explanations, and skip count."""
        self.planned_tasks = []
        self.planned_items = []
        self.explanations = []
        self.skipped_count = 0
        self.conflicts = []

    def _clear_scheduled_times(self, owner: Owner) -> None:
        """Remove scheduled times from all of an owner's tasks before replanning."""
        for _, task in owner.get_all_tasks():
            task.clear_scheduled_time()

    def _time_sort_key(self, task: CareTask) -> int:
        """Convert HH:MM scheduled_time to minutes for sorting; unscheduled tasks go last."""
        if not task.scheduled_time:
            return 24 * 60
        hours, minutes = task.scheduled_time.split(":")
        return int(hours) * 60 + int(minutes)

    def _task_time_range(self, task: CareTask) -> Optional[Tuple[int, int]]:
        """Convert a task's scheduled start time and duration into minute-based bounds."""
        if not task.scheduled_time:
            return None
        start = self._time_sort_key(task)
        return (start, start + task.duration_minutes)

    def _format_clock(self, minutes: int) -> str:
        """Format minutes from midnight as HH:MM."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

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


def _task_to_dict(task: CareTask) -> Dict[str, Any]:
    """Convert a CareTask to a JSON-friendly dictionary."""
    return {
        "description": task.description,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "frequency": task.frequency,
        "completed": task.completed,
        "scheduled_time": task.scheduled_time,
        "due_date": task.due_date.isoformat(),
    }


def _task_from_dict(data: Dict[str, Any]) -> CareTask:
    """Rebuild a CareTask from a dictionary produced by _task_to_dict()."""
    return CareTask(
        description=data["description"],
        duration_minutes=data["duration_minutes"],
        priority=data.get("priority", "medium"),
        frequency=data.get("frequency", "daily"),
        completed=data.get("completed", False),
        scheduled_time=data.get("scheduled_time"),
        due_date=date.fromisoformat(data["due_date"]),
    )


def _pet_to_dict(pet: Pet) -> Dict[str, Any]:
    """Convert a Pet and its tasks to a JSON-friendly dictionary."""
    return {
        "name": pet.name,
        "species": pet.species,
        "owner_name": pet.owner_name,
        "tasks": [_task_to_dict(task) for task in pet.tasks],
    }


def _pet_from_dict(data: Dict[str, Any]) -> Pet:
    """Rebuild a Pet from a dictionary produced by _pet_to_dict()."""
    pet = Pet(
        name=data["name"],
        species=data["species"],
        owner_name=data.get("owner_name"),
        tasks=[_task_from_dict(task_data) for task_data in data.get("tasks", [])],
    )
    return pet


def _owner_to_dict(owner: Owner) -> Dict[str, Any]:
    """Convert an Owner graph to a JSON-friendly dictionary."""
    return {
        "name": owner.name,
        "available_time_minutes": owner.available_time_minutes,
        "preferences": list(owner.preferences),
        "pets": [_pet_to_dict(pet) for pet in owner.pets],
    }


def _owner_from_dict(data: Dict[str, Any]) -> Owner:
    """Rebuild an Owner graph from a dictionary produced by _owner_to_dict()."""
    owner = Owner(
        name=data["name"],
        available_time_minutes=data["available_time_minutes"],
        preferences=list(data.get("preferences", [])),
        pets=[_pet_from_dict(pet_data) for pet_data in data.get("pets", [])],
    )
    for pet in owner.pets:
        pet.owner_name = owner.name
    return owner


# Alias matching common project terminology.
Task = CareTask
