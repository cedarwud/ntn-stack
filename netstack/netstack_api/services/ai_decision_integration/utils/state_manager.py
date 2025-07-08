"""
狀態管理器
==========

負責管理整個決策系統的狀態，包括衛星池、網路條件、歷史決策等。
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
import structlog
from collections import deque
from dataclasses import dataclass

from ..interfaces.decision_engine import Decision
from ..interfaces.executor import ExecutionResult

logger = structlog.get_logger(__name__)

@dataclass
class NetworkConditions:
    """網路條件狀態"""
    total_satellites: int
    active_connections: int
    average_latency: float
    packet_loss_rate: float
    throughput_mbps: float
    congestion_level: float
    interference_level: float
    timestamp: float

@dataclass 
class HandoverState:
    """換手狀態"""
    ue_id: str
    source_satellite: str
    target_satellite: str
    handover_type: str
    start_time: float
    completion_time: Optional[float] = None
    success: Optional[bool] = None
    performance_metrics: Dict[str, float] = None

class StateManager:
    """
    狀態管理器主類
    
    維護系統的全局狀態，提供狀態查詢和更新接口。
    """
    
    def __init__(self, redis_adapter=None):
        """
        初始化狀態管理器
        
        Args:
            redis_adapter: Redis適配器 (可選)
        """
        self.redis_adapter = redis_adapter
        
        # 本地狀態緩存
        self._satellite_pool: List[Dict[str, Any]] = []
        self._network_conditions: Optional[NetworkConditions] = None
        self._handover_history: deque = deque(maxlen=1000)
        self._active_handovers: Dict[str, HandoverState] = {}
        self._system_metrics: Dict[str, Any] = {}
        
        # 更新鎖
        self._update_lock = asyncio.Lock()
        
        # 初始化默認網路條件
        self._network_conditions = NetworkConditions(
            total_satellites=0,
            active_connections=0,
            average_latency=50.0,
            packet_loss_rate=0.01,
            throughput_mbps=100.0,
            congestion_level=0.3,
            interference_level=0.2,
            timestamp=time.time()
        )
        
        logger.info("State manager initialized")
    
    async def get_satellite_pool(self) -> List[Dict[str, Any]]:
        """
        獲取可用衛星池
        
        Returns:
            List[Dict[str, Any]]: 衛星池數據
        """
        async with self._update_lock:
            if self.redis_adapter:
                try:
                    # 從Redis獲取最新數據
                    cached_pool = await self.redis_adapter.get("satellite_pool")
                    if cached_pool:
                        self._satellite_pool = cached_pool
                except Exception as e:
                    logger.warning("Failed to get satellite pool from Redis", error=str(e))
            
            # 如果沒有數據，生成模擬數據
            if not self._satellite_pool:
                self._satellite_pool = self._generate_mock_satellite_pool()
            
            return self._satellite_pool.copy()
    
    async def update_satellite_pool(self, satellite_pool: List[Dict[str, Any]]):
        """
        更新衛星池
        
        Args:
            satellite_pool: 新的衛星池數據
        """
        async with self._update_lock:
            self._satellite_pool = satellite_pool
            
            if self.redis_adapter:
                try:
                    await self.redis_adapter.set("satellite_pool", satellite_pool, ttl=60)
                except Exception as e:
                    logger.warning("Failed to cache satellite pool to Redis", error=str(e))
            
            logger.debug("Satellite pool updated", satellites=len(satellite_pool))
    
    async def get_network_conditions(self) -> NetworkConditions:
        """
        獲取當前網路條件
        
        Returns:
            NetworkConditions: 網路條件數據
        """
        async with self._update_lock:
            if self.redis_adapter:
                try:
                    cached_conditions = await self.redis_adapter.get("network_conditions")
                    if cached_conditions:
                        self._network_conditions = NetworkConditions(**cached_conditions)
                except Exception as e:
                    logger.warning("Failed to get network conditions from Redis", error=str(e))
            
            return self._network_conditions
    
    async def update_network_conditions(self, conditions: Dict[str, Any]):
        """
        更新網路條件
        
        Args:
            conditions: 網路條件數據
        """
        async with self._update_lock:
            self._network_conditions = NetworkConditions(
                timestamp=time.time(),
                **conditions
            )
            
            if self.redis_adapter:
                try:
                    await self.redis_adapter.set(
                        "network_conditions", 
                        conditions, 
                        ttl=30
                    )
                except Exception as e:
                    logger.warning("Failed to cache network conditions to Redis", error=str(e))
            
            logger.debug("Network conditions updated")
    
    async def update_handover_state(self, decision: Decision, result: ExecutionResult):
        """
        更新換手狀態
        
        Args:
            decision: 決策結果
            result: 執行結果
        """
        async with self._update_lock:
            handover_state = HandoverState(
                ue_id=decision.context.get("ue_id", "unknown"),
                source_satellite=decision.context.get("source_satellite", "unknown"),
                target_satellite=decision.selected_satellite,
                handover_type=decision.context.get("handover_type", "A4"),
                start_time=decision.context.get("start_time", time.time()),
                completion_time=time.time() if result.success else None,
                success=result.success,
                performance_metrics=result.performance_metrics
            )
            
            # 添加到歷史記錄
            self._handover_history.append(handover_state)
            
            # 更新活躍換手
            if result.success:
                handover_key = f"{handover_state.ue_id}_{handover_state.target_satellite}"
                self._active_handovers[handover_key] = handover_state
            
            logger.debug("Handover state updated",
                        ue_id=handover_state.ue_id,
                        success=handover_state.success)
    
    async def get_handover_history(self, limit: int = 100) -> List[HandoverState]:
        """
        獲取換手歷史
        
        Args:
            limit: 返回記錄數限制
            
        Returns:
            List[HandoverState]: 換手歷史列表
        """
        async with self._update_lock:
            return list(self._handover_history)[-limit:]
    
    async def get_active_handovers(self) -> Dict[str, HandoverState]:
        """
        獲取活躍的換手
        
        Returns:
            Dict[str, HandoverState]: 活躍換手字典
        """
        async with self._update_lock:
            return self._active_handovers.copy()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        獲取系統指標
        
        Returns:
            Dict[str, Any]: 系統指標數據
        """
        async with self._update_lock:
            return {
                "satellite_pool_size": len(self._satellite_pool),
                "active_handovers": len(self._active_handovers),
                "handover_history_size": len(self._handover_history),
                "network_conditions": self._network_conditions.__dict__ if self._network_conditions else {},
                "last_updated": time.time()
            }
    
    def _generate_mock_satellite_pool(self) -> List[Dict[str, Any]]:
        """生成模擬衛星池數據"""
        import random
        
        satellites = []
        for i in range(1, 21):  # 20顆衛星
            satellites.append({
                "satellite_id": f"SAT_{i:03d}",
                "elevation": random.uniform(10, 85),
                "signal_strength": random.uniform(-100, -70),
                "load_factor": random.uniform(0.1, 0.8),
                "distance": random.uniform(500, 2000),
                "azimuth": random.uniform(0, 360),
                "doppler_shift": random.uniform(-5000, 5000),
                "position": {
                    "x": random.uniform(-5000, 5000),
                    "y": random.uniform(-5000, 5000),
                    "z": random.uniform(500, 2000)
                },
                "velocity": {
                    "vx": random.uniform(-10, 10),
                    "vy": random.uniform(-10, 10),
                    "vz": random.uniform(-2, 2)
                },
                "visibility_time": random.uniform(300, 1800)
            })
        
        logger.debug("Generated mock satellite pool", satellites=len(satellites))
        return satellites
    
    async def cleanup_expired_handovers(self, expiry_time: float = 3600):
        """
        清理過期的活躍換手
        
        Args:
            expiry_time: 過期時間 (秒)
        """
        async with self._update_lock:
            current_time = time.time()
            expired_keys = []
            
            for key, handover in self._active_handovers.items():
                if current_time - handover.start_time > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._active_handovers[key]
            
            if expired_keys:
                logger.debug("Cleaned up expired handovers", count=len(expired_keys))