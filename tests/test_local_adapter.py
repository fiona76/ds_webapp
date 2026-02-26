from types import SimpleNamespace

from integration.local_adapter import LocalIntegrationAdapter


def _new_state():
    return SimpleNamespace(
        bc_power_sources=[],
        bc_temperatures=[],
        bc_stresses=[],
        bc_power_source_counter=0,
        bc_temperature_counter=0,
        bc_stress_counter=0,
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


def test_power_source_assignment_steal():
    """Assigning an object already owned by another PS steals it silently."""
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.add_power_source("project_1")

    ok1 = adapter.toggle_assign_power_source_object("project_1", "ps_1", "CHIP")
    ok2 = adapter.toggle_assign_power_source_object("project_1", "ps_2", "CHIP")

    assert ok1.ok is True
    assert ok2.ok is True
    assert ok2.message == "Assigned"
    # PS2 now owns CHIP
    assert "CHIP" in state.bc_power_sources[1]["assigned_objects"]
    # PS1 no longer owns CHIP — it appears in overridden_objects
    assert "CHIP" not in state.bc_power_sources[0]["assigned_objects"]
    assert "CHIP" in state.bc_power_sources[0]["overridden_objects"]


def test_reclaim_bc_assignment():
    """Reclaiming an overridden object restores it to the original PS."""
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.add_power_source("project_1")
    adapter.toggle_assign_power_source_object("project_1", "ps_1", "CHIP")
    adapter.toggle_assign_power_source_object("project_1", "ps_2", "CHIP")  # steals CHIP

    result = adapter.reclaim_bc_assignment("project_1", "ps_1", "CHIP")

    assert result.ok is True
    assert result.message == "Reclaimed"
    # PS1 owns CHIP again
    assert "CHIP" in state.bc_power_sources[0]["assigned_objects"]
    assert "CHIP" not in state.bc_power_sources[0]["overridden_objects"]
    # PS2 no longer owns CHIP
    assert "CHIP" not in state.bc_power_sources[1]["assigned_objects"]


def test_set_bc_assignment_mode_all():
    """set_bc_assignment_mode 'all' bulk-assigns all_values and steals from other BCs."""
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.add_power_source("project_1")
    # PS2 owns CHIP initially
    adapter.toggle_assign_power_source_object("project_1", "ps_2", "CHIP")

    result = adapter.set_bc_assignment_mode("project_1", "ps_1", "all", ["CHIP", "PCB"])

    assert result.ok is True
    # PS1 now owns CHIP and PCB
    assert state.bc_power_sources[0]["assigned_objects"] == ["CHIP", "PCB"]
    assert state.bc_power_sources[0]["selection_mode"] == "all"
    # CHIP was stolen from PS2 → appears in overridden_objects
    assert "CHIP" not in state.bc_power_sources[1]["assigned_objects"]
    assert "CHIP" in state.bc_power_sources[1]["overridden_objects"]


def test_unassign_reverts_mode_to_manual():
    """Removing an item from an 'all' PS reverts selection_mode to 'manual'."""
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.set_bc_assignment_mode("project_1", "ps_1", "all", ["CHIP", "PCB"])
    assert state.bc_power_sources[0]["selection_mode"] == "all"

    result = adapter.toggle_assign_power_source_object("project_1", "ps_1", "CHIP")

    assert result.ok is True
    assert result.message == "Unassigned"
    assert state.bc_power_sources[0]["selection_mode"] == "manual"
    assert "PCB" in state.bc_power_sources[0]["assigned_objects"]
    assert "CHIP" not in state.bc_power_sources[0]["assigned_objects"]


def test_remove_selected_reverts_mode_to_manual():
    """Using remove_selected_assignment on an 'all' PS reverts selection_mode."""
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    adapter.add_power_source("project_1")
    adapter.set_bc_assignment_mode("project_1", "ps_1", "all", ["CHIP", "PCB"])

    result = adapter.remove_selected_assignment("project_1", "ps_1", ["PCB"])

    assert result.ok is True
    assert state.bc_power_sources[0]["selection_mode"] == "manual"
    assert "CHIP" in state.bc_power_sources[0]["assigned_objects"]


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


def test_list_default_materials_returns_not_available():
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)

    response = adapter.list_default_materials()

    assert response.result.ok is False
    assert response.result.error_code == "NOT_AVAILABLE"
    assert response.names == []


def test_get_default_material_returns_not_available():
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)

    response = adapter.get_default_material("SiO2")

    assert response.result.ok is False
    assert response.result.error_code == "NOT_AVAILABLE"
