from dataclasses import dataclass, field
from typing import Any, Optional


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
class MaterialRecord:
    name: str
    kx: float
    ky: float
    kz: float


@dataclass
class MaterialWarning:
    line: int
    reason: str
    raw: str


@dataclass
class MaterialsImportResponse:
    result: OperationResult
    created_count: int = 0
    updated_count: int = 0
    warnings: list[MaterialWarning] = field(default_factory=list)
    materials: list[MaterialRecord] = field(default_factory=list)


@dataclass
class MaterialsListResponse:
    result: OperationResult
    materials: list[MaterialRecord] = field(default_factory=list)
