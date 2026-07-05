"""Integration tests for app.py helpers that bridge UI and backend logic."""

from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from pawpal_system import CareTask, Owner, Pet


class SessionState(dict):
    """Minimal Streamlit session_state stand-in supporting attribute access."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


def _build_streamlit_mock() -> MagicMock:
    st_mock = MagicMock()
    st_mock.session_state = SessionState()

    @contextmanager
    def fake_context(*args, **kwargs):
        yield MagicMock()

    st_mock.sidebar.__enter__ = MagicMock(return_value=st_mock.sidebar)
    st_mock.sidebar.__exit__ = MagicMock(return_value=False)
    st_mock.form = fake_context
    st_mock.container = fake_context
    st_mock.expander = fake_context
    st_mock.tabs = MagicMock(return_value=(MagicMock(), MagicMock(), MagicMock()))
    st_mock.columns = MagicMock(return_value=(MagicMock(), MagicMock()))
    st_mock.text_input = MagicMock(side_effect=lambda *args, value=None, **kwargs: value)
    st_mock.number_input = MagicMock(side_effect=lambda *args, value=None, **kwargs: value)
    st_mock.button = MagicMock(return_value=False)
    st_mock.radio = MagicMock(return_value=None)
    st_mock.selectbox = MagicMock(return_value="dog")
    st_mock.segmented_control = MagicMock(return_value="Pending")
    st_mock.markdown = MagicMock()
    st_mock.set_page_config = MagicMock()
    st_mock.info = MagicMock()
    st_mock.warning = MagicMock()
    st_mock.success = MagicMock()
    st_mock.error = MagicMock()
    st_mock.caption = MagicMock()
    st_mock.write = MagicMock()
    st_mock.dataframe = MagicMock()
    st_mock.rerun = MagicMock()
    return st_mock


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    """Import app with Streamlit mocked so module-level UI code does not run."""
    monkeypatch.chdir(tmp_path)
    st_mock = _build_streamlit_mock()

    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "streamlit", st_mock)
        for module_name in list(sys.modules):
            if module_name == "app":
                del sys.modules[module_name]
        import app as loaded_app

        importlib.reload(loaded_app)
        yield loaded_app


def test_task_rows_adds_emojis_and_status_labels(app_module):
    """task_rows() should format rows the Streamlit dataframe expects."""
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("Morning walk", 20, priority="high")

    rows = app_module.task_rows([(pet, task)])

    assert len(rows) == 1
    assert rows[0]["Pet"] == "🐕 Mochi"
    assert rows[0]["Task"] == "🚶 Morning walk"
    assert rows[0]["Priority"] == "🔴 high"
    assert rows[0]["Status"] == "⏳ Pending"


def test_task_rows_marks_completed_tasks(app_module):
    """Completed tasks should show a Done status in the UI table."""
    pet = Pet(name="Biscuit", species="cat")
    task = CareTask("Feed breakfast", 10, priority="medium")
    task.mark_complete()

    rows = app_module.task_rows([(pet, task)])

    assert rows[0]["Status"] == "✅ Done"


def test_plan_summary_reports_used_and_remaining_minutes(app_module):
    """plan_summary() should match the Schedule tab metrics."""
    owner = Owner(name="Jordan", available_time_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("Evening meds", 5, scheduled_time="18:00")

    used, remaining = app_module.plan_summary(owner, [(pet, task)])

    assert used == 5
    assert remaining == 55


def test_save_and_load_owner_via_app_helpers(app_module, tmp_path):
    """save_owner_state() and load_saved_owner() should round-trip through data.json."""
    owner = Owner(name="Jordan", available_time_minutes=45)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Morning walk", 20, priority="high"))
    owner.add_pet(pet)

    app_module.save_owner_state(owner)
    loaded = app_module.load_saved_owner()

    assert loaded is not None
    assert loaded.name == "Jordan"
    assert loaded.get_pet("Mochi") is not None
    assert len(loaded.get_pet("Mochi").get_tasks()) == 1
