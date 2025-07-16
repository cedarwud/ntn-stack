"""
負載均衡器 - Phase 4 核心組件

實現分佈式訓練環境中的智能負載均衡：
- 動態負載監控
- 智能任務分配
- 資源使用優化
- 性能預測和調度

Features:
- 基於負載和性能的智能調度
- 支援多種負載均衡算法
- 實時性能監控和調整
- 預測式資源分配
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque

from .node_coordinator import NodeInfo, NodeStatus, NodeType, TrainingTask

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """負載均衡策略"""
    ROUND_ROBIN = "round_robin"        # 輪詢
    LEAST_LOADED = "least_loaded"      # 最少負載
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加權輪詢
    PREDICTIVE = "predictive"          # 預測式
    ADAPTIVE = "adaptive"              # 自適應


@dataclass
class LoadMetrics:
    """負載指標"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: float = 0.0
    network_io: float = 0.0
    disk_io: float = 0.0
    active_tasks: int = 0
    queue_length: int = 0
    response_time: float = 0.0
    throughput: float = 0.0
    
    def get_composite_load(self) -> float:
        """計算複合負載分數"""
        weights = {
            'cpu': 0.3,
            'memory': 0.2,
            'gpu': 0.3,
            'network': 0.1,
            'disk': 0.1
        }
        
        return (
            weights['cpu'] * self.cpu_usage +
            weights['memory'] * self.memory_usage +
            weights['gpu'] * self.gpu_usage +
            weights['network'] * self.network_io +
            weights['disk'] * self.disk_io
        )


@dataclass
class NodePerformanceHistory:
    """節點性能歷史"""
    node_id: str
    load_history: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: deque = field(default_factory=lambda: deque(maxlen=50))
    throughput_history: deque = field(default_factory=lambda: deque(maxlen=50))
    task_completion_times: deque = field(default_factory=lambda: deque(maxlen=30))
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_load_sample(self, load: float):
        """添加負載樣本"""
        self.load_history.append((datetime.now(), load))
        self.last_updated = datetime.now()
    
    def add_response_time(self, response_time: float):
        """添加響應時間樣本"""
        self.response_times.append(response_time)
        self.last_updated = datetime.now()
    
    def add_throughput(self, throughput: float):
        """添加吞吐量樣本"""
        self.throughput_history.append(throughput)
        self.last_updated = datetime.now()
    
    def add_task_completion_time(self, completion_time: float):
        """添加任務完成時間樣本"""
        self.task_completion_times.append(completion_time)
        self.last_updated = datetime.now()
    
    def get_average_load(self, window_minutes: int = 5) -> float:
        """獲取平均負載"""
        if not self.load_history:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_loads = [load for timestamp, load in self.load_history 
                       if timestamp >= cutoff_time]
        
        return np.mean(recent_loads) if recent_loads else 0.0
    
    def get_average_response_time(self) -> float:
        """獲取平均響應時間"""
        return np.mean(self.response_times) if self.response_times else 0.0
    
    def get_average_throughput(self) -> float:
        """獲取平均吞吐量"""
        return np.mean(self.throughput_history) if self.throughput_history else 0.0
    
    def predict_completion_time(self, task_complexity: float = 1.0) -> float:
        """預測任務完成時間"""
        if not self.task_completion_times:
            return 300.0  # 默認 5 分鐘
        
        avg_completion_time = np.mean(self.task_completion_times)
        std_completion_time = np.std(self.task_completion_times)
        
        # 根據任務複雜度調整
        predicted_time = avg_completion_time * task_complexity
        
        # 添加不確定性
        uncertainty = std_completion_time * 0.5
        
        return predicted_time + uncertainty


class LoadBalancer:
    """
    負載均衡器
    
    實現分佈式訓練環境中的智能負載均衡，
    支持多種負載均衡策略和動態調整。
    """
    
    def __init__(self,
                 strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
                 monitoring_interval: int = 30,
                 prediction_window: int = 300):
        """
        初始化負載均衡器
        
        Args:
            strategy: 負載均衡策略
            monitoring_interval: 監控間隔（秒）
            prediction_window: 預測時間窗口（秒）
        """
        self.strategy = strategy
        self.monitoring_interval = monitoring_interval
        self.prediction_window = prediction_window
        
        # 性能數據
        self.node_metrics: Dict[str, LoadMetrics] = {}
        self.performance_history: Dict[str, NodePerformanceHistory] = {}
        
        # 負載均衡狀態
        self.round_robin_counter = 0
        self.last_assignments: Dict[str, datetime] = {}
        
        # 運行狀態
        self.nodes: Dict[str, Any] = {}
        self.is_running = False
        self.start_time = datetime.now()
        self.last_selection_time = None
        
        # 統計信息
        self.stats = {
            LoadBalancingStrategy.ROUND_ROBIN: 0,
            LoadBalancingStrategy.LEAST_LOADED: 0,
            LoadBalancingStrategy.PREDICTIVE: 0,
            LoadBalancingStrategy.ADAPTIVE: 0
        }
        
        # 詳細統計信息
        self.assignment_stats = {
            "total_assignments": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "strategy_switches": 0,
            "average_response_time": 0.0,
            "last_optimization": datetime.now()
        }
        
        # 運行狀態
        self.is_running = False
        self.monitoring_task = None
        
        self.logger = logger
        
    async def start(self):
        """啟動負載均衡器"""
        try:
            self.logger.info("🚀 啟動負載均衡器...")
            
            # 啟動監控任務
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.is_running = True
            
            self.logger.info(f"✅ 負載均衡器啟動成功 (策略: {self.strategy.value})")
            
        except Exception as e:
            self.logger.error(f"❌ 負載均衡器啟動失敗: {e}")
            raise
    
    async def stop(self):
        """停止負載均衡器"""
        try:
            self.logger.info("🛑 停止負載均衡器...")
            
            self.is_running = False
            
            # 停止監控任務
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("✅ 負載均衡器已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止負載均衡器失敗: {e}")
    
    async def select_node(self, 
                         available_nodes: List[NodeInfo],
                         task: TrainingTask) -> Optional[NodeInfo]:
        """
        選擇最適合的節點
        
        Args:
            available_nodes: 可用節點列表
            task: 訓練任務
            
        Returns:
            選中的節點，如果沒有可用節點則返回 None
        """
        if not available_nodes:
            return None
        
        try:
            # 根據策略選擇節點
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return await self._round_robin_selection(available_nodes)
            elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
                return await self._least_loaded_selection(available_nodes)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return await self._weighted_round_robin_selection(available_nodes)
            elif self.strategy == LoadBalancingStrategy.PREDICTIVE:
                return await self._predictive_selection(available_nodes, task)
            elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
                return await self._adaptive_selection(available_nodes, task)
            else:
                # 默認使用最少負載策略
                return await self._least_loaded_selection(available_nodes)
                
        except Exception as e:
            self.logger.error(f"❌ 節點選擇失敗: {e}")
            # 失敗時使用簡單輪詢
            return available_nodes[self.round_robin_counter % len(available_nodes)]
    
    async def _round_robin_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """輪詢選擇"""
        selected_node = nodes[self.round_robin_counter % len(nodes)]
        self.round_robin_counter += 1
        
        self.logger.debug(f"🔄 輪詢選擇節點: {selected_node.node_id}")
        
        return selected_node
    
    async def _least_loaded_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """最少負載選擇"""
        # 計算每個節點的負載分數
        node_loads = []
        for node in nodes:
            metrics = self.node_metrics.get(node.node_id, LoadMetrics())
            load_score = metrics.get_composite_load()
            node_loads.append((node, load_score))
        
        # 選擇負載最低的節點
        selected_node = min(node_loads, key=lambda x: x[1])[0]
        
        self.logger.debug(f"⚖️ 最少負載選擇節點: {selected_node.node_id}")
        
        return selected_node
    
    async def _weighted_round_robin_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """加權輪詢選擇"""
        # 根據節點能力計算權重
        weights = []
        for node in nodes:
            # 基礎權重
            weight = 1.0
            
            # 根據 CPU 核心數調整
            cpu_cores = node.capabilities.get('cpu_cores', 1)
            weight *= cpu_cores
            
            # 根據 GPU 數量調整
            gpu_count = node.capabilities.get('gpu_count', 0)
            weight *= (1 + gpu_count * 0.5)
            
            # 根據內存大小調整
            memory_gb = node.capabilities.get('memory_gb', 8)
            weight *= (memory_gb / 8)
            
            weights.append(weight)
        
        # 加權隨機選擇
        total_weight = sum(weights)
        if total_weight == 0:
            return nodes[0]
        
        probabilities = [w / total_weight for w in weights]
        selected_index = np.random.choice(len(nodes), p=probabilities)
        
        selected_node = nodes[selected_index]
        
        self.logger.debug(f"⚖️ 加權輪詢選擇節點: {selected_node.node_id}")
        
        return selected_node
    
    async def _predictive_selection(self, nodes: List[NodeInfo], task: TrainingTask) -> NodeInfo:
        """預測式選擇"""
        # 預測每個節點的性能
        node_predictions = []
        
        for node in nodes:
            history = self.performance_history.get(node.node_id)
            if history:
                # 根據任務算法估算複雜度
                task_complexity = self._estimate_task_complexity(task)
                
                # 預測完成時間
                predicted_time = history.predict_completion_time(task_complexity)
                
                # 考慮當前負載
                current_load = self.node_metrics.get(node.node_id, LoadMetrics()).get_composite_load()
                
                # 綜合評分（越低越好）
                score = predicted_time * (1 + current_load)
                
                node_predictions.append((node, score))
            else:
                # 沒有歷史數據，使用默認分數
                node_predictions.append((node, 1000.0))
        
        # 選擇預測性能最好的節點
        selected_node = min(node_predictions, key=lambda x: x[1])[0]
        
        self.logger.debug(f"🔮 預測式選擇節點: {selected_node.node_id}")
        
        return selected_node
    
    async def _adaptive_selection(self, nodes: List[NodeInfo], task: TrainingTask) -> NodeInfo:
        """自適應選擇"""
        # 根據當前系統狀態選擇最適合的策略
        
        # 分析系統狀態
        total_nodes = len(nodes)
        avg_load = np.mean([
            self.node_metrics.get(node.node_id, LoadMetrics()).get_composite_load()
            for node in nodes
        ])
        
        load_variance = np.var([
            self.node_metrics.get(node.node_id, LoadMetrics()).get_composite_load()
            for node in nodes
        ])
        
        # 選擇策略
        if total_nodes <= 2:
            # 節點少，使用輪詢
            return await self._round_robin_selection(nodes)
        elif avg_load > 0.8:
            # 系統負載高，使用最少負載策略
            return await self._least_loaded_selection(nodes)
        elif load_variance > 0.3:
            # 負載差異大，使用預測式策略
            return await self._predictive_selection(nodes, task)
        else:
            # 系統穩定，使用加權輪詢
            return await self._weighted_round_robin_selection(nodes)
    
    def _estimate_task_complexity(self, task: TrainingTask) -> float:
        """估算任務複雜度"""
        complexity = 1.0
        
        # 根據算法類型調整
        algorithm_complexity = {
            'dqn': 1.0,
            'ppo': 1.2,
            'sac': 1.5,
            'a3c': 1.8
        }
        
        complexity *= algorithm_complexity.get(task.algorithm, 1.0)
        
        # 根據參數調整
        if task.parameters:
            episodes = task.parameters.get('episodes', 100)
            complexity *= (episodes / 100)
            
            batch_size = task.parameters.get('batch_size', 32)
            complexity *= (batch_size / 32)
        
        return complexity
    
    async def update_node_metrics(self, node_id: str, metrics: LoadMetrics):
        """更新節點指標"""
        self.node_metrics[node_id] = metrics
        
        # 更新性能歷史
        if node_id not in self.performance_history:
            self.performance_history[node_id] = NodePerformanceHistory(node_id)
        
        history = self.performance_history[node_id]
        history.add_load_sample(metrics.get_composite_load())
        
        if metrics.response_time > 0:
            history.add_response_time(metrics.response_time)
        
        if metrics.throughput > 0:
            history.add_throughput(metrics.throughput)
    
    async def record_task_completion(self, node_id: str, completion_time: float):
        """記錄任務完成時間"""
        if node_id in self.performance_history:
            self.performance_history[node_id].add_task_completion_time(completion_time)
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 監控節點性能
                await self._monitor_node_performance()
                
                # 優化負載均衡策略
                await self._optimize_strategy()
                
                # 清理過期數據
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 監控循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_node_performance(self):
        """監控節點性能"""
        try:
            # 計算平均響應時間
            response_times = []
            for history in self.performance_history.values():
                if history.response_times:
                    response_times.extend(history.response_times)
            
            if response_times:
                self.assignment_stats["average_response_time"] = np.mean(response_times)
            
            # 檢測異常節點
            await self._detect_anomalous_nodes()
            
        except Exception as e:
            self.logger.error(f"❌ 節點性能監控失敗: {e}")
    
    async def _detect_anomalous_nodes(self):
        """檢測異常節點"""
        try:
            for node_id, history in self.performance_history.items():
                if len(history.response_times) < 5:
                    continue
                
                # 檢測響應時間異常
                recent_times = list(history.response_times)[-5:]
                avg_time = np.mean(recent_times)
                
                # 如果響應時間超過平均值的 2 倍，標記為異常
                if avg_time > self.assignment_stats["average_response_time"] * 2:
                    self.logger.warning(f"⚠️ 檢測到異常節點: {node_id} (響應時間: {avg_time:.2f}s)")
                    
        except Exception as e:
            self.logger.error(f"❌ 異常節點檢測失敗: {e}")
    
    async def _optimize_strategy(self):
        """優化負載均衡策略"""
        try:
            # 如果使用自適應策略，不需要優化
            if self.strategy == LoadBalancingStrategy.ADAPTIVE:
                return
            
            # 分析當前策略的效果
            current_time = datetime.now()
            
            # 計算最近的平均性能
            recent_performance = self._calculate_recent_performance()
            
            # 如果性能下降，考慮切換策略
            if recent_performance < 0.7:  # 70% 閾值
                await self._switch_strategy()
                
        except Exception as e:
            self.logger.error(f"❌ 策略優化失敗: {e}")
    
    def _calculate_recent_performance(self) -> float:
        """計算最近的性能分數"""
        try:
            # 計算成功率
            total_assignments = self.assignment_stats["total_assignments"]
            successful_assignments = self.assignment_stats["successful_assignments"]
            
            if total_assignments == 0:
                return 1.0
            
            success_rate = successful_assignments / total_assignments
            
            # 計算響應時間性能
            avg_response_time = self.assignment_stats["average_response_time"]
            response_performance = max(0.0, 1.0 - (avg_response_time / 10.0))  # 10秒作為基準
            
            # 綜合性能分數
            performance_score = (success_rate * 0.7 + response_performance * 0.3)
            
            return performance_score
            
        except Exception as e:
            self.logger.error(f"❌ 性能計算失敗: {e}")
            return 1.0
    
    async def _switch_strategy(self):
        """切換負載均衡策略"""
        try:
            # 策略切換順序
            strategy_order = [
                LoadBalancingStrategy.LEAST_LOADED,
                LoadBalancingStrategy.PREDICTIVE,
                LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN,
                LoadBalancingStrategy.ROUND_ROBIN
            ]
            
            # 找到當前策略的索引
            current_index = strategy_order.index(self.strategy)
            
            # 切換到下一個策略
            next_index = (current_index + 1) % len(strategy_order)
            new_strategy = strategy_order[next_index]
            
            self.logger.info(f"🔄 切換負載均衡策略: {self.strategy.value} -> {new_strategy.value}")
            
            self.strategy = new_strategy
            self.assignment_stats["strategy_switches"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ 策略切換失敗: {e}")
    
    async def _cleanup_old_data(self):
        """清理過期數據"""
        try:
            # 清理超過 1 小時的分配記錄
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            expired_assignments = [
                node_id for node_id, timestamp in self.last_assignments.items()
                if timestamp < cutoff_time
            ]
            
            for node_id in expired_assignments:
                del self.last_assignments[node_id]
                
        except Exception as e:
            self.logger.error(f"❌ 數據清理失敗: {e}")
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """獲取負載均衡器統計信息"""
        return {
            "strategy": self.strategy.value,
            "total_nodes": len(self.node_metrics),
            "assignment_stats": self.assignment_stats,
            "average_loads": {
                node_id: metrics.get_composite_load()
                for node_id, metrics in self.node_metrics.items()
            },
            "performance_summary": {
                node_id: {
                    "avg_load": history.get_average_load(),
                    "avg_response_time": history.get_average_response_time(),
                    "avg_throughput": history.get_average_throughput()
                }
                for node_id, history in self.performance_history.items()
            }
        }
    
    def get_node_metrics(self, node_id: str) -> Optional[LoadMetrics]:
        """獲取節點指標"""
        return self.node_metrics.get(node_id)
    
    def get_node_performance_history(self, node_id: str) -> Optional[NodePerformanceHistory]:
        """獲取節點性能歷史"""
        return self.performance_history.get(node_id)
    
    async def set_strategy(self, strategy: LoadBalancingStrategy):
        """設置負載均衡策略"""
        if strategy != self.strategy:
            self.logger.info(f"🔄 設置負載均衡策略: {strategy.value}")
            self.strategy = strategy
            self.assignment_stats["strategy_switches"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取負載均衡統計信息"""
        try:
            total_requests = sum(self.stats.values())
            uptime = (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0
            
            return {
                "total_requests": total_requests,
                "requests_per_strategy": dict(self.stats),
                "current_strategy": self.strategy.value,
                "managed_nodes": len(self.nodes),
                "uptime_seconds": uptime,
                "last_selection_time": self.last_selection_time.isoformat() if hasattr(self, 'last_selection_time') else None,
                "performance_history_size": sum(len(history.response_times) for history in self.performance_history.values()),
                "is_running": self.is_running
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_requests": 0,
                "is_running": self.is_running
            }
