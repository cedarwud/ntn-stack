"""
事件總線服務

實現事件驅動架構的核心組件，支援：
- 異步事件發布和訂閱
- 事件持久化和重播
- 高性能事件分發
- 事件溯源 (Event Sourcing)
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class EventPriority(Enum):
    """事件優先級"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """事件狀態"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Event:
    """事件數據結構"""

    id: str
    type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    version: int = 1
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """從字典創建事件"""
        return cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            version=data.get("version", 1),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            ttl_seconds=data.get("ttl_seconds"),
        )


@dataclass
class EventHandler:
    """事件處理器"""

    id: str
    event_type: str
    handler_func: Callable[[Event], Union[bool, Any]]
    is_async: bool = True
    priority: int = 100
    max_concurrent: int = 10
    timeout_seconds: int = 30


class EventStore:
    """事件存儲（內存實現，生產環境可替換為 Redis/MongoDB）"""

    def __init__(self, max_events: int = 10000):
        self.events: Dict[str, Event] = {}
        self.events_by_type: Dict[str, List[str]] = {}
        self.events_by_correlation: Dict[str, List[str]] = {}
        self.max_events = max_events
        self._lock = asyncio.Lock()

    async def store_event(self, event: Event) -> bool:
        """存儲事件"""
        async with self._lock:
            # 檢查 TTL
            if event.ttl_seconds:
                expiry_time = event.timestamp + timedelta(seconds=event.ttl_seconds)
                if datetime.utcnow() > expiry_time:
                    logger.warning("事件已過期，拒絕存儲", event_id=event.id)
                    return False

            # 存儲事件
            self.events[event.id] = event

            # 按類型索引
            if event.type not in self.events_by_type:
                self.events_by_type[event.type] = []
            self.events_by_type[event.type].append(event.id)

            # 按關聯ID索引
            if event.correlation_id:
                if event.correlation_id not in self.events_by_correlation:
                    self.events_by_correlation[event.correlation_id] = []
                self.events_by_correlation[event.correlation_id].append(event.id)

            # 清理舊事件（簡單 LRU）
            if len(self.events) > self.max_events:
                await self._cleanup_old_events()

            return True

    async def get_event(self, event_id: str) -> Optional[Event]:
        """獲取事件"""
        return self.events.get(event_id)

    async def get_events_by_type(
        self, event_type: str, limit: int = 100
    ) -> List[Event]:
        """按類型獲取事件"""
        event_ids = self.events_by_type.get(event_type, [])
        events = []
        for event_id in event_ids[-limit:]:  # 最新的事件
            if event_id in self.events:
                events.append(self.events[event_id])
        return events

    async def get_events_by_correlation(self, correlation_id: str) -> List[Event]:
        """按關聯ID獲取事件"""
        event_ids = self.events_by_correlation.get(correlation_id, [])
        events = []
        for event_id in event_ids:
            if event_id in self.events:
                events.append(self.events[event_id])
        return sorted(events, key=lambda e: e.timestamp)

    async def _cleanup_old_events(self):
        """清理舊事件"""
        # 簡單實現：刪除最舊的 10% 事件
        cleanup_count = int(self.max_events * 0.1)
        sorted_events = sorted(self.events.items(), key=lambda x: x[1].timestamp)

        for event_id, event in sorted_events[:cleanup_count]:
            # 從主存儲刪除
            del self.events[event_id]

            # 從索引刪除
            if event.type in self.events_by_type:
                if event_id in self.events_by_type[event.type]:
                    self.events_by_type[event.type].remove(event_id)

            if (
                event.correlation_id
                and event.correlation_id in self.events_by_correlation
            ):
                if event_id in self.events_by_correlation[event.correlation_id]:
                    self.events_by_correlation[event.correlation_id].remove(event_id)


class EventBusService:
    """事件總線服務"""

    def __init__(self, event_store: Optional[EventStore] = None):
        self.event_store = event_store or EventStore()
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.running = False
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0,
            "active_processors": 0,
        }

        # 事件佇列 (按優先級)
        self.event_queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }

        # 處理器控制
        self.processor_tasks: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

    async def start(self, num_processors: int = 4):
        """啟動事件總線"""
        if self.running:
            logger.warning("事件總線已在運行")
            return

        self.running = True
        self.shutdown_event.clear()

        # 啟動事件處理器
        for i in range(num_processors):
            task = asyncio.create_task(self._event_processor(f"processor-{i}"))
            self.processor_tasks.append(task)

        logger.info("事件總線已啟動", processors=num_processors)

    async def stop(self):
        """停止事件總線"""
        if not self.running:
            return

        logger.info("正在停止事件總線...")
        self.running = False
        self.shutdown_event.set()

        # 等待所有處理器完成
        if self.processor_tasks:
            await asyncio.gather(*self.processor_tasks, return_exceptions=True)

        # 取消活躍的處理任務
        for task in self.processing_tasks.values():
            if not task.done():
                task.cancel()

        logger.info("事件總線已停止")

    def register_handler(
        self,
        event_type: str,
        handler_func: Callable,
        handler_id: Optional[str] = None,
        priority: int = 100,
        max_concurrent: int = 10,
        timeout_seconds: int = 30,
    ) -> str:
        """註冊事件處理器"""
        handler_id = handler_id or f"{event_type}_{uuid.uuid4().hex[:8]}"

        handler = EventHandler(
            id=handler_id,
            event_type=event_type,
            handler_func=handler_func,
            is_async=asyncio.iscoroutinefunction(handler_func),
            priority=priority,
            max_concurrent=max_concurrent,
            timeout_seconds=timeout_seconds,
        )

        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        self.handlers[event_type].sort(key=lambda h: h.priority)  # 按優先級排序

        self.metrics["handlers_registered"] += 1

        logger.info(
            "事件處理器已註冊",
            handler_id=handler_id,
            event_type=event_type,
            priority=priority,
        )

        return handler_id

    def unregister_handler(self, handler_id: str, event_type: str) -> bool:
        """註銷事件處理器"""
        if event_type not in self.handlers:
            return False

        handlers = self.handlers[event_type]
        for i, handler in enumerate(handlers):
            if handler.id == handler_id:
                del handlers[i]
                logger.info(
                    "事件處理器已註銷", handler_id=handler_id, event_type=event_type
                )
                return True

        return False

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """發布事件"""
        event = Event(
            id=f"evt_{uuid.uuid4().hex}",
            type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            causation_id=causation_id,
            ttl_seconds=ttl_seconds,
        )

        # 存儲事件
        stored = await self.event_store.store_event(event)
        if not stored:
            logger.error("事件存儲失敗", event_id=event.id)
            return event.id

        # 加入處理佇列
        try:
            await self.event_queues[priority].put(event)
            self.metrics["events_published"] += 1

            logger.debug(
                "事件已發布",
                event_id=event.id,
                event_type=event_type,
                priority=priority.name,
            )

        except Exception as e:
            logger.error("事件發布失敗", event_id=event.id, error=str(e))

        return event.id

    async def _event_processor(self, processor_id: str):
        """事件處理器"""
        logger.info("事件處理器啟動", processor_id=processor_id)

        while self.running and not self.shutdown_event.is_set():
            try:
                # 按優先級處理事件
                event = await self._get_next_event()

                if event:
                    self.metrics["active_processors"] += 1

                    # 處理事件
                    await self._process_event(event, processor_id)

                    self.metrics["active_processors"] -= 1
                else:
                    # 沒有事件時短暫休眠
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("事件處理器異常", processor_id=processor_id, error=str(e))
                await asyncio.sleep(1)  # 錯誤後暫停

        logger.info("事件處理器停止", processor_id=processor_id)

    async def _get_next_event(self) -> Optional[Event]:
        """獲取下一個待處理事件（按優先級）"""
        # 按優先級從高到低檢查佇列
        for priority in [
            EventPriority.CRITICAL,
            EventPriority.HIGH,
            EventPriority.NORMAL,
            EventPriority.LOW,
        ]:
            try:
                event = self.event_queues[priority].get_nowait()
                return event
            except asyncio.QueueEmpty:
                continue

        # 如果所有佇列都空，等待任一佇列有事件
        try:
            # 使用 asyncio.wait 等待任一佇列有事件，設置超時避免無限等待
            done, pending = await asyncio.wait(
                [queue.get() for queue in self.event_queues.values()],
                timeout=1.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # 取消其他等待
            for task in pending:
                task.cancel()

            if done:
                return done.pop().result()

        except asyncio.TimeoutError:
            pass

        return None

    async def _process_event(self, event: Event, processor_id: str):
        """處理單個事件"""
        start_time = time.time()

        try:
            # 檢查是否有處理器
            handlers = self.handlers.get(event.type, [])
            if not handlers:
                logger.debug(
                    "沒有處理器處理此事件", event_type=event.type, event_id=event.id
                )
                return

            # 並行執行所有處理器
            handler_tasks = []
            for handler in handlers:
                task = asyncio.create_task(
                    self._execute_handler(event, handler, processor_id)
                )
                handler_tasks.append(task)

            # 等待所有處理器完成
            results = await asyncio.gather(*handler_tasks, return_exceptions=True)

            # 檢查結果
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "處理器執行失敗",
                        handler_id=handlers[i].id,
                        event_id=event.id,
                        error=str(result),
                    )
                else:
                    success_count += 1

            if success_count > 0:
                self.metrics["events_processed"] += 1
                processing_time = (time.time() - start_time) * 1000

                logger.debug(
                    "事件處理完成",
                    event_id=event.id,
                    processors=success_count,
                    processing_time_ms=f"{processing_time:.2f}",
                )
            else:
                self.metrics["events_failed"] += 1

                # 重試機制
                if event.retry_count < event.max_retries:
                    await self._retry_event(event)

        except Exception as e:
            logger.error("事件處理異常", event_id=event.id, error=str(e))
            self.metrics["events_failed"] += 1

    async def _execute_handler(
        self, event: Event, handler: EventHandler, processor_id: str
    ):
        """執行單個處理器"""
        try:
            if handler.is_async:
                result = await asyncio.wait_for(
                    handler.handler_func(event), timeout=handler.timeout_seconds
                )
            else:
                # 在執行器中運行同步函數
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handler.handler_func, event)

            return result

        except asyncio.TimeoutError:
            logger.error(
                "處理器執行超時",
                handler_id=handler.id,
                event_id=event.id,
                timeout=handler.timeout_seconds,
            )
            raise
        except Exception as e:
            logger.error(
                "處理器執行異常", handler_id=handler.id, event_id=event.id, error=str(e)
            )
            raise

    async def _retry_event(self, event: Event):
        """重試事件"""
        event.retry_count += 1

        # 計算重試延遲（指數退避）
        delay = min(2**event.retry_count, 60)  # 最大 60 秒

        logger.info(
            "事件將重試",
            event_id=event.id,
            retry_count=event.retry_count,
            delay_seconds=delay,
        )

        # 延遲後重新加入佇列
        asyncio.create_task(self._delayed_retry(event, delay))

    async def _delayed_retry(self, event: Event, delay: float):
        """延遲重試"""
        await asyncio.sleep(delay)

        if self.running:
            await self.event_queues[event.priority].put(event)
            logger.debug("事件已重新加入佇列", event_id=event.id)

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取事件總線指標"""
        queue_sizes = {
            priority.name: queue.qsize()
            for priority, queue in self.event_queues.items()
        }

        return {
            **self.metrics,
            "queue_sizes": queue_sizes,
            "running": self.running,
            "handler_types": list(self.handlers.keys()),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
        }


# 全局事件總線實例
_global_event_bus: Optional[EventBusService] = None


async def get_event_bus() -> EventBusService:
    """獲取全局事件總線實例"""
    global _global_event_bus

    if _global_event_bus is None:
        _global_event_bus = EventBusService()
        await _global_event_bus.start()

    return _global_event_bus


async def shutdown_event_bus():
    """關閉全局事件總線"""
    global _global_event_bus

    if _global_event_bus:
        await _global_event_bus.stop()
        _global_event_bus = None


# 便利函數
async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    source: str = "unknown",
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: Optional[str] = None,
) -> str:
    """發布事件的便利函數"""
    bus = await get_event_bus()
    return await bus.publish(event_type, data, source, priority, correlation_id)


def event_handler(
    event_type: str,
    priority: int = 100,
    max_concurrent: int = 10,
    timeout_seconds: int = 30,
):
    """事件處理器裝飾器"""

    def decorator(func):
        # 在應用啟動時註冊處理器
        async def register():
            bus = await get_event_bus()
            handler_id = bus.register_handler(
                event_type, func, None, priority, max_concurrent, timeout_seconds
            )
            return handler_id

        # 為函數添加註冊方法
        func._register_handler = register
        func._event_type = event_type

        return func

    return decorator


# 換手相關事件類型常數
class HandoverEventTypes:
    """換手事件類型常數"""
    
    # 預測事件
    PREDICTION_CREATED = "handover.prediction.created"
    PREDICTION_UPDATED = "handover.prediction.updated"
    PREDICTION_EXPIRED = "handover.prediction.expired"
    
    # 計劃事件
    PLAN_CREATED = "handover.plan.created"
    PLAN_UPDATED = "handover.plan.updated"
    PLAN_CANCELLED = "handover.plan.cancelled"
    
    # 執行事件
    EXECUTION_STARTED = "handover.execution.started"
    EXECUTION_PREPARING = "handover.execution.preparing"
    EXECUTION_EXECUTING = "handover.execution.executing"
    EXECUTION_COMPLETED = "handover.execution.completed"
    EXECUTION_FAILED = "handover.execution.failed"
    EXECUTION_ROLLBACK = "handover.execution.rollback"
    
    # 協調事件
    COORDINATION_REQUESTED = "handover.coordination.requested"
    COORDINATION_APPROVED = "handover.coordination.approved"
    COORDINATION_REJECTED = "handover.coordination.rejected"
    
    # 指標事件
    METRICS_UPDATED = "handover.metrics.updated"
    PERFORMANCE_ALERT = "handover.performance.alert"
    
    # 衛星狀態事件
    SATELLITE_AVAILABILITY_CHANGED = "satellite.availability.changed"
    SATELLITE_LOAD_CHANGED = "satellite.load.changed"
    
    # UE 狀態事件
    UE_SIGNAL_DEGRADED = "ue.signal.degraded"
    UE_CONNECTION_LOST = "ue.connection.lost"
    UE_HANDOVER_REQUIRED = "ue.handover.required"


class HandoverEventBusExtension:
    """換手事件總線擴展"""
    
    def __init__(self, event_bus: EventBusService):
        self.event_bus = event_bus
        self.handover_subscribers: Dict[str, List[Callable]] = {}
        
    async def publish_handover_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        ue_id: Optional[str] = None,
        satellite_id: Optional[str] = None,
        priority: str = "NORMAL",
        correlation_id: Optional[str] = None
    ) -> str:
        """發布換手相關事件"""
        
        # 轉換優先級
        event_priority = EventPriority.NORMAL
        if priority == "LOW":
            event_priority = EventPriority.LOW
        elif priority == "HIGH":
            event_priority = EventPriority.HIGH
        elif priority == "CRITICAL":
            event_priority = EventPriority.CRITICAL
        
        # 增強事件數據
        enhanced_data = {
            **data,
            "event_category": "handover",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if ue_id:
            enhanced_data["ue_id"] = ue_id
        if satellite_id:
            enhanced_data["satellite_id"] = satellite_id
            
        return await self.event_bus.publish(
            event_type=event_type,
            data=enhanced_data,
            source="handover_service",
            priority=event_priority,
            correlation_id=correlation_id
        )
    
    async def subscribe_to_handover_events(
        self,
        event_patterns: List[str],
        handler_func: Callable,
        subscriber_id: Optional[str] = None,
        priority: int = 100
    ) -> List[str]:
        """訂閱換手事件模式"""
        
        handler_ids = []
        
        for pattern in event_patterns:
            # 支持通配符模式
            if pattern.endswith(".*"):
                # 獲取所有匹配的事件類型
                base_pattern = pattern[:-2]
                matching_types = [
                    event_type for event_type in dir(HandoverEventTypes)
                    if not event_type.startswith("_") and 
                    getattr(HandoverEventTypes, event_type).startswith(base_pattern)
                ]
                
                for event_type_name in matching_types:
                    event_type = getattr(HandoverEventTypes, event_type_name)
                    handler_id = self.event_bus.register_handler(
                        event_type=event_type,
                        handler_func=handler_func,
                        handler_id=f"{subscriber_id}_{event_type}" if subscriber_id else None,
                        priority=priority
                    )
                    handler_ids.append(handler_id)
            else:
                # 精確匹配
                handler_id = self.event_bus.register_handler(
                    event_type=pattern,
                    handler_func=handler_func,
                    handler_id=f"{subscriber_id}_{pattern}" if subscriber_id else None,
                    priority=priority
                )
                handler_ids.append(handler_id)
        
        return handler_ids
    
    async def publish_prediction_event(
        self,
        prediction_data: Dict[str, Any],
        event_subtype: str = "created",
        priority: str = "HIGH"
    ) -> str:
        """發布換手預測事件"""
        
        event_type = f"handover.prediction.{event_subtype}"
        
        return await self.publish_handover_event(
            event_type=event_type,
            data=prediction_data,
            ue_id=prediction_data.get("ue_id"),
            satellite_id=prediction_data.get("current_satellite"),
            priority=priority,
            correlation_id=prediction_data.get("prediction_id")
        )
    
    async def publish_execution_event(
        self,
        execution_data: Dict[str, Any],
        event_subtype: str = "started",
        priority: str = "HIGH"
    ) -> str:
        """發布換手執行事件"""
        
        event_type = f"handover.execution.{event_subtype}"
        
        return await self.publish_handover_event(
            event_type=event_type,
            data=execution_data,
            ue_id=execution_data.get("ue_id"),
            satellite_id=execution_data.get("target_satellite"),
            priority=priority,
            correlation_id=execution_data.get("execution_id")
        )
    
    async def publish_coordination_event(
        self,
        coordination_data: Dict[str, Any],
        event_subtype: str = "requested",
        priority: str = "NORMAL"
    ) -> str:
        """發布換手協調事件"""
        
        event_type = f"handover.coordination.{event_subtype}"
        
        return await self.publish_handover_event(
            event_type=event_type,
            data=coordination_data,
            priority=priority,
            correlation_id=coordination_data.get("coordination_id")
        )
    
    async def publish_metrics_event(
        self,
        metrics_data: Dict[str, Any],
        priority: str = "LOW"
    ) -> str:
        """發布換手指標事件"""
        
        return await self.publish_handover_event(
            event_type=HandoverEventTypes.METRICS_UPDATED,
            data=metrics_data,
            priority=priority
        )
    
    async def publish_alert_event(
        self,
        alert_data: Dict[str, Any],
        priority: str = "HIGH"
    ) -> str:
        """發布換手性能警報事件"""
        
        return await self.publish_handover_event(
            event_type=HandoverEventTypes.PERFORMANCE_ALERT,
            data=alert_data,
            ue_id=alert_data.get("ue_id"),
            satellite_id=alert_data.get("satellite_id"),
            priority=priority
        )
    
    async def get_handover_event_history(
        self,
        event_type: Optional[str] = None,
        ue_id: Optional[str] = None,
        satellite_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """獲取換手事件歷史"""
        
        if event_type:
            events = await self.event_bus.event_store.get_events_by_type(event_type, limit)
        else:
            # 獲取所有換手相關事件
            all_handover_events = []
            
            for attr_name in dir(HandoverEventTypes):
                if not attr_name.startswith("_"):
                    event_type_value = getattr(HandoverEventTypes, attr_name)
                    events = await self.event_bus.event_store.get_events_by_type(event_type_value, limit // 20)
                    all_handover_events.extend(events)
            
            # 按時間排序
            all_handover_events.sort(key=lambda e: e.timestamp, reverse=True)
            events = all_handover_events[:limit]
        
        # 過濾條件
        filtered_events = []
        for event in events:
            if ue_id and event.data.get("ue_id") != ue_id:
                continue
            if satellite_id and event.data.get("satellite_id") != satellite_id:
                continue
            filtered_events.append(event)
        
        return filtered_events
    
    async def get_handover_event_statistics(self) -> Dict[str, Any]:
        """獲取換手事件統計"""
        
        stats = {
            "event_counts": {},
            "recent_activity": {},
            "error_rates": {},
            "average_processing_times": {}
        }
        
        # 統計各類事件數量
        for attr_name in dir(HandoverEventTypes):
            if not attr_name.startswith("_"):
                event_type = getattr(HandoverEventTypes, attr_name)
                events = await self.event_bus.event_store.get_events_by_type(event_type, 1000)
                stats["event_counts"][event_type] = len(events)
                
                # 最近1小時的活動
                recent_events = [
                    e for e in events 
                    if (datetime.utcnow() - e.timestamp).total_seconds() < 3600
                ]
                stats["recent_activity"][event_type] = len(recent_events)
        
        return stats


# 全局換手事件總線擴展實例
_global_handover_event_bus: Optional[HandoverEventBusExtension] = None


async def get_handover_event_bus() -> HandoverEventBusExtension:
    """獲取全局換手事件總線擴展實例"""
    global _global_handover_event_bus
    
    if _global_handover_event_bus is None:
        main_event_bus = await get_event_bus()
        _global_handover_event_bus = HandoverEventBusExtension(main_event_bus)
    
    return _global_handover_event_bus


# 換手事件裝飾器
def handover_event_handler(
    event_patterns: List[str],
    priority: int = 100,
    subscriber_id: Optional[str] = None
):
    """換手事件處理器裝飾器"""
    
    def decorator(func):
        async def register():
            handover_bus = await get_handover_event_bus()
            handler_ids = await handover_bus.subscribe_to_handover_events(
                event_patterns=event_patterns,
                handler_func=func,
                subscriber_id=subscriber_id,
                priority=priority
            )
            return handler_ids
        
        func._register_handover_handler = register
        func._event_patterns = event_patterns
        return func
    
    return decorator
