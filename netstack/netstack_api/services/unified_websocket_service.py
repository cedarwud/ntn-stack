"""
統一 WebSocket 推送服務

整合 RL 系統和其他服務的事件推送，提供統一的實時通信機制
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class EventType(Enum):
    """事件類型"""

    # RL 系統事件
    RL_TRAINING_STARTED = "rl_training_started"
    RL_TRAINING_STOPPED = "rl_training_stopped"
    RL_TRAINING_PROGRESS = "rl_training_progress"
    RL_TRAINING_COMPLETED = "rl_training_completed"
    RL_TRAINING_ERROR = "rl_training_error"
    RL_METRICS_UPDATE = "rl_metrics_update"

    # 網路狀態事件
    NETWORK_STATUS_UPDATE = "network_status_update"
    HANDOVER_EVENT = "handover_event"
    SATELLITE_POSITION_UPDATE = "satellite_position_update"
    UAV_TELEMETRY_UPDATE = "uav_telemetry_update"

    # 系統事件
    SYSTEM_HEALTH_UPDATE = "system_health_update"
    SYSTEM_ALERT = "system_alert"

    # 連接事件
    CONNECTION_ESTABLISHED = "connection_established"
    HEARTBEAT = "heartbeat"


@dataclass
class WebSocketEvent:
    """WebSocket 事件"""

    event_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    priority: int = 0
    channel: Optional[str] = None


class WebSocketConnection:
    """WebSocket 連接管理"""

    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
        self.subscribed_channels: Set[str] = set()
        self.client_info: Dict[str, Any] = {}
        self.is_active = True
        self.events_sent = 0
        self.events_received = 0

    async def send_event(self, event: WebSocketEvent) -> bool:
        """
        發送事件到客戶端

        Args:
            event: 要發送的事件

        Returns:
            bool: 是否發送成功
        """
        try:
            message = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source,
                "priority": event.priority,
                "channel": event.channel,
            }

            await self.websocket.send_text(json.dumps(message))
            self.events_sent += 1
            return True

        except Exception as e:
            logger.error(f"事件發送失敗 (連接 {self.connection_id}): {e}")
            self.is_active = False
            return False

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        發送原始消息到客戶端

        Args:
            message: 要發送的消息

        Returns:
            bool: 是否發送成功
        """
        try:
            await self.websocket.send_text(json.dumps(message))
            return True

        except Exception as e:
            logger.error(f"消息發送失敗 (連接 {self.connection_id}): {e}")
            self.is_active = False
            return False

    def subscribe_channel(self, channel: str):
        """訂閱頻道"""
        self.subscribed_channels.add(channel)

    def unsubscribe_channel(self, channel: str):
        """取消訂閱頻道"""
        self.subscribed_channels.discard(channel)

    def is_subscribed(self, channel: str) -> bool:
        """檢查是否訂閱了頻道"""
        return channel in self.subscribed_channels

    async def close(self):
        """關閉連接"""
        try:
            await self.websocket.close()
        except:
            pass
        self.is_active = False


class UnifiedWebSocketService:
    """
    統一 WebSocket 推送服務

    提供統一的實時通信機制，整合 RL 系統和其他服務的事件推送
    """

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_events_sent": 0,
            "total_events_received": 0,
            "channels_count": 0,
        }

        # 心跳配置
        self.heartbeat_interval = 30  # 秒
        self.heartbeat_task = None

        # 事件隊列
        self.event_queue = asyncio.Queue()
        self.event_processor_task = None

        # 狀態
        self.is_running = False

    async def start(self):
        """啟動服務"""
        if self.is_running:
            return

        self.is_running = True

        # 啟動心跳任務
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # 啟動事件處理器
        self.event_processor_task = asyncio.create_task(self._process_events())

        logger.info("統一 WebSocket 推送服務已啟動")

    async def stop(self):
        """停止服務"""
        if not self.is_running:
            return

        self.is_running = False

        # 停止任務
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.event_processor_task:
            self.event_processor_task.cancel()

        # 關閉所有連接
        for connection in list(self.connections.values()):
            await connection.close()

        self.connections.clear()
        self.channels.clear()

        logger.info("統一 WebSocket 推送服務已停止")

    async def register_connection(
        self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        註冊新的 WebSocket 連接

        Args:
            websocket: WebSocket 連接
            client_info: 客戶端信息

        Returns:
            str: 連接 ID
        """
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(websocket, connection_id)

        if client_info:
            connection.client_info = client_info

        self.connections[connection_id] = connection
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.connections)

        # 發送歡迎消息
        welcome_event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CONNECTION_ESTABLISHED,
            timestamp=datetime.now(),
            data={
                "connection_id": connection_id,
                "server_info": {
                    "version": "1.0.0",
                    "supported_events": [e.value for e in EventType],
                },
            },
            source="websocket_service",
        )

        await connection.send_event(welcome_event)

        logger.info(f"新連接註冊: {connection_id}", client_info=client_info)
        return connection_id

    async def unregister_connection(self, connection_id: str):
        """
        取消註冊連接

        Args:
            connection_id: 連接 ID
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # 從所有頻道中移除
            for channel in list(connection.subscribed_channels):
                self.unsubscribe_channel(connection_id, channel)

            # 關閉連接
            await connection.close()

            # 移除連接
            del self.connections[connection_id]
            self.stats["active_connections"] = len(self.connections)

            logger.info(f"連接已取消註冊: {connection_id}")

    async def broadcast_event(self, event: WebSocketEvent):
        """
        廣播事件到所有連接

        Args:
            event: 要廣播的事件
        """
        await self.event_queue.put(("broadcast", event))

    async def send_to_channel(self, channel: str, event: WebSocketEvent):
        """
        發送事件到特定頻道

        Args:
            channel: 頻道名稱
            event: 要發送的事件
        """
        event.channel = channel
        await self.event_queue.put(("channel", channel, event))

    async def send_to_connection(self, connection_id: str, event: WebSocketEvent):
        """
        發送事件到特定連接

        Args:
            connection_id: 連接 ID
            event: 要發送的事件
        """
        await self.event_queue.put(("connection", connection_id, event))

    def subscribe_channel(self, connection_id: str, channel: str):
        """
        訂閱頻道

        Args:
            connection_id: 連接 ID
            channel: 頻道名稱
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscribe_channel(channel)

            # 更新頻道映射
            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(connection_id)

            self.stats["channels_count"] = len(self.channels)

            logger.info(f"連接 {connection_id} 訂閱頻道: {channel}")

    def unsubscribe_channel(self, connection_id: str, channel: str):
        """
        取消訂閱頻道

        Args:
            connection_id: 連接 ID
            channel: 頻道名稱
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.unsubscribe_channel(channel)

            # 更新頻道映射
            if channel in self.channels:
                self.channels[channel].discard(connection_id)
                if not self.channels[channel]:
                    del self.channels[channel]

            self.stats["channels_count"] = len(self.channels)

            logger.info(f"連接 {connection_id} 取消訂閱頻道: {channel}")

    def register_event_handler(self, event_type: EventType, handler: Callable):
        """
        註冊事件處理器

        Args:
            event_type: 事件類型
            handler: 處理函數
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def _process_events(self):
        """處理事件隊列"""
        while self.is_running:
            try:
                # 獲取事件
                event_data = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                if event_data[0] == "broadcast":
                    await self._broadcast_event(event_data[1])
                elif event_data[0] == "channel":
                    await self._send_to_channel(event_data[1], event_data[2])
                elif event_data[0] == "connection":
                    await self._send_to_connection(event_data[1], event_data[2])

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"事件處理錯誤: {e}")

    async def _broadcast_event(self, event: WebSocketEvent):
        """廣播事件實現"""
        failed_connections = []

        for connection_id, connection in self.connections.items():
            if connection.is_active:
                success = await connection.send_event(event)
                if not success:
                    failed_connections.append(connection_id)

        # 清理失敗的連接
        for connection_id in failed_connections:
            await self.unregister_connection(connection_id)

        self.stats["total_events_sent"] += len(self.connections) - len(
            failed_connections
        )

    async def _send_to_channel(self, channel: str, event: WebSocketEvent):
        """發送到頻道實現"""
        if channel not in self.channels:
            return

        failed_connections = []
        sent_count = 0

        for connection_id in self.channels[channel]:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_active:
                    success = await connection.send_event(event)
                    if success:
                        sent_count += 1
                    else:
                        failed_connections.append(connection_id)

        # 清理失敗的連接
        for connection_id in failed_connections:
            await self.unregister_connection(connection_id)

        self.stats["total_events_sent"] += sent_count

    async def _send_to_connection(self, connection_id: str, event: WebSocketEvent):
        """發送到特定連接實現"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            if connection.is_active:
                success = await connection.send_event(event)
                if success:
                    self.stats["total_events_sent"] += 1
                else:
                    await self.unregister_connection(connection_id)

    async def _heartbeat_loop(self):
        """心跳循環"""
        while self.is_running:
            try:
                # 發送心跳到所有連接
                heartbeat_event = WebSocketEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.HEARTBEAT,
                    timestamp=datetime.now(),
                    data={"server_time": datetime.now().isoformat()},
                    source="websocket_service",
                )

                await self.broadcast_event(heartbeat_event)

                # 等待下次心跳
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"心跳循環錯誤: {e}")
                await asyncio.sleep(5)

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            "connections": {
                conn_id: {
                    "connection_id": conn.connection_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscribed_channels": list(conn.subscribed_channels),
                    "events_sent": conn.events_sent,
                    "events_received": conn.events_received,
                    "is_active": conn.is_active,
                }
                for conn_id, conn in self.connections.items()
            },
            "channels": {
                channel: len(connection_ids)
                for channel, connection_ids in self.channels.items()
            },
        }


# 全局服務實例
_websocket_service = None


def get_websocket_service() -> UnifiedWebSocketService:
    """
    獲取統一 WebSocket 服務實例

    Returns:
        UnifiedWebSocketService: 服務實例
    """
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = UnifiedWebSocketService()
    return _websocket_service


# RL 系統事件推送輔助函數
async def push_rl_training_event(
    event_type: EventType, data: Dict[str, Any], source: str = "rl_system"
):
    """
    推送 RL 訓練事件

    Args:
        event_type: 事件類型
        data: 事件數據
        source: 事件源
    """
    service = get_websocket_service()

    event = WebSocketEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        data=data,
        source=source,
        channel="rl_training",
    )

    await service.send_to_channel("rl_training", event)


async def push_system_event(
    event_type: EventType, data: Dict[str, Any], source: str = "system"
):
    """
    推送系統事件

    Args:
        event_type: 事件類型
        data: 事件數據
        source: 事件源
    """
    service = get_websocket_service()

    event = WebSocketEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        data=data,
        source=source,
    )

    await service.broadcast_event(event)
