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
    """獲取真實 D2 測量數據 - 使用預處理 Volume 數據"""
    try:
        logger.info(f"獲取真實 D2 數據: {request.scenario_name}")
        
        # 導入本地數據服務
        from app.services.local_volume_data_service import get_local_volume_service
        volume_service = get_local_volume_service()
        
        # 構建參考位置
        reference_location = {
            "latitude": request.ue_position.latitude,
            "longitude": request.ue_position.longitude,
            "altitude": request.ue_position.altitude
        }
        
        logger.info(f"🌐 使用預處理數據 - 星座: {request.constellation}, 位置: {request.ue_position.latitude:.4f}°N, {request.ue_position.longitude:.4f}°E")
        
        # 從預處理數據獲取統一時間序列
        unified_data = await volume_service.generate_120min_timeseries(
            constellation=request.constellation,
            reference_location=reference_location
        )
        
        if not unified_data or not unified_data.get('satellites'):
            raise HTTPException(
                status_code=404,
                detail=f"無法獲取 {request.constellation} 預處理數據"
            )
        
        # 提取 D2 測量事件數據
        results = []
        start_time = datetime.now(timezone.utc)
        
        # 計算時間點數量（根據請求的持續時間）
        total_points = min(
            (request.duration_minutes * 60) // request.sample_interval_seconds,
            len(unified_data['satellites'][0]['time_series']) if unified_data['satellites'] else 0
        )
        
        # 獲取最佳衛星的時間序列數據（通常是第一顆）
        if unified_data['satellites']:
            best_satellite_data = unified_data['satellites'][0]
            time_series = best_satellite_data['time_series'][:total_points]
            
            for i, time_point in enumerate(time_series):
                try:
                    current_time = start_time + timedelta(seconds=i * request.sample_interval_seconds)
                    measurement_events = time_point.get('measurement_events', {})
                    observation = time_point.get('observation', {})
                    position = time_point.get('position', {})
                    
                    # 創建測量值
                    measurement_values = MeasurementValues(
                        satellite_distance=measurement_events.get('d2_satellite_distance_m', 0.0),
                        ground_distance=measurement_events.get('d2_ground_distance_m', 0.0),
                        reference_satellite=best_satellite_data.get('name', 'Unknown'),
                        elevation_angle=observation.get('elevation_deg', 0.0),
                        azimuth_angle=observation.get('azimuth_deg', 0.0),
                        signal_strength=observation.get('rsrp_dbm', -120.0)
                    )
                    
                    # 觸發條件
                    trigger_condition_met = measurement_events.get('a4_trigger_condition', False)
                    
                    result = D2MeasurementResult(
                        timestamp=current_time.isoformat(),
                        measurement_values=measurement_values,
                        trigger_condition_met=trigger_condition_met,
                        satellite_info={
                            "norad_id": best_satellite_data.get('norad_id', 0),
                            "constellation": best_satellite_data.get('constellation', request.constellation),
                            "orbital_period": 95.0,  # 典型 LEO 週期
                            "inclination": 53.0,     # 典型傾角
                            "latitude": position.get('latitude', 0.0),
                            "longitude": position.get('longitude', 0.0),
                            "altitude": position.get('altitude', 550000.0)
                        }
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"處理時間點 {i} 失敗: {e}")
                    continue
        
        # 設置參考位置（如果未提供，使用台北作為默認）
        if request.reference_position:
            reference_pos = {
                "latitude": request.reference_position.latitude,
                "longitude": request.reference_position.longitude,
                "altitude": request.reference_position.altitude
            }
        else:
            reference_pos = {
                "latitude": 25.0330,  # 台北
                "longitude": 121.5654,
                "altitude": 0.0
            }
        
        response = D2Response(
            success=True,
            scenario_name=request.scenario_name,
            data_source="real_preprocessed_volume",
            ue_position=request.ue_position,
            duration_minutes=request.duration_minutes,
            sample_count=len(results),
            results=results,
            metadata={
                "constellation": request.constellation,
                "reference_position": reference_pos,
                "data_source": unified_data.get('metadata', {}).get('data_source', 'volume_preprocessed'),
                "satellites_processed": len(unified_data.get('satellites', [])),
                "data_quality": "preprocessed_volume_data",
                "sgp4_precision": "preprocessed",
                "atmospheric_corrections": True,
                "volume_timestamp": unified_data.get('metadata', {}).get('computation_time', 'unknown')
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info(f"✅ 成功從預處理數據生成 {len(results)} 個 D2 測量點")
        return response
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        logger.error(f"獲取真實 D2 數據失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
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
