"""
衛星領域模組

包含衛星軌道計算、TLE 數據管理和過境預測等功能。
"""

from app.domains.satellite.models.satellite_model import (
    Satellite,
    SatellitePass,
    TLEData,
    OrbitPoint,
    OrbitPropagationResult,
)
from app.domains.satellite.interfaces.satellite_repository import (
    SatelliteRepositoryInterface,
)
from app.domains.satellite.interfaces.orbit_service_interface import (
    OrbitServiceInterface,
)
from app.domains.satellite.interfaces.tle_service_interface import TLEServiceInterface
from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
    SQLModelSatelliteRepository,
)
from app.domains.satellite.services.orbit_service import OrbitService
from app.domains.satellite.services.tle_service import TLEService
