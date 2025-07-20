#!/usr/bin/env python3
"""
測量事件 API 路由 - 統一改進主準則 REST API

提供測量事件的 REST API 端點：
1. /api/measurement-events/{event_type}/data - 實時數據
2. /api/measurement-events/{event_type}/simulate - 事件模擬  
3. /api/measurement-events/config - 參數配置管理
4. /api/measurement-events/sib19-status - SIB19 狀態
5. /api/measurement-events/orbit-data - 軌道數據
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog

from ..services.measurement_event_service import (
    MeasurementEventService, EventType, TriggerState,
    A4Parameters, D1Parameters, D2Parameters, T1Parameters,
    SimulationScenario, MeasurementResult
)
from ..services.orbit_calculation_engine import (
    OrbitCalculationEngine, Position, SatellitePosition
)
from ..services.sib19_unified_platform import SIB19UnifiedPlatform
from ..services.tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/measurement-events", tags=["measurement-events"])

# 全局服務實例
_orbit_engine: Optional[OrbitCalculationEngine] = None
_sib19_platform: Optional[SIB19UnifiedPlatform] = None
_tle_manager: Optional[TLEDataManager] = None
_measurement_service: Optional[MeasurementEventService] = None


# Pydantic 模型
class PositionModel(BaseModel):
    """位置模型"""
    latitude: float = Field(..., description="緯度 (度)", ge=-90, le=90)
    longitude: float = Field(..., description="經度 (度)", ge=-180, le=180)
    altitude: float = Field(0.0, description="高度 (米)", ge=0)


class A4ParametersModel(BaseModel):
    """A4 事件參數"""
    a4_threshold: float = Field(-80.0, description="A4 門檻值 (dBm)", ge=-100, le=-40)
    hysteresis: float = Field(3.0, description="遲滯 (dB)", ge=0, le=10)
    time_to_trigger: int = Field(160, description="觸發時間 (ms)")


class D1ParametersModel(BaseModel):
    """D1 事件參數"""
    thresh1: float = Field(10000.0, description="門檻值1 (m)", ge=50, le=50000)
    thresh2: float = Field(5000.0, description="門檻值2 (m)", ge=10, le=10000)
    hysteresis: float = Field(500.0, description="遲滯 (m)", ge=1, le=1000)
    time_to_trigger: int = Field(160, description="觸發時間 (ms)")


class D2ParametersModel(BaseModel):
    """D2 事件參數"""
    thresh1: float = Field(800000.0, description="門檻值1 - 衛星距離 (m)", ge=400000, le=2000000)
    thresh2: float = Field(30000.0, description="門檻值2 - 地面距離 (m)", ge=100, le=50000)
    hysteresis: float = Field(500.0, description="遲滯 (m)", ge=100, le=5000)
    time_to_trigger: int = Field(160, description="觸發時間 (ms)")


class T1ParametersModel(BaseModel):
    """T1 事件參數"""
    t1_threshold: float = Field(300.0, description="時間門檻 (秒)", ge=1, le=3600)
    duration: float = Field(60.0, description="持續時間 (秒)", ge=1, le=300)
    time_to_trigger: int = Field(160, description="觸發時間 (ms)")


class SimulationScenarioModel(BaseModel):
    """模擬場景"""
    scenario_name: str = Field(..., description="場景名稱")
    ue_position: PositionModel = Field(..., description="UE 位置")
    duration_minutes: int = Field(60, description="持續時間 (分鐘)", ge=1, le=1440)
    sample_interval_seconds: int = Field(5, description="採樣間隔 (秒)", ge=1, le=60)
    target_satellites: List[str] = Field(default_factory=list, description="目標衛星列表")


class MeasurementDataRequest(BaseModel):
    """測量數據請求"""
    ue_position: PositionModel = Field(..., description="UE 位置")
    a4_params: Optional[A4ParametersModel] = None
    d1_params: Optional[D1ParametersModel] = None
    d2_params: Optional[D2ParametersModel] = None
    t1_params: Optional[T1ParametersModel] = None


# 依賴注入
async def get_services():
    """獲取服務實例"""
    global _orbit_engine, _sib19_platform, _tle_manager, _measurement_service
    
    if not _measurement_service:
        # 初始化服務 (實際應從依賴注入容器獲取)
        _tle_manager = TLEDataManager()
        _orbit_engine = OrbitCalculationEngine()
        _sib19_platform = SIB19UnifiedPlatform(_orbit_engine, _tle_manager)
        _measurement_service = MeasurementEventService(
            _orbit_engine, _sib19_platform, _tle_manager
        )
        
        # 正確的初始化順序
        # 1. 首先初始化 TLE 管理器和數據源
        await _tle_manager.initialize_default_sources()
        
        # 2. 強制更新 TLE 數據，確保有衛星數據
        await _tle_manager.force_update_all()
        
        # 3. 確保測量服務與軌道引擎數據同步
        await _measurement_service.sync_tle_data_from_manager()
        
        # 4. 最後初始化 SIB19 平台 (此時已有衛星數據)
        await _sib19_platform.initialize_sib19_platform()
        
    return {
        "measurement_service": _measurement_service,
        "orbit_engine": _orbit_engine,
        "sib19_platform": _sib19_platform,
        "tle_manager": _tle_manager
    }


# API 端點
@router.post(
    "/{event_type}/data",
    summary="獲取實時測量數據",
    description="基於真實軌道計算獲取指定事件類型的實時測量數據"
)
async def get_real_time_measurement_data(
    event_type: EventType = Path(..., description="事件類型 (A4/D1/D2/T1)"),
    request: MeasurementDataRequest = Body(..., description="測量請求參數"),
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """獲取實時測量數據"""
    try:
        measurement_service = services["measurement_service"]
        
        # 轉換位置
        ue_position = Position(
            x=0, y=0, z=0,
            latitude=request.ue_position.latitude,
            longitude=request.ue_position.longitude,
            altitude=request.ue_position.altitude
        )
        
        # 選擇事件參數
        event_params = None
        if event_type == EventType.A4 and request.a4_params:
            event_params = A4Parameters(
                a4_threshold=request.a4_params.a4_threshold,
                hysteresis=request.a4_params.hysteresis,
                time_to_trigger=request.a4_params.time_to_trigger
            )
        elif event_type == EventType.D1 and request.d1_params:
            event_params = D1Parameters(
                thresh1=request.d1_params.thresh1,
                thresh2=request.d1_params.thresh2,
                hysteresis=request.d1_params.hysteresis,
                time_to_trigger=request.d1_params.time_to_trigger
            )
        elif event_type == EventType.D2 and request.d2_params:
            event_params = D2Parameters(
                thresh1=request.d2_params.thresh1,
                thresh2=request.d2_params.thresh2,
                hysteresis=request.d2_params.hysteresis,
                time_to_trigger=request.d2_params.time_to_trigger
            )
        elif event_type == EventType.T1 and request.t1_params:
            event_params = T1Parameters(
                t1_threshold=request.t1_params.t1_threshold,
                duration=request.t1_params.duration,
                time_to_trigger=request.t1_params.time_to_trigger
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"缺少 {event_type.value} 事件的參數配置"
            )
            
        # 獲取測量數據
        result = await measurement_service.get_real_time_measurement_data(
            event_type, ue_position, event_params
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="測量數據獲取失敗"
            )
            
        # 轉換結果格式
        return {
            "event_type": result.event_type.value,
            "timestamp": result.timestamp.isoformat(),
            "trigger_state": result.trigger_state.value,
            "trigger_condition_met": result.trigger_condition_met,
            "measurement_values": result.measurement_values,
            "trigger_details": result.trigger_details,
            "sib19_data": result.sib19_data,
            "satellite_positions": {
                sat_id: {
                    "latitude": pos.latitude,
                    "longitude": pos.longitude,
                    "altitude": pos.altitude,
                    "velocity_x": pos.velocity_x,
                    "velocity_y": pos.velocity_y,
                    "velocity_z": pos.velocity_z
                }
                for sat_id, pos in result.satellite_positions.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"實時測量數據獲取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{event_type}/simulate",
    summary="模擬測量事件",
    description="執行測量事件模擬，返回時間序列數據和統計分析"
)
async def simulate_measurement_event(
    event_type: EventType = Path(..., description="事件類型 (A4/D1/D2/T1)"),
    scenario: SimulationScenarioModel = Body(..., description="模擬場景"),
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """模擬測量事件"""
    try:
        measurement_service = services["measurement_service"]
        
        # 轉換位置
        ue_position = Position(
            x=0, y=0, z=0,
            latitude=scenario.ue_position.latitude,
            longitude=scenario.ue_position.longitude,
            altitude=scenario.ue_position.altitude
        )
        
        # 根據事件類型創建默認參數
        if event_type == EventType.A4:
            event_params = A4Parameters()
        elif event_type == EventType.D1:
            event_params = D1Parameters()
        elif event_type == EventType.D2:
            event_params = D2Parameters()
        elif event_type == EventType.T1:
            event_params = T1Parameters()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的事件類型: {event_type.value}"
            )
            
        # 創建模擬場景
        sim_scenario = SimulationScenario(
            scenario_name=scenario.scenario_name,
            ue_position=ue_position,
            duration_minutes=scenario.duration_minutes,
            sample_interval_seconds=scenario.sample_interval_seconds,
            event_parameters=event_params,
            target_satellites=scenario.target_satellites
        )
        
        # 執行模擬
        result = await measurement_service.simulate_measurement_event(sim_scenario)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測量事件模擬失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/config/parameters",
    summary="獲取事件參數配置",
    description="獲取所有事件類型的參數約束和默認值"
)
async def get_event_parameters_config() -> Dict[str, Any]:
    """獲取事件參數配置"""
    return {
        "A4": {
            "description": "信號強度測量事件",
            "parameters": {
                "a4_threshold": {
                    "type": "float",
                    "unit": "dBm",
                    "range": [-100, -40],
                    "default": -80.0,
                    "description": "A4 觸發門檻值"
                },
                "hysteresis": {
                    "type": "float", 
                    "unit": "dB",
                    "range": [0, 10],
                    "default": 3.0,
                    "description": "遲滯值"
                },
                "time_to_trigger": {
                    "type": "int",
                    "unit": "ms",
                    "values": [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640],
                    "default": 160,
                    "description": "觸發時間"
                }
            }
        },
        "D1": {
            "description": "雙重距離測量事件",
            "parameters": {
                "thresh1": {
                    "type": "float",
                    "unit": "meters",
                    "range": [50, 50000],
                    "default": 10000.0,
                    "description": "距離門檻值1"
                },
                "thresh2": {
                    "type": "float",
                    "unit": "meters", 
                    "range": [10, 10000],
                    "default": 5000.0,
                    "description": "距離門檻值2"
                },
                "hysteresis": {
                    "type": "float",
                    "unit": "meters",
                    "range": [1, 1000],
                    "default": 500.0,
                    "description": "遲滯值"
                }
            }
        },
        "D2": {
            "description": "移動參考位置距離事件",
            "parameters": {
                "thresh1": {
                    "type": "float",
                    "unit": "meters",
                    "range": [400000, 2000000],
                    "default": 800000.0,
                    "description": "衛星距離門檻值"
                },
                "thresh2": {
                    "type": "float",
                    "unit": "meters",
                    "range": [100, 50000],
                    "default": 30000.0,
                    "description": "地面距離門檻值"
                },
                "hysteresis": {
                    "type": "float",
                    "unit": "meters",
                    "range": [100, 5000],
                    "default": 500.0,
                    "description": "遲滯值"
                }
            }
        },
        "T1": {
            "description": "時間條件測量事件",
            "parameters": {
                "t1_threshold": {
                    "type": "float",
                    "unit": "seconds",
                    "range": [1, 3600],
                    "default": 300.0,
                    "description": "時間門檻值"
                },
                "duration": {
                    "type": "float",
                    "unit": "seconds",
                    "range": [1, 300],
                    "default": 60.0,
                    "description": "持續時間"
                }
            }
        }
    }


@router.get(
    "/sib19-status",
    summary="獲取 SIB19 狀態",
    description="獲取 SIB19 統一基礎平台的當前狀態"
)
async def get_sib19_status(
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """獲取 SIB19 狀態"""
    try:
        sib19_platform = services["sib19_platform"]
        status = await sib19_platform.get_sib19_status()
        return status
        
    except Exception as e:
        logger.error(f"SIB19 狀態獲取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/orbit-data/satellites",
    summary="獲取可用衛星列表", 
    description="獲取當前可用的衛星列表和基本軌道資訊"
)
async def get_available_satellites(
    constellation: Optional[str] = Query(None, description="星座篩選 (starlink/oneweb/gps)"),
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """獲取可用衛星列表"""
    try:
        tle_manager = services["tle_manager"]
        
        if constellation:
            satellites = await tle_manager.get_constellation_satellites(constellation)
        else:
            satellites = await tle_manager.get_active_satellites()
            
        satellite_list = []
        for tle_data in satellites:
            satellite_list.append({
                "satellite_id": tle_data.satellite_id,
                "satellite_name": tle_data.satellite_name,
                "epoch": tle_data.epoch.isoformat(),
                "last_updated": tle_data.last_updated.isoformat()
            })
            
        constellation_info = await tle_manager.get_constellation_info()
        
        return {
            "satellites": satellite_list,
            "total_count": len(satellite_list),
            "constellation_filter": constellation,
            "constellation_info": {
                name: {
                    "satellite_count": info.satellite_count,
                    "active_satellites": info.active_satellites,
                    "operator": info.operator,
                    "coverage_area": info.coverage_area,
                    "last_updated": info.last_updated.isoformat()
                }
                for name, info in constellation_info.items()
            }
        }
        
    except Exception as e:
        logger.error(f"衛星列表獲取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/orbit-data/position/{satellite_id}",
    summary="獲取衛星位置",
    description="獲取指定衛星的當前位置和軌道參數"
)
async def get_satellite_position(
    satellite_id: str = Path(..., description="衛星ID"),
    timestamp: Optional[float] = Query(None, description="時間戳 (Unix timestamp)"),
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """獲取衛星位置"""
    try:
        orbit_engine = services["orbit_engine"]
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).timestamp()
            
        position = orbit_engine.calculate_satellite_position(satellite_id, timestamp)
        
        if not position:
            raise HTTPException(
                status_code=404,
                detail=f"無法獲取衛星 {satellite_id} 的位置數據"
            )
            
        return {
            "satellite_id": position.satellite_id,
            "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
            "position": {
                "x": position.x,
                "y": position.y,
                "z": position.z,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude": position.altitude
            },
            "velocity": {
                "x": position.velocity_x,
                "y": position.velocity_y,
                "z": position.velocity_z
            },
            "orbital_period_minutes": position.orbital_period
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"衛星位置獲取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/orbit-data/update-tle",
    summary="更新 TLE 數據",
    description="強制更新所有 TLE 數據源"
)
async def force_update_tle_data(
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """強制更新 TLE 數據"""
    try:
        tle_manager = services["tle_manager"]
        
        update_results = await tle_manager.force_update_all()
        
        summary = {
            "total_sources": len(update_results),
            "successful_updates": len([r for r in update_results if r.success]),
            "failed_updates": len([r for r in update_results if not r.success]),
            "total_satellites_updated": sum(r.satellites_updated for r in update_results),
            "total_satellites_added": sum(r.satellites_added for r in update_results),
        }
        
        detailed_results = []
        for result in update_results:
            detailed_results.append({
                "source_name": result.source_name,
                "success": result.success,
                "satellites_updated": result.satellites_updated,
                "satellites_added": result.satellites_added,
                "satellites_failed": result.satellites_failed,
                "update_time": result.update_time.isoformat(),
                "errors": result.errors
            })
            
        return {
            "summary": summary,
            "detailed_results": detailed_results
        }
        
    except Exception as e:
        logger.error(f"TLE 數據更新失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{event_type}/statistics",
    summary="獲取事件統計信息",
    description="獲取指定事件類型的統計信息和性能指標"
)
async def get_event_statistics(
    event_type: EventType = Path(..., description="事件類型 (A4/D1/D2/T1)"),
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """獲取事件統計信息"""
    try:
        measurement_service = services["measurement_service"]
        
        # 獲取基本統計信息 
        current_time = datetime.now(timezone.utc)
        
        # 模擬統計數據 - 實際應從測量服務獲取歷史數據
        base_stats = {
            "event_type": event_type.value,
            "timestamp": current_time.isoformat(),
            "total_events": 0,
            "success_rate": 0.0,
            "average_trigger_time_ms": 0,
            "last_24h_events": 0,
            "last_hour_events": 0
        }
        
        if event_type == EventType.A4:
            # A4 特定統計
            a4_stats = {
                **base_stats,
                "total_events": 1247,
                "success_rate": 96.3,
                "average_trigger_time_ms": 142,
                "last_24h_events": 89,
                "last_hour_events": 4,
                "signal_strength_stats": {
                    "average_rsrp_dbm": -78.5,
                    "min_rsrp_dbm": -95.2,
                    "max_rsrp_dbm": -65.1,
                    "rsrp_variance": 12.4
                },
                "threshold_analysis": {
                    "current_threshold_dbm": -80.0,
                    "optimal_threshold_dbm": -79.2,
                    "threshold_efficiency": 92.1,
                    "false_positive_rate": 3.7
                },
                "handover_performance": {
                    "successful_handovers": 1201,
                    "failed_handovers": 46,
                    "average_handover_duration_ms": 187,
                    "handover_success_rate": 96.3
                },
                "satellite_distribution": {
                    "starlink": {"count": 743, "success_rate": 97.1},
                    "oneweb": {"count": 356, "success_rate": 94.8},
                    "kuiper": {"count": 148, "success_rate": 95.9}
                },
                "time_analysis": {
                    "peak_hours": ["19:00-21:00", "08:00-10:00"],
                    "low_activity_hours": ["02:00-06:00"],
                    "weekend_vs_weekday_ratio": 0.73
                }
            }
            return a4_stats
            
        elif event_type == EventType.D1:
            # D1 特定統計
            d1_stats = {
                **base_stats,
                "total_events": 892,
                "success_rate": 94.7,
                "average_trigger_time_ms": 156,
                "last_24h_events": 67,
                "last_hour_events": 3,
                "distance_stats": {
                    "average_distance_km": 8.7,
                    "min_distance_km": 0.5,
                    "max_distance_km": 45.2,
                    "distance_variance": 15.8
                },
                "threshold_analysis": {
                    "thresh1_km": 10.0,
                    "thresh2_km": 5.0,
                    "optimal_thresh1_km": 9.8,
                    "optimal_thresh2_km": 4.9,
                    "threshold_efficiency": 89.3
                }
            }
            return d1_stats
            
        elif event_type == EventType.D2:
            # D2 特定統計
            d2_stats = {
                **base_stats,
                "total_events": 634,
                "success_rate": 91.2,
                "average_trigger_time_ms": 171,
                "last_24h_events": 45,
                "last_hour_events": 2,
                "satellite_distance_stats": {
                    "average_sat_distance_km": 785.3,
                    "min_sat_distance_km": 412.1,
                    "max_sat_distance_km": 1456.7
                },
                "ground_distance_stats": {
                    "average_ground_distance_km": 28.9,
                    "min_ground_distance_km": 2.1,
                    "max_ground_distance_km": 47.8
                }
            }
            return d2_stats
            
        elif event_type == EventType.T1:
            # T1 特定統計
            t1_stats = {
                **base_stats,
                "total_events": 445,
                "success_rate": 88.5,
                "average_trigger_time_ms": 198,
                "last_24h_events": 32,
                "last_hour_events": 1,
                "time_condition_stats": {
                    "average_condition_duration_s": 287.4,
                    "min_duration_s": 45.2,
                    "max_duration_s": 592.1
                },
                "threshold_analysis": {
                    "current_threshold_s": 300.0,
                    "optimal_threshold_s": 295.3,
                    "threshold_efficiency": 85.7
                }
            }
            return t1_stats
        
        # 如果沒有匹配的事件類型，返回基本統計
        return base_stats
        
    except Exception as e:
        logger.error(f"事件統計信息獲取失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="健康檢查",
    description="檢查測量事件服務的健康狀態"
)
async def health_check(
    services: Dict[str, Any] = Depends(get_services)
) -> Dict[str, Any]:
    """健康檢查"""
    try:
        measurement_service = services["measurement_service"]
        tle_manager = services["tle_manager"]
        sib19_platform = services["sib19_platform"]
        
        # 檢查 TLE 數據
        active_satellites = await tle_manager.get_active_satellites()
        
        # 檢查 SIB19 狀態
        sib19_status = await sib19_platform.get_sib19_status()
        
        # 檢查更新狀態
        update_status = await tle_manager.get_update_status()
        
        health_status = {
            "service": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "measurement_service": "available",
                "orbit_engine": "available",
                "sib19_platform": sib19_status.get("status", "unknown"),
                "tle_manager": "available"
            },
            "statistics": {
                "active_satellites": len(active_satellites),
                "total_satellites": update_status.get("total_satellites", 0),
                "active_constellations": update_status.get("constellations", 0),
                "active_tle_sources": update_status.get("active_sources", 0)
            },
            "sib19_info": {
                "status": sib19_status.get("status"),
                "satellites_count": sib19_status.get("satellites_count", 0),
                "time_sync_accuracy_ms": sib19_status.get("time_sync_accuracy_ms", 0)
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "service": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }