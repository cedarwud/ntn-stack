"""
即時事件推送系統
===============

提供 WebSocket 即時事件推送功能，支援多客戶端連接。
"""

import asyncio
import json
import logging
import websockets
from typing import Set, Dict, Any, Optional, List
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class EventMessage:
    """事件消息結構"""
    event_id: str
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    priority: int = 0
    retry_count: int = 0


class RealtimeEventStreamer:
    """
    即時事件推送器
    
    提供 WebSocket 即時事件推送功能：
    - 多客戶端連接管理
    - 事件廣播
    - 連接狀態監控
    - 自動重連處理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化即時事件推送器
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logger.bind(component="realtime_event_streamer")
        
        # WebSocket 連接管理
        self.websocket_connections: Set[websockets.WebSocketServerProtocol] = set()
        self.connection_info: Dict[str, Dict[str, Any]] = {}  # connection_id -> info
        
        # 事件隊列和歷史
        self.event_queue: deque = deque(maxlen=1000)
        self.event_history: deque = deque(maxlen=5000)
        self.failed_events: deque = deque(maxlen=100)
        
        # 統計信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_events_sent": 0,
            "failed_events": 0,
            "last_event_time": 0.0,
        }
        
        # 配置參數
        self.max_connections = self.config.get("max_connections", 100)
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30.0)
        self.max_retry_attempts = self.config.get("max_retry_attempts", 3)
        self.event_buffer_size = self.config.get("event_buffer_size", 1000)
        
        # 心跳任務
        self.heartbeat_task = None
        self.is_running = False
        
        self.logger.info("即時事件推送器初始化完成")

    async def start(self):
        """啟動推送器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self.logger.info("即時事件推送器已啟動")

    async def stop(self):
        """停止推送器"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 停止心跳任務
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 關閉所有連接
        for websocket in self.websocket_connections.copy():
            await websocket.close()
        
        self.logger.info("即時事件推送器已停止")

    async def register_connection(self, websocket: websockets.WebSocketServerProtocol,
                                client_info: Optional[Dict[str, Any]] = None):
        """
        註冊新的 WebSocket 連接
        
        Args:
            websocket: WebSocket 連接
            client_info: 客戶端信息
        """
        if len(self.websocket_connections) >= self.max_connections:
            self.logger.warning("達到最大連接數限制")
            await websocket.close(code=1013, reason="Too many connections")
            return
            
        # 生成連接ID
        connection_id = f"conn_{len(self.websocket_connections)}_{int(datetime.now().timestamp())}"
        
        # 註冊連接
        self.websocket_connections.add(websocket)
        self.connection_info[connection_id] = {
            "websocket": websocket,
            "client_info": client_info or {},
            "connected_at": datetime.now().timestamp(),
            "last_ping": datetime.now().timestamp(),
            "events_sent": 0,
        }
        
        # 更新統計
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.websocket_connections)
        
        # 發送歡迎消息
        welcome_message = {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.now().timestamp(),
            "server_info": {
                "version": "1.0.0",
                "features": ["realtime_events", "heartbeat", "event_history"],
            },
        }
        
        await self._send_to_connection(websocket, welcome_message)
        
        self.logger.info(
            "新連接註冊成功",
            connection_id=connection_id,
            client_info=client_info,
            total_connections=self.stats["active_connections"],
        )
        
        try:
            # 監聽連接
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # 清理連接
            await self._cleanup_connection(websocket, connection_id)

    async def broadcast_event(self, event: Dict[str, Any]):
        """
        廣播事件到所有連接的客戶端
        
        Args:
            event: 事件數據
        """
        if not self.websocket_connections:
            return
            
        # 創建事件消息
        event_message = EventMessage(
            event_id=f"event_{int(datetime.now().timestamp() * 1000)}",
            event_type=event.get("type", "unknown"),
            timestamp=datetime.now().timestamp(),
            data=event,
            priority=event.get("priority", 0),
        )
        
        # 添加到隊列和歷史
        self.event_queue.append(event_message)
        self.event_history.append(event_message)
        
        # 廣播到所有連接
        await self._broadcast_to_all(event_message)
        
        # 更新統計
        self.stats["total_events_sent"] += 1
        self.stats["last_event_time"] = datetime.now().timestamp()
        
        self.logger.debug(
            "事件廣播完成",
            event_id=event_message.event_id,
            event_type=event_message.event_type,
            connections=len(self.websocket_connections),
        )

    async def send_to_client(self, connection_id: str, event: Dict[str, Any]):
        """
        發送事件到特定客戶端
        
        Args:
            connection_id: 連接ID
            event: 事件數據
        """
        if connection_id not in self.connection_info:
            self.logger.warning("連接不存在", connection_id=connection_id)
            return
            
        websocket = self.connection_info[connection_id]["websocket"]
        
        event_message = EventMessage(
            event_id=f"event_{int(datetime.now().timestamp() * 1000)}",
            event_type=event.get("type", "unknown"),
            timestamp=datetime.now().timestamp(),
            data=event,
            priority=event.get("priority", 0),
        )
        
        await self._send_to_connection(websocket, asdict(event_message))

    async def get_event_history(self, limit: int = 100) -> List[EventMessage]:
        """
        獲取事件歷史
        
        Args:
            limit: 返回數量限制
            
        Returns:
            List[EventMessage]: 事件歷史列表
        """
        return list(self.event_history)[-limit:]

    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        獲取連接統計
        
        Returns:
            Dict[str, Any]: 連接統計信息
        """
        return {
            **self.stats,
            "connections": [
                {
                    "connection_id": conn_id,
                    "connected_at": info["connected_at"],
                    "last_ping": info["last_ping"],
                    "events_sent": info["events_sent"],
                    "client_info": info["client_info"],
                }
                for conn_id, info in self.connection_info.items()
            ],
        }

    async def ping_all_connections(self):
        """向所有連接發送心跳"""
        if not self.websocket_connections:
            return
            
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().timestamp(),
        }
        
        failed_connections = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send(json.dumps(ping_message))
            except websockets.exceptions.ConnectionClosed:
                failed_connections.append(websocket)
            except Exception as e:
                self.logger.error("心跳發送失敗", error=str(e))
                failed_connections.append(websocket)
        
        # 清理失敗的連接
        for websocket in failed_connections:
            await self._cleanup_connection(websocket)

    # 私有方法
    async def _broadcast_to_all(self, event_message: EventMessage):
        """廣播到所有連接"""
        if not self.websocket_connections:
            return
            
        message = json.dumps(asdict(event_message))
        failed_connections = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send(message)
                
                # 更新連接統計
                for conn_id, info in self.connection_info.items():
                    if info["websocket"] == websocket:
                        info["events_sent"] += 1
                        break
                        
            except websockets.exceptions.ConnectionClosed:
                failed_connections.append(websocket)
            except Exception as e:
                self.logger.error("事件發送失敗", error=str(e))
                failed_connections.append(websocket)
        
        # 清理失敗的連接
        for websocket in failed_connections:
            await self._cleanup_connection(websocket)
        
        # 記錄失敗事件
        if failed_connections:
            self.failed_events.append(event_message)
            self.stats["failed_events"] += len(failed_connections)

    async def _send_to_connection(self, websocket: websockets.WebSocketServerProtocol, 
                                message: Dict[str, Any]):
        """發送消息到特定連接"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            await self._cleanup_connection(websocket)
        except Exception as e:
            self.logger.error("消息發送失敗", error=str(e))
            await self._cleanup_connection(websocket)

    async def _cleanup_connection(self, websocket: websockets.WebSocketServerProtocol, 
                                connection_id: Optional[str] = None):
        """清理連接"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        
        # 清理連接信息
        if connection_id:
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]
        else:
            # 查找並刪除連接信息
            to_remove = []
            for conn_id, info in self.connection_info.items():
                if info["websocket"] == websocket:
                    to_remove.append(conn_id)
            
            for conn_id in to_remove:
                del self.connection_info[conn_id]
        
        # 更新統計
        self.stats["active_connections"] = len(self.websocket_connections)
        
        self.logger.debug(
            "連接已清理",
            connection_id=connection_id,
            remaining_connections=self.stats["active_connections"],
        )

    async def _heartbeat_loop(self):
        """心跳循環"""
        while self.is_running:
            try:
                await self.ping_all_connections()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("心跳循環異常", error=str(e))
                await asyncio.sleep(self.heartbeat_interval)

    async def stream_decision_update(self, decision):
        """推送決策更新"""
        await self.broadcast_event({
            "type": "decision_update",
            "decision": {
                "selected_satellite": decision.selected_satellite,
                "confidence": decision.confidence,
                "visualization_data": decision.visualization_data,
                "algorithm_used": decision.algorithm_used,
            },
            "timestamp": datetime.now().timestamp(),
        })

    async def stream_execution_update(self, execution_result):
        """推送執行更新"""
        await self.broadcast_event({
            "type": "execution_update",
            "execution_result": {
                "success": execution_result.success,
                "execution_time": execution_result.execution_time,
                "performance_metrics": execution_result.performance_metrics,
                "status": execution_result.status.value,
            },
            "timestamp": datetime.now().timestamp(),
        })

    async def stream_monitoring_update(self, monitoring_data):
        """推送監控更新"""
        await self.broadcast_event({
            "type": "monitoring_update",
            "monitoring_data": monitoring_data,
            "timestamp": datetime.now().timestamp(),
        })