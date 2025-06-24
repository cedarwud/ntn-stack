"""
簡單閾值算法

基於信號強度閾值的基礎切換算法，作為性能基準對比
"""

import numpy as np
from typing import Dict, Any, Optional
import logging

from .base_algorithm import BaseAlgorithm, AlgorithmResult

logger = logging.getLogger(__name__)


class SimpleThresholdAlgorithm(BaseAlgorithm):
    """
    簡單閾值切換算法
    
    基於固定閾值進行切換決策：
    - 當信號強度低於閾值時觸發切換
    - 當信號強度極低時立即切換
    - 否則維持當前連接
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化簡單閾值算法
        
        Args:
            config: 算法配置，包含：
                - handover_threshold: 切換閾值 (0-1)
                - emergency_threshold: 緊急切換閾值 (0-1)  
                - hysteresis_margin: 滯後邊際，防止乒乓效應
                - signal_weight: 信號強度權重
                - sinr_weight: SINR 權重
        """
        super().__init__("Simple_Threshold", config)
        
        # 上一次的決策狀態（用於滯後控制）
        self._last_decision = 0
        self._decision_counter = 0
    
    def _initialize_algorithm(self):
        """初始化算法參數"""
        # 設置默認閾值
        self.handover_threshold = self.config.get('handover_threshold', 0.4)
        self.emergency_threshold = self.config.get('emergency_threshold', 0.2)
        self.hysteresis_margin = self.config.get('hysteresis_margin', 0.1)
        self.signal_weight = self.config.get('signal_weight', 0.6)
        self.sinr_weight = self.config.get('sinr_weight', 0.4)
        
        # 滯後控制參數
        self.min_stable_decisions = self.config.get('min_stable_decisions', 3)
        
        logger.info(f"簡單閾值算法初始化: handover={self.handover_threshold}, "
                   f"emergency={self.emergency_threshold}, hysteresis={self.hysteresis_margin}")
    
    def make_decision(self, observation: np.ndarray, info: Dict[str, Any]) -> AlgorithmResult:
        """
        基於閾值進行切換決策
        
        Args:
            observation: 環境觀測向量
            info: 環境額外資訊
            
        Returns:
            AlgorithmResult: 決策結果
        """
        try:
            # 解析觀測向量中的信號品質資訊
            signal_metrics = self._extract_signal_metrics(observation, info)
            
            # 計算綜合信號品質
            combined_quality = self._calculate_combined_quality(signal_metrics)
            
            # 基於閾值做決策
            decision_info = self._make_threshold_decision(combined_quality, signal_metrics)
            
            # 應用滯後控制
            final_decision = self._apply_hysteresis_control(decision_info['decision'])
            
            # 計算預期性能
            performance = self._estimate_performance(final_decision, combined_quality)
            
            result = AlgorithmResult(
                handover_decision=final_decision,
                target_satellite=decision_info.get('target_satellite'),
                timing=decision_info.get('timing', 2.0),
                confidence=decision_info.get('confidence', 0.8),
                expected_latency=performance['latency'],
                expected_success_rate=performance['success_rate'],
                decision_reason=decision_info['reason']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"簡單閾值算法決策失敗: {e}")
            return AlgorithmResult(
                handover_decision=0,
                decision_reason=f"Algorithm error: {str(e)}",
                expected_latency=35.0,
                expected_success_rate=0.8,
                confidence=0.5
            )
    
    def _extract_signal_metrics(self, observation: np.ndarray, info: Dict[str, Any]) -> Dict[str, float]:
        """從觀測向量中提取信號品質指標"""
        
        signal_metrics = {
            'signal_strength': 0.5,
            'sinr': 0.5,
            'connection_status': 0.5,
            'load_factor': 0.5
        }
        
        try:
            # 假設優化版觀測向量結構 (72 維)
            if len(observation) >= 8:
                # 從第一個 UE 的狀態中提取信號指標
                signal_metrics['signal_strength'] = max(0, min(1, observation[5]))  # 信號強度
                signal_metrics['sinr'] = max(0, min(1, observation[6]))  # SINR
                signal_metrics['connection_status'] = max(0, min(1, observation[7]))  # 連接狀態
            
            # 如果有衛星負載資訊，也考慮進去
            if len(observation) >= 20:  # UE(8) + 至少2顆衛星(12)
                # 從第一顆衛星獲取負載資訊
                satellite_load = observation[13]  # 衛星負載
                signal_metrics['load_factor'] = 1.0 - max(0, min(1, satellite_load))
            
            # 從 info 中獲取額外資訊
            if 'signal_strength' in info:
                signal_metrics['signal_strength'] = info['signal_strength']
            if 'sinr' in info:
                signal_metrics['sinr'] = info['sinr']
                
        except Exception as e:
            logger.warning(f"信號指標提取失敗: {e}")
        
        return signal_metrics
    
    def _calculate_combined_quality(self, signal_metrics: Dict[str, float]) -> float:
        """計算綜合信號品質評分"""
        
        # 加權組合不同的信號指標
        combined_quality = (
            signal_metrics['signal_strength'] * self.signal_weight +
            signal_metrics['sinr'] * self.sinr_weight +
            signal_metrics['connection_status'] * 0.2 +
            signal_metrics['load_factor'] * 0.2
        )
        
        # 確保在 [0, 1] 範圍內
        return max(0.0, min(1.0, combined_quality))
    
    def _make_threshold_decision(self, combined_quality: float, signal_metrics: Dict[str, float]) -> Dict[str, Any]:
        """基於閾值做出決策"""
        
        if combined_quality <= self.emergency_threshold:
            # 緊急切換
            decision = 1
            reason = f"Emergency handover: quality={combined_quality:.3f} <= {self.emergency_threshold}"
            confidence = 0.95
            timing = 0.5  # 立即切換
            
        elif combined_quality <= self.handover_threshold:
            # 正常切換
            decision = 1
            reason = f"Normal handover: quality={combined_quality:.3f} <= {self.handover_threshold}"
            confidence = 0.8
            timing = 1.5  # 較快切換
            
        elif combined_quality <= self.handover_threshold + self.hysteresis_margin:
            # 滯後區域，準備切換
            decision = 2
            reason = f"Prepare handover: quality={combined_quality:.3f} in hysteresis zone"
            confidence = 0.6
            timing = 2.5
            
        else:
            # 維持連接
            decision = 0
            reason = f"Maintain connection: quality={combined_quality:.3f} > {self.handover_threshold + self.hysteresis_margin}"
            confidence = 0.9
            timing = 3.0
        
        # 選擇目標衛星（簡單策略：隨機選擇）
        target_satellite = None
        if decision == 1:
            # 簡單選擇：選擇編號0的衛星
            target_satellite = 0
        
        return {
            'decision': decision,
            'target_satellite': target_satellite,
            'timing': timing,
            'confidence': confidence,
            'reason': reason,
            'combined_quality': combined_quality
        }
    
    def _apply_hysteresis_control(self, new_decision: int) -> int:
        """應用滯後控制防止乒乓效應"""
        
        if new_decision == self._last_decision:
            # 決策一致，增加計數器
            self._decision_counter += 1
        else:
            # 決策改變，重置計數器
            self._decision_counter = 1
        
        # 只有當決策穩定足夠長時間才執行
        if self._decision_counter >= self.min_stable_decisions:
            self._last_decision = new_decision
            return new_decision
        else:
            # 維持上一次的決策
            return self._last_decision
    
    def _estimate_performance(self, decision: int, quality: float) -> Dict[str, float]:
        """估計決策的預期性能"""
        
        if decision == 0:
            # 維持連接
            latency = 15.0 + (1.0 - quality) * 20.0  # 品質越差延遲越高
            success_rate = 0.95 - (1.0 - quality) * 0.2
            
        elif decision == 1:
            # 執行切換
            latency = 30.0 + np.random.uniform(-5, 5)  # 切換基本延遲
            success_rate = 0.85 + quality * 0.1  # 品質越好成功率越高
            
        elif decision == 2:
            # 準備切換
            latency = 20.0 + (1.0 - quality) * 15.0
            success_rate = 0.90 + quality * 0.05
            
        else:
            latency = 25.0
            success_rate = 0.80
        
        return {
            'latency': max(10.0, min(60.0, latency)),
            'success_rate': max(0.5, min(1.0, success_rate))
        }
    
    def get_threshold_info(self) -> Dict[str, Any]:
        """獲取閾值配置資訊"""
        return {
            'handover_threshold': self.handover_threshold,
            'emergency_threshold': self.emergency_threshold,
            'hysteresis_margin': self.hysteresis_margin,
            'signal_weight': self.signal_weight,
            'sinr_weight': self.sinr_weight,
            'last_decision': self._last_decision,
            'decision_counter': self._decision_counter,
            'min_stable_decisions': self.min_stable_decisions
        }
    
    def reset_state(self):
        """重置算法內部狀態"""
        self._last_decision = 0
        self._decision_counter = 0
        logger.info("簡單閾值算法狀態已重置")