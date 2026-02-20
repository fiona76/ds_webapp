from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CatalogProperty:
    name: str
    kind: str           # "scalar" | "tensor"
    default_units: str
    symmetry: Optional[str] = None  # "orthotropic" | "isotropic" | "anisotropic" | None


@dataclass
class CatalogResponse:
    result: "OperationResult"
    properties: list[CatalogProperty] = field(default_factory=list)


@dataclass
class OperationResult:
    ok: bool
    message: str = ""
    error_code: Optional[str] = None
    details: Optional[dict[str, Any]] = None


@dataclass
class AddPowerSourceResponse:
    result: OperationResult
    item: Optional[dict] = None


@dataclass
class AddTemperatureResponse:
    result: OperationResult
    item: Optional[dict] = None


@dataclass
class BoundaryConfigResponse:
    result: OperationResult
    power_sources: list[dict] = field(default_factory=list)
    temperatures: list[dict] = field(default_factory=list)


@dataclass
class SyncResult:
    result: OperationResult
    synced: bool = False
    version: int = 0


@dataclass
class DefaultMaterialsListResponse:
    result: OperationResult
    names: list[str] = field(default_factory=list)


@dataclass
class DefaultMaterialDetailResponse:
    result: OperationResult
    name: str = ""
    properties: dict = field(default_factory=dict)


@dataclass
class DefaultMaterialsBulkResponse:
    result: OperationResult
    materials: list[dict] = field(default_factory=list)  # each: {name, properties}
