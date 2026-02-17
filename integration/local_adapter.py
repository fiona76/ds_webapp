from copy import deepcopy
from typing import Any

from integration.dto import (
    AddPowerSourceResponse,
    AddTemperatureResponse,
    BoundaryConfigResponse,
    OperationResult,
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
        if not hasattr(self.state, "project_unsynced") or getattr(self.state, "project_unsynced") is None:
            self.state.project_unsynced = False

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
            "power": 0,
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
            target["assigned_objects"] = [name for name in assigned if name != object_name]
            self.state.bc_power_sources = items
            self._mark_mutation()
            return OperationResult(ok=True, message="Unassigned")

        for it in items:
            if it["id"] != power_source_id and object_name in it.get("assigned_objects", []):
                return OperationResult(ok=False, message="Object already assigned", error_code="CONFLICT")

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
            "temperature": 0,
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
            target["assigned_surfaces"] = [name for name in assigned if name != surface_name]
            self.state.bc_temperatures = items
            self._mark_mutation()
            return OperationResult(ok=True, message="Unassigned")

        for it in items:
            if it["id"] != temperature_id and surface_name in it.get("assigned_surfaces", []):
                return OperationResult(ok=False, message="Surface already assigned", error_code="CONFLICT")

        target["assigned_surfaces"] = assigned + [surface_name]
        self.state.bc_temperatures = items
        self._mark_mutation()
        return OperationResult(ok=True, message="Assigned")

    def remove_selected_assignment(self, project_id: str, item_id: str, selected_values: list[str]) -> OperationResult:
        _ = project_id
        if not selected_values:
            return OperationResult(ok=False, message="No selected values", error_code="VALIDATION_ERROR")
        if item_id.startswith("ps_"):
            items = [dict(it) for it in self.state.bc_power_sources]
            found = False
            for it in items:
                if it["id"] == item_id:
                    it["assigned_objects"] = [
                        obj for obj in it.get("assigned_objects", [])
                        if obj not in selected_values
                    ]
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
                    it["assigned_surfaces"] = [
                        surface for surface in it.get("assigned_surfaces", [])
                        if surface not in selected_values
                    ]
                    found = True
                    break
            if not found:
                return OperationResult(ok=False, message="Temperature not found", error_code="NOT_FOUND")
            self.state.bc_temperatures = items
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
        )

    def sync_project_state(self, project_id: str) -> SyncResult:
        _ = project_id
        self.state.project_unsynced = False
        return SyncResult(
            result=OperationResult(ok=True, message="Local state marked as synced"),
            synced=True,
            version=int(getattr(self.state, "project_version", 0)),
        )
