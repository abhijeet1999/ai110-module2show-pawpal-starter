# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Implement two stretch features in one agent session:

1. **Challenge 1 — Advanced algorithm:** Add `Scheduler.find_next_available_slot()` to scan a day's schedule and return the earliest HH:MM start time where a task of a given duration fits without overlapping existing scheduled tasks. Surface the result in the Schedule tab when conflicts are detected.
2. **Challenge 2 — Data persistence:** Add `Owner.save_to_json()` and `Owner.load_from_json()` with custom dictionary conversion helpers so pets and tasks survive between Streamlit runs via `data.json`.

**What did the agent do?**

| File | Changes |
|------|---------|
| `pawpal_system.py` | Added `find_next_available_slot()`; `_task_to_dict` / `_task_from_dict` and related helpers; `Owner.save_to_json()` and `Owner.load_from_json()` |
| `app.py` | Load owner from `data.json` on startup; `save_owner_state()` after mutations and at end of each rerun; conflict UI shows next available slot |
| `tests/test_pawpal.py` | Added 3 tests for slot finding and JSON round-trip |
| `main.py` | Terminal demos for next-slot search and save/load |
| `README.md` | Documented persistence workflow, modified files, and the new algorithm in Smarter Scheduling |
| `ai_interactions.md` | This agent workflow section |

The agent also ran `python -m pytest` to verify all tests pass.

**What did you have to verify or fix manually?**

- **Serialization approach:** The agent chose custom dict helpers instead of marshmallow to avoid a new dependency. I verified that `due_date` round-trips correctly as ISO strings and that `scheduled_time` handles `null` in JSON.
- **Save timing:** Initial draft only saved on button clicks; I confirmed saving at the end of each Streamlit rerun so owner name and time-budget edits persist even without adding a task.
- **Slot algorithm edge case:** Manually checked that a 30-minute task at 08:00 leaves 08:30 as the next 20-minute slot, not 09:00.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

**Task compared:** Implement logic to **reschedule weekly tasks** when a pet owner marks a recurring care task complete — specifically, compute the next due date and create a fresh task instance without duplicating or losing history.

**Shared prompt (sent to both models with `pawpal_system.py` attached):**

> *"In PawPal+, when a user completes a weekly CareTask, the system should create the next occurrence due exactly 7 days later. Implement `next_due_date()`, `create_next_occurrence()`, and wire it into `Pet.mark_task_complete()`. Use Python's datetime module. Show me the methods and explain edge cases for daily vs weekly vs once tasks."*

| | Option A — Claude (Cursor chat) | Option B — GitHub Copilot Chat |
|-|--------------------------------|-------------------------------|
| **Model / tool used** | Claude Sonnet in Cursor | GitHub Copilot Chat in VS Code |
| **Prompt** | Same shared prompt above | Same shared prompt above |
| **Response summary** | Added three focused methods on `CareTask` using `timedelta(days=7)` for weekly and `timedelta(days=1)` for daily; `create_next_occurrence()` returns a new incomplete copy; `Pet.mark_task_complete()` calls it after `mark_complete()`; `once` returns `None`. Included a pytest example for +7 days. | Proposed a new `WeeklyScheduler` class, used `calendar` and weekday math (`weekday()`, `% 7` adjustments), stored `last_completed_at` on every task, and suggested deleting the old task instead of marking it complete. |
| **What was useful** | Clear separation of concerns — date math stays on `CareTask`, list mutation stays on `Pet`. Code matched existing dataclass patterns and was easy to test with fixed `today=` parameters. | Reminded me to think about weekday drift (completing on Sunday vs due on Monday) and to document behavior when `frequency` is unknown. |
| **Problems noticed** | Did not initially pass `today=` into recurrence helpers, which made unit tests depend on the real clock — I added an optional `today` parameter manually. | Over-engineered: extra class not in UML, calendar math harder to read than `+ timedelta(days=7)`, and deleting completed tasks would break task history and filtering in the UI. |
| **Decision** | **Used Option A** as the foundation | **Rejected** — kept only the edge-case reminder about documenting frequency behavior |

**Which approach did you use in your final implementation and why?**

I implemented **Option A (Claude)** because it fit the existing four-class design: `CareTask.next_due_date()` handles the date math, `create_next_occurrence()` clones the task, and `Pet.mark_task_complete()` orchestrates completion plus recurrence. The Copilot suggestion would have introduced a fifth class and destructive deletes that conflict with PawPal+'s "show completed tasks" UI.

From Copilot I kept one idea: document that **`once`** tasks must not create a follow-up (both models agreed on that). I added explicit tests — `test_weekly_task_completion_creates_next_occurrence()` and `test_once_task_does_not_create_next_occurrence()` — and a formatted weekly rescheduling demo in `main.py` to verify the behavior visually.

**Manual correction after Option A:** Added optional `today: Optional[date] = None` parameters so pytest can pin dates instead of relying on `date.today()`.
