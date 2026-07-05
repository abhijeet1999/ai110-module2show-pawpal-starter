# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

PawPal+ is built around three essential things a pet owner should be able to do:

1. **Set up their pet profile.** The user enters basic information about themselves and their pet—such as the owner’s name, the pet’s name, and species—so the app knows who the plan is for and can tailor care suggestions accordingly.

2. **Add and manage care tasks.** The user can create tasks like walks, feeding, medication, or grooming. Each task includes at least how long it takes and how important it is, so the system has enough detail to prioritize what matters most when time is limited.

3. **Generate and review today’s plan.** The user asks PawPal+ to build a daily schedule from their tasks and constraints (for example, how much time they have available). The app shows which tasks fit into the day, when they happen, and ideally explains why those choices were made.

**a. Initial design**

The first UML draft uses four classes:

- **Owner** — Stores the owner’s name, how much time they have available today, and optional preferences. Can own one or more pets. Responsible for supplying scheduling constraints and managing their pet list.
- **Pet** — Stores the pet’s name and species, and holds the list of care tasks for that pet. Each pet belongs to one owner. Responsible for adding, removing, and listing tasks.
- **CareTask** — Represents one care activity (walk, feeding, meds, etc.) with a title, duration, and priority. Can receive a scheduled time once the plan is built.
- **Scheduler** — Takes a pet’s tasks and the owner’s time budget, sorts and filters tasks, assigns time slots, and produces explanations for the final plan.

See `diagrams/uml_draft.mmd` for the full Mermaid class diagram.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
