"""
統一的衛星API響應格式和數據驗證
"""

from typing import Generic, TypeVar, Optional, Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

T = TypeVar('T')

class ApiStatus(str, Enum):
    """API響應狀態枚舉"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ErrorCode(str, Enum):
    """統一的錯誤代碼"""
    # TLE相關錯誤
    TLE_FETCH_FAILED = "TLE_FETCH_FAILED"
    TLE_INVALID_FORMAT = "TLE_INVALID_FORMAT"
    TLE_DATA_OUTDATED = "TLE_DATA_OUTDATED"
    
    # 軌道計算錯誤
    ORBIT_CALCULATION_FAILED = "ORBIT_CALCULATION_FAILED"
    ORBIT_PREDICTION_TIMEOUT = "ORBIT_PREDICTION_TIMEOUT"
    INVALID_TIME_RANGE = "INVALID_TIME_RANGE"
    
    # 衛星相關錯誤
    SATELLITE_NOT_FOUND = "SATELLITE_NOT_FOUND"
    SATELLITE_NOT_VISIBLE = "SATELLITE_NOT_VISIBLE"
    INVALID_SATELLITE_ID = "INVALID_SATELLITE_ID"
    
    # 座標和位置錯誤
    INVALID_COORDINATES = "INVALID_COORDINATES"
    OBSERVER_LOCATION_INVALID = "OBSERVER_LOCATION_INVALID"
    
    # 系統和網路錯誤
    NETWORK_ERROR = "NETWORK_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

class ApiError(BaseModel):
    """API錯誤詳情"""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ApiResponse(BaseModel, Generic[T]):
    """統一的API響應格式"""
    status: ApiStatus
    data: Optional[T] = None
    error: Optional[ApiError] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('data', 'error')
    def validate_response_content(cls, v, values):
        """驗證響應內容的一致性"""
        status = values.get('status')
        if status == ApiStatus.SUCCESS and v is None and 'error' not in values:
            raise ValueError("成功響應必須包含數據或沒有錯誤")
        if status == ApiStatus.ERROR and 'data' in values and values['data'] is not None:
            raise ValueError("錯誤響應不應包含數據")
        return v

class SatellitePosition(BaseModel):
    """衛星位置數據格式"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度（度）")
    longitude: float = Field(..., ge=-180, le=180, description="經度（度）")
    altitude: float = Field(..., ge=0, description="高度（公里）")
    timestamp: datetime = Field(..., description="位置時間戳")
    
    # ECEF座標（可選）
    ecef_x_km: Optional[float] = None
    ecef_y_km: Optional[float] = None
    ecef_z_km: Optional[float] = None
    
    # 相對於觀測者的參數（可選）
    elevation_deg: Optional[float] = Field(None, ge=0, le=90)
    azimuth_deg: Optional[float] = Field(None, ge=0, lt=360)
    distance_km: Optional[float] = Field(None, ge=0)

class SatelliteVelocity(BaseModel):
    """衛星速度數據格式"""
    speed_km_s: float = Field(..., description="速度大小（公里/秒）")
    velocity_x: float = Field(..., description="X方向速度分量")
    velocity_y: float = Field(..., description="Y方向速度分量")
    velocity_z: float = Field(..., description="Z方向速度分量")

class SatelliteOrbitalParameters(BaseModel):
    """衛星軌道參數"""
    period_minutes: float = Field(..., gt=0, description="軌道週期（分鐘）")
    inclination_deg: float = Field(..., ge=0, le=180, description="軌道傾角（度）")
    apogee_km: float = Field(..., ge=0, description="遠地點高度（公里）")
    perigee_km: float = Field(..., ge=0, description="近地點高度（公里）")
    eccentricity: float = Field(..., ge=0, lt=1, description="軌道離心率")

class TLEData(BaseModel):
    """TLE數據格式"""
    line1: str = Field(..., min_length=69, max_length=69, description="TLE第一行")
    line2: str = Field(..., min_length=69, max_length=69, description="TLE第二行")
    epoch: datetime = Field(..., description="TLE數據時期")
    source: str = Field(..., description="TLE數據來源")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('line1', 'line2')
    def validate_tle_format(cls, v):
        """驗證TLE格式"""
        if len(v) != 69:
            raise ValueError("TLE行必須為69個字符")
        if not v[0].isdigit():
            raise ValueError("TLE行必須以數字開頭")
        return v

class StandardSatelliteInfo(BaseModel):
    """標準化的衛星信息格式"""
    id: int = Field(..., description="衛星數據庫ID")
    name: str = Field(..., min_length=1, description="衛星名稱")
    norad_id: int = Field(..., gt=0, description="NORAD ID")
    
    # 當前位置和狀態
    position: SatellitePosition
    velocity: Optional[SatelliteVelocity] = None
    
    # 軌道參數
    orbital_parameters: SatelliteOrbitalParameters
    
    # TLE數據
    tle_data: Optional[TLEData] = None
    
    # 衛星分類和狀態
    constellation: Optional[str] = Field(None, description="所屬星座")
    operational_status: Optional[str] = Field(None, description="運行狀態")
    launch_date: Optional[datetime] = Field(None, description="發射日期")

class SatellitePass(BaseModel):
    """衛星過境信息"""
    satellite_id: int = Field(..., description="衛星ID")
    start_time: datetime = Field(..., description="過境開始時間")
    end_time: datetime = Field(..., description="過境結束時間")
    max_elevation: float = Field(..., ge=0, le=90, description="最大仰角（度）")
    max_elevation_time: datetime = Field(..., description="最大仰角時間")
    duration_seconds: int = Field(..., gt=0, description="過境持續時間（秒）")
    
    # 過境詳細軌跡（可選）
    trajectory_points: Optional[List[SatellitePosition]] = None

class BatchSatelliteRequest(BaseModel):
    """批量衛星數據請求格式"""
    satellite_ids: List[int] = Field(..., min_items=1, max_items=100)
    include_velocity: bool = Field(default=False)
    include_orbital_parameters: bool = Field(default=False)
    include_tle_data: bool = Field(default=False)

class SatelliteQueryFilter(BaseModel):
    """衛星查詢篩選器"""
    constellation: Optional[str] = None
    min_elevation_deg: Optional[float] = Field(None, ge=0, le=90)
    max_distance_km: Optional[float] = Field(None, gt=0)
    operational_only: bool = Field(default=True)
    limit: int = Field(default=50, gt=0, le=500)
    offset: int = Field(default=0, ge=0)

# 工具函數
def create_success_response(data: T, meta: Optional[Dict[str, Any]] = None) -> ApiResponse[T]:
    """創建成功響應"""
    return ApiResponse(
        status=ApiStatus.SUCCESS,
        data=data,
        meta=meta
    )

def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> ApiResponse[None]:
    """創建錯誤響應"""
    return ApiResponse(
        status=ApiStatus.ERROR,
        error=ApiError(
            code=error_code,
            message=message,
            details=details
        )
    )

def create_warning_response(
    data: T,
    warning_message: str,
    meta: Optional[Dict[str, Any]] = None
) -> ApiResponse[T]:
    """創建警告響應"""
    return ApiResponse(
        status=ApiStatus.WARNING,
        data=data,
        meta={**(meta or {}), "warning": warning_message}
    )

# 數據驗證工具
class SatelliteDataValidator:
    """衛星數據驗證工具"""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float, alt: float) -> bool:
        """驗證座標有效性"""
        return (
            -90 <= lat <= 90 and
            -180 <= lon <= 180 and
            alt >= -500  # 允許海平面以下500m
        )
    
    @staticmethod
    def validate_norad_id(norad_id: int) -> bool:
        """驗證NORAD ID格式"""
        return 10000 <= norad_id <= 99999
    
    @staticmethod
    def validate_time_range(start_time: datetime, end_time: datetime) -> bool:
        """驗證時間範圍"""
        return start_time < end_time and (end_time - start_time).days <= 30
    
    @staticmethod
    def validate_tle_lines(line1: str, line2: str) -> bool:
        """驗證TLE行格式"""
        if len(line1) != 69 or len(line2) != 69:
            return False
        
        # 檢查行號
        if not (line1.startswith('1 ') and line2.startswith('2 ')):
            return False
        
        # 檢查NORAD ID一致性
        try:
            norad1 = int(line1[2:7])
            norad2 = int(line2[2:7])
            return norad1 == norad2
        except ValueError:
            return False