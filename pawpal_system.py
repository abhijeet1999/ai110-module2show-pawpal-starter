"""PawPal+ backend logic layer — class skeletons from UML draft."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    scheduled_time: Optional[str] = None

    def get_priority_rank(self) -> int:
        """Return a numeric rank for sorting tasks by priority."""
        pass

    def assign_time(self, time_slot: str) -> None:
        """Set the scheduled time for this task."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet's list."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a care task by title."""
        pass

    def get_tasks(self) -> List[CareTask]:
        """Return all care tasks for this pet."""
        pass


@dataclass
class Owner:
    name: str
    available_time_minutes: int
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def get_available_time(self) -> int:
        """Return how many minutes the owner has available today."""
        pass

    def update_preferences(self, preferences: List[str]) -> None:
        """Replace the owner's preferences."""
        pass

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        pass

    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner."""
        pass


class Scheduler:
    def __init__(self) -> None:
        self.planned_tasks: List[CareTask] = []
        self.explanations: List[str] = []

    def generate_plan(self, pet: Pet, owner: Owner) -> List[CareTask]:
        """Build a daily plan from a pet's tasks and the owner's constraints."""
        pass

    def sort_tasks_by_priority(self, tasks: List[CareTask]) -> List[CareTask]:
        """Sort tasks so higher-priority items come first."""
        pass

    def fit_tasks_to_time(self, tasks: List[CareTask], minutes: int) -> List[CareTask]:
        """Select tasks that fit within the available time."""
        pass

    def explain_plan(self) -> List[str]:
        """Return human-readable reasons for the planned schedule."""
        pass
