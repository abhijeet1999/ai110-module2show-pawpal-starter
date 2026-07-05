import streamlit as st

from typing import Optional

from pawpal_system import CareTask, Owner, Pet, Scheduler

SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "other": "🐾"}
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 1100px;
            }
            [data-testid="stSidebar"] {
                background: #f4f7f8;
                border-right: 1px solid #d7e0e3;
            }
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
                color: #163843 !important;
            }
            .hero {
                background: linear-gradient(135deg, #e8f5f0 0%, #fdf6ec 100%);
                border: 1px solid #d7ebe3;
                border-radius: 16px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 1.9rem;
                color: #163843;
            }
            .hero p {
                margin: 0.35rem 0 0 0;
                color: #48656a;
            }
            .step-card {
                background: #ffffff;
                border: 1px solid #e7ecef;
                border-radius: 14px;
                padding: 1rem 1.1rem;
                box-shadow: 0 2px 10px rgba(22, 56, 67, 0.05);
                margin-bottom: 1rem;
            }
            .step-title {
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                color: #5b7a80;
                margin-bottom: 0.35rem;
            }
            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #e7ecef;
                border-radius: 12px;
                padding: 0.75rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def task_rows(items: list[tuple[Pet, CareTask]]) -> list[dict]:
    return [
        {
            "Time": task.scheduled_time or "—",
            "Pet": f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}",
            "Task": task.description,
            "Min": task.duration_minutes,
            "Priority": f"{PRIORITY_EMOJI.get(task.priority, '⚪')} {task.priority}",
            "Frequency": task.frequency,
            "Status": "✅ Done" if task.completed else "⏳ Pending",
            "Due": str(task.due_date),
        }
        for pet, task in items
    ]


def plan_summary(owner: Owner, plan: list[tuple[Pet, CareTask]]) -> tuple[int, int]:
    used = sum(task.duration_minutes for _, task in plan)
    return used, owner.get_available_time() - used


def render_empty_state() -> None:
    st.info("👋 Welcome! Use the sidebar to add your first pet, then come back here to add tasks.")


def get_active_pet(owner: Owner) -> Optional[Pet]:
    pets = owner.get_pets()
    if not pets:
        return None
    names = [pet.name for pet in pets]
    if st.session_state.active_pet_name not in names:
        st.session_state.active_pet_name = names[0]
    return owner.get_pet(st.session_state.active_pet_name)


st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=90)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()
if "active_pet_name" not in st.session_state:
    st.session_state.active_pet_name = None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# --- Sidebar: settings, pets, primary action ---
with st.sidebar:
    st.markdown("## 🐾 PawPal+")
    st.markdown("Your daily pet care planner")

    owner.name = st.text_input("Your name", value=owner.name)
    owner.available_time_minutes = st.number_input(
        "Minutes available today",
        min_value=1,
        max_value=480,
        value=owner.available_time_minutes,
        step=15,
    )

    st.markdown("---")
    st.markdown("### Your pets")

    pets = owner.get_pets()
    if pets:
        pet_names = [pet.name for pet in pets]
        st.session_state.active_pet_name = st.radio(
            "Select a pet to manage",
            pet_names,
            index=pet_names.index(st.session_state.active_pet_name)
            if st.session_state.active_pet_name in pet_names
            else 0,
            label_visibility="collapsed",
        )
    else:
        st.caption("No pets yet — add one below.")

    st.markdown("### ➕ Add a new pet")
    with st.container(border=True):
        new_pet_name = st.text_input("Pet name", key="new_pet_name", placeholder="Mochi")
        new_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")
        if st.button("Save pet", key="add_pet_button", type="primary", use_container_width=True):
            cleaned_name = new_pet_name.strip()
            if not cleaned_name:
                st.error("Enter a pet name.")
            elif owner.get_pet(cleaned_name):
                st.warning(f"{cleaned_name} already exists.")
                st.session_state.active_pet_name = cleaned_name
            else:
                owner.add_pet(Pet(name=cleaned_name, species=new_species))
                st.session_state.active_pet_name = cleaned_name
                st.success(f"Added {cleaned_name}!")
                st.rerun()

    st.markdown("---")
    if st.button("✨ Generate today's plan", type="primary", use_container_width=True):
        if not owner.get_pets():
            st.warning("Add a pet first.")
        elif not owner.get_all_pending_tasks():
            st.warning("Add at least one pending task.")
        else:
            plan = scheduler.generate_plan_for_owner(owner)
            st.session_state.last_plan = plan
            if not plan:
                st.warning("No tasks fit in your time budget.")
            else:
                st.rerun()

# --- Main header ---
st.markdown(
    """
    <div class="hero">
        <h1>Plan care with confidence</h1>
        <p>Add pets, create tasks, and build a smart daily schedule in a few clicks.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

active_pet = get_active_pet(owner)

if active_pet is None:
    render_empty_state()
else:
    pending_count = len(active_pet.get_pending_tasks())
    total_count = len(active_pet.get_tasks())

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Active pet", active_pet.name)
    top2.metric("Species", f"{SPECIES_EMOJI.get(active_pet.species, '🐾')} {active_pet.species}")
    top3.metric("Pending tasks", pending_count)
    top4.metric("Time budget", f"{owner.get_available_time()} min")

    tab_tasks, tab_schedule, tab_all = st.tabs(["📝 Tasks", "📅 Schedule", "📋 All pets"])

    with tab_tasks:
        st.markdown('<div class="step-card"><div class="step-title">Step 1</div><strong>Add a care task</strong></div>', unsafe_allow_html=True)

        with st.form("add_task_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                task_description = st.text_input("What needs to be done?", placeholder="Morning walk")
            with c2:
                duration = st.number_input("Minutes", min_value=1, max_value=240, value=20)

            c3, c4, c5 = st.columns(3)
            with c3:
                priority = st.selectbox("Priority", ["high", "medium", "low"], index=0)
            with c4:
                frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
            with c5:
                st.write("")
                st.write("")
                submitted = st.form_submit_button("Add task", type="primary", use_container_width=True)

            if submitted:
                if not task_description.strip():
                    st.error("Enter a task description.")
                else:
                    active_pet.add_task(
                        CareTask(
                            description=task_description.strip(),
                            duration_minutes=int(duration),
                            priority=priority,
                            frequency=frequency,
                        )
                    )
                    st.success(f"Added task for {active_pet.name}.")
                    st.rerun()

        st.markdown('<div class="step-card"><div class="step-title">Step 2</div><strong>Manage tasks</strong></div>', unsafe_allow_html=True)

        task_filter = st.segmented_control(
            "Show",
            ["Pending", "Completed", "All"],
            default="Pending",
            key="active_pet_task_filter",
        )

        pet_items = [(active_pet, task) for task in active_pet.get_tasks()]
        if task_filter == "Pending":
            pet_items = scheduler.filter_tasks(pet_items, completed=False)
        elif task_filter == "Completed":
            pet_items = scheduler.filter_tasks(pet_items, completed=True)

        if pet_items:
            if task_filter == "Pending":
                pending_only = [task for _, task in pet_items]
                display_items = [
                    (active_pet, task)
                    for task in scheduler.sort_tasks_by_priority(pending_only)
                ]
            else:
                display_items = pet_items

            st.dataframe(task_rows(display_items), use_container_width=True, hide_index=True)

            pending_items = scheduler.filter_tasks(
                [(active_pet, task) for task in active_pet.get_tasks()],
                completed=False,
            )
            if pending_items:
                st.markdown("**Mark a task complete**")
                complete_labels = [
                    f"{task.description} · {task.duration_minutes} min · {task.priority}"
                    for _, task in pending_items
                ]
                c1, c2 = st.columns([3, 1])
                with c1:
                    complete_choice = st.selectbox(
                        "Choose task",
                        complete_labels,
                        label_visibility="collapsed",
                    )
                with c2:
                    if st.button("Complete", use_container_width=True):
                        idx = complete_labels.index(complete_choice)
                        chosen_task = pending_items[idx][1]
                        next_task = active_pet.mark_task_complete(chosen_task)
                        st.success(f"Completed {chosen_task.description}.")
                        if next_task:
                            st.info(f"Next due: {next_task.due_date}")
                        st.rerun()
        else:
            st.info(f"No {task_filter.lower()} tasks for {active_pet.name} yet.")

    with tab_schedule:
        plan = st.session_state.last_plan
        if not plan:
            st.info("Click **Generate today's plan** in the sidebar when your tasks are ready.")
        else:
            sorted_plan = scheduler.sort_items_by_time(plan)
            used_minutes, remaining_minutes = plan_summary(owner, sorted_plan)

            m1, m2, m3 = st.columns(3)
            m1.metric("Scheduled tasks", len(sorted_plan))
            m2.metric("Time used", f"{used_minutes} min")
            m3.metric("Time left", f"{remaining_minutes} min")

            if scheduler.skipped_count:
                st.warning(
                    f"{scheduler.skipped_count} task(s) could not fit in your "
                    f"{owner.get_available_time()}-minute budget."
                )

            st.dataframe(task_rows(sorted_plan), use_container_width=True, hide_index=True)

            if scheduler.conflicts:
                st.error("Schedule conflict detected")
                for warning in scheduler.conflicts:
                    st.warning(warning)
                st.markdown(
                    "Try removing a lower-priority task, increasing your available time in the sidebar, "
                    "then regenerate the plan."
                )
            else:
                st.success("No time conflicts — you're good to go.")

            with st.expander("Why this plan?"):
                for line in scheduler.explain_plan():
                    if not line.startswith("Warning:"):
                        st.write(f"- {line}")

    with tab_all:
        if not owner.get_pets():
            st.info("Add pets to see the full overview.")
        else:
            f1, f2 = st.columns(2)
            with f1:
                overview_pet = st.selectbox(
                    "Pet",
                    ["All pets"] + [pet.name for pet in owner.get_pets()],
                )
            with f2:
                overview_status = st.selectbox(
                    "Status",
                    ["All", "Pending", "Completed"],
                )

            all_items = owner.get_all_tasks()
            if overview_pet != "All pets":
                all_items = scheduler.filter_tasks(all_items, pet_name=overview_pet)
            if overview_status == "Pending":
                all_items = scheduler.filter_tasks(all_items, completed=False)
            elif overview_status == "Completed":
                all_items = scheduler.filter_tasks(all_items, completed=True)

            if all_items:
                st.dataframe(task_rows(all_items), use_container_width=True, hide_index=True)
            else:
                st.warning("No tasks match these filters.")

            st.markdown("**Pet summary**")
            st.dataframe(
                [
                    {
                        "Pet": f"{SPECIES_EMOJI.get(pet.species, '🐾')} {pet.name}",
                        "Species": pet.species,
                        "Total tasks": len(pet.get_tasks()),
                        "Pending": len(pet.get_pending_tasks()),
                    }
                    for pet in owner.get_pets()
                ],
                use_container_width=True,
                hide_index=True,
            )
