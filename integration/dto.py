from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OperationResult:
    ok: bool
    message: str = ""
    error_code: Optional[str] = None


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

