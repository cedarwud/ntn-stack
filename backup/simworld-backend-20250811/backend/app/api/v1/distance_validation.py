"""
距離驗證API端點 - 提供距離計算驗證服務

功能：
1. 驗證衛星距離計算精度
2. 提供理論vs實際對比分析  
3. 生成距離精度報告
4. 監控系統性偏差問題
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ...services.distance_validator import (
    DistanceValidator, 
    DistanceValidationResult, 
    ValidationSummary,
    create_distance_validator
)
from ...services.distance_calculator import Position

logger = structlog.get_logger(__name__)

# Response Models
class DistanceValidationResponse(BaseModel):
    """距離驗證響應"""
    satellite_name: str
    norad_id: str
    elevation_deg: float
    azimuth_deg: float
    sgp4_distance_km: float
    theoretical_distance_km: float
    distance_difference_km: float
    relative_error_percent: float
    validation_status: str
    error_analysis: str
    timestamp: str

class ValidationSummaryResponse(BaseModel):
    """驗證摘要響應"""
    total_satellites: int
    validation_passed: int
    validation_warnings: int
    validation_failed: int
    mean_error_km: float
    max_error_km: float
    min_error_km: float
    std_error_km: float
    high_elevation_accuracy: float
    medium_elevation_accuracy: float
    low_elevation_accuracy: float

class ConstellationValidationResponse(BaseModel):
    """星座驗證響應"""
    validation_results: List[DistanceValidationResponse]
    summary: ValidationSummaryResponse
    validation_report: str
    timestamp: str
    observer_location: Dict[str, float]

class SatelliteDataInput(BaseModel):
    """衛星數據輸入"""
    name: str
    norad_id: str
    latitude: float
    longitude: float
    altitude: float = Field(default=550.0, description="軌道高度(km)")
    distance_km: float = Field(description="SGP4計算的距離(km)")

# 創建路由器
router = APIRouter(
    prefix="/api/v1/distance-validation",
    tags=["Distance Validation"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

def get_distance_validator() -> DistanceValidator:
    """獲取距離驗證器實例"""
    return create_distance_validator()

@router.get(
    "/theoretical-distance",
    summary="計算理論斜距",
    description="使用球面幾何公式計算理論斜距"
)
async def calculate_theoretical_distance(
    elevation_deg: float = Query(..., ge=-90, le=90, description="衛星仰角(度)"),
    orbit_altitude_km: float = Query(550.0, ge=200, le=2000, description="軌道高度(km)"),
    validator: DistanceValidator = Depends(get_distance_validator)
):
    """計算理論斜距"""
    try:
        theoretical_distance = validator.calculate_theoretical_slant_range(
            elevation_deg=elevation_deg,
            orbit_altitude_km=orbit_altitude_km
        )
        
        return {
            "elevation_deg": elevation_deg,
            "orbit_altitude_km": orbit_altitude_km,
            "theoretical_distance_km": theoretical_distance,
            "formula": "d = √[R_e² + (R_e + h)² - 2·R_e·(R_e + h)·sin(ε)]",
            "parameters": {
                "R_e": validator.EARTH_RADIUS_KM,
                "h": orbit_altitude_km,
                "epsilon": elevation_deg
            }
        }
        
    except Exception as e:
        logger.error("理論斜距計算失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"計算失敗: {str(e)}")

@router.post(
    "/validate-satellite",
    response_model=DistanceValidationResponse,
    summary="驗證單顆衛星距離",
    description="驗證單顆衛星的距離計算精度"
)
async def validate_single_satellite(
    satellite_data: SatelliteDataInput,
    observer_lat: float = Query(..., ge=-90, le=90, description="觀測者緯度"),
    observer_lon: float = Query(..., ge=-180, le=180, description="觀測者經度"), 
    observer_alt: float = Query(0.024, ge=0, description="觀測者高度(km)"),
    validator: DistanceValidator = Depends(get_distance_validator)
):
    """驗證單顆衛星距離計算"""
    try:
        # 構建觀測者位置
        ue_position = Position(
            latitude=observer_lat,
            longitude=observer_lon,
            altitude=observer_alt
        )
        
        # 構建衛星位置
        from ...services.sgp4_calculator import OrbitPosition
        satellite_position = OrbitPosition(
            latitude=satellite_data.latitude,
            longitude=satellite_data.longitude,
            altitude=satellite_data.altitude,
            velocity=(0.0, 0.0, 0.0),
            timestamp=datetime.utcnow(),
            satellite_id=satellite_data.norad_id
        )
        
        # 驗證距離
        result = validator.validate_satellite_distance(
            satellite_name=satellite_data.name,
            norad_id=satellite_data.norad_id,
            ue_position=ue_position,
            satellite_position=satellite_position,
            sgp4_distance_km=satellite_data.distance_km
        )
        
        return DistanceValidationResponse(
            satellite_name=result.satellite_name,
            norad_id=result.norad_id,
            elevation_deg=result.elevation_deg,
            azimuth_deg=result.azimuth_deg,
            sgp4_distance_km=result.sgp4_distance_km,
            theoretical_distance_km=result.theoretical_distance_km,
            distance_difference_km=result.distance_difference_km,
            relative_error_percent=result.relative_error_percent,
            validation_status=result.validation_status,
            error_analysis=result.error_analysis,
            timestamp=result.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error("衛星距離驗證失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")

@router.post(
    "/validate-constellation",
    response_model=ConstellationValidationResponse,
    summary="驗證衛星星座距離",
    description="批量驗證衛星星座的距離計算精度"
)
async def validate_constellation(
    satellites_data: List[SatelliteDataInput],
    observer_lat: float = Query(..., ge=-90, le=90, description="觀測者緯度"),
    observer_lon: float = Query(..., ge=-180, le=180, description="觀測者經度"),
    observer_alt: float = Query(0.024, ge=0, description="觀測者高度(km)"),
    validator: DistanceValidator = Depends(get_distance_validator)
):
    """驗證衛星星座距離計算"""
    try:
        # 構建觀測者位置
        ue_position = Position(
            latitude=observer_lat,
            longitude=observer_lon,
            altitude=observer_alt
        )
        
        # 轉換輸入數據格式
        satellites_dict = []
        for sat in satellites_data:
            satellites_dict.append({
                'name': sat.name,
                'norad_id': sat.norad_id,
                'latitude': sat.latitude,
                'longitude': sat.longitude,
                'altitude': sat.altitude,
                'distance_km': sat.distance_km
            })
        
        # 執行星座驗證
        validation_results, summary = validator.validate_satellite_constellation(
            satellites_data=satellites_dict,
            ue_position=ue_position
        )
        
        # 生成驗證報告
        validation_report = validator.generate_validation_report(
            validation_results, summary
        )
        
        # 轉換響應格式
        validation_responses = []
        for result in validation_results:
            validation_responses.append(
                DistanceValidationResponse(
                    satellite_name=result.satellite_name,
                    norad_id=result.norad_id,
                    elevation_deg=result.elevation_deg,
                    azimuth_deg=result.azimuth_deg,
                    sgp4_distance_km=result.sgp4_distance_km,
                    theoretical_distance_km=result.theoretical_distance_km,
                    distance_difference_km=result.distance_difference_km,
                    relative_error_percent=result.relative_error_percent,
                    validation_status=result.validation_status,
                    error_analysis=result.error_analysis,
                    timestamp=result.timestamp.isoformat()
                )
            )
        
        summary_response = ValidationSummaryResponse(
            total_satellites=summary.total_satellites,
            validation_passed=summary.validation_passed,
            validation_warnings=summary.validation_warnings,
            validation_failed=summary.validation_failed,
            mean_error_km=summary.mean_error_km,
            max_error_km=summary.max_error_km,
            min_error_km=summary.min_error_km,
            std_error_km=summary.std_error_km,
            high_elevation_accuracy=summary.high_elevation_accuracy,
            medium_elevation_accuracy=summary.medium_elevation_accuracy,
            low_elevation_accuracy=summary.low_elevation_accuracy
        )
        
        logger.info(
            "星座距離驗證完成",
            total_satellites=summary.total_satellites,
            passed=summary.validation_passed,
            warnings=summary.validation_warnings,
            failed=summary.validation_failed,
            mean_error_km=summary.mean_error_km
        )
        
        return ConstellationValidationResponse(
            validation_results=validation_responses,
            summary=summary_response,
            validation_report=validation_report,
            timestamp=datetime.utcnow().isoformat(),
            observer_location={
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt
            }
        )
        
    except Exception as e:
        logger.error("星座距離驗證失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")

@router.get(
    "/validation-standards",
    summary="獲取驗證標準",
    description="獲取距離驗證的標準和閾值"
)
async def get_validation_standards(
    validator: DistanceValidator = Depends(get_distance_validator)
):
    """獲取驗證標準"""
    return {
        "earth_radius_km": validator.EARTH_RADIUS_KM,
        "leo_altitude_km": validator.LEO_ALTITUDE_KM,
        "accuracy_threshold_percent": validator.ACCURACY_THRESHOLD_PERCENT,
        "warning_threshold_percent": validator.WARNING_THRESHOLD_PERCENT,
        "theoretical_formula": "d = √[R_e² + (R_e + h)² - 2·R_e·(R_e + h)·sin(ε)]",
        "formula_explanation": {
            "R_e": "地球半徑 (6371 km)",
            "h": "衛星軌道高度 (km)",
            "ε": "衛星仰角 (度)",
            "d": "理論斜距 (km)"
        },
        "validation_levels": {
            "PASS": f"相對誤差 ≤ {validator.WARNING_THRESHOLD_PERCENT}%",
            "WARNING": f"相對誤差 {validator.WARNING_THRESHOLD_PERCENT}% - {validator.ACCURACY_THRESHOLD_PERCENT}%", 
            "FAIL": f"相對誤差 > {validator.ACCURACY_THRESHOLD_PERCENT}%"
        }
    }

@router.get(
    "/health",
    summary="距離驗證服務健康檢查",
    description="檢查距離驗證服務的健康狀態"
)
async def health_check():
    """健康檢查"""
    try:
        # 測試理論公式計算
        validator = create_distance_validator()
        test_distance = validator.calculate_theoretical_slant_range(45.0, 550.0)
        
        return {
            "healthy": True,
            "service": "distance-validation",
            "timestamp": datetime.utcnow().isoformat(),
            "test_calculation": {
                "elevation_deg": 45.0,
                "theoretical_distance_km": test_distance
            },
            "endpoints": [
                "/api/v1/distance-validation/theoretical-distance",
                "/api/v1/distance-validation/validate-satellite",
                "/api/v1/distance-validation/validate-constellation",
                "/api/v1/distance-validation/validation-standards",
                "/api/v1/distance-validation/health"
            ]
        }
        
    except Exception as e:
        logger.error("距離驗證健康檢查失敗", error=str(e))
        raise HTTPException(status_code=503, detail=f"服務不可用: {str(e)}")