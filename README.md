# PawPal+

**PawPal+** is a pet care planning assistant built with Python and Streamlit. It helps a busy owner manage multiple pets, prioritize care tasks, and generate a daily schedule that respects available time, task priority, and recurring due dates.

Backend logic lives in `pawpal_system.py`. The interactive demo runs through `app.py`. Terminal verification is available via `main.py`.

## Features

- **Multi-pet profiles** — An `Owner` can save multiple `Pet` records and switch between them in the UI.
- **Task management** — Add care tasks with description, duration, priority, and frequency (`daily`, `weekly`, `once`).
- **Priority-based scheduling** — Each `CareTask` has a **High / Medium / Low** priority; the scheduler ranks tasks by priority before fitting them into the time budget, then displays the plan in chronological order.
- **Sorting by time** — `Scheduler.sort_by_time()` and `sort_items_by_time()` display plans in chronological order using an `HH:MM` sort key.
- **Filtering** — `Scheduler.filter_tasks()` narrows tasks by pet name and/or completion status.
- **Daily and weekly recurrence** — `Pet.mark_task_complete()` creates the next task instance using `timedelta` (+1 day or +7 days).
- **Due-date planning** — `CareTask.is_due_for_planning()` excludes future recurring tasks from today's plan.
- **Conflict warnings** — `Scheduler.detect_conflicts()` flags overlapping scheduled tasks and returns readable warnings instead of crashing.
- **Plan explanations** — `Scheduler.explain_plan()` describes why each task was chosen and notes skipped tasks.
- **Automated tests** — `tests/test_pawpal.py` verifies sorting, recurrence, conflicts, and core task behavior.

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

### Run tests

```bash
python -m pytest
```

## Architecture

System design is documented in:

- `diagrams/uml_final.mmd` — final class diagram matching `pawpal_system.py`
- `diagrams/uml_draft.mmd` — initial Phase 1 design

Core classes:

| Class | Responsibility |
|-------|----------------|
| `Owner` | Profile, time budget, pet list, cross-pet task access |
| `Pet` | One animal and its task list; completes tasks and triggers recurrence |
| `CareTask` | One care activity with priority, frequency, due date, and scheduled time |
| `Scheduler` | Sort, filter, plan, detect conflicts, and explain results |

## Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_items_by_time()`, `Scheduler.sort_tasks_by_priority()`, `Scheduler.sort_tasks_by_priority_then_time()` | Priority first when building a plan; chronological order for calendar display |
| Priority scheduling | `CareTask.priority`, `get_priority_rank()`, `sort_tasks_by_priority()` | High → Medium → Low ranking; shorter tasks break ties at the same priority |
| Filtering | `Scheduler.filter_tasks()` | Filter by pet name and/or completion status |
| Conflict handling | `Scheduler.detect_conflicts()` | Detects overlapping time ranges; returns warnings |
| Next available slot | `Scheduler.find_next_available_slot()` | Finds the earliest gap where a new task fits without overlap |
| Recurring tasks | `CareTask.next_due_date()`, `CareTask.create_next_occurrence()`, `Pet.mark_task_complete()`, `CareTask.is_due_for_planning()` | Daily +1 day; weekly +7 days; once does not repeat |
| Data persistence | `Owner.save_to_json()`, `Owner.load_from_json()` | Saves pets and tasks to `data.json` between app runs |

## Data Persistence

PawPal+ remembers your pets and tasks between Streamlit sessions using a local **`data.json`** file in the project root.

### How it works

1. **On startup** — `app.py` calls `Owner.load_from_json("data.json")` when the file exists; otherwise it creates a fresh owner profile.
2. **During use** — After you add pets, add tasks, complete tasks, or generate a plan, the app calls `owner.save_to_json("data.json")`.
3. **Serialization** — Custom dictionary helpers in `pawpal_system.py` convert `Owner`, `Pet`, and `CareTask` objects to JSON (including ISO-formatted `due_date` strings). No extra library is required; marshmallow would add schema validation but was not needed for this flat structure.

### Files modified for persistence

| File | Change |
|------|--------|
| `pawpal_system.py` | `_owner_to_dict()`, `_owner_from_dict()`, and related helpers; `Owner.save_to_json()` / `Owner.load_from_json()` |
| `app.py` | Load on startup; `save_owner_state()` after each interaction |
| `tests/test_pawpal.py` | Round-trip test using a temporary JSON file |
| `main.py` | Terminal demo of save/load |

### Try it

```bash
streamlit run app.py
# Add a pet and task, stop the app, then restart — your data should still be there.
```

To reset, delete `data.json` and relaunch the app.

## Priority-Based Scheduling

Every `CareTask` stores a **priority** field: `high`, `medium`, or `low` (see `VALID_PRIORITIES` in `pawpal_system.py`). The scheduler uses a two-step approach:

1. **Rank by priority** — `sort_tasks_by_priority()` orders pending tasks High → Medium → Low (shorter duration breaks ties).
2. **Fit to time budget** — `fit_tasks_to_time()` walks that queue and stops when minutes run out, so lower-priority work may be skipped.
3. **Display by time** — After slots are assigned, `sort_items_by_time()` shows the calendar view; `sort_items_by_priority_then_time()` groups by priority when comparing tasks.

Run the dedicated demo at the top of `main.py`:

```bash
python main.py
```

### CLI output: priority queue and constrained schedule

When Alex has **30 minutes** and Luna has four mixed-priority tasks, the terminal shows:

```
Step 1: Priority queue (High → Low)
------------------------------------------------------------------------
RANK   PRIORITY   MIN    TASK
------------------------------------------------------------------------
1      high       10     Give meds
2      high       10     Feed breakfast
3      medium     25     Morning walk
4      low        15     Brush coat

Step 2: Daily plan (time order — high-priority tasks scheduled first)
------------------------------------------------------------------------
Owner: Alex
Time available today: 30 minutes

TIME     PET        TASK                     DURATION   PRIORITY
------------------------------------------------------------------------
08:00    Luna       Give meds                10 min     high
08:10    Luna       Feed breakfast           10 min     high
------------------------------------------------------------------------
Summary: 2 task(s) scheduled · 20 min used · 10 min remaining

Step 3: Same plan sorted by priority, then time:
------------------------------------------------------------------------
  high     | 08:00    | 10 min | Luna: Give meds
  high     | 08:10    | 10 min | Luna: Feed breakfast

Note: 2 lower-priority task(s) skipped because only 30 minutes were available.
```

High-priority meds and feeding fit in the budget; the medium walk and low-priority brush are deferred — exactly the behavior a busy owner needs when time is limited.

## CLI Formatting

The terminal demo (`main.py`) uses a dedicated formatting module — **`cli_format.py`** — to make output easier to scan.

### Libraries

| Library | Purpose |
|---------|---------|
| **[tabulate](https://pypi.org/project/tabulate/)** | Renders structured tables with the `rounded_outline` style for schedules, task lists, and priority queues |
| **ANSI escape codes** | Color-codes priority (`RED`/`YELLOW`/`GREEN`) and status labels in the terminal |

Install with: `pip install tabulate` (included in `requirements.txt`).

### Formatting functions

| Function | What it formats |
|----------|-----------------|
| `format_schedule_table()` | Daily plan with time, pet, task, duration, priority columns |
| `format_task_table()` | Filtered task lists with priority, frequency, status, and due date |
| `format_priority_queue_table()` | Pre-scheduling priority ranking |
| `format_warnings_block()` | Conflict alerts with red ⚠️ prefix |
| `format_explanations_block()` | Numbered “Why this plan” section |
| `format_priority_label()` | 🔴 High / 🟡 Medium / 🟢 Low with color |
| `format_status_label()` | ✅ Done (green) or ⏳ Pending (yellow) |
| `task_type_emoji()` | Keyword-based task icons (🚶 walk, 💊 meds, 🍽️ feed, 🛁 bath, etc.) |

### Streamlit UI

`app.py` imports `task_type_emoji`, `PRIORITY_EMOJI`, and `SPECIES_EMOJI` from `cli_format.py` so the web UI and CLI share the same visual vocabulary.

Run the formatted CLI demo:

```bash
python main.py
```

## Demo Walkthrough

### App screenshot

![PawPal+ Streamlit app showing sidebar pet selection, task filters, and All pets overview](docs/images/app-demo.png)

*Screenshot: owner profile and pet selection in the sidebar; metrics, task tabs, and filtered task table in the main view.*

### Main UI features

The Streamlit app (`app.py`) connects directly to the backend classes stored in `st.session_state`:

1. **Sidebar — Owner Profile** — Set your name and available minutes for today.
2. **Sidebar — Your pets** — Select an active pet with radio buttons; add new pets in the bordered form below.
3. **Tasks tab** — Add tasks for the selected pet; filter pending/completed tasks; mark tasks complete to trigger recurrence.
4. **Schedule tab** — View the generated daily plan, skipped-task warnings, conflict alerts, and explanations.
5. **All pets tab** — Filter tasks across every pet by name and status; view a pet summary table.
6. **Generate today's plan** — Primary sidebar button builds a cross-pet schedule using the smart scheduler.

### Example workflow

1. Open the app and enter owner details (for example, **Kevin**, **30 minutes** available).
2. Add pets such as **Leo** and **Hero** (dog) using **Save pet** in the sidebar.
3. Select **Hero** in the sidebar and open the **Tasks** tab to add care activities.
4. Switch to **All pets** to review tasks across both pets with filters.
5. Mark a daily task complete and confirm a new recurring instance appears with a future due date.
6. Click **Generate today's plan** in the sidebar.
7. Open the **Schedule** tab to review the time-sorted plan, skipped-task warnings, and any conflict alerts.

### Scheduler behaviors shown in the UI

- **Sorting** — The schedule table uses `sort_items_by_time()` so tasks appear earliest to latest.
- **Priority fit** — Higher-priority pending tasks are scheduled first within the available minute budget.
- **Filtering** — Task lists and the overview section use `filter_tasks()` so owners can focus on one pet or pending work.
- **Recurrence** — Completing a daily task creates the next occurrence due tomorrow.
- **Conflict warnings** — If two tasks overlap, the UI shows an expanded warning panel with plain-language guidance.
- **Next available slot** — When conflicts exist, the Schedule tab suggests the earliest open time block for rescheduling.

### Sample CLI output

Running `python main.py` uses **tabulate** tables, emoji task icons, and color-coded status labels. Example schedule excerpt:

```
╭────────┬────────────┬──────────────────────────┬──────────┬────────────╮
│ Time   │ Pet        │ Task                     │ Duration │ Priority   │
├────────┼────────────┼──────────────────────────┼──────────┼────────────┤
│ 08:00  │ 🐕 Mochi   │ 💊 Evening meds          │ 5 min    │ 🔴 high    │
│ 08:05  │ 🐕 Mochi   │ 🚶 Morning walk          │ 30 min   │ 🔴 high    │
│ 08:35  │ 🐈 Biscuit │ 🧹 Clean litter box      │ 15 min   │ 🟡 medium  │
╰────────┴────────────┴──────────────────────────┴──────────┴────────────╯

Summary: 4 task(s) · 70 min used · 20 min remaining
```

Conflict warnings appear in red with a ⚠️ prefix; pending tasks show ⏳ Pending (yellow) and completed tasks show ✅ Done (green).

## Testing PawPal+

Run the automated test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite in `tests/test_pawpal.py` verifies:

- **Task lifecycle** — completing a task updates its status; adding a task increases a pet's task count
- **Sorting** — `Scheduler.sort_by_time()` returns tasks in chronological order; `sort_tasks_by_priority_then_time()` ranks by priority then time
- **Priority scheduling** — high-priority tasks are scheduled first when the time budget is tight; lower-priority tasks may be skipped
- **Recurrence** — completing a daily task creates a new task due the next day; weekly tasks recur in 7 days; one-time tasks do not repeat
- **Conflict detection** — `Scheduler.detect_conflicts()` flags duplicate/overlapping scheduled times with warning messages
- **Next available slot** — `Scheduler.find_next_available_slot()` finds the earliest non-overlapping gap
- **Persistence** — `Owner.save_to_json()` / `Owner.load_from_json()` round-trip owner data through JSON

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/abhijeetcherungottil/Desktop/ai110-module2show-pawpal-starter
collected 13 items

tests/test_pawpal.py .............                                         [100%]

============================== 13 passed in 0.05s ===============================
```

### Confidence level

**★★★★☆ (4/5)** — Core scheduling, sorting, recurrence, and conflict detection are covered by passing tests and the CLI demo. Confidence would reach 5/5 with additional edge-case tests (empty pets, zero time budget, partial time overlaps, and UI integration tests).
