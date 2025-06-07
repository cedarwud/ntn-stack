"""
網路拓撲自動調整服務 (Network Topology Auto Adjustment Service)

實現智能網路拓撲監控、分析和自動調整功能。
根據網路狀態、負載分佈和性能指標自動優化網路拓撲結構。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json

import structlog
import numpy as np
from pydantic import BaseModel

from ..models.uav_models import UAVPosition, UAVSignalQuality

logger = structlog.get_logger(__name__)


class TopologyAdjustmentTrigger(Enum):
    """拓撲調整觸發條件"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    LOAD_IMBALANCE = "load_imbalance"
    NODE_FAILURE = "node_failure"
    CONNECTIVITY_LOSS = "connectivity_loss"
    ENERGY_DEPLETION = "energy_depletion"
    MISSION_REQUIREMENT = "mission_requirement"
    PROACTIVE_OPTIMIZATION = "proactive_optimization"


class AdjustmentStrategy(Enum):
    """調整策略"""
    CONSERVATIVE = "conservative"     # 保守：最小變動
    BALANCED = "balanced"            # 平衡：適度調整
    AGGRESSIVE = "aggressive"        # 激進：大幅優化
    EMERGENCY = "emergency"          # 緊急：快速恢復


class TopologyPattern(Enum):
    """拓撲模式"""
    CENTRALIZED = "centralized"      # 中心化
    DISTRIBUTED = "distributed"     # 分散式
    HIERARCHICAL = "hierarchical"   # 階層式
    MESH = "mesh"                   # 網狀
    HYBRID = "hybrid"               # 混合式
    ADAPTIVE = "adaptive"           # 自適應


@dataclass
class TopologyMetrics:
    """拓撲指標"""
    connectivity_index: float = 0.0          # 連接性指數
    clustering_coefficient: float = 0.0      # 聚類係數
    average_path_length: float = 0.0         # 平均路徑長度
    network_diameter: int = 0                # 網路直徑
    betweenness_centrality: float = 0.0      # 中間性中心度
    load_distribution_variance: float = 0.0  # 負載分佈方差
    fault_tolerance: float = 0.0             # 容錯性
    energy_efficiency: float = 0.0           # 能源效率
    throughput_efficiency: float = 0.0       # 吞吐量效率
    latency_optimality: float = 0.0          # 延遲最優性


@dataclass
class TopologyNode:
    """拓撲節點"""
    node_id: str
    node_type: str
    position: UAVPosition
    connections: Set[str] = field(default_factory=set)
    capacity: float = 100.0           # 節點容量
    current_load: float = 0.0         # 當前負載
    energy_level: float = 100.0       # 能量水平
    reliability: float = 1.0          # 可靠性
    centrality_score: float = 0.0     # 中心性分數
    is_critical: bool = False         # 是否關鍵節點
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class TopologyLink:
    """拓撲連結"""
    link_id: str
    source_node: str
    target_node: str
    capacity: float = 100.0           # 連結容量
    current_utilization: float = 0.0  # 當前利用率
    latency: float = 50.0             # 延遲
    reliability: float = 1.0          # 可靠性
    cost: float = 1.0                 # 成本
    is_critical: bool = False         # 是否關鍵連結
    established_at: datetime = field(default_factory=datetime.now)


@dataclass
class TopologyAdjustment:
    """拓撲調整記錄"""
    adjustment_id: str
    trigger: TopologyAdjustmentTrigger
    strategy: AdjustmentStrategy
    changes: List[Dict] = field(default_factory=list)
    metrics_before: Optional[TopologyMetrics] = None
    metrics_after: Optional[TopologyMetrics] = None
    improvement_score: float = 0.0
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NetworkTopology:
    """網路拓撲"""
    topology_id: str
    pattern: TopologyPattern
    nodes: Dict[str, TopologyNode] = field(default_factory=dict)
    links: Dict[str, TopologyLink] = field(default_factory=dict)
    metrics: TopologyMetrics = field(default_factory=TopologyMetrics)
    adjustment_history: List[TopologyAdjustment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_adjustment: Optional[datetime] = None


class TopologyAnalysisRequest(BaseModel):
    """拓撲分析請求"""
    include_predictions: bool = True
    analysis_depth: str = "full"  # "basic", "detailed", "full"
    time_window_minutes: int = 30


class TopologyAdjustmentRequest(BaseModel):
    """拓撲調整請求"""
    trigger: TopologyAdjustmentTrigger
    strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED
    target_pattern: Optional[TopologyPattern] = None
    constraints: Dict[str, any] = {}
    dry_run: bool = False


class NetworkTopologyAutoAdjustmentService:
    """網路拓撲自動調整服務"""

    def __init__(self, mesh_optimization_service=None, uav_swarm_service=None):
        self.logger = structlog.get_logger(__name__)
        self.mesh_optimization_service = mesh_optimization_service
        self.uav_swarm_service = uav_swarm_service
        
        # 當前拓撲
        self.current_topology = NetworkTopology(
            topology_id=f"topology_{uuid.uuid4().hex[:8]}",
            pattern=TopologyPattern.ADAPTIVE
        )
        
        # 調整參數
        self.monitoring_interval = 10.0  # 監控間隔(秒)
        self.adjustment_threshold = 0.7   # 調整閾值
        self.stability_window = 60.0      # 穩定性窗口(秒)
        self.max_adjustments_per_hour = 10
        
        # 監控和調整任務
        self.monitoring_task: Optional[asyncio.Task] = None
        self.adjustment_queue: asyncio.Queue = asyncio.Queue()
        self.adjustment_lock = asyncio.Lock()
        
        # 性能歷史
        self.metrics_history: List[Tuple[datetime, TopologyMetrics]] = []
        self.adjustment_counter = 0
        self.last_hour_adjustments = []
        
    async def start_auto_adjustment_service(self):
        """啟動自動調整服務"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._adjustment_processor())
            self.logger.info("網路拓撲自動調整服務已啟動")
    
    async def stop_auto_adjustment_service(self):
        """停止自動調整服務"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            self.logger.info("網路拓撲自動調整服務已停止")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while True:
            try:
                # 更新拓撲狀態
                await self._update_topology_state()
                
                # 計算拓撲指標
                await self._calculate_topology_metrics()
                
                # 檢測調整觸發條件
                triggers = await self._detect_adjustment_triggers()
                
                # 將觸發的調整加入隊列
                for trigger in triggers:
                    await self.adjustment_queue.put(trigger)
                
                # 記錄指標歷史
                self.metrics_history.append((datetime.now(), self.current_topology.metrics))
                
                # 清理舊歷史數據
                cutoff_time = datetime.now() - timedelta(hours=2)
                self.metrics_history = [
                    (t, m) for t, m in self.metrics_history if t > cutoff_time
                ]
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"拓撲監控異常: {e}")
                await asyncio.sleep(5.0)
    
    async def _adjustment_processor(self):
        """調整處理器"""
        while True:
            try:
                # 等待調整觸發
                trigger_info = await self.adjustment_queue.get()
                
                # 檢查調整頻率限制
                if await self._check_adjustment_rate_limit():
                    await self._execute_topology_adjustment(trigger_info)
                else:
                    self.logger.warning("調整頻率超限，跳過此次調整")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"拓撲調整處理異常: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_topology_state(self):
        """更新拓撲狀態"""
        # 從Mesh優化服務獲取網路狀態
        if self.mesh_optimization_service:
            try:
                network_status = await self.mesh_optimization_service.get_network_status()
                await self._update_from_network_status(network_status)
            except Exception as e:
                self.logger.warning(f"無法獲取網路狀態: {e}")
        
        # 從UAV群組服務獲取UAV狀態
        if self.uav_swarm_service:
            try:
                # 獲取所有群組的狀態
                pass  # 實現UAV狀態更新
            except Exception as e:
                self.logger.warning(f"無法獲取UAV狀態: {e}")
    
    async def _update_from_network_status(self, network_status: Dict):
        """從網路狀態更新拓撲"""
        nodes_info = network_status.get("nodes", [])
        
        # 更新節點信息
        for node_info in nodes_info:
            node_id = node_info["node_id"]
            if node_id not in self.current_topology.nodes:
                # 創建新節點
                node = TopologyNode(
                    node_id=node_id,
                    node_type=node_info["node_type"],
                    position=UAVPosition(latitude=0, longitude=0, altitude=0),  # 需要實際位置
                    energy_level=node_info.get("energy_level", 100.0)
                )
                self.current_topology.nodes[node_id] = node
            else:
                # 更新現有節點
                node = self.current_topology.nodes[node_id]
                node.energy_level = node_info.get("energy_level", node.energy_level)
                node.last_update = datetime.now()
    
    async def _calculate_topology_metrics(self):
        """計算拓撲指標"""
        nodes = self.current_topology.nodes
        links = self.current_topology.links
        
        if not nodes:
            return
        
        # 連接性指數
        total_possible_connections = len(nodes) * (len(nodes) - 1)
        actual_connections = len(links) * 2  # 雙向連結
        connectivity_index = actual_connections / max(1, total_possible_connections)
        
        # 平均路徑長度
        average_path_length = await self._calculate_average_path_length()
        
        # 聚類係數
        clustering_coefficient = await self._calculate_clustering_coefficient()
        
        # 網路直徑
        network_diameter = await self._calculate_network_diameter()
        
        # 負載分佈方差
        loads = [node.current_load for node in nodes.values()]
        load_variance = np.var(loads) if loads else 0.0
        
        # 容錯性評估
        fault_tolerance = await self._assess_fault_tolerance()
        
        # 能源效率
        energy_levels = [node.energy_level for node in nodes.values()]
        energy_efficiency = np.mean(energy_levels) / 100.0 if energy_levels else 0.0
        
        # 更新指標
        self.current_topology.metrics = TopologyMetrics(
            connectivity_index=connectivity_index,
            clustering_coefficient=clustering_coefficient,
            average_path_length=average_path_length,
            network_diameter=network_diameter,
            load_distribution_variance=load_variance,
            fault_tolerance=fault_tolerance,
            energy_efficiency=energy_efficiency
        )
    
    async def _detect_adjustment_triggers(self) -> List[Dict]:
        """檢測調整觸發條件"""
        triggers = []
        metrics = self.current_topology.metrics
        
        # 性能退化檢測
        if metrics.connectivity_index < 0.6:
            triggers.append({
                "trigger": TopologyAdjustmentTrigger.CONNECTIVITY_LOSS,
                "severity": "high",
                "metric_value": metrics.connectivity_index,
                "threshold": 0.6
            })
        
        # 負載不平衡檢測
        if metrics.load_distribution_variance > 0.3:
            triggers.append({
                "trigger": TopologyAdjustmentTrigger.LOAD_IMBALANCE,
                "severity": "medium",
                "metric_value": metrics.load_distribution_variance,
                "threshold": 0.3
            })
        
        # 能源耗盡檢測
        if metrics.energy_efficiency < 0.3:
            triggers.append({
                "trigger": TopologyAdjustmentTrigger.ENERGY_DEPLETION,
                "severity": "high",
                "metric_value": metrics.energy_efficiency,
                "threshold": 0.3
            })
        
        # 節點故障檢測
        failed_nodes = [
            node_id for node_id, node in self.current_topology.nodes.items()
            if (datetime.now() - node.last_update).seconds > 60
        ]
        if failed_nodes:
            triggers.append({
                "trigger": TopologyAdjustmentTrigger.NODE_FAILURE,
                "severity": "high",
                "failed_nodes": failed_nodes
            })
        
        # 主動優化檢測（定期觸發）
        if (not self.current_topology.last_adjustment or 
            (datetime.now() - self.current_topology.last_adjustment).seconds > 300):
            
            # 計算綜合性能分數
            performance_score = (
                metrics.connectivity_index * 0.3 +
                (1.0 - metrics.load_distribution_variance) * 0.3 +
                metrics.fault_tolerance * 0.2 +
                metrics.energy_efficiency * 0.2
            )
            
            if performance_score < 0.8:
                triggers.append({
                    "trigger": TopologyAdjustmentTrigger.PROACTIVE_OPTIMIZATION,
                    "severity": "low",
                    "performance_score": performance_score,
                    "threshold": 0.8
                })
        
        return triggers
    
    async def _execute_topology_adjustment(self, trigger_info: Dict):
        """執行拓撲調整"""
        async with self.adjustment_lock:
            start_time = datetime.now()
            
            adjustment_id = f"adj_{uuid.uuid4().hex[:8]}"
            trigger = trigger_info["trigger"]
            severity = trigger_info.get("severity", "medium")
            
            # 選擇調整策略
            strategy = self._select_adjustment_strategy(trigger, severity)
            
            # 記錄調整前指標
            metrics_before = self.current_topology.metrics
            
            self.logger.info(
                f"開始拓撲調整: {adjustment_id}",
                trigger=trigger.value,
                strategy=strategy.value,
                severity=severity
            )
            
            # 執行調整
            changes = await self._perform_topology_changes(trigger, strategy, trigger_info)
            
            # 重新計算指標
            await self._calculate_topology_metrics()
            metrics_after = self.current_topology.metrics
            
            # 計算改善分數
            improvement_score = self._calculate_improvement_score(metrics_before, metrics_after)
            
            # 記錄調整
            execution_time = (datetime.now() - start_time).total_seconds()
            adjustment = TopologyAdjustment(
                adjustment_id=adjustment_id,
                trigger=trigger,
                strategy=strategy,
                changes=changes,
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvement_score=improvement_score,
                execution_time=execution_time
            )
            
            self.current_topology.adjustment_history.append(adjustment)
            self.current_topology.last_adjustment = datetime.now()
            
            # 記錄調整統計
            self.adjustment_counter += 1
            self.last_hour_adjustments.append(datetime.now())
            
            self.logger.info(
                f"拓撲調整完成: {adjustment_id}",
                changes_count=len(changes),
                improvement_score=improvement_score,
                execution_time=execution_time
            )
    
    def _select_adjustment_strategy(
        self, 
        trigger: TopologyAdjustmentTrigger, 
        severity: str
    ) -> AdjustmentStrategy:
        """選擇調整策略"""
        if severity == "high" or trigger == TopologyAdjustmentTrigger.NODE_FAILURE:
            return AdjustmentStrategy.EMERGENCY
        elif severity == "medium":
            return AdjustmentStrategy.BALANCED
        elif trigger == TopologyAdjustmentTrigger.PROACTIVE_OPTIMIZATION:
            return AdjustmentStrategy.CONSERVATIVE
        else:
            return AdjustmentStrategy.BALANCED
    
    async def _perform_topology_changes(
        self, 
        trigger: TopologyAdjustmentTrigger, 
        strategy: AdjustmentStrategy, 
        trigger_info: Dict
    ) -> List[Dict]:
        """執行拓撲變更"""
        changes = []
        
        if trigger == TopologyAdjustmentTrigger.NODE_FAILURE:
            # 處理節點故障
            failed_nodes = trigger_info.get("failed_nodes", [])
            changes.extend(await self._handle_node_failures(failed_nodes, strategy))
            
        elif trigger == TopologyAdjustmentTrigger.LOAD_IMBALANCE:
            # 處理負載不平衡
            changes.extend(await self._rebalance_network_load(strategy))
            
        elif trigger == TopologyAdjustmentTrigger.CONNECTIVITY_LOSS:
            # 處理連接性損失
            changes.extend(await self._restore_network_connectivity(strategy))
            
        elif trigger == TopologyAdjustmentTrigger.ENERGY_DEPLETION:
            # 處理能源耗盡
            changes.extend(await self._optimize_energy_usage(strategy))
            
        elif trigger == TopologyAdjustmentTrigger.PROACTIVE_OPTIMIZATION:
            # 主動優化
            changes.extend(await self._perform_proactive_optimization(strategy))
        
        return changes
    
    async def _handle_node_failures(self, failed_nodes: List[str], strategy: AdjustmentStrategy) -> List[Dict]:
        """處理節點故障"""
        changes = []
        
        for node_id in failed_nodes:
            if node_id in self.current_topology.nodes:
                failed_node = self.current_topology.nodes[node_id]
                
                # 移除故障節點
                del self.current_topology.nodes[node_id]
                changes.append({
                    "action": "remove_node",
                    "node_id": node_id,
                    "reason": "node_failure"
                })
                
                # 移除相關連結
                links_to_remove = [
                    link_id for link_id, link in self.current_topology.links.items()
                    if link.source_node == node_id or link.target_node == node_id
                ]
                
                for link_id in links_to_remove:
                    del self.current_topology.links[link_id]
                    changes.append({
                        "action": "remove_link",
                        "link_id": link_id,
                        "reason": "connected_to_failed_node"
                    })
                
                # 如果是關鍵節點，嘗試重建連接
                if failed_node.is_critical:
                    changes.extend(await self._rebuild_critical_connections(failed_node, strategy))
        
        return changes
    
    async def _rebalance_network_load(self, strategy: AdjustmentStrategy) -> List[Dict]:
        """重新平衡網路負載"""
        changes = []
        
        # 識別高負載和低負載節點
        nodes = list(self.current_topology.nodes.values())
        avg_load = np.mean([node.current_load for node in nodes])
        
        high_load_nodes = [node for node in nodes if node.current_load > avg_load * 1.5]
        low_load_nodes = [node for node in nodes if node.current_load < avg_load * 0.5]
        
        # 在高負載節點附近添加連結以分散負載
        for high_load_node in high_load_nodes:
            potential_targets = [
                node for node in low_load_nodes 
                if node.node_id not in high_load_node.connections
            ]
            
            if potential_targets and strategy != AdjustmentStrategy.CONSERVATIVE:
                # 選擇最近的低負載節點
                target_node = min(potential_targets, key=lambda n: 
                    self._calculate_node_distance(high_load_node, n))
                
                # 創建新連結
                link_id = f"link_{uuid.uuid4().hex[:8]}"
                new_link = TopologyLink(
                    link_id=link_id,
                    source_node=high_load_node.node_id,
                    target_node=target_node.node_id
                )
                
                self.current_topology.links[link_id] = new_link
                high_load_node.connections.add(target_node.node_id)
                target_node.connections.add(high_load_node.node_id)
                
                changes.append({
                    "action": "add_link",
                    "link_id": link_id,
                    "source": high_load_node.node_id,
                    "target": target_node.node_id,
                    "reason": "load_balancing"
                })
        
        return changes
    
    def _calculate_node_distance(self, node1: TopologyNode, node2: TopologyNode) -> float:
        """計算節點距離"""
        lat_diff = (node2.position.latitude - node1.position.latitude) * 111000
        lon_diff = (node2.position.longitude - node1.position.longitude) * 111000
        alt_diff = node2.position.altitude - node1.position.altitude
        
        return np.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)
    
    async def _check_adjustment_rate_limit(self) -> bool:
        """檢查調整頻率限制"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # 清理舊記錄
        self.last_hour_adjustments = [
            t for t in self.last_hour_adjustments if t > one_hour_ago
        ]
        
        return len(self.last_hour_adjustments) < self.max_adjustments_per_hour
    
    def _calculate_improvement_score(
        self, 
        before: TopologyMetrics, 
        after: TopologyMetrics
    ) -> float:
        """計算改善分數"""
        # 各指標的權重
        weights = {
            'connectivity_index': 0.25,
            'fault_tolerance': 0.20,
            'energy_efficiency': 0.20,
            'load_distribution_variance': 0.15,  # 負向指標
            'average_path_length': 0.10,         # 負向指標
            'clustering_coefficient': 0.10
        }
        
        improvements = []
        
        # 正向指標（值越大越好）
        positive_metrics = ['connectivity_index', 'fault_tolerance', 'energy_efficiency', 'clustering_coefficient']
        for metric in positive_metrics:
            before_val = getattr(before, metric, 0.0)
            after_val = getattr(after, metric, 0.0)
            improvement = (after_val - before_val) / max(0.001, before_val)
            improvements.append(improvement * weights[metric])
        
        # 負向指標（值越小越好）
        negative_metrics = ['load_distribution_variance', 'average_path_length']
        for metric in negative_metrics:
            before_val = getattr(before, metric, 1.0)
            after_val = getattr(after, metric, 1.0)
            improvement = (before_val - after_val) / max(0.001, before_val)
            improvements.append(improvement * weights[metric])
        
        return sum(improvements)
    
    async def analyze_topology(self, request: TopologyAnalysisRequest) -> Dict[str, any]:
        """分析拓撲"""
        analysis_result = {
            "topology_id": self.current_topology.topology_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "current_metrics": {
                "connectivity_index": self.current_topology.metrics.connectivity_index,
                "clustering_coefficient": self.current_topology.metrics.clustering_coefficient,
                "average_path_length": self.current_topology.metrics.average_path_length,
                "network_diameter": self.current_topology.metrics.network_diameter,
                "fault_tolerance": self.current_topology.metrics.fault_tolerance,
                "energy_efficiency": self.current_topology.metrics.energy_efficiency,
                "load_distribution_variance": self.current_topology.metrics.load_distribution_variance
            },
            "network_summary": {
                "total_nodes": len(self.current_topology.nodes),
                "total_links": len(self.current_topology.links),
                "active_nodes": sum(1 for n in self.current_topology.nodes.values() 
                                  if (datetime.now() - n.last_update).seconds < 60),
                "critical_nodes": sum(1 for n in self.current_topology.nodes.values() if n.is_critical),
                "average_node_degree": np.mean([len(n.connections) for n in self.current_topology.nodes.values()]) if self.current_topology.nodes else 0
            }
        }
        
        if request.analysis_depth in ["detailed", "full"]:
            # 添加詳細分析
            analysis_result["bottleneck_analysis"] = await self._analyze_bottlenecks()
            analysis_result["resilience_analysis"] = await self._analyze_resilience()
            
        if request.analysis_depth == "full":
            # 添加完整分析
            analysis_result["optimization_recommendations"] = await self._generate_optimization_recommendations()
            analysis_result["trend_analysis"] = self._analyze_performance_trends(request.time_window_minutes)
        
        if request.include_predictions:
            analysis_result["performance_predictions"] = await self._predict_performance_trends()
        
        return analysis_result
    
    async def get_adjustment_history(self, limit: int = 50) -> Dict[str, any]:
        """獲取調整歷史"""
        recent_adjustments = self.current_topology.adjustment_history[-limit:]
        
        return {
            "total_adjustments": len(self.current_topology.adjustment_history),
            "recent_adjustments": [
                {
                    "adjustment_id": adj.adjustment_id,
                    "trigger": adj.trigger.value,
                    "strategy": adj.strategy.value,
                    "changes_count": len(adj.changes),
                    "improvement_score": adj.improvement_score,
                    "execution_time": adj.execution_time,
                    "timestamp": adj.timestamp.isoformat()
                }
                for adj in recent_adjustments
            ],
            "adjustment_statistics": {
                "total_count": self.adjustment_counter,
                "last_hour_count": len(self.last_hour_adjustments),
                "rate_limit": self.max_adjustments_per_hour,
                "average_improvement": np.mean([adj.improvement_score for adj in recent_adjustments]) if recent_adjustments else 0.0
            }
        }