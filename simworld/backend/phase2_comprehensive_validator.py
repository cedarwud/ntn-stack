#!/usr/bin/env python3
"""
Phase 2 軌道多樣性篩選驗證系統
全面驗證 Phase 2 篩選結果是否符合所有設計要求
"""

import json
import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime, timedelta

from integrated_phase1_phase2_filter import IntegratedSatelliteFilterSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase2ComprehensiveValidator:
    """
    Phase 2 全面驗證器
    """
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        
        # 驗證標準
        self.validation_criteria = {
            'target_satellite_count': {'min': 490, 'max': 510, 'ideal': 500},
            'raan_coverage_threshold': 85.0,  # 最低 RAAN 覆蓋度
            'min_quality_score': 60.0,        # 最低品質分數
            'avg_quality_score': 75.0,        # 平均品質分數目標
            'max_temporal_gap_minutes': 15,   # 最大時間空窗期
            'constellation_balance': {
                'starlink': {'min': 300, 'max': 400},
                'oneweb': {'min': 100, 'max': 200}
            }
        }
    
    def validate_phase2_results(self, integrated_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行 Phase 2 結果的全面驗證
        """
        logger.info("🔍 開始 Phase 2 全面驗證")
        
        validation_results = {
            'validation_timestamp': datetime.now().isoformat(),
            'target_coordinate': f"{self.target_lat:.4f}°N, {self.target_lon:.4f}°E",
            'validation_criteria': self.validation_criteria,
            'test_results': {},
            'overall_assessment': {},
            'recommendations': [],
            'phase2_status': 'unknown'
        }
        
        # 提取 Phase 2 結果
        phase2_results = integrated_results['phase2_details']
        final_satellites = phase2_results['selected_satellites']
        
        # 測試1: 衛星數量驗證
        logger.info("📊 測試1: 衛星數量驗證")
        count_validation = self._validate_satellite_count(final_satellites)
        validation_results['test_results']['satellite_count'] = count_validation
        
        # 測試2: RAAN 覆蓋度驗證
        logger.info("🌐 測試2: RAAN 覆蓋度驗證")
        raan_validation = self._validate_raan_coverage(final_satellites)
        validation_results['test_results']['raan_coverage'] = raan_validation
        
        # 測試3: 品質分數驗證
        logger.info("⭐ 測試3: 品質分數驗證")
        quality_validation = self._validate_quality_scores(final_satellites)
        validation_results['test_results']['quality_scores'] = quality_validation
        
        # 測試4: 星座分布驗證
        logger.info("📡 測試4: 星座分布驗證")
        constellation_validation = self._validate_constellation_balance(final_satellites)
        validation_results['test_results']['constellation_balance'] = constellation_validation
        
        # 測試5: 軌道多樣性驗證
        logger.info("🔄 測試5: 軌道多樣性驗證")
        diversity_validation = self._validate_orbital_diversity(final_satellites)
        validation_results['test_results']['orbital_diversity'] = diversity_validation
        
        # 測試6: 時間覆蓋驗證
        logger.info("⏰ 測試6: 時間覆蓋驗證")
        temporal_validation = self._validate_temporal_coverage(final_satellites)
        validation_results['test_results']['temporal_coverage'] = temporal_validation
        
        # 測試7: 換手場景潛力驗證
        logger.info("🔄 測試7: 換手場景潛力驗證")
        handover_validation = self._validate_handover_potential(final_satellites)
        validation_results['test_results']['handover_potential'] = handover_validation
        
        # 生成整體評估
        overall_assessment = self._generate_overall_assessment(validation_results['test_results'])
        validation_results['overall_assessment'] = overall_assessment
        
        # 生成建議
        recommendations = self._generate_recommendations(validation_results['test_results'])
        validation_results['recommendations'] = recommendations
        
        # 確定 Phase 2 狀態
        phase2_status = self._determine_phase2_status(overall_assessment)
        validation_results['phase2_status'] = phase2_status
        
        logger.info(f"✅ Phase 2 驗證完成 - 狀態: {phase2_status}")
        
        return validation_results
    
    def _validate_satellite_count(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證衛星數量是否符合要求
        """
        count = len(satellites)
        criteria = self.validation_criteria['target_satellite_count']
        
        result = {
            'actual_count': count,
            'target_range': f"{criteria['min']}-{criteria['max']}",
            'ideal_count': criteria['ideal'],
            'within_range': criteria['min'] <= count <= criteria['max'],
            'deviation_from_ideal': abs(count - criteria['ideal']),
            'score': 0
        }
        
        # 計算分數
        if result['within_range']:
            # 在範圍內，根據與理想值的接近程度評分
            max_deviation = max(criteria['ideal'] - criteria['min'], criteria['max'] - criteria['ideal'])
            score = max(70, 100 - (result['deviation_from_ideal'] / max_deviation * 30))
            result['score'] = score
        else:
            # 超出範圍，低分
            result['score'] = 30
        
        result['status'] = 'pass' if result['within_range'] else 'fail'
        
        return result
    
    def _validate_raan_coverage(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證 RAAN 覆蓋度
        """
        raan_bins = set()
        raan_values = []
        
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                raan_values.append(raan)
                bin_index = int(raan / 10)  # 10度一個bin
                raan_bins.add(bin_index)
            except (KeyError, ValueError, TypeError):
                continue
        
        total_bins = 36  # 360度 / 10度
        coverage_percent = len(raan_bins) / total_bins * 100
        threshold = self.validation_criteria['raan_coverage_threshold']
        
        result = {
            'covered_bins': len(raan_bins),
            'total_bins': total_bins,
            'coverage_percent': coverage_percent,
            'threshold': threshold,
            'meets_threshold': coverage_percent >= threshold,
            'raan_distribution': self._analyze_raan_distribution(raan_values),
            'score': min(100, coverage_percent * 1.2)  # 獎勵高覆蓋度
        }
        
        result['status'] = 'pass' if result['meets_threshold'] else 'fail'
        
        return result
    
    def _validate_quality_scores(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證品質分數
        """
        quality_scores = []
        category_scores = {
            'orbital_stability': [],
            'coverage_uniformity': [],
            'handover_frequency': [],
            'signal_quality': []
        }
        
        for sat in satellites:
            if 'quality_scores' in sat:
                scores = sat['quality_scores']
                total_score = scores.get('total_score', 0)
                quality_scores.append(total_score)
                
                for category in category_scores:
                    if category in scores:
                        category_scores[category].append(scores[category])
        
        if not quality_scores:
            return {
                'status': 'fail',
                'error': 'No quality scores found',
                'score': 0
            }
        
        avg_score = np.mean(quality_scores)
        min_score = np.min(quality_scores)
        max_score = np.max(quality_scores)
        
        criteria = self.validation_criteria
        meets_min_threshold = min_score >= criteria['min_quality_score']
        meets_avg_threshold = avg_score >= criteria['avg_quality_score']
        
        result = {
            'total_satellites_scored': len(quality_scores),
            'average_score': avg_score,
            'min_score': min_score,
            'max_score': max_score,
            'std_deviation': np.std(quality_scores),
            'min_threshold': criteria['min_quality_score'],
            'avg_threshold': criteria['avg_quality_score'],
            'meets_min_threshold': meets_min_threshold,
            'meets_avg_threshold': meets_avg_threshold,
            'category_averages': {cat: np.mean(scores) if scores else 0 
                                for cat, scores in category_scores.items()},
            'score': min(100, avg_score * 1.2)  # 基於平均分數評分
        }
        
        result['status'] = 'pass' if (meets_min_threshold and meets_avg_threshold) else 'fail'
        
        return result
    
    def _validate_constellation_balance(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證星座分布平衡
        """
        constellation_counts = {}
        
        for sat in satellites:
            constellation = sat.get('constellation', 'unknown')
            constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1
        
        criteria = self.validation_criteria['constellation_balance']
        result = {
            'constellation_counts': constellation_counts,
            'balance_analysis': {},
            'overall_balance_score': 0,
            'meets_requirements': True
        }
        
        balance_scores = []
        
        for constellation, count in constellation_counts.items():
            if constellation in criteria:
                req = criteria[constellation]
                within_range = req['min'] <= count <= req['max']
                
                # 計算平衡分數
                if within_range:
                    ideal = (req['min'] + req['max']) / 2
                    deviation = abs(count - ideal)
                    max_deviation = max(ideal - req['min'], req['max'] - ideal)
                    balance_score = max(70, 100 - (deviation / max_deviation * 30))
                else:
                    balance_score = 30
                    result['meets_requirements'] = False
                
                result['balance_analysis'][constellation] = {
                    'count': count,
                    'required_range': f"{req['min']}-{req['max']}",
                    'within_range': within_range,
                    'balance_score': balance_score
                }
                
                balance_scores.append(balance_score)
        
        result['overall_balance_score'] = np.mean(balance_scores) if balance_scores else 0
        result['score'] = result['overall_balance_score']
        result['status'] = 'pass' if result['meets_requirements'] else 'fail'
        
        return result
    
    def _validate_orbital_diversity(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證軌道多樣性
        """
        orbital_params = {
            'inclinations': [],
            'eccentricities': [],
            'mean_motions': [],
            'raans': [],
            'arg_perigees': []
        }
        
        for sat in satellites:
            try:
                orbital_params['inclinations'].append(float(sat['INCLINATION']))
                orbital_params['eccentricities'].append(float(sat['ECCENTRICITY']))
                orbital_params['mean_motions'].append(float(sat['MEAN_MOTION']))
                orbital_params['raans'].append(float(sat['RA_OF_ASC_NODE']))
                orbital_params['arg_perigees'].append(float(sat['ARG_OF_PERICENTER']))
            except (KeyError, ValueError, TypeError):
                continue
        
        diversity_metrics = {}
        overall_diversity_score = 0
        
        for param_name, values in orbital_params.items():
            if values:
                std_dev = np.std(values)
                value_range = np.max(values) - np.min(values)
                
                # 正規化多樣性分數
                if param_name == 'inclinations':
                    diversity_score = min(100, std_dev * 5)  # 傾角多樣性
                elif param_name == 'raans':
                    diversity_score = min(100, value_range / 360 * 100)  # RAAN 分布
                elif param_name == 'mean_motions':
                    diversity_score = min(100, std_dev * 50)  # 平均運動多樣性
                else:
                    diversity_score = min(100, std_dev * 100)
                
                diversity_metrics[param_name] = {
                    'std_deviation': std_dev,
                    'range': value_range,
                    'diversity_score': diversity_score
                }
                
                overall_diversity_score += diversity_score
        
        overall_diversity_score = overall_diversity_score / len(diversity_metrics) if diversity_metrics else 0
        
        result = {
            'parameter_diversity': diversity_metrics,
            'overall_diversity_score': overall_diversity_score,
            'diversity_threshold': 60.0,
            'meets_diversity_threshold': overall_diversity_score >= 60.0,
            'score': overall_diversity_score
        }
        
        result['status'] = 'pass' if result['meets_diversity_threshold'] else 'fail'
        
        return result
    
    def _validate_temporal_coverage(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證時間覆蓋（簡化版本）
        """
        # 這是一個簡化的時間覆蓋驗證
        # 實際實現需要完整的 SGP4 軌道計算
        
        # 估算每小時的衛星覆蓋
        hourly_coverage = []
        
        for hour in range(24):
            visible_satellites = 0
            
            for sat in satellites:
                try:
                    inclination = float(sat['INCLINATION'])
                    mean_motion = float(sat['MEAN_MOTION'])
                    
                    # 簡化的可見性估算
                    if inclination > 80:  # 極地軌道
                        visibility_prob = 0.8
                    elif inclination > 50:
                        visibility_prob = 0.4
                    else:
                        visibility_prob = 0.2
                    
                    # 基於軌道週期的時間修正
                    orbital_period = 24 / mean_motion
                    phase_offset = (hour * orbital_period) % 24
                    
                    if phase_offset < (orbital_period * visibility_prob):
                        visible_satellites += 1
                        
                except (KeyError, ValueError, TypeError):
                    continue
            
            hourly_coverage.append(visible_satellites)
        
        # 分析覆蓋空隙
        min_coverage = min(hourly_coverage)
        avg_coverage = np.mean(hourly_coverage)
        coverage_gaps = sum(1 for cov in hourly_coverage if cov < 3)  # 少於3顆衛星的時段
        
        result = {
            'hourly_coverage': hourly_coverage,
            'min_hourly_coverage': min_coverage,
            'avg_hourly_coverage': avg_coverage,
            'coverage_gaps_hours': coverage_gaps,
            'max_allowed_gaps': 2,  # 允許最多2小時覆蓋不足
            'meets_coverage_requirement': coverage_gaps <= 2,
            'score': max(0, 100 - coverage_gaps * 20)  # 每個空隙扣20分
        }
        
        result['status'] = 'pass' if result['meets_coverage_requirement'] else 'fail'
        
        return result
    
    def _validate_handover_potential(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證換手場景潛力
        """
        handover_metrics = {
            'polar_satellites': 0,
            'high_inclination_satellites': 0,
            'medium_inclination_satellites': 0,
            'diverse_raan_groups': 0,
            'multiple_altitudes': 0
        }
        
        raan_groups = set()
        altitudes = []
        
        for sat in satellites:
            try:
                inclination = float(sat['INCLINATION'])
                mean_motion = float(sat['MEAN_MOTION'])
                raan = float(sat['RA_OF_ASC_NODE'])
                
                # 分類傾角
                if inclination > 80:
                    handover_metrics['polar_satellites'] += 1
                elif inclination > 60:
                    handover_metrics['high_inclination_satellites'] += 1
                elif inclination > 40:
                    handover_metrics['medium_inclination_satellites'] += 1
                
                # RAAN 分組
                raan_group = int(raan / 30)  # 30度一組
                raan_groups.add(raan_group)
                
                # 計算軌道高度
                altitude = self._calculate_altitude_from_mean_motion(mean_motion)
                altitudes.append(altitude)
                
            except (KeyError, ValueError, TypeError):
                continue
        
        handover_metrics['diverse_raan_groups'] = len(raan_groups)
        
        # 分析高度多樣性
        if altitudes:
            altitude_std = np.std(altitudes)
            handover_metrics['altitude_diversity'] = altitude_std
            handover_metrics['multiple_altitudes'] = 1 if altitude_std > 50 else 0
        
        # 計算換手潛力分數
        potential_score = (
            handover_metrics['polar_satellites'] * 0.4 +
            handover_metrics['high_inclination_satellites'] * 0.3 +
            handover_metrics['medium_inclination_satellites'] * 0.2 +
            handover_metrics['diverse_raan_groups'] * 2 +
            handover_metrics['multiple_altitudes'] * 10
        )
        
        result = {
            'handover_metrics': handover_metrics,
            'potential_score': min(100, potential_score),
            'potential_threshold': 70.0,
            'meets_potential_threshold': potential_score >= 70.0,
            'score': min(100, potential_score)
        }
        
        result['status'] = 'pass' if result['meets_potential_threshold'] else 'fail'
        
        return result
    
    def _analyze_raan_distribution(self, raan_values: List[float]) -> Dict[str, Any]:
        """
        分析 RAAN 分布
        """
        if not raan_values:
            return {'error': 'No RAAN values provided'}
        
        # 將 RAAN 值分組到 30 度的扇區中
        sectors = [0] * 12  # 360/30 = 12 個扇區
        
        for raan in raan_values:
            sector = int(raan / 30) % 12
            sectors[sector] += 1
        
        # 計算分布均勻性
        expected_per_sector = len(raan_values) / 12
        chi_square = sum((observed - expected_per_sector)**2 / expected_per_sector 
                        for observed in sectors if expected_per_sector > 0)
        
        return {
            'sector_distribution': sectors,
            'chi_square_statistic': chi_square,
            'uniformity_score': max(0, 100 - chi_square * 2),  # 簡化的均勻性分數
            'empty_sectors': sectors.count(0)
        }
    
    def _calculate_altitude_from_mean_motion(self, mean_motion: float) -> float:
        """
        從平均運動計算軌道高度
        """
        GM = 398600.4418  # 地球標準重力參數 (km³/s²)
        earth_radius = 6371.0  # 地球半徑 (km)
        
        period_seconds = 24 * 3600 / mean_motion
        semi_major_axis = ((GM * period_seconds**2) / (4 * math.pi**2))**(1/3)
        altitude = semi_major_axis - earth_radius
        
        return altitude
    
    def _generate_overall_assessment(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成整體評估
        """
        # 收集所有測試分數
        test_scores = {}
        pass_count = 0
        total_tests = 0
        
        for test_name, result in test_results.items():
            if isinstance(result, dict) and 'score' in result:
                test_scores[test_name] = result['score']
                total_tests += 1
                if result.get('status') == 'pass':
                    pass_count += 1
        
        # 計算加權平均分數
        weighted_scores = {
            'satellite_count': test_scores.get('satellite_count', 0) * 0.2,
            'raan_coverage': test_scores.get('raan_coverage', 0) * 0.15,
            'quality_scores': test_scores.get('quality_scores', 0) * 0.25,
            'constellation_balance': test_scores.get('constellation_balance', 0) * 0.15,
            'orbital_diversity': test_scores.get('orbital_diversity', 0) * 0.15,
            'temporal_coverage': test_scores.get('temporal_coverage', 0) * 0.05,
            'handover_potential': test_scores.get('handover_potential', 0) * 0.05
        }
        
        overall_score = sum(weighted_scores.values())
        pass_rate = pass_count / total_tests * 100 if total_tests > 0 else 0
        
        # 確定等級
        if overall_score >= 90 and pass_rate >= 85:
            grade = 'A'
            status = 'excellent'
        elif overall_score >= 80 and pass_rate >= 70:
            grade = 'B'
            status = 'good'
        elif overall_score >= 70 and pass_rate >= 60:
            grade = 'C'
            status = 'acceptable'
        else:
            grade = 'D'
            status = 'needs_improvement'
        
        return {
            'overall_score': overall_score,
            'pass_rate': pass_rate,
            'total_tests': total_tests,
            'passed_tests': pass_count,
            'grade': grade,
            'status': status,
            'test_scores': test_scores,
            'weighted_contributions': weighted_scores
        }
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """
        根據測試結果生成建議
        """
        recommendations = []
        
        # 檢查每個測試結果並生成相應建議
        for test_name, result in test_results.items():
            if isinstance(result, dict) and result.get('status') == 'fail':
                if test_name == 'satellite_count':
                    recommendations.append(f"調整篩選參數以達到目標衛星數量 ({self.validation_criteria['target_satellite_count']['ideal']} 顆)")
                
                elif test_name == 'raan_coverage':
                    recommendations.append(f"增加 RAAN 覆蓋度至至少 {self.validation_criteria['raan_coverage_threshold']}%")
                
                elif test_name == 'quality_scores':
                    recommendations.append("提高品質評分標準或調整評分權重")
                
                elif test_name == 'constellation_balance':
                    recommendations.append("調整星座配額以達到更好的平衡")
                
                elif test_name == 'orbital_diversity':
                    recommendations.append("增加軌道參數的多樣性")
                
                elif test_name == 'temporal_coverage':
                    recommendations.append("優化時間覆蓋以減少空窗期")
                
                elif test_name == 'handover_potential':
                    recommendations.append("增加更多極地軌道衛星以提高換手場景潛力")
        
        if not recommendations:
            recommendations.append("所有測試項目均已通過，Phase 2 篩選質量優秀")
        
        return recommendations
    
    def _determine_phase2_status(self, overall_assessment: Dict[str, Any]) -> str:
        """
        確定 Phase 2 狀態
        """
        status = overall_assessment['status']
        
        if status == 'excellent':
            return 'fully_completed'
        elif status == 'good':
            return 'mostly_completed'
        elif status == 'acceptable':
            return 'partially_completed'
        else:
            return 'needs_improvement'
    
    def run_full_validation(self) -> Dict[str, Any]:
        """
        執行完整的 Phase 2 驗證流程
        """
        logger.info("🚀 開始執行完整的 Phase 2 驗證")
        
        # 執行整合篩選
        tle_data_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
        filter_system = IntegratedSatelliteFilterSystem()
        
        try:
            # 執行篩選
            integrated_results = filter_system.execute_complete_filtering(tle_data_dir)
            
            # 執行驗證
            validation_results = self.validate_phase2_results(integrated_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"驗證過程中發生錯誤: {e}")
            return {
                'phase2_status': 'error',
                'error_message': str(e),
                'validation_timestamp': datetime.now().isoformat()
            }

def main():
    """主要驗證程序"""
    
    validator = Phase2ComprehensiveValidator()
    
    try:
        # 執行完整驗證
        results = validator.run_full_validation()
        
        # 顯示結果
        print("\n" + "="*80)
        print("🔍 Phase 2 軌道多樣性篩選驗證報告")
        print("="*80)
        
        if results['phase2_status'] == 'error':
            print(f"❌ 驗證過程發生錯誤: {results['error_message']}")
            return
        
        print(f"📍 目標座標: {results['target_coordinate']}")
        print(f"⏰ 驗證時間: {results['validation_timestamp']}")
        print(f"🎯 Phase 2 狀態: {results['phase2_status']}")
        
        # 顯示測試結果摘要
        overall = results['overall_assessment']
        print(f"\n📊 整體評估:")
        print(f"  整體分數: {overall['overall_score']:.1f}/100")
        print(f"  通過率: {overall['pass_rate']:.1f}%")
        print(f"  等級: {overall['grade']}")
        print(f"  狀態: {overall['status']}")
        
        # 顯示各項測試結果
        print(f"\n🧪 詳細測試結果:")
        for test_name, result in results['test_results'].items():
            if isinstance(result, dict):
                status_icon = "✅" if result.get('status') == 'pass' else "❌"
                score = result.get('score', 0)
                print(f"  {status_icon} {test_name}: {score:.1f}/100")
        
        # 顯示建議
        if results['recommendations']:
            print(f"\n💡 改進建議:")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # 保存詳細結果
        output_file = Path("/home/sat/ntn-stack/simworld/backend/phase2_validation_report.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 詳細驗證報告已保存至: {output_file}")
        
        # 最終判定
        if results['phase2_status'] == 'fully_completed':
            print(f"\n🎉 Phase 2 軌道多樣性篩選已完全通過驗證！")
            print(f"✅ 可以進入下一階段開發")
        else:
            print(f"\n⚠️ Phase 2 需要進一步改進")
            print(f"📋 請參考上述建議進行調整")
        
    except Exception as e:
        logger.error(f"主程序執行錯誤: {e}")
        print(f"❌ 驗證失敗: {e}")

if __name__ == "__main__":
    main()