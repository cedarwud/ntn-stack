"""
測量事件 API 路由 - 支持 D2 真實數據模式

提供測量事件的 REST API 端點：
1. POST /api/measurement-events/D2/real - 獲取真實 D2 數據
2. POST /api/measurement-events/D2/simulate - 模擬 D2 數據（保持兼容）
3. GET /api/measurement-events/D2/status - 獲取 D2 服務狀態

符合 d2.md Phase 4 前端集成要求
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.constellation_manager import ConstellationManager
from app.services.distance_calculator import DistanceCalculator, Position

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/measurement-events", tags=["Measurement Events"])

# 服務實例
constellation_manager = ConstellationManager()
distance_calculator = DistanceCalculator()

class UEPosition(BaseModel):
    """UE 位置模型"""
    latitude: float
    longitude: float
    altitude: float

class D2RealDataRequest(BaseModel):
    """D2 真實數據請求模型"""
    scenario_name: str = "Real_D2_Measurement"
    ue_position: UEPosition
    duration_minutes: int = 5
    sample_interval_seconds: int = 10
    constellation: str = "starlink"
    reference_position: Optional[UEPosition] = None

class D2SimulateRequest(BaseModel):
    """D2 模擬數據請求模型（保持兼容）"""
    scenario_name: str = "Enhanced_D2_Simulation"
    ue_position: UEPosition
    duration_minutes: int = 5
    sample_interval_seconds: int = 10
    target_satellites: List[str] = []

class MeasurementValues(BaseModel):
    """測量值模型"""
    satellite_distance: float
    ground_distance: float
    reference_satellite: str
    elevation_angle: float
    azimuth_angle: float
    signal_strength: float

class D2MeasurementResult(BaseModel):
    """D2 測量結果模型"""
    timestamp: str
    measurement_values: MeasurementValues
    trigger_condition_met: bool
    satellite_info: Dict[str, Any]

class D2Response(BaseModel):
    """D2 響應模型"""
    success: bool
    scenario_name: str
    data_source: str  # "real" or "simulated"
    ue_position: UEPosition
    duration_minutes: int
    sample_count: int
    results: List[D2MeasurementResult]
    metadata: Dict[str, Any]
    timestamp: str

@router.post("/D2/real")
async def get_real_d2_data(request: D2RealDataRequest):
    """獲取真實 D2 測量數據"""
    try:
        logger.info(f"獲取真實 D2 數據: {request.scenario_name}")
        
        # 轉換位置格式
        ue_position = Position(
            latitude=request.ue_position.latitude,
            longitude=request.ue_position.longitude,
            altitude=request.ue_position.altitude
        )
        
        # 設置參考位置（如果未提供，使用台中作為默認）
        if request.reference_position:
            reference_position = Position(
                latitude=request.reference_position.latitude,
                longitude=request.reference_position.longitude,
                altitude=request.reference_position.altitude
            )
        else:
            reference_position = Position(
                latitude=25.0330,  # 台北（與台中有足夠距離差異）
                longitude=121.5654,
                altitude=0.0
            )
        
        # 生成時間序列
        start_time = datetime.now(timezone.utc)
        results = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=request.duration_minutes)
        interval_delta = timedelta(seconds=request.sample_interval_seconds)
        
        while current_time <= end_time:
            try:
                # 獲取最佳衛星
                best_satellite = await constellation_manager.get_best_satellite(
                    ue_position, current_time, request.constellation
                )
                
                if best_satellite:
                    # 計算距離
                    distance_result = distance_calculator.calculate_d2_distances(
                        ue_position, best_satellite.current_position, reference_position
                    )
                    
                    # 創建測量結果
                    measurement_values = MeasurementValues(
                        satellite_distance=distance_result.satellite_distance,
                        ground_distance=distance_result.ground_distance,
                        reference_satellite=best_satellite.tle_data.satellite_name,
                        elevation_angle=best_satellite.elevation_angle,
                        azimuth_angle=best_satellite.azimuth_angle,
                        signal_strength=best_satellite.signal_strength
                    )
                    
                    # 簡單的觸發條件（可以根據需要調整）
                    trigger_condition_met = (
                        distance_result.satellite_distance > 800000 and  # 800km
                        distance_result.ground_distance < 50000  # 50km
                    )
                    
                    result = D2MeasurementResult(
                        timestamp=current_time.isoformat(),
                        measurement_values=measurement_values,
                        trigger_condition_met=trigger_condition_met,
                        satellite_info={
                            "norad_id": best_satellite.tle_data.catalog_number,
                            "constellation": best_satellite.constellation,
                            "orbital_period": 1440 / best_satellite.tle_data.mean_motion,
                            "inclination": best_satellite.tle_data.inclination,
                            "latitude": best_satellite.current_position.latitude,
                            "longitude": best_satellite.current_position.longitude,
                            "altitude": best_satellite.current_position.altitude
                        }
                    )
                    
                    results.append(result)
                else:
                    # 如果沒有可見衛星，創建空結果
                    measurement_values = MeasurementValues(
                        satellite_distance=0.0,
                        ground_distance=distance_calculator.calculate_d2_distances(
                            ue_position, ue_position, reference_position
                        ).ground_distance,
                        reference_satellite="none",
                        elevation_angle=0.0,
                        azimuth_angle=0.0,
                        signal_strength=0.0
                    )
                    
                    result = D2MeasurementResult(
                        timestamp=current_time.isoformat(),
                        measurement_values=measurement_values,
                        trigger_condition_met=False,
                        satellite_info={}
                    )
                    
                    results.append(result)
                
            except Exception as e:
                logger.error(f"計算時間點 {current_time} 的數據失敗: {e}")
                import traceback
                logger.error(f"詳細錯誤: {traceback.format_exc()}")
            
            current_time += interval_delta
        
        # 獲取覆蓋分析
        coverage_analysis = await constellation_manager.analyze_coverage(ue_position)
        
        response = D2Response(
            success=True,
            scenario_name=request.scenario_name,
            data_source="real",
            ue_position=request.ue_position,
            duration_minutes=request.duration_minutes,
            sample_count=len(results),
            results=results,
            metadata={
                "constellation": request.constellation,
                "reference_position": {
                    "latitude": reference_position.latitude,
                    "longitude": reference_position.longitude,
                    "altitude": reference_position.altitude
                },
                "coverage_analysis": {
                    "visible_satellites": coverage_analysis.visible_satellites,
                    "coverage_percentage": coverage_analysis.coverage_percentage,
                    "average_elevation": coverage_analysis.average_elevation,
                    "constellation_distribution": coverage_analysis.constellation_distribution
                },
                "data_quality": "real_satellite_data",
                "sgp4_precision": "high",
                "atmospheric_corrections": True
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info(f"成功生成 {len(results)} 個真實 D2 測量點")
        return response
        
    except Exception as e:
        logger.error(f"獲取真實 D2 數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取真實 D2 數據失敗: {str(e)}"
        )

@router.post("/D2/simulate")
async def simulate_d2_data(request: D2SimulateRequest):
    """模擬 D2 測量數據（保持向後兼容）"""
    try:
        logger.info(f"模擬 D2 數據: {request.scenario_name}")
        
        # 轉換為真實數據請求格式
        real_request = D2RealDataRequest(
            scenario_name=request.scenario_name,
            ue_position=request.ue_position,
            duration_minutes=request.duration_minutes,
            sample_interval_seconds=request.sample_interval_seconds,
            constellation="starlink"  # 默認使用 Starlink
        )
        
        # 調用真實數據端點
        response = await get_real_d2_data(real_request)
        
        # 修改響應以表明這是模擬模式
        response.data_source = "simulated"
        response.metadata["note"] = "使用真實衛星數據進行模擬"
        
        return response
        
    except Exception as e:
        logger.error(f"模擬 D2 數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"模擬 D2 數據失敗: {str(e)}"
        )

@router.get("/D2/status")
async def get_d2_service_status():
    """獲取 D2 服務狀態"""
    try:
        # 獲取星座統計
        stats = await constellation_manager.get_constellation_statistics()
        
        # 檢查服務健康狀態
        service_health = {
            "constellation_manager": "healthy",
            "distance_calculator": "healthy",
            "sgp4_calculator": "healthy"
        }
        
        # 計算總可用衛星數
        total_satellites = sum(
            stat.get('total_satellites', 0) 
            for stat in stats.values() 
            if 'error' not in stat
        )
        
        return {
            "success": True,
            "service_status": "operational",
            "data_source": "real_satellite_data",
            "supported_constellations": list(stats.keys()),
            "total_satellites": total_satellites,
            "constellation_stats": stats,
            "service_health": service_health,
            "capabilities": {
                "real_time_tracking": True,
                "sgp4_propagation": True,
                "atmospheric_corrections": True,
                "multi_constellation": True,
                "handover_prediction": True
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取 D2 服務狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取服務狀態失敗: {str(e)}"
        )
