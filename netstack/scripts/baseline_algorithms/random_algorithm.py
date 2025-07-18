"""
隨機基準算法

完全隨機的切換決策，作為性能基準的最低參考點
"""

import numpy as np
from typing import Dict, Any, Optional
import logging

from .base_algorithm import BaseAlgorithm, AlgorithmResult

logger = logging.getLogger(__name__)


class RandomAlgorithm(BaseAlgorithm):
    """
    隨機基準算法
    
    提供完全隨機的切換決策，作為其他算法性能評估的底線基準：
    - 隨機決定是否切換
    - 隨機選擇目標衛星
    - 隨機分配切換時機
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化隨機算法
        
        Args:
            config: 算法配置，包含：
                - handover_probability: 觸發切換的機率 (0-1)
                - prepare_probability: 準備切換的機率 (0-1)
                - random_seed: 隨機種子（可選）
                - satellite_count: 可選衛星數量
        """
        super().__init__("Random_Baseline", config)
        
        # 隨機種子設置
        self.random_seed = self.config.get('random_seed', None)
        if self.random_seed is not None:
            np.random.seed(self.random_seed)
            logger.info(f"隨機算法使用固定種子: {self.random_seed}")
    
    def _initialize_algorithm(self):
        """初始化算法參數"""
        # 設置決策機率
        self.handover_probability = self.config.get('handover_probability', 0.2)
        self.prepare_probability = self.config.get('prepare_probability', 0.3)
        self.satellite_count = self.config.get('satellite_count', 10)
        
        # 性能範圍設置
        self.latency_range = self.config.get('latency_range', (15.0, 60.0))
        self.success_rate_range = self.config.get('success_rate_range', (0.6, 0.95))
        self.timing_range = self.config.get('timing_range', (0.5, 5.0))
        
        logger.info(f"隨機算法初始化: handover_p={self.handover_probability}, "
                   f"prepare_p={self.prepare_probability}, satellites={self.satellite_count}")
    
    def make_decision(self, observation: np.ndarray, info: Dict[str, Any]) -> AlgorithmResult:
        """
        隨機生成切換決策
        
        Args:
            observation: 環境觀測向量（隨機算法不使用此資訊）
            info: 環境額外資訊
            
        Returns:
            AlgorithmResult: 隨機決策結果
        """
        try:
            # 隨機決策邏輯
            decision_info = self._make_random_decision(info)
            
            # 隨機生成性能指標
            performance = self._generate_random_performance()
            
            result = AlgorithmResult(
                handover_decision=decision_info['decision'],
                target_satellite=decision_info.get('target_satellite'),
                timing=decision_info.get('timing'),
                confidence=decision_info.get('confidence'),
                expected_latency=performance['latency'],
                expected_success_rate=performance['success_rate'],
                decision_reason=decision_info['reason']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"隨機算法決策失敗: {e}")
            return AlgorithmResult(
                handover_decision=0,
                decision_reason=f"Random algorithm error: {str(e)}",
                expected_latency=40.0,
                expected_success_rate=0.7,
                confidence=0.5
            )
    
    def _make_random_decision(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """生成隨機決策"""
        
        # 生成隨機機率
        rand_value = np.random.random()
        
        if rand_value < self.handover_probability:
            # 觸發切換
            decision = 1
            reason = f"Random handover triggered (p={rand_value:.3f} < {self.handover_probability})"
            confidence = np.random.uniform(0.7, 0.95)
            timing = np.random.uniform(*self.timing_range)
            
            # 隨機選擇目標衛星
            satellite_count = info.get('active_satellite_count', self.satellite_count)
            target_satellite = np.random.randint(0, max(1, satellite_count))
            
        elif rand_value < self.handover_probability + self.prepare_probability:
            # 準備切換
            decision = 2
            reason = f"Random prepare decision (p={rand_value:.3f})"
            confidence = np.random.uniform(0.5, 0.8)
            timing = np.random.uniform(*self.timing_range)
            target_satellite = None
            
        else:
            # 維持連接
            decision = 0
            reason = f"Random maintain decision (p={rand_value:.3f})"
            confidence = np.random.uniform(0.6, 0.9)
            timing = np.random.uniform(*self.timing_range)
            target_satellite = None
        
        return {
            'decision': decision,
            'target_satellite': target_satellite,
            'timing': timing,
            'confidence': confidence,
            'reason': reason
        }
    
    def _generate_random_performance(self) -> Dict[str, float]:
        """生成隨機性能指標"""
        
        # 隨機延遲（使用正常分布偏向較高值）
        latency = np.random.normal(
            loc=(self.latency_range[0] + self.latency_range[1]) / 2,
            scale=(self.latency_range[1] - self.latency_range[0]) / 6
        )
        latency = max(self.latency_range[0], min(self.latency_range[1], latency))
        
        # 隨機成功率（使用 beta 分布偏向中等值）
        success_rate = np.random.beta(2, 2)  # 偏向中間值的分布
        success_rate = (
            self.success_rate_range[0] + 
            success_rate * (self.success_rate_range[1] - self.success_rate_range[0])
        )
        
        return {
            'latency': latency,
            'success_rate': success_rate
        }
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """獲取算法詳細資訊"""
        return {
            'name': self.name,
            'type': 'Random Baseline Algorithm',
            'description': 'Completely random handover decisions for baseline comparison',
            'config': self.config,
            'features': [
                'Random handover decisions',
                'Random target satellite selection',
                'Random timing assignment',
                'Configurable decision probabilities'
            ],
            'performance_characteristics': {
                'expected_latency_range': f"{self.latency_range[0]}-{self.latency_range[1]}ms",
                'expected_success_rate_range': f"{self.success_rate_range[0]:.1%}-{self.success_rate_range[1]:.1%}",
                'computational_complexity': 'O(1)',
                'memory_usage': 'Minimal',
                'predictability': 'None (purely random)'
            },
            'probabilities': {
                'handover_probability': self.handover_probability,
                'prepare_probability': self.prepare_probability,
                'no_handover_probability': 1.0 - self.handover_probability - self.prepare_probability
            }
        }
    
    def reset_state(self):
        """重置算法狀態"""
        # 隨機算法無內部狀態需要重置
        if self.random_seed is not None:
            np.random.seed(self.random_seed)
        logger.info("隨機算法狀態已重置")
    
    def set_deterministic_mode(self, seed: int):
        """設置確定性模式，用於可重現的訓練"""
        self.random_seed = seed
        np.random.seed(seed)
        logger.info(f"隨機算法切換至確定性模式，種子: {seed}")
    
    def get_decision_distribution(self, sample_count: int = 1000) -> Dict[str, float]:
        """
        獲取決策分布統計
        
        Args:
            sample_count: 抽樣次數
            
        Returns:
            Dict: 決策分布統計
        """
        decisions = []
        
        # 生成大量隨機決策進行統計
        for _ in range(sample_count):
            decision_info = self._make_random_decision({})
            decisions.append(decision_info['decision'])
        
        # 計算分布
        decisions = np.array(decisions)
        distribution = {
            'no_handover_rate': np.mean(decisions == 0),
            'handover_rate': np.mean(decisions == 1),
            'prepare_rate': np.mean(decisions == 2),
            'sample_count': sample_count
        }
        
        return distribution