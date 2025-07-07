"""
🎭 換手協調器

算法生態系統的主控制器，負責協調多個算法的執行、負載均衡、錯誤處理和性能監控。
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque

from .interfaces import (
    HandoverAlgorithm,
    RLHandoverAlgorithm,
    HandoverContext,
    HandoverDecision,
    AlgorithmInfo,
    AlgorithmType,
    HandoverDecisionType
)
from .registry import AlgorithmRegistry
from .environment_manager import EnvironmentManager

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    """協調器模式"""
    SINGLE_ALGORITHM = "single"  # 單一算法模式
    LOAD_BALANCING = "load_balancing"  # 負載均衡模式
    A_B_TESTING = "ab_testing"  # A/B 測試模式
    ENSEMBLE = "ensemble"  # 集成模式
    ADAPTIVE = "adaptive"  # 自適應模式


class DecisionStrategy(Enum):
    """決策策略"""
    PRIORITY_BASED = "priority"  # 基於優先級
    PERFORMANCE_BASED = "performance"  # 基於性能
    ROUND_ROBIN = "round_robin"  # 輪詢
    WEIGHTED_RANDOM = "weighted_random"  # 加權隨機
    CONFIDENCE_BASED = "confidence"  # 基於信心度


@dataclass
class AlgorithmMetrics:
    """算法性能指標"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    success_rate: float = 0.0
    confidence_scores: List[float] = None
    average_confidence: float = 0.0
    last_used: Optional[datetime] = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = []


@dataclass
class OrchestratorConfig:
    """協調器配置"""
    mode: OrchestratorMode = OrchestratorMode.SINGLE_ALGORITHM
    decision_strategy: DecisionStrategy = DecisionStrategy.PRIORITY_BASED
    default_algorithm: Optional[str] = None
    fallback_algorithm: Optional[str] = None
    timeout_seconds: float = 5.0
    max_concurrent_requests: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 60
    enable_monitoring: bool = True
    monitoring_window_minutes: int = 10
    ab_test_config: Optional[Dict[str, Any]] = None
    ensemble_config: Optional[Dict[str, Any]] = None


class HandoverOrchestrator:
    """換手協調器
    
    統一管理和協調多個換手算法的執行，提供負載均衡、錯誤處理、
    性能監控和 A/B 測試等功能。
    """
    
    def __init__(
        self, 
        algorithm_registry: AlgorithmRegistry,
        environment_manager: EnvironmentManager,
        config: Optional[OrchestratorConfig] = None
    ):
        """初始化協調器
        
        Args:
            algorithm_registry: 算法註冊中心
            environment_manager: 環境管理器
            config: 協調器配置
        """
        self.algorithm_registry = algorithm_registry
        self.environment_manager = environment_manager
        self.config = config or OrchestratorConfig()
        
        # 算法性能指標
        self._algorithm_metrics: Dict[str, AlgorithmMetrics] = defaultdict(AlgorithmMetrics)
        
        # 決策緩存
        self._decision_cache: Dict[str, Tuple[HandoverDecision, datetime]] = {}
        
        # 並發控制
        self._concurrent_requests = 0
        self._request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # A/B 測試配置
        self._ab_test_weights: Dict[str, float] = {}
        self._ab_test_results: Dict[str, List[float]] = defaultdict(list)
        self._active_ab_tests: Dict[str, Dict[str, float]] = {}  # test_id -> traffic_split
        
        # 自適應學習
        self._performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # 集成投票記錄
        self._ensemble_decisions: List[Tuple[str, HandoverDecision, datetime]] = []
        
        # 輪詢計數器
        self._round_robin_counter = 0
        
        self._initialized = False
        
        logger.info("換手協調器初始化完成")
    
    async def initialize(self) -> None:
        """初始化協調器"""
        if self._initialized:
            return
        
        logger.info("開始初始化換手協調器...")
        
        # 確保依賴組件已初始化
        if not self.algorithm_registry._initialized:
            await self.algorithm_registry.initialize()
        
        if not self.environment_manager._initialized:
            await self.environment_manager.initialize()
        
        # 初始化 A/B 測試配置
        if self.config.mode == OrchestratorMode.A_B_TESTING:
            await self._initialize_ab_testing()
        
        # 初始化集成配置
        if self.config.mode == OrchestratorMode.ENSEMBLE:
            await self._initialize_ensemble()
        
        self._initialized = True
        logger.info("換手協調器初始化完成")
    
    async def predict_handover(
        self, 
        context: HandoverContext,
        algorithm_name: Optional[str] = None,
        use_cache: bool = None
    ) -> HandoverDecision:
        """執行換手預測
        
        Args:
            context: 換手上下文
            algorithm_name: 指定算法名稱（可選）
            use_cache: 是否使用緩存（可選）
            
        Returns:
            HandoverDecision: 換手決策
        """
        if not self._initialized:
            await self.initialize()
        
        # 並發控制
        async with self._request_semaphore:
            self._concurrent_requests += 1
            
            try:
                start_time = time.time()
                
                # 檢查緩存
                if use_cache is None:
                    use_cache = self.config.enable_caching
                
                if use_cache:
                    cached_decision = self._get_cached_decision(context)
                    if cached_decision:
                        logger.debug(f"返回緩存決策: {context.ue_id}")
                        return cached_decision
                
                # 選擇算法
                if algorithm_name:
                    algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
                    if not algorithm:
                        logger.error(f"指定算法 '{algorithm_name}' 不存在")
                        return await self._get_fallback_decision(context)
                    selected_algorithm_name = algorithm_name
                else:
                    algorithm, selected_algorithm_name = await self._select_algorithm(context)
                    if not algorithm:
                        logger.error("沒有可用的算法")
                        return await self._get_fallback_decision(context)
                
                # 執行算法
                try:
                    decision = await asyncio.wait_for(
                        algorithm.predict_handover(context),
                        timeout=self.config.timeout_seconds
                    )
                    
                    # 設置算法名稱
                    decision.algorithm_name = selected_algorithm_name
                    
                    # 記錄性能指標
                    execution_time = (time.time() - start_time) * 1000
                    await self._record_algorithm_metrics(
                        selected_algorithm_name, 
                        execution_time, 
                        True, 
                        decision.confidence
                    )
                    
                    # 緩存決策
                    if use_cache:
                        self._cache_decision(context, decision)
                    
                    # A/B 測試記錄
                    if self.config.mode == OrchestratorMode.A_B_TESTING:
                        await self._record_ab_test_result(selected_algorithm_name, decision)
                    
                    # 集成模式處理
                    if self.config.mode == OrchestratorMode.ENSEMBLE:
                        decision = await self._handle_ensemble_decision(context, decision, selected_algorithm_name)
                    
                    logger.debug(f"算法 '{selected_algorithm_name}' 完成決策: {decision.handover_decision}")
                    return decision
                    
                except asyncio.TimeoutError:
                    logger.error(f"算法 '{selected_algorithm_name}' 執行超時")
                    await self._record_algorithm_metrics(selected_algorithm_name, self.config.timeout_seconds * 1000, False, 0.0)
                    return await self._get_fallback_decision(context)
                
                except Exception as e:
                    logger.error(f"算法 '{selected_algorithm_name}' 執行失敗: {e}")
                    await self._record_algorithm_metrics(selected_algorithm_name, 0.0, False, 0.0)
                    return await self._get_fallback_decision(context)
                
            finally:
                self._concurrent_requests -= 1
    
    async def _select_algorithm(self, context: HandoverContext) -> Tuple[Optional[HandoverAlgorithm], Optional[str]]:
        """選擇算法
        
        Args:
            context: 換手上下文
            
        Returns:
            Tuple[HandoverAlgorithm, str]: 選擇的算法和名稱
        """
        available_algorithms = self.algorithm_registry.list_enabled_algorithms()
        
        if not available_algorithms:
            return None, None
        
        if self.config.mode == OrchestratorMode.SINGLE_ALGORITHM:
            # 單一算法模式
            algorithm_name = self.config.default_algorithm or available_algorithms[0]
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif self.config.decision_strategy == DecisionStrategy.PRIORITY_BASED:
            # 優先級選擇
            algorithm = self.algorithm_registry.get_best_algorithm("priority")
            algorithm_name = algorithm.name if algorithm else None
            return algorithm, algorithm_name
        
        elif self.config.decision_strategy == DecisionStrategy.PERFORMANCE_BASED:
            # 性能選擇
            best_algorithm_name = self._get_best_performing_algorithm()
            algorithm = self.algorithm_registry.get_algorithm(best_algorithm_name)
            return algorithm, best_algorithm_name
        
        elif self.config.decision_strategy == DecisionStrategy.ROUND_ROBIN:
            # 輪詢選擇
            algorithm_name = available_algorithms[self._round_robin_counter % len(available_algorithms)]
            self._round_robin_counter += 1
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif self.config.decision_strategy == DecisionStrategy.WEIGHTED_RANDOM:
            # 加權隨機選擇
            algorithm_name = self._weighted_random_selection(available_algorithms)
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        elif self.config.decision_strategy == DecisionStrategy.CONFIDENCE_BASED:
            # 基於歷史信心度選擇
            algorithm_name = self._confidence_based_selection(available_algorithms)
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
        
        else:
            # 默認選擇第一個可用算法
            algorithm_name = available_algorithms[0]
            algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
            return algorithm, algorithm_name
    
    def _get_best_performing_algorithm(self) -> str:
        """獲取性能最佳的算法"""
        available_algorithms = self.algorithm_registry.list_enabled_algorithms()
        
        if not available_algorithms:
            return None
        
        best_algorithm = available_algorithms[0]
        best_score = 0.0
        
        for algorithm_name in available_algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.total_requests > 0:
                # 綜合評分：成功率 * 0.6 + (1 - 標準化響應時間) * 0.3 + 平均信心度 * 0.1
                success_score = metrics.success_rate * 0.6
                
                # 標準化響應時間（越小越好）
                if metrics.average_response_time > 0:
                    time_score = max(0, 1 - metrics.average_response_time / 1000) * 0.3
                else:
                    time_score = 0.3
                
                confidence_score = metrics.average_confidence * 0.1
                
                total_score = success_score + time_score + confidence_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_algorithm = algorithm_name
        
        return best_algorithm
    
    def _weighted_random_selection(self, algorithms: List[str]) -> str:
        """加權隨機選擇"""
        weights = []
        for algorithm_name in algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.total_requests > 0:
                # 權重基於成功率和信心度
                weight = metrics.success_rate * metrics.average_confidence
            else:
                weight = 0.5  # 默認權重
            weights.append(weight)
        
        # 歸一化權重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(algorithms)] * len(algorithms)
        
        # 隨機選擇
        return np.random.choice(algorithms, p=weights)
    
    def _confidence_based_selection(self, algorithms: List[str]) -> str:
        """基於信心度的選擇"""
        best_algorithm = algorithms[0]
        highest_confidence = 0.0
        
        for algorithm_name in algorithms:
            metrics = self._algorithm_metrics[algorithm_name]
            if metrics.average_confidence > highest_confidence:
                highest_confidence = metrics.average_confidence
                best_algorithm = algorithm_name
        
        return best_algorithm
    
    async def _get_fallback_decision(self, context: HandoverContext) -> HandoverDecision:
        """獲取回退決策"""
        if self.config.fallback_algorithm:
            fallback_algorithm = self.algorithm_registry.get_algorithm(self.config.fallback_algorithm)
            if fallback_algorithm:
                try:
                    decision = await fallback_algorithm.predict_handover(context)
                    decision.algorithm_name = f"{self.config.fallback_algorithm} (fallback)"
                    return decision
                except Exception as e:
                    logger.error(f"回退算法執行失敗: {e}")
        
        # 最終回退：安全決策
        return HandoverDecision(
            target_satellite=None,
            handover_decision=HandoverDecisionType.NO_HANDOVER,
            confidence=0.1,
            timing=None,
            decision_reason="Fallback: No algorithm available",
            algorithm_name="fallback",
            decision_time=0.0,
            metadata={"fallback": True}
        )
    
    async def _record_algorithm_metrics(
        self, 
        algorithm_name: str, 
        execution_time: float, 
        success: bool, 
        confidence: float
    ) -> None:
        """記錄算法性能指標"""
        metrics = self._algorithm_metrics[algorithm_name]
        
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        metrics.total_response_time += execution_time
        metrics.average_response_time = metrics.total_response_time / metrics.total_requests
        
        if execution_time < metrics.min_response_time:
            metrics.min_response_time = execution_time
        if execution_time > metrics.max_response_time:
            metrics.max_response_time = execution_time
        
        metrics.success_rate = metrics.successful_requests / metrics.total_requests
        
        if success:
            metrics.confidence_scores.append(confidence)
            if len(metrics.confidence_scores) > 100:
                metrics.confidence_scores.pop(0)
            metrics.average_confidence = sum(metrics.confidence_scores) / len(metrics.confidence_scores)
        
        metrics.last_used = datetime.now()
        
        # 記錄性能歷史
        self._performance_history[algorithm_name].append({
            'timestamp': datetime.now(),
            'execution_time': execution_time,
            'success': success,
            'confidence': confidence
        })
    
    def _get_cached_decision(self, context: HandoverContext) -> Optional[HandoverDecision]:
        """獲取緩存決策"""
        cache_key = self._generate_cache_key(context)
        
        if cache_key in self._decision_cache:
            decision, timestamp = self._decision_cache[cache_key]
            
            # 檢查緩存是否過期
            if datetime.now() - timestamp < timedelta(seconds=self.config.cache_ttl_seconds):
                return decision
            else:
                # 清理過期緩存
                del self._decision_cache[cache_key]
        
        return None
    
    def _cache_decision(self, context: HandoverContext, decision: HandoverDecision) -> None:
        """緩存決策"""
        cache_key = self._generate_cache_key(context)
        self._decision_cache[cache_key] = (decision, datetime.now())
        
        # 清理過期緩存
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._decision_cache.items()
            if current_time - timestamp >= timedelta(seconds=self.config.cache_ttl_seconds)
        ]
        for key in expired_keys:
            del self._decision_cache[key]
    
    def _generate_cache_key(self, context: HandoverContext) -> str:
        """生成緩存鍵"""
        # 基於關鍵上下文信息生成唯一鍵
        return f"{context.ue_id}_{context.current_satellite}_{len(context.candidate_satellites)}_{hash(str(context.network_state))}"
    
    async def _initialize_ab_testing(self) -> None:
        """初始化 A/B 測試"""
        if not self.config.ab_test_config:
            return
        
        traffic_split = self.config.ab_test_config.get('traffic_split', {})
        total_weight = sum(traffic_split.values())
        
        if total_weight > 0:
            self._ab_test_weights = {
                name: weight / total_weight 
                for name, weight in traffic_split.items()
            }
        
        logger.info(f"A/B 測試配置: {self._ab_test_weights}")
    
    async def _record_ab_test_result(self, algorithm_name: str, decision: HandoverDecision) -> None:
        """記錄 A/B 測試結果"""
        # 這裡可以記錄各種指標，如信心度、決策類型等
        self._ab_test_results[algorithm_name].append(decision.confidence)
        
        # 限制歷史記錄大小
        if len(self._ab_test_results[algorithm_name]) > 1000:
            self._ab_test_results[algorithm_name].pop(0)
    
    async def _initialize_ensemble(self) -> None:
        """初始化集成模式"""
        if not self.config.ensemble_config:
            self.config.ensemble_config = {
                'voting_strategy': 'majority',  # majority, weighted, confidence_based
                'min_algorithms': 2,
                'max_algorithms': 5
            }
        
        logger.info(f"集成模式配置: {self.config.ensemble_config}")
    
    async def _handle_ensemble_decision(
        self, 
        context: HandoverContext, 
        current_decision: HandoverDecision, 
        algorithm_name: str
    ) -> HandoverDecision:
        """處理集成決策"""
        # 記錄當前決策
        self._ensemble_decisions.append((algorithm_name, current_decision, datetime.now()))
        
        # 清理舊決策（只保留最近一段時間的）
        cutoff_time = datetime.now() - timedelta(seconds=1)
        self._ensemble_decisions = [
            (name, decision, timestamp) for name, decision, timestamp in self._ensemble_decisions
            if timestamp > cutoff_time
        ]
        
        min_algorithms = self.config.ensemble_config.get('min_algorithms', 2)
        
        # 如果決策數量不足，直接返回當前決策
        if len(self._ensemble_decisions) < min_algorithms:
            return current_decision
        
        # 執行集成投票
        voting_strategy = self.config.ensemble_config.get('voting_strategy', 'majority')
        
        if voting_strategy == 'majority':
            return self._majority_voting()
        elif voting_strategy == 'weighted':
            return self._weighted_voting()
        elif voting_strategy == 'confidence_based':
            return self._confidence_voting()
        else:
            return current_decision
    
    def _majority_voting(self) -> HandoverDecision:
        """多數投票"""
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        
        # 統計決策類型
        decision_counts = defaultdict(int)
        for decision in decisions:
            decision_counts[decision.handover_decision] += 1
        
        # 找出多數決策
        majority_decision = max(decision_counts.items(), key=lambda x: x[1])[0]
        
        # 找出具有該決策類型且信心度最高的決策
        best_decision = None
        highest_confidence = 0.0
        
        for decision in decisions:
            if decision.handover_decision == majority_decision and decision.confidence > highest_confidence:
                highest_confidence = decision.confidence
                best_decision = decision
        
        if best_decision:
            best_decision.algorithm_name += " (ensemble)"
            best_decision.metadata['ensemble_voting'] = 'majority'
            best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision or decisions[0]
    
    def _weighted_voting(self) -> HandoverDecision:
        """加權投票"""
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        algorithm_names = [name for name, _, _ in self._ensemble_decisions]
        
        # 根據算法性能計算權重
        weights = []
        for name in algorithm_names:
            metrics = self._algorithm_metrics[name]
            weight = metrics.success_rate * metrics.average_confidence if metrics.total_requests > 0 else 0.5
            weights.append(weight)
        
        # 加權投票
        decision_scores = defaultdict(float)
        for i, decision in enumerate(decisions):
            decision_scores[decision.handover_decision] += weights[i]
        
        # 選擇得分最高的決策類型
        best_decision_type = max(decision_scores.items(), key=lambda x: x[1])[0]
        
        # 找出該類型中信心度最高的決策
        best_decision = None
        highest_confidence = 0.0
        
        for decision in decisions:
            if decision.handover_decision == best_decision_type and decision.confidence > highest_confidence:
                highest_confidence = decision.confidence
                best_decision = decision
        
        if best_decision:
            best_decision.algorithm_name += " (ensemble)"
            best_decision.metadata['ensemble_voting'] = 'weighted'
            best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision or decisions[0]
    
    def _confidence_voting(self) -> HandoverDecision:
        """基於信心度的投票"""
        decisions = [decision for _, decision, _ in self._ensemble_decisions]
        
        # 直接選擇信心度最高的決策
        best_decision = max(decisions, key=lambda x: x.confidence)
        best_decision.algorithm_name += " (ensemble)"
        best_decision.metadata['ensemble_voting'] = 'confidence_based'
        best_decision.metadata['ensemble_count'] = len(decisions)
        
        return best_decision
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """獲取協調器統計信息"""
        return {
            'mode': self.config.mode.value,
            'decision_strategy': self.config.decision_strategy.value,
            'algorithm_metrics': {
                name: asdict(metrics) for name, metrics in self._algorithm_metrics.items()
            },
            'concurrent_requests': self._concurrent_requests,
            'cache_size': len(self._decision_cache),
            'ab_test_results': dict(self._ab_test_results) if self.config.mode == OrchestratorMode.A_B_TESTING else {},
            'performance_history_size': {
                name: len(history) for name, history in self._performance_history.items()
            },
            'initialized': self._initialized
        }
    
    async def update_config(self, new_config: OrchestratorConfig) -> None:
        """更新協調器配置"""
        self.config = new_config
        
        # 重新初始化相關組件
        if self.config.mode == OrchestratorMode.A_B_TESTING:
            await self._initialize_ab_testing()
        elif self.config.mode == OrchestratorMode.ENSEMBLE:
            await self._initialize_ensemble()
        
        logger.info("協調器配置更新完成")
    
    async def cleanup(self) -> None:
        """清理資源"""
        logger.info("開始清理換手協調器...")
        
        # 清理緩存
        self._decision_cache.clear()
        
        # 清理統計信息
        self._algorithm_metrics.clear()
        self._ab_test_results.clear()
        self._performance_history.clear()
        self._ensemble_decisions.clear()
        
        self._initialized = False
        logger.info("換手協調器清理完成")
    
    # A/B 測試支持方法（用於分析引擎）
    def set_ab_test_config(self, test_id: str, traffic_split: Dict[str, float]) -> None:
        """設置 A/B 測試配置
        
        Args:
            test_id: 測試ID
            traffic_split: 流量分配比例
        """
        self._active_ab_tests[test_id] = traffic_split
        self._ab_test_weights = traffic_split
        
        # 更新模式為 A/B 測試
        if self.config.mode != OrchestratorMode.A_B_TESTING:
            self.config.mode = OrchestratorMode.A_B_TESTING
        
        logger.info(f"設置 A/B 測試配置: {test_id} -> {traffic_split}")
    
    def clear_ab_test_config(self, test_id: str) -> None:
        """清除 A/B 測試配置
        
        Args:
            test_id: 測試ID
        """
        if test_id in self._active_ab_tests:
            del self._active_ab_tests[test_id]
        
        # 如果沒有活躍的 A/B 測試，切換回單一算法模式
        if not self._active_ab_tests:
            self._ab_test_weights.clear()
            self.config.mode = OrchestratorMode.SINGLE_ALGORITHM
        
        logger.info(f"清除 A/B 測試配置: {test_id}")
    
    def get_ab_test_performance(self, test_id: str) -> Dict[str, Any]:
        """獲取 A/B 測試性能數據
        
        Args:
            test_id: 測試ID
            
        Returns:
            Dict[str, Any]: 性能數據
        """
        if test_id not in self._active_ab_tests:
            return {}
        
        traffic_split = self._active_ab_tests[test_id]
        performance_data = {}
        
        for algorithm_name in traffic_split.keys():
            if algorithm_name in self._algorithm_metrics:
                metrics = self._algorithm_metrics[algorithm_name]
                performance_data[algorithm_name] = {
                    'total_requests': metrics.total_requests,
                    'success_rate': metrics.success_rate,
                    'average_response_time': metrics.average_response_time,
                    'average_confidence': metrics.average_confidence,
                    'traffic_allocation': traffic_split[algorithm_name]
                }
        
        return performance_data
    
    def export_metrics_for_analysis(self) -> Dict[str, Any]:
        """導出指標數據供分析引擎使用
        
        Returns:
            Dict[str, Any]: 指標數據
        """
        export_data = {
            'algorithm_metrics': {},
            'performance_history': {},
            'ab_test_results': dict(self._ab_test_results),
            'active_ab_tests': self._active_ab_tests.copy(),
            'ensemble_decisions': [
                {
                    'algorithm_name': name,
                    'handover_decision': decision.handover_decision.name,
                    'confidence': decision.confidence,
                    'timestamp': timestamp.isoformat()
                }
                for name, decision, timestamp in self._ensemble_decisions
            ]
        }
        
        # 導出算法指標
        for name, metrics in self._algorithm_metrics.items():
            export_data['algorithm_metrics'][name] = {
                'total_requests': metrics.total_requests,
                'success_rate': metrics.success_rate,
                'average_response_time': metrics.average_response_time,
                'min_response_time': metrics.min_response_time,
                'max_response_time': metrics.max_response_time,
                'average_confidence': metrics.average_confidence,
                'last_used': metrics.last_used.isoformat() if metrics.last_used else None
            }
        
        # 導出性能歷史
        for name, history in self._performance_history.items():
            export_data['performance_history'][name] = [
                {
                    'timestamp': record['timestamp'].isoformat(),
                    'execution_time': record['execution_time'],
                    'success': record['success'],
                    'confidence': record['confidence']
                }
                for record in list(history)
            ]
        
        return export_data