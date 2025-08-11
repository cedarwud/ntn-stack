"""
座標領域模組

包含各種座標系統間的轉換功能，提供地理座標、笛卡爾座標、
ECEF座標等之間的互相轉換服務。
"""

from app.domains.coordinates.models.coordinate_model import (
    GeoCoordinate,
    CartesianCoordinate,
    CoordinateTransformation,
)
from app.domains.coordinates.interfaces.coordinate_service_interface import (
    CoordinateServiceInterface,
)
from app.domains.coordinates.services.coordinate_service import CoordinateService
