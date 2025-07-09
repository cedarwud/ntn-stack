"""
視覺化專用 API
=============

提供 3D 視覺化專用的 API 端點。
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse

from .handover_3d_coordinator import Handover3DCoordinator
from .realtime_event_streamer import RealtimeEventStreamer
from .rl_monitor_bridge import RLMonitorBridge
from .animation_sync_manager import AnimationSyncManager
from ..interfaces.visualization_coordinator import VisualizationEvent, AnimationType

logger = logging.getLogger(__name__)

# 創建 API 路由器
router = APIRouter(prefix="/api/v1/visualization", tags=["3D 視覺化"])

# 全局組件實例 (實際應該通過依賴注入)
_event_streamer: Optional[RealtimeEventStreamer] = None
_coordinator: Optional[Handover3DCoordinator] = None
_rl_bridge: Optional[RLMonitorBridge] = None
_sync_manager: Optional[AnimationSyncManager] = None


def get_event_streamer() -> RealtimeEventStreamer:
    """獲取事件推送器"""
    global _event_streamer
    if _event_streamer is None:
        _event_streamer = RealtimeEventStreamer()
    return _event_streamer


def get_visualization_coordinator() -> Handover3DCoordinator:
    """獲取視覺化協調器"""
    global _coordinator
    if _coordinator is None:
        _coordinator = Handover3DCoordinator(get_event_streamer())
    return _coordinator


def get_rl_bridge() -> RLMonitorBridge:
    """獲取 RL 監控橋接器"""
    global _rl_bridge
    if _rl_bridge is None:
        _rl_bridge = RLMonitorBridge(get_event_streamer())
    return _rl_bridge


def get_sync_manager() -> AnimationSyncManager:
    """獲取同步管理器"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = AnimationSyncManager()
    return _sync_manager


# WebSocket 端點
@router.websocket("/ws/handover-events")
async def websocket_handover_events(websocket: WebSocket):
    """WebSocket 連接用於即時換手事件推送"""
    await websocket.accept()
    
    try:
        # 註冊到事件推送器
        event_streamer = get_event_streamer()
        await event_streamer.register_connection(websocket)
        
    except WebSocketDisconnect:
        logger.info("WebSocket 連接斷開")
    except Exception as e:
        logger.error("WebSocket 連接異常", error=str(e))


@router.websocket("/ws/rl-monitor")
async def websocket_rl_monitor(websocket: WebSocket):
    """WebSocket 連接用於 RL 監控數據推送"""
    await websocket.accept()
    
    try:
        # 註冊到事件推送器
        event_streamer = get_event_streamer()
        await event_streamer.register_connection(websocket, {"type": "rl_monitor"})
        
    except WebSocketDisconnect:
        logger.info("RL 監控 WebSocket 連接斷開")
    except Exception as e:
        logger.error("RL 監控 WebSocket 連接異常", error=str(e))


# 3D 視覺化端點
@router.get("/handover/3d-state")
async def get_3d_handover_state(coordinator: Handover3DCoordinator = Depends(get_visualization_coordinator)):
    """獲取當前 3D 換手狀態"""
    try:
        state = {
            "animation_state": {
                "active_animations": len(coordinator.get_active_animations()),
                "animation_queue": len(coordinator.animation_queue),
            },
            "active_handovers": coordinator.get_active_handovers(),
            "satellite_positions": coordinator.get_current_satellite_positions(),
            "timestamp": coordinator.last_position_update,
        }
        
        return JSONResponse(content=state)
        
    except Exception as e:
        logger.error("獲取 3D 換手狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/handover/trigger")
async def trigger_manual_handover(
    handover_request: Dict[str, Any],
    coordinator: Handover3DCoordinator = Depends(get_visualization_coordinator)
):
    """手動觸發換手（用於測試和演示）"""
    try:
        # 創建視覺化事件
        event = VisualizationEvent(
            event_type=AnimationType.HANDOVER_STARTED,
            timestamp=handover_request.get("timestamp", 0.0),
            satellite_data=handover_request.get("satellite_data", {}),
            animation_params=handover_request.get("animation_params", {}),
            duration_ms=handover_request.get("duration_ms", 3000),
            priority=handover_request.get("priority", 0),
        )
        
        # 觸發動畫
        animation_id = await coordinator.trigger_3d_animation(event)
        
        return JSONResponse(content={
            "success": True,
            "animation_id": animation_id,
            "message": "換手動畫已觸發",
        })
        
    except Exception as e:
        logger.error("手動觸發換手失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/handover/history/{satellite_id}")
async def get_handover_history(satellite_id: str):
    """獲取特定衛星的換手歷史"""
    try:
        # 簡化實現，實際應該查詢數據庫
        history = {
            "satellite_id": satellite_id,
            "handover_count": 10,
            "success_rate": 0.95,
            "avg_handover_time": 2.5,
            "recent_handovers": [
                {
                    "timestamp": 1640995200.0,
                    "source_satellite": "SAT_001",
                    "target_satellite": satellite_id,
                    "success": True,
                    "duration": 2.1,
                },
                {
                    "timestamp": 1640995500.0,
                    "source_satellite": satellite_id,
                    "target_satellite": "SAT_003",
                    "success": True,
                    "duration": 2.8,
                },
            ],
        }
        
        return JSONResponse(content=history)
        
    except Exception as e:
        logger.error("獲取換手歷史失敗", satellite_id=satellite_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/animation/control")
async def control_animation(
    control_request: Dict[str, Any],
    coordinator: Handover3DCoordinator = Depends(get_visualization_coordinator)
):
    """控制動畫（暫停、恢復、取消）"""
    try:
        action = control_request.get("action")
        animation_id = control_request.get("animation_id")
        
        if not action or not animation_id:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        success = False
        
        if action == "pause":
            success = await coordinator.pause_animation(animation_id)
        elif action == "resume":
            success = await coordinator.resume_animation(animation_id)
        elif action == "cancel":
            success = await coordinator.cancel_animation(animation_id)
        else:
            raise HTTPException(status_code=400, detail="不支持的動作")
        
        return JSONResponse(content={
            "success": success,
            "action": action,
            "animation_id": animation_id,
            "message": f"動畫 {action} {'成功' if success else '失敗'}",
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("動畫控制失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/animation/status/{animation_id}")
async def get_animation_status(
    animation_id: str,
    coordinator: Handover3DCoordinator = Depends(get_visualization_coordinator)
):
    """獲取動畫狀態"""
    try:
        state = coordinator.get_animation_state(animation_id)
        
        if state is None:
            raise HTTPException(status_code=404, detail="動畫不存在")
        
        return JSONResponse(content={
            "animation_id": state.animation_id,
            "status": state.status,
            "progress": state.progress,
            "start_time": state.start_time,
            "duration": state.duration,
            "parameters": state.parameters,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("獲取動畫狀態失敗", animation_id=animation_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/animation/list")
async def list_active_animations(
    coordinator: Handover3DCoordinator = Depends(get_visualization_coordinator)
):
    """列出所有活躍動畫"""
    try:
        active_animations = coordinator.get_active_animations()
        
        animations = []
        for state in active_animations:
            animations.append({
                "animation_id": state.animation_id,
                "status": state.status,
                "progress": state.progress,
                "start_time": state.start_time,
                "duration": state.duration,
            })
        
        return JSONResponse(content={
            "active_animations": animations,
            "total_count": len(animations),
        })
        
    except Exception as e:
        logger.error("列出活躍動畫失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# RL 監控端點
@router.get("/rl/training-status")
async def get_rl_training_status(
    rl_bridge: RLMonitorBridge = Depends(get_rl_bridge)
):
    """獲取 RL 訓練狀態"""
    try:
        status = await rl_bridge.get_training_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error("獲取 RL 訓練狀態失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rl/algorithm-metrics/{algorithm}")
async def get_algorithm_metrics(
    algorithm: str,
    rl_bridge: RLMonitorBridge = Depends(get_rl_bridge)
):
    """獲取算法指標"""
    try:
        metrics = await rl_bridge.get_algorithm_metrics(algorithm)
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error("獲取算法指標失敗", algorithm=algorithm, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rl/notify-training")
async def notify_training_update(
    training_data: Dict[str, Any],
    rl_bridge: RLMonitorBridge = Depends(get_rl_bridge)
):
    """通知訓練更新"""
    try:
        algorithm = training_data.get("algorithm")
        metrics = training_data.get("metrics", {})
        
        if not algorithm:
            raise HTTPException(status_code=400, detail="缺少算法名稱")
        
        await rl_bridge.notify_training_update(algorithm, metrics)
        
        return JSONResponse(content={
            "success": True,
            "message": "訓練更新通知已發送",
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("通知訓練更新失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# 同步管理端點
@router.post("/sync/create-group")
async def create_animation_group(
    group_request: Dict[str, Any],
    sync_manager: AnimationSyncManager = Depends(get_sync_manager)
):
    """創建動畫組"""
    try:
        group_id = group_request.get("group_id")
        animations = group_request.get("animations", [])
        sync_mode = group_request.get("sync_mode", "sequential")
        
        if not group_id or not animations:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        from .animation_sync_manager import SyncMode
        mode = SyncMode(sync_mode)
        
        group = sync_manager.create_animation_group(
            group_id=group_id,
            animations=animations,
            sync_mode=mode,
            priority=group_request.get("priority", 0),
            conditions=group_request.get("conditions", {}),
            start_delay=group_request.get("start_delay", 0.0),
        )
        
        return JSONResponse(content={
            "success": True,
            "group_id": group.group_id,
            "message": "動畫組創建成功",
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("創建動畫組失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/execute-group/{group_id}")
async def execute_animation_group(
    group_id: str,
    sync_manager: AnimationSyncManager = Depends(get_sync_manager)
):
    """執行動畫組"""
    try:
        success = await sync_manager.execute_animation_group(group_id)
        
        return JSONResponse(content={
            "success": success,
            "group_id": group_id,
            "message": f"動畫組執行{'成功' if success else '失敗'}",
        })
        
    except Exception as e:
        logger.error("執行動畫組失敗", group_id=group_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# 統計端點
@router.get("/stats/connection")
async def get_connection_stats(
    event_streamer: RealtimeEventStreamer = Depends(get_event_streamer)
):
    """獲取連接統計"""
    try:
        stats = await event_streamer.get_connection_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error("獲取連接統計失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/events")
async def get_event_stats(
    limit: int = 100,
    event_streamer: RealtimeEventStreamer = Depends(get_event_streamer)
):
    """獲取事件統計"""
    try:
        history = await event_streamer.get_event_history(limit)
        
        # 統計事件類型
        event_types = {}
        for event in history:
            event_type = event.event_type
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        return JSONResponse(content={
            "total_events": len(history),
            "event_types": event_types,
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "priority": event.priority,
                }
                for event in history[-10:]  # 最近10個事件
            ],
        })
        
    except Exception as e:
        logger.error("獲取事件統計失敗", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# 健康檢查端點
@router.get("/health")
async def health_check():
    """健康檢查"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": 1640995200.0,
        "components": {
            "event_streamer": "active",
            "visualization_coordinator": "active",
            "rl_bridge": "active",
            "sync_manager": "active",
        },
    })


class VisualizationAPI:
    """視覺化 API 管理器"""
    
    def __init__(self, event_streamer: RealtimeEventStreamer,
                 coordinator: Handover3DCoordinator,
                 rl_bridge: RLMonitorBridge,
                 sync_manager: AnimationSyncManager):
        """
        初始化視覺化 API
        
        Args:
            event_streamer: 事件推送器
            coordinator: 視覺化協調器
            rl_bridge: RL 監控橋接器
            sync_manager: 同步管理器
        """
        global _event_streamer, _coordinator, _rl_bridge, _sync_manager
        
        _event_streamer = event_streamer
        _coordinator = coordinator
        _rl_bridge = rl_bridge
        _sync_manager = sync_manager
        
        self.logger = logger.bind(component="visualization_api")
        self.logger.info("視覺化 API 初始化完成")
    
    def get_router(self) -> APIRouter:
        """獲取 API 路由器"""
        return router