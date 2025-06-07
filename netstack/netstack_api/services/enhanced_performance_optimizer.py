"""
增強版性能優化器 (Enhanced Performance Optimizer)

實現階段七要求的多維度性能調優算法，包括：
1. 端到端延遲優化
2. 系統資源利用率優化
3. 網路吞吐量優化
4. AI算法性能優化
5. 自動化性能調優決策
"""

import asyncio
import time
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog
import psutil
import threading
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
import json

logger = structlog.get_logger(__name__)


class OptimizationDomain(Enum):
    """優化領域"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RESOURCE_UTILIZATION = "resource_utilization"
    AI_PERFORMANCE = "ai_performance"
    NETWORK_EFFICIENCY = "network_efficiency"
    SATELLITE_HANDOVER = "satellite_handover"
    UAV_COORDINATION = "uav_coordination"


class OptimizationStrategy(Enum):
    """優化策略"""
    CONSERVATIVE = "conservative"  # 保守策略，小幅優化
    BALANCED = "balanced"         # 平衡策略，適中優化
    AGGRESSIVE = "aggressive"     # 激進策略，大幅優化
    ADAPTIVE = "adaptive"         # 自適應策略，根據環境決定


class PerformanceIndicator(Enum):
    """性能指標"""
    E2E_LATENCY_MS = "e2e_latency_ms"
    THROUGHPUT_MBPS = "throughput_mbps"
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    GPU_UTILIZATION = "gpu_utilization"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    HANDOVER_SUCCESS_RATE = "handover_success_rate"
    AI_INFERENCE_TIME = "ai_inference_time"


@dataclass
class PerformanceTarget:
    """性能目標"""
    indicator: PerformanceIndicator
    target_value: float
    tolerance: float = 0.1  # 容忍度
    priority: int = 1       # 優先級 (1-10)
    constraint_type: str = "max"  # max, min, exact


@dataclass
class OptimizationAction:
    """優化動作"""
    action_id: str
    domain: OptimizationDomain
    action_type: str
    parameters: Dict[str, Any]
    expected_improvement: float
    risk_level: str = "low"  # low, medium, high
    rollback_available: bool = True
    execution_time_estimate: float = 0.0  # 執行時間估計(秒)


@dataclass
class OptimizationResult:
    """優化結果"""
    action_id: str
    domain: OptimizationDomain
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_achieved: Dict[str, float]
    execution_time: float
    success: bool
    timestamp: datetime
    rollback_performed: bool = False
    side_effects: List[str] = field(default_factory=list)


@dataclass
class SystemState:
    """系統狀態"""
    timestamp: datetime
    metrics: Dict[str, float]
    active_services: List[str]
    resource_usage: Dict[str, float]
    network_conditions: Dict[str, Any]
    ai_model_performance: Dict[str, float]


class MLPerformancePredictor:
    """機器學習性能預測器"""
    
    def __init__(self):
        self.models: Dict[PerformanceIndicator, Any] = {}
        self.scalers: Dict[PerformanceIndicator, StandardScaler] = {}
        self.training_data: Dict[PerformanceIndicator, List[Tuple]] = {}
        self.is_trained = False
        
    def add_training_data(self, features: List[float], target: PerformanceIndicator, value: float):
        """添加訓練數據"""
        if target not in self.training_data:
            self.training_data[target] = []
        self.training_data[target].append((features, value))
    
    def train_models(self):
        """訓練預測模型"""
        for indicator, data in self.training_data.items():
            if len(data) < 10:  # 需要至少10個樣本
                continue
                
            X = [features for features, _ in data]
            y = [value for _, value in data]
            
            # 數據標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # 訓練線性回歸模型
            model = LinearRegression()
            model.fit(X_scaled, y)
            
            self.scalers[indicator] = scaler
            self.models[indicator] = model
            
        self.is_trained = True
        logger.info(f"訓練了 {len(self.models)} 個性能預測模型")
    
    def predict_performance(self, features: List[float], indicator: PerformanceIndicator) -> Optional[float]:
        """預測性能指標"""
        if not self.is_trained or indicator not in self.models:
            return None
            
        try:
            scaler = self.scalers[indicator]
            model = self.models[indicator]
            
            features_scaled = scaler.transform([features])
            prediction = model.predict(features_scaled)[0]
            
            return prediction
        except Exception as e:
            logger.error(f"性能預測失敗: {e}")
            return None


class EnhancedPerformanceOptimizer:
    """增強版性能優化器"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        
        # 性能目標
        self.performance_targets = self._initialize_performance_targets()
        
        # 優化歷史
        self.optimization_history: List[OptimizationResult] = []
        
        # 系統狀態歷史
        self.system_states: List[SystemState] = []
        
        # ML 預測器
        self.ml_predictor = MLPerformancePredictor()
        
        # 優化策略
        self.current_strategy = OptimizationStrategy.BALANCED
        
        # 優化鎖定（防止並發優化）
        self.optimization_lock = threading.Lock()
        
        # 優化統計
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "failed_optimizations": 0,
            "rollbacks_performed": 0,
            "total_improvement_achieved": {},
            "average_execution_time": 0.0
        }
        
        # 自動優化開關
        self.auto_optimization_enabled = True
        
        # 監控任務
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
    
    def _initialize_performance_targets(self) -> Dict[PerformanceIndicator, PerformanceTarget]:
        """初始化性能目標"""
        targets = {
            PerformanceIndicator.E2E_LATENCY_MS: PerformanceTarget(
                indicator=PerformanceIndicator.E2E_LATENCY_MS,
                target_value=50.0,
                tolerance=0.2,
                priority=10,
                constraint_type="max"
            ),
            PerformanceIndicator.THROUGHPUT_MBPS: PerformanceTarget(
                indicator=PerformanceIndicator.THROUGHPUT_MBPS,
                target_value=100.0,
                tolerance=0.1,
                priority=8,
                constraint_type="min"
            ),
            PerformanceIndicator.CPU_UTILIZATION: PerformanceTarget(
                indicator=PerformanceIndicator.CPU_UTILIZATION,
                target_value=80.0,
                tolerance=0.1,
                priority=7,
                constraint_type="max"
            ),
            PerformanceIndicator.MEMORY_UTILIZATION: PerformanceTarget(
                indicator=PerformanceIndicator.MEMORY_UTILIZATION,
                target_value=85.0,
                tolerance=0.1,
                priority=6,
                constraint_type="max"
            ),
            PerformanceIndicator.CACHE_HIT_RATE: PerformanceTarget(
                indicator=PerformanceIndicator.CACHE_HIT_RATE,
                target_value=90.0,
                tolerance=0.05,
                priority=5,
                constraint_type="min"
            ),
            PerformanceIndicator.ERROR_RATE: PerformanceTarget(
                indicator=PerformanceIndicator.ERROR_RATE,
                target_value=1.0,
                tolerance=0.5,
                priority=9,
                constraint_type="max"
            ),
            PerformanceIndicator.HANDOVER_SUCCESS_RATE: PerformanceTarget(
                indicator=PerformanceIndicator.HANDOVER_SUCCESS_RATE,
                target_value=95.0,
                tolerance=0.02,
                priority=8,
                constraint_type="min"
            )
        }
        return targets
    
    async def start_monitoring(self):
        """開始性能監控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("增強版性能監控已啟動")
    
    async def stop_monitoring(self):
        """停止性能監控"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("增強版性能監控已停止")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 收集系統狀態
                current_state = await self._collect_system_state()
                self.system_states.append(current_state)
                
                # 保留最近1000個狀態
                if len(self.system_states) > 1000:
                    self.system_states = self.system_states[-1000:]
                
                # 分析性能趨勢
                performance_issues = await self._analyze_performance_trends()
                
                # 自動優化（如果啟用）
                if self.auto_optimization_enabled and performance_issues:
                    await self._trigger_auto_optimization(performance_issues)
                
                # 更新ML模型
                await self._update_ml_models()
                
                await asyncio.sleep(10.0)  # 每10秒監控一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能監控循環異常: {e}")
                await asyncio.sleep(30.0)
    
    async def _collect_system_state(self) -> SystemState:
        """收集系統狀態"""
        current_time = datetime.now()
        
        # 收集基礎指標
        metrics = {}
        
        # CPU 指標
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics[PerformanceIndicator.CPU_UTILIZATION.value] = cpu_percent
        
        # 記憶體指標
        memory = psutil.virtual_memory()
        metrics[PerformanceIndicator.MEMORY_UTILIZATION.value] = memory.percent
        
        # 模擬其他指標（實際應從真實服務收集）
        metrics[PerformanceIndicator.E2E_LATENCY_MS.value] = await self._measure_e2e_latency()
        metrics[PerformanceIndicator.THROUGHPUT_MBPS.value] = await self._measure_throughput()
        metrics[PerformanceIndicator.CACHE_HIT_RATE.value] = await self._measure_cache_hit_rate()
        metrics[PerformanceIndicator.ERROR_RATE.value] = await self._measure_error_rate()
        metrics[PerformanceIndicator.HANDOVER_SUCCESS_RATE.value] = await self._measure_handover_success_rate()
        
        # 資源使用情況
        resource_usage = {
            "cpu_cores": psutil.cpu_count(),
            "memory_gb": memory.total / (1024**3),
            "disk_usage_percent": psutil.disk_usage("/").percent
        }
        
        # 活躍服務（模擬）
        active_services = [
            "netstack-api", "simworld-backend", "open5gs-amf", 
            "ueransim-gnb", "satellite-handover-service"
        ]
        
        # 網路條件（模擬）
        network_conditions = {
            "bandwidth_mbps": 1000,
            "packet_loss_rate": 0.001,
            "jitter_ms": 2.0
        }
        
        # AI模型性能（模擬）
        ai_model_performance = {
            "interference_detection_accuracy": 0.92,
            "handover_prediction_accuracy": 0.88,
            "resource_allocation_efficiency": 0.85
        }
        
        return SystemState(
            timestamp=current_time,
            metrics=metrics,
            active_services=active_services,
            resource_usage=resource_usage,
            network_conditions=network_conditions,
            ai_model_performance=ai_model_performance
        )
    
    async def _measure_e2e_latency(self) -> float:
        """測量端到端延遲"""
        # 模擬端到端延遲測量
        import random
        base_latency = 45.0
        variation = random.uniform(-10, 15)
        return max(20.0, base_latency + variation)
    
    async def _measure_throughput(self) -> float:
        """測量吞吐量"""
        # 模擬吞吐量測量
        import random
        base_throughput = 95.0
        variation = random.uniform(-20, 30)
        return max(50.0, base_throughput + variation)
    
    async def _measure_cache_hit_rate(self) -> float:
        """測量快取命中率"""
        import random
        return random.uniform(85.0, 95.0)
    
    async def _measure_error_rate(self) -> float:
        """測量錯誤率"""
        import random
        return random.uniform(0.5, 2.0)
    
    async def _measure_handover_success_rate(self) -> float:
        """測量換手成功率"""
        import random
        return random.uniform(92.0, 98.0)
    
    async def _analyze_performance_trends(self) -> List[PerformanceIndicator]:
        """分析性能趨勢"""
        if len(self.system_states) < 5:
            return []
        
        issues = []
        recent_states = self.system_states[-10:]  # 最近10個狀態
        
        for indicator, target in self.performance_targets.items():
            values = [state.metrics.get(indicator.value, 0) for state in recent_states]
            
            if not values:
                continue
            
            current_value = values[-1]
            trend_slope = self._calculate_trend_slope(values)
            
            # 檢查是否違反目標
            if target.constraint_type == "max" and current_value > target.target_value:
                issues.append(indicator)
            elif target.constraint_type == "min" and current_value < target.target_value:
                issues.append(indicator)
            elif target.constraint_type == "exact":
                deviation = abs(current_value - target.target_value) / target.target_value
                if deviation > target.tolerance:
                    issues.append(indicator)
            
            # 檢查負面趨勢
            if target.constraint_type == "max" and trend_slope > 0 and current_value > target.target_value * 0.9:
                if indicator not in issues:
                    issues.append(indicator)
            elif target.constraint_type == "min" and trend_slope < 0 and current_value < target.target_value * 1.1:
                if indicator not in issues:
                    issues.append(indicator)
        
        return issues
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """計算趨勢斜率"""
        if len(values) < 2:
            return 0.0
        
        x = list(range(len(values)))
        try:
            slope = np.polyfit(x, values, 1)[0]
            return slope
        except:
            return 0.0
    
    async def _trigger_auto_optimization(self, issues: List[PerformanceIndicator]):
        """觸發自動優化"""
        if not issues:
            return
        
        # 按優先級排序問題
        sorted_issues = sorted(issues, key=lambda x: self.performance_targets[x].priority, reverse=True)
        
        self.logger.info(f"檢測到性能問題，開始自動優化: {[issue.value for issue in sorted_issues[:3]]}")
        
        # 處理前3個最高優先級問題
        for issue in sorted_issues[:3]:
            try:
                optimization_actions = await self._generate_optimization_actions(issue)
                
                for action in optimization_actions[:2]:  # 最多執行2個動作
                    await self._execute_optimization_action(action)
                    
            except Exception as e:
                self.logger.error(f"自動優化執行失敗 {issue.value}: {e}")
    
    async def _generate_optimization_actions(self, issue: PerformanceIndicator) -> List[OptimizationAction]:
        """生成優化動作"""
        actions = []
        
        if issue == PerformanceIndicator.E2E_LATENCY_MS:
            actions.extend([
                OptimizationAction(
                    action_id=f"latency_opt_{int(time.time())}",
                    domain=OptimizationDomain.LATENCY,
                    action_type="cache_optimization",
                    parameters={"cache_size_increase": 20, "ttl_adjustment": -0.1},
                    expected_improvement=0.15,
                    risk_level="low"
                ),
                OptimizationAction(
                    action_id=f"latency_opt_parallel_{int(time.time())}",
                    domain=OptimizationDomain.LATENCY,
                    action_type="parallel_processing",
                    parameters={"worker_threads": 2, "batch_size": 10},
                    expected_improvement=0.20,
                    risk_level="medium"
                )
            ])
        
        elif issue == PerformanceIndicator.THROUGHPUT_MBPS:
            actions.extend([
                OptimizationAction(
                    action_id=f"throughput_opt_{int(time.time())}",
                    domain=OptimizationDomain.THROUGHPUT,
                    action_type="buffer_optimization",
                    parameters={"buffer_size_increase": 30, "compression_enabled": True},
                    expected_improvement=0.25,
                    risk_level="low"
                ),
                OptimizationAction(
                    action_id=f"throughput_opt_conn_{int(time.time())}",
                    domain=OptimizationDomain.THROUGHPUT,
                    action_type="connection_pooling",
                    parameters={"max_connections": 50, "keep_alive": True},
                    expected_improvement=0.18,
                    risk_level="medium"
                )
            ])
        
        elif issue == PerformanceIndicator.CPU_UTILIZATION:
            actions.extend([
                OptimizationAction(
                    action_id=f"cpu_opt_{int(time.time())}",
                    domain=OptimizationDomain.RESOURCE_UTILIZATION,
                    action_type="algorithm_optimization",
                    parameters={"optimization_level": 2, "vectorization": True},
                    expected_improvement=0.20,
                    risk_level="low"
                ),
                OptimizationAction(
                    action_id=f"cpu_opt_schedule_{int(time.time())}",
                    domain=OptimizationDomain.RESOURCE_UTILIZATION,
                    action_type="task_scheduling",
                    parameters={"priority_adjustment": True, "load_balancing": True},
                    expected_improvement=0.15,
                    risk_level="medium"
                )
            ])
        
        elif issue == PerformanceIndicator.MEMORY_UTILIZATION:
            actions.extend([
                OptimizationAction(
                    action_id=f"memory_opt_{int(time.time())}",
                    domain=OptimizationDomain.RESOURCE_UTILIZATION,
                    action_type="garbage_collection",
                    parameters={"aggressive_gc": True, "memory_pool_resize": 10},
                    expected_improvement=0.12,
                    risk_level="low"
                ),
                OptimizationAction(
                    action_id=f"memory_opt_cache_{int(time.time())}",
                    domain=OptimizationDomain.RESOURCE_UTILIZATION,
                    action_type="memory_cache_cleanup",
                    parameters={"cleanup_threshold": 0.8, "lru_eviction": True},
                    expected_improvement=0.10,
                    risk_level="low"
                )
            ])
        
        elif issue == PerformanceIndicator.HANDOVER_SUCCESS_RATE:
            actions.extend([
                OptimizationAction(
                    action_id=f"handover_opt_{int(time.time())}",
                    domain=OptimizationDomain.SATELLITE_HANDOVER,
                    action_type="prediction_tuning",
                    parameters={"confidence_threshold": -0.05, "prediction_window": 5},
                    expected_improvement=0.08,
                    risk_level="medium"
                ),
                OptimizationAction(
                    action_id=f"handover_opt_timeout_{int(time.time())}",
                    domain=OptimizationDomain.SATELLITE_HANDOVER,
                    action_type="timeout_adjustment",
                    parameters={"handover_timeout": 2000, "retry_limit": 3},
                    expected_improvement=0.06,
                    risk_level="low"
                )
            ])
        
        return actions
    
    async def _execute_optimization_action(self, action: OptimizationAction) -> OptimizationResult:
        """執行優化動作"""
        with self.optimization_lock:
            start_time = time.time()
            
            # 記錄執行前的指標
            before_state = await self._collect_system_state()
            before_metrics = before_state.metrics.copy()
            
            success = False
            rollback_performed = False
            side_effects = []
            
            try:
                # 執行優化動作
                success = await self._apply_optimization_action(action)
                
                if success:
                    # 等待優化生效
                    await asyncio.sleep(2.0)
                    
                    # 記錄執行後的指標
                    after_state = await self._collect_system_state()
                    after_metrics = after_state.metrics.copy()
                    
                    # 驗證優化效果
                    improvement_achieved = self._calculate_improvement(before_metrics, after_metrics, action.domain)
                    
                    # 檢查是否有負面影響
                    negative_impacts = self._check_negative_impacts(before_metrics, after_metrics)
                    
                    if negative_impacts:
                        side_effects.extend(negative_impacts)
                        
                        # 如果負面影響嚴重，執行回滾
                        if self._is_severe_impact(negative_impacts) and action.rollback_available:
                            await self._rollback_optimization_action(action)
                            rollback_performed = True
                            success = False
                else:
                    after_metrics = before_metrics.copy()
                    improvement_achieved = {}
                
            except Exception as e:
                self.logger.error(f"優化動作執行異常 {action.action_id}: {e}")
                after_metrics = before_metrics.copy()
                improvement_achieved = {}
                success = False
            
            execution_time = time.time() - start_time
            
            # 創建結果記錄
            result = OptimizationResult(
                action_id=action.action_id,
                domain=action.domain,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_achieved=improvement_achieved,
                execution_time=execution_time,
                success=success,
                timestamp=datetime.now(),
                rollback_performed=rollback_performed,
                side_effects=side_effects
            )
            
            # 記錄結果
            self.optimization_history.append(result)
            
            # 更新統計
            self._update_optimization_stats(result)
            
            # 添加訓練數據到ML模型
            self._add_ml_training_data(action, result)
            
            self.logger.info(
                f"優化動作執行完成: {action.action_id}",
                success=success,
                improvement=improvement_achieved,
                execution_time=execution_time
            )
            
            return result
    
    async def _apply_optimization_action(self, action: OptimizationAction) -> bool:
        """應用優化動作"""
        try:
            if action.action_type == "cache_optimization":
                return await self._apply_cache_optimization(action.parameters)
            elif action.action_type == "parallel_processing":
                return await self._apply_parallel_processing(action.parameters)
            elif action.action_type == "buffer_optimization":
                return await self._apply_buffer_optimization(action.parameters)
            elif action.action_type == "connection_pooling":
                return await self._apply_connection_pooling(action.parameters)
            elif action.action_type == "algorithm_optimization":
                return await self._apply_algorithm_optimization(action.parameters)
            elif action.action_type == "task_scheduling":
                return await self._apply_task_scheduling(action.parameters)
            elif action.action_type == "garbage_collection":
                return await self._apply_garbage_collection(action.parameters)
            elif action.action_type == "memory_cache_cleanup":
                return await self._apply_memory_cache_cleanup(action.parameters)
            elif action.action_type == "prediction_tuning":
                return await self._apply_prediction_tuning(action.parameters)
            elif action.action_type == "timeout_adjustment":
                return await self._apply_timeout_adjustment(action.parameters)
            else:
                self.logger.warning(f"未知的優化動作類型: {action.action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"應用優化動作失敗 {action.action_type}: {e}")
            return False
    
    async def _apply_cache_optimization(self, params: Dict[str, Any]) -> bool:
        """應用快取優化"""
        # 模擬快取優化
        await asyncio.sleep(0.1)
        return True
    
    async def _apply_parallel_processing(self, params: Dict[str, Any]) -> bool:
        """應用並行處理優化"""
        await asyncio.sleep(0.2)
        return True
    
    async def _apply_buffer_optimization(self, params: Dict[str, Any]) -> bool:
        """應用緩衝區優化"""
        await asyncio.sleep(0.1)
        return True
    
    async def _apply_connection_pooling(self, params: Dict[str, Any]) -> bool:
        """應用連接池優化"""
        await asyncio.sleep(0.15)
        return True
    
    async def _apply_algorithm_optimization(self, params: Dict[str, Any]) -> bool:
        """應用算法優化"""
        await asyncio.sleep(0.3)
        return True
    
    async def _apply_task_scheduling(self, params: Dict[str, Any]) -> bool:
        """應用任務調度優化"""
        await asyncio.sleep(0.2)
        return True
    
    async def _apply_garbage_collection(self, params: Dict[str, Any]) -> bool:
        """應用垃圾回收優化"""
        import gc
        gc.collect()
        return True
    
    async def _apply_memory_cache_cleanup(self, params: Dict[str, Any]) -> bool:
        """應用記憶體快取清理"""
        await asyncio.sleep(0.1)
        return True
    
    async def _apply_prediction_tuning(self, params: Dict[str, Any]) -> bool:
        """應用預測調優"""
        await asyncio.sleep(0.1)
        return True
    
    async def _apply_timeout_adjustment(self, params: Dict[str, Any]) -> bool:
        """應用超時調整"""
        await asyncio.sleep(0.05)
        return True
    
    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float], domain: OptimizationDomain) -> Dict[str, float]:
        """計算改善效果"""
        improvements = {}
        
        for metric_name, after_value in after.items():
            before_value = before.get(metric_name, after_value)
            
            if before_value == 0:
                continue
            
            # 根據指標類型計算改善
            if metric_name in ["e2e_latency_ms", "cpu_utilization", "memory_utilization", "error_rate"]:
                # 這些指標越低越好
                improvement = (before_value - after_value) / before_value
            else:
                # 這些指標越高越好
                improvement = (after_value - before_value) / before_value
            
            improvements[metric_name] = improvement
        
        return improvements
    
    def _check_negative_impacts(self, before: Dict[str, float], after: Dict[str, float]) -> List[str]:
        """檢查負面影響"""
        negative_impacts = []
        
        for metric_name, after_value in after.items():
            before_value = before.get(metric_name, after_value)
            
            if before_value == 0:
                continue
            
            change_percent = abs(after_value - before_value) / before_value
            
            # 檢查指標惡化
            if metric_name in ["e2e_latency_ms", "error_rate"]:
                if after_value > before_value * 1.1:  # 惡化超過10%
                    negative_impacts.append(f"{metric_name}_degraded")
            elif metric_name in ["throughput_mbps", "cache_hit_rate", "handover_success_rate"]:
                if after_value < before_value * 0.9:  # 下降超過10%
                    negative_impacts.append(f"{metric_name}_degraded")
        
        return negative_impacts
    
    def _is_severe_impact(self, negative_impacts: List[str]) -> bool:
        """判斷是否為嚴重負面影響"""
        severe_keywords = ["error_rate", "handover_success_rate", "e2e_latency"]
        return any(keyword in impact for impact in negative_impacts for keyword in severe_keywords)
    
    async def _rollback_optimization_action(self, action: OptimizationAction):
        """回滾優化動作"""
        # 模擬回滾操作
        await asyncio.sleep(0.1)
        self.logger.info(f"已回滾優化動作: {action.action_id}")
    
    def _update_optimization_stats(self, result: OptimizationResult):
        """更新優化統計"""
        self.optimization_stats["total_optimizations"] += 1
        
        if result.success:
            self.optimization_stats["successful_optimizations"] += 1
        else:
            self.optimization_stats["failed_optimizations"] += 1
        
        if result.rollback_performed:
            self.optimization_stats["rollbacks_performed"] += 1
        
        # 更新平均執行時間
        total_time = (self.optimization_stats["average_execution_time"] * 
                     (self.optimization_stats["total_optimizations"] - 1) + 
                     result.execution_time)
        self.optimization_stats["average_execution_time"] = total_time / self.optimization_stats["total_optimizations"]
        
        # 更新改善統計
        for metric, improvement in result.improvement_achieved.items():
            if metric not in self.optimization_stats["total_improvement_achieved"]:
                self.optimization_stats["total_improvement_achieved"][metric] = 0
            self.optimization_stats["total_improvement_achieved"][metric] += improvement
    
    def _add_ml_training_data(self, action: OptimizationAction, result: OptimizationResult):
        """添加ML訓練數據"""
        # 構建特徵向量
        features = [
            result.before_metrics.get("cpu_utilization", 0),
            result.before_metrics.get("memory_utilization", 0),
            result.before_metrics.get("e2e_latency_ms", 0),
            result.before_metrics.get("throughput_mbps", 0),
            action.expected_improvement,
            1.0 if action.risk_level == "low" else 2.0 if action.risk_level == "medium" else 3.0
        ]
        
        # 為每個性能指標添加訓練數據
        for metric_name, after_value in result.after_metrics.items():
            try:
                indicator = PerformanceIndicator(metric_name)
                self.ml_predictor.add_training_data(features, indicator, after_value)
            except ValueError:
                # 忽略未定義的指標
                pass
    
    async def _update_ml_models(self):
        """更新ML模型"""
        if len(self.optimization_history) > 20 and len(self.optimization_history) % 10 == 0:
            # 每10次優化後重新訓練模型
            try:
                self.ml_predictor.train_models()
                self.logger.info("ML性能預測模型已更新")
            except Exception as e:
                self.logger.error(f"ML模型更新失敗: {e}")
    
    async def get_optimization_summary(self) -> Dict[str, Any]:
        """獲取優化摘要"""
        current_state = await self._collect_system_state() if self.system_states else None
        
        # 計算性能目標達成狀況
        target_achievement = {}
        if current_state:
            for indicator, target in self.performance_targets.items():
                current_value = current_state.metrics.get(indicator.value, 0)
                if target.constraint_type == "max":
                    achieved = current_value <= target.target_value
                elif target.constraint_type == "min":
                    achieved = current_value >= target.target_value
                else:  # exact
                    deviation = abs(current_value - target.target_value) / target.target_value
                    achieved = deviation <= target.tolerance
                
                target_achievement[indicator.value] = {
                    "achieved": achieved,
                    "current_value": current_value,
                    "target_value": target.target_value,
                    "deviation_percent": abs(current_value - target.target_value) / target.target_value * 100
                }
        
        # 最近優化結果
        recent_optimizations = self.optimization_history[-10:] if self.optimization_history else []
        
        summary = {
            "optimization_stats": self.optimization_stats,
            "target_achievement": target_achievement,
            "recent_optimizations": [
                {
                    "action_id": opt.action_id,
                    "domain": opt.domain.value,
                    "success": opt.success,
                    "improvement": opt.improvement_achieved,
                    "timestamp": opt.timestamp.isoformat()
                } for opt in recent_optimizations
            ],
            "ml_model_status": {
                "trained": self.ml_predictor.is_trained,
                "models_count": len(self.ml_predictor.models),
                "training_data_points": sum(len(data) for data in self.ml_predictor.training_data.values())
            },
            "current_strategy": self.current_strategy.value,
            "auto_optimization_enabled": self.auto_optimization_enabled,
            "monitoring_active": self.is_monitoring
        }
        
        return summary
    
    async def manual_optimization(self, domain: OptimizationDomain, strategy: OptimizationStrategy = None) -> Dict[str, Any]:
        """手動觸發優化"""
        if strategy:
            self.current_strategy = strategy
        
        self.logger.info(f"手動觸發優化: {domain.value}, 策略: {self.current_strategy.value}")
        
        # 識別該領域的性能問題
        current_state = await self._collect_system_state()
        domain_issues = []
        
        for indicator, target in self.performance_targets.items():
            current_value = current_state.metrics.get(indicator.value, 0)
            
            # 檢查是否需要優化
            needs_optimization = False
            if target.constraint_type == "max" and current_value > target.target_value * 0.9:
                needs_optimization = True
            elif target.constraint_type == "min" and current_value < target.target_value * 1.1:
                needs_optimization = True
            
            if needs_optimization:
                domain_issues.append(indicator)
        
        if not domain_issues:
            return {"message": "當前性能良好，無需優化", "domain": domain.value}
        
        # 生成並執行優化動作
        results = []
        for issue in domain_issues[:3]:  # 最多處理3個問題
            actions = await self._generate_optimization_actions(issue)
            for action in actions[:1]:  # 每個問題執行1個動作
                if action.domain == domain:
                    result = await self._execute_optimization_action(action)
                    results.append(result)
        
        return {
            "domain": domain.value,
            "strategy": self.current_strategy.value,
            "actions_executed": len(results),
            "results": [
                {
                    "action_id": r.action_id,
                    "success": r.success,
                    "improvement": r.improvement_achieved
                } for r in results
            ]
        }
    
    def set_optimization_strategy(self, strategy: OptimizationStrategy):
        """設置優化策略"""
        self.current_strategy = strategy
        self.logger.info(f"優化策略已更改為: {strategy.value}")
    
    def enable_auto_optimization(self, enabled: bool = True):
        """啟用/禁用自動優化"""
        self.auto_optimization_enabled = enabled
        self.logger.info(f"自動優化已{'啟用' if enabled else '禁用'}")
    
    def update_performance_target(self, indicator: PerformanceIndicator, target_value: float, tolerance: float = None):
        """更新性能目標"""
        if indicator in self.performance_targets:
            self.performance_targets[indicator].target_value = target_value
            if tolerance is not None:
                self.performance_targets[indicator].tolerance = tolerance
            self.logger.info(f"性能目標已更新: {indicator.value} = {target_value}")