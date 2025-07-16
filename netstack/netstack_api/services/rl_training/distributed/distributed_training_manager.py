"""
分佈式訓練管理器 - Phase 4 核心組件

整合所有分佈式訓練組件，提供統一的訓練管理介面：
- 訓練任務編排
- 節點協調管理
- 負載均衡控制
- 故障恢復機制
- 性能監控分析

Features:
- 全自動化訓練流程
- 智能資源調度
- 實時監控與分析
- 高可用性保證
- 彈性擴展能力
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from .node_coordinator import NodeCoordinator, NodeInfo, NodeStatus, NodeType, TrainingTask
from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .fault_recovery import FaultRecovery, FailureEvent, RecoveryStrategy

logger = logging.getLogger(__name__)


class TrainingPhase(Enum):
    """訓練階段"""
    INITIALIZING = "initializing"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingMode(Enum):
    """訓練模式"""
    SINGLE_NODE = "single_node"
    MULTI_NODE = "multi_node"
    FEDERATED = "federated"
    HIERARCHICAL = "hierarchical"


@dataclass
class TrainingConfiguration:
    """訓練配置"""
    algorithm: str  # DQN, PPO, SAC
    environment: str
    hyperparameters: Dict[str, Any]
    training_mode: TrainingMode
    max_nodes: int
    min_nodes: int
    resource_requirements: Dict[str, Any]
    training_steps: int
    evaluation_frequency: int
    checkpoint_frequency: int
    timeout: int
    enable_fault_recovery: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "algorithm": self.algorithm,
            "environment": self.environment,
            "hyperparameters": self.hyperparameters,
            "training_mode": self.training_mode.value,
            "max_nodes": self.max_nodes,
            "min_nodes": self.min_nodes,
            "resource_requirements": self.resource_requirements,
            "training_steps": self.training_steps,
            "evaluation_frequency": self.evaluation_frequency,
            "checkpoint_frequency": self.checkpoint_frequency,
            "timeout": self.timeout,
            "enable_fault_recovery": self.enable_fault_recovery
        }


@dataclass
class TrainingSession:
    """訓練會話"""
    session_id: str
    configuration: TrainingConfiguration
    phase: TrainingPhase
    assigned_nodes: List[str]
    tasks: Dict[str, TrainingTask]
    start_time: datetime
    end_time: Optional[datetime] = None
    current_step: int = 0
    total_steps: int = 0
    best_performance: float = float('-inf')
    last_checkpoint: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "session_id": self.session_id,
            "configuration": self.configuration.to_dict(),
            "phase": self.phase.value,
            "assigned_nodes": self.assigned_nodes,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "best_performance": self.best_performance,
            "last_checkpoint": self.last_checkpoint,
            "metrics": self.metrics,
            "logs": self.logs
        }


@dataclass
class TrainingMetrics:
    """訓練指標"""
    session_id: str
    timestamp: datetime
    node_id: str
    step: int
    episode_reward: float
    episode_length: int
    loss: float
    learning_rate: float
    epsilon: float
    q_values: List[float]
    actor_loss: Optional[float] = None
    critic_loss: Optional[float] = None
    entropy: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "node_id": self.node_id,
            "step": self.step,
            "episode_reward": self.episode_reward,
            "episode_length": self.episode_length,
            "loss": self.loss,
            "learning_rate": self.learning_rate,
            "epsilon": self.epsilon,
            "q_values": self.q_values,
            "actor_loss": self.actor_loss,
            "critic_loss": self.critic_loss,
            "entropy": self.entropy
        }


class DistributedTrainingManager:
    """
    分佈式訓練管理器
    
    整合所有分佈式訓練組件，提供統一的訓練管理介面，
    實現全自動化的分佈式強化學習訓練流程。
    """
    
    def __init__(self,
                 coordinator_port: int = 8080,
                 enable_fault_recovery: bool = True,
                 monitoring_interval: int = 10,
                 checkpoint_dir: str = "/tmp/phase4_checkpoints"):
        """
        初始化分佈式訓練管理器
        
        Args:
            coordinator_port: 節點協調器端口
            enable_fault_recovery: 是否啟用故障恢復
            monitoring_interval: 監控間隔（秒）
            checkpoint_dir: 檢查點目錄
        """
        self.coordinator_port = coordinator_port
        self.enable_fault_recovery = enable_fault_recovery
        self.monitoring_interval = monitoring_interval
        self.checkpoint_dir = checkpoint_dir
        
        # 核心組件
        self.node_coordinator = NodeCoordinator(coordinator_port=coordinator_port)
        self.load_balancer = LoadBalancer()
        self.fault_recovery = FaultRecovery() if enable_fault_recovery else None
        
        # 訓練管理
        self.training_sessions: Dict[str, TrainingSession] = {}
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.training_metrics: Dict[str, List[TrainingMetrics]] = {}
        
        # 運行狀態
        self.is_running = False
        self.monitoring_task = None
        
        # 統計信息
        self.stats = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "total_training_time": 0.0,
            "average_training_time": 0.0,
            "nodes_utilized": 0,
            "tasks_completed": 0,
            "start_time": datetime.now()
        }
        
        self.logger = logger
        
    async def start(self):
        """啟動分佈式訓練管理器"""
        try:
            self.logger.info("🚀 啟動分佈式訓練管理器...")
            
            # 創建檢查點目錄
            import os
            os.makedirs(self.checkpoint_dir, exist_ok=True)
            
            # 啟動核心組件
            await self.node_coordinator.start()
            await self.load_balancer.start()
            
            if self.fault_recovery:
                await self.fault_recovery.start()
            
            # 啟動監控任務
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.is_running = True
            self.stats["start_time"] = datetime.now()
            
            self.logger.info("✅ 分佈式訓練管理器啟動成功")
            
        except Exception as e:
            self.logger.error(f"❌ 分佈式訓練管理器啟動失敗: {e}")
            raise
    
    async def stop(self):
        """停止分佈式訓練管理器"""
        try:
            self.logger.info("🛑 停止分佈式訓練管理器...")
            
            self.is_running = False
            
            # 停止所有活動訓練會話
            for session_id in list(self.active_sessions.keys()):
                await self.cancel_training_session(session_id)
            
            # 停止監控任務
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # 停止核心組件
            if self.fault_recovery:
                await self.fault_recovery.stop()
            
            await self.load_balancer.stop()
            await self.node_coordinator.stop()
            
            self.logger.info("✅ 分佈式訓練管理器已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止分佈式訓練管理器失敗: {e}")
    
    async def create_training_session(self, 
                                    configuration: TrainingConfiguration) -> str:
        """創建訓練會話"""
        try:
            session_id = str(uuid.uuid4())
            
            # 驗證配置
            if not await self._validate_configuration(configuration):
                raise ValueError("Invalid training configuration")
            
            # 創建訓練會話
            session = TrainingSession(
                session_id=session_id,
                configuration=configuration,
                phase=TrainingPhase.INITIALIZING,
                assigned_nodes=[],
                tasks={},
                start_time=datetime.now(),
                total_steps=configuration.training_steps
            )
            
            self.training_sessions[session_id] = session
            self.training_metrics[session_id] = []
            
            self.logger.info(f"📋 訓練會話創建: {session_id}")
            self.stats["total_sessions"] += 1
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"❌ 創建訓練會話失敗: {e}")
            raise
    
    async def start_training_session(self, session_id: str) -> bool:
        """啟動訓練會話"""
        try:
            session = self.training_sessions.get(session_id)
            if not session:
                raise ValueError(f"Training session not found: {session_id}")
            
            if session.phase != TrainingPhase.INITIALIZING:
                raise ValueError(f"Session {session_id} is not in initializing phase")
            
            self.logger.info(f"🎯 啟動訓練會話: {session_id}")
            
            # 更新會話狀態
            session.phase = TrainingPhase.PREPARING
            self.active_sessions[session_id] = session
            
            # 分配節點
            await self._allocate_nodes(session)
            
            # 創建訓練任務
            await self._create_training_tasks(session)
            
            # 開始訓練
            await self._start_training(session)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 啟動訓練會話失敗: {e}")
            return False
    
    async def _validate_configuration(self, config: TrainingConfiguration) -> bool:
        """驗證訓練配置"""
        try:
            # 檢查算法支持
            supported_algorithms = ["DQN", "PPO", "SAC"]
            if config.algorithm not in supported_algorithms:
                self.logger.error(f"❌ 不支持的算法: {config.algorithm}")
                return False
            
            # 檢查節點數量
            if config.min_nodes < 1:
                self.logger.error("❌ 最小節點數量必須大於0")
                return False
            
            if config.max_nodes < config.min_nodes:
                self.logger.error("❌ 最大節點數量必須大於等於最小節點數量")
                return False
            
            # 檢查訓練步數
            if config.training_steps < 1:
                self.logger.error("❌ 訓練步數必須大於0")
                return False
            
            # 檢查超參數
            required_params = ["learning_rate", "batch_size", "buffer_size"]
            for param in required_params:
                if param not in config.hyperparameters:
                    self.logger.error(f"❌ 缺少必要超參數: {param}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置驗證失敗: {e}")
            return False
    
    async def _allocate_nodes(self, session: TrainingSession):
        """分配節點"""
        try:
            config = session.configuration
            
            # 獲取可用節點
            available_nodes = await self.node_coordinator.get_available_nodes()
            
            if len(available_nodes) < config.min_nodes:
                raise RuntimeError(f"Insufficient nodes: need {config.min_nodes}, available {len(available_nodes)}")
            
            # 選擇最佳節點
            selected_nodes = await self.load_balancer.select_nodes(
                available_nodes, 
                min(config.max_nodes, len(available_nodes))
            )
            
            # 分配節點
            for node_id in selected_nodes:
                await self.node_coordinator.allocate_node(node_id, session.session_id)
            
            session.assigned_nodes = selected_nodes
            
            self.logger.info(f"🎯 節點分配完成: {len(selected_nodes)} 個節點")
            
        except Exception as e:
            self.logger.error(f"❌ 節點分配失敗: {e}")
            raise
    
    async def _create_training_tasks(self, session: TrainingSession):
        """創建訓練任務"""
        try:
            config = session.configuration
            
            # 根據訓練模式創建任務
            if config.training_mode == TrainingMode.SINGLE_NODE:
                task = await self._create_single_node_task(session)
                session.tasks[task.task_id] = task
            elif config.training_mode == TrainingMode.MULTI_NODE:
                tasks = await self._create_multi_node_tasks(session)
                session.tasks.update({task.task_id: task for task in tasks})
            elif config.training_mode == TrainingMode.FEDERATED:
                tasks = await self._create_federated_tasks(session)
                session.tasks.update({task.task_id: task for task in tasks})
            elif config.training_mode == TrainingMode.HIERARCHICAL:
                tasks = await self._create_hierarchical_tasks(session)
                session.tasks.update({task.task_id: task for task in tasks})
            
            self.logger.info(f"📋 訓練任務創建完成: {len(session.tasks)} 個任務")
            
        except Exception as e:
            self.logger.error(f"❌ 創建訓練任務失敗: {e}")
            raise
    
    async def _create_single_node_task(self, session: TrainingSession) -> TrainingTask:
        """創建單節點訓練任務"""
        task_id = f"task_{session.session_id}_single"
        
        task = TrainingTask(
            task_id=task_id,
            task_type="single_training",
            algorithm=session.configuration.algorithm,
            environment=session.configuration.environment,
            hyperparameters=session.configuration.hyperparameters,
            resource_requirements=session.configuration.resource_requirements,
            priority=1,
            timeout=session.configuration.timeout,
            created_at=datetime.now(),
            session_id=session.session_id
        )
        
        # 分配給第一個節點
        if session.assigned_nodes:
            task.assigned_node = session.assigned_nodes[0]
        
        return task
    
    async def _create_multi_node_tasks(self, session: TrainingSession) -> List[TrainingTask]:
        """創建多節點訓練任務"""
        tasks = []
        
        # 為每個節點創建訓練任務
        for i, node_id in enumerate(session.assigned_nodes):
            task_id = f"task_{session.session_id}_node_{i}"
            
            task = TrainingTask(
                task_id=task_id,
                task_type="multi_training",
                algorithm=session.configuration.algorithm,
                environment=session.configuration.environment,
                hyperparameters=session.configuration.hyperparameters,
                resource_requirements=session.configuration.resource_requirements,
                priority=1,
                timeout=session.configuration.timeout,
                created_at=datetime.now(),
                session_id=session.session_id,
                assigned_node=node_id
            )
            
            tasks.append(task)
        
        return tasks
    
    async def _create_federated_tasks(self, session: TrainingSession) -> List[TrainingTask]:
        """創建聯邦學習任務"""
        tasks = []
        
        # 創建參數服務器任務
        server_task = TrainingTask(
            task_id=f"task_{session.session_id}_server",
            task_type="parameter_server",
            algorithm=session.configuration.algorithm,
            environment=session.configuration.environment,
            hyperparameters=session.configuration.hyperparameters,
            resource_requirements=session.configuration.resource_requirements,
            priority=1,
            timeout=session.configuration.timeout,
            created_at=datetime.now(),
            session_id=session.session_id,
            assigned_node=session.assigned_nodes[0] if session.assigned_nodes else None
        )
        tasks.append(server_task)
        
        # 創建客戶端任務
        for i, node_id in enumerate(session.assigned_nodes[1:], 1):
            task_id = f"task_{session.session_id}_client_{i}"
            
            task = TrainingTask(
                task_id=task_id,
                task_type="federated_client",
                algorithm=session.configuration.algorithm,
                environment=session.configuration.environment,
                hyperparameters=session.configuration.hyperparameters,
                resource_requirements=session.configuration.resource_requirements,
                priority=1,
                timeout=session.configuration.timeout,
                created_at=datetime.now(),
                session_id=session.session_id,
                assigned_node=node_id
            )
            
            tasks.append(task)
        
        return tasks
    
    async def _create_hierarchical_tasks(self, session: TrainingSession) -> List[TrainingTask]:
        """創建分層訓練任務"""
        tasks = []
        
        # 創建主節點任務
        master_task = TrainingTask(
            task_id=f"task_{session.session_id}_master",
            task_type="hierarchical_master",
            algorithm=session.configuration.algorithm,
            environment=session.configuration.environment,
            hyperparameters=session.configuration.hyperparameters,
            resource_requirements=session.configuration.resource_requirements,
            priority=1,
            timeout=session.configuration.timeout,
            created_at=datetime.now(),
            session_id=session.session_id,
            assigned_node=session.assigned_nodes[0] if session.assigned_nodes else None
        )
        tasks.append(master_task)
        
        # 創建工作節點任務
        for i, node_id in enumerate(session.assigned_nodes[1:], 1):
            task_id = f"task_{session.session_id}_worker_{i}"
            
            task = TrainingTask(
                task_id=task_id,
                task_type="hierarchical_worker",
                algorithm=session.configuration.algorithm,
                environment=session.configuration.environment,
                hyperparameters=session.configuration.hyperparameters,
                resource_requirements=session.configuration.resource_requirements,
                priority=1,
                timeout=session.configuration.timeout,
                created_at=datetime.now(),
                session_id=session.session_id,
                assigned_node=node_id
            )
            
            tasks.append(task)
        
        return tasks
    
    async def _start_training(self, session: TrainingSession):
        """開始訓練"""
        try:
            session.phase = TrainingPhase.TRAINING
            
            # 分配任務到節點
            for task in session.tasks.values():
                await self.node_coordinator.assign_task(task)
            
            # 啟動訓練監控
            asyncio.create_task(self._monitor_training_session(session))
            
            self.logger.info(f"🎯 訓練開始: {session.session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 開始訓練失敗: {e}")
            session.phase = TrainingPhase.FAILED
            raise
    
    async def _monitor_training_session(self, session: TrainingSession):
        """監控訓練會話"""
        try:
            while (session.phase == TrainingPhase.TRAINING and 
                   session.session_id in self.active_sessions):
                
                # 檢查任務狀態
                await self._check_task_status(session)
                
                # 收集訓練指標
                await self._collect_training_metrics(session)
                
                # 檢查完成條件
                if await self._check_completion_conditions(session):
                    await self._complete_training_session(session)
                    break
                
                # 檢查超時
                if await self._check_timeout(session):
                    await self._timeout_training_session(session)
                    break
                
                await asyncio.sleep(self.monitoring_interval)
                
        except Exception as e:
            self.logger.error(f"❌ 訓練監控失敗: {e}")
            session.phase = TrainingPhase.FAILED
    
    async def _check_task_status(self, session: TrainingSession):
        """檢查任務狀態"""
        try:
            for task in session.tasks.values():
                # 獲取任務最新狀態
                updated_task = await self.node_coordinator.get_task_status(task.task_id)
                if updated_task:
                    session.tasks[task.task_id] = updated_task
                    
        except Exception as e:
            self.logger.error(f"❌ 檢查任務狀態失敗: {e}")
    
    async def _collect_training_metrics(self, session: TrainingSession):
        """收集訓練指標"""
        try:
            for task in session.tasks.values():
                if task.assigned_node:
                    # 從節點收集指標
                    metrics = await self.node_coordinator.get_task_metrics(task.task_id)
                    if metrics:
                        training_metrics = TrainingMetrics(
                            session_id=session.session_id,
                            timestamp=datetime.now(),
                            node_id=task.assigned_node,
                            step=metrics.get("step", 0),
                            episode_reward=metrics.get("episode_reward", 0.0),
                            episode_length=metrics.get("episode_length", 0),
                            loss=metrics.get("loss", 0.0),
                            learning_rate=metrics.get("learning_rate", 0.0),
                            epsilon=metrics.get("epsilon", 0.0),
                            q_values=metrics.get("q_values", [])
                        )
                        
                        self.training_metrics[session.session_id].append(training_metrics)
                        
                        # 更新會話進度
                        session.current_step = max(session.current_step, training_metrics.step)
                        session.best_performance = max(session.best_performance, training_metrics.episode_reward)
                        
        except Exception as e:
            self.logger.error(f"❌ 收集訓練指標失敗: {e}")
    
    async def _check_completion_conditions(self, session: TrainingSession) -> bool:
        """檢查完成條件"""
        try:
            # 檢查訓練步數
            if session.current_step >= session.total_steps:
                return True
            
            # 檢查所有任務是否完成
            completed_tasks = sum(1 for task in session.tasks.values() if task.status == "completed")
            if completed_tasks == len(session.tasks):
                return True
            
            # 檢查自定義完成條件
            if session.configuration.algorithm == "DQN":
                # DQN 特定的完成條件
                if session.best_performance > 500:  # 示例閾值
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 檢查完成條件失敗: {e}")
            return False
    
    async def _check_timeout(self, session: TrainingSession) -> bool:
        """檢查超時"""
        try:
            runtime = (datetime.now() - session.start_time).total_seconds()
            return runtime > session.configuration.timeout
            
        except Exception as e:
            self.logger.error(f"❌ 檢查超時失敗: {e}")
            return False
    
    async def _complete_training_session(self, session: TrainingSession):
        """完成訓練會話"""
        try:
            session.phase = TrainingPhase.COMPLETED
            session.end_time = datetime.now()
            
            # 保存最終檢查點
            await self._save_checkpoint(session)
            
            # 清理資源
            await self._cleanup_session_resources(session)
            
            # 移除活動會話
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
            
            # 更新統計
            self.stats["completed_sessions"] += 1
            training_time = (session.end_time - session.start_time).total_seconds()
            self.stats["total_training_time"] += training_time
            
            completed_sessions = self.stats["completed_sessions"]
            self.stats["average_training_time"] = (
                self.stats["total_training_time"] / completed_sessions
            )
            
            self.logger.info(f"✅ 訓練會話完成: {session.session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 完成訓練會話失敗: {e}")
    
    async def _timeout_training_session(self, session: TrainingSession):
        """超時訓練會話"""
        try:
            session.phase = TrainingPhase.FAILED
            session.end_time = datetime.now()
            
            # 清理資源
            await self._cleanup_session_resources(session)
            
            # 移除活動會話
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
            
            # 更新統計
            self.stats["failed_sessions"] += 1
            
            self.logger.warning(f"⏰ 訓練會話超時: {session.session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 超時訓練會話失敗: {e}")
    
    async def _save_checkpoint(self, session: TrainingSession):
        """保存檢查點"""
        try:
            checkpoint_file = f"{self.checkpoint_dir}/checkpoint_{session.session_id}.json"
            
            checkpoint_data = {
                "session": session.to_dict(),
                "metrics": [m.to_dict() for m in self.training_metrics.get(session.session_id, [])]
            }
            
            import json
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            session.last_checkpoint = checkpoint_file
            
            self.logger.info(f"💾 檢查點保存: {checkpoint_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存檢查點失敗: {e}")
    
    async def _cleanup_session_resources(self, session: TrainingSession):
        """清理會話資源"""
        try:
            # 釋放節點
            for node_id in session.assigned_nodes:
                await self.node_coordinator.release_node(node_id)
            
            # 清理任務
            for task in session.tasks.values():
                await self.node_coordinator.cancel_task(task.task_id)
            
            self.logger.info(f"🧹 會話資源清理完成: {session.session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 清理會話資源失敗: {e}")
    
    async def cancel_training_session(self, session_id: str) -> bool:
        """取消訓練會話"""
        try:
            session = self.training_sessions.get(session_id)
            if not session:
                return False
            
            session.phase = TrainingPhase.CANCELLED
            session.end_time = datetime.now()
            
            # 清理資源
            await self._cleanup_session_resources(session)
            
            # 移除活動會話
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            self.logger.info(f"🚫 訓練會話取消: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 取消訓練會話失敗: {e}")
            return False
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 更新負載均衡器
                nodes = await self.node_coordinator.get_all_nodes()
                await self.load_balancer.update_nodes(nodes)
                
                # 更新故障恢復機制
                if self.fault_recovery:
                    tasks = {}
                    for session in self.active_sessions.values():
                        tasks.update(session.tasks)
                    
                    await self.fault_recovery.update_system_state(nodes, tasks)
                
                # 更新統計
                self.stats["nodes_utilized"] = len(nodes)
                self.stats["tasks_completed"] = sum(
                    len([t for t in session.tasks.values() if t.status == "completed"])
                    for session in self.training_sessions.values()
                )
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 監控循環錯誤: {e}")
                await asyncio.sleep(5)
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話狀態"""
        session = self.training_sessions.get(session_id)
        if not session:
            return None
        
        return session.to_dict()
    
    def get_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
        """獲取會話指標"""
        metrics = self.training_metrics.get(session_id, [])
        return [m.to_dict() for m in metrics]
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """獲取所有會話"""
        return [session.to_dict() for session in self.training_sessions.values()]
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """獲取活動會話"""
        return [session.to_dict() for session in self.active_sessions.values()]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """獲取系統統計"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "active_sessions": len(self.active_sessions),
            "total_sessions": len(self.training_sessions),
            "node_coordinator_stats": self.node_coordinator.get_stats(),
            "load_balancer_stats": self.load_balancer.get_stats(),
            "fault_recovery_stats": self.fault_recovery.get_failure_stats() if self.fault_recovery else {}
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        health = {
            "status": "healthy",
            "components": {
                "node_coordinator": "healthy",
                "load_balancer": "healthy",
                "fault_recovery": "healthy" if self.fault_recovery else "disabled"
            },
            "active_sessions": len(self.active_sessions),
            "available_nodes": len(self.node_coordinator.nodes),
            "issues": []
        }
        
        # 檢查組件健康狀態
        try:
            # 檢查節點協調器
            if not self.node_coordinator.is_running:
                health["components"]["node_coordinator"] = "unhealthy"
                health["issues"].append("Node coordinator is not running")
            
            # 檢查負載均衡器
            if not self.load_balancer.is_running:
                health["components"]["load_balancer"] = "unhealthy"
                health["issues"].append("Load balancer is not running")
            
            # 檢查故障恢復機制
            if self.fault_recovery and not self.fault_recovery.is_running:
                health["components"]["fault_recovery"] = "unhealthy"
                health["issues"].append("Fault recovery is not running")
            
            # 檢查會話狀態
            failed_sessions = sum(1 for session in self.active_sessions.values() 
                                if session.phase == TrainingPhase.FAILED)
            if failed_sessions > 0:
                health["issues"].append(f"{failed_sessions} training sessions failed")
            
            # 整體健康狀態
            if health["issues"]:
                health["status"] = "degraded" if len(health["issues"]) < 3 else "unhealthy"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["issues"].append(f"Health check failed: {e}")
        
        return health
