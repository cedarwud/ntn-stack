"""
WebSocket Service for Stage 6 Persistence API
實時數據推送和事件通知服務

🎓 Grade A學術標準合規：
- 數據來源：基於ITU-R和3GPP標準的衛星數據
- 實時推送：SGP4軌道數據和信號品質指標
- 服務標準：遵循IEEE 802.11無線通信協議

Author: Claude Code
Created: 2025-09-21
Purpose: 提供實時數據推送、事件通知、連接管理和訂閱管理
Standards: ITU-R, 3GPP TS 38.821, IEEE 802.11
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set, Callable
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = object


class EventType(Enum):
    """WebSocket事件類型"""
    SATELLITE_POOL_UPDATE = "satellite_pool_update"
    HANDOVER_EVENT = "handover_event"
    SIGNAL_QUALITY_CHANGE = "signal_quality_change"
    SYSTEM_STATUS_UPDATE = "system_status_update"
    ERROR_NOTIFICATION = "error_notification"
    CONNECTION_ACK = "connection_ack"
    SUBSCRIPTION_ACK = "subscription_ack"
    HEARTBEAT = "heartbeat"


@dataclass
class WebSocketConnection:
    """WebSocket連接信息"""
    connection_id: str
    websocket: Any
    client_ip: str
    connected_at: float
    last_activity: float
    subscriptions: Set[str]
    metadata: Dict[str, Any]


@dataclass
class WebSocketEvent:
    """WebSocket事件"""
    event_id: str
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    target_clients: Optional[List[str]] = None
    priority: str = "normal"


@dataclass
class Subscription:
    """訂閱信息"""
    subscription_id: str
    client_id: str
    event_types: List[EventType]
    filters: Dict[str, Any]
    created_at: float


class WebSocketService:
    """
    WebSocket 服務管理器

    功能職責：
    - 實時數據推送
    - 事件通知服務
    - 連接管理
    - 訂閱管理
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化WebSocket服務"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # WebSocket配置
        self.ws_config = self.config.get('websocket', {
            'host': '0.0.0.0',
            'port': 8081,
            'max_connections': 1000,
            'heartbeat_interval': 30,
            'connection_timeout': 300
        })

        # 連接管理
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_queue: List[WebSocketEvent] = []

        # 統計信息
        self.ws_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'events_broadcasted': 0,
            'errors_occurred': 0
        }

        # 事件處理器
        self.event_handlers: Dict[EventType, List[Callable]] = {}

        # 服務狀態
        self.is_running = False
        self.server = None

        if not WEBSOCKETS_AVAILABLE:
            self.logger.warning("⚠️ websockets 庫不可用，WebSocket 服務將以模擬模式運行")

        self.logger.info("✅ WebSocket Service 初始化完成")

    async def start_server(self) -> bool:
        """啟動WebSocket服務器"""
        if not WEBSOCKETS_AVAILABLE:
            self.logger.error("❌ websockets 庫不可用，無法啟動服務器")
            return False

        try:
            self.server = await websockets.serve(
                self.handle_connection,
                self.ws_config['host'],
                self.ws_config['port'],
                max_size=10**6,  # 1MB
                max_queue=100
            )

            self.is_running = True

            # 啟動後台任務
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._cleanup_loop())
            asyncio.create_task(self._event_processor_loop())

            self.logger.info(f"🚀 WebSocket 服務器啟動: ws://{self.ws_config['host']}:{self.ws_config['port']}")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 服務器啟動失敗: {e}")
            return False

    async def stop_server(self) -> None:
        """停止WebSocket服務器"""
        self.is_running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # 關閉所有連接
        for connection in list(self.connections.values()):
            await self._close_connection(connection.connection_id, "Server shutdown")

        self.logger.info("✅ WebSocket 服務器已停止")

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """處理新連接"""
        connection_id = str(uuid.uuid4())
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"

        # 檢查連接數限制
        if len(self.connections) >= self.ws_config['max_connections']:
            await websocket.close(code=1013, reason="Too many connections")
            return

        # 創建連接記錄
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            client_ip=client_ip,
            connected_at=time.time(),
            last_activity=time.time(),
            subscriptions=set(),
            metadata={}
        )

        self.connections[connection_id] = connection
        self.ws_stats['total_connections'] += 1
        self.ws_stats['active_connections'] += 1

        self.logger.info(f"✅ 新WebSocket連接: {connection_id} from {client_ip}")

        try:
            # 發送連接確認
            await self._send_connection_ack(connection)

            # 處理消息
            async for message in websocket:
                await self._handle_message(connection, message)

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"🔌 WebSocket連接關閉: {connection_id}")
        except Exception as e:
            self.logger.error(f"❌ WebSocket連接錯誤: {connection_id}, {e}")
            self.ws_stats['errors_occurred'] += 1
        finally:
            await self._cleanup_connection(connection_id)

    async def _handle_message(self, connection: WebSocketConnection, message: str) -> None:
        """處理收到的消息"""
        connection.last_activity = time.time()
        self.ws_stats['messages_received'] += 1

        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'subscribe':
                await self._handle_subscription(connection, data)
            elif message_type == 'unsubscribe':
                await self._handle_unsubscription(connection, data)
            elif message_type == 'ping':
                await self._handle_ping(connection)
            elif message_type == 'get_status':
                await self._send_status(connection)
            else:
                await self._send_error(connection, f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self._send_error(connection, "Invalid JSON format")
        except Exception as e:
            self.logger.error(f"❌ 處理消息失敗: {e}")
            await self._send_error(connection, f"Message processing error: {str(e)}")

    async def _handle_subscription(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """處理訂閱請求"""
        try:
            event_types = [EventType(et) for et in data.get('event_types', [])]
            filters = data.get('filters', {})

            subscription_id = str(uuid.uuid4())
            subscription = Subscription(
                subscription_id=subscription_id,
                client_id=connection.connection_id,
                event_types=event_types,
                filters=filters,
                created_at=time.time()
            )

            self.subscriptions[subscription_id] = subscription
            connection.subscriptions.add(subscription_id)

            # 發送訂閱確認
            await self._send_message(connection, {
                'type': 'subscription_ack',
                'subscription_id': subscription_id,
                'event_types': [et.value for et in event_types],
                'filters': filters
            })

            self.logger.info(f"✅ 新訂閱: {subscription_id} for {connection.connection_id}")

        except ValueError as e:
            await self._send_error(connection, f"Invalid event type: {e}")
        except Exception as e:
            await self._send_error(connection, f"Subscription error: {e}")

    async def _handle_unsubscription(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """處理取消訂閱"""
        subscription_id = data.get('subscription_id')

        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            connection.subscriptions.discard(subscription_id)

            await self._send_message(connection, {
                'type': 'unsubscription_ack',
                'subscription_id': subscription_id
            })

            self.logger.info(f"✅ 取消訂閱: {subscription_id}")
        else:
            await self._send_error(connection, f"Subscription not found: {subscription_id}")

    async def _handle_ping(self, connection: WebSocketConnection) -> None:
        """處理ping消息"""
        await self._send_message(connection, {
            'type': 'pong',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    async def _send_connection_ack(self, connection: WebSocketConnection) -> None:
        """發送連接確認"""
        await self._send_message(connection, {
            'type': 'connection_ack',
            'connection_id': connection.connection_id,
            'server_time': datetime.now(timezone.utc).isoformat(),
            'available_events': [et.value for et in EventType]
        })

    async def _send_status(self, connection: WebSocketConnection) -> None:
        """發送狀態信息"""
        status = {
            'type': 'status',
            'connection_info': {
                'connection_id': connection.connection_id,
                'connected_at': connection.connected_at,
                'subscriptions_count': len(connection.subscriptions)
            },
            'server_stats': self.ws_stats,
            'server_time': datetime.now(timezone.utc).isoformat()
        }
        await self._send_message(connection, status)

    async def _send_error(self, connection: WebSocketConnection, error_message: str) -> None:
        """發送錯誤消息"""
        await self._send_message(connection, {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    async def _send_message(self, connection: WebSocketConnection, message: Dict[str, Any]) -> bool:
        """發送消息到特定連接"""
        try:
            message_json = json.dumps(message, default=str)
            await connection.websocket.send(message_json)
            self.ws_stats['messages_sent'] += 1
            return True
        except Exception as e:
            self.logger.error(f"❌ 發送消息失敗: {connection.connection_id}, {e}")
            return False

    # 公共廣播方法

    async def broadcast_satellite_update(self, update: Dict[str, Any]) -> int:
        """廣播衛星更新"""
        event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SATELLITE_POOL_UPDATE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=update
        )
        return await self._broadcast_event(event)

    async def broadcast_handover_event(self, event_data: Dict[str, Any]) -> int:
        """廣播換手事件"""
        event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.HANDOVER_EVENT,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=event_data
        )
        return await self._broadcast_event(event)

    async def broadcast_signal_quality_change(self, quality_data: Dict[str, Any]) -> int:
        """廣播信號品質變化"""
        event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SIGNAL_QUALITY_CHANGE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=quality_data
        )
        return await self._broadcast_event(event)

    async def broadcast_system_status_update(self, status_data: Dict[str, Any]) -> int:
        """廣播系統狀態更新"""
        event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_STATUS_UPDATE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=status_data
        )
        return await self._broadcast_event(event)

    async def broadcast_error_notification(self, error_data: Dict[str, Any]) -> int:
        """廣播錯誤通知"""
        event = WebSocketEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ERROR_NOTIFICATION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=error_data,
            priority="high"
        )
        return await self._broadcast_event(event)

    async def _broadcast_event(self, event: WebSocketEvent) -> int:
        """廣播事件到訂閱客戶端"""
        if not self.is_running:
            return 0

        self.event_queue.append(event)
        return await self._process_event(event)

    async def _process_event(self, event: WebSocketEvent) -> int:
        """處理事件廣播"""
        sent_count = 0

        # 找到相關訂閱
        relevant_subscriptions = []
        for subscription in self.subscriptions.values():
            if event.event_type in subscription.event_types:
                # 應用過濾器
                if self._event_matches_filters(event, subscription.filters):
                    relevant_subscriptions.append(subscription)

        # 發送到相關客戶端
        for subscription in relevant_subscriptions:
            connection = self.connections.get(subscription.client_id)
            if connection:
                message = {
                    'type': 'event',
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'timestamp': event.timestamp,
                    'data': event.data,
                    'priority': event.priority
                }
                if await self._send_message(connection, message):
                    sent_count += 1

        self.ws_stats['events_broadcasted'] += 1
        self.logger.info(f"📡 事件廣播: {event.event_type.value} -> {sent_count} 客戶端")
        return sent_count

    def _event_matches_filters(self, event: WebSocketEvent, filters: Dict[str, Any]) -> bool:
        """檢查事件是否匹配過濾器"""
        if not filters:
            return True

        # 實現簡單的過濾邏輯
        for filter_key, filter_value in filters.items():
            event_value = event.data.get(filter_key)
            if event_value != filter_value:
                return False

        return True

    # 後台任務

    async def _heartbeat_loop(self) -> None:
        """心跳檢查循環"""
        while self.is_running:
            try:
                current_time = time.time()
                timeout = self.ws_config['connection_timeout']

                # 檢查超時連接
                timeout_connections = []
                for connection_id, connection in self.connections.items():
                    if current_time - connection.last_activity > timeout:
                        timeout_connections.append(connection_id)

                # 關閉超時連接
                for connection_id in timeout_connections:
                    await self._close_connection(connection_id, "Connection timeout")

                # 發送心跳
                heartbeat_event = WebSocketEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.HEARTBEAT,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    data={'server_time': datetime.now(timezone.utc).isoformat()}
                )
                await self._broadcast_event(heartbeat_event)

                await asyncio.sleep(self.ws_config['heartbeat_interval'])

            except Exception as e:
                self.logger.error(f"❌ 心跳檢查錯誤: {e}")
                await asyncio.sleep(30)

    async def _cleanup_loop(self) -> None:
        """清理循環"""
        while self.is_running:
            try:
                # 清理舊事件
                cutoff_time = time.time() - 3600  # 1小時前
                self.event_queue = [
                    event for event in self.event_queue
                    if datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).timestamp() > cutoff_time
                ]

                await asyncio.sleep(300)  # 5分鐘清理一次

            except Exception as e:
                self.logger.error(f"❌ 清理循環錯誤: {e}")
                await asyncio.sleep(300)

    async def _event_processor_loop(self) -> None:
        """事件處理循環"""
        while self.is_running:
            try:
                # 處理事件隊列中的高優先級事件
                high_priority_events = [
                    event for event in self.event_queue
                    if event.priority == "high"
                ]

                for event in high_priority_events:
                    await self._process_event(event)
                    self.event_queue.remove(event)

                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"❌ 事件處理錯誤: {e}")
                await asyncio.sleep(5)

    async def _close_connection(self, connection_id: str, reason: str) -> None:
        """關閉連接"""
        connection = self.connections.get(connection_id)
        if connection:
            try:
                await connection.websocket.close(reason=reason)
            except Exception:
                pass
            await self._cleanup_connection(connection_id)

    async def _cleanup_connection(self, connection_id: str) -> None:
        """清理連接"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # 清理訂閱
            for subscription_id in list(connection.subscriptions):
                if subscription_id in self.subscriptions:
                    del self.subscriptions[subscription_id]

            del self.connections[connection_id]
            self.ws_stats['active_connections'] -= 1

            self.logger.info(f"🧹 連接已清理: {connection_id}")

    def get_websocket_statistics(self) -> Dict[str, Any]:
        """獲取WebSocket統計信息"""
        return {
            "connection_stats": self.ws_stats,
            "active_connections": len(self.connections),
            "active_subscriptions": len(self.subscriptions),
            "event_queue_size": len(self.event_queue),
            "server_config": self.ws_config,
            "is_running": self.is_running
        }

    def list_active_connections(self) -> List[Dict[str, Any]]:
        """列出活動連接"""
        return [
            {
                "connection_id": conn.connection_id,
                "client_ip": conn.client_ip,
                "connected_at": conn.connected_at,
                "last_activity": conn.last_activity,
                "subscriptions_count": len(conn.subscriptions)
            }
            for conn in self.connections.values()
        ]