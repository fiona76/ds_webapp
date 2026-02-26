from copy import deepcopy
from typing import Any

from app.engine.project import deserialize_project, serialize_project
from integration.dto import (
    AddPowerSourceResponse,
    AddStressResponse,
    AddTemperatureResponse,
    BoundaryConfigResponse,
    CatalogResponse,
    DefaultMaterialDetailResponse,
    DefaultMaterialsBulkResponse,
    DefaultMaterialsListResponse,
    LoadProjectResponse,
    OperationResult,
    SaveProjectResponse,
    SyncResult,
)


class LocalIntegrationAdapter:
    """Local adapter implementation backed by trame state."""

    def __init__(self, state: Any):
        self.state = state
        if not hasattr(self.state, "project_version") or getattr(self.state, "project_version") is None:
            self.state.project_version = 0
        if not hasattr(self.state, "project_dirty") or getattr(self.state, "project_dirty") is None:
            self.state.project_dirty = False
        if not hasattr(self.state, "project_filename") or getattr(self.state, "project_filename") is None:
            self.state.project_filename = ""
        if not hasattr(self.state, "project_unsynced") or getattr(self.state, "project_unsynced") is None:
            self.state.project_unsynced = False
        if not hasattr(self.state, "materials_library") or getattr(self.state, "materials_library") is None:
            self.state.materials_library = []

    def _mark_mutation(self):
        version = getattr(self.state, "project_version", 0)
        try:
            version_int = int(version)
        except Exception:
            version_int = 0
        self.state.project_version = version_int + 1
        self.state.project_dirty = True
        self.state.project_unsynced = True

    def add_power_source(self, project_id: str, name: str | None = None) -> AddPowerSourceResponse:
        _ = project_id
        self.state.bc_power_source_counter = self.state.bc_power_source_counter + 1
        item = {
            "id": f"ps_{self.state.bc_power_source_counter}",
            "name": name.strip() if name and name.strip() else f"Power Source {self.state.bc_power_source_counter}",
            "assigned_objects": [],
            "overridden_objects": [],
            "power": 0,
            "selection_mode": "manual",
        }
        self.state.bc_power_sources = list(self.state.bc_power_sources) + [item]
        self._mark_mutation()
        return AddPowerSourceResponse(result=OperationResult(ok=True), item=item)

    def rename_power_source(self, project_id: str, power_source_id: str, new_name: str) -> OperationResult:
        _ = project_id
        if not new_name or not new_name.strip():
            return OperationResult(ok=False, message="Name cannot be empty", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_power_sources]
        found = False
        for it in items:
            if it["id"] == power_source_id:
                it["name"] = new_name.strip()
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
        self.state.bc_power_sources = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def delete_power_source(self, project_id: str, power_source_id: str) -> OperationResult:
        _ = project_id
        before = len(self.state.bc_power_sources)
        self.state.bc_power_sources = [it for it in self.state.bc_power_sources if it["id"] != power_source_id]
        if len(self.state.bc_power_sources) == before:
            return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
        self._mark_mutation()
        return OperationResult(ok=True)

    def set_power_source_value(self, project_id: str, power_source_id: str, power_w_per_m: str | float) -> OperationResult:
        _ = project_id
        try:
            numeric_value = float(power_w_per_m)
        except Exception:
            numeric_value = 0.0
        items = [dict(it) for it in self.state.bc_power_sources]
        found = False
        for it in items:
            if it["id"] == power_source_id:
                it["power"] = numeric_value
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
        self.state.bc_power_sources = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def toggle_assign_power_source_object(self, project_id: str, power_source_id: str, object_name: str) -> OperationResult:
        _ = project_id
        if not power_source_id or not object_name:
            return OperationResult(ok=False, message="Invalid assignment", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_power_sources]
        target = None
        for it in items:
            if it["id"] == power_source_id:
                target = it
                break
        if target is None:
            return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")

        assigned = list(target.get("assigned_objects", []))
        if object_name in assigned:
            # Unassign: remove from assigned, revert mode if needed
            target["assigned_objects"] = [n for n in assigned if n != object_name]
            if target.get("selection_mode") == "all":
                target["selection_mode"] = "manual"
            self.state.bc_power_sources = items
            self._mark_mutation()
            return OperationResult(ok=True, message="Unassigned")

        # Steal from any other PS that currently owns this object
        for it in items:
            if it["id"] != power_source_id and object_name in it.get("assigned_objects", []):
                it["assigned_objects"] = [n for n in it["assigned_objects"] if n != object_name]
                overridden = list(it.get("overridden_objects", []))
                if object_name not in overridden:
                    overridden.append(object_name)
                it["overridden_objects"] = overridden

        # Remove from this item's own overridden list (if it was there)
        target["overridden_objects"] = [n for n in target.get("overridden_objects", []) if n != object_name]
        target["assigned_objects"] = assigned + [object_name]
        self.state.bc_power_sources = items
        self._mark_mutation()
        return OperationResult(ok=True, message="Assigned")

    def add_temperature(self, project_id: str, name: str | None = None) -> AddTemperatureResponse:
        _ = project_id
        self.state.bc_temperature_counter = self.state.bc_temperature_counter + 1
        item = {
            "id": f"temp_{self.state.bc_temperature_counter}",
            "name": name.strip() if name and name.strip() else f"Temperature {self.state.bc_temperature_counter}",
            "assigned_surfaces": [],
            "overridden_surfaces": [],
            "temperature": 0,
            "selection_mode": "manual",
        }
        self.state.bc_temperatures = list(self.state.bc_temperatures) + [item]
        self._mark_mutation()
        return AddTemperatureResponse(result=OperationResult(ok=True), item=item)

    def rename_temperature(self, project_id: str, temperature_id: str, new_name: str) -> OperationResult:
        _ = project_id
        if not new_name or not new_name.strip():
            return OperationResult(ok=False, message="Name cannot be empty", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_temperatures]
        found = False
        for it in items:
            if it["id"] == temperature_id:
                it["name"] = new_name.strip()
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
        self.state.bc_temperatures = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def delete_temperature(self, project_id: str, temperature_id: str) -> OperationResult:
        _ = project_id
        before = len(self.state.bc_temperatures)
        self.state.bc_temperatures = [it for it in self.state.bc_temperatures if it["id"] != temperature_id]
        if len(self.state.bc_temperatures) == before:
            return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
        self._mark_mutation()
        return OperationResult(ok=True)

    def set_temperature_value(self, project_id: str, temperature_id: str, temperature_c: str | float) -> OperationResult:
        _ = project_id
        try:
            numeric_value = float(temperature_c)
        except Exception:
            numeric_value = 0.0
        items = [dict(it) for it in self.state.bc_temperatures]
        found = False
        for it in items:
            if it["id"] == temperature_id:
                it["temperature"] = numeric_value
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
        self.state.bc_temperatures = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def toggle_assign_temperature_surface(self, project_id: str, temperature_id: str, surface_name: str) -> OperationResult:
        _ = project_id
        if not temperature_id or not surface_name:
            return OperationResult(ok=False, message="Invalid assignment", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_temperatures]
        target = None
        for it in items:
            if it["id"] == temperature_id:
                target = it
                break
        if target is None:
            return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")

        assigned = list(target.get("assigned_surfaces", []))
        if surface_name in assigned:
            target["assigned_surfaces"] = [n for n in assigned if n != surface_name]
            if target.get("selection_mode") == "all":
                target["selection_mode"] = "manual"
            self.state.bc_temperatures = items
            self._mark_mutation()
            return OperationResult(ok=True, message="Unassigned")

        # Steal from any other temperature that currently owns this surface
        for it in items:
            if it["id"] != temperature_id and surface_name in it.get("assigned_surfaces", []):
                it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != surface_name]
                overridden = list(it.get("overridden_surfaces", []))
                if surface_name not in overridden:
                    overridden.append(surface_name)
                it["overridden_surfaces"] = overridden

        target["overridden_surfaces"] = [n for n in target.get("overridden_surfaces", []) if n != surface_name]
        target["assigned_surfaces"] = assigned + [surface_name]
        self.state.bc_temperatures = items
        self._mark_mutation()
        return OperationResult(ok=True, message="Assigned")

    def add_stress(self, project_id: str, name: str | None = None) -> AddStressResponse:
        _ = project_id
        self.state.bc_stress_counter = self.state.bc_stress_counter + 1
        item = {
            "id": f"stress_{self.state.bc_stress_counter}",
            "name": name.strip() if name and name.strip() else f"Stress {self.state.bc_stress_counter}",
            "assigned_surfaces": [],
            "overridden_surfaces": [],
            "value": 0,
            "selection_mode": "manual",
        }
        self.state.bc_stresses = list(self.state.bc_stresses) + [item]
        self._mark_mutation()
        return AddStressResponse(result=OperationResult(ok=True), item=item)

    def rename_stress(self, project_id: str, stress_id: str, new_name: str) -> OperationResult:
        _ = project_id
        if not new_name or not new_name.strip():
            return OperationResult(ok=False, message="Name cannot be empty", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_stresses]
        found = False
        for it in items:
            if it["id"] == stress_id:
                it["name"] = new_name.strip()
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
        self.state.bc_stresses = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def delete_stress(self, project_id: str, stress_id: str) -> OperationResult:
        _ = project_id
        before = len(self.state.bc_stresses)
        self.state.bc_stresses = [it for it in self.state.bc_stresses if it["id"] != stress_id]
        if len(self.state.bc_stresses) == before:
            return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
        self._mark_mutation()
        return OperationResult(ok=True)

    def set_stress_value(self, project_id: str, stress_id: str, value: str | float) -> OperationResult:
        _ = project_id
        try:
            numeric_value = float(value)
        except Exception:
            numeric_value = 0.0
        items = [dict(it) for it in self.state.bc_stresses]
        found = False
        for it in items:
            if it["id"] == stress_id:
                it["value"] = numeric_value
                found = True
                break
        if not found:
            return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
        self.state.bc_stresses = items
        self._mark_mutation()
        return OperationResult(ok=True)

    def toggle_assign_stress_surface(self, project_id: str, stress_id: str, surface_name: str) -> OperationResult:
        _ = project_id
        if not stress_id or not surface_name:
            return OperationResult(ok=False, message="Invalid assignment", error_code="VALIDATION_ERROR")
        items = [dict(it) for it in self.state.bc_stresses]
        target = None
        for it in items:
            if it["id"] == stress_id:
                target = it
                break
        if target is None:
            return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")

        assigned = list(target.get("assigned_surfaces", []))
        if surface_name in assigned:
            target["assigned_surfaces"] = [n for n in assigned if n != surface_name]
            if target.get("selection_mode") == "all":
                target["selection_mode"] = "manual"
            self.state.bc_stresses = items
            self._mark_mutation()
            return OperationResult(ok=True, message="Unassigned")

        # Steal from any other stress that currently owns this surface
        for it in items:
            if it["id"] != stress_id and surface_name in it.get("assigned_surfaces", []):
                it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != surface_name]
                overridden = list(it.get("overridden_surfaces", []))
                if surface_name not in overridden:
                    overridden.append(surface_name)
                it["overridden_surfaces"] = overridden

        target["overridden_surfaces"] = [n for n in target.get("overridden_surfaces", []) if n != surface_name]
        target["assigned_surfaces"] = assigned + [surface_name]
        self.state.bc_stresses = items
        self._mark_mutation()
        return OperationResult(ok=True, message="Assigned")

    def remove_selected_assignment(self, project_id: str, item_id: str, selected_values: list[str]) -> OperationResult:
        _ = project_id
        if not selected_values:
            return OperationResult(ok=False, message="No selected values", error_code="VALIDATION_ERROR")
        selected_set = set(selected_values)
        if item_id.startswith("ps_"):
            items = [dict(it) for it in self.state.bc_power_sources]
            found = False
            for it in items:
                if it["id"] == item_id:
                    old_assigned = list(it.get("assigned_objects", []))
                    it["assigned_objects"] = [obj for obj in old_assigned if obj not in selected_set]
                    it["overridden_objects"] = [obj for obj in it.get("overridden_objects", []) if obj not in selected_set]
                    if it.get("selection_mode") == "all" and any(obj in selected_set for obj in old_assigned):
                        it["selection_mode"] = "manual"
                    found = True
                    break
            if not found:
                return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
            self.state.bc_power_sources = items
        elif item_id.startswith("temp_"):
            items = [dict(it) for it in self.state.bc_temperatures]
            found = False
            for it in items:
                if it["id"] == item_id:
                    old_assigned = list(it.get("assigned_surfaces", []))
                    it["assigned_surfaces"] = [s for s in old_assigned if s not in selected_set]
                    it["overridden_surfaces"] = [s for s in it.get("overridden_surfaces", []) if s not in selected_set]
                    if it.get("selection_mode") == "all" and any(s in selected_set for s in old_assigned):
                        it["selection_mode"] = "manual"
                    found = True
                    break
            if not found:
                return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
            self.state.bc_temperatures = items
        elif item_id.startswith("stress_"):
            items = [dict(it) for it in self.state.bc_stresses]
            found = False
            for it in items:
                if it["id"] == item_id:
                    old_assigned = list(it.get("assigned_surfaces", []))
                    it["assigned_surfaces"] = [s for s in old_assigned if s not in selected_set]
                    it["overridden_surfaces"] = [s for s in it.get("overridden_surfaces", []) if s not in selected_set]
                    if it.get("selection_mode") == "all" and any(s in selected_set for s in old_assigned):
                        it["selection_mode"] = "manual"
                    found = True
                    break
            if not found:
                return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
            self.state.bc_stresses = items
        else:
            return OperationResult(ok=False, message="Invalid item id", error_code="VALIDATION_ERROR")
        self._mark_mutation()
        return OperationResult(ok=True)

    def reclaim_bc_assignment(self, project_id: str, item_id: str, value: str) -> OperationResult:
        _ = project_id
        if not item_id or not value:
            return OperationResult(ok=False, message="Invalid arguments", error_code="VALIDATION_ERROR")
        if item_id.startswith("ps_"):
            items = [dict(it) for it in self.state.bc_power_sources]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
            if value not in target.get("overridden_objects", []):
                return OperationResult(ok=False, message="Value not in overridden list", error_code="NOT_FOUND")
            # Remove from current owner's assigned list
            for it in items:
                if it["id"] != item_id and value in it.get("assigned_objects", []):
                    it["assigned_objects"] = [n for n in it["assigned_objects"] if n != value]
            # Move from overridden to assigned
            target["overridden_objects"] = [n for n in target["overridden_objects"] if n != value]
            assigned = list(target.get("assigned_objects", []))
            if value not in assigned:
                assigned.append(value)
            target["assigned_objects"] = assigned
            self.state.bc_power_sources = items
        elif item_id.startswith("temp_"):
            items = [dict(it) for it in self.state.bc_temperatures]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
            if value not in target.get("overridden_surfaces", []):
                return OperationResult(ok=False, message="Value not in overridden list", error_code="NOT_FOUND")
            for it in items:
                if it["id"] != item_id and value in it.get("assigned_surfaces", []):
                    it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != value]
            target["overridden_surfaces"] = [n for n in target["overridden_surfaces"] if n != value]
            assigned = list(target.get("assigned_surfaces", []))
            if value not in assigned:
                assigned.append(value)
            target["assigned_surfaces"] = assigned
            self.state.bc_temperatures = items
        elif item_id.startswith("stress_"):
            items = [dict(it) for it in self.state.bc_stresses]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
            if value not in target.get("overridden_surfaces", []):
                return OperationResult(ok=False, message="Value not in overridden list", error_code="NOT_FOUND")
            for it in items:
                if it["id"] != item_id and value in it.get("assigned_surfaces", []):
                    it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != value]
            target["overridden_surfaces"] = [n for n in target["overridden_surfaces"] if n != value]
            assigned = list(target.get("assigned_surfaces", []))
            if value not in assigned:
                assigned.append(value)
            target["assigned_surfaces"] = assigned
            self.state.bc_stresses = items
        else:
            return OperationResult(ok=False, message="Invalid item id", error_code="VALIDATION_ERROR")
        self._mark_mutation()
        return OperationResult(ok=True, message="Reclaimed")

    def set_bc_assignment_mode(self, project_id: str, item_id: str, mode: str, all_values: list[str] = []) -> OperationResult:
        _ = project_id
        if not item_id:
            return OperationResult(ok=False, message="Invalid item id", error_code="VALIDATION_ERROR")
        if item_id.startswith("ps_"):
            items = [dict(it) for it in self.state.bc_power_sources]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Power source not found", error_code="NOT_FOUND")
            target["selection_mode"] = mode
            if mode == "all":
                existing_assigned = list(target.get("assigned_objects", []))
                for value in all_values:
                    if value not in existing_assigned:
                        for it in items:
                            if it["id"] != item_id and value in it.get("assigned_objects", []):
                                it["assigned_objects"] = [n for n in it["assigned_objects"] if n != value]
                                overridden = list(it.get("overridden_objects", []))
                                if value not in overridden:
                                    overridden.append(value)
                                it["overridden_objects"] = overridden
                target["assigned_objects"] = list(dict.fromkeys(all_values))
                all_set = set(all_values)
                target["overridden_objects"] = [n for n in target.get("overridden_objects", []) if n not in all_set]
            self.state.bc_power_sources = items
        elif item_id.startswith("temp_"):
            items = [dict(it) for it in self.state.bc_temperatures]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
            target["selection_mode"] = mode
            if mode == "all":
                existing_assigned = list(target.get("assigned_surfaces", []))
                for value in all_values:
                    if value not in existing_assigned:
                        for it in items:
                            if it["id"] != item_id and value in it.get("assigned_surfaces", []):
                                it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != value]
                                overridden = list(it.get("overridden_surfaces", []))
                                if value not in overridden:
                                    overridden.append(value)
                                it["overridden_surfaces"] = overridden
                target["assigned_surfaces"] = list(dict.fromkeys(all_values))
                all_set = set(all_values)
                target["overridden_surfaces"] = [n for n in target.get("overridden_surfaces", []) if n not in all_set]
            self.state.bc_temperatures = items
        elif item_id.startswith("stress_"):
            items = [dict(it) for it in self.state.bc_stresses]
            target = None
            for it in items:
                if it["id"] == item_id:
                    target = it
                    break
            if target is None:
                return OperationResult(ok=False, message="Stress not found", error_code="NOT_FOUND")
            target["selection_mode"] = mode
            if mode == "all":
                existing_assigned = list(target.get("assigned_surfaces", []))
                for value in all_values:
                    if value not in existing_assigned:
                        for it in items:
                            if it["id"] != item_id and value in it.get("assigned_surfaces", []):
                                it["assigned_surfaces"] = [n for n in it["assigned_surfaces"] if n != value]
                                overridden = list(it.get("overridden_surfaces", []))
                                if value not in overridden:
                                    overridden.append(value)
                                it["overridden_surfaces"] = overridden
                target["assigned_surfaces"] = list(dict.fromkeys(all_values))
                all_set = set(all_values)
                target["overridden_surfaces"] = [n for n in target.get("overridden_surfaces", []) if n not in all_set]
            self.state.bc_stresses = items
        else:
            return OperationResult(ok=False, message="Invalid item id", error_code="VALIDATION_ERROR")
        self._mark_mutation()
        return OperationResult(ok=True)

    def get_boundary_config(self, project_id: str) -> BoundaryConfigResponse:
        _ = project_id
        return BoundaryConfigResponse(
            result=OperationResult(ok=True),
            power_sources=deepcopy(list(self.state.bc_power_sources)),
            temperatures=deepcopy(list(self.state.bc_temperatures)),
            stresses=deepcopy(list(self.state.bc_stresses)),
        )

    def sync_project_state(self, project_id: str) -> SyncResult:
        _ = project_id
        self.state.project_unsynced = False
        return SyncResult(
            result=OperationResult(ok=True, message="Local state marked as synced"),
            synced=True,
            version=int(getattr(self.state, "project_version", 0)),
        )

    def get_materials_catalog(self) -> CatalogResponse:
        return CatalogResponse(
            result=OperationResult(
                ok=False,
                message="Materials catalog requires the redrock API server",
                error_code="NOT_AVAILABLE",
            )
        )

    def list_default_materials(self) -> DefaultMaterialsListResponse:
        return DefaultMaterialsListResponse(
            result=OperationResult(
                ok=False,
                message="Load default materials requires the redrock API server",
                error_code="NOT_AVAILABLE",
            )
        )

    def get_default_material(self, name: str) -> DefaultMaterialDetailResponse:
        return DefaultMaterialDetailResponse(
            result=OperationResult(
                ok=False,
                message="Load default materials requires the redrock API server",
                error_code="NOT_AVAILABLE",
            )
        )

    def list_default_materials_full(self) -> DefaultMaterialsBulkResponse:
        return DefaultMaterialsBulkResponse(
            result=OperationResult(
                ok=False,
                message="Load default materials requires the redrock API server",
                error_code="NOT_AVAILABLE",
            )
        )

    def save_project(self, project_id: str, geometry_meshes: dict, step_file_paths: dict) -> SaveProjectResponse:
        _ = project_id
        try:
            zip_bytes = serialize_project(self.state, geometry_meshes, step_file_paths)
            self.state.project_dirty = False
            filename = getattr(self.state, "project_filename", "") or "project.zip"
            return SaveProjectResponse(
                result=OperationResult(ok=True),
                zip_bytes=zip_bytes,
                suggested_filename=filename,
            )
        except Exception as exc:
            return SaveProjectResponse(
                result=OperationResult(ok=False, message=str(exc), error_code="SERIALIZE_ERROR"),
            )

    def load_project(self, project_id: str, zip_bytes: bytes) -> LoadProjectResponse:
        _ = project_id
        try:
            result = deserialize_project(zip_bytes)
            return LoadProjectResponse(
                result=OperationResult(ok=True),
                project_data=result["project_data"],
                step_file_bytes=result["step_file_bytes"],
            )
        except Exception as exc:
            return LoadProjectResponse(
                result=OperationResult(ok=False, message=str(exc), error_code="DESERIALIZE_ERROR"),
            )
