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


def test_material_import_upsert_and_warning(tmp_path):
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    material_file = tmp_path / "materials.txt"
    material_file.write_text(
        "name,kx,ky,kz\n"
        "Cu,390,390,390\n"
        "BadRow\n"
        "Cu,401,401,401\n"
        "Silicon,148,148,148\n",
        encoding="utf-8",
    )

    response = adapter.import_materials_file("project_1", str(material_file))

    assert response.result.ok is True
    assert response.created_count == 2
    assert response.updated_count == 0
    assert len(response.materials) == 2
    assert len(response.warnings) >= 2
    cu = next(item for item in response.materials if item.name.casefold() == "cu")
    assert cu.kx == 401.0
    assert state.project_unsynced is True


def test_material_import_all_invalid_returns_validation_error(tmp_path):
    state = _new_state()
    adapter = LocalIntegrationAdapter(state)
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("name,kx,ky,kz\nBadRow\n,1,2,3\n", encoding="utf-8")

    response = adapter.import_materials_file("project_1", str(bad_file))

    assert response.result.ok is False
    assert response.result.error_code == "VALIDATION_ERROR"
    assert len(response.materials) == 0
