#!/usr/bin/env python3
"""
分層仰角門檻換手決策引擎
基於 ITU-R P.618 標準的實務換手策略實現
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class HandoverPhase(Enum):
    """換手階段定義"""
    MONITORING = "monitoring"      # 監控階段 (>15°)
    PRE_HANDOVER = "pre_handover"  # 預備觸發 (5°-15°)
    EXECUTION = "execution"        # 執行門檻 (10°-12°)
    CRITICAL = "critical"          # 臨界狀態 (5°-10°)
    DISCONNECTED = "disconnected"  # 已斷開 (<5°)

@dataclass
class LayeredThreshold:
    """分層門檻配置"""
    pre_handover_elevation: float = 15.0    # 預備觸發仰角
    execution_elevation: float = 10.0       # 執行門檻仰角
    critical_elevation: float = 5.0         # 臨界仰角
    environment_factor: float = 1.0         # 環境調整係數
    
    def get_adjusted_thresholds(self, environment: str = "open") -> Dict[str, float]:
        """根據環境調整門檻"""
        adjustments = {
            "open": 1.0,        # 開闊地區
            "urban": 1.1,       # 城市環境
            "mountain": 1.3,    # 山區
            "rain_heavy": 1.5   # 強降雨區
        }
        
        factor = adjustments.get(environment, 1.0)
        
        return {
            "pre_handover": self.pre_handover_elevation * factor,
            "execution": self.execution_elevation * factor,
            "critical": self.critical_elevation,  # 臨界門檻不調整
            "environment": environment,
            "adjustment_factor": factor
        }

class LayeredElevationEngine:
    """分層仰角換手決策引擎"""
    
    def __init__(self, threshold_config: LayeredThreshold = None, 
                 environment: str = "open"):
        """
        初始化分層仰角引擎
        
        Args:
            threshold_config: 門檻配置
            environment: 環境類型 (open/urban/mountain/rain_heavy)
        """
        self.config = threshold_config or LayeredThreshold()
        self.environment = environment
        self.thresholds = self.config.get_adjusted_thresholds(environment)
        
        # 換手狀態記錄
        self.handover_states = {}
        self.preparation_started = {}
        
        logger.info(f"LayeredElevationEngine 初始化 - 環境: {environment}")
        logger.info(f"  預備觸發: {self.thresholds['pre_handover']:.1f}°")
        logger.info(f"  執行門檻: {self.thresholds['execution']:.1f}°")
        logger.info(f"  臨界門檻: {self.thresholds['critical']:.1f}°")
    
    def analyze_satellite_phase(self, satellite_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析衛星當前所處的換手階段
        
        Args:
            satellite_info: 包含 elevation/elevation_deg, azimuth, range_km 等信息
            
        Returns:
            Dict: 換手階段分析結果
        """
        # 統一處理仰角字段 - 支援 elevation_deg 和 elevation
        elevation = satellite_info.get('elevation_deg') or satellite_info.get('elevation', 0.0)
        satellite_id = satellite_info.get('satellite_id', 'unknown')
        
        # 判斷當前階段
        if elevation >= self.thresholds['pre_handover']:
            phase = HandoverPhase.MONITORING
            urgency = "low"
            action_required = "continue_monitoring"
            
        elif elevation >= self.thresholds['execution']:
            phase = HandoverPhase.PRE_HANDOVER
            urgency = "medium" 
            action_required = "prepare_handover"
            
        elif elevation >= self.thresholds['critical']:
            phase = HandoverPhase.EXECUTION
            urgency = "high"
            action_required = "execute_handover"
            
        elif elevation > 0:
            phase = HandoverPhase.CRITICAL
            urgency = "critical"
            action_required = "emergency_handover"
            
        else:
            phase = HandoverPhase.DISCONNECTED
            urgency = "none"
            action_required = "connection_lost"
        
        # 計算剩餘時間估算
        time_to_critical = self._estimate_time_to_threshold(
            satellite_info, self.thresholds['critical']
        )
        
        time_to_execution = self._estimate_time_to_threshold(
            satellite_info, self.thresholds['execution']
        )
        
        # ITU-R P.618 衰減風險評估
        attenuation_risk = self._assess_attenuation_risk(elevation)
        
        return {
            'satellite_id': satellite_id,
            'current_elevation': elevation,
            'handover_phase': phase.value,
            'urgency_level': urgency,
            'action_required': action_required,
            'time_estimates': {
                'to_critical': time_to_critical,
                'to_execution': time_to_execution
            },
            'signal_quality': {
                'attenuation_risk': attenuation_risk,
                'itu_compliance': elevation >= 10.0,
                'recommended_action': self._get_signal_recommendation(elevation)
            },
            'thresholds_used': self.thresholds.copy(),
            'environment': self.environment
        }
    
    def _estimate_time_to_threshold(self, satellite_info: Dict[str, Any], 
                                   threshold: float) -> Optional[float]:
        """估算到達指定閾值的時間（秒）"""
        try:
            current_elevation = satellite_info.get('elevation', 0.0)
            
            if current_elevation <= threshold:
                return 0.0
            
            # 簡化的線性下降估算（實際應用中需要軌道動力學計算）
            # LEO 衛星典型的仰角變化率約 0.5-2.0 度/分鐘
            typical_rate = 1.0  # 度/分鐘
            
            elevation_diff = current_elevation - threshold
            estimated_minutes = elevation_diff / typical_rate
            
            return estimated_minutes * 60  # 轉換為秒
            
        except Exception as e:
            logger.warning(f"時間估算失敗: {e}")
            return None
    
    def _assess_attenuation_risk(self, elevation: float) -> str:
        """
        基於 ITU-R P.618 評估大氣衰減風險
        """
        if elevation >= 15:
            return "minimal"  # 最小風險
        elif elevation >= 10:
            return "low"      # 低風險 (ITU-R 建議標準)
        elif elevation >= 5:
            return "high"     # 高風險 (多徑、閃變增加)
        else:
            return "critical" # 臨界風險
    
    def _get_signal_recommendation(self, elevation: float) -> str:
        """獲取信號品質建議"""
        if elevation >= 15:
            return "optimal_quality"
        elif elevation >= 10:
            return "good_quality_itu_compliant"
        elif elevation >= 5:
            return "degraded_quality_prepare_handover"
        else:
            return "poor_quality_immediate_action"
    
    def batch_analyze_constellation(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量分析星座中所有衛星的換手階段
        
        Args:
            satellites: 衛星列表，每個包含位置和可見性信息
            
        Returns:
            Dict: 星座換手分析結果
        """
        analysis_results = []
        phase_summary = {phase.value: 0 for phase in HandoverPhase}
        urgency_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0, "none": 0}
        
        for satellite in satellites:
            if not satellite.get('instantaneous_visibility', {}).get('is_visible', False):
                continue
                
            # 構建衛星信息
            visibility = satellite['instantaneous_visibility']
            sat_info = {
                'satellite_id': satellite.get('name', 'unknown'),
                'elevation': visibility.get('elevation', 0.0),
                'azimuth': visibility.get('azimuth', 0.0),
                'range_km': visibility.get('range_km', 0.0)
            }
            
            # 分析單顆衛星
            analysis = self.analyze_satellite_phase(sat_info)
            analysis_results.append(analysis)
            
            # 統計匯總
            phase_summary[analysis['handover_phase']] += 1
            urgency_summary[analysis['urgency_level']] += 1
        
        # 找出需要立即關注的衛星
        critical_satellites = [
            result for result in analysis_results 
            if result['urgency_level'] in ['high', 'critical']
        ]
        
        # 推薦的換手順序
        handover_priority = sorted(
            analysis_results,
            key=lambda x: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'none': 4}[x['urgency_level']],
                -x['current_elevation']  # 仰角越低優先級越高
            )
        )
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'thresholds_applied': self.thresholds,
            'total_satellites_analyzed': len(analysis_results),
            'individual_analyses': analysis_results,
            'phase_distribution': phase_summary,
            'urgency_distribution': urgency_summary,
            'critical_attention_required': critical_satellites,
            'recommended_handover_sequence': handover_priority[:10],  # 前10個優先級
            'system_recommendations': self._generate_system_recommendations(
                phase_summary, urgency_summary, critical_satellites
            )
        }
    
    def _generate_system_recommendations(self, phase_summary: Dict, 
                                       urgency_summary: Dict,
                                       critical_satellites: List) -> List[str]:
        """生成系統級建議"""
        recommendations = []
        
        if urgency_summary['critical'] > 0:
            recommendations.append(
                f"⚠️ {urgency_summary['critical']} 顆衛星處於臨界狀態，需要立即執行緊急換手"
            )
        
        if urgency_summary['high'] > 0:
            recommendations.append(
                f"🔄 {urgency_summary['high']} 顆衛星需要執行換手程序"
            )
        
        if urgency_summary['medium'] > 5:
            recommendations.append(
                f"📋 {urgency_summary['medium']} 顆衛星進入預備階段，建議提前準備換手資源"
            )
        
        if phase_summary['monitoring'] < 5:
            recommendations.append(
                "⚡ 高仰角衛星數量較少，建議增加監控覆蓋範圍或調整服務策略"
            )
        
        return recommendations

def create_layered_engine(environment: str = "open", 
                         custom_thresholds: Dict[str, float] = None) -> LayeredElevationEngine:
    """
    創建分層仰角引擎實例
    
    Args:
        environment: 環境類型
        custom_thresholds: 自定義門檻值
        
    Returns:
        LayeredElevationEngine: 配置好的引擎實例
    """
    if custom_thresholds:
        config = LayeredThreshold(
            pre_handover_elevation=custom_thresholds.get('pre_handover', 15.0),
            execution_elevation=custom_thresholds.get('execution', 10.0),
            critical_elevation=custom_thresholds.get('critical', 5.0)
        )
    else:
        config = LayeredThreshold()
    
    return LayeredElevationEngine(config, environment)

if __name__ == "__main__":
    # 示例使用
    print("🛰️ 分層仰角門檻換手決策引擎測試")
    
    # 不同環境測試
    environments = ["open", "urban", "mountain", "rain_heavy"]
    
    for env in environments:
        print(f"\n📍 環境: {env}")
        engine = create_layered_engine(env)
        
        # 測試衛星
        test_satellite = {
            'satellite_id': 'STARLINK-TEST',
            'elevation': 8.5,
            'azimuth': 45.0,
            'range_km': 1200.0
        }
        
        result = engine.analyze_satellite_phase(test_satellite)
        print(f"  階段: {result['handover_phase']}")
        print(f"  緊急度: {result['urgency_level']}")
        print(f"  行動: {result['action_required']}")
        print(f"  ITU 合規: {result['signal_quality']['itu_compliance']}")