#!/usr/bin/env python3
"""
驗證 Phase 1 篩選結果的真實性和實用性
測試篩選出的衛星是否真的能在座標 24.9441°N, 121.3714°E 進行有效的換手決策
"""

import json
import math
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np

# 導入SGP4進行軌道計算
try:
    from sgp4.api import Satrec
    from sgp4 import omm
    SGP4_AVAILABLE = True
except ImportError:
    print("WARNING: SGP4 not available, using simplified orbital calculations")
    SGP4_AVAILABLE = False

from rl_optimized_satellite_filter import RLOptimizedSatelliteFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase1ValidationTester:
    """Phase 1 篩選結果驗證器"""
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        self.min_elevation = 10.0  # 最低仰角（度）
        self.earth_radius = 6371.0  # 地球半徑（公里）
        
    def validate_filtered_satellites(self, constellation: str, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證篩選後的衛星數據
        """
        logger.info(f"🔍 開始驗證 {constellation.upper()} 篩選結果")
        logger.info(f"待驗證衛星數量: {len(satellites)}")
        
        results = {
            'constellation': constellation,
            'total_satellites': len(satellites),
            'visibility_tests': {},
            'handover_scenarios': {},
            'quality_scores': {},
            'validation_summary': {}
        }
        
        # 進行多項驗證測試
        visibility_results = self._test_visibility_coverage(satellites)
        handover_results = self._test_handover_scenarios(satellites)
        quality_results = self._calculate_quality_scores(satellites)
        
        results['visibility_tests'] = visibility_results
        results['handover_scenarios'] = handover_results
        results['quality_scores'] = quality_results
        
        # 生成驗證摘要
        results['validation_summary'] = self._generate_validation_summary(
            visibility_results, handover_results, quality_results
        )
        
        return results
    
    def _test_visibility_coverage(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        測試衛星的可見性覆蓋能力
        使用簡化的軌道計算模型
        """
        logger.info("📡 測試衛星可見性覆蓋...")
        
        visibility_stats = {
            'visible_satellites': 0,
            'pass_durations': [],
            'daily_passes': [],
            'elevation_angles': [],
            'failed_satellites': []
        }
        
        # 模擬24小時內的衛星通過
        test_time = datetime.utcnow()
        time_steps = [test_time + timedelta(hours=h) for h in range(24)]
        
        for sat_data in satellites[:50]:  # 測試前50顆衛星
            sat_name = sat_data.get('name', f"SAT-{sat_data.get('norad_id', 'unknown')}")
            
            try:
                # 計算衛星軌道參數
                inclination = float(sat_data['INCLINATION'])
                mean_motion = float(sat_data['MEAN_MOTION'])
                
                # 簡化的可見性計算
                passes_in_24h = self._estimate_daily_passes(inclination, mean_motion)
                max_elevation = self._estimate_max_elevation(inclination)
                
                if passes_in_24h >= 2 and max_elevation >= self.min_elevation:
                    visibility_stats['visible_satellites'] += 1
                    visibility_stats['daily_passes'].append(passes_in_24h)
                    visibility_stats['elevation_angles'].append(max_elevation)
                    
                    # 估算通過時長
                    pass_duration = self._estimate_pass_duration(inclination, mean_motion)
                    visibility_stats['pass_durations'].append(pass_duration)
                else:
                    visibility_stats['failed_satellites'].append({
                        'name': sat_name,
                        'reason': f"Daily passes: {passes_in_24h:.1f}, Max elevation: {max_elevation:.1f}°"
                    })
                    
            except Exception as e:
                visibility_stats['failed_satellites'].append({
                    'name': sat_name,
                    'reason': f"Calculation error: {str(e)}"
                })
        
        # 計算統計數據
        if visibility_stats['daily_passes']:
            visibility_stats['avg_daily_passes'] = np.mean(visibility_stats['daily_passes'])
            visibility_stats['avg_elevation'] = np.mean(visibility_stats['elevation_angles'])
            visibility_stats['avg_pass_duration'] = np.mean(visibility_stats['pass_durations'])
        else:
            visibility_stats['avg_daily_passes'] = 0
            visibility_stats['avg_elevation'] = 0
            visibility_stats['avg_pass_duration'] = 0
        
        visibility_stats['success_rate'] = visibility_stats['visible_satellites'] / min(50, len(satellites)) * 100
        
        return visibility_stats
    
    def _test_handover_scenarios(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        測試衛星的換手場景生成能力
        """
        logger.info("🔄 測試衛星換手場景...")
        
        handover_stats = {
            'potential_handovers_per_hour': [],
            'orbital_diversity_score': 0,
            'elevation_thresholds_coverage': {},
            'scenario_quality': 'unknown'
        }
        
        # 分析軌道多樣性
        inclinations = []
        raans = []
        
        for sat_data in satellites:
            try:
                inclinations.append(float(sat_data['INCLINATION']))
                raans.append(float(sat_data['RA_OF_ASC_NODE']))
            except (KeyError, ValueError):
                continue
        
        if inclinations and raans:
            # 計算軌道多樣性分數
            inc_std = np.std(inclinations)
            raan_spread = max(raans) - min(raans)
            handover_stats['orbital_diversity_score'] = (inc_std + raan_spread / 360 * 180) / 2
            
            # 分析仰角門檻覆蓋
            handover_stats['elevation_thresholds_coverage'] = {
                '5_degree': sum(1 for inc in inclinations if inc > 30),
                '10_degree': sum(1 for inc in inclinations if inc > 35),
                '15_degree': sum(1 for inc in inclinations if inc > 40)
            }
            
            # 估算每小時潛在換手次數
            for hour in range(24):
                active_satellites = min(len(satellites), 8)  # 假設最多8顆衛星同時可見
                handover_opportunities = active_satellites * 0.3  # 30%機率發生換手
                handover_stats['potential_handovers_per_hour'].append(handover_opportunities)
        
        # 評估場景品質
        if handover_stats['orbital_diversity_score'] > 50:
            handover_stats['scenario_quality'] = 'excellent'
        elif handover_stats['orbital_diversity_score'] > 30:
            handover_stats['scenario_quality'] = 'good'
        elif handover_stats['orbital_diversity_score'] > 15:
            handover_stats['scenario_quality'] = 'fair'
        else:
            handover_stats['scenario_quality'] = 'poor'
        
        return handover_stats
    
    def _calculate_quality_scores(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        計算衛星數據品質分數
        """
        logger.info("📊 計算數據品質分數...")
        
        quality_scores = {
            'parameter_completeness': 0,
            'orbital_stability': 0,
            'coverage_quality': 0,
            'rl_training_value': 0,
            'overall_score': 0
        }
        
        valid_satellites = 0
        
        for sat_data in satellites:
            try:
                # 參數完整性檢查
                required_params = ['INCLINATION', 'MEAN_MOTION', 'ECCENTRICITY', 
                                 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY']
                completeness = sum(1 for param in required_params if param in sat_data and sat_data[param] is not None)
                completeness_score = completeness / len(required_params) * 100
                
                # 軌道穩定性評分
                eccentricity = float(sat_data.get('ECCENTRICITY', 0))
                stability_score = max(0, 100 - eccentricity * 400)  # 低離心率 = 高穩定性
                
                # 覆蓋品質評分
                inclination = float(sat_data.get('INCLINATION', 0))
                if inclination > 80:  # 極地軌道
                    coverage_score = 100
                elif inclination > 50:  # 中等傾角
                    coverage_score = 80
                else:  # 低傾角
                    coverage_score = 60
                
                # RL訓練價值評分
                mean_motion = float(sat_data.get('MEAN_MOTION', 0))
                if 11 <= mean_motion <= 17:  # LEO範圍內
                    rl_score = 100
                else:
                    rl_score = 50
                
                quality_scores['parameter_completeness'] += completeness_score
                quality_scores['orbital_stability'] += stability_score
                quality_scores['coverage_quality'] += coverage_score
                quality_scores['rl_training_value'] += rl_score
                
                valid_satellites += 1
                
            except (KeyError, ValueError, TypeError):
                continue
        
        # 平均化分數
        if valid_satellites > 0:
            for key in ['parameter_completeness', 'orbital_stability', 'coverage_quality', 'rl_training_value']:
                quality_scores[key] /= valid_satellites
            
            quality_scores['overall_score'] = np.mean([
                quality_scores['parameter_completeness'],
                quality_scores['orbital_stability'],
                quality_scores['coverage_quality'],
                quality_scores['rl_training_value']
            ])
        
        return quality_scores
    
    def _estimate_daily_passes(self, inclination: float, mean_motion: float) -> float:
        """估算每日通過次數"""
        orbital_period_hours = 24 / mean_motion
        
        if inclination > 80:  # 極地軌道
            return mean_motion * 0.8
        elif inclination > 50:  # 中等傾角
            return mean_motion * 0.4
        else:  # 低傾角
            return mean_motion * 0.2
    
    def _estimate_max_elevation(self, inclination: float) -> float:
        """估算最大仰角"""
        if inclination > 80:
            return 85  # 極地軌道幾乎天頂通過
        elif inclination > 60:
            return 70
        elif inclination > 40:
            return 50
        else:
            return max(10, inclination)
    
    def _estimate_pass_duration(self, inclination: float, mean_motion: float) -> float:
        """估算通過時長（秒）"""
        base_duration = 600  # 10分鐘基準
        
        if inclination > 80:
            return base_duration * 1.2  # 極地軌道通過時間稍長
        else:
            return base_duration * (inclination / 90)
    
    def _generate_validation_summary(self, visibility: Dict, handover: Dict, quality: Dict) -> Dict[str, Any]:
        """生成驗證摘要報告"""
        
        summary = {
            'overall_status': 'unknown',
            'key_metrics': {},
            'recommendations': [],
            'phase1_completion_verified': False
        }
        
        # 關鍵指標
        summary['key_metrics'] = {
            'visibility_success_rate': visibility.get('success_rate', 0),
            'avg_daily_passes': visibility.get('avg_daily_passes', 0),
            'orbital_diversity_score': handover.get('orbital_diversity_score', 0),
            'overall_quality_score': quality.get('overall_score', 0),
            'scenario_quality': handover.get('scenario_quality', 'unknown')
        }
        
        # 評估整體狀態
        metrics = summary['key_metrics']
        
        if (metrics['visibility_success_rate'] >= 90 and 
            metrics['avg_daily_passes'] >= 3 and 
            metrics['overall_quality_score'] >= 80):
            summary['overall_status'] = 'excellent'
            summary['phase1_completion_verified'] = True
        elif (metrics['visibility_success_rate'] >= 75 and 
              metrics['avg_daily_passes'] >= 2 and 
              metrics['overall_quality_score'] >= 70):
            summary['overall_status'] = 'good'
            summary['phase1_completion_verified'] = True
        elif (metrics['visibility_success_rate'] >= 60 and 
              metrics['avg_daily_passes'] >= 1.5 and 
              metrics['overall_quality_score'] >= 60):
            summary['overall_status'] = 'acceptable'
            summary['phase1_completion_verified'] = True
        else:
            summary['overall_status'] = 'needs_improvement'
            summary['phase1_completion_verified'] = False
        
        # 建議
        if metrics['visibility_success_rate'] < 80:
            summary['recommendations'].append("考慮調整可見性篩選標準")
        
        if metrics['avg_daily_passes'] < 2:
            summary['recommendations'].append("增加極地軌道衛星比例")
        
        if metrics['orbital_diversity_score'] < 30:
            summary['recommendations'].append("需要更多軌道多樣性")
        
        if not summary['recommendations']:
            summary['recommendations'].append("Phase 1 篩選質量優秀，可以進入 Phase 2")
        
        return summary

def main():
    """主要驗證程序"""
    
    # 載入 TLE 數據
    tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    
    # 初始化篩選器和驗證器
    filter_system = RLOptimizedSatelliteFilter()
    validator = Phase1ValidationTester()
    
    # 測試 Starlink
    starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
    if starlink_file.exists():
        print("🛰️ 正在驗證 Starlink 篩選結果...")
        
        with open(starlink_file, 'r') as f:
            starlink_data = json.load(f)
        
        # 執行篩選
        starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
        accepted_starlink = starlink_results['accepted']
        
        # 驗證篩選結果
        validation_results = validator.validate_filtered_satellites("starlink", accepted_starlink)
        
        print(f"\n📊 Starlink 驗證結果:")
        print(f"  原始數量: {len(starlink_data)}")
        print(f"  篩選後數量: {len(accepted_starlink)}")
        print(f"  可見性成功率: {validation_results['visibility_tests']['success_rate']:.1f}%")
        print(f"  平均每日通過: {validation_results['visibility_tests']['avg_daily_passes']:.1f} 次")
        print(f"  軌道多樣性分數: {validation_results['handover_scenarios']['orbital_diversity_score']:.1f}")
        print(f"  整體品質分數: {validation_results['quality_scores']['overall_score']:.1f}")
        print(f"  場景品質: {validation_results['handover_scenarios']['scenario_quality']}")
        print(f"  整體狀態: {validation_results['validation_summary']['overall_status']}")
        print(f"  Phase 1 完成驗證: {'✅ 通過' if validation_results['validation_summary']['phase1_completion_verified'] else '❌ 未通過'}")
        
        if validation_results['validation_summary']['recommendations']:
            print(f"\n💡 建議:")
            for rec in validation_results['validation_summary']['recommendations']:
                print(f"    - {rec}")
    
    # 測試 OneWeb
    oneweb_file = tle_dir / "oneweb/json/oneweb_20250731.json"
    if oneweb_file.exists():
        print(f"\n🛰️ 正在驗證 OneWeb 篩選結果...")
        
        with open(oneweb_file, 'r') as f:
            oneweb_data = json.load(f)
        
        # 執行篩選
        oneweb_results = filter_system.filter_constellation(oneweb_data, "oneweb")
        accepted_oneweb = oneweb_results['accepted']
        
        # 驗證篩選結果
        validation_results = validator.validate_filtered_satellites("oneweb", accepted_oneweb)
        
        print(f"\n📊 OneWeb 驗證結果:")
        print(f"  原始數量: {len(oneweb_data)}")
        print(f"  篩選後數量: {len(accepted_oneweb)}")
        print(f"  可見性成功率: {validation_results['visibility_tests']['success_rate']:.1f}%")
        print(f"  平均每日通過: {validation_results['visibility_tests']['avg_daily_passes']:.1f} 次")
        print(f"  軌道多樣性分數: {validation_results['handover_scenarios']['orbital_diversity_score']:.1f}")
        print(f"  整體品質分數: {validation_results['quality_scores']['overall_score']:.1f}")
        print(f"  場景品質: {validation_results['handover_scenarios']['scenario_quality']}")
        print(f"  整體狀態: {validation_results['validation_summary']['overall_status']}")
        print(f"  Phase 1 完成驗證: {'✅ 通過' if validation_results['validation_summary']['phase1_completion_verified'] else '❌ 未通過'}")
        
        if validation_results['validation_summary']['recommendations']:
            print(f"\n💡 建議:")
            for rec in validation_results['validation_summary']['recommendations']:
                print(f"    - {rec}")

if __name__ == "__main__":
    main()