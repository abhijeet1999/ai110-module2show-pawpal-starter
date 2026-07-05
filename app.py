import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=90)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

if "active_pet_name" not in st.session_state:
    st.session_state.active_pet_name = None

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()
st.subheader("Owner Profile")

owner.name = st.text_input("Owner name", value=owner.name)
owner.available_time_minutes = st.number_input(
    "Available time today (minutes)",
    min_value=1,
    max_value=480,
    value=owner.available_time_minutes,
)

st.divider()
st.subheader("Saved Pets")

if owner.get_pets():
    pet_names = [pet.name for pet in owner.get_pets()]

    if st.session_state.active_pet_name not in pet_names:
        st.session_state.active_pet_name = pet_names[0]

    st.markdown("Select a saved pet to view or add tasks:")
    selected_pet_name = st.selectbox(
        "Active pet",
        pet_names,
        index=pet_names.index(st.session_state.active_pet_name),
        key="saved_pet_selector",
    )
    st.session_state.active_pet_name = selected_pet_name
    active_pet = owner.get_pet(selected_pet_name)

    st.markdown("**Your pets**")
    st.table(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "tasks": len(pet.get_tasks()),
                "selected": pet.name == selected_pet_name,
            }
            for pet in owner.get_pets()
        ]
    )
else:
    active_pet = None
    st.info("No pets saved yet. Add your first pet below.")

st.divider()
st.subheader("Add a New Pet")

new_pet_name = st.text_input("New pet name", key="new_pet_name", placeholder="e.g. Mochi")
new_species = st.selectbox(
    "Species",
    ["dog", "cat", "other"],
    key="new_pet_species",
)

if st.button("Add pet", key="add_pet_button"):
    cleaned_name = new_pet_name.strip()
    if not cleaned_name:
        st.error("Enter a pet name before adding.")
    elif owner.get_pet(cleaned_name):
        st.warning(
            f"**{cleaned_name}** is already saved. Select them from **Saved Pets** above to add tasks."
        )
        st.session_state.active_pet_name = cleaned_name
    else:
        pet = Pet(name=cleaned_name, species=new_species)
        owner.add_pet(pet)
        st.session_state.active_pet_name = cleaned_name
        st.success(f"Added **{cleaned_name}** ({new_species}). You can now add tasks for them.")
        st.rerun()

st.divider()
st.subheader("Tasks")

if active_pet is None:
    st.info("Add a pet first, then select them above to start adding tasks.")
else:
    st.caption(f"Adding tasks for **{active_pet.name}** ({active_pet.species})")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_description = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task", key="add_task_button"):
        task = CareTask(
            description=task_description,
            duration_minutes=int(duration),
            priority=priority,
        )
        active_pet.add_task(task)
        st.success(f"Added '{task.description}' for **{active_pet.name}**.")
        st.rerun()

    tasks = active_pet.get_tasks()
    if tasks:
        st.write(f"Tasks for **{active_pet.name}**:")
        st.table(
            [
                {
                    "description": task.description,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "completed": task.completed,
                    "due_date": str(task.due_date),
                    "scheduled_time": task.scheduled_time or "—",
                }
                for task in tasks
            ]
        )
    else:
        st.info(f"No tasks yet for {active_pet.name}. Add one above.")

st.divider()
st.subheader("Build Schedule")
st.caption("Builds a plan for all pending tasks across every saved pet.")

if st.button("Generate schedule", key="generate_schedule_button"):
    if not owner.get_pets():
        st.warning("Add at least one pet before generating a schedule.")
    elif not owner.get_all_pending_tasks():
        st.warning("Add at least one pending task before generating a schedule.")
    else:
        plan = scheduler.generate_plan_for_owner(owner)

        if not plan:
            st.warning("No tasks could be scheduled with the current time budget.")
        else:
            st.success("Schedule generated.")
            st.table(
                [
                    {
                        "time": task.scheduled_time,
                        "pet": pet.name,
                        "task": task.description,
                        "duration_minutes": task.duration_minutes,
                        "priority": task.priority,
                    }
                    for pet, task in plan
                ]
            )

            if scheduler.conflicts:
                st.markdown("**Schedule warnings:**")
                for warning in scheduler.conflicts:
                    st.warning(warning)

            st.markdown("**Why this plan:**")
            for line in scheduler.explain_plan():
                if line.startswith("Warning:"):
                    continue
                st.write(f"- {line}")
