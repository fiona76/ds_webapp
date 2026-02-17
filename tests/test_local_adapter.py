from types import SimpleNamespace

from integration.local_adapter import LocalIntegrationAdapter


def _new_state():
    return SimpleNamespace(
        bc_power_sources=[],
        bc_temperatures=[],
        bc_power_source_counter=0,
        bc_temperature_counter=0,
    )


def test_add_power_source_marks_unsynced_and_version():
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)

    response = adapter.add_power_source("project_1")

    assert response.result.ok is True
    assert len(state.bc_power_sources) == 1
    assert state.bc_power_sources[0]["name"] == "Power Source 1"
    assert state.project_dirty is True
    assert state.project_unsynced is True
    assert state.project_version == 1


def test_power_source_assignment_exclusive():
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.add_power_source("project_1")

    ok = adapter.toggle_assign_power_source_object("project_1", "ps_1", "CHIP")
    conflict = adapter.toggle_assign_power_source_object("project_1", "ps_2", "CHIP")

    assert ok.ok is True
    assert conflict.ok is False
    assert conflict.error_code == "CONFLICT"
    assert "CHIP" in state.bc_power_sources[0]["assigned_objects"]
    assert "CHIP" not in state.bc_power_sources[1]["assigned_objects"]


def test_remove_selected_assignment_and_sync():
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_temperature("project_1")
    adapter.toggle_assign_temperature_surface("project_1", "temp_1", "CHIP:Face-1")
    adapter.toggle_assign_temperature_surface("project_1", "temp_1", "CHIP:Face-2")

    result = adapter.remove_selected_assignment("project_1", "temp_1", ["CHIP:Face-1"])
    assert result.ok is True
    assert state.bc_temperatures[0]["assigned_surfaces"] == ["CHIP:Face-2"]
    assert state.project_unsynced is True

    sync = adapter.sync_project_state("project_1")
    assert sync.result.ok is True
    assert sync.synced is True
    assert state.project_unsynced is False
