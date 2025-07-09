"""
動畫同步管理器
=============

管理多個動畫之間的同步和協調。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from ..interfaces.visualization_coordinator import AnimationState, AnimationType

logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """同步模式"""
    SEQUENTIAL = "sequential"  # 順序執行
    PARALLEL = "parallel"     # 並行執行
    CONDITIONAL = "conditional"  # 條件執行


@dataclass
class AnimationGroup:
    """動畫組"""
    group_id: str
    animations: List[str]  # 動畫ID列表
    sync_mode: SyncMode
    priority: int = 0
    conditions: Dict[str, Any] = None
    start_delay: float = 0.0
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}


@dataclass
class SyncEvent:
    """同步事件"""
    event_id: str
    event_type: str
    trigger_animations: List[str]
    timestamp: float
    data: Dict[str, Any]


class AnimationSyncManager:
    """
    動畫同步管理器
    
    管理多個動畫之間的同步和協調：
    - 動畫組管理
    - 同步事件處理
    - 依賴關係管理
    - 衝突檢測和解決
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化動畫同步管理器
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logger.bind(component="animation_sync_manager")
        
        # 動畫組管理
        self.animation_groups: Dict[str, AnimationGroup] = {}
        self.group_states: Dict[str, str] = {}  # group_id -> state
        
        # 同步事件
        self.sync_events: List[SyncEvent] = []
        self.event_handlers: Dict[str, List[callable]] = defaultdict(list)
        
        # 依賴關係
        self.dependencies: Dict[str, List[str]] = defaultdict(list)  # animation_id -> [depends_on]
        self.dependents: Dict[str, List[str]] = defaultdict(list)    # animation_id -> [dependent_animations]
        
        # 動畫狀態快取
        self.animation_states: Dict[str, AnimationState] = {}
        
        # 衝突檢測
        self.conflict_rules: List[Dict[str, Any]] = []
        self.resource_locks: Dict[str, str] = {}  # resource -> animation_id
        
        # 配置參數
        self.max_parallel_animations = self.config.get("max_parallel", 10)
        self.default_sync_timeout = self.config.get("sync_timeout", 30.0)
        self.conflict_resolution = self.config.get("conflict_resolution", "priority")
        
        # 任務管理
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # 載入預設同步規則
        self._load_default_sync_rules()
        
        self.logger.info("動畫同步管理器初始化完成")

    async def start(self):
        """啟動同步管理器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("動畫同步管理器已啟動")

    async def stop(self):
        """停止同步管理器"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # 取消所有同步任務
        for task in self.sync_tasks.values():
            task.cancel()
            
        # 等待任務完成
        if self.sync_tasks:
            await asyncio.gather(*self.sync_tasks.values(), return_exceptions=True)
        
        self.sync_tasks.clear()
        self.logger.info("動畫同步管理器已停止")

    def create_animation_group(self, group_id: str, animations: List[str], 
                             sync_mode: SyncMode = SyncMode.SEQUENTIAL,
                             priority: int = 0, conditions: Dict[str, Any] = None,
                             start_delay: float = 0.0) -> AnimationGroup:
        """
        創建動畫組
        
        Args:
            group_id: 組ID
            animations: 動畫ID列表
            sync_mode: 同步模式
            priority: 優先級
            conditions: 條件
            start_delay: 開始延遲
            
        Returns:
            AnimationGroup: 動畫組
        """
        group = AnimationGroup(
            group_id=group_id,
            animations=animations,
            sync_mode=sync_mode,
            priority=priority,
            conditions=conditions or {},
            start_delay=start_delay,
        )
        
        self.animation_groups[group_id] = group
        self.group_states[group_id] = "created"
        
        self.logger.info(
            "動畫組創建成功",
            group_id=group_id,
            animations=animations,
            sync_mode=sync_mode.value,
        )
        
        return group

    def add_dependency(self, animation_id: str, depends_on: str):
        """
        添加依賴關係
        
        Args:
            animation_id: 動畫ID
            depends_on: 依賴的動畫ID
        """
        self.dependencies[animation_id].append(depends_on)
        self.dependents[depends_on].append(animation_id)
        
        self.logger.debug(
            "依賴關係添加",
            animation_id=animation_id,
            depends_on=depends_on,
        )

    def remove_dependency(self, animation_id: str, depends_on: str):
        """
        移除依賴關係
        
        Args:
            animation_id: 動畫ID
            depends_on: 依賴的動畫ID
        """
        if depends_on in self.dependencies[animation_id]:
            self.dependencies[animation_id].remove(depends_on)
            
        if animation_id in self.dependents[depends_on]:
            self.dependents[depends_on].remove(animation_id)
            
        self.logger.debug(
            "依賴關係移除",
            animation_id=animation_id,
            depends_on=depends_on,
        )

    async def execute_animation_group(self, group_id: str) -> bool:
        """
        執行動畫組
        
        Args:
            group_id: 組ID
            
        Returns:
            bool: 是否執行成功
        """
        if group_id not in self.animation_groups:
            self.logger.error("動畫組不存在", group_id=group_id)
            return False
            
        group = self.animation_groups[group_id]
        
        try:
            # 檢查條件
            if not self._check_conditions(group.conditions):
                self.logger.warning("動畫組條件不滿足", group_id=group_id)
                return False
            
            # 更新狀態
            self.group_states[group_id] = "executing"
            
            # 等待開始延遲
            if group.start_delay > 0:
                await asyncio.sleep(group.start_delay)
            
            # 根據同步模式執行
            if group.sync_mode == SyncMode.SEQUENTIAL:
                success = await self._execute_sequential(group)
            elif group.sync_mode == SyncMode.PARALLEL:
                success = await self._execute_parallel(group)
            elif group.sync_mode == SyncMode.CONDITIONAL:
                success = await self._execute_conditional(group)
            else:
                self.logger.error("不支持的同步模式", sync_mode=group.sync_mode)
                success = False
            
            # 更新狀態
            self.group_states[group_id] = "completed" if success else "failed"
            
            self.logger.info(
                "動畫組執行完成",
                group_id=group_id,
                success=success,
            )
            
            return success
            
        except Exception as e:
            self.group_states[group_id] = "failed"
            self.logger.error("動畫組執行失敗", group_id=group_id, error=str(e))
            return False

    def trigger_sync_event(self, event_type: str, trigger_animations: List[str], 
                          data: Dict[str, Any] = None):
        """
        觸發同步事件
        
        Args:
            event_type: 事件類型
            trigger_animations: 觸發動畫列表
            data: 事件數據
        """
        event = SyncEvent(
            event_id=f"sync_{int(datetime.now().timestamp() * 1000)}",
            event_type=event_type,
            trigger_animations=trigger_animations,
            timestamp=datetime.now().timestamp(),
            data=data or {},
        )
        
        self.sync_events.append(event)
        
        # 觸發事件處理器
        asyncio.create_task(self._handle_sync_event(event))
        
        self.logger.debug(
            "同步事件觸發",
            event_type=event_type,
            trigger_animations=trigger_animations,
        )

    def register_event_handler(self, event_type: str, handler: callable):
        """
        註冊事件處理器
        
        Args:
            event_type: 事件類型
            handler: 處理器函數
        """
        self.event_handlers[event_type].append(handler)
        self.logger.debug("事件處理器註冊", event_type=event_type)

    def check_conflicts(self, animation_ids: List[str]) -> List[Dict[str, Any]]:
        """
        檢查動畫衝突
        
        Args:
            animation_ids: 動畫ID列表
            
        Returns:
            List[Dict[str, Any]]: 衝突列表
        """
        conflicts = []
        
        for rule in self.conflict_rules:
            conflict = self._check_conflict_rule(rule, animation_ids)
            if conflict:
                conflicts.append(conflict)
        
        return conflicts

    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """
        解決衝突
        
        Args:
            conflicts: 衝突列表
            
        Returns:
            List[str]: 解決後的動畫ID列表
        """
        if not conflicts:
            return []
            
        resolved_animations = []
        
        for conflict in conflicts:
            resolution = self._resolve_conflict(conflict)
            if resolution:
                resolved_animations.extend(resolution)
        
        return resolved_animations

    def get_animation_dependencies(self, animation_id: str) -> List[str]:
        """
        獲取動畫依賴
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            List[str]: 依賴的動畫ID列表
        """
        return self.dependencies.get(animation_id, [])

    def get_animation_dependents(self, animation_id: str) -> List[str]:
        """
        獲取動畫依賴者
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            List[str]: 依賴該動畫的動畫ID列表
        """
        return self.dependents.get(animation_id, [])

    def is_animation_ready(self, animation_id: str) -> bool:
        """
        檢查動畫是否準備就緒
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否準備就緒
        """
        dependencies = self.get_animation_dependencies(animation_id)
        
        for dep_id in dependencies:
            if dep_id not in self.animation_states:
                return False
                
            dep_state = self.animation_states[dep_id]
            if dep_state.status not in ["completed", "success"]:
                return False
        
        return True

    # 私有方法
    async def _execute_sequential(self, group: AnimationGroup) -> bool:
        """順序執行動畫組"""
        for animation_id in group.animations:
            if not await self._wait_for_animation_ready(animation_id):
                return False
                
            # 模擬動畫執行
            await self._simulate_animation_execution(animation_id)
            
            # 檢查執行結果
            if animation_id in self.animation_states:
                state = self.animation_states[animation_id]
                if state.status not in ["completed", "success"]:
                    return False
        
        return True

    async def _execute_parallel(self, group: AnimationGroup) -> bool:
        """並行執行動畫組"""
        # 等待所有動畫準備就緒
        ready_tasks = []
        for animation_id in group.animations:
            task = asyncio.create_task(self._wait_for_animation_ready(animation_id))
            ready_tasks.append(task)
        
        ready_results = await asyncio.gather(*ready_tasks, return_exceptions=True)
        
        # 檢查是否都準備就緒
        if not all(result for result in ready_results if not isinstance(result, Exception)):
            return False
        
        # 並行執行動畫
        execution_tasks = []
        for animation_id in group.animations:
            task = asyncio.create_task(self._simulate_animation_execution(animation_id))
            execution_tasks.append(task)
        
        execution_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # 檢查執行結果
        success_count = 0
        for i, result in enumerate(execution_results):
            if isinstance(result, Exception):
                continue
                
            animation_id = group.animations[i]
            if animation_id in self.animation_states:
                state = self.animation_states[animation_id]
                if state.status in ["completed", "success"]:
                    success_count += 1
        
        return success_count == len(group.animations)

    async def _execute_conditional(self, group: AnimationGroup) -> bool:
        """條件執行動畫組"""
        executed_animations = []
        
        for animation_id in group.animations:
            # 檢查條件
            animation_conditions = group.conditions.get(animation_id, {})
            if not self._check_conditions(animation_conditions):
                continue
            
            # 等待準備就緒
            if not await self._wait_for_animation_ready(animation_id):
                continue
            
            # 執行動畫
            await self._simulate_animation_execution(animation_id)
            executed_animations.append(animation_id)
        
        return len(executed_animations) > 0

    async def _wait_for_animation_ready(self, animation_id: str, timeout: float = None) -> bool:
        """等待動畫準備就緒"""
        if timeout is None:
            timeout = self.default_sync_timeout
        
        start_time = datetime.now().timestamp()
        
        while datetime.now().timestamp() - start_time < timeout:
            if self.is_animation_ready(animation_id):
                return True
            await asyncio.sleep(0.1)
        
        self.logger.warning("動畫準備就緒超時", animation_id=animation_id)
        return False

    async def _simulate_animation_execution(self, animation_id: str):
        """模擬動畫執行"""
        # 創建動畫狀態
        state = AnimationState(
            animation_id=animation_id,
            status="active",
            progress=0.0,
            start_time=datetime.now().timestamp(),
            duration=2.0,  # 2秒默認持續時間
            parameters={},
        )
        
        self.animation_states[animation_id] = state
        
        # 模擬執行過程
        for i in range(10):
            await asyncio.sleep(0.2)
            state.progress = (i + 1) / 10
        
        # 標記完成
        state.status = "completed"
        state.progress = 1.0

    def _check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """檢查條件"""
        if not conditions:
            return True
        
        # 簡化條件檢查
        for key, value in conditions.items():
            if key == "min_confidence" and hasattr(self, 'last_decision_confidence'):
                if self.last_decision_confidence < value:
                    return False
            elif key == "max_concurrent_animations":
                active_count = sum(1 for state in self.animation_states.values() 
                                 if state.status == "active")
                if active_count >= value:
                    return False
        
        return True

    async def _handle_sync_event(self, event: SyncEvent):
        """處理同步事件"""
        try:
            # 調用事件處理器
            handlers = self.event_handlers.get(event.event_type, [])
            for handler in handlers:
                await handler(event)
            
            self.logger.debug(
                "同步事件處理完成",
                event_type=event.event_type,
                handlers_count=len(handlers),
            )
            
        except Exception as e:
            self.logger.error("同步事件處理失敗", event_type=event.event_type, error=str(e))

    def _check_conflict_rule(self, rule: Dict[str, Any], animation_ids: List[str]) -> Optional[Dict[str, Any]]:
        """檢查衝突規則"""
        conflict_type = rule.get("type")
        
        if conflict_type == "resource_conflict":
            # 資源衝突檢查
            resource = rule.get("resource")
            conflicting_animations = []
            
            for animation_id in animation_ids:
                # 簡化檢查，實際應該檢查動畫使用的資源
                if resource in self.resource_locks:
                    conflicting_animations.append(animation_id)
            
            if len(conflicting_animations) > 1:
                return {
                    "type": "resource_conflict",
                    "resource": resource,
                    "conflicting_animations": conflicting_animations,
                    "rule": rule,
                }
        
        return None

    def _resolve_conflict(self, conflict: Dict[str, Any]) -> List[str]:
        """解決衝突"""
        if self.conflict_resolution == "priority":
            # 按優先級解決
            animations = conflict.get("conflicting_animations", [])
            if animations:
                # 簡化實現，返回第一個動畫
                return [animations[0]]
        
        return []

    def _load_default_sync_rules(self):
        """載入預設同步規則"""
        self.conflict_rules = [
            {
                "type": "resource_conflict",
                "resource": "camera",
                "description": "攝像機資源衝突",
            },
            {
                "type": "resource_conflict", 
                "resource": "satellite_highlight",
                "description": "衛星高亮資源衝突",
            },
        ]