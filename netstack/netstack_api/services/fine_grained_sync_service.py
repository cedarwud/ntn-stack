"""
細粒度同步服務 (Fine-Grained Sync Service)

提供精細的同步控制和狀態管理，用於協調網路組件的同步狀態。
這個服務主要用於管理核心同步路由器中的細粒度同步操作。
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class SyncState(Enum):
    """同步狀態枚舉"""

    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    SYNCHRONIZED = "synchronized"
    PARTIAL_SYNC = "partial_sync"
    OUT_OF_SYNC = "out_of_sync"
    SYNCHRONIZING = "synchronizing"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class ComponentSync:
    """組件同步狀態"""

    component_id: str
    state: SyncState = SyncState.UNKNOWN
    last_sync_time: Optional[datetime] = None
    sync_accuracy: float = 0.0  # 同步精度 (ms)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncMetrics:
    """同步指標"""

    total_components: int = 0
    synchronized_components: int = 0
    partially_synced_components: int = 0
    failed_components: int = 0
    average_sync_accuracy: float = 0.0
    last_update_time: Optional[datetime] = None


class FineGrainedSyncService:
    """細粒度同步服務

    管理網路組件的細粒度同步狀態，提供：
    - 組件同步狀態追蹤
    - 同步精度監控
    - 同步失敗恢復
    - 同步指標統計
    """

    def __init__(self):
        self.component_states: Dict[str, ComponentSync] = {}
        self.sync_threshold: float = 1.0  # 同步閾值 (ms)
        self.max_error_count: int = 3
        self.metrics = SyncMetrics()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info("細粒度同步服務已初始化")

    async def start(self):
        """啟動同步服務"""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_sync_states())
        logger.info("細粒度同步服務已啟動")

    async def stop(self):
        """停止同步服務"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("細粒度同步服務已停止")

    def register_component(
        self, component_id: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """註冊組件"""
        if component_id not in self.component_states:
            self.component_states[component_id] = ComponentSync(
                component_id=component_id, metadata=metadata or {}
            )
            logger.info(f"組件已註冊: {component_id}")
            self._update_metrics()

    def unregister_component(self, component_id: str):
        """取消註冊組件"""
        if component_id in self.component_states:
            del self.component_states[component_id]
            logger.info(f"組件已取消註冊: {component_id}")
            self._update_metrics()

    def update_component_sync(
        self,
        component_id: str,
        state: SyncState,
        sync_accuracy: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """更新組件同步狀態"""
        if component_id not in self.component_states:
            self.register_component(component_id, metadata)

        component = self.component_states[component_id]
        old_state = component.state
        component.state = state
        component.last_sync_time = datetime.now(timezone.utc)

        if sync_accuracy is not None:
            component.sync_accuracy = sync_accuracy

        if metadata:
            component.metadata.update(metadata)

        # 處理狀態變化
        if old_state != state:
            if state == SyncState.FAILED:
                component.error_count += 1
                logger.warning(
                    f"組件 {component_id} 同步失敗 (錯誤計數: {component.error_count})"
                )
            elif state == SyncState.SYNCHRONIZED:
                component.error_count = 0
                logger.info(f"組件 {component_id} 同步成功")

        self._update_metrics()

    def get_component_state(self, component_id: str) -> Optional[ComponentSync]:
        """獲取組件同步狀態"""
        return self.component_states.get(component_id)

    def get_all_states(self) -> Dict[str, ComponentSync]:
        """獲取所有組件狀態"""
        return self.component_states.copy()

    def get_metrics(self) -> SyncMetrics:
        """獲取同步指標"""
        return self.metrics

    def is_component_synchronized(self, component_id: str) -> bool:
        """檢查組件是否同步"""
        component = self.component_states.get(component_id)
        if not component:
            return False

        return (
            component.state == SyncState.SYNCHRONIZED
            and component.sync_accuracy <= self.sync_threshold
        )

    def get_synchronized_components(self) -> List[str]:
        """獲取已同步的組件列表"""
        return [
            comp_id
            for comp_id, comp in self.component_states.items()
            if self.is_component_synchronized(comp_id)
        ]

    def get_failed_components(self) -> List[str]:
        """獲取失敗的組件列表"""
        return [
            comp_id
            for comp_id, comp in self.component_states.items()
            if comp.state == SyncState.FAILED
            or comp.error_count >= self.max_error_count
        ]

    async def sync_component(self, component_id: str) -> bool:
        """同步特定組件"""
        if component_id not in self.component_states:
            logger.error(f"組件未註冊: {component_id}")
            return False

        try:
            self.update_component_sync(component_id, SyncState.SYNCHRONIZING)

            # 模擬同步過程
            await asyncio.sleep(0.1)

            # 根據組件狀態決定同步結果
            component = self.component_states[component_id]
            if component.error_count >= self.max_error_count:
                self.update_component_sync(component_id, SyncState.FAILED)
                return False

            # 成功同步
            sync_accuracy = 0.5  # 模擬同步精度
            self.update_component_sync(
                component_id, SyncState.SYNCHRONIZED, sync_accuracy=sync_accuracy
            )
            return True

        except Exception as e:
            logger.error(f"同步組件 {component_id} 時發生錯誤: {e}")
            self.update_component_sync(component_id, SyncState.FAILED)
            return False

    async def sync_all_components(self) -> Dict[str, bool]:
        """同步所有組件"""
        results = {}
        tasks = []

        for component_id in self.component_states.keys():
            task = asyncio.create_task(self.sync_component(component_id))
            tasks.append((component_id, task))

        for component_id, task in tasks:
            try:
                results[component_id] = await task
            except Exception as e:
                logger.error(f"同步組件 {component_id} 時發生錯誤: {e}")
                results[component_id] = False

        return results

    def _update_metrics(self):
        """更新同步指標"""
        total = len(self.component_states)
        synchronized = sum(
            1
            for comp in self.component_states.values()
            if comp.state == SyncState.SYNCHRONIZED
        )
        partial_sync = sum(
            1
            for comp in self.component_states.values()
            if comp.state == SyncState.PARTIAL_SYNC
        )
        failed = sum(
            1
            for comp in self.component_states.values()
            if comp.state == SyncState.FAILED
        )

        # 計算平均同步精度
        accuracies = [
            comp.sync_accuracy
            for comp in self.component_states.values()
            if comp.sync_accuracy > 0
        ]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        self.metrics = SyncMetrics(
            total_components=total,
            synchronized_components=synchronized,
            partially_synced_components=partial_sync,
            failed_components=failed,
            average_sync_accuracy=avg_accuracy,
            last_update_time=datetime.now(timezone.utc),
        )

    async def _monitor_sync_states(self):
        """監控同步狀態"""
        while self._running:
            try:
                # 檢查長時間未更新的組件
                current_time = datetime.now(timezone.utc)
                timeout_threshold = timedelta(minutes=5)

                for component_id, component in self.component_states.items():
                    if (
                        component.last_sync_time
                        and current_time - component.last_sync_time > timeout_threshold
                    ):
                        logger.warning(f"組件 {component_id} 長時間未更新同步狀態")
                        self.update_component_sync(component_id, SyncState.OUT_OF_SYNC)

                # 嘗試恢復失敗的組件
                failed_components = self.get_failed_components()
                for component_id in failed_components:
                    component = self.component_states[component_id]
                    if component.error_count < self.max_error_count:
                        logger.info(f"嘗試恢復組件: {component_id}")
                        await self.sync_component(component_id)

                await asyncio.sleep(30)  # 每30秒檢查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"監控同步狀態時發生錯誤: {e}")
                await asyncio.sleep(10)
