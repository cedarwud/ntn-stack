"""
Core Network Synchronization API Router

提供 IEEE INFOCOM 2024 核心同步服務的 REST API 端點

主要功能：
1. 同步服務管理 (啟動/停止/狀態查詢)
2. 同步性能監控
3. 組件同步狀態查詢
4. Fine-Grained 同步控制
5. 緊急同步處理
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

# Import services
from ..services.core_network_sync_service import CoreNetworkSyncService, CoreSyncState, NetworkComponent
from ..services.fine_grained_sync_service import FineGrainedSyncService, SyncState
from ..services.event_bus_service import EventBusService
from ..services.paper_synchronized_algorithm import SynchronizedAlgorithm, AccessInfo
from ..services.fast_access_prediction_service import FastSatellitePrediction, AccessStrategy
from ..services.handover_measurement_service import HandoverMeasurement, HandoverScheme, HandoverResult
import sys
import os

# 設置 logger 必須在其他導入之前
logger = structlog.get_logger(__name__)

# UPF 橋接模組導入 - 多路徑嘗試策略
UPF_BRIDGE_AVAILABLE = False
UPFSyncBridge = None
UEInfo = None
HandoverRequest = None

# 嘗試多個可能的路徑
upf_extension_paths = [
    os.path.join(os.path.dirname(__file__), '../../docker/upf-extension'),
    '/app/docker/upf-extension',
    './docker/upf-extension',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docker/upf-extension'))
]

for path in upf_extension_paths:
    try:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
        
        from python_upf_bridge import UPFSyncBridge, UEInfo, HandoverRequest
        UPF_BRIDGE_AVAILABLE = True
        logger.info("UPF 橋接模組已成功載入", path=path)
        break
        
    except ImportError as e:
        logger.debug(f"嘗試從 {path} 載入 UPF 橋接模組失敗: {e}")
        continue

if not UPF_BRIDGE_AVAILABLE:
    # 創建模擬類別作為回退
    logger.warning("UPF 橋接模組不可用，使用模擬實現")
    
    class MockUPFSyncBridge:
        def __init__(self, *args, **kwargs):
            self.is_running = False
        
        async def start(self):
            self.is_running = True
            return True
        
        async def stop(self):
            self.is_running = False
        
        async def get_algorithm_status(self):
            return {
                "service_status": {"running": False, "library_loaded": False},
                "ue_management": {"registered_ue_count": 0, "active_handover_count": 0},
                "handover_statistics": {"total_handovers": 0, "successful_handovers": 0},
                "note": "UPF bridge unavailable - using mock implementation"
            }
    
    class MockUEInfo:
        def __init__(self, ue_id: str, **kwargs):
            self.ue_id = ue_id
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class MockHandoverRequest:
        def __init__(self, ue_id: str, target_satellite_id: str, predicted_time: float, **kwargs):
            self.ue_id = ue_id
            self.target_satellite_id = target_satellite_id
            self.predicted_time = predicted_time
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    UPFSyncBridge = MockUPFSyncBridge
    UEInfo = MockUEInfo
    HandoverRequest = MockHandoverRequest

# Request/Response Models
class CoreSyncStartRequest(BaseModel):
    """核心同步服務啟動請求"""
    signaling_free_mode: bool = Field(True, description="啟用無信令模式")
    binary_search_enabled: bool = Field(True, description="啟用二進制搜索")
    max_sync_error_ms: float = Field(10.0, description="最大同步誤差(毫秒)")
    auto_resync_enabled: bool = Field(True, description="啟用自動重新同步")
    debug_logging: bool = Field(False, description="啟用調試日誌")


class CoreSyncStatusResponse(BaseModel):
    """核心同步狀態響應"""
    service_info: Dict[str, Any]
    sync_performance: Dict[str, Any]
    component_states: Dict[str, Any]
    statistics: Dict[str, Any]
    configuration: Dict[str, Any]
    ieee_infocom_2024_features: Dict[str, Any]


class ComponentSyncRequest(BaseModel):
    """組件同步請求"""
    component: str = Field(..., description="網路組件名稱")
    force_resync: bool = Field(False, description="強制重新同步")
    sync_accuracy_target_ms: Optional[float] = Field(None, description="目標同步精度")


class SatelliteAccessPredictionRequest(BaseModel):
    """衛星接入預測請求"""
    ue_id: str = Field(..., description="UE設備ID")
    satellite_id: str = Field(..., description="衛星ID")
    time_horizon_minutes: float = Field(30.0, description="預測時間範圍(分鐘)")


class EmergencyResyncRequest(BaseModel):
    """緊急重新同步請求"""
    target_components: Optional[List[str]] = Field(None, description="目標組件列表")
    emergency_threshold_ms: float = Field(100.0, description="緊急閾值(毫秒)")
    force_restart: bool = Field(False, description="強制重啟服務")


# 1.4 版本新增的請求/響應模型
class SyncPredictRequest(BaseModel):
    """同步預測請求"""
    ue_ids: List[str] = Field(..., description="UE ID 列表")
    prediction_horizon_seconds: float = Field(30.0, description="預測時間範圍(秒)")
    algorithm: str = Field("algorithm_1", description="使用的演算法 (algorithm_1 或 algorithm_2)")


class SyncHandoverRequest(BaseModel):
    """同步切換請求"""
    ue_id: str = Field(..., description="UE ID")
    target_satellite_id: str = Field(..., description="目標衛星 ID")
    predicted_time: Optional[float] = Field(None, description="預測切換時間戳")
    force_handover: bool = Field(False, description="強制執行切換")


class UPFIntegrationRequest(BaseModel):
    """UPF 整合請求"""
    ue_id: str = Field(..., description="UE ID")
    current_satellite_id: Optional[str] = Field(None, description="當前衛星 ID")
    access_strategy: str = Field("flexible", description="接入策略 (flexible 或 consistent)")
    position: Optional[Dict[str, float]] = Field(None, description="UE 位置 {lat, lon, alt}")


class SyncMetricsResponse(BaseModel):
    """同步指標響應"""
    algorithm_metrics: Dict[str, Any]
    handover_statistics: Dict[str, Any]
    upf_integration_status: Dict[str, Any]
    performance_summary: Dict[str, Any]


# Global service instances
core_sync_service: Optional[CoreNetworkSyncService] = None
paper_algorithm: Optional[SynchronizedAlgorithm] = None
fast_prediction_service: Optional[FastSatellitePrediction] = None
upf_bridge: Optional[UPFSyncBridge] = None
handover_measurement: Optional[HandoverMeasurement] = None


def get_core_sync_service() -> CoreNetworkSyncService:
    """獲取核心同步服務實例"""
    global core_sync_service
    if core_sync_service is None:
        # 初始化依賴服務
        fine_grained_sync = FineGrainedSyncService()
        event_bus = EventBusService() if hasattr(EventBusService, '__init__') else None
        
        # 創建核心同步服務
        core_sync_service = CoreNetworkSyncService(
            fine_grained_sync_service=fine_grained_sync,
            event_bus_service=event_bus
        )
    
    return core_sync_service


def get_paper_algorithm() -> SynchronizedAlgorithm:
    """獲取論文同步演算法實例"""
    global paper_algorithm
    if paper_algorithm is None:
        paper_algorithm = SynchronizedAlgorithm(
            delta_t=5.0,
            binary_search_precision=0.01
        )
    return paper_algorithm


def get_fast_prediction_service() -> FastSatellitePrediction:
    """獲取快速衛星預測服務實例"""
    global fast_prediction_service
    if fast_prediction_service is None:
        fast_prediction_service = FastSatellitePrediction(
            earth_radius_km=6371.0,
            block_size_degrees=10.0,
            prediction_accuracy_target=0.95
        )
    return fast_prediction_service


async def get_upf_bridge() -> Optional[UPFSyncBridge]:
    """獲取 UPF 橋接服務實例"""
    global upf_bridge
    if upf_bridge is None and UPF_BRIDGE_AVAILABLE:
        try:
            upf_bridge = UPFSyncBridge()
            # 嘗試啟動橋接服務
            success = await upf_bridge.start()
            if not success:
                logger.warning("UPF 橋接服務啟動失敗")
                upf_bridge = None
        except Exception as e:
            logger.error(f"初始化 UPF 橋接服務失敗: {e}")
            upf_bridge = None
    return upf_bridge


def get_handover_measurement() -> HandoverMeasurement:
    """獲取效能測量服務實例"""
    global handover_measurement
    if handover_measurement is None:
        handover_measurement = HandoverMeasurement(
            output_dir="./measurement_results"
        )
    return handover_measurement


# 創建路由器
router = APIRouter(
    prefix="/api/v1/core-sync",
    tags=["Core Network Synchronization"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.post("/service/start", 
             summary="啟動核心同步服務",
             description="啟動 IEEE INFOCOM 2024 核心網路同步服務")
async def start_core_sync_service(
    background_tasks: BackgroundTasks,
    request: CoreSyncStartRequest,
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """啟動核心同步服務"""
    try:
        # 更新配置
        service.config.signaling_free_mode = request.signaling_free_mode
        service.config.binary_search_enabled = request.binary_search_enabled
        service.config.max_sync_error_ms = request.max_sync_error_ms
        service.config.auto_resync_enabled = request.auto_resync_enabled
        service.config.debug_logging = request.debug_logging
        
        # 啟動服務
        await service.start_core_sync_service()
        
        logger.info(
            "核心同步服務啟動成功",
            signaling_free=request.signaling_free_mode,
            binary_search=request.binary_search_enabled
        )
        
        return {
            "success": True,
            "message": "核心同步服務啟動成功",
            "service_state": service.core_sync_state.value,
            "config": {
                "signaling_free_mode": request.signaling_free_mode,
                "binary_search_enabled": request.binary_search_enabled,
                "max_sync_error_ms": request.max_sync_error_ms
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"啟動核心同步服務失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"啟動核心同步服務失敗: {str(e)}"
        )


@router.post("/service/stop",
             summary="停止核心同步服務", 
             description="停止核心網路同步服務")
async def stop_core_sync_service(
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """停止核心同步服務"""
    try:
        await service.stop_core_sync_service()
        
        logger.info("核心同步服務停止成功")
        
        return {
            "success": True,
            "message": "核心同步服務停止成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"停止核心同步服務失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"停止核心同步服務失敗: {str(e)}"
        )


@router.get("/status",
            response_model=CoreSyncStatusResponse,
            summary="獲取同步狀態",
            description="獲取完整的核心同步狀態信息")
async def get_core_sync_status(
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """獲取核心同步狀態"""
    try:
        status = await service.get_core_sync_status()
        return CoreSyncStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"獲取同步狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取同步狀態失敗: {str(e)}"
        )


@router.get("/status/summary",
            summary="獲取同步狀態摘要",
            description="獲取核心同步狀態的簡要摘要")
async def get_sync_status_summary(
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """獲取同步狀態摘要"""
    try:
        status = await service.get_core_sync_status()
        
        # 提取關鍵指標
        summary = {
            "is_running": status["service_info"]["is_running"],
            "core_sync_state": status["service_info"]["core_sync_state"],
            "overall_accuracy_ms": status["sync_performance"]["overall_accuracy_ms"],
            "signaling_free_enabled": status["sync_performance"]["signaling_free_enabled"],
            "synchronized_components": len([
                comp for comp, info in status["component_states"].items()
                if info["sync_state"] == "synchronized"
            ]),
            "total_components": len(status["component_states"]),
            "uptime_percentage": status["statistics"].get("uptime_percentage", 0.0),
            "last_update": datetime.now().isoformat()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"獲取同步狀態摘要失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取同步狀態摘要失敗: {str(e)}"
        )


@router.get("/components/{component_name}/status",
            summary="獲取組件同步狀態",
            description="獲取特定網路組件的同步狀態")
async def get_component_sync_status(
    component_name: str = Path(..., description="組件名稱"),
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """獲取組件同步狀態"""
    try:
        # 驗證組件名稱
        try:
            component = NetworkComponent(component_name.lower())
        except ValueError:
            valid_components = [comp.value for comp in NetworkComponent]
            raise HTTPException(
                status_code=400,
                detail=f"無效的組件名稱。有效選項: {valid_components}"
            )
        
        status = await service.get_core_sync_status()
        component_info = status["component_states"].get(component.value)
        
        if not component_info:
            raise HTTPException(
                status_code=404,
                detail=f"找不到組件 {component_name} 的狀態信息"
            )
        
        # 添加額外的組件特定信息
        component_metrics = service.performance_metrics.get(component)
        if component_metrics:
            component_info.update({
                "latency_ms": component_metrics.latency_ms,
                "jitter_ms": component_metrics.jitter_ms,
                "throughput_mbps": component_metrics.throughput_mbps,
                "packet_loss_rate": component_metrics.packet_loss_rate,
                "error_rate": component_metrics.error_rate
            })
        
        return {
            "component": component_name,
            "status": component_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取組件 {component_name} 狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取組件狀態失敗: {str(e)}"
        )


@router.post("/components/sync",
             summary="同步指定組件",
             description="對指定的網路組件執行同步操作")
async def sync_component(
    request: ComponentSyncRequest,
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """同步指定組件"""
    try:
        # 驗證組件名稱
        try:
            component = NetworkComponent(request.component.lower())
        except ValueError:
            valid_components = [comp.value for comp in NetworkComponent]
            raise HTTPException(
                status_code=400,
                detail=f"無效的組件名稱。有效選項: {valid_components}"
            )
        
        # 執行組件同步
        reference_time = datetime.now()
        sync_result = await service._synchronize_component(component, reference_time)
        
        if sync_result["success"]:
            service.component_states[component] = SyncState.SYNCHRONIZED
            
            logger.info(f"組件 {request.component} 同步成功")
            
            return {
                "success": True,
                "message": f"組件 {request.component} 同步成功",
                "component": request.component,
                "sync_result": sync_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"組件 {request.component} 同步失敗: {sync_result.get('error')}")
            
            return {
                "success": False,
                "message": f"組件 {request.component} 同步失敗",
                "component": request.component,
                "error": sync_result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步組件 {request.component} 失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同步組件失敗: {str(e)}"
        )


@router.post("/prediction/satellite-access",
             summary="預測衛星接入",
             description="使用 Fine-Grained 算法預測衛星接入時間")
async def predict_satellite_access(
    request: SatelliteAccessPredictionRequest,
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """預測衛星接入"""
    try:
        if not service.fine_grained_sync:
            raise HTTPException(
                status_code=503,
                detail="Fine-Grained 同步服務不可用"
            )
        
        # 執行衛星接入預測
        prediction = await service.fine_grained_sync.predict_satellite_access(
            ue_id=request.ue_id,
            satellite_id=request.satellite_id,
            time_horizon_minutes=request.time_horizon_minutes
        )
        
        logger.info(
            f"衛星接入預測完成: {request.ue_id} -> {request.satellite_id}",
            prediction_id=prediction.prediction_id
        )
        
        return {
            "success": True,
            "prediction_id": prediction.prediction_id,
            "ue_id": prediction.ue_id,
            "satellite_id": prediction.satellite_id,
            "predicted_access_time": prediction.predicted_access_time.isoformat(),
            "confidence_score": prediction.confidence_score,
            "error_bound_ms": prediction.error_bound_ms,
            "binary_search_iterations": prediction.binary_search_iterations,
            "convergence_achieved": prediction.convergence_achieved,
            "access_probability": prediction.access_probability,
            "algorithm_details": {
                "two_point_prediction": {
                    "time_t": prediction.prediction_time_t.isoformat(),
                    "time_t_delta": prediction.prediction_time_t_delta.isoformat()
                },
                "binary_search_refinement": {
                    "iterations": prediction.binary_search_iterations,
                    "converged": prediction.convergence_achieved
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"衛星接入預測失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"衛星接入預測失敗: {str(e)}"
        )


@router.post("/emergency/resync",
             summary="緊急重新同步",
             description="在緊急情況下執行重新同步操作")
async def emergency_resync(
    request: EmergencyResyncRequest,
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """緊急重新同步"""
    try:
        # 確定要重新同步的組件
        if request.target_components:
            target_components = []
            for comp_name in request.target_components:
                try:
                    component = NetworkComponent(comp_name.lower())
                    target_components.append(component)
                except ValueError:
                    logger.warning(f"忽略無效組件名稱: {comp_name}")
        else:
            # 如果沒有指定組件，同步所有組件
            target_components = list(NetworkComponent)
        
        if not target_components:
            raise HTTPException(
                status_code=400,
                detail="沒有有效的目標組件"
            )
        
        # 檢查是否需要強制重啟
        if request.force_restart:
            await service.stop_core_sync_service()
            await asyncio.sleep(1.0)  # 等待服務完全停止
            await service.start_core_sync_service()
        
        # 執行選擇性重新同步
        await service._perform_selective_resync(target_components)
        
        # 更新緊急閾值
        service.config.emergency_threshold_ms = request.emergency_threshold_ms
        
        logger.info(
            "緊急重新同步完成",
            target_components=[comp.value for comp in target_components],
            force_restart=request.force_restart
        )
        
        return {
            "success": True,
            "message": "緊急重新同步完成",
            "target_components": [comp.value for comp in target_components],
            "force_restart": request.force_restart,
            "emergency_threshold_ms": request.emergency_threshold_ms,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"緊急重新同步失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"緊急重新同步失敗: {str(e)}"
        )


@router.get("/metrics/performance",
            summary="獲取性能指標",
            description="獲取核心同步服務的詳細性能指標")
async def get_performance_metrics(
    component: Optional[str] = Query(None, description="特定組件名稱(可選)"),
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """獲取性能指標"""
    try:
        if component:
            # 獲取特定組件的性能指標
            try:
                target_component = NetworkComponent(component.lower())
            except ValueError:
                valid_components = [comp.value for comp in NetworkComponent]
                raise HTTPException(
                    status_code=400,
                    detail=f"無效的組件名稱。有效選項: {valid_components}"
                )
            
            metrics = service.performance_metrics.get(target_component)
            if not metrics:
                raise HTTPException(
                    status_code=404,
                    detail=f"找不到組件 {component} 的性能指標"
                )
            
            return {
                "component": component,
                "metrics": {
                    "sync_accuracy_ms": metrics.sync_accuracy_ms,
                    "clock_drift_ms": metrics.clock_drift_ms,
                    "last_sync_time": metrics.last_sync_time.isoformat(),
                    "sync_frequency_hz": metrics.sync_frequency_hz,
                    "error_rate": metrics.error_rate,
                    "latency_ms": metrics.latency_ms,
                    "jitter_ms": metrics.jitter_ms,
                    "packet_loss_rate": metrics.packet_loss_rate,
                    "throughput_mbps": metrics.throughput_mbps,
                    "availability": metrics.availability
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 獲取所有組件的性能指標
            all_metrics = {}
            for comp, metrics in service.performance_metrics.items():
                all_metrics[comp.value] = {
                    "sync_accuracy_ms": metrics.sync_accuracy_ms,
                    "clock_drift_ms": metrics.clock_drift_ms,
                    "last_sync_time": metrics.last_sync_time.isoformat(),
                    "sync_frequency_hz": metrics.sync_frequency_hz,
                    "error_rate": metrics.error_rate,
                    "latency_ms": metrics.latency_ms,
                    "jitter_ms": metrics.jitter_ms,
                    "packet_loss_rate": metrics.packet_loss_rate,
                    "throughput_mbps": metrics.throughput_mbps,
                    "availability": metrics.availability
                }
            
            return {
                "all_components": all_metrics,
                "summary": {
                    "total_components": len(all_metrics),
                    "average_accuracy_ms": sum(m["sync_accuracy_ms"] for m in all_metrics.values()) / len(all_metrics),
                    "average_availability": sum(m["availability"] for m in all_metrics.values()) / len(all_metrics)
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取性能指標失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取性能指標失敗: {str(e)}"
        )


@router.get("/events/recent",
            summary="獲取最近同步事件",
            description="獲取最近的同步事件列表")
async def get_recent_sync_events(
    limit: int = Query(10, ge=1, le=100, description="返回事件數量限制"),
    event_type: Optional[str] = Query(None, description="事件類型過濾"),
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """獲取最近同步事件"""
    try:
        # 獲取最近的事件
        recent_events = service.sync_events[-limit:] if service.sync_events else []
        
        # 過濾事件類型
        if event_type:
            recent_events = [
                event for event in recent_events 
                if event_type.lower() in event.event_type.lower()
            ]
        
        # 格式化事件數據
        formatted_events = []
        for event in recent_events:
            formatted_events.append({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source_component": event.source_component.value,
                "target_component": event.target_component.value if event.target_component else None,
                "sync_accuracy_achieved": event.sync_accuracy_achieved,
                "error_occurred": event.error_occurred,
                "error_message": event.error_message,
                "corrective_action": event.corrective_action,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata
            })
        
        return {
            "events": formatted_events,
            "total_events": len(formatted_events),
            "filter_applied": {"event_type": event_type} if event_type else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取同步事件失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取同步事件失敗: {str(e)}"
        )


# Health check endpoint
@router.get("/health",
            summary="健康檢查",
            description="檢查核心同步服務的健康狀態")
async def health_check(
    service: CoreNetworkSyncService = Depends(get_core_sync_service)
):
    """健康檢查"""
    try:
        is_healthy = (
            service.is_running and 
            service.core_sync_state in [CoreSyncState.SYNCHRONIZED, CoreSyncState.PARTIAL_SYNC]
        )
        
        status_code = 200 if is_healthy else 503
        
        health_info = {
            "healthy": is_healthy,
            "service_running": service.is_running,
            "core_sync_state": service.core_sync_state.value,
            "active_tasks": len([t for t in service.sync_tasks.values() if not t.done()]),
            "last_check": datetime.now().isoformat()
        }
        
        return JSONResponse(content=health_info, status_code=status_code)
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return JSONResponse(
            content={
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            },
            status_code=503
        )


# =============================================================================
# 1.4 版本新增 API 端點
# =============================================================================

@router.post("/sync/predict",
             summary="觸發同步預測",
             description="使用論文演算法觸發同步預測更新")
async def trigger_sync_prediction(
    request: SyncPredictRequest,
    algorithm_service: SynchronizedAlgorithm = Depends(get_paper_algorithm),
    fast_service: FastSatellitePrediction = Depends(get_fast_prediction_service)
):
    """觸發同步預測"""
    try:
        start_time = time.time()
        
        if request.algorithm == "algorithm_1":
            # 使用 Algorithm 1 (同步演算法)
            predictions = {}
            for ue_id in request.ue_ids:
                # 執行 UE 更新
                await algorithm_service.update_ue(ue_id)
                
                # 獲取預測結果
                ue_status = await algorithm_service.get_ue_status(ue_id)
                predictions[ue_id] = {
                    "current_satellite": ue_status.get("current_satellite"),
                    "predicted_satellite": ue_status.get("next_access_satellite"),
                    "predicted_handover_time": ue_status.get("handover_time"),
                    "algorithm_used": "algorithm_1"
                }
            
            # 獲取演算法狀態
            algorithm_status = await algorithm_service.get_algorithm_status()
            
            result = {
                "success": True,
                "algorithm": "algorithm_1",
                "predictions": predictions,
                "algorithm_status": algorithm_status,
                "prediction_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
            
        elif request.algorithm == "algorithm_2":
            # 使用 Algorithm 2 (快速衛星預測)
            # 準備衛星資料（模擬）
            satellites = [
                {"satellite_id": f"starlink_{i}", "lat": 0.0, "lon": 0.0, "alt": 550.0}
                for i in range(1001, 1021)  # 使用 20 顆衛星進行測試
            ]
            
            # 執行快速預測
            future_time = time.time() + request.prediction_horizon_seconds
            predictions = await fast_service.predict_access_satellites(
                users=request.ue_ids,
                satellites=satellites,
                time_t=future_time
            )
            
            # 獲取服務狀態
            service_status = await fast_service.get_service_status()
            
            result = {
                "success": True,
                "algorithm": "algorithm_2",
                "predictions": {
                    ue_id: {
                        "predicted_satellite": satellite_id,
                        "prediction_time": future_time,
                        "algorithm_used": "algorithm_2"
                    }
                    for ue_id, satellite_id in predictions.items()
                },
                "service_status": service_status,
                "prediction_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的演算法: {request.algorithm}. 支援的選項: algorithm_1, algorithm_2"
            )
        
        logger.info(
            "同步預測完成",
            algorithm=request.algorithm,
            ue_count=len(request.ue_ids),
            prediction_time_ms=result["prediction_time_ms"]
        )
        
        return result
        
    except Exception as e:
        logger.error(f"同步預測失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"同步預測失敗: {str(e)}"
        )


@router.post("/sync/handover",
             summary="手動觸發切換",
             description="手動觸發 UE 衛星切換")
async def trigger_sync_handover(
    request: SyncHandoverRequest,
    upf_bridge: UPFSyncBridge = Depends(get_upf_bridge)
):
    """手動觸發切換"""
    try:
        
        if not upf_bridge:
            # 如果 UPF 橋接不可用，使用模擬模式
            logger.info(
                "UPF 橋接不可用，使用模擬切換",
                ue_id=request.ue_id,
                target_satellite=request.target_satellite_id
            )
            
            # 模擬切換延遲
            await asyncio.sleep(0.025)  # 25ms 模擬延遲
            
            return {
                "success": True,
                "ue_id": request.ue_id,
                "target_satellite_id": request.target_satellite_id,
                "handover_type": "simulated",
                "latency_ms": 25.0,
                "force_handover": request.force_handover,
                "predicted_time": request.predicted_time,
                "timestamp": datetime.now().isoformat()
            }
        
        # 使用真實 UPF 橋接執行切換
        handover_req = HandoverRequest(
            ue_id=request.ue_id,
            target_satellite_id=request.target_satellite_id,
            predicted_time=request.predicted_time or time.time(),
            reason="manual_trigger"
        )
        
        start_time = time.time()
        success = await upf_bridge.trigger_handover(handover_req)
        latency_ms = (time.time() - start_time) * 1000
        
        if success:
            logger.info(
                "手動切換成功",
                ue_id=request.ue_id,
                target_satellite=request.target_satellite_id,
                latency_ms=latency_ms
            )
            
            return {
                "success": True,
                "ue_id": request.ue_id,
                "target_satellite_id": request.target_satellite_id,
                "handover_type": "upf_integrated",
                "latency_ms": latency_ms,
                "force_handover": request.force_handover,
                "predicted_time": request.predicted_time,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="UPF 切換執行失敗"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"觸發切換失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"觸發切換失敗: {str(e)}"
        )


@router.get("/sync/status",
            summary="獲取演算法運行狀態",
            description="獲取同步演算法的運行狀態")
async def get_sync_status(
    algorithm_service: SynchronizedAlgorithm = Depends(get_paper_algorithm),
    fast_service: FastSatellitePrediction = Depends(get_fast_prediction_service),
    upf_bridge: UPFSyncBridge = Depends(get_upf_bridge)
):
    """獲取同步演算法狀態"""
    try:
        
        # 獲取 Algorithm 1 狀態
        algorithm1_status = await algorithm_service.get_algorithm_status()
        
        # 獲取 Algorithm 2 狀態
        algorithm2_status = await fast_service.get_service_status()
        
        # 獲取 UPF 橋接狀態
        upf_status = None
        if upf_bridge:
            upf_status = await upf_bridge.get_algorithm_status()
        
        return {
            "algorithm_1": {
                "name": "Synchronized Algorithm",
                "status": algorithm1_status,
                "available": True
            },
            "algorithm_2": {
                "name": "Fast Satellite Prediction",
                "status": algorithm2_status,
                "available": True
            },
            "upf_integration": {
                "available": upf_bridge is not None,
                "status": upf_status,
                "bridge_loaded": UPF_BRIDGE_AVAILABLE
            },
            "overall_status": {
                "algorithms_running": (
                    algorithm1_status.get("algorithm_state") != "stopped" or
                    algorithm2_status.get("accuracy_achieved", False)
                ),
                "upf_integrated": upf_bridge is not None,
                "system_ready": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取同步狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取同步狀態失敗: {str(e)}"
        )


@router.get("/sync/metrics",
            response_model=SyncMetricsResponse,
            summary="獲取效能指標",
            description="獲取同步演算法和 UPF 整合的效能指標")
async def get_sync_metrics(
    algorithm_service: SynchronizedAlgorithm = Depends(get_paper_algorithm),
    fast_service: FastSatellitePrediction = Depends(get_fast_prediction_service),
    upf_bridge: UPFSyncBridge = Depends(get_upf_bridge)
):
    """獲取同步指標"""
    try:
        
        # 獲取 Algorithm 1 指標
        algorithm1_metrics = await algorithm_service.get_performance_metrics()
        
        # 獲取 Algorithm 2 指標
        algorithm2_status = await fast_service.get_service_status()
        algorithm2_metrics = algorithm2_status.get("performance_stats", {})
        
        # 獲取 UPF 指標
        upf_metrics = {}
        handover_stats = {}
        if upf_bridge:
            upf_status = await upf_bridge.get_algorithm_status()
            upf_metrics = upf_status.get("service_status", {})
            handover_stats = upf_status.get("handover_statistics", {})
        
        # 彙總效能指標
        performance_summary = {
            "algorithm_1_accuracy": algorithm1_metrics.get("prediction_accuracy", 0.0),
            "algorithm_2_accuracy": algorithm2_status.get("current_accuracy", 0.0),
            "total_handovers": handover_stats.get("total_handovers", 0),
            "successful_handovers": handover_stats.get("successful_handovers", 0),
            "average_latency_ms": handover_stats.get("average_latency_ms", 0.0),
            "upf_integration_active": upf_bridge is not None
        }
        
        return SyncMetricsResponse(
            algorithm_metrics={
                "algorithm_1": algorithm1_metrics,
                "algorithm_2": algorithm2_metrics
            },
            handover_statistics=handover_stats,
            upf_integration_status=upf_metrics,
            performance_summary=performance_summary
        )
        
    except Exception as e:
        logger.error(f"獲取同步指標失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取同步指標失敗: {str(e)}"
        )


@router.post("/upf/register-ue",
             summary="註冊 UE 到 UPF",
             description="將 UE 註冊到 UPF 同步演算法系統")
async def register_ue_to_upf(
    request: UPFIntegrationRequest,
    upf_bridge: UPFSyncBridge = Depends(get_upf_bridge)
):
    """註冊 UE 到 UPF"""
    try:
        
        if not upf_bridge:
            raise HTTPException(
                status_code=503,
                detail="UPF 橋接服務不可用"
            )
        
        # 創建 UE 資訊
        access_strategy = AccessStrategy.FLEXIBLE if request.access_strategy == "flexible" else AccessStrategy.CONSISTENT
        
        ue_info = UEInfo(
            ue_id=request.ue_id,
            current_satellite_id=request.current_satellite_id,
            access_strategy=access_strategy,
            position=request.position or {"lat": 24.1477, "lon": 120.6736, "alt": 100.0}
        )
        
        # 註冊 UE
        success = await upf_bridge.register_ue(ue_info)
        
        if success:
            logger.info(
                "UE 註冊到 UPF 成功",
                ue_id=request.ue_id,
                access_strategy=request.access_strategy
            )
            
            return {
                "success": True,
                "ue_id": request.ue_id,
                "access_strategy": request.access_strategy,
                "current_satellite_id": request.current_satellite_id,
                "position": ue_info.position,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="UE 註冊失敗"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"註冊 UE 到 UPF 失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"註冊 UE 失敗: {str(e)}"
        )


@router.get("/upf/ue/{ue_id}/status",
            summary="獲取 UE 在 UPF 中的狀態",
            description="獲取 UE 在 UPF 同步系統中的狀態")
async def get_ue_upf_status(
    ue_id: str = Path(..., description="UE ID"),
    upf_bridge: UPFSyncBridge = Depends(get_upf_bridge)
):
    """獲取 UE UPF 狀態"""
    try:
        
        if not upf_bridge:
            raise HTTPException(
                status_code=503,
                detail="UPF 橋接服務不可用"
            )
        
        # 獲取 UE 狀態
        ue_status = await upf_bridge.get_ue_status(ue_id)
        
        if ue_status is None:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 UE {ue_id}"
            )
        
        return {
            "ue_id": ue_id,
            "status": ue_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 UE UPF 狀態失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取 UE 狀態失敗: {str(e)}"
        )


# =============================================================================
# 論文效能測量 API 端點
# =============================================================================

@router.post("/measurement/record-handover",
             summary="記錄切換事件",
             description="記錄切換事件到效能測量系統")
async def record_handover_event(
    ue_id: str,
    source_gnb: str,
    target_gnb: str,
    start_time: float,
    end_time: float,
    scheme: str,
    result: str = "success",
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """記錄切換事件"""
    try:
        # 轉換方案類型
        try:
            handover_scheme = HandoverScheme(scheme.upper())
        except ValueError:
            valid_schemes = [s.value for s in HandoverScheme]
            raise HTTPException(
                status_code=400,
                detail=f"無效的切換方案: {scheme}. 有效選項: {valid_schemes}"
            )
        
        # 轉換結果類型
        try:
            handover_result = HandoverResult(result.lower())
        except ValueError:
            valid_results = [r.value for r in HandoverResult]
            raise HTTPException(
                status_code=400,
                detail=f"無效的切換結果: {result}. 有效選項: {valid_results}"
            )
        
        # 記錄事件
        event_id = measurement_service.record_handover(
            ue_id=ue_id,
            source_gnb=source_gnb,
            target_gnb=target_gnb,
            start_time=start_time,
            end_time=end_time,
            handover_scheme=handover_scheme,
            result=handover_result
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "ue_id": ue_id,
            "scheme": scheme,
            "result": result,
            "latency_ms": (end_time - start_time) * 1000,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"記錄切換事件失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"記錄切換事件失敗: {str(e)}"
        )


@router.get("/measurement/statistics",
            summary="獲取效能統計",
            description="獲取四種方案的效能統計分析")
async def get_measurement_statistics(
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """獲取效能統計"""
    try:
        statistics = measurement_service.analyze_latency()
        summary = measurement_service.get_summary_statistics()
        
        return {
            "summary": summary,
            "detailed_statistics": {
                scheme.value: {
                    "scheme": stats.scheme.value,
                    "total_handovers": stats.total_handovers,
                    "successful_handovers": stats.successful_handovers,
                    "success_rate": stats.success_rate,
                    "mean_latency_ms": stats.mean_latency_ms,
                    "std_latency_ms": stats.std_latency_ms,
                    "percentile_95_ms": stats.percentile_95_ms,
                    "percentile_99_ms": stats.percentile_99_ms,
                    "mean_prediction_accuracy": stats.mean_prediction_accuracy
                }
                for scheme, stats in statistics.items()
                if stats.total_handovers > 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取效能統計失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取效能統計失敗: {str(e)}"
        )


@router.get("/measurement/comparison-report",
            summary="生成對比報告",
            description="生成四種方案的詳細對比報告")
async def get_comparison_report(
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """生成對比報告"""
    try:
        report = measurement_service.generate_comparison_report()
        return report
        
    except Exception as e:
        logger.error(f"生成對比報告失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成對比報告失敗: {str(e)}"
        )


@router.post("/measurement/generate-cdf",
             summary="生成 CDF 圖表",
             description="生成切換延遲的累積分佈函數圖表")
async def generate_cdf_plot(
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """生成 CDF 圖表"""
    try:
        plot_path = measurement_service.plot_latency_cdf()
        
        return {
            "success": True,
            "plot_path": plot_path,
            "message": "CDF 圖表生成成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成 CDF 圖表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成 CDF 圖表失敗: {str(e)}"
        )


@router.post("/measurement/export-data",
             summary="匯出測量數據",
             description="匯出效能測量數據")
async def export_measurement_data(
    format: str = "json",
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """匯出測量數據"""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的匯出格式: {format}. 支援的格式: json, csv"
            )
        
        export_path = measurement_service.export_data(format)
        
        return {
            "success": True,
            "export_path": export_path,
            "format": format,
            "total_events": len(measurement_service.handover_events),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"匯出測量數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"匯出測量數據失敗: {str(e)}"
        )


@router.post("/measurement/run-automated-test",
             summary="執行自動化對比測試",
             description="執行四種方案的自動化對比測試")
async def run_automated_comparison_test(
    duration_seconds: int = 60,
    ue_count: int = 3,
    handover_interval_seconds: float = 5.0,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    measurement_service: HandoverMeasurement = Depends(get_handover_measurement)
):
    """執行自動化對比測試"""
    try:
        # 驗證參數
        if duration_seconds < 10 or duration_seconds > 3600:
            raise HTTPException(
                status_code=400,
                detail="測試持續時間必須在 10-3600 秒之間"
            )
        
        if ue_count < 1 or ue_count > 20:
            raise HTTPException(
                status_code=400,
                detail="UE 數量必須在 1-20 之間"
            )
        
        if handover_interval_seconds < 1.0 or handover_interval_seconds > 60.0:
            raise HTTPException(
                status_code=400,
                detail="切換間隔必須在 1.0-60.0 秒之間"
            )
        
        # 執行測試（異步）
        test_result = await measurement_service.run_automated_comparison_test(
            duration_seconds=duration_seconds,
            ue_count=ue_count,
            handover_interval_seconds=handover_interval_seconds
        )
        
        return {
            "success": True,
            "test_result": test_result,
            "message": "自動化對比測試完成",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行自動化測試失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"執行自動化測試失敗: {str(e)}"
        )