# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Run the demo script to verify scheduling logic in the terminal:

```bash
python main.py
```

Output from `main.py` (Owner: Jordan, 2 pets, 4 tasks, 90 minutes available):

```
PawPal+ | Today's Schedule
------------------------------------------------------------------------
Owner: Jordan
Time available today: 90 minutes

TIME     PET        TASK                     DURATION   PRIORITY
------------------------------------------------------------------------
08:00    Mochi      Feed breakfast           10 min     high    
08:10    Mochi      Morning walk             30 min     high    
08:40    Biscuit    Clean litter box         15 min     medium  
08:55    Biscuit    Play session             20 min     low     
------------------------------------------------------------------------
Summary: 4 task(s) scheduled · 75 min used · 15 min remaining

Why this plan:
------------------------------------------------------------------------
1. 08:00 — Feed breakfast for Mochi (10 min, high priority, daily): chosen because it is pending and ranked highly within today's 4-task plan.
2. 08:10 — Morning walk for Mochi (30 min, high priority, daily): chosen because it is pending and ranked highly within today's 4-task plan.
3. 08:40 — Clean litter box for Biscuit (15 min, medium priority, daily): chosen because it is pending and ranked highly within today's 4-task plan.
4. 08:55 — Play session for Biscuit (20 min, low priority, weekly): chosen because it is pending and ranked highly within today's 4-task plan.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

PawPal+ includes lightweight algorithms for sorting, filtering, conflict detection, and recurring tasks. Run `python main.py` to see them in the CLI demo.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_items_by_time()`, `Scheduler.sort_tasks_by_priority()` | Sort by scheduled time (HH:MM via lambda key) for display; sort by priority when building a plan |
| Filtering | `Scheduler.filter_tasks()` | Filter `(Pet, CareTask)` pairs by pet name and/or completion status (`completed=True/False`) |
| Conflict handling | `Scheduler.detect_conflicts()` | Compares overlapping start + duration ranges; returns warning messages instead of crashing |
| Recurring tasks | `CareTask.next_due_date()`, `CareTask.create_next_occurrence()`, `Pet.mark_task_complete()`, `CareTask.is_due_for_planning()` | Daily tasks due tomorrow (+1 day); weekly tasks due in 7 days; one-time tasks do not repeat |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
