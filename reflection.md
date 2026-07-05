# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

PawPal+ is built around three essential things a pet owner should be able to do:

1. **Set up their pet profile.** The user enters basic information about themselves and their pet—such as the owner’s name, the pet’s name, and species—so the app knows who the plan is for and can tailor care suggestions accordingly.

2. **Add and manage care tasks.** The user can create tasks like walks, feeding, medication, or grooming. Each task includes at least how long it takes and how important it is, so the system has enough detail to prioritize what matters most when time is limited.

3. **Generate and review today’s plan.** The user asks PawPal+ to build a daily schedule from their tasks and constraints (for example, how much time they have available). The app shows which tasks fit into the day, when they happen, and ideally explains why those choices were made.

**a. Initial design**

The first UML draft uses four classes. Each class has one clear job, and together they support the three core user actions (set up profiles, manage tasks, generate a plan).

**Owner** holds who is using the app and what limits apply today. Its attributes are `name`, `available_time_minutes`, `preferences`, and a list of `pets`. Its methods manage that data: `get_available_time()` returns the time budget for scheduling, `update_preferences()` stores owner preferences for future filtering, `add_pet()` and `get_pets()` maintain the one-to-many owner–pet relationship, and `get_pet(name)` looks up a specific pet when the owner has more than one.

**Pet** represents one animal under an owner. It stores `name`, `species`, `owner_name` (a link back to the owner), and a list of `tasks`. Its methods focus on task management: `add_task()`, `remove_task()`, and `get_tasks()`. Pets do not schedule themselves; they only collect the work that needs to be done.

**CareTask** represents a single care activity (for example, a walk or feeding). It stores `title`, `duration_minutes`, `priority`, and an optional `scheduled_time` that is filled in later by the scheduler. Its methods are small but important: `get_priority_rank()` converts priority labels into a sortable number, `assign_time()` sets when the task happens, and `clear_scheduled_time()` removes an old time before a new plan is built.

**Scheduler** is the planning engine. It is not a dataclass because it performs behavior rather than storing user profile data. It keeps `planned_tasks` and `explanations` from the last run. Its methods implement the scheduling pipeline: `generate_plan(pet, owner)` orchestrates the full flow, `sort_tasks_by_priority()` orders tasks, `fit_tasks_to_time()` chooses what fits in the available minutes, and `explain_plan()` returns reasons for the final schedule.

Relationships: one **Owner** owns many **Pets**; each **Pet** has many **CareTasks**; the **Scheduler** reads from **Pet** and **Owner** and writes scheduled times onto **CareTask** objects. The scheduler builds one plan for one pet at a time, using the owner’s shared time budget.

See `diagrams/uml_draft.mmd` for the full Mermaid class diagram.

**b. Design changes**

Yes. After reviewing the `pawpal_system.py` skeleton, a few gaps were fixed before moving on to implementation:

1. **Added `Owner.get_pet(name)`** — With multiple pets per owner, the app needs a way to select one pet by name for scheduling. The original skeleton only listed all pets, which would become awkward in the UI and scheduler.

2. **Added `owner_name` on `Pet` and clarified `add_pet()`** — The UML says each pet belongs to an owner, but the skeleton only stored pets on the owner side. Linking a pet back to its owner makes the relationship explicit and easier to validate later.

3. **Added `CareTask.clear_scheduled_time()`** — The scheduler updates tasks in place. Without clearing old times, generating a new plan could leave stale scheduled times on tasks that were dropped from the latest plan.

4. **Clarified `Scheduler.generate_plan()` behavior** — The docstring now states that a new plan should reset scheduler state and clear old scheduled times first. This avoids a logic bottleneck where repeated planning calls produce confusing or inconsistent results.

The final architecture is documented in `diagrams/uml_final.mmd`, which adds recurring-task fields, sorting/filtering/conflict methods, cross-pet planning, and `Pet.mark_task_complete()`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Available time** — the owner’s daily minute budget (`available_time_minutes`)
- **Task priority** — high, medium, low (sorted first when building a plan)
- **Completion status** — completed tasks are excluded
- **Due date / frequency** — daily, weekly, and once tasks use `due_date` and `is_due_for_planning()`
- **Scheduled time ranges** — used for sorting and conflict warnings after a plan is built

Priority and available time matter most because the scenario is a busy owner trying to fit the most important care into limited time. Preferences are stored on `Owner` but not yet used in ranking. Conflict detection runs after scheduling and warns rather than blocking the plan.

**b. Tradeoffs**

One tradeoff is in **`detect_conflicts()`**: the scheduler checks for **overlapping time ranges** (start + duration), not just tasks with the exact same start time.

A simpler approach would only flag tasks where `scheduled_time` is identical (for example, two tasks both at `09:00`). That is easier to read and slightly faster, but it would miss cases like a 30-minute walk starting at 09:00 conflicting with a 15-minute feeding starting at 09:10.

I kept the overlap check because a pet owner cannot be in two places at once even when start times differ. The tradeoff is extra logic and pairwise comparisons (fine for small daily plans), in exchange for more realistic warnings. The scheduler still **warns only** — it does not auto-reschedule or crash — so the app stays usable while surfacing the problem.

When reviewing AI suggestions to simplify this method, a more “Pythonic” version using `itertools.combinations` and `max(start_a, start_b) < min(end_a, end_b)` was shorter but harder to follow line-by-line. I kept the explicit nested loop because readability matters more here than saving a few lines.

---

## 3. AI Collaboration

**a. How you used AI**

I used the AI coding assistant across every phase of PawPal+, but in different ways depending on the goal:

| Phase | How AI helped | Example prompts |
|-------|---------------|-----------------|
| **Design (UML)** | Brainstormed the four-class model and generated Mermaid syntax | *"Create a Mermaid class diagram for Owner, Pet, CareTask, and Scheduler with these attributes and methods."* |
| **Skeleton review** | Attached `pawpal_system.py` and asked for missing relationships or bottlenecks | *"Review this skeleton — do you see any logic bottlenecks before I implement?"* |
| **Core implementation** | Agent mode filled in method bodies while I kept the four-class structure | *"Implement Owner, Pet, CareTask, and Scheduler based on the UML."* |
| **Smart algorithms** | Targeted chat on individual methods | *"How do I sort tasks by HH:MM using a lambda key?"* and *"Suggest a lightweight conflict detection strategy that returns warnings."* |
| **UI bridge** | Investigated Streamlit patterns I had not used before | *"How do I persist an Owner object across reruns with st.session_state?"* |
| **Polish & docs** | README walkthrough, terminal formatting, and UI CSS fixes | *"Suggest a clearer way to format this schedule output for the terminal."* |

**Most effective features for building the scheduler**

1. **Agent mode with file context** — Best for multi-step work (implement `sort_by_time`, wire it into `generate_plan`, update `main.py`, run the demo). The assistant could edit several files in one pass while I checked the output.
2. **Method-scoped chat** — Asking about one function at a time (`filter_tasks`, `detect_conflicts`, `mark_task_complete`) produced focused, testable code instead of large rewrites.
3. **Attach-and-review** — Uploading `pawpal_system.py` after the skeleton phase surfaced real design gaps (`get_pet(name)`, `clear_scheduled_time()`) before logic was built on a shaky foundation.
4. **Terminal verification loops** — Running `python main.py` and `python -m pytest` immediately after AI edits was the fastest way to confirm the scheduler actually worked, not just looked correct.

**b. Judgment and verification**

**One suggestion I rejected:** When implementing `detect_conflicts()`, the AI proposed a shorter version using `itertools.combinations` and interval overlap math (`max(start_a, start_b) < min(end_a, end_b)`). It was technically cleaner, but harder to read line-by-line during review and debugging. I kept an explicit nested loop with named variables because readability mattered more than saving a few lines for a small daily plan.

**Another modification:** During UI polish, the assistant suggested a dark sidebar with custom CSS. That styling made text inputs and buttons nearly invisible (white-on-white). I rejected the dark theme and switched to a light sidebar with bordered form sections instead — same layout goal, but a design choice driven by usability, not whatever CSS the AI generated first.

**How I verified AI output**

- **Run the code** — `main.py` for scheduling demos, `streamlit run app.py` for UI behavior.
- **Automated tests** — Expanded from two basic tests to eight covering sorting, recurrence, conflicts, and plan ordering.
- **Design check** — Compared changes against the UML and the four-class rule: if a suggestion added a fifth class (for example, a separate `DailyPlan` or `Database` layer), I rejected it unless the benefit clearly outweighed the extra complexity.

---

## 4. Testing and Verification

**a. What you tested**

The suite in `tests/test_pawpal.py` grew to **8 passing tests**:

| Test | What it verifies | Why it matters |
|------|------------------|----------------|
| `test_mark_complete_changes_task_status` | `mark_complete()` flips `completed` and `is_pending()` | Core task lifecycle — the UI "Complete" button depends on this |
| `test_add_task_increases_pet_task_count` | `add_task()` grows the pet's list | Confirms tasks are stored on the right object |
| `test_sort_by_time_returns_tasks_in_chronological_order` | `sort_by_time()` orders `"08:00"` before `"14:30"` | Schedule display must not show afternoon tasks before morning ones |
| `test_daily_recurrence_creates_task_for_following_day` | Completing a daily task creates a new task due +1 day | Recurring care is a central "smart" feature |
| `test_weekly_task_completion_creates_next_occurrence` | Weekly tasks recur in 7 days | Different frequency rules must not be hard-coded to daily only |
| `test_once_task_does_not_create_next_occurrence` | One-time tasks do not repeat | Prevents infinite task lists from vet visits and similar events |
| `test_conflict_detection_flags_duplicate_times` | `detect_conflicts()` returns a readable warning | Safety net when two pets' tasks overlap |
| `test_generate_plan_sorts_scheduled_items_by_time` | Full plan output is time-sorted | End-to-end check that the scheduler pipeline works together |

These tests target the behaviors that would embarrass the app if wrong: wrong sort order, broken recurrence, silent conflicts, and tasks that never complete.

**b. Confidence**

**Confidence: ★★★★★ (5 out of 5)**

Core scheduling, sorting, recurrence, and conflict detection are covered by passing tests and confirmed in both `main.py` and the Streamlit UI. Additional edge-case tests now verify empty owners, zero-minute budgets, partial time overlaps, future due dates, and UI helper integration (`task_rows`, `plan_summary`, persistence helpers).

---

## 5. Reflection

**a. What went well**

I am most satisfied with the **separation between logic and UI**. `pawpal_system.py` owns all scheduling decisions; `app.py` only reads and writes `Owner`, `Pet`, and `CareTask` objects through `st.session_state`. That made it possible to verify the scheduler in the terminal first, then connect buttons later without rewriting the core design.

The **scheduler pipeline** also came together cleanly: filter pending → sort by priority → fit to time budget → assign slots → sort by time → detect conflicts → explain results. Each step maps to one method, which made debugging and AI-assisted edits much easier.

**b. What you would improve**

On a second iteration I would:

1. **Use owner preferences in ranking** — `Owner.preferences` is stored but not yet applied when sorting tasks.
2. **Auto-reschedule or suggest fixes for conflicts** — today the app warns only; a smarter version could shift lower-priority tasks.
3. **Stronger UI tests** — added pytest coverage for `task_rows`, `plan_summary`, and save/load helpers; full Streamlit click-path tests would still be a future improvement.
4. **Tighter recurrence UX** — show "next due" more prominently when a daily task is completed.

**c. Key takeaway — lead architect with AI**

The most important lesson was that **powerful AI tools do not replace system design — they amplify it**. When I had a clear four-class model and concrete user actions (set up profile, manage tasks, generate a plan), the assistant was fast and accurate. When I asked vague questions, I got over-built or stylistically wrong suggestions (extra classes, dark CSS, clever one-liners).

**Separate chat sessions per phase** helped me stay organized: design chats did not get polluted with UI CSS, and algorithm chats stayed focused on `Scheduler` methods without re-litigating the UML. Each session had one job.

My role as lead architect was to:

- **Set constraints** — four classes, warn-don't-crash on conflicts, dataclasses for data objects.
- **Review before accepting** — read diffs, reject clever code that hurt clarity.
- **Verify with evidence** — pytest and terminal output, not trust alone.

AI was the implementation partner; I was responsible for what the system *meant* and whether it was *correct*.
