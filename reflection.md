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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
