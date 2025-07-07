"""
數據轉換模組 - 從 environment_manager.py 中提取的數據轉換邏輯
包含所有相關轉換函數，重點解決方法過長問題
"""

from typing import Dict, Any, Union
from datetime import datetime
import numpy as np
import logging

try:
    import gymnasium.spaces as spaces
except ImportError:
    spaces = None

from ..interfaces import (
    HandoverContext,
    HandoverDecision,
    HandoverDecisionType,
    GeoCoordinate,
    SignalMetrics,
    SatelliteInfo
)

logger = logging.getLogger(__name__)


class EnvironmentDataConverter:
    """環境數據轉換器 - 處理觀測和決策之間的轉換"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def obs_to_context(self, obs: np.ndarray, info: Dict[str, Any]) -> HandoverContext:
        """將環境觀察轉換為 HandoverContext
        
        Args:
            obs: 環境觀察
            info: 環境信息
            
        Returns:
            HandoverContext: 換手上下文
        """
        try:
            # 解析觀察向量 (基於 LEOSatelliteHandoverEnv 的觀察空間)
            # 觀察向量格式: [ue_features(4), current_satellite_features(6), candidate_satellites_features(6*max_satellites), network_features(4)]
            
            ue_features = obs[:4]  # UE 位置和速度
            current_sat_features = obs[4:10]  # 當前衛星特徵
            
            # 解析 UE 信息
            ue_location = self._parse_ue_location(ue_features)
            ue_velocity = self._parse_ue_velocity(ue_features)
            
            # 解析當前衛星信息
            current_satellite, current_signal_metrics = self._parse_current_satellite(current_sat_features)
            
            # 解析候選衛星信息
            candidate_satellites = self._parse_candidate_satellites(obs)
            
            # 構建網路狀態
            network_state = self._parse_network_state(obs)
            
            # 創建 HandoverContext
            context = HandoverContext(
                user_id=info.get('ue_id', 'ue_001'),
                current_satellite_id=current_satellite,
                user_location=ue_location,
                user_velocity=ue_velocity,
                signal_metrics=current_signal_metrics,
                candidate_satellites=candidate_satellites,
                network_state=network_state,
                timestamp=datetime.now(),
                scenario_info=info.get('scenario_info'),
                weather_conditions=info.get('weather_conditions'),
                traffic_load=info.get('traffic_load')
            )
            
            return context
            
        except Exception as e:
            logger.error(f"觀察轉換失敗: {e}")
            # 返回最小化的上下文
            return self._create_fallback_context(info)
    
    def decision_to_action(self, decision: HandoverDecision, action_space) -> Union[int, np.ndarray]:
        """將 HandoverDecision 轉換為環境動作
        
        Args:
            decision: 換手決策
            action_space: 動作空間
            
        Returns:
            環境動作
        """
        try:
            if action_space and hasattr(action_space, '__class__'):
                if spaces and isinstance(action_space, spaces.Discrete):
                    return self._convert_to_discrete_action(decision, action_space)
                elif spaces and isinstance(action_space, spaces.Box):
                    return self._convert_to_continuous_action(decision, action_space)
                else:
                    # 其他動作空間類型
                    return decision.handover_decision.value
            else:
                # 沒有定義動作空間，返回決策值
                return decision.handover_decision.value
                
        except Exception as e:
            logger.error(f"決策轉換失敗: {e}")
            return 0  # 默認無換手動作
    
    # === 私有輔助方法 ===
    
    def _parse_ue_location(self, ue_features: np.ndarray) -> GeoCoordinate:
        """解析 UE 位置"""
        return GeoCoordinate(
            latitude=float(ue_features[0]),
            longitude=float(ue_features[1]),
            altitude=0.0
        )
    
    def _parse_ue_velocity(self, ue_features: np.ndarray) -> GeoCoordinate:
        """解析 UE 速度"""
        return GeoCoordinate(
            latitude=float(ue_features[2]),
            longitude=float(ue_features[3]),
            altitude=0.0
        )
    
    def _parse_current_satellite(self, current_sat_features: np.ndarray) -> tuple:
        """解析當前衛星信息"""
        current_satellite = None
        current_signal_metrics = None
        
        if current_sat_features[0] > 0:  # 有當前衛星
            current_satellite = f"sat_{int(current_sat_features[0])}"
            current_signal_metrics = SignalMetrics(
                rsrp=float(current_sat_features[1]),
                rsrq=float(current_sat_features[2]),
                sinr=float(current_sat_features[3]),
                throughput=float(current_sat_features[4]),
                latency=float(current_sat_features[5])
            )
        
        return current_satellite, current_signal_metrics
    
    def _parse_candidate_satellites(self, obs: np.ndarray) -> list:
        """解析候選衛星信息"""
        candidate_satellites = []
        max_satellites = self.config.get('max_satellites', 10)
        
        for i in range(max_satellites):
            start_idx = 10 + i * 6
            sat_features = obs[start_idx:start_idx + 6]
            
            if sat_features[0] > 0:  # 衛星存在
                satellite_info = SatelliteInfo(
                    satellite_id=f"sat_{int(sat_features[0])}",
                    position=GeoCoordinate(
                        latitude=float(sat_features[1]),
                        longitude=float(sat_features[2]),
                        altitude=600000.0  # LEO 軌道高度
                    ),
                    signal_metrics=SignalMetrics(
                        rsrp=float(sat_features[3]),
                        rsrq=float(sat_features[4]),
                        sinr=float(sat_features[5]),
                        throughput=0.0,
                        latency=0.0
                    )
                )
                candidate_satellites.append(satellite_info)
        
        return candidate_satellites
    
    def _parse_network_state(self, obs: np.ndarray) -> Dict[str, Any]:
        """解析網路狀態"""
        max_satellites = self.config.get('max_satellites', 10)
        network_start_idx = 10 + max_satellites * 6
        network_features = obs[network_start_idx:network_start_idx + 4]
        
        return {
            'total_ues': int(network_features[0]),
            'active_satellites': int(network_features[1]),
            'network_load': float(network_features[2]),
            'interference_level': float(network_features[3])
        }
    
    def _create_fallback_context(self, info: Dict[str, Any]) -> HandoverContext:
        """創建回退上下文"""
        return HandoverContext(
            user_id=info.get('ue_id', 'ue_001'),
            current_satellite_id=None,
            user_location=GeoCoordinate(latitude=0.0, longitude=0.0),
            user_velocity=None,
            signal_metrics=None,
            candidate_satellites=[],
            network_state={},
            timestamp=datetime.now()
        )
    
    def _convert_to_discrete_action(self, decision: HandoverDecision, action_space) -> int:
        """轉換為離散動作"""
        if decision.handover_decision == HandoverDecisionType.NO_HANDOVER:
            return 0
        elif decision.handover_decision == HandoverDecisionType.IMMEDIATE_HANDOVER:
            # 如果有目標衛星，返回對應的動作索引
            if decision.target_satellite_id:
                try:
                    sat_id = int(decision.target_satellite_id.split('_')[-1])
                    return min(sat_id, action_space.n - 1)
                except (ValueError, IndexError):
                    return 1  # 默認換手動作
            return 1
        elif decision.handover_decision == HandoverDecisionType.PREPARE_HANDOVER:
            return 2
        else:
            return 0
    
    def _convert_to_continuous_action(self, decision: HandoverDecision, action_space) -> np.ndarray:
        """轉換為連續動作"""
        action = np.zeros(action_space.shape)
        action[0] = float(decision.handover_decision.value)
        
        if decision.target_satellite_id:
            try:
                sat_id = int(decision.target_satellite_id.split('_')[-1])
                action[1] = min(float(sat_id), action_space.high[1])
            except (ValueError, IndexError):
                action[1] = 0.0
        
        action[2] = decision.confidence
        return action


# === 獨立轉換函數（向後兼容） ===

def convert_obs_to_context(obs: np.ndarray, info: Dict[str, Any], config: Dict[str, Any]) -> HandoverContext:
    """將觀察轉換為上下文的獨立函數"""
    converter = EnvironmentDataConverter(config)
    return converter.obs_to_context(obs, info)


def convert_decision_to_action(decision: HandoverDecision, action_space, config: Dict[str, Any]) -> Union[int, np.ndarray]:
    """將決策轉換為動作的獨立函數"""
    converter = EnvironmentDataConverter(config)
    return converter.decision_to_action(decision, action_space)