#!/usr/bin/env python3
"""
Phase 1 最終驗證報告
驗證零容忍篩選是否已100%完成並符合所有預期標準
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from rl_optimized_satellite_filter import RLOptimizedSatelliteFilter

class Phase1FinalValidator:
    """Phase 1 最終驗證器"""
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        
        # Phase 1 預期標準
        self.expected_results = {
            'starlink': {
                'original_count': 8044,
                'expected_filtered': 1707,
                'expected_rate': 21.2
            },
            'oneweb': {
                'original_count': 651,
                'expected_filtered': 651,
                'expected_rate': 100.0
            },
            'total': {
                'original_count': 8695,
                'expected_filtered': 2358,
                'expected_rate': 27.1
            }
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        執行全面的 Phase 1 驗證
        """
        print("🔍 執行 Phase 1 全面驗證...")
        print(f"📍 目標座標: {self.target_lat:.4f}°N, {self.target_lon:.4f}°E")
        
        validation_results = {
            'phase1_status': 'unknown',
            'implementation_check': {},
            'numerical_validation': {},
            'quality_assessment': {},
            'handover_readiness': {},
            'completion_verification': {},
            'final_score': 0
        }
        
        # 1. 實施檢查
        implementation_check = self._check_implementation()
        validation_results['implementation_check'] = implementation_check
        
        # 2. 數值驗證
        numerical_validation = self._validate_numerical_results()
        validation_results['numerical_validation'] = numerical_validation
        
        # 3. 品質評估
        quality_assessment = self._assess_filtering_quality()
        validation_results['quality_assessment'] = quality_assessment
        
        # 4. 換手準備度評估
        handover_readiness = self._assess_handover_readiness()
        validation_results['handover_readiness'] = handover_readiness
        
        # 5. 完成度驗證
        completion_verification = self._verify_completion_status(
            implementation_check, numerical_validation, quality_assessment, handover_readiness
        )
        validation_results['completion_verification'] = completion_verification
        
        # 6. 計算最終分數
        final_score = self._calculate_final_score(validation_results)
        validation_results['final_score'] = final_score
        
        # 7. 確定 Phase 1 狀態
        if final_score >= 90:
            validation_results['phase1_status'] = 'fully_completed'
        elif final_score >= 80:
            validation_results['phase1_status'] = 'mostly_completed'
        elif final_score >= 70:
            validation_results['phase1_status'] = 'partially_completed'
        else:
            validation_results['phase1_status'] = 'incomplete'
        
        return validation_results
    
    def _check_implementation(self) -> Dict[str, Any]:
        """
        檢查實施狀況
        """
        print("📋 檢查實施狀況...")
        
        implementation_check = {
            'filter_code_exists': False,
            'design_doc_exists': False,
            'validation_scripts_exist': False,
            'implementation_score': 0
        }
        
        # 檢查核心篩選代碼
        filter_file = Path("/home/sat/ntn-stack/simworld/backend/rl_optimized_satellite_filter.py")
        implementation_check['filter_code_exists'] = filter_file.exists()
        
        # 檢查設計文檔
        design_doc = Path("/home/sat/ntn-stack/satellite-filtering-pipeline/01-zero-tolerance-filter.md")
        implementation_check['design_doc_exists'] = design_doc.exists()
        
        # 檢查驗證腳本
        validation_scripts = [
            Path("/home/sat/ntn-stack/simworld/backend/validate_phase1_results.py"),
            Path("/home/sat/ntn-stack/simworld/backend/phase1_final_validation.py")
        ]
        implementation_check['validation_scripts_exist'] = all(script.exists() for script in validation_scripts)
        
        # 計算實施分數
        implementation_score = 0
        if implementation_check['filter_code_exists']:
            implementation_score += 60
        if implementation_check['design_doc_exists']:
            implementation_score += 20
        if implementation_check['validation_scripts_exist']:
            implementation_score += 20
        
        implementation_check['implementation_score'] = implementation_score
        
        return implementation_check
    
    def _validate_numerical_results(self) -> Dict[str, Any]:
        """
        驗證數值結果
        """
        print("🔢 驗證數值結果...")
        
        numerical_validation = {
            'starlink_validation': {},
            'oneweb_validation': {},
            'total_validation': {},
            'numerical_accuracy_score': 0
        }
        
        try:
            # 載入 TLE 數據
            tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
            filter_system = RLOptimizedSatelliteFilter()
            
            # 驗證 Starlink
            starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
            if starlink_file.exists():
                with open(starlink_file, 'r') as f:
                    starlink_data = json.load(f)
                
                starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
                
                starlink_validation = {
                    'original_count': len(starlink_data),
                    'filtered_count': len(starlink_results['accepted']),
                    'acceptance_rate': len(starlink_results['accepted']) / len(starlink_data) * 100,
                    'expected_count': self.expected_results['starlink']['expected_filtered'],
                    'count_match': abs(len(starlink_results['accepted']) - self.expected_results['starlink']['expected_filtered']) <= 5,
                    'rate_match': abs(len(starlink_results['accepted']) / len(starlink_data) * 100 - self.expected_results['starlink']['expected_rate']) <= 1.0
                }
                
                numerical_validation['starlink_validation'] = starlink_validation
            
            # 驗證 OneWeb
            oneweb_file = tle_dir / "oneweb/json/oneweb_20250731.json"
            if oneweb_file.exists():
                with open(oneweb_file, 'r') as f:
                    oneweb_data = json.load(f)
                
                oneweb_results = filter_system.filter_constellation(oneweb_data, "oneweb")
                
                oneweb_validation = {
                    'original_count': len(oneweb_data),
                    'filtered_count': len(oneweb_results['accepted']),
                    'acceptance_rate': len(oneweb_results['accepted']) / len(oneweb_data) * 100,
                    'expected_count': self.expected_results['oneweb']['expected_filtered'],
                    'count_match': len(oneweb_results['accepted']) == self.expected_results['oneweb']['expected_filtered'],
                    'rate_match': abs(len(oneweb_results['accepted']) / len(oneweb_data) * 100 - self.expected_results['oneweb']['expected_rate']) <= 0.1
                }
                
                numerical_validation['oneweb_validation'] = oneweb_validation
            
            # 計算總體驗證
            total_filtered = (numerical_validation['starlink_validation']['filtered_count'] + 
                            numerical_validation['oneweb_validation']['filtered_count'])
            total_original = (numerical_validation['starlink_validation']['original_count'] + 
                            numerical_validation['oneweb_validation']['original_count'])
            
            total_validation = {
                'total_filtered': total_filtered,
                'total_original': total_original,
                'total_rate': total_filtered / total_original * 100,
                'expected_total': self.expected_results['total']['expected_filtered'],
                'total_match': abs(total_filtered - self.expected_results['total']['expected_filtered']) <= 10
            }
            
            numerical_validation['total_validation'] = total_validation
            
            # 計算數值準確性分數
            accuracy_score = 0
            if numerical_validation['starlink_validation']['count_match']:
                accuracy_score += 30
            if numerical_validation['starlink_validation']['rate_match']:
                accuracy_score += 20
            if numerical_validation['oneweb_validation']['count_match']:
                accuracy_score += 30
            if numerical_validation['oneweb_validation']['rate_match']:
                accuracy_score += 20
            
            numerical_validation['numerical_accuracy_score'] = accuracy_score
            
        except Exception as e:
            numerical_validation['error'] = str(e)
            numerical_validation['numerical_accuracy_score'] = 0
        
        return numerical_validation
    
    def _assess_filtering_quality(self) -> Dict[str, Any]:
        """
        評估篩選品質
        """
        print("🎯 評估篩選品質...")
        
        quality_assessment = {
            'parameter_completeness': 0,
            'physics_compliance': 0,
            'coverage_effectiveness': 0,
            'rl_suitability': 0,
            'overall_quality_score': 0
        }
        
        try:
            # 載入篩選後的數據進行品質分析
            tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
            filter_system = RLOptimizedSatelliteFilter()
            
            starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
            if starlink_file.exists():
                with open(starlink_file, 'r') as f:
                    starlink_data = json.load(f)
                
                starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
                accepted_starlink = starlink_results['accepted']
                
                # 分析前100顆衛星的品質
                sample_satellites = accepted_starlink[:100]
                
                # 參數完整性檢查
                complete_params = 0
                for sat in sample_satellites:
                    required_params = ['INCLINATION', 'MEAN_MOTION', 'ECCENTRICITY', 
                                     'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY']
                    if all(param in sat and sat[param] is not None for param in required_params):
                        complete_params += 1
                
                quality_assessment['parameter_completeness'] = complete_params / len(sample_satellites) * 100
                
                # 物理合規性檢查
                physics_compliant = 0
                for sat in sample_satellites:
                    try:
                        inclination = float(sat['INCLINATION'])
                        mean_motion = float(sat['MEAN_MOTION'])
                        eccentricity = float(sat['ECCENTRICITY'])
                        
                        if (25.0 <= inclination <= 180.0 and 
                            11.0 <= mean_motion <= 17.0 and 
                            0.0 <= eccentricity <= 0.25):
                            physics_compliant += 1
                    except:
                        continue
                
                quality_assessment['physics_compliance'] = physics_compliant / len(sample_satellites) * 100
                
                # 覆蓋有效性評估
                coverage_effective = 0
                for sat in sample_satellites:
                    try:
                        inclination = float(sat['INCLINATION'])
                        if inclination >= abs(self.target_lat):  # 能覆蓋目標緯度
                            coverage_effective += 1
                    except:
                        continue
                
                quality_assessment['coverage_effectiveness'] = coverage_effective / len(sample_satellites) * 100
                
                # RL適用性評估
                rl_suitable = 0
                for sat in sample_satellites:
                    try:
                        inclination = float(sat['INCLINATION'])
                        mean_motion = float(sat['MEAN_MOTION'])
                        
                        # 估算每日通過次數
                        if inclination > 80:
                            daily_passes = mean_motion * 0.8
                        elif inclination > 50:
                            daily_passes = mean_motion * 0.4
                        else:
                            daily_passes = mean_motion * 0.2
                        
                        if 2 <= daily_passes <= 15:
                            rl_suitable += 1
                    except:
                        continue
                
                quality_assessment['rl_suitability'] = rl_suitable / len(sample_satellites) * 100
                
                # 計算整體品質分數
                quality_assessment['overall_quality_score'] = np.mean([
                    quality_assessment['parameter_completeness'],
                    quality_assessment['physics_compliance'],
                    quality_assessment['coverage_effectiveness'],
                    quality_assessment['rl_suitability']
                ])
        
        except Exception as e:
            quality_assessment['error'] = str(e)
        
        return quality_assessment
    
    def _assess_handover_readiness(self) -> Dict[str, Any]:
        """
        評估換手準備度
        """
        print("🔄 評估換手準備度...")
        
        handover_readiness = {
            'satellite_diversity': 0,
            'elevation_coverage': 0,
            'temporal_distribution': 0,
            'scenario_potential': 0,
            'handover_readiness_score': 0
        }
        
        try:
            # 載入篩選後的數據
            tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
            filter_system = RLOptimizedSatelliteFilter()
            
            starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
            if starlink_file.exists():
                with open(starlink_file, 'r') as f:
                    starlink_data = json.load(f)
                
                starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
                accepted_starlink = starlink_results['accepted']
                
                # 衛星多樣性分析
                inclinations = []
                raans = []
                for sat in accepted_starlink:
                    try:
                        inclinations.append(float(sat['INCLINATION']))
                        raans.append(float(sat['RA_OF_ASC_NODE']))
                    except:
                        continue
                
                if inclinations and raans:
                    inc_diversity = np.std(inclinations)
                    raan_spread = max(raans) - min(raans)
                    handover_readiness['satellite_diversity'] = min(100, (inc_diversity + raan_spread / 360 * 180) / 2)
                
                # 仰角覆蓋評估
                high_elevation_count = sum(1 for inc in inclinations if inc > 70)
                medium_elevation_count = sum(1 for inc in inclinations if 45 <= inc <= 70)
                handover_readiness['elevation_coverage'] = (high_elevation_count + medium_elevation_count * 0.7) / len(inclinations) * 100
                
                # 時間分布評估
                orbital_periods = []
                for sat in accepted_starlink:
                    try:
                        mean_motion = float(sat['MEAN_MOTION'])
                        period = 24.0 / mean_motion
                        orbital_periods.append(period)
                    except:
                        continue
                
                if orbital_periods:
                    period_diversity = np.std(orbital_periods)
                    handover_readiness['temporal_distribution'] = min(100, period_diversity * 50)
                
                # 場景潛力評估
                polar_orbits = sum(1 for inc in inclinations if inc > 80)
                medium_inclination = sum(1 for inc in inclinations if 45 <= inc <= 80)
                scenario_score = (polar_orbits * 1.2 + medium_inclination * 0.8) / len(inclinations) * 100
                handover_readiness['scenario_potential'] = min(100, scenario_score)
                
                # 計算整體換手準備度分數
                handover_readiness['handover_readiness_score'] = np.mean([
                    handover_readiness['satellite_diversity'],
                    handover_readiness['elevation_coverage'],
                    handover_readiness['temporal_distribution'],
                    handover_readiness['scenario_potential']
                ])
        
        except Exception as e:
            handover_readiness['error'] = str(e)
        
        return handover_readiness
    
    def _verify_completion_status(self, implementation: Dict, numerical: Dict, 
                                 quality: Dict, handover: Dict) -> Dict[str, Any]:
        """
        驗證完成狀態
        """
        print("✅ 驗證完成狀態...")
        
        completion_criteria = {
            'implementation_complete': implementation['implementation_score'] >= 80,
            'numerical_accurate': numerical['numerical_accuracy_score'] >= 80,
            'quality_sufficient': quality['overall_quality_score'] >= 70,
            'handover_ready': handover['handover_readiness_score'] >= 60,
            'phase1_requirements_met': False
        }
        
        # 檢查所有關鍵標準
        all_criteria_met = all([
            completion_criteria['implementation_complete'],
            completion_criteria['numerical_accurate'],
            completion_criteria['quality_sufficient'],
            completion_criteria['handover_ready']
        ])
        
        completion_criteria['phase1_requirements_met'] = all_criteria_met
        
        return completion_criteria
    
    def _calculate_final_score(self, validation_results: Dict) -> float:
        """
        計算最終分數
        """
        implementation_score = validation_results['implementation_check']['implementation_score']
        numerical_score = validation_results['numerical_validation']['numerical_accuracy_score']
        quality_score = validation_results['quality_assessment']['overall_quality_score']
        handover_score = validation_results['handover_readiness']['handover_readiness_score']
        
        # 加權平均
        final_score = (
            implementation_score * 0.25 +
            numerical_score * 0.35 +
            quality_score * 0.25 +
            handover_score * 0.15
        )
        
        return final_score

def main():
    """主要驗證程序"""
    
    print("🚀 Phase 1 零容忍篩選系統 - 最終驗證")
    print("=" * 60)
    
    validator = Phase1FinalValidator()
    results = validator.run_comprehensive_validation()
    
    print(f"\n📊 最終驗證結果:")
    print(f"{'='*60}")
    
    # 實施檢查結果
    impl = results['implementation_check']
    print(f"\n🔧 實施檢查 (分數: {impl['implementation_score']}/100):")
    print(f"  ✅ 核心篩選代碼: {'存在' if impl['filter_code_exists'] else '缺失'}")
    print(f"  ✅ 設計文檔: {'存在' if impl['design_doc_exists'] else '缺失'}")
    print(f"  ✅ 驗證腳本: {'存在' if impl['validation_scripts_exist'] else '缺失'}")
    
    # 數值驗證結果
    numerical = results['numerical_validation']
    if 'starlink_validation' in numerical:
        starlink = numerical['starlink_validation']
        print(f"\n🔢 數值驗證 (分數: {numerical['numerical_accuracy_score']}/100):")
        print(f"  📡 Starlink: {starlink['original_count']} → {starlink['filtered_count']} 顆 ({starlink['acceptance_rate']:.1f}%)")
        print(f"    ✅ 數量匹配: {'是' if starlink['count_match'] else '否'}")
        print(f"    ✅ 比率匹配: {'是' if starlink['rate_match'] else '否'}")
        
        if 'oneweb_validation' in numerical:
            oneweb = numerical['oneweb_validation']
            print(f"  📡 OneWeb: {oneweb['original_count']} → {oneweb['filtered_count']} 顆 ({oneweb['acceptance_rate']:.1f}%)")
            print(f"    ✅ 數量匹配: {'是' if oneweb['count_match'] else '否'}")
            print(f"    ✅ 比率匹配: {'是' if oneweb['rate_match'] else '否'}")
            
            total = numerical['total_validation']
            print(f"  📊 總計: {total['total_original']} → {total['total_filtered']} 顆 ({total['total_rate']:.1f}%)")
    
    # 品質評估結果
    quality = results['quality_assessment']
    print(f"\n🎯 品質評估 (分數: {quality['overall_quality_score']:.1f}/100):")
    print(f"  📋 參數完整性: {quality['parameter_completeness']:.1f}%")
    print(f"  ⚛️  物理合規性: {quality['physics_compliance']:.1f}%")
    print(f"  📡 覆蓋有效性: {quality['coverage_effectiveness']:.1f}%")
    print(f"  🤖 RL適用性: {quality['rl_suitability']:.1f}%")
    
    # 換手準備度結果
    handover = results['handover_readiness']
    print(f"\n🔄 換手準備度 (分數: {handover['handover_readiness_score']:.1f}/100):")
    print(f"  🌐 衛星多樣性: {handover['satellite_diversity']:.1f}")
    print(f"  📐 仰角覆蓋: {handover['elevation_coverage']:.1f}")
    print(f"  ⏰ 時間分布: {handover['temporal_distribution']:.1f}")
    print(f"  🎭 場景潛力: {handover['scenario_potential']:.1f}")
    
    # 完成狀態驗證
    completion = results['completion_verification']
    print(f"\n✅ 完成狀態驗證:")
    print(f"  🔧 實施完成: {'✅' if completion['implementation_complete'] else '❌'}")
    print(f"  🔢 數值準確: {'✅' if completion['numerical_accurate'] else '❌'}")
    print(f"  🎯 品質充足: {'✅' if completion['quality_sufficient'] else '❌'}")
    print(f"  🔄 換手就緒: {'✅' if completion['handover_ready'] else '❌'}")
    print(f"  📋 Phase 1 要求: {'✅ 完全滿足' if completion['phase1_requirements_met'] else '❌ 部分滿足'}")
    
    # 最終結論
    print(f"\n🏆 最終評估:")
    print(f"{'='*60}")
    print(f"  🎯 最終分數: {results['final_score']:.1f}/100")
    print(f"  📊 Phase 1 狀態: {results['phase1_status']}")
    
    status_messages = {
        'fully_completed': '🎉 Phase 1 已完全完成，可以進入 Phase 2',
        'mostly_completed': '✅ Phase 1 基本完成，建議小幅優化後進入 Phase 2',
        'partially_completed': '⚠️ Phase 1 部分完成，需要解決關鍵問題',
        'incomplete': '❌ Phase 1 未完成，需要重新實施'
    }
    
    print(f"  💬 結論: {status_messages.get(results['phase1_status'], '未知狀態')}")

if __name__ == "__main__":
    main()