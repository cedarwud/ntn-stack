"""
Weather-Integrated Prediction API
天氣整合預測 API 端點
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import logging
import time

from ..services.weather_integrated_prediction_service import (
    WeatherIntegratedPredictionService,
    WeatherCondition
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handover/weather-prediction", tags=["Weather Prediction"])

# 全局服務實例
weather_prediction_service = WeatherIntegratedPredictionService()


# === API 數據模型 ===

class WeatherPredictionRequest(BaseModel):
    """天氣預測請求"""
    ue_id: str = Field(description="UE 設備 ID")
    ue_latitude: float = Field(description="UE 緯度")
    ue_longitude: float = Field(description="UE 經度") 
    ue_altitude: float = Field(default=0.0, description="UE 海拔高度 (米)")
    satellite_candidates: List[Dict[str, Any]] = Field(description="候選衛星列表")
    future_time_horizon_sec: int = Field(default=300, description="預測時間範圍 (秒)")


class WeatherConditionsResponse(BaseModel):
    """天氣條件響應"""
    success: bool
    weather_condition: str
    temperature_celsius: float
    humidity_percent: float
    precipitation_rate_mmh: float
    cloud_coverage_percent: float
    visibility_km: float
    atmospheric_impact: Dict[str, float]


class WeatherPredictionResponse(BaseModel):
    """天氣預測響應"""
    success: bool
    selected_satellite: Optional[Dict[str, Any]]
    atmospheric_conditions: Dict[str, float]
    prediction_confidence: float
    future_weather_outlook: Dict[str, Any]
    weather_impact_analysis: Dict[str, Any]
    timestamp: float


# === API 端點 ===

@router.get("/weather-conditions", response_model=WeatherConditionsResponse)
async def get_weather_conditions(
    latitude: float = Query(description="緯度"),
    longitude: float = Query(description="經度"),
    altitude: float = Query(default=0.0, description="海拔高度 (米)")
):
    """
    獲取指定位置的天氣條件
    """
    try:
        weather_data = await weather_prediction_service.get_weather_conditions(
            (latitude, longitude, altitude)
        )
        
        # 計算大氣影響
        atmospheric_loss = weather_prediction_service.calculate_atmospheric_loss(
            weather_data, 45.0  # 假設 45° 仰角
        )
        
        return WeatherConditionsResponse(
            success=True,
            weather_condition=weather_data.condition.value,
            temperature_celsius=weather_data.temperature_celsius,
            humidity_percent=weather_data.humidity_percent,
            precipitation_rate_mmh=weather_data.precipitation_rate_mmh,
            cloud_coverage_percent=weather_data.cloud_coverage_percent,
            visibility_km=weather_data.visibility_km,
            atmospheric_impact={
                "total_loss_db": atmospheric_loss.total_atmospheric_loss_db,
                "rain_attenuation_db": atmospheric_loss.rain_attenuation_db,
                "cloud_attenuation_db": atmospheric_loss.cloud_attenuation_db,
                "atmospheric_absorption_db": atmospheric_loss.atmospheric_absorption_db,
                "scintillation_db": atmospheric_loss.scintillation_db,
                "confidence_factor": atmospheric_loss.confidence_factor
            }
        )
        
    except Exception as e:
        logger.error(f"獲取天氣條件失敗: {e}")
        raise HTTPException(status_code=500, detail=f"天氣查詢失敗: {str(e)}")


@router.post("/predict", response_model=WeatherPredictionResponse)
async def predict_with_weather_integration(
    request: WeatherPredictionRequest,
    background_tasks: BackgroundTasks
):
    """
    執行天氣整合的衛星預測
    """
    try:
        start_time = time.time()
        logger.info(f"收到天氣整合預測請求 - UE: {request.ue_id}")
        
        # 執行天氣整合預測
        prediction_result = await weather_prediction_service.predict_with_weather_integration(
            ue_id=request.ue_id,
            ue_position=(request.ue_latitude, request.ue_longitude, request.ue_altitude),
            satellite_candidates=request.satellite_candidates,
            future_time_horizon_sec=request.future_time_horizon_sec
        )
        
        processing_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        if prediction_result['success']:
            # 添加處理時間信息
            prediction_result['processing_time_ms'] = processing_time
            
            # 在背景任務中記錄詳細日誌
            background_tasks.add_task(
                _log_weather_prediction_details,
                request.ue_id,
                prediction_result,
                processing_time
            )
            
            return WeatherPredictionResponse(
                success=True,
                selected_satellite=prediction_result['selected_satellite'],
                atmospheric_conditions=prediction_result['atmospheric_conditions'],
                prediction_confidence=prediction_result['prediction_confidence'],
                future_weather_outlook=prediction_result['future_weather_outlook'],
                weather_impact_analysis={
                    "processing_time_ms": processing_time,
                    "weather_adjustment_applied": True,
                    "satellite_candidates_count": len(request.satellite_candidates)
                },
                timestamp=prediction_result['timestamp']
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=prediction_result.get('error', '預測失敗')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"天氣整合預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測失敗: {str(e)}")


@router.get("/statistics")
async def get_weather_prediction_statistics():
    """
    獲取天氣預測統計信息
    """
    try:
        stats = weather_prediction_service.get_weather_prediction_statistics()
        
        # 添加額外的分析指標
        analysis = {
            "performance_metrics": {
                "prediction_efficiency": "high" if stats["total_predictions"] > 10 else "low",
                "confidence_level": "high" if stats["average_confidence"] > 0.8 else "medium",
                "cache_utilization": stats["cache_size"] / max(stats["total_predictions"], 1)
            },
            "weather_insights": {
                "dominant_conditions": _analyze_weather_distribution(stats["weather_distribution"]),
                "prediction_reliability": stats["average_confidence"],
                "system_stability": "stable" if stats["total_predictions"] > 0 else "initializing"
            }
        }
        
        return {
            "success": True,
            "statistics": stats,
            "analysis": analysis,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"獲取天氣預測統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計查詢失敗: {str(e)}")


@router.put("/weather-coefficients")
async def update_weather_coefficients(
    condition: str = Query(description="天氣條件"),
    rain_attenuation_factor: Optional[float] = Query(default=None, description="雨衰係數"),
    cloud_attenuation_factor: Optional[float] = Query(default=None, description="雲層衰減係數"),
    reliability_multiplier: Optional[float] = Query(default=None, description="可靠性乘數")
):
    """
    更新天氣影響係數
    """
    try:
        # 驗證天氣條件
        try:
            weather_condition = WeatherCondition(condition)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"無效的天氣條件: {condition}"
            )
        
        # 準備更新的係數
        coefficients = {}
        if rain_attenuation_factor is not None:
            coefficients["rain_attenuation_factor"] = rain_attenuation_factor
        if cloud_attenuation_factor is not None:
            coefficients["cloud_attenuation_factor"] = cloud_attenuation_factor
        if reliability_multiplier is not None:
            coefficients["reliability_multiplier"] = reliability_multiplier
        
        if not coefficients:
            raise HTTPException(status_code=400, detail="至少需要提供一個係數更新")
        
        # 更新係數
        weather_prediction_service.update_weather_coefficients(weather_condition, coefficients)
        
        return {
            "success": True,
            "message": f"天氣條件 {condition} 的係數已更新",
            "updated_coefficients": coefficients
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新天氣係數失敗: {e}")
        raise HTTPException(status_code=500, detail=f"係數更新失敗: {str(e)}")


@router.post("/weather-adjustment/toggle")
async def toggle_weather_adjustment(enabled: bool = Query(description="啟用天氣調整")):
    """
    啟用/禁用天氣調整
    """
    try:
        weather_prediction_service.enable_weather_adjustment(enabled)
        
        return {
            "success": True,
            "message": f"天氣調整已{'啟用' if enabled else '禁用'}",
            "weather_adjustment_enabled": enabled
        }
        
    except Exception as e:
        logger.error(f"天氣調整切換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"調整失敗: {str(e)}")


@router.post("/atmospheric-impact/analyze")
async def analyze_atmospheric_impact(
    latitude: float = Query(description="緯度"),
    longitude: float = Query(description="經度"),
    altitude: float = Query(default=0.0, description="海拔高度"),
    elevation_angles: List[float] = Query(description="仰角列表")
):
    """
    分析不同仰角下的大氣影響
    """
    try:
        # 獲取天氣條件
        weather_data = await weather_prediction_service.get_weather_conditions(
            (latitude, longitude, altitude)
        )
        
        # 分析不同仰角的影響
        impact_analysis = []
        for elevation in elevation_angles:
            if elevation < 5 or elevation > 90:
                continue  # 跳過無效仰角
                
            atmospheric_loss = weather_prediction_service.calculate_atmospheric_loss(
                weather_data, elevation
            )
            
            impact_analysis.append({
                "elevation_deg": elevation,
                "total_loss_db": atmospheric_loss.total_atmospheric_loss_db,
                "rain_attenuation_db": atmospheric_loss.rain_attenuation_db,
                "cloud_attenuation_db": atmospheric_loss.cloud_attenuation_db,
                "confidence_factor": atmospheric_loss.confidence_factor
            })
        
        return {
            "success": True,
            "weather_condition": weather_data.condition.value,
            "location": {"latitude": latitude, "longitude": longitude, "altitude": altitude},
            "atmospheric_impact_analysis": impact_analysis,
            "summary": {
                "min_total_loss_db": min(a["total_loss_db"] for a in impact_analysis) if impact_analysis else 0,
                "max_total_loss_db": max(a["total_loss_db"] for a in impact_analysis) if impact_analysis else 0,
                "optimal_elevation_deg": min(impact_analysis, key=lambda x: x["total_loss_db"])["elevation_deg"] if impact_analysis else 0
            }
        }
        
    except Exception as e:
        logger.error(f"大氣影響分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


# === 輔助函數 ===

async def _log_weather_prediction_details(
    ue_id: str, 
    prediction_result: Dict, 
    processing_time_ms: float
):
    """記錄天氣預測詳細信息（背景任務）"""
    selected = prediction_result.get('selected_satellite', {})
    confidence = prediction_result.get('prediction_confidence', 0.0)
    
    logger.info(
        f"天氣整合預測完成 - UE: {ue_id}, "
        f"衛星: {selected.get('satellite_id', 'unknown')}, "
        f"信心度: {confidence:.3f}, "
        f"處理時間: {processing_time_ms:.1f}ms"
    )


def _analyze_weather_distribution(weather_dist: Dict) -> str:
    """分析天氣分布"""
    if not weather_dist:
        return "no_data"
    
    total_count = sum(weather_dist.values())
    if total_count == 0:
        return "no_data"
    
    # 找出主要天氣條件
    dominant_weather = max(weather_dist, key=weather_dist.get)
    dominant_percentage = (weather_dist[dominant_weather] / total_count) * 100
    
    if dominant_percentage > 70:
        return f"predominantly_{dominant_weather}"
    elif dominant_percentage > 50:
        return f"mostly_{dominant_weather}"
    else:
        return "mixed_conditions"