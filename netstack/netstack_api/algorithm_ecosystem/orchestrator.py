"""
🎭 換手協調器 - 重構後的簡化版本

算法生態系統的主控制器，負責協調多個算法的執行。
重構後職責專注於協調，具體功能委派給專門模組。
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

# 導入重構後的模組
from .orchestrator.algorithm_selection import AlgorithmSelector, OrchestratorMode, DecisionStrategy
from .orchestrator.performance_monitoring import PerformanceMonitor, AlgorithmMetrics
from .orchestrator.ab_testing import ABTestManager
from .orchestrator.ensemble_voting import EnsembleVotingManager

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """協調器配置"""
    mode: str = OrchestratorMode.SINGLE_ALGORITHM
    decision_strategy: str = DecisionStrategy.PRIORITY_BASED
    default_algorithm: Optional[str] = None
    enable_caching: bool = True
    cache_ttl_seconds: int = 60
    max_concurrent_requests: int = 100
    ab_test_config: Optional[Dict] = None
    ensemble_config: Optional[Dict] = None


class HandoverOrchestrator:
    """換手協調器 - 重構後的簡化版本
    
    主要職責：
    1. 協調各個專門模組
    2. 管理請求流程
    3. 提供統一的API接口
    """
    
    def __init__(self, algorithm_registry: AlgorithmRegistry, 
                 environment_manager: EnvironmentManager, 
                 config: OrchestratorConfig):
        self.algorithm_registry = algorithm_registry
        self.environment_manager = environment_manager
        self.config = config
        
        # 初始化專門模組
        self._performance_monitor = PerformanceMonitor()
        self._algorithm_selector = AlgorithmSelector(
            algorithm_registry, 
            self._performance_monitor._algorithm_metrics
        )
        self._ab_test_manager = ABTestManager()
        self._ensemble_voting_manager = EnsembleVotingManager(
            self._performance_monitor._algorithm_metrics
        )
        
        # 決策緩存
        self._decision_cache: Dict[str, Tuple[HandoverDecision, datetime]] = {}
        
        # 併發控制
        self._concurrent_requests = 0
        self._request_semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        # 初始化狀態
        self._initialized = False

    async def initialize(self) -> None:
        """初始化協調器"""
        try:
            # 初始化專門模組
            if self.config.ab_test_config:
                await self._ab_test_manager.initialize_ab_testing(self.config.ab_test_config)
            
            if self.config.ensemble_config:
                await self._ensemble_voting_manager.initialize_ensemble()
            
            self._initialized = True
            logger.info("HandoverOrchestrator 初始化完成")
            
        except Exception as e:
            logger.error(f"HandoverOrchestrator 初始化失敗: {e}")
            raise

    async def predict_handover(self, context: HandoverContext, 
                             algorithm_name: Optional[str] = None, 
                             use_cache: bool = None) -> Optional[HandoverDecision]:
        """預測換手決策 - 主要協調方法"""
        if use_cache is None:
            use_cache = self.config.enable_caching
        
        # 併發控制
        async with self._request_semaphore:
            self._concurrent_requests += 1
            
            try:
                start_time = time.time()
                
                # 檢查緩存
                if use_cache:
                    cached_decision = self._get_cached_decision(context)
                    if cached_decision:
                        return cached_decision
                
                # 選擇算法
                if not algorithm_name:
                    algorithm, selected_algorithm_name = await self._algorithm_selector.select_algorithm(
                        context, self.config.mode, self.config.decision_strategy, self.config.default_algorithm
                    )
                else:
                    algorithm = self.algorithm_registry.get_algorithm(algorithm_name)
                    selected_algorithm_name = algorithm_name
                
                if not algorithm:
                    return self._get_fallback_decision(context)
                
                # 執行算法
                try:
                    decision = await algorithm.predict_handover(context)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # 記錄性能指標
                    await self._performance_monitor.record_algorithm_metrics(
                        selected_algorithm_name, execution_time, True, decision.confidence
                    )
                    
                    # 處理A/B測試
                    if self.config.mode == OrchestratorMode.A_B_TESTING:
                        await self._ab_test_manager.record_ab_test_result(selected_algorithm_name, decision)
                    
                    # 處理集成投票
                    if self.config.mode == OrchestratorMode.ENSEMBLE:
                        decision = await self._ensemble_voting_manager.handle_ensemble_decision(
                            context, decision, selected_algorithm_name, self.config.ensemble_config
                        )
                    
                    # 緩存決策
                    if use_cache:
                        self._cache_decision(context, decision)
                    
                    return decision
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    await self._performance_monitor.record_algorithm_metrics(
                        selected_algorithm_name, execution_time, False, 0.0
                    )
                    logger.error(f"算法執行失敗 {selected_algorithm_name}: {e}")
                    return self._get_fallback_decision(context)
                    
            except Exception as e:
                logger.error(f"預測換手決策失敗: {e}")
                return self._get_fallback_decision(context)
                
            finally:
                self._concurrent_requests -= 1

    def _get_fallback_decision(self, context: HandoverContext) -> HandoverDecision:
        """獲取回退決策"""
        try:
            fallback_algorithm = self.algorithm_registry.get_algorithm("random")
            if fallback_algorithm:
                try:
                    decision = fallback_algorithm.predict_handover(context)
                    decision.algorithm_name = "fallback_random"
                    return decision
                except Exception as e:
                    logger.error(f"回退算法執行失敗: {e}")
        except Exception:
            pass
        
        # 最終回退：不換手
        return HandoverDecision(
            handover_decision=HandoverDecisionType.NO_HANDOVER,
            target_satellite_id=None,
            confidence=0.1,
            algorithm_name="emergency_fallback",
            metadata={"reason": "all_algorithms_failed"}
        )

    def _get_cached_decision(self, context: HandoverContext) -> Optional[HandoverDecision]:
        """獲取緩存決策"""
        cache_key = self._generate_cache_key(context)
        if cache_key in self._decision_cache:
            decision, timestamp = self._decision_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.config.cache_ttl_seconds):
                return decision
        return None

    def _cache_decision(self, context: HandoverContext, decision: HandoverDecision) -> None:
        """緩存決策"""
        cache_key = self._generate_cache_key(context)
        
        # 清理過期緩存
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._decision_cache.items()
            if current_time - timestamp >= timedelta(seconds=self.config.cache_ttl_seconds)
        ]
        for key in expired_keys:
            del self._decision_cache[key]
        
        self._decision_cache[cache_key] = (decision, current_time)

    def _generate_cache_key(self, context: HandoverContext) -> str:
        """生成緩存鍵"""
        return f"{context.user_id}_{context.current_satellite_id}_{hash(str(context.signal_metrics))}"

    # === 公共API方法 ===

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """獲取協調器統計信息"""
        return self._performance_monitor.get_orchestrator_stats()

    async def update_config(self, new_config: OrchestratorConfig) -> None:
        """更新配置"""
        self.config = new_config
        
        # 重新初始化相關模組
        if new_config.ab_test_config:
            await self._ab_test_manager.initialize_ab_testing(new_config.ab_test_config)
        
        logger.info("協調器配置已更新")

    async def cleanup(self) -> None:
        """清理資源"""
        self._decision_cache.clear()
        await self._ensemble_voting_manager.initialize_ensemble()  # 重置集成狀態
        logger.info("協調器資源已清理")

    # === A/B測試管理方法 ===

    def set_ab_test_config(self, test_id: str, traffic_split: Dict[str, float]) -> None:
        """設置 A/B 測試配置"""
        self._ab_test_manager.set_ab_test_config(test_id, traffic_split)
        
        # 更新模式為 A/B 測試
        if self.config.mode != OrchestratorMode.A_B_TESTING:
            self.config.mode = OrchestratorMode.A_B_TESTING

    def clear_ab_test_config(self, test_id: str) -> None:
        """清除 A/B 測試配置"""
        self._ab_test_manager.clear_ab_test_config(test_id)

    def get_ab_test_performance(self, test_id: str) -> Dict[str, Any]:
        """獲取 A/B 測試性能數據"""
        return self._ab_test_manager.get_ab_test_performance(test_id)

    def export_metrics_for_analysis(self) -> Dict[str, Any]:
        """導出指標用於分析"""
        return self._performance_monitor.export_metrics_for_analysis()