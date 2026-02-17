from typing import Protocol

from integration.dto import (
    AddPowerSourceResponse,
    AddTemperatureResponse,
    BoundaryConfigResponse,
    OperationResult,
    SyncResult,
)


class IntegrationAPI(Protocol):
    def add_power_source(self, project_id: str, name: str | None = None) -> AddPowerSourceResponse:
        ...

    def rename_power_source(self, project_id: str, power_source_id: str, new_name: str) -> OperationResult:
        ...

    def delete_power_source(self, project_id: str, power_source_id: str) -> OperationResult:
        ...

    def set_power_source_value(self, project_id: str, power_source_id: str, power_w_per_m: str | float) -> OperationResult:
        ...

    def toggle_assign_power_source_object(self, project_id: str, power_source_id: str, object_name: str) -> OperationResult:
        ...

    def add_temperature(self, project_id: str, name: str | None = None) -> AddTemperatureResponse:
        ...

    def rename_temperature(self, project_id: str, temperature_id: str, new_name: str) -> OperationResult:
        ...

    def delete_temperature(self, project_id: str, temperature_id: str) -> OperationResult:
        ...

    def set_temperature_value(self, project_id: str, temperature_id: str, temperature_c: str | float) -> OperationResult:
        ...

    def toggle_assign_temperature_surface(self, project_id: str, temperature_id: str, surface_name: str) -> OperationResult:
        ...

    def remove_selected_assignment(self, project_id: str, item_id: str, selected_values: list[str]) -> OperationResult:
        ...

    def get_boundary_config(self, project_id: str) -> BoundaryConfigResponse:
        ...

    def sync_project_state(self, project_id: str) -> SyncResult:
        ...

