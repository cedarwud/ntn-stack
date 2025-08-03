"""
🔧 傳統算法適配器

將現有的傳統算法包裝為統一的 HandoverAlgorithm 接口。
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from ..interfaces import (
    HandoverAlgorithm,
    HandoverContext,
    HandoverDecision,
    AlgorithmInfo,
    AlgorithmType,
    HandoverDecisionType,
    GeoCoordinate,
    SignalMetrics,
    SatelliteInfo
)

# 導入現有算法
try:
    import sys
    from pathlib import Path
    
    # 添加 netstack 根目錄到 Python 路徑
    netstack_root = Path(__file__).parent.parent.parent.parent
    if str(netstack_root) not in sys.path:
        sys.path.insert(0, str(netstack_root))
    
    from scripts.baseline_algorithms.infocom2024_algorithm import InfocomAlgorithm
    from scripts.baseline_algorithms.simple_threshold_algorithm import SimpleThresholdAlgorithm
    from scripts.baseline_algorithms.random_algorithm import RandomAlgorithm
    from scripts.baseline_algorithms.base_algorithm import AlgorithmResult
    BASELINE_ALGORITHMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"無法導入基準算法: {e}")
    BASELINE_ALGORITHMS_AVAILABLE = False
    
    # 創建模擬類以避免錯誤
    class InfocomAlgorithm:
        def __init__(self, name, config): pass
        def decide(self, obs, info): pass
        def get_algorithm_info(self): return {}
    
    class SimpleThresholdAlgorithm:
        def __init__(self, name, config): pass
        def decide(self, obs, info): pass
    
    class RandomAlgorithm:
        def __init__(self, name, config): pass
        def decide(self, obs, info): pass
    
    class AlgorithmResult:
        def __init__(self):
            self.handover_decision = 0
            self.algorithm_name = "mock"
            self.decision_reason = "mock"
            self.decision_time = 0.0

logger = logging.getLogger(__name__)


class BaseTraditionalAdapter(HandoverAlgorithm):
    """傳統算法適配器基類"""
    
    def __init__(self, name: str, wrapped_algorithm: Any, config: Optional[Dict[str, Any]] = None):
        """初始化適配器
        
        Args:
            name: 算法名稱
            wrapped_algorithm: 被包裝的原始算法
            config: 算法配置
        """
        super().__init__(name, config)
        self.wrapped_algorithm = wrapped_algorithm
        self._algorithm_info = None
    
    def _context_to_observation(self, context: HandoverContext) -> tuple:
        """將 HandoverContext 轉換為原始算法的輸入格式
        
        Args:
            context: 換手上下文
            
        Returns:
            tuple: (observation, info) 原始算法所需的輸入
        """
        try:
            # 構建觀察向量 (基於原始算法的期望格式)
            max_satellites = self.config.get('max_satellites', 8)  # 使用 SIB19 合規配置
            obs_dim = 4 + 6 + (6 * max_satellites) + 4  # ue + current_sat + candidates + network
            
            observation = np.zeros(obs_dim)
            
            # UE 特徵 (位置和速度)
            observation[0] = context.ue_location.latitude
            observation[1] = context.ue_location.longitude
            if context.ue_velocity:
                observation[2] = context.ue_velocity.latitude
                observation[3] = context.ue_velocity.longitude
            
            # 當前衛星特徵
            current_sat_start = 4
            if context.current_satellite and context.current_signal_metrics:
                try:
                    sat_id = int(context.current_satellite.split('_')[-1])
                    observation[current_sat_start] = sat_id
                except (ValueError, IndexError):
                    observation[current_sat_start] = 1
                
                observation[current_sat_start + 1] = context.current_signal_metrics.rsrp
                observation[current_sat_start + 2] = context.current_signal_metrics.rsrq
                observation[current_sat_start + 3] = context.current_signal_metrics.sinr
                observation[current_sat_start + 4] = context.current_signal_metrics.throughput
                observation[current_sat_start + 5] = context.current_signal_metrics.latency
            
            # 候選衛星特徵
            candidates_start = current_sat_start + 6
            for i, satellite in enumerate(context.candidate_satellites[:max_satellites]):
                start_idx = candidates_start + i * 6
                
                try:
                    sat_id = int(satellite.satellite_id.split('_')[-1])
                    observation[start_idx] = sat_id
                except (ValueError, IndexError):
                    observation[start_idx] = i + 1
                
                observation[start_idx + 1] = satellite.position.latitude
                observation[start_idx + 2] = satellite.position.longitude
                
                if satellite.signal_metrics:
                    observation[start_idx + 3] = satellite.signal_metrics.rsrp
                    observation[start_idx + 4] = satellite.signal_metrics.rsrq
                    observation[start_idx + 5] = satellite.signal_metrics.sinr
            
            # 網路狀態特徵
            network_start = candidates_start + max_satellites * 6
            network_state = context.network_state or {}
            observation[network_start] = network_state.get('total_ues', 0)
            observation[network_start + 1] = network_state.get('active_satellites', 0)
            observation[network_start + 2] = network_state.get('network_load', 0.0)
            observation[network_start + 3] = network_state.get('interference_level', 0.0)
            
            # 構建 info 字典
            info = {
                'ue_id': context.ue_id,
                'current_satellite': context.current_satellite,
                'timestamp': context.timestamp.timestamp(),
                'scenario_info': context.scenario_info,
                'weather_conditions': context.weather_conditions,
                'traffic_load': context.traffic_load,
                'candidate_count': len(context.candidate_satellites)
            }
            
            return observation, info
            
        except Exception as e:
            logger.error(f"上下文轉換失敗: {e}")
            # 返回最小化的觀察
            obs_dim = 4 + 6 + (6 * self.config.get('max_satellites', 10)) + 4
            return np.zeros(obs_dim), {'ue_id': context.ue_id}
    
    def _result_to_decision(self, result: 'AlgorithmResult', context: HandoverContext) -> HandoverDecision:
        """將原始算法結果轉換為 HandoverDecision
        
        Args:
            result: 原始算法結果
            context: 原始上下文
            
        Returns:
            HandoverDecision: 統一決策格式
        """
        try:
            # 映射決策類型
            if result.handover_decision == 0:
                decision_type = HandoverDecisionType.NO_HANDOVER
                target_satellite = None
            elif result.handover_decision == 1:
                decision_type = HandoverDecisionType.IMMEDIATE_HANDOVER
                # 嘗試從結果中獲取目標衛星
                target_satellite = getattr(result, 'target_satellite', None)
                if not target_satellite and context.candidate_satellites:
                    # 選擇信號最強的候選衛星
                    best_satellite = max(
                        context.candidate_satellites,
                        key=lambda s: s.signal_metrics.sinr if s.signal_metrics else -float('inf')
                    )
                    target_satellite = best_satellite.satellite_id
            elif result.handover_decision == 2:
                decision_type = HandoverDecisionType.PREPARE_HANDOVER
                target_satellite = getattr(result, 'target_satellite', None)
            else:
                decision_type = HandoverDecisionType.NO_HANDOVER
                target_satellite = None
            
            # 計算信心度 (基於決策原因和算法特性)
            confidence = getattr(result, 'confidence', 0.8)
            if hasattr(result, 'decision_reason') and 'error' in result.decision_reason.lower():
                confidence = 0.1
            
            # 構建決策
            decision = HandoverDecision(
                target_satellite=target_satellite,
                handover_decision=decision_type,
                confidence=confidence,
                timing=datetime.now() if decision_type != HandoverDecisionType.NO_HANDOVER else None,
                decision_reason=getattr(result, 'decision_reason', 'Algorithm decision'),
                algorithm_name=result.algorithm_name,
                decision_time=getattr(result, 'decision_time', 0.0),
                metadata={
                    'original_decision': result.handover_decision,
                    'algorithm_type': 'traditional',
                    'adapter': self.__class__.__name__
                }
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"結果轉換失敗: {e}")
            return HandoverDecision(
                target_satellite=None,
                handover_decision=HandoverDecisionType.NO_HANDOVER,
                confidence=0.1,
                timing=None,
                decision_reason=f"Conversion error: {str(e)}",
                algorithm_name=self.name,
                decision_time=0.0,
                metadata={'error': True}
            )


class InfocomAlgorithmAdapter(BaseTraditionalAdapter):
    """IEEE INFOCOM 2024 算法適配器"""
    
    def __init__(self, name: str = "ieee_infocom_2024", config: Optional[Dict[str, Any]] = None):
        """初始化 INFOCOM 算法適配器"""
        if not BASELINE_ALGORITHMS_AVAILABLE:
            logger.warning("基準算法模組不可用，使用 fallback 實現")
            # 使用 fallback 實現而不是拋出異常
            self.name = name
            self.config = config or {}
            self._algorithm_info = None
            self.wrapped_algorithm = None
            return
        
        # 創建原始算法實例
        wrapped_algorithm = InfocomAlgorithm(config)
        super().__init__(name, wrapped_algorithm, config)
    
    async def _initialize_algorithm(self) -> None:
        """初始化算法特定邏輯"""
        # 原始算法已在構造函數中初始化
        logger.info(f"INFOCOM 算法適配器 '{self.name}' 初始化完成")
    
    async def predict_handover(self, context: HandoverContext) -> HandoverDecision:
        """執行換手預測
        
        Args:
            context: 換手上下文
            
        Returns:
            HandoverDecision: 換手決策
        """
        if not BASELINE_ALGORITHMS_AVAILABLE or self.wrapped_algorithm is None:
            # Fallback 實現：基於信號強度的簡單決策
            try:
                if context.current_satellite and context.candidate_satellites:
                    current_rsrp = context.current_satellite.signal_metrics.rsrp if context.current_satellite.signal_metrics else -120
                    best_candidate = max(context.candidate_satellites, 
                                       key=lambda s: s.signal_metrics.rsrp if s.signal_metrics else -120)
                    best_rsrp = best_candidate.signal_metrics.rsrp if best_candidate.signal_metrics else -120
                    
                    if best_rsrp > current_rsrp + 3:  # 3dB 門檻
                        return HandoverDecision(
                            target_satellite=best_candidate.satellite_id,
                            handover_decision=HandoverDecisionType.HANDOVER,
                            confidence=0.7,
                            timing=None,
                            decision_reason="Fallback: Signal strength based decision",
                            algorithm_name=self.name,
                            decision_time=0.0,
                            metadata={'fallback': True}
                        )
                
                return HandoverDecision(
                    target_satellite=None,
                    handover_decision=HandoverDecisionType.NO_HANDOVER,
                    confidence=0.7,
                    timing=None,
                    decision_reason="Fallback: No better candidate found",
                    algorithm_name=self.name,
                    decision_time=0.0,
                    metadata={'fallback': True}
                )
            except Exception as e:
                logger.error(f"Fallback算法執行失敗: {e}")
                return HandoverDecision(
                    target_satellite=None,
                    handover_decision=HandoverDecisionType.NO_HANDOVER,
                    confidence=0.1,
                    timing=None,
                    decision_reason=f"Fallback error: {str(e)}",
                    algorithm_name=self.name,
                    decision_time=0.0,
                    metadata={'error': True, 'fallback': True}
                )
        
        try:
            # 轉換輸入格式
            observation, info = self._context_to_observation(context)
            
            # 調用原始算法
            result = self.wrapped_algorithm.decide(observation, info)
            
            # 轉換輸出格式
            decision = self._result_to_decision(result, context)
            decision.algorithm_name = self.name
            
            return decision
            
        except Exception as e:
            logger.error(f"INFOCOM 算法執行失敗: {e}")
            return HandoverDecision(
                target_satellite=None,
                handover_decision=HandoverDecisionType.NO_HANDOVER,
                confidence=0.1,
                timing=None,
                decision_reason=f"Algorithm error: {str(e)}",
                algorithm_name=self.name,
                decision_time=0.0,
                metadata={'error': True, 'exception': str(e)}
            )
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取算法信息"""
        if not self._algorithm_info:
            if not BASELINE_ALGORITHMS_AVAILABLE or self.wrapped_algorithm is None:
                # Fallback 模式的算法信息
                self._algorithm_info = AlgorithmInfo(
                    name=self.name,
                    version="1.0.0-fallback",
                    algorithm_type=AlgorithmType.TRADITIONAL,
                    description="IEEE INFOCOM 2024 算法適配器 (Fallback模式) - 基於信號強度的簡單換手決策",
                    parameters=self.config,
                    author="Fallback implementation",
                    created_at=datetime.now(),
                    performance_metrics={},
                    supported_scenarios=["urban", "suburban", "rural", "highway"]
                )
            else:
                original_info = self.wrapped_algorithm.get_algorithm_info()
                
                self._algorithm_info = AlgorithmInfo(
                    name=self.name,
                    version="1.0.0-adapter",
                    algorithm_type=AlgorithmType.TRADITIONAL,
                    description="IEEE INFOCOM 2024 論文算法適配器 - 基於二分搜索的精確換手時機預測",
                    parameters=self.config,
                    author="Adapted from original implementation",
                    created_at=datetime.now(),
                    performance_metrics=original_info.get('performance_metrics'),
                    supported_scenarios=["urban", "suburban", "rural", "highway"]
                )
        
        return self._algorithm_info


class SimpleThresholdAlgorithmAdapter(BaseTraditionalAdapter):
    """簡單閾值算法適配器"""
    
    def __init__(self, name: str = "simple_threshold", config: Optional[Dict[str, Any]] = None):
        """初始化簡單閾值算法適配器"""
        if not BASELINE_ALGORITHMS_AVAILABLE:
            logger.warning("基準算法模組不可用，使用 fallback 實現")
            self.name = name
            self.config = config or {}
            self._algorithm_info = None
            self.wrapped_algorithm = None
            return
        
        wrapped_algorithm = SimpleThresholdAlgorithm(config)
        super().__init__(name, wrapped_algorithm, config)
    
    async def _initialize_algorithm(self) -> None:
        """初始化算法特定邏輯"""
        logger.info(f"簡單閾值算法適配器 '{self.name}' 初始化完成")
    
    async def predict_handover(self, context: HandoverContext) -> HandoverDecision:
        """執行換手預測"""
        if not BASELINE_ALGORITHMS_AVAILABLE or self.wrapped_algorithm is None:
            # Fallback: 簡單閾值實現
            try:
                if context.current_satellite and context.candidate_satellites:
                    current_rsrp = context.current_satellite.signal_metrics.rsrp if context.current_satellite.signal_metrics else -120
                    threshold = self.config.get('rsrp_threshold', -110)  # 默認 -110dBm
                    
                    for candidate in context.candidate_satellites:
                        candidate_rsrp = candidate.signal_metrics.rsrp if candidate.signal_metrics else -120
                        if candidate_rsrp > threshold and candidate_rsrp > current_rsrp:
                            return HandoverDecision(
                                target_satellite=candidate.satellite_id,
                                handover_decision=HandoverDecisionType.HANDOVER,
                                confidence=0.8,
                                timing=None,
                                decision_reason="Fallback: Threshold-based decision",
                                algorithm_name=self.name,
                                decision_time=0.0,
                                metadata={'fallback': True, 'threshold': threshold}
                            )
                
                return HandoverDecision(
                    target_satellite=None,
                    handover_decision=HandoverDecisionType.NO_HANDOVER,
                    confidence=0.8,
                    timing=None,
                    decision_reason="Fallback: No candidate above threshold",
                    algorithm_name=self.name,
                    decision_time=0.0,
                    metadata={'fallback': True}
                )
            except Exception as e:
                logger.error(f"Fallback閾值算法執行失敗: {e}")
                return HandoverDecision(
                    target_satellite=None,
                    handover_decision=HandoverDecisionType.NO_HANDOVER,
                    confidence=0.1,
                    timing=None,
                    decision_reason=f"Fallback error: {str(e)}",
                    algorithm_name=self.name,
                    decision_time=0.0,
                    metadata={'error': True, 'fallback': True}
                )
        
        try:
            observation, info = self._context_to_observation(context)
            result = self.wrapped_algorithm.decide(observation, info)
            decision = self._result_to_decision(result, context)
            decision.algorithm_name = self.name
            return decision
            
        except Exception as e:
            logger.error(f"簡單閾值算法執行失敗: {e}")
            return HandoverDecision(
                target_satellite=None,
                handover_decision=HandoverDecisionType.NO_HANDOVER,
                confidence=0.1,
                timing=None,
                decision_reason=f"Algorithm error: {str(e)}",
                algorithm_name=self.name,
                decision_time=0.0,
                metadata={'error': True, 'exception': str(e)}
            )
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取算法信息"""
        if not self._algorithm_info:
            self._algorithm_info = AlgorithmInfo(
                name=self.name,
                version="1.0.0-adapter",
                algorithm_type=AlgorithmType.HEURISTIC,
                description="基於簡單信號強度閾值的換手算法適配器",
                parameters=self.config,
                author="Adapted from original implementation",
                created_at=datetime.now(),
                supported_scenarios=["basic", "testing"]
            )
        
        return self._algorithm_info


class RandomAlgorithmAdapter(BaseTraditionalAdapter):
    """隨機算法適配器"""
    
    def __init__(self, name: str = "random", config: Optional[Dict[str, Any]] = None):
        """初始化隨機算法適配器"""
        if not BASELINE_ALGORITHMS_AVAILABLE:
            logger.warning("基準算法模組不可用，使用 fallback 實現")
            self.name = name
            self.config = config or {}
            self._algorithm_info = None
            self.wrapped_algorithm = None
            return
        
        wrapped_algorithm = RandomAlgorithm(config)
        super().__init__(name, wrapped_algorithm, config)
    
    async def _initialize_algorithm(self) -> None:
        """初始化算法特定邏輯"""
        logger.info(f"隨機算法適配器 '{self.name}' 初始化完成")
    
    async def predict_handover(self, context: HandoverContext) -> HandoverDecision:
        """執行換手預測"""
        if not BASELINE_ALGORITHMS_AVAILABLE or self.wrapped_algorithm is None:
            # Fallback: 隨機決策實現
            import random
            try:
                handover_probability = self.config.get('handover_probability', 0.3)  # 30% 機率換手
                
                if context.candidate_satellites and random.random() < handover_probability:
                    # 隨機選擇一個候選衛星
                    target = random.choice(context.candidate_satellites)
                    return HandoverDecision(
                        target_satellite=target.satellite_id,
                        handover_decision=HandoverDecisionType.HANDOVER,
                        confidence=0.5,
                        timing=None,
                        decision_reason="Fallback: Random decision",
                        algorithm_name=self.name,
                        decision_time=0.0,
                        metadata={'fallback': True, 'probability': handover_probability}
                    )
                else:
                    return HandoverDecision(
                        target_satellite=None,
                        handover_decision=HandoverDecisionType.NO_HANDOVER,
                        confidence=0.5,
                        timing=None,
                        decision_reason="Fallback: Random no-handover",
                        algorithm_name=self.name,
                        decision_time=0.0,
                        metadata={'fallback': True}
                    )
            except Exception as e:
                logger.error(f"Fallback隨機算法執行失敗: {e}")
                return HandoverDecision(
                    target_satellite=None,
                    handover_decision=HandoverDecisionType.NO_HANDOVER,
                    confidence=0.1,
                    timing=None,
                    decision_reason=f"Fallback error: {str(e)}",
                    algorithm_name=self.name,
                    decision_time=0.0,
                    metadata={'error': True, 'fallback': True}
                )
        
        try:
            observation, info = self._context_to_observation(context)
            result = self.wrapped_algorithm.decide(observation, info)
            decision = self._result_to_decision(result, context)
            decision.algorithm_name = self.name
            return decision
            
        except Exception as e:
            logger.error(f"隨機算法執行失敗: {e}")
            return HandoverDecision(
                target_satellite=None,
                handover_decision=HandoverDecisionType.NO_HANDOVER,
                confidence=0.1,
                timing=None,
                decision_reason=f"Algorithm error: {str(e)}",
                algorithm_name=self.name,
                decision_time=0.0,
                metadata={'error': True, 'exception': str(e)}
            )
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取算法信息"""
        if not self._algorithm_info:
            self._algorithm_info = AlgorithmInfo(
                name=self.name,
                version="1.0.0-adapter",
                algorithm_type=AlgorithmType.HEURISTIC,
                description="隨機換手決策算法適配器 - 用於基準比較",
                parameters=self.config,
                author="Adapted from original implementation",
                created_at=datetime.now(),
                supported_scenarios=["testing", "baseline"]
            )
        
        return self._algorithm_info