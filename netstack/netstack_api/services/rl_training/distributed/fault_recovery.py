"""
故障恢復機制 - Phase 4 核心組件

實現分佈式訓練環境中的故障檢測和恢復：
- 節點故障檢測
- 任務自動恢復
- 系統狀態恢復
- 數據一致性保證

Features:
- 實時故障檢測
- 自動故障恢復
- 任務狀態保護
- 系統健壯性保證
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import copy
import pickle
import os

from .node_coordinator import NodeInfo, NodeStatus, NodeType, TrainingTask

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """故障類型"""
    NODE_TIMEOUT = "node_timeout"
    NODE_CRASH = "node_crash"
    TASK_FAILURE = "task_failure"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CORRUPTION = "corruption"


class RecoveryStrategy(Enum):
    """恢復策略"""
    IMMEDIATE = "immediate"        # 立即恢復
    DELAYED = "delayed"           # 延遲恢復
    MANUAL = "manual"             # 手動恢復
    GRACEFUL = "graceful"         # 優雅恢復
    AGGRESSIVE = "aggressive"     # 激進恢復


@dataclass
class FailureEvent:
    """故障事件"""
    failure_id: str
    failure_type: FailureType
    affected_node: str
    affected_tasks: List[str]
    detection_time: datetime
    description: str
    severity: str  # low, medium, high, critical
    recovery_strategy: RecoveryStrategy
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "failure_id": self.failure_id,
            "failure_type": self.failure_type.value,
            "affected_node": self.affected_node,
            "affected_tasks": self.affected_tasks,
            "detection_time": self.detection_time.isoformat(),
            "description": self.description,
            "severity": self.severity,
            "recovery_strategy": self.recovery_strategy.value,
            "recovery_attempts": self.recovery_attempts,
            "max_recovery_attempts": self.max_recovery_attempts,
            "resolved": self.resolved,
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None
        }


@dataclass
class SystemSnapshot:
    """系統快照"""
    snapshot_id: str
    timestamp: datetime
    nodes: Dict[str, NodeInfo]
    tasks: Dict[str, TrainingTask]
    system_state: Dict[str, Any]
    checksum: str
    
    def calculate_checksum(self) -> str:
        """計算校驗和"""
        data = {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "system_state": self.system_state
        }
        
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()


@dataclass
class RecoveryPlan:
    """恢復計劃"""
    plan_id: str
    failure_event: FailureEvent
    recovery_steps: List[Dict[str, Any]]
    estimated_duration: int
    priority: int
    dependencies: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "plan_id": self.plan_id,
            "failure_event": self.failure_event.to_dict(),
            "recovery_steps": self.recovery_steps,
            "estimated_duration": self.estimated_duration,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat()
        }


class FaultRecovery:
    """
    故障恢復機制
    
    實現分佈式訓練環境中的故障檢測和自動恢復，
    保證系統的高可用性和數據一致性。
    """
    
    def __init__(self,
                 detection_interval: int = 10,
                 recovery_timeout: int = 300,
                 max_recovery_attempts: int = 3,
                 snapshot_interval: int = 60,
                 enable_auto_recovery: bool = True):
        """
        初始化故障恢復機制
        
        Args:
            detection_interval: 故障檢測間隔（秒）
            recovery_timeout: 恢復超時時間（秒）
            max_recovery_attempts: 最大恢復嘗試次數
            snapshot_interval: 快照間隔（秒）
            enable_auto_recovery: 是否啟用自動恢復
        """
        self.detection_interval = detection_interval
        self.recovery_timeout = recovery_timeout
        self.max_recovery_attempts = max_recovery_attempts
        self.snapshot_interval = snapshot_interval
        self.enable_auto_recovery = enable_auto_recovery
        
        # 故障管理
        self.failure_events: Dict[str, FailureEvent] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.active_recoveries: Set[str] = set()
        
        # 系統快照
        self.snapshots: Dict[str, SystemSnapshot] = {}
        self.snapshot_history: List[str] = []
        self.max_snapshots = 10
        
        # 監控狀態
        self.monitored_nodes: Dict[str, NodeInfo] = {}
        self.monitored_tasks: Dict[str, TrainingTask] = {}
        
        # 運行狀態
        self.is_running = False
        self.detection_task = None
        self.recovery_task = None
        self.snapshot_task = None
        
        # 統計信息
        self.stats = {
            "total_failures": 0,
            "resolved_failures": 0,
            "failed_recoveries": 0,
            "average_recovery_time": 0.0,
            "system_uptime": 0.0,
            "last_failure": None,
            "start_time": datetime.now()
        }
        
        self.logger = logger
        
    async def start(self):
        """啟動故障恢復機制"""
        try:
            self.logger.info("🚀 啟動故障恢復機制...")
            
            # 創建快照目錄
            self.snapshot_dir = "/tmp/phase4_snapshots"
            os.makedirs(self.snapshot_dir, exist_ok=True)
            
            # 啟動監控任務
            self.detection_task = asyncio.create_task(self._failure_detection_loop())
            self.recovery_task = asyncio.create_task(self._recovery_loop())
            self.snapshot_task = asyncio.create_task(self._snapshot_loop())
            
            self.is_running = True
            self.stats["start_time"] = datetime.now()
            
            self.logger.info("✅ 故障恢復機制啟動成功")
            
        except Exception as e:
            self.logger.error(f"❌ 故障恢復機制啟動失敗: {e}")
            raise
    
    async def stop(self):
        """停止故障恢復機制"""
        try:
            self.logger.info("🛑 停止故障恢復機制...")
            
            self.is_running = False
            
            # 停止監控任務
            for task in [self.detection_task, self.recovery_task, self.snapshot_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # 保存最後一個快照
            if self.monitored_nodes or self.monitored_tasks:
                await self._create_snapshot("final_snapshot")
            
            self.logger.info("✅ 故障恢復機制已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止故障恢復機制失敗: {e}")
    
    async def update_system_state(self, 
                                nodes: Dict[str, NodeInfo], 
                                tasks: Dict[str, TrainingTask]):
        """更新系統狀態"""
        self.monitored_nodes = copy.deepcopy(nodes)
        self.monitored_tasks = copy.deepcopy(tasks)
    
    async def _failure_detection_loop(self):
        """故障檢測循環"""
        while self.is_running:
            try:
                # 檢測節點故障
                await self._detect_node_failures()
                
                # 檢測任務故障
                await self._detect_task_failures()
                
                # 檢測網絡分區
                await self._detect_network_partitions()
                
                # 檢測資源耗盡
                await self._detect_resource_exhaustion()
                
                await asyncio.sleep(self.detection_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 故障檢測循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _detect_node_failures(self):
        """檢測節點故障"""
        try:
            current_time = datetime.now()
            
            for node_id, node in self.monitored_nodes.items():
                # 檢測超時
                if node.last_heartbeat:
                    time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()
                    if time_since_heartbeat > 90:  # 90秒超時
                        await self._handle_node_timeout(node_id, time_since_heartbeat)
                
                # 檢測狀態異常
                if node.status == NodeStatus.ERROR:
                    await self._handle_node_error(node_id)
                
                # 檢測負載異常
                if node.current_load > 1.0:
                    await self._handle_node_overload(node_id, node.current_load)
                    
        except Exception as e:
            self.logger.error(f"❌ 節點故障檢測失敗: {e}")
    
    async def _detect_task_failures(self):
        """檢測任務故障"""
        try:
            current_time = datetime.now()
            
            for task_id, task in self.monitored_tasks.items():
                # 檢測長時間運行的任務
                if task.status == "running":
                    runtime = (current_time - task.created_at).total_seconds()
                    if runtime > 3600:  # 1小時超時
                        await self._handle_task_timeout(task_id, runtime)
                
                # 檢測失敗任務
                if task.status == "failed":
                    await self._handle_task_failure(task_id)
                    
        except Exception as e:
            self.logger.error(f"❌ 任務故障檢測失敗: {e}")
    
    async def _detect_network_partitions(self):
        """檢測網絡分區"""
        try:
            # 檢測節點間的連接狀態
            # 這裡可以實現 ping 測試或其他網絡檢測
            pass
            
        except Exception as e:
            self.logger.error(f"❌ 網絡分區檢測失敗: {e}")
    
    async def _detect_resource_exhaustion(self):
        """檢測資源耗盡"""
        try:
            # 檢測系統資源使用情況
            # 這裡可以實現 CPU、內存、磁盤使用率檢測
            pass
            
        except Exception as e:
            self.logger.error(f"❌ 資源耗盡檢測失敗: {e}")
    
    async def _handle_node_timeout(self, node_id: str, timeout_duration: float):
        """處理節點超時"""
        failure_id = f"node_timeout_{node_id}_{int(time.time())}"
        
        # 找到受影響的任務
        affected_tasks = [
            task_id for task_id, task in self.monitored_tasks.items()
            if task.assigned_node == node_id and task.status in ["assigned", "running"]
        ]
        
        failure_event = FailureEvent(
            failure_id=failure_id,
            failure_type=FailureType.NODE_TIMEOUT,
            affected_node=node_id,
            affected_tasks=affected_tasks,
            detection_time=datetime.now(),
            description=f"Node {node_id} timeout after {timeout_duration:.1f} seconds",
            severity="high",
            recovery_strategy=RecoveryStrategy.IMMEDIATE
        )
        
        await self._register_failure(failure_event)
    
    async def _handle_node_error(self, node_id: str):
        """處理節點錯誤"""
        failure_id = f"node_error_{node_id}_{int(time.time())}"
        
        affected_tasks = [
            task_id for task_id, task in self.monitored_tasks.items()
            if task.assigned_node == node_id and task.status in ["assigned", "running"]
        ]
        
        failure_event = FailureEvent(
            failure_id=failure_id,
            failure_type=FailureType.NODE_CRASH,
            affected_node=node_id,
            affected_tasks=affected_tasks,
            detection_time=datetime.now(),
            description=f"Node {node_id} in error state",
            severity="high",
            recovery_strategy=RecoveryStrategy.GRACEFUL
        )
        
        await self._register_failure(failure_event)
    
    async def _handle_node_overload(self, node_id: str, load: float):
        """處理節點過載"""
        failure_id = f"node_overload_{node_id}_{int(time.time())}"
        
        failure_event = FailureEvent(
            failure_id=failure_id,
            failure_type=FailureType.RESOURCE_EXHAUSTION,
            affected_node=node_id,
            affected_tasks=[],
            detection_time=datetime.now(),
            description=f"Node {node_id} overloaded (load: {load:.2f})",
            severity="medium",
            recovery_strategy=RecoveryStrategy.DELAYED
        )
        
        await self._register_failure(failure_event)
    
    async def _handle_task_timeout(self, task_id: str, runtime: float):
        """處理任務超時"""
        failure_id = f"task_timeout_{task_id}_{int(time.time())}"
        
        task = self.monitored_tasks[task_id]
        
        failure_event = FailureEvent(
            failure_id=failure_id,
            failure_type=FailureType.TASK_FAILURE,
            affected_node=task.assigned_node or "unknown",
            affected_tasks=[task_id],
            detection_time=datetime.now(),
            description=f"Task {task_id} timeout after {runtime:.1f} seconds",
            severity="medium",
            recovery_strategy=RecoveryStrategy.IMMEDIATE
        )
        
        await self._register_failure(failure_event)
    
    async def _handle_task_failure(self, task_id: str):
        """處理任務失敗"""
        failure_id = f"task_failure_{task_id}_{int(time.time())}"
        
        task = self.monitored_tasks[task_id]
        
        failure_event = FailureEvent(
            failure_id=failure_id,
            failure_type=FailureType.TASK_FAILURE,
            affected_node=task.assigned_node or "unknown",
            affected_tasks=[task_id],
            detection_time=datetime.now(),
            description=f"Task {task_id} failed",
            severity="low",
            recovery_strategy=RecoveryStrategy.IMMEDIATE
        )
        
        await self._register_failure(failure_event)
    
    async def _register_failure(self, failure_event: FailureEvent):
        """註冊故障事件"""
        self.failure_events[failure_event.failure_id] = failure_event
        self.stats["total_failures"] += 1
        self.stats["last_failure"] = failure_event.detection_time
        
        self.logger.warning(f"⚠️ 故障事件註冊: {failure_event.failure_id} - {failure_event.description}")
        
        # 如果啟用自動恢復，創建恢復計劃
        if self.enable_auto_recovery:
            await self._create_recovery_plan(failure_event)
    
    async def _create_recovery_plan(self, failure_event: FailureEvent):
        """創建恢復計劃"""
        try:
            plan_id = f"recovery_plan_{failure_event.failure_id}"
            
            # 根據故障類型創建不同的恢復步驟
            recovery_steps = []
            
            if failure_event.failure_type == FailureType.NODE_TIMEOUT:
                recovery_steps = [
                    {"step": "verify_node_status", "node_id": failure_event.affected_node},
                    {"step": "reassign_tasks", "tasks": failure_event.affected_tasks},
                    {"step": "remove_failed_node", "node_id": failure_event.affected_node}
                ]
            elif failure_event.failure_type == FailureType.TASK_FAILURE:
                recovery_steps = [
                    {"step": "analyze_task_failure", "task_id": failure_event.affected_tasks[0]},
                    {"step": "restart_task", "task_id": failure_event.affected_tasks[0]},
                    {"step": "monitor_task_progress", "task_id": failure_event.affected_tasks[0]}
                ]
            elif failure_event.failure_type == FailureType.RESOURCE_EXHAUSTION:
                recovery_steps = [
                    {"step": "redistribute_load", "node_id": failure_event.affected_node},
                    {"step": "scale_resources", "node_id": failure_event.affected_node},
                    {"step": "monitor_resource_usage", "node_id": failure_event.affected_node}
                ]
            
            # 估算恢復時間
            estimated_duration = len(recovery_steps) * 30  # 每步驟 30 秒
            
            recovery_plan = RecoveryPlan(
                plan_id=plan_id,
                failure_event=failure_event,
                recovery_steps=recovery_steps,
                estimated_duration=estimated_duration,
                priority=self._calculate_recovery_priority(failure_event),
                dependencies=[],
                created_at=datetime.now()
            )
            
            self.recovery_plans[plan_id] = recovery_plan
            
            self.logger.info(f"📋 恢復計劃創建: {plan_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 恢復計劃創建失敗: {e}")
    
    def _calculate_recovery_priority(self, failure_event: FailureEvent) -> int:
        """計算恢復優先級"""
        priority = 0
        
        # 根據嚴重程度調整優先級
        severity_weights = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        priority += severity_weights.get(failure_event.severity, 1) * 10
        
        # 根據受影響的任務數量調整
        priority += len(failure_event.affected_tasks) * 5
        
        # 根據故障類型調整
        type_weights = {
            FailureType.NODE_TIMEOUT: 15,
            FailureType.NODE_CRASH: 20,
            FailureType.TASK_FAILURE: 5,
            FailureType.NETWORK_PARTITION: 25,
            FailureType.RESOURCE_EXHAUSTION: 10
        }
        
        priority += type_weights.get(failure_event.failure_type, 5)
        
        return priority
    
    async def _recovery_loop(self):
        """恢復循環"""
        while self.is_running:
            try:
                # 執行恢復計劃
                await self._execute_recovery_plans()
                
                # 清理已完成的恢復
                await self._cleanup_completed_recoveries()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"❌ 恢復循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _execute_recovery_plans(self):
        """執行恢復計劃"""
        try:
            # 按優先級排序恢復計劃
            sorted_plans = sorted(
                self.recovery_plans.values(),
                key=lambda p: p.priority,
                reverse=True
            )
            
            for plan in sorted_plans:
                if plan.plan_id in self.active_recoveries:
                    continue
                
                failure_event = plan.failure_event
                
                # 檢查是否超過最大恢復嘗試次數
                if failure_event.recovery_attempts >= failure_event.max_recovery_attempts:
                    self.logger.error(f"❌ 恢復失敗，超過最大嘗試次數: {plan.plan_id}")
                    failure_event.resolved = False
                    self.stats["failed_recoveries"] += 1
                    continue
                
                # 執行恢復
                self.active_recoveries.add(plan.plan_id)
                asyncio.create_task(self._execute_single_recovery(plan))
                
        except Exception as e:
            self.logger.error(f"❌ 恢復計劃執行失敗: {e}")
    
    async def _execute_single_recovery(self, plan: RecoveryPlan):
        """執行單個恢復計劃"""
        try:
            self.logger.info(f"🔧 開始執行恢復計劃: {plan.plan_id}")
            
            start_time = datetime.now()
            plan.failure_event.recovery_attempts += 1
            
            # 逐步執行恢復步驟
            for i, step in enumerate(plan.recovery_steps):
                try:
                    self.logger.info(f"🔧 執行恢復步驟 {i+1}/{len(plan.recovery_steps)}: {step['step']}")
                    
                    # 執行具體的恢復步驟
                    success = await self._execute_recovery_step(step)
                    
                    if not success:
                        self.logger.error(f"❌ 恢復步驟失敗: {step['step']}")
                        break
                    
                    await asyncio.sleep(1)  # 步驟間隔
                    
                except Exception as e:
                    self.logger.error(f"❌ 恢復步驟執行錯誤: {e}")
                    break
            else:
                # 所有步驟成功完成
                plan.failure_event.resolved = True
                plan.failure_event.resolution_time = datetime.now()
                
                # 更新統計
                self.stats["resolved_failures"] += 1
                recovery_time = (datetime.now() - start_time).total_seconds()
                
                # 計算平均恢復時間
                current_avg = self.stats["average_recovery_time"]
                resolved_count = self.stats["resolved_failures"]
                self.stats["average_recovery_time"] = (
                    (current_avg * (resolved_count - 1) + recovery_time) / resolved_count
                )
                
                self.logger.info(f"✅ 恢復計劃完成: {plan.plan_id} (耗時: {recovery_time:.1f}s)")
            
        except Exception as e:
            self.logger.error(f"❌ 恢復計劃執行失敗: {e}")
        finally:
            self.active_recoveries.discard(plan.plan_id)
    
    async def _execute_recovery_step(self, step: Dict[str, Any]) -> bool:
        """執行恢復步驟"""
        try:
            step_type = step["step"]
            
            if step_type == "verify_node_status":
                return await self._verify_node_status(step["node_id"])
            elif step_type == "reassign_tasks":
                return await self._reassign_tasks(step["tasks"])
            elif step_type == "remove_failed_node":
                return await self._remove_failed_node(step["node_id"])
            elif step_type == "analyze_task_failure":
                return await self._analyze_task_failure(step["task_id"])
            elif step_type == "restart_task":
                return await self._restart_task(step["task_id"])
            elif step_type == "monitor_task_progress":
                return await self._monitor_task_progress(step["task_id"])
            elif step_type == "redistribute_load":
                return await self._redistribute_load(step["node_id"])
            elif step_type == "scale_resources":
                return await self._scale_resources(step["node_id"])
            elif step_type == "monitor_resource_usage":
                return await self._monitor_resource_usage(step["node_id"])
            else:
                self.logger.warning(f"⚠️ 未知的恢復步驟類型: {step_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 恢復步驟執行失敗: {e}")
            return False
    
    async def _verify_node_status(self, node_id: str) -> bool:
        """驗證節點狀態"""
        # 模擬節點狀態驗證
        self.logger.info(f"🔍 驗證節點狀態: {node_id}")
        await asyncio.sleep(1)
        return True
    
    async def _reassign_tasks(self, task_ids: List[str]) -> bool:
        """重新分配任務"""
        self.logger.info(f"🔄 重新分配任務: {task_ids}")
        await asyncio.sleep(2)
        return True
    
    async def _remove_failed_node(self, node_id: str) -> bool:
        """移除失敗節點"""
        self.logger.info(f"🗑️ 移除失敗節點: {node_id}")
        await asyncio.sleep(1)
        return True
    
    async def _analyze_task_failure(self, task_id: str) -> bool:
        """分析任務失敗原因"""
        self.logger.info(f"🔍 分析任務失敗: {task_id}")
        await asyncio.sleep(1)
        return True
    
    async def _restart_task(self, task_id: str) -> bool:
        """重啟任務"""
        self.logger.info(f"🔄 重啟任務: {task_id}")
        await asyncio.sleep(2)
        return True
    
    async def _monitor_task_progress(self, task_id: str) -> bool:
        """監控任務進度"""
        self.logger.info(f"📊 監控任務進度: {task_id}")
        await asyncio.sleep(1)
        return True
    
    async def _redistribute_load(self, node_id: str) -> bool:
        """重新分配負載"""
        self.logger.info(f"⚖️ 重新分配負載: {node_id}")
        await asyncio.sleep(2)
        return True
    
    async def _scale_resources(self, node_id: str) -> bool:
        """擴展資源"""
        self.logger.info(f"📈 擴展資源: {node_id}")
        await asyncio.sleep(3)
        return True
    
    async def _monitor_resource_usage(self, node_id: str) -> bool:
        """監控資源使用"""
        self.logger.info(f"📊 監控資源使用: {node_id}")
        await asyncio.sleep(1)
        return True
    
    async def _cleanup_completed_recoveries(self):
        """清理已完成的恢復"""
        try:
            completed_plans = [
                plan_id for plan_id, plan in self.recovery_plans.items()
                if plan.failure_event.resolved or 
                   plan.failure_event.recovery_attempts >= plan.failure_event.max_recovery_attempts
            ]
            
            for plan_id in completed_plans:
                del self.recovery_plans[plan_id]
                
        except Exception as e:
            self.logger.error(f"❌ 清理已完成恢復失敗: {e}")
    
    async def _snapshot_loop(self):
        """快照循環"""
        while self.is_running:
            try:
                # 創建系統快照
                snapshot_id = f"snapshot_{int(time.time())}"
                await self._create_snapshot(snapshot_id)
                
                # 清理舊快照
                await self._cleanup_old_snapshots()
                
                await asyncio.sleep(self.snapshot_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 快照循環錯誤: {e}")
                await asyncio.sleep(30)
    
    async def _create_snapshot(self, snapshot_id: str):
        """創建系統快照"""
        try:
            snapshot = SystemSnapshot(
                snapshot_id=snapshot_id,
                timestamp=datetime.now(),
                nodes=copy.deepcopy(self.monitored_nodes),
                tasks=copy.deepcopy(self.monitored_tasks),
                system_state={
                    "failure_events": len(self.failure_events),
                    "recovery_plans": len(self.recovery_plans),
                    "active_recoveries": len(self.active_recoveries)
                },
                checksum=""
            )
            
            snapshot.checksum = snapshot.calculate_checksum()
            
            # 保存快照
            self.snapshots[snapshot_id] = snapshot
            self.snapshot_history.append(snapshot_id)
            
            # 保存到文件
            snapshot_file = os.path.join(self.snapshot_dir, f"{snapshot_id}.pkl")
            with open(snapshot_file, 'wb') as f:
                pickle.dump(snapshot, f)
            
            self.logger.debug(f"📸 系統快照創建: {snapshot_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 創建系統快照失敗: {e}")
    
    async def _cleanup_old_snapshots(self):
        """清理舊快照"""
        try:
            # 保持最大快照數量
            while len(self.snapshot_history) > self.max_snapshots:
                oldest_snapshot = self.snapshot_history.pop(0)
                
                # 從內存中刪除
                if oldest_snapshot in self.snapshots:
                    del self.snapshots[oldest_snapshot]
                
                # 刪除文件
                snapshot_file = os.path.join(self.snapshot_dir, f"{oldest_snapshot}.pkl")
                if os.path.exists(snapshot_file):
                    os.remove(snapshot_file)
                    
        except Exception as e:
            self.logger.error(f"❌ 清理舊快照失敗: {e}")
    
    async def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """從快照恢復"""
        try:
            snapshot = self.snapshots.get(snapshot_id)
            if not snapshot:
                # 嘗試從文件載入
                snapshot_file = os.path.join(self.snapshot_dir, f"{snapshot_id}.pkl")
                if os.path.exists(snapshot_file):
                    with open(snapshot_file, 'rb') as f:
                        snapshot = pickle.load(f)
                else:
                    self.logger.error(f"❌ 快照不存在: {snapshot_id}")
                    return False
            
            # 驗證快照完整性
            if snapshot.checksum != snapshot.calculate_checksum():
                self.logger.error(f"❌ 快照校驗失敗: {snapshot_id}")
                return False
            
            # 恢復系統狀態
            self.monitored_nodes = snapshot.nodes
            self.monitored_tasks = snapshot.tasks
            
            self.logger.info(f"✅ 從快照恢復系統狀態: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 從快照恢復失敗: {e}")
            return False
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """獲取故障統計"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "active_failures": len([f for f in self.failure_events.values() if not f.resolved]),
            "active_recoveries": len(self.active_recoveries),
            "recovery_plans": len(self.recovery_plans),
            "snapshots": len(self.snapshots),
            "failure_types": {
                failure_type.value: len([f for f in self.failure_events.values() 
                                       if f.failure_type == failure_type])
                for failure_type in FailureType
            }
        }
    
    def get_failure_history(self) -> List[Dict[str, Any]]:
        """獲取故障歷史"""
        return [failure.to_dict() for failure in self.failure_events.values()]
    
    def get_recovery_plans(self) -> List[Dict[str, Any]]:
        """獲取恢復計劃"""
        return [plan.to_dict() for plan in self.recovery_plans.values()]
    
    def get_snapshots(self) -> List[Dict[str, Any]]:
        """獲取快照列表"""
        return [
            {
                "snapshot_id": snapshot.snapshot_id,
                "timestamp": snapshot.timestamp.isoformat(),
                "nodes_count": len(snapshot.nodes),
                "tasks_count": len(snapshot.tasks),
                "checksum": snapshot.checksum
            }
            for snapshot in self.snapshots.values()
        ]
