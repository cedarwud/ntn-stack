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

logger = structlog.get_logger(__name__)

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


# Global service instance
core_sync_service: Optional[CoreNetworkSyncService] = None


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
    request: CoreSyncStartRequest,
    background_tasks: BackgroundTasks,
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