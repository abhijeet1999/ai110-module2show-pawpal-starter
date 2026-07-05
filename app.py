import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")

# Step 2: Manage application memory with st.session_state.
# Streamlit reruns the script on every interaction, so we store backend
# objects in session_state to keep owner, pets, and tasks across clicks.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=90)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

if "active_pet_name" not in st.session_state:
    st.session_state.active_pet_name = "Mochi"

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()
st.subheader("Owner & Pet Profile")

owner.name = st.text_input("Owner name", value=owner.name)
owner.available_time_minutes = st.number_input(
    "Available time today (minutes)",
    min_value=1,
    max_value=480,
    value=owner.available_time_minutes,
)

col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value=st.session_state.active_pet_name)
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    pet = Pet(name=pet_name, species=species)
    owner.add_pet(pet)
    st.session_state.active_pet_name = pet_name
    st.success(f"Added {pet_name} ({species}).")

active_pet = owner.get_pet(st.session_state.active_pet_name)
if active_pet is None and owner.get_pets():
    st.session_state.active_pet_name = owner.get_pets()[0].name
    active_pet = owner.get_pet(st.session_state.active_pet_name)

if owner.get_pets():
    pet_names = [pet.name for pet in owner.get_pets()]
    st.session_state.active_pet_name = st.selectbox(
        "Select pet for tasks",
        pet_names,
        index=pet_names.index(st.session_state.active_pet_name),
    )
    active_pet = owner.get_pet(st.session_state.active_pet_name)

st.divider()
st.subheader("Tasks")
st.caption("Tasks are stored on the selected pet in your Owner object.")

if active_pet is None:
    st.info("Add a pet above before creating tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_description = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        task = CareTask(
            description=task_description,
            duration_minutes=int(duration),
            priority=priority,
        )
        active_pet.add_task(task)
        st.success(f"Added '{task.description}' for {active_pet.name}.")

    tasks = active_pet.get_tasks()
    if tasks:
        st.write(f"Current tasks for {active_pet.name}:")
        st.table(
            [
                {
                    "description": task.description,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "completed": task.completed,
                    "scheduled_time": task.scheduled_time or "—",
                }
                for task in tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()
st.subheader("Build Schedule")
st.caption("Calls your Scheduler backend using the Owner stored in session_state.")

if st.button("Generate schedule"):
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

            st.markdown("**Why this plan:**")
            for line in scheduler.explain_plan():
                st.write(f"- {line}")
