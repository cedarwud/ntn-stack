#!/usr/bin/env python3
"""
3GPP 事件分析器 - NTN 標準事件評估

遷移自現有的 IntelligentSatelliteSelector，整合到新的模組化架構中
依據: 3GPP TS 38.331 NTN 事件定義和觸發條件
"""

import logging
import math
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# 導入信號計算模組
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from signal_calculation.rsrp_calculator import RSRPCalculator
    RSRP_CALCULATOR_AVAILABLE = True
except ImportError:
    RSRP_CALCULATOR_AVAILABLE = False
    logging.warning("RSRP 計算器不可用，將使用簡化估算")

logger = logging.getLogger(__name__)


class GPPEventAnalyzer:
    """3GPP NTN 事件分析器
    
    支援 A4、A5、D2 等標準事件的潛力評估
    """
    
    def __init__(self, rsrp_calculator: Optional[RSRPCalculator] = None):
        """
        初始化 3GPP 事件分析器
        
        Args:
            rsrp_calculator: RSRP 信號計算器實例
        """
        self.rsrp_calculator = rsrp_calculator
        
        # 3GPP NTN 事件觸發條件 - 基於完整軌道週期優化
        self.event_thresholds = {
            'A4': {
                'rsrp_dbm': -95,           # 鄰近小區變優觸發門檻
                'hysteresis_db': 3,        # 遲滯
                'time_to_trigger_ms': 640  # 觸發時間
            },
            'A5': {
                'thresh1_dbm': -100,       # 服務小區門檻1 (劣化)
                'thresh2_dbm': -95,        # 鄰近小區門檻2 (變優)
                'hysteresis_db': 3,        # 遲滯
                'time_to_trigger_ms': 480  # 觸發時間
            },
            'D2': {
                'low_elev_deg': 10,        # 低仰角觸發門檻 (擴展範圍)
                'high_elev_deg': 30,       # 高仰角觸發門檻
                'hysteresis_deg': 2,       # 仰角遲滯
                'time_to_trigger_ms': 320  # 觸發時間
            }
        }
        
        logger.info("🎯 3GPP 事件分析器初始化完成")
        logger.info(f"📊 事件門檻: A4={self.event_thresholds['A4']['rsrp_dbm']}dBm, "
                   f"A5={self.event_thresholds['A5']['thresh2_dbm']}dBm, "
                   f"D2={self.event_thresholds['D2']['low_elev_deg']}-{self.event_thresholds['D2']['high_elev_deg']}°")
    
    def analyze_event_potential(self, satellite: Dict[str, Any]) -> Dict[str, float]:
        """
        分析衛星的事件觸發潛力
        
        Args:
            satellite: 衛星數據 (包含軌道參數和時間序列)
            
        Returns:
            各種事件的觸發潛力評分 (0-1)
        """
        # 獲取信號強度估算
        estimated_rsrp = self._estimate_satellite_rsrp(satellite)
        
        # 獲取仰角範圍
        elevation_range = self._estimate_elevation_range(satellite)
        
        event_scores = {}
        
        # A4 事件潛力 (鄰近小區變優)
        event_scores['A4'] = self._evaluate_a4_potential(estimated_rsrp)
        
        # A5 事件潛力 (服務小區變差且鄰近變優)
        event_scores['A5'] = self._evaluate_a5_potential(estimated_rsrp)
        
        # D2 事件潛力 (仰角觸發)
        event_scores['D2'] = self._evaluate_d2_potential(elevation_range)
        
        # 計算綜合事件分數
        event_scores['composite'] = (
            event_scores['A4'] * 0.4 +
            event_scores['A5'] * 0.4 +
            event_scores['D2'] * 0.2
        )
        
        logger.debug(f"事件潛力分析: {satellite.get('satellite_id', 'Unknown')} - "
                    f"A4={event_scores['A4']:.2f}, A5={event_scores['A5']:.2f}, "
                    f"D2={event_scores['D2']:.2f}, 綜合={event_scores['composite']:.2f}")
        
        return event_scores
    
    def _estimate_satellite_rsrp(self, satellite: Dict[str, Any]) -> float:
        """估算衛星的 RSRP 信號強度"""
        if self.rsrp_calculator and RSRP_CALCULATOR_AVAILABLE:
            # 使用真實的 RSRP 計算器
            return self.rsrp_calculator.calculate_rsrp(satellite)
        else:
            # 使用簡化估算作為後備
            orbit_data = satellite.get('orbit_data', {})
            altitude = orbit_data.get('altitude', 550.0)
            
            # 基於高度的簡化 RSRP 估算
            if altitude <= 600:
                base_rsrp = -85.0  # Starlink 典型值
            elif altitude <= 1300:
                base_rsrp = -90.0  # OneWeb 典型值
            else:
                base_rsrp = -95.0  # 其他高度
            
            # 添加高度相關的修正
            height_correction = (altitude - 550) * 0.01
            estimated_rsrp = base_rsrp - height_correction
            
            return estimated_rsrp
    
    def _estimate_elevation_range(self, satellite: Dict[str, Any]) -> Dict[str, float]:
        """估算衛星的仰角範圍"""
        orbit_data = satellite.get('orbit_data', {})
        inclination = orbit_data.get('inclination', 53.0)
        altitude = orbit_data.get('altitude', 550.0)
        
        # 基於軌道力學的仰角範圍估算
        observer_lat = 24.9441667  # NTPU 緯度
        
        if abs(observer_lat) <= inclination:
            max_elevation = 90.0
        else:
            max_elevation = 90.0 - abs(abs(observer_lat) - inclination)
        
        # 考慮地平線限制
        earth_radius = 6371.0  # km
        horizon_angle = math.degrees(math.acos(earth_radius / (earth_radius + altitude)))
        min_elevation = max(0.0, 90.0 - horizon_angle)
        
        return {
            'min': min_elevation,
            'max': min(90.0, max_elevation),
            'mean': (min_elevation + max_elevation) / 2
        }
    
    def _evaluate_a4_potential(self, rsrp_dbm: float) -> float:
        """
        評估 A4 事件潛力 (鄰近小區變優)
        
        A4 事件在鄰近小區信號強度超過門檻時觸發
        """
        threshold = self.event_thresholds['A4']['rsrp_dbm']
        hysteresis = self.event_thresholds['A4']['hysteresis_db']
        
        if rsrp_dbm > threshold + hysteresis:
            # 信號明顯高於門檻，高觸發潛力
            score = min(1.0, (rsrp_dbm - threshold) / 10.0)
        elif rsrp_dbm > threshold:
            # 信號接近門檻，中等觸發潛力
            score = 0.5 + (rsrp_dbm - threshold) / (2 * hysteresis)
        else:
            # 信號低於門檻，低觸發潛力
            score = max(0.0, (rsrp_dbm - threshold + 10) / 20.0)
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_a5_potential(self, rsrp_dbm: float) -> float:
        """
        評估 A5 事件潛力 (服務小區變差且鄰近變優)
        
        A5 事件在服務小區劣化且鄰近小區變優時觸發
        """
        thresh1 = self.event_thresholds['A5']['thresh1_dbm']
        thresh2 = self.event_thresholds['A5']['thresh2_dbm']
        
        if rsrp_dbm > thresh2:
            # 鄰近小區信號強度好，高觸發潛力
            score = min(1.0, (rsrp_dbm - thresh2) / 15.0)
        elif rsrp_dbm > thresh1:
            # 信號在中等範圍，中等觸發潛力
            score = 0.3 + (rsrp_dbm - thresh1) / (2 * (thresh2 - thresh1))
        else:
            # 信號太弱，低觸發潛力
            score = max(0.0, (rsrp_dbm - thresh1 + 15) / 30.0)
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_d2_potential(self, elevation_range: Dict[str, float]) -> float:
        """
        評估 D2 事件潛力 (仰角觸發)
        
        D2 事件基於衛星仰角變化觸發
        """
        min_elev = elevation_range['min']
        max_elev = elevation_range['max']
        low_threshold = self.event_thresholds['D2']['low_elev_deg']
        high_threshold = self.event_thresholds['D2']['high_elev_deg']
        
        # 檢查仰角範圍是否跨越觸發區間
        if (max_elev >= low_threshold and min_elev <= high_threshold):
            # 仰角範圍覆蓋觸發區間，高觸發潛力
            overlap_range = min(max_elev, high_threshold) - max(min_elev, low_threshold)
            total_trigger_range = high_threshold - low_threshold
            score = min(1.0, overlap_range / total_trigger_range)
        elif max_elev < low_threshold:
            # 仰角太低，基於接近程度給分
            score = max(0.0, (max_elev - 5) / (low_threshold - 5))
        elif min_elev > high_threshold:
            # 仰角太高，基於距離給分
            score = max(0.0, (60 - min_elev) / (60 - high_threshold))
        else:
            # 其他情況，中等潛力
            score = 0.5
        
        return min(1.0, max(0.0, score))
    
    def analyze_batch_events(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量分析多顆衛星的事件潛力
        
        Args:
            satellites: 衛星列表
            
        Returns:
            批量事件分析結果
        """
        if not satellites:
            return {'error': 'no_satellites_provided'}
        
        event_results = []
        event_statistics = {
            'A4': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0},
            'A5': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0},
            'D2': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0}
        }
        
        for satellite in satellites:
            event_scores = self.analyze_event_potential(satellite)
            
            # 增強衛星數據
            enhanced_satellite = satellite.copy()
            enhanced_satellite['event_potential'] = event_scores
            enhanced_satellite['event_composite_score'] = event_scores['composite']
            event_results.append(enhanced_satellite)
            
            # 更新統計
            for event_type in ['A4', 'A5', 'D2']:
                score = event_scores[event_type]
                if score >= 0.7:
                    event_statistics[event_type]['high_potential'] += 1
                elif score >= 0.4:
                    event_statistics[event_type]['medium_potential'] += 1
                else:
                    event_statistics[event_type]['low_potential'] += 1
        
        # 按綜合事件分數排序
        event_results.sort(key=lambda x: x['event_composite_score'], reverse=True)
        
        return {
            'total_satellites': len(satellites),
            'satellites_with_events': event_results,
            'event_statistics': event_statistics,
            'top_event_satellites': event_results[:5],
            'analysis_config': {
                'thresholds': self.event_thresholds,
                'rsrp_calculator_available': self.rsrp_calculator is not None
            }
        }
    
    def get_event_capable_satellites(self, satellites: List[Dict[str, Any]], 
                                   min_composite_score: float = 0.6) -> List[Dict[str, Any]]:
        """
        獲取具有事件觸發能力的衛星
        
        Args:
            satellites: 衛星列表
            min_composite_score: 最小綜合事件分數
            
        Returns:
            具有事件能力的衛星列表
        """
        analysis_result = self.analyze_batch_events(satellites)
        
        event_capable = [
            sat for sat in analysis_result['satellites_with_events']
            if sat['event_composite_score'] >= min_composite_score
        ]
        
        logger.info(f"🎯 事件能力篩選: {len(event_capable)}/{len(satellites)} 顆衛星 "
                   f"(綜合分數 ≥ {min_composite_score})")
        
        return event_capable


def create_gpp_event_analyzer(rsrp_calculator: Optional[RSRPCalculator] = None) -> GPPEventAnalyzer:
    """創建 3GPP 事件分析器實例"""
    return GPPEventAnalyzer(rsrp_calculator)


if __name__ == "__main__":
    import math
    
    # 測試 3GPP 事件分析器
    analyzer = create_gpp_event_analyzer()
    
    # 測試衛星數據
    test_satellites = [
        {
            "satellite_id": "STARLINK-1007",
            "orbit_data": {
                "altitude": 550,
                "inclination": 53,
                "position": {"x": 1234, "y": 5678, "z": 9012}
            }
        },
        {
            "satellite_id": "ONEWEB-0123",
            "orbit_data": {
                "altitude": 1200,
                "inclination": 87,
                "position": {"x": 2345, "y": 6789, "z": 123}
            }
        }
    ]
    
    # 批量事件分析
    results = analyzer.analyze_batch_events(test_satellites)
    
    print("📊 3GPP 事件分析結果:")
    print(f"總衛星數: {results['total_satellites']}")
    print(f"高潛力事件衛星: {len(results['top_event_satellites'])}")
    
    for event_type, stats in results['event_statistics'].items():
        total = stats['high_potential'] + stats['medium_potential'] + stats['low_potential']
        if total > 0:
            print(f"{event_type} 事件: 高{stats['high_potential']} 中{stats['medium_potential']} 低{stats['low_potential']}")
    
    print(f"\n✅ 3GPP 事件分析器測試完成")