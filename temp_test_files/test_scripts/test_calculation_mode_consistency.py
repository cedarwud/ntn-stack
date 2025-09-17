#!/usr/bin/env python3
"""
🧪 Stage3 計算模式結果一致性測試
測試 standard/prediction/integration_optimized 三種模式的核心信號品質指標一致性
"""

import sys
import os
import json
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# 添加專案路徑
sys.path.append('/home/sat/ntn-stack/satellite-processing-system/src')

from stages.stage3_signal_analysis.signal_quality_calculator import SignalQualityCalculator

class CalculationModeConsistencyTester:
    def __init__(self):
        self.calculator = SignalQualityCalculator()
        self.test_results = {
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'test_timestamp': datetime.now(timezone.utc).isoformat()
            },
            'consistency_checks': [],
            'detailed_results': {}
        }

    def create_test_satellite_data(self, scenario: str = 'default') -> Dict[str, Any]:
        """創建測試用衛星數據"""
        base_data = {
            'satellite_id': f'test_satellite_{scenario}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'position': {
                'latitude': 39.9042,  # 北京座標
                'longitude': 116.4074,
                'altitude_km': 550.0  # LEO軌道高度
            },
            'orbital_elements': {
                'inclination': 97.4,
                'raan': 125.2,
                'eccentricity': 0.0014,
                'arg_perigee': 90.0,
                'mean_anomaly': 180.0,
                'mean_motion': 15.5
            },
            'ground_station': {
                'latitude': 39.9042,
                'longitude': 116.4074,
                'altitude_m': 50.0
            },
            'link_geometry': {
                'range_km': 1200.0,
                'elevation_deg': 25.0,
                'azimuth_deg': 180.0,
                'distance_m': 1200000.0  # 添加明確的距離值（米）
            },
            # 添加信號計算所需的核心參數
            'signal_parameters': {
                'frequency_ghz': 2.1,
                'tx_power_dbw': 20.0,
                'constellation': 'starlink',
                'eirp_dbm': 55.0,
                'cable_loss_db': 2.0,
                'antenna_gain_dbi': 2.15
            }
        }

        # 根據場景調整參數
        scenarios = {
            'high_elevation': {
                'link_geometry': {
                    'range_km': 800.0,
                    'elevation_deg': 45.0,
                    'azimuth_deg': 90.0,
                    'distance_m': 800000.0
                }
            },
            'low_elevation': {
                'link_geometry': {
                    'range_km': 1800.0,
                    'elevation_deg': 8.0,
                    'azimuth_deg': 270.0,
                    'distance_m': 1800000.0
                }
            },
            'optimal': {
                'link_geometry': {
                    'range_km': 600.0,
                    'elevation_deg': 90.0,  # 天頂通過
                    'azimuth_deg': 0.0,
                    'distance_m': 600000.0
                }
            }
        }

        if scenario in scenarios:
            base_data.update(scenarios[scenario])

        return base_data

    def extract_core_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """提取核心信號品質指標用於比較"""
        core_metrics = {}

        # 基本信號品質指標
        if 'rsrp_dbm' in result:
            core_metrics['rsrp_dbm'] = result['rsrp_dbm']
        if 'rsrq_db' in result:
            core_metrics['rsrq_db'] = result['rsrq_db']
        if 'sinr_db' in result:
            core_metrics['sinr_db'] = result['sinr_db']

        # 路徑損耗相關
        if 'path_loss_db' in result:
            core_metrics['path_loss_db'] = result['path_loss_db']
        if 'free_space_path_loss_db' in result:
            core_metrics['free_space_path_loss_db'] = result['free_space_path_loss_db']

        # 幾何相關
        if 'link_geometry' in result:
            geometry = result['link_geometry']
            if 'elevation_deg' in geometry:
                core_metrics['elevation_deg'] = geometry['elevation_deg']
            if 'range_km' in geometry:
                core_metrics['range_km'] = geometry['range_km']

        return core_metrics

    def check_metric_consistency(self, standard_metrics: Dict[str, float],
                               comparison_metrics: Dict[str, float],
                               tolerance_pct: float = 1.0) -> Dict[str, Any]:
        """檢查兩組指標的一致性"""
        consistency_result = {
            'is_consistent': True,
            'metric_comparisons': {},
            'inconsistent_metrics': []
        }

        for metric_name in standard_metrics:
            if metric_name not in comparison_metrics:
                consistency_result['inconsistent_metrics'].append({
                    'metric': metric_name,
                    'issue': 'missing_in_comparison'
                })
                consistency_result['is_consistent'] = False
                continue

            standard_value = standard_metrics[metric_name]
            comparison_value = comparison_metrics[metric_name]

            # 計算相對差異
            if standard_value != 0:
                relative_diff_pct = abs(comparison_value - standard_value) / abs(standard_value) * 100
            else:
                relative_diff_pct = 0 if comparison_value == 0 else 100

            is_metric_consistent = relative_diff_pct <= tolerance_pct

            consistency_result['metric_comparisons'][metric_name] = {
                'standard_value': standard_value,
                'comparison_value': comparison_value,
                'absolute_diff': abs(comparison_value - standard_value),
                'relative_diff_pct': round(relative_diff_pct, 3),
                'is_consistent': is_metric_consistent,
                'tolerance_pct': tolerance_pct
            }

            if not is_metric_consistent:
                consistency_result['inconsistent_metrics'].append({
                    'metric': metric_name,
                    'issue': 'exceeds_tolerance',
                    'relative_diff_pct': relative_diff_pct,
                    'tolerance_pct': tolerance_pct
                })
                consistency_result['is_consistent'] = False

        return consistency_result

    def test_calculation_mode_consistency(self, scenario: str = 'default') -> Dict[str, Any]:
        """測試特定場景下三種計算模式的結果一致性"""
        test_satellite_data = self.create_test_satellite_data(scenario)

        test_result = {
            'scenario': scenario,
            'test_status': 'passed',
            'mode_results': {},
            'consistency_checks': {},
            'summary': {
                'all_modes_consistent': True,
                'total_core_metrics': 0,
                'consistent_metrics': 0
            }
        }

        modes = ['standard', 'prediction', 'integration_optimized']

        # 執行各種模式的計算
        for mode in modes:
            try:
                result = self.calculator.calculate_signal_quality_parameterized(
                    test_satellite_data,
                    calculation_mode=mode
                )
                test_result['mode_results'][mode] = {
                    'success': True,
                    'result': result,
                    'core_metrics': self.extract_core_metrics(result)
                }
            except Exception as e:
                test_result['mode_results'][mode] = {
                    'success': False,
                    'error': str(e)
                }
                test_result['test_status'] = 'failed'

        # 檢查一致性 (以 standard 模式為基準)
        if 'standard' in test_result['mode_results'] and test_result['mode_results']['standard']['success']:
            standard_metrics = test_result['mode_results']['standard']['core_metrics']

            for mode in ['prediction', 'integration_optimized']:
                if mode in test_result['mode_results'] and test_result['mode_results'][mode]['success']:
                    comparison_metrics = test_result['mode_results'][mode]['core_metrics']

                    consistency_check = self.check_metric_consistency(
                        standard_metrics, comparison_metrics, tolerance_pct=2.0
                    )

                    test_result['consistency_checks'][f'standard_vs_{mode}'] = consistency_check

                    if not consistency_check['is_consistent']:
                        test_result['summary']['all_modes_consistent'] = False
                        test_result['test_status'] = 'failed'

            # 計算一致性統計
            total_metrics = len(standard_metrics)
            test_result['summary']['total_core_metrics'] = total_metrics

            consistent_count = 0
            for check_name, check_result in test_result['consistency_checks'].items():
                for metric_name, metric_comparison in check_result['metric_comparisons'].items():
                    if metric_comparison['is_consistent']:
                        consistent_count += 1

            test_result['summary']['consistent_metrics'] = consistent_count
            test_result['summary']['consistency_rate'] = (consistent_count / (total_metrics * 2)) * 100 if total_metrics > 0 else 0

        return test_result

    def run_comprehensive_consistency_tests(self) -> Dict[str, Any]:
        """執行全面的計算模式一致性測試"""
        print("🧪 開始執行 Stage3 計算模式結果一致性測試...")

        test_scenarios = ['default', 'high_elevation', 'low_elevation', 'optimal']

        for scenario in test_scenarios:
            print(f"  🔍 測試場景: {scenario}")

            scenario_result = self.test_calculation_mode_consistency(scenario)
            self.test_results['detailed_results'][scenario] = scenario_result

            self.test_results['test_summary']['total_tests'] += 1

            if scenario_result['test_status'] == 'passed':
                self.test_results['test_summary']['passed_tests'] += 1
                print(f"    ✅ 場景 {scenario} 測試通過")
                print(f"    📊 一致性率: {scenario_result['summary']['consistency_rate']:.1f}%")
            else:
                self.test_results['test_summary']['failed_tests'] += 1
                print(f"    ❌ 場景 {scenario} 測試失敗")

                # 顯示不一致的指標
                for check_name, check_result in scenario_result['consistency_checks'].items():
                    if not check_result['is_consistent']:
                        print(f"    🚨 {check_name} 不一致:")
                        for inconsistent_metric in check_result['inconsistent_metrics']:
                            print(f"      - {inconsistent_metric['metric']}: {inconsistent_metric.get('relative_diff_pct', 'N/A')}% 差異")

        # 生成總體摘要
        self.generate_test_summary()

        return self.test_results

    def generate_test_summary(self):
        """生成測試摘要"""
        summary = self.test_results['test_summary']

        print(f"\n📋 Stage3 計算模式一致性測試摘要:")
        print(f"  總測試數: {summary['total_tests']}")
        print(f"  通過測試: {summary['passed_tests']}")
        print(f"  失敗測試: {summary['failed_tests']}")
        print(f"  成功率: {(summary['passed_tests']/summary['total_tests']*100):.1f}%")

        # 分析常見問題
        all_inconsistent_metrics = []
        for scenario_name, scenario_result in self.test_results['detailed_results'].items():
            for check_name, check_result in scenario_result['consistency_checks'].items():
                for inconsistent_metric in check_result['inconsistent_metrics']:
                    all_inconsistent_metrics.append(inconsistent_metric['metric'])

        if all_inconsistent_metrics:
            from collections import Counter
            metric_issues = Counter(all_inconsistent_metrics)
            print(f"\n🔍 常見不一致指標:")
            for metric, count in metric_issues.most_common(5):
                print(f"  - {metric}: {count} 次")

    def save_test_results(self, output_path: str = "/tmp/stage3_consistency_test_results.json"):
        """保存測試結果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        print(f"📄 測試結果已保存到: {output_path}")

def main():
    """主測試函數"""
    tester = CalculationModeConsistencyTester()

    try:
        # 執行全面一致性測試
        results = tester.run_comprehensive_consistency_tests()

        # 保存結果
        tester.save_test_results()

        # 回傳測試狀態
        if results['test_summary']['failed_tests'] == 0:
            print("\n🎉 所有計算模式一致性測試均通過！")
            return 0
        else:
            print(f"\n⚠️  有 {results['test_summary']['failed_tests']} 個測試失敗，需要進一步檢查")
            return 1

    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit(main())