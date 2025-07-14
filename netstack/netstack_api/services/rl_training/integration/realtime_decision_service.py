"""
Phase 2.3 實時決策服務

整合 WebSocket 推送實時決策狀態：
- 實時決策狀態廣播
- 算法性能監控
- 決策事件流處理
- 前端數據同步
- 性能儀表板支援
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from enum import Enum
import uuid

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

from .rl_algorithm_integrator import (
    RLAlgorithmIntegrator,
    AlgorithmType,
    AlgorithmDecision,
)
from .real_environment_bridge import (
    RealEnvironmentBridge,
    EnvironmentObservation,
    EnvironmentAction,
    EnvironmentReward,
)
from .decision_analytics_engine import DecisionAnalyticsEngine, DecisionRecord
from .multi_algorithm_comparator import MultiAlgorithmComparator

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket 消息類型"""

    # 狀態更新
    ALGORITHM_STATUS = "algorithm_status"
    ENVIRONMENT_STATUS = "environment_status"
    DECISION_UPDATE = "decision_update"

    # 性能監控
    PERFORMANCE_METRICS = "performance_metrics"
    REAL_TIME_STATS = "real_time_stats"

    # 決策事件
    DECISION_EVENT = "decision_event"
    HANDOVER_EVENT = "handover_event"
    TRIGGER_EVENT = "trigger_event"

    # 分析數據
    EXPLAINABILITY_DATA = "explainability_data"
    COMPARISON_RESULT = "comparison_result"

    # 控制命令
    ALGORITHM_SWITCH = "algorithm_switch"
    TEST_START = "test_start"
    TEST_STOP = "test_stop"

    # 系統事件
    CONNECTION_STATUS = "connection_status"
    ERROR_NOTIFICATION = "error_notification"
    SYSTEM_ALERT = "system_alert"


@dataclass
class WebSocketMessage:
    """WebSocket 消息格式"""

    message_type: MessageType
    timestamp: datetime
    data: Dict[str, Any]
    client_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ClientConnection:
    """客戶端連接資訊"""

    client_id: str
    websocket: Any  # WebSocket connection object
    connected_at: datetime
    last_activity: datetime
    subscriptions: Set[MessageType]
    metadata: Dict[str, Any]


@dataclass
class DecisionEvent:
    """決策事件"""

    event_id: str
    timestamp: datetime
    algorithm_type: AlgorithmType
    decision: AlgorithmDecision
    action: EnvironmentAction
    observation: EnvironmentObservation
    explanation: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceSnapshot:
    """性能快照"""

    timestamp: datetime
    algorithm_metrics: Dict[AlgorithmType, Dict[str, float]]
    environment_status: Dict[str, Any]
    system_metrics: Dict[str, float]


class RealtimeDecisionService:
    """實時決策服務"""

    def __init__(
        self,
        algorithm_integrator: RLAlgorithmIntegrator,
        environment_bridge: RealEnvironmentBridge,
        analytics_engine: DecisionAnalyticsEngine,
        comparator: MultiAlgorithmComparator,
        config: Dict[str, Any],
    ):
        """
        初始化實時決策服務

        Args:
            algorithm_integrator: RL算法整合器
            environment_bridge: 環境橋接器
            analytics_engine: 決策分析引擎
            comparator: 多算法比較器
            config: 服務配置
        """
        self.algorithm_integrator = algorithm_integrator
        self.environment_bridge = environment_bridge
        self.analytics_engine = analytics_engine
        self.comparator = comparator
        self.config = config

        # WebSocket 服務配置
        self.websocket_host = config.get("websocket_host", "localhost")
        self.websocket_port = config.get("websocket_port", 8765)
        self.max_connections = config.get("max_connections", 100)

        # 連接管理
        self.clients: Dict[str, ClientConnection] = {}
        self.websocket_server = None
        self.is_running = False

        # 事件處理
        self.event_handlers: Dict[MessageType, List[Callable]] = {}
        self.event_queue = asyncio.Queue()
        self.broadcast_queue = asyncio.Queue()

        # 性能監控
        self.performance_monitor_interval = config.get(
            "performance_monitor_interval", 5.0
        )
        self.performance_history: List[PerformanceSnapshot] = []
        self.max_performance_history = config.get("max_performance_history", 1000)

        # 決策事件記錄
        self.decision_events: List[DecisionEvent] = []
        self.max_decision_events = config.get("max_decision_events", 10000)

        # 統計
        self.total_messages_sent = 0
        self.total_clients_connected = 0
        self.service_start_time = None

        logger.info(f"實時決策服務初始化，WebSocket 端口: {self.websocket_port}")

    async def start_service(self) -> bool:
        """啟動實時決策服務"""
        try:
            logger.info("啟動實時決策服務...")

            if not WEBSOCKETS_AVAILABLE:
                logger.warning("WebSockets 庫不可用，實時決策服務將以模擬模式運行")
                self.is_running = True
                self.service_start_time = datetime.now()
                return True

            # 啟動 WebSocket 服務器
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                self.websocket_host,
                self.websocket_port,
                max_size=1024 * 1024,  # 1MB
                ping_timeout=20,
                ping_interval=10,
            )

            # 啟動後台任務
            asyncio.create_task(self._event_processor())
            asyncio.create_task(self._broadcast_processor())
            asyncio.create_task(self._performance_monitor())
            asyncio.create_task(self._connection_monitor())

            self.is_running = True
            self.service_start_time = datetime.now()

            logger.info(
                f"實時決策服務已啟動，監聽 {self.websocket_host}:{self.websocket_port}"
            )
            return True

        except Exception as e:
            logger.error(f"實時決策服務啟動失敗: {e}")
            return False

    async def stop_service(self) -> None:
        """停止實時決策服務"""
        try:
            logger.info("停止實時決策服務...")

            self.is_running = False

            # 關閉所有客戶端連接
            for client in list(self.clients.values()):
                await self._disconnect_client(client.client_id, "Service stopping")

            # 關閉 WebSocket 服務器
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()

            logger.info("實時決策服務已停止")

        except Exception as e:
            logger.error(f"停止實時決策服務時發生錯誤: {e}")

    async def _handle_websocket_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """處理 WebSocket 連接"""
        client_id = str(uuid.uuid4())

        try:
            # 檢查連接數限制
            if len(self.clients) >= self.max_connections:
                await websocket.close(code=1013, reason="Maximum connections reached")
                return

            # 創建客戶端連接
            client = ClientConnection(
                client_id=client_id,
                websocket=websocket,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                subscriptions=set(),
                metadata={"remote_address": websocket.remote_address},
            )

            self.clients[client_id] = client
            self.total_clients_connected += 1

            # 發送連接確認
            await self._send_to_client(
                client_id,
                WebSocketMessage(
                    message_type=MessageType.CONNECTION_STATUS,
                    timestamp=datetime.now(),
                    data={
                        "status": "connected",
                        "client_id": client_id,
                        "server_info": {
                            "version": "2.3.0",
                            "capabilities": [t.value for t in MessageType],
                        },
                    },
                ),
            )

            logger.info(f"客戶端已連接: {client_id}")

            # 處理客戶端消息
            async for message in websocket:
                try:
                    await self._process_client_message(client_id, message)
                    client.last_activity = datetime.now()
                except Exception as e:
                    logger.error(f"處理客戶端消息失敗: {e}")
                    await self._send_error(
                        client_id, f"Message processing error: {str(e)}"
                    )

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客戶端連接已關閉: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket 連接處理錯誤: {e}")
        finally:
            # 清理連接
            if client_id in self.clients:
                await self._disconnect_client(client_id, "Connection closed")

    async def _process_client_message(self, client_id: str, raw_message: str) -> None:
        """處理客戶端消息"""
        try:
            message_data = json.loads(raw_message)
            message_type = MessageType(message_data.get("type"))

            if message_type == MessageType.ALGORITHM_SWITCH:
                # 處理算法切換請求
                algorithm_name = message_data.get("algorithm")
                if algorithm_name:
                    algorithm_type = AlgorithmType(algorithm_name.lower())
                    success = await self.algorithm_integrator.switch_algorithm(
                        algorithm_type
                    )

                    await self._send_to_client(
                        client_id,
                        WebSocketMessage(
                            message_type=MessageType.ALGORITHM_STATUS,
                            timestamp=datetime.now(),
                            data={
                                "action": "switch_result",
                                "success": success,
                                "current_algorithm": (
                                    algorithm_type.value if success else None
                                ),
                            },
                        ),
                    )

            elif message_type in [
                MessageType.PERFORMANCE_METRICS,
                MessageType.REAL_TIME_STATS,
            ]:
                # 處理訂閱請求
                client = self.clients[client_id]
                client.subscriptions.add(message_type)

                await self._send_to_client(
                    client_id,
                    WebSocketMessage(
                        message_type=MessageType.CONNECTION_STATUS,
                        timestamp=datetime.now(),
                        data={
                            "action": "subscription_confirmed",
                            "message_type": message_type.value,
                        },
                    ),
                )

        except Exception as e:
            logger.error(f"客戶端消息處理錯誤: {e}")
            await self._send_error(client_id, f"Invalid message format: {str(e)}")

    async def _send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """發送消息到特定客戶端"""
        if client_id not in self.clients:
            return False

        try:
            client = self.clients[client_id]
            message_json = json.dumps(
                {
                    "type": message.message_type.value,
                    "timestamp": message.timestamp.isoformat(),
                    "data": message.data,
                }
            )

            await client.websocket.send(message_json)
            self.total_messages_sent += 1
            return True

        except Exception as e:
            logger.error(f"發送消息到客戶端 {client_id} 失敗: {e}")
            await self._disconnect_client(client_id, f"Send error: {str(e)}")
            return False

    async def _broadcast_message(
        self,
        message: WebSocketMessage,
        message_type_filter: Optional[MessageType] = None,
    ) -> int:
        """廣播消息到所有訂閱的客戶端"""
        target_type = message_type_filter or message.message_type
        sent_count = 0

        for client_id, client in list(self.clients.items()):
            if target_type in client.subscriptions:
                if await self._send_to_client(client_id, message):
                    sent_count += 1

        return sent_count

    async def _send_error(self, client_id: str, error_message: str) -> None:
        """發送錯誤消息到客戶端"""
        await self._send_to_client(
            client_id,
            WebSocketMessage(
                message_type=MessageType.ERROR_NOTIFICATION,
                timestamp=datetime.now(),
                data={"error": error_message, "timestamp": datetime.now().isoformat()},
            ),
        )

    async def _disconnect_client(self, client_id: str, reason: str) -> None:
        """斷開客戶端連接"""
        if client_id in self.clients:
            client = self.clients[client_id]

            try:
                await client.websocket.close(code=1000, reason=reason)
            except:
                pass

            del self.clients[client_id]
            logger.info(f"客戶端已斷開: {client_id}, 原因: {reason}")

    async def _event_processor(self) -> None:
        """事件處理器"""
        while self.is_running:
            try:
                # 等待事件
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # 處理事件
                await self._process_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"事件處理錯誤: {e}")

    async def _process_event(self, event: Any) -> None:
        """處理單個事件"""
        # 這裡可以根據事件類型執行不同的處理邏輯
        pass

    async def _broadcast_processor(self) -> None:
        """廣播處理器"""
        while self.is_running:
            try:
                # 等待廣播消息
                message = await asyncio.wait_for(
                    self.broadcast_queue.get(), timeout=1.0
                )

                # 執行廣播
                await self._broadcast_message(message)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"廣播處理錯誤: {e}")

    async def _performance_monitor(self) -> None:
        """性能監控器"""
        while self.is_running:
            try:
                # 收集性能數據
                snapshot = await self._collect_performance_snapshot()

                # 存儲快照
                self.performance_history.append(snapshot)
                if len(self.performance_history) > self.max_performance_history:
                    self.performance_history = self.performance_history[
                        -self.max_performance_history :
                    ]

                # 廣播性能更新
                await self.broadcast_performance_update(snapshot)

                # 等待下次監控
                await asyncio.sleep(self.performance_monitor_interval)

            except Exception as e:
                logger.error(f"性能監控錯誤: {e}")
                await asyncio.sleep(self.performance_monitor_interval)

    async def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """收集性能快照"""
        # 算法指標
        algorithm_metrics = {}
        for algo_type in self.algorithm_integrator.get_available_algorithms():
            metrics = self.algorithm_integrator.get_algorithm_metrics()
            if algo_type.value in metrics:
                algo_metrics = metrics[algo_type.value]
                algorithm_metrics[algo_type] = {
                    "total_decisions": algo_metrics.total_decisions,
                    "successful_decisions": algo_metrics.successful_decisions,
                    "average_decision_time_ms": algo_metrics.average_decision_time_ms,
                    "average_confidence": algo_metrics.average_confidence,
                    "total_reward": algo_metrics.total_reward,
                    "success_rate": algo_metrics.successful_decisions
                    / max(algo_metrics.total_decisions, 1),
                }

        # 環境狀態
        environment_status = self.environment_bridge.get_status()

        # 系統指標
        system_metrics = {
            "connected_clients": len(self.clients),
            "total_messages_sent": self.total_messages_sent,
            "uptime_seconds": (
                (datetime.now() - self.service_start_time).total_seconds()
                if self.service_start_time
                else 0
            ),
            "memory_usage_mb": 0,  # 簡化，實際可使用 psutil
            "cpu_usage_percent": 0,
        }

        return PerformanceSnapshot(
            timestamp=datetime.now(),
            algorithm_metrics=algorithm_metrics,
            environment_status=environment_status,
            system_metrics=system_metrics,
        )

    async def _connection_monitor(self) -> None:
        """連接監控器"""
        while self.is_running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(minutes=5)

                # 檢查超時連接
                timeout_clients = []
                for client_id, client in self.clients.items():
                    if client.last_activity < timeout_threshold:
                        timeout_clients.append(client_id)

                # 斷開超時連接
                for client_id in timeout_clients:
                    await self._disconnect_client(client_id, "Connection timeout")

                await asyncio.sleep(30)  # 每30秒檢查一次

            except Exception as e:
                logger.error(f"連接監控錯誤: {e}")
                await asyncio.sleep(30)

    # 公共 API 方法

    async def broadcast_decision_event(
        self,
        algorithm_type: AlgorithmType,
        decision: AlgorithmDecision,
        action: EnvironmentAction,
        observation: EnvironmentObservation,
        explanation: Optional[Dict[str, Any]] = None,
    ) -> None:
        """廣播決策事件"""

        event = DecisionEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            algorithm_type=algorithm_type,
            decision=decision,
            action=action,
            observation=observation,
            explanation=explanation,
        )

        # 存儲事件
        self.decision_events.append(event)
        if len(self.decision_events) > self.max_decision_events:
            self.decision_events = self.decision_events[-self.max_decision_events :]

        # 廣播事件
        message = WebSocketMessage(
            message_type=MessageType.DECISION_EVENT,
            timestamp=event.timestamp,
            data={
                "event_id": event.event_id,
                "algorithm": algorithm_type.value,
                "action": asdict(action),
                "confidence": decision.confidence,
                "decision_time_ms": decision.decision_time_ms,
                "observation_summary": {
                    "step": observation.time_step,
                    "scenario_type": observation.scenario_type,
                    "signal_strength": observation.serving_satellite_signal.get(
                        "rsrp", -100
                    ),
                    "candidate_count": len(observation.candidate_satellites),
                    "trigger_severity": observation.trigger_severity,
                },
                "explanation": explanation,
            },
        )

        await self.broadcast_queue.put(message)

    async def broadcast_handover_event(
        self, handover_result: Dict[str, Any], algorithm_type: AlgorithmType
    ) -> None:
        """廣播換手事件"""

        message = WebSocketMessage(
            message_type=MessageType.HANDOVER_EVENT,
            timestamp=datetime.now(),
            data={
                "algorithm": algorithm_type.value,
                "success": handover_result.get("success", False),
                "target_satellite": handover_result.get("target_satellite"),
                "latency_ms": handover_result.get("handover_latency_ms", 0),
                "candidate_score": handover_result.get("candidate_score", 0),
                "execution_time_ms": handover_result.get("execution_time_ms", 0),
            },
        )

        await self.broadcast_queue.put(message)

    async def broadcast_performance_update(self, snapshot: PerformanceSnapshot) -> None:
        """廣播性能更新"""

        message = WebSocketMessage(
            message_type=MessageType.PERFORMANCE_METRICS,
            timestamp=snapshot.timestamp,
            data={
                "algorithms": {
                    algo.value: metrics
                    for algo, metrics in snapshot.algorithm_metrics.items()
                },
                "environment": snapshot.environment_status,
                "system": snapshot.system_metrics,
            },
        )

        await self.broadcast_queue.put(message)

    async def broadcast_algorithm_status(self, status_data: Dict[str, Any]) -> None:
        """廣播算法狀態"""

        message = WebSocketMessage(
            message_type=MessageType.ALGORITHM_STATUS,
            timestamp=datetime.now(),
            data=status_data,
        )

        await self.broadcast_queue.put(message)

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """獲取已連接的客戶端列表"""
        return [
            {
                "client_id": client.client_id,
                "connected_at": client.connected_at.isoformat(),
                "last_activity": client.last_activity.isoformat(),
                "subscriptions": [sub.value for sub in client.subscriptions],
                "remote_address": client.metadata.get("remote_address"),
            }
            for client in self.clients.values()
        ]

    def get_recent_decision_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取最近的決策事件"""
        recent_events = self.decision_events[-limit:]
        return [
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "algorithm": event.algorithm_type.value,
                "action_type": event.action.action_type,
                "confidence": event.decision.confidence,
                "decision_time_ms": event.decision.decision_time_ms,
            }
            for event in recent_events
        ]

    def get_performance_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取性能歷史記錄"""
        recent_snapshots = self.performance_history[-limit:]
        return [
            {
                "timestamp": snapshot.timestamp.isoformat(),
                "algorithm_metrics": {
                    algo.value: metrics
                    for algo, metrics in snapshot.algorithm_metrics.items()
                },
                "system_metrics": snapshot.system_metrics,
            }
            for snapshot in recent_snapshots
        ]

    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "is_running": self.is_running,
            "websocket_host": self.websocket_host,
            "websocket_port": self.websocket_port,
            "connected_clients": len(self.clients),
            "total_clients_connected": self.total_clients_connected,
            "total_messages_sent": self.total_messages_sent,
            "uptime_seconds": (
                (datetime.now() - self.service_start_time).total_seconds()
                if self.service_start_time
                else 0
            ),
            "decision_events_count": len(self.decision_events),
            "performance_snapshots_count": len(self.performance_history),
        }
