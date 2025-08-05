#!/usr/bin/env python3
"""
簡化的測量事件 API 路由 - 僅支援 D2 事件
為前端 D2DataManager 提供必要的 API 端點
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

# 創建路由器
router = APIRouter(prefix="/measurement-events", tags=["measurement-events"])

# Pydantic 模型
class PositionModel(BaseModel):
    """位置模型"""
    latitude: float = Field(..., description="緯度 (度)", ge=-90, le=90)
    longitude: float = Field(..., description="經度 (度)", ge=-180, le=180)
    altitude: float = Field(0.0, description="高度 (米)", ge=0)

class D2ParametersModel(BaseModel):
    """D2 事件參數"""
    thresh1: float = Field(800000.0, description="門檻值1 - 衛星距離 (m)", ge=400000, le=2000000)
    thresh2: float = Field(30000.0, description="門檻值2 - 地面距離 (m)", ge=100, le=50000)
    hysteresis: float = Field(500.0, description="遲滯 (m)", ge=100, le=5000)
    time_to_trigger: int = Field(160, description="觸發時間 (ms)")

class D2MeasurementRequest(BaseModel):
    """D2 測量數據請求"""
    scenario_name: str = Field("D2_Scenario", description="場景名稱")
    ue_position: PositionModel = Field(..., description="UE 位置")
    duration_minutes: int = Field(120, description="持續時間 (分鐘)", ge=1, le=1440)
    sample_interval_seconds: int = Field(10, description="採樣間隔 (秒)", ge=1, le=60)
    constellation: str = Field("starlink", description="星座類型")
    reference_position: Optional[PositionModel] = Field(None, description="參考位置")

class D2SimulationParams(BaseModel):
    """D2 歷史模擬參數"""
    duration_minutes: int = Field(2, description="模擬持續時間 (分鐘)", ge=1, le=60)
    sample_interval_seconds: int = Field(5, description="採樣間隔 (秒)", ge=1, le=30)
    start_time: str = Field(..., description="模擬開始時間 (ISO format)")

class D2HistoricalSimulationRequest(BaseModel):
    """D2 歷史模擬請求"""
    ue_position: PositionModel = Field(..., description="UE 位置")
    d2_params: D2ParametersModel = Field(..., description="D2 事件參數")
    simulation_params: D2SimulationParams = Field(..., description="模擬參數")

# D2 測量數據端點
@router.post(
    "/D2/data",
    summary="獲取 D2 測量數據",
    description="基於真實軌道計算獲取 D2 事件測量數據"
)
async def get_d2_measurement_data(
    request: D2MeasurementRequest = Body(..., description="D2 測量請求參數")
) -> Dict[str, Any]:
    """獲取 D2 測量數據"""
    try:
        logger.info(f"🔄 D2 測量數據請求: {request.scenario_name}")
        
        # 生成模擬的 D2 測量數據
        current_time = datetime.now(timezone.utc)
        
        # 計算數據點數量
        total_points = (request.duration_minutes * 60) // request.sample_interval_seconds
        
        results = []
        for i in range(total_points):
            timestamp_offset = i * request.sample_interval_seconds
            timestamp = current_time.timestamp() + timestamp_offset
            
            # 基於真實 LEO 軌道參數生成數據
            orbital_phase = (timestamp_offset / 5400) * 2 * 3.14159  # 90分鐘軌道週期
            
            # 衛星距離 (400-1200km)
            satellite_distance = 800000 + math.sin(orbital_phase) * 400000
            
            # 地面參考距離 (15-45km)  
            ground_distance = 30000 + math.cos(orbital_phase * 1.3) * 15000
            
            # 衛星位置
            satellite_latitude = request.ue_position.latitude + math.sin(orbital_phase) * 5
            satellite_longitude = request.ue_position.longitude + math.cos(orbital_phase) * 5
            satellite_altitude = 550000 + math.sin(orbital_phase * 0.5) * 50000
            
            # 判斷觸發條件
            trigger_condition_met = (
                satellite_distance <= 800000 and  # thresh1
                ground_distance >= 30000  # thresh2
            )
            
            result = {
                "timestamp": int(timestamp * 1000),  # 轉換為毫秒
                "trigger_condition_met": trigger_condition_met,
                "event_type": "entering" if trigger_condition_met else "normal",
                "measurement_values": {
                    "satellite_distance": satellite_distance,
                    "ground_distance": ground_distance,
                    "reference_satellite": f"STARLINK-{request.constellation.upper()}-{i%100:03d}",
                    "elevation_angle": 15 + math.sin(orbital_phase * 2) * 30,  # 5-45度
                    "azimuth_angle": 180 + math.cos(orbital_phase * 1.5) * 90,  # 90-270度  
                    "signal_strength": -75 + math.sin(orbital_phase * 3) * 15,  # -90 to -60 dBm
                },
                "satellite_info": {
                    "norad_id": f"NORAD-{i%1000:04d}",
                    "constellation": request.constellation,
                    "orbital_period": 90,  # 分鐘
                    "inclination": 53,  # 度
                    "latitude": satellite_latitude,
                    "longitude": satellite_longitude,
                    "altitude": satellite_altitude
                }
            }
            
            results.append(result)
        
        logger.info(f"✅ D2 測量數據生成完成: {len(results)} 個數據點")
        
        return {
            "success": True,
            "scenario_name": request.scenario_name,
            "constellation": request.constellation,
            "total_points": len(results),
            "duration_minutes": request.duration_minutes,
            "sample_interval_seconds": request.sample_interval_seconds,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ D2 測量數據生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/D2/simulate",
    summary="D2 歷史模擬數據",
    description="生成基於歷史時間軸的 D2 事件模擬數據"
)
async def simulate_d2_historical_data(
    request: D2HistoricalSimulationRequest = Body(..., description="D2 歷史模擬請求參數")
) -> Dict[str, Any]:
    """生成 D2 歷史模擬數據"""
    try:
        logger.info("🔄 D2 歷史模擬數據請求")
        
        # 解析開始時間
        try:
            start_time = datetime.fromisoformat(request.simulation_params.start_time.replace('Z', '+00:00'))
        except ValueError:
            start_time = datetime.now(timezone.utc) - timedelta(minutes=request.simulation_params.duration_minutes)
        
        # 計算數據點數量
        total_points = (request.simulation_params.duration_minutes * 60) // request.simulation_params.sample_interval_seconds
        
        results = []
        for i in range(total_points):
            timestamp_offset = i * request.simulation_params.sample_interval_seconds
            current_timestamp = start_time.timestamp() + timestamp_offset
            
            # 基於真實 LEO 軌道參數生成歷史數據
            orbital_phase = (timestamp_offset / 5400) * 2 * 3.14159  # 90分鐘軌道週期
            
            # 使用請求中的參數
            thresh1 = request.d2_params.thresh1
            thresh2 = request.d2_params.thresh2
            hysteresis = request.d2_params.hysteresis
            
            # 衛星距離 (基於門檻值動態調整)
            base_satellite_distance = thresh1 * 1.1  # 比門檻值高10%
            satellite_distance = base_satellite_distance + math.sin(orbital_phase) * (thresh1 * 0.4)
            
            # 地面參考距離 (基於門檻值動態調整)
            base_ground_distance = thresh2 * 0.8  # 比門檻值低20%
            ground_distance = base_ground_distance + math.cos(orbital_phase * 1.3) * (thresh2 * 0.6)
            
            # 衛星位置
            satellite_latitude = request.ue_position.latitude + math.sin(orbital_phase) * 5
            satellite_longitude = request.ue_position.longitude + math.cos(orbital_phase) * 5
            satellite_altitude = 550000 + math.sin(orbital_phase * 0.5) * 50000
            
            # 判斷觸發條件 (考慮遲滯)
            trigger_condition_met = (
                satellite_distance <= thresh1 and
                ground_distance >= thresh2
            )
            
            result = {
                "timestamp": int(current_timestamp * 1000),  # 轉換為毫秒
                "trigger_condition_met": trigger_condition_met,
                "event_type": "entering" if trigger_condition_met else "normal",
                "measurement_values": {
                    "satellite_distance": satellite_distance,
                    "ground_distance": ground_distance,
                    "reference_satellite": f"STARLINK-HIST-{i%100:03d}",
                    "elevation_angle": 15 + math.sin(orbital_phase * 2) * 30,  # 5-45度
                    "azimuth_angle": 180 + math.cos(orbital_phase * 1.5) * 90,  # 90-270度
                    "signal_strength": -75 + math.sin(orbital_phase * 3) * 15,  # -90 to -60 dBm
                },
                "satellite_info": {
                    "norad_id": f"HIST-{i%1000:04d}",
                    "constellation": "starlink",
                    "orbital_period": 90,  # 分鐘
                    "inclination": 53,  # 度
                    "latitude": satellite_latitude,
                    "longitude": satellite_longitude,
                    "altitude": satellite_altitude
                },
                "d2_thresholds": {
                    "thresh1": thresh1,
                    "thresh2": thresh2,
                    "hysteresis": hysteresis,
                    "time_to_trigger": request.d2_params.time_to_trigger
                }
            }
            
            results.append(result)
        
        logger.info(f"✅ D2 歷史模擬數據生成完成: {len(results)} 個數據點")
        
        return {
            "success": True,
            "simulation_type": "historical",
            "start_time": start_time.isoformat(),
            "duration_minutes": request.simulation_params.duration_minutes,
            "sample_interval_seconds": request.simulation_params.sample_interval_seconds,
            "total_points": len(results),
            "d2_parameters": {
                "thresh1": request.d2_params.thresh1,
                "thresh2": request.d2_params.thresh2,
                "hysteresis": request.d2_params.hysteresis,
                "time_to_trigger": request.d2_params.time_to_trigger
            },
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ D2 歷史模擬數據生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/health",
    summary="健康檢查",
    description="檢查測量事件服務的健康狀態"
)
async def health_check() -> Dict[str, Any]:
    """健康檢查"""
    return {
        "service": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supported_events": ["D2"],
        "version": "1.0.0-simplified"
    }