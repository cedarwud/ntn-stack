from typing import Dict, List, Callable, Any, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)

class DomainEventBus:
    """領域事件總線，用於跨領域間的事件通信"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}
        
    def subscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None]]) -> None:
        """訂閱指定類型的領域事件
        
        Args:
            event_type: 事件類型名稱
            callback: 非同步回調函數，接收事件數據
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"已訂閱事件: {event_type}")
        
    async def publish(self, event_type: str, event_data: Any) -> None:
        """發布領域事件
        
        Args:
            event_type: 事件類型名稱
            event_data: 事件數據
        """
        if event_type not in self._subscribers:
            logger.debug(f"沒有訂閱者的事件: {event_type}")
            return
            
        logger.debug(f"發布事件: {event_type}, 訂閱者數量: {len(self._subscribers[event_type])}")
        tasks = [callback(event_data) for callback in self._subscribers[event_type]]
        await asyncio.gather(*tasks)

# 全局事件總線實例，供各領域使用
event_bus = DomainEventBus() 