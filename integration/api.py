from typing import Protocol

from integration.dto import (
    AddPowerSourceResponse,
    AddStressResponse,
    AddTemperatureResponse,
    BoundaryConfigResponse,
    CatalogResponse,
    DefaultMaterialsListResponse,
    DefaultMaterialDetailResponse,
    DefaultMaterialsBulkResponse,
    LoadProjectResponse,
    OperationResult,
    SaveProjectResponse,
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

    def add_stress(self, project_id: str, name: str | None = None) -> AddStressResponse:
        ...

    def rename_stress(self, project_id: str, stress_id: str, new_name: str) -> OperationResult:
        ...

    def delete_stress(self, project_id: str, stress_id: str) -> OperationResult:
        ...

    def set_stress_value(self, project_id: str, stress_id: str, value: str | float) -> OperationResult:
        ...

    def toggle_assign_stress_surface(self, project_id: str, stress_id: str, surface_name: str) -> OperationResult:
        ...

    def reclaim_bc_assignment(self, project_id: str, item_id: str, value: str) -> OperationResult:
        ...

    def set_bc_assignment_mode(self, project_id: str, item_id: str, mode: str, all_values: list[str] = ...) -> OperationResult:
        ...

    def remove_selected_assignment(self, project_id: str, item_id: str, selected_values: list[str]) -> OperationResult:
        ...

    def get_boundary_config(self, project_id: str) -> BoundaryConfigResponse:
        ...

    def sync_project_state(self, project_id: str) -> SyncResult:
        ...

    def get_materials_catalog(self) -> CatalogResponse:
        ...

    def list_default_materials(self) -> DefaultMaterialsListResponse:
        ...

    def get_default_material(self, name: str) -> DefaultMaterialDetailResponse:
        ...

    def list_default_materials_full(self) -> DefaultMaterialsBulkResponse:
        ...

    def save_project(self, project_id: str, geometry_meshes: dict, step_file_paths: dict) -> SaveProjectResponse:
        ...

    def load_project(self, project_id: str, zip_bytes: bytes) -> LoadProjectResponse:
        ...
