"""
WebSocket 路由器

提供統一的 WebSocket 端點，支援 RL 訓練和系統狀態的實時推送
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse

from ..services.unified_websocket_service import get_websocket_service

logger = logging.getLogger(__name__)

# 創建 WebSocket 路由器
websocket_router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket"])


@websocket_router.websocket("/rl")
async def websocket_rl_endpoint(websocket: WebSocket, channel: Optional[str] = Query(None)):
    """
    RL 系統 WebSocket 端點
    
    支援實時推送 RL 訓練狀態、進度和結果
    """
    service = get_websocket_service()
    connection_id = None
    
    try:
        await websocket.accept()
        logger.info("WebSocket 連接建立")
        
        # 註冊連接
        connection_id = await service.register_connection(
            websocket,
            {"type": "rl_client", "endpoint": "/api/v1/ws/rl"}
        )
        
        # 訂閱 RL 訓練頻道
        if channel:
            service.subscribe_channel(connection_id, channel)
        else:
            # RL training channel subscription removed
            service.subscribe_channel(connection_id, "system")
        
        # 保持連接並處理客戶端消息
        while True:
            try:
                # 接收客戶端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 處理客戶端訂閱請求
                if message.get("type") == "subscribe":
                    channel_name = message.get("channel")
                    if channel_name:
                        service.subscribe_channel(connection_id, channel_name)
                        await websocket.send_text(json.dumps({
                            "type": "subscription_confirmed",
                            "channel": channel_name,
                            "timestamp": service.connections[connection_id].connected_at.isoformat()
                        }))
                        
                elif message.get("type") == "unsubscribe":
                    channel_name = message.get("channel")
                    if channel_name:
                        service.unsubscribe_channel(connection_id, channel_name)
                        await websocket.send_text(json.dumps({
                            "type": "unsubscription_confirmed",
                            "channel": channel_name
                        }))
                        
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": logger.info("收到客戶端 ping")
                    }))
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"處理 WebSocket 消息錯誤: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket 連接關閉: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}")
    finally:
        if connection_id:
            await service.unregister_connection(connection_id)


@websocket_router.websocket("/system")
async def websocket_system_endpoint(websocket: WebSocket):
    """
    系統狀態 WebSocket 端點
    
    支援實時推送系統健康狀態、警報和監控數據
    """
    service = get_websocket_service()
    connection_id = None
    
    try:
        await websocket.accept()
        logger.info("系統 WebSocket 連接建立")
        
        # 註冊連接
        connection_id = await service.register_connection(
            websocket,
            {"type": "system_client", "endpoint": "/api/v1/ws/system"}
        )
        
        # 訂閱系統頻道
        service.subscribe_channel(connection_id, "system")
        service.subscribe_channel(connection_id, "network")
        
        # 保持連接
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "get_stats":
                    stats = service.get_stats()
                    await websocket.send_text(json.dumps({
                        "type": "stats",
                        "data": stats
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"處理系統 WebSocket 消息錯誤: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"系統 WebSocket 連接關閉: {connection_id}")
    except Exception as e:
        logger.error(f"系統 WebSocket 錯誤: {e}")
    finally:
        if connection_id:
            await service.unregister_connection(connection_id)


@websocket_router.get("/stats")
async def get_websocket_stats():
    """獲取 WebSocket 服務統計信息"""
    try:
        service = get_websocket_service()
        stats = service.get_stats()
        
        return JSONResponse(content={
            "status": "success",
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"獲取 WebSocket 統計失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@websocket_router.get("/channels")
async def get_websocket_channels():
    """獲取可用的 WebSocket 頻道"""
    return JSONResponse(content={
        "status": "success",
        "channels": [
            # RL training channel removed
            {
                "name": "system",
                "description": "系統狀態和健康監控",
                "events": [
                    "system_health_update",
                    "system_alert"
                ]
            },
            {
                "name": "network",
                "description": "網路狀態和換手事件",
                "events": [
                    "network_status_update",
                    "handover_event",
                    "satellite_position_update",
                    "uav_telemetry_update"
                ]
            }
        ]
    })