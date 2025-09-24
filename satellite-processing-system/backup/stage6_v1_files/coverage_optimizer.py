"""
CoverageOptimizer - 空間覆蓋優化器

專注於空間覆蓋相關的優化功能：
- 衛星選擇演算法
- 覆蓋品質評估
- 星座模式分析
- 相位多樣性計算

從原始 CoverageOptimizationEngine 重構，移除時域和池管理功能
"""

import json
import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class CoverageOptimizer:
    """空間覆蓋優化器 - 專注於空間覆蓋和衛星選擇"""

    def __init__(self, optimizer_config: Dict[str, Any] = None):
        """初始化覆蓋優化器"""
        self.config = optimizer_config or self._get_default_config()
        self.logger = logger

        # 初始化共享核心模組
        try:
            from ..shared.orbital_calculations_core import OrbitalCalculationsCore
            from ..shared.visibility_calculations_core import VisibilityCalculationsCore

            observer_config = self.config.get('observer_config', {})
            self.orbital_calc = OrbitalCalculationsCore(observer_config)
            self.visibility_calc = VisibilityCalculationsCore(observer_config)

        except ImportError:
            logger.warning("無法導入共享核心模組，使用簡化實現")
            self.orbital_calc = None
            self.visibility_calc = None

        # 優化統計
        self.optimization_stats = {
            'coverage_optimizations_performed': 0,
            'successful_selections': 0,
            'coverage_improvements_achieved': 0,
            'total_satellites_processed': 0
        }

        self.logger.info("🎯 空間覆蓋優化器初始化完成")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'coverage_optimization': {
                'target_satellite_count': 16,
                'min_satellite_count': 8,
                'max_satellite_count': 24,
                'diversity_weight': 0.4,
                'coverage_weight': 0.3,
                'quality_weight': 0.3
            },
            'selection_criteria': {
                'phase_contribution_weight': 0.35,
                'raan_contribution_weight': 0.25,
                'coverage_quality_weight': 0.25,
                'orbital_stability_weight': 0.15
            },
            'diversity_thresholds': {
                'minimum_phase_diversity': 0.6,
                'target_phase_diversity': 0.8,
                'angular_separation_threshold': 30.0  # degrees
            }
        }

    def optimize_spatial_coverage(self,
                                satellite_candidates: List[Dict],
                                coverage_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """執行空間覆蓋優化主流程"""

        start_time = datetime.now()
        self.logger.info(f"🎯 開始空間覆蓋優化，候選衛星: {len(satellite_candidates)}顆")

        try:
            # 1. 分析候選衛星的空間分佈
            spatial_analysis = self._analyze_spatial_distribution(satellite_candidates)

            # 2. 計算覆蓋評分
            coverage_scores = self._calculate_coverage_scores(satellite_candidates, coverage_requirements)

            # 3. 執行選擇演算法
            selection_result = self._execute_spatial_selection_algorithm(
                satellite_candidates, coverage_scores, coverage_requirements
            )

            # 4. 驗證優化結果
            validation_result = self._validate_coverage_optimization(selection_result)

            # 5. 產生優化報告
            optimization_report = {
                'optimization_type': 'spatial_coverage',
                'input_satellites': len(satellite_candidates),
                'selected_satellites': selection_result.get('selected_satellites', []),
                'spatial_analysis': spatial_analysis,
                'coverage_scores': coverage_scores,
                'selection_metrics': selection_result.get('selection_metrics', {}),
                'validation_result': validation_result,
                'optimization_duration': (datetime.now() - start_time).total_seconds(),
                'optimization_timestamp': datetime.now().isoformat()
            }

            # 更新統計
            self.optimization_stats['coverage_optimizations_performed'] += 1
            self.optimization_stats['total_satellites_processed'] += len(satellite_candidates)

            if validation_result.get('optimization_valid', False):
                self.optimization_stats['successful_selections'] += 1

            improvement = selection_result.get('coverage_improvement', 0)
            if improvement > 0:
                self.optimization_stats['coverage_improvements_achieved'] += 1

            self.logger.info(f"✅ 空間覆蓋優化完成，選擇 {len(selection_result.get('selected_satellites', []))} 顆衛星")
            return optimization_report

        except Exception as e:
            self.logger.error(f"❌ 空間覆蓋優化失敗: {e}")
            return {'error': str(e), 'optimization_type': 'spatial_coverage'}

    def calculate_phase_diversity_score(self, satellites: List[Dict]) -> float:
        """計算相位多樣性分數"""
        try:
            if not satellites:
                return 0.0

            # 提取軌道元素
            orbital_elements = self._extract_orbital_elements(satellites)
            if not orbital_elements:
                return 0.0

            # 計算平均近點角分佈
            mean_anomalies = [elem.get('mean_anomaly', 0) for elem in orbital_elements]
            raan_values = [elem.get('raan', 0) for elem in orbital_elements]

            # 計算角度分散度
            ma_diversity = self._calculate_angular_diversity(mean_anomalies)
            raan_diversity = self._calculate_angular_diversity(raan_values)

            # 綜合多樣性分數
            overall_diversity = (ma_diversity + raan_diversity) / 2

            self.logger.debug(f"📊 相位多樣性分數: {overall_diversity:.3f}")
            return overall_diversity

        except Exception as e:
            self.logger.error(f"❌ 相位多樣性計算失敗: {e}")
            return 0.0

    def evaluate_satellite_coverage_quality(self, satellite: Dict) -> float:
        """評估單顆衛星的覆蓋品質"""
        try:
            # 提取軌道參數
            orbital_elements = self._extract_orbital_elements([satellite])
            if not orbital_elements:
                return 0.5

            element = orbital_elements[0]

            # 評估因子
            altitude_score = self._assess_altitude_quality(element)
            inclination_score = self._assess_inclination_quality(element)
            eccentricity_score = self._assess_eccentricity_quality(element)

            # 加權平均
            weights = self.config.get('quality_weights', {
                'altitude': 0.4,
                'inclination': 0.3,
                'eccentricity': 0.3
            })

            quality_score = (
                weights.get('altitude', 0.4) * altitude_score +
                weights.get('inclination', 0.3) * inclination_score +
                weights.get('eccentricity', 0.3) * eccentricity_score
            )

            return max(0.0, min(1.0, quality_score))

        except Exception as e:
            self.logger.error(f"❌ 覆蓋品質評估失敗: {e}")
            return 0.5

    def select_optimal_satellite_set(self,
                                   candidates: List[Dict],
                                   selection_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """選擇最佳衛星集合"""
        try:
            target_count = selection_criteria.get('target_count', 16)
            criteria_weights = selection_criteria.get('weights', self.config['selection_criteria'])

            self.logger.info(f"🎯 執行衛星選擇，目標: {target_count}顆")

            # 計算每顆衛星的綜合評分
            satellite_scores = []
            for satellite in candidates:
                score = self._calculate_satellite_selection_score(
                    satellite, candidates, criteria_weights
                )
                satellite_scores.append({
                    'satellite': satellite,
                    'score': score,
                    'satellite_id': satellite.get('satellite_id', 'unknown')
                })

            # 按分數排序
            satellite_scores.sort(key=lambda x: x['score'], reverse=True)

            # 選擇前N個
            selected_count = min(target_count, len(satellite_scores))
            selected_items = satellite_scores[:selected_count]

            # 計算選擇品質指標
            selected_satellites = [item['satellite'] for item in selected_items]
            selection_quality = self._assess_selection_quality(selected_satellites)

            return {
                'selected_satellites': selected_satellites,
                'selection_scores': [item['score'] for item in selected_items],
                'average_score': np.mean([item['score'] for item in selected_items]),
                'selection_quality': selection_quality,
                'candidates_evaluated': len(candidates),
                'selection_method': 'weighted_multi_criteria'
            }

        except Exception as e:
            self.logger.error(f"❌ 衛星選擇失敗: {e}")
            return {'selected_satellites': [], 'error': str(e)}

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取優化統計資訊"""
        return self.optimization_stats.copy()

    # =============== 私有輔助方法 ===============

    def _analyze_spatial_distribution(self, satellites: List[Dict]) -> Dict[str, Any]:
        """分析衛星空間分佈"""
        try:
            orbital_elements = self._extract_orbital_elements(satellites)
            if not orbital_elements:
                return {'error': 'No valid orbital elements'}

            # 分析軌道平面分佈
            raan_values = [elem.get('raan', 0) for elem in orbital_elements]
            inclination_values = [elem.get('inclination', 0) for elem in orbital_elements]

            analysis = {
                'total_satellites': len(satellites),
                'valid_orbital_elements': len(orbital_elements),
                'raan_distribution': {
                    'values': raan_values,
                    'spread': self._calculate_angular_spread(raan_values),
                    'uniformity': self._calculate_angular_diversity(raan_values)
                },
                'inclination_distribution': {
                    'values': inclination_values,
                    'mean': np.mean(inclination_values),
                    'std': np.std(inclination_values),
                    'range': [min(inclination_values), max(inclination_values)]
                },
                'constellation_breakdown': self._analyze_constellation_distribution(satellites)
            }

            return analysis

        except Exception as e:
            self.logger.error(f"❌ 空間分佈分析失敗: {e}")
            return {'error': str(e)}

    def _calculate_coverage_scores(self, satellites: List[Dict], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """計算覆蓋評分"""
        try:
            coverage_scores = {}

            for i, satellite in enumerate(satellites):
                satellite_id = satellite.get('satellite_id', f'sat_{i}')

                # 計算個別衛星的覆蓋分數
                quality_score = self.evaluate_satellite_coverage_quality(satellite)

                # 計算相對於要求的符合度
                requirement_compliance = self._assess_requirement_compliance(satellite, requirements)

                coverage_scores[satellite_id] = {
                    'quality_score': quality_score,
                    'requirement_compliance': requirement_compliance,
                    'combined_score': (quality_score + requirement_compliance) / 2
                }

            return coverage_scores

        except Exception as e:
            self.logger.error(f"❌ 覆蓋評分計算失敗: {e}")
            return {}

    def _execute_spatial_selection_algorithm(self,
                                           candidates: List[Dict],
                                           coverage_scores: Dict[str, Any],
                                           requirements: Dict[str, Any]) -> Dict[str, Any]:
        """執行空間選擇演算法"""
        try:
            target_count = requirements.get('target_satellite_count', 16)
            selection_strategy = requirements.get('selection_strategy', 'balanced')

            if selection_strategy == 'balanced':
                return self._balanced_spatial_selection(candidates, coverage_scores, target_count)
            elif selection_strategy == 'maximum_coverage':
                return self._maximum_coverage_selection(candidates, coverage_scores, target_count)
            elif selection_strategy == 'diversity_focused':
                return self._diversity_focused_selection(candidates, coverage_scores, target_count)
            else:
                return self._balanced_spatial_selection(candidates, coverage_scores, target_count)

        except Exception as e:
            self.logger.error(f"❌ 空間選擇演算法執行失敗: {e}")
            return {'selected_satellites': [], 'error': str(e)}

    def _balanced_spatial_selection(self, candidates: List[Dict], scores: Dict[str, Any], target_count: int) -> Dict[str, Any]:
        """平衡空間選擇策略"""
        try:
            # 結合覆蓋品質和多樣性進行選擇
            selection_criteria = {
                'target_count': target_count,
                'weights': {
                    'coverage_quality_weight': 0.4,
                    'phase_contribution_weight': 0.3,
                    'raan_contribution_weight': 0.2,
                    'orbital_stability_weight': 0.1
                }
            }

            selection_result = self.select_optimal_satellite_set(candidates, selection_criteria)

            # 添加平衡選擇特定的指標
            selected_satellites = selection_result.get('selected_satellites', [])
            balance_metrics = {
                'diversity_score': self.calculate_phase_diversity_score(selected_satellites),
                'average_quality': np.mean([
                    self.evaluate_satellite_coverage_quality(sat) for sat in selected_satellites
                ]) if selected_satellites else 0,
                'coverage_improvement': self._estimate_coverage_improvement(selected_satellites)
            }

            selection_result['selection_metrics'] = balance_metrics
            selection_result['selection_strategy'] = 'balanced_spatial'

            return selection_result

        except Exception as e:
            self.logger.error(f"❌ 平衡空間選擇失敗: {e}")
            return {'selected_satellites': [], 'error': str(e)}

    def _maximum_coverage_selection(self, candidates: List[Dict], scores: Dict[str, Any], target_count: int) -> Dict[str, Any]:
        """最大覆蓋選擇策略"""
        # 簡化實現：選擇覆蓋品質最高的衛星
        try:
            satellite_quality_scores = []
            for i, satellite in enumerate(candidates):
                satellite_id = satellite.get('satellite_id', f'sat_{i}')
                quality = scores.get(satellite_id, {}).get('quality_score', 0)
                satellite_quality_scores.append((satellite, quality))

            # 按品質排序並選擇前N個
            satellite_quality_scores.sort(key=lambda x: x[1], reverse=True)
            selected = [item[0] for item in satellite_quality_scores[:target_count]]

            return {
                'selected_satellites': selected,
                'selection_metrics': {
                    'average_quality': np.mean([item[1] for item in satellite_quality_scores[:target_count]]),
                    'coverage_improvement': self._estimate_coverage_improvement(selected)
                },
                'selection_strategy': 'maximum_coverage'
            }

        except Exception as e:
            self.logger.error(f"❌ 最大覆蓋選擇失敗: {e}")
            return {'selected_satellites': [], 'error': str(e)}

    def _diversity_focused_selection(self, candidates: List[Dict], scores: Dict[str, Any], target_count: int) -> Dict[str, Any]:
        """多樣性優先選擇策略"""
        try:
            # 使用貪婪演算法，逐步添加最能增加多樣性的衛星
            selected_satellites = []
            remaining_candidates = candidates.copy()

            # 選擇第一顆衛星（品質最高的）
            if remaining_candidates:
                first_satellite = max(remaining_candidates,
                                    key=lambda s: scores.get(s.get('satellite_id', ''), {}).get('quality_score', 0))
                selected_satellites.append(first_satellite)
                remaining_candidates.remove(first_satellite)

            # 逐步添加增加多樣性最多的衛星
            while len(selected_satellites) < target_count and remaining_candidates:
                best_candidate = None
                best_diversity_gain = -1

                for candidate in remaining_candidates:
                    test_selection = selected_satellites + [candidate]
                    diversity_score = self.calculate_phase_diversity_score(test_selection)

                    if diversity_score > best_diversity_gain:
                        best_diversity_gain = diversity_score
                        best_candidate = candidate

                if best_candidate:
                    selected_satellites.append(best_candidate)
                    remaining_candidates.remove(best_candidate)
                else:
                    break

            return {
                'selected_satellites': selected_satellites,
                'selection_metrics': {
                    'final_diversity_score': self.calculate_phase_diversity_score(selected_satellites),
                    'coverage_improvement': self._estimate_coverage_improvement(selected_satellites)
                },
                'selection_strategy': 'diversity_focused'
            }

        except Exception as e:
            self.logger.error(f"❌ 多樣性優先選擇失敗: {e}")
            return {'selected_satellites': [], 'error': str(e)}

    def _calculate_satellite_selection_score(self, satellite: Dict, all_satellites: List[Dict], weights: Dict[str, float]) -> float:
        """計算衛星選擇綜合評分"""
        try:
            scores = {}

            # 覆蓋品質分數
            scores['coverage_quality'] = self.evaluate_satellite_coverage_quality(satellite)

            # 相位貢獻分數
            scores['phase_contribution'] = self._calculate_phase_contribution(satellite, all_satellites)

            # RAAN貢獻分數
            scores['raan_contribution'] = self._calculate_raan_contribution(satellite, all_satellites)

            # 軌道穩定性分數
            scores['orbital_stability'] = self._assess_orbital_stability(satellite)

            # 加權計算總分
            total_score = sum(weights.get(f"{criterion}_weight", 0.25) * score
                            for criterion, score in scores.items())

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.error(f"❌ 衛星選擇評分計算失敗: {e}")
            return 0.5

    def _extract_orbital_elements(self, satellites: List[Dict]) -> List[Dict]:
        """提取軌道元素"""
        try:
            if self.orbital_calc:
                return self.orbital_calc.extract_orbital_elements(satellites)
            else:
                # 簡化實現
                elements = []
                for sat in satellites:
                    if 'tle_line1' in sat and 'tle_line2' in sat:
                        # 簡化的TLE解析
                        element = {
                            'satellite_id': sat.get('satellite_id', 'unknown'),
                            'semi_major_axis': 7000,  # 假設值
                            'eccentricity': 0.001,
                            'inclination': 53.0,
                            'raan': 0.0,
                            'argument_of_perigee': 0.0,
                            'mean_anomaly': 0.0
                        }
                        elements.append(element)
                return elements

        except Exception as e:
            self.logger.error(f"❌ 軌道元素提取失敗: {e}")
            return []

    def _calculate_angular_diversity(self, angles: List[float]) -> float:
        """計算角度多樣性"""
        if len(angles) < 2:
            return 0.0

        try:
            # 計算圓形方差
            angles_rad = [math.radians(a) for a in angles]
            mean_cos = np.mean([math.cos(a) for a in angles_rad])
            mean_sin = np.mean([math.sin(a) for a in angles_rad])

            circular_variance = 1 - math.sqrt(mean_cos**2 + mean_sin**2)
            return circular_variance

        except Exception:
            return 0.0

    def _calculate_angular_spread(self, angles: List[float]) -> float:
        """計算角度分散度"""
        if len(angles) < 2:
            return 0.0

        try:
            angles_sorted = sorted(angles)
            max_gap = 0

            for i in range(len(angles_sorted)):
                next_i = (i + 1) % len(angles_sorted)
                gap = angles_sorted[next_i] - angles_sorted[i]
                if gap < 0:
                    gap += 360
                max_gap = max(max_gap, gap)

            # 返回最大間隙的補角（分散度）
            return (360 - max_gap) / 360

        except Exception:
            return 0.0

    def _assess_altitude_quality(self, orbital_element: Dict) -> float:
        """評估高度品質"""
        try:
            altitude = orbital_element.get('semi_major_axis', 7000) - 6371
            # 550km為理想高度，偏離越少分數越高
            ideal_altitude = 550
            deviation = abs(altitude - ideal_altitude)
            score = max(0.0, 1.0 - deviation / 1000)  # 1000km為最大容忍偏差
            return score
        except:
            return 0.7

    def _assess_inclination_quality(self, orbital_element: Dict) -> float:
        """評估傾角品質"""
        try:
            inclination = orbital_element.get('inclination', 53.0)
            # 53度為理想傾角（Starlink）
            ideal_inclination = 53.0
            deviation = abs(inclination - ideal_inclination)
            score = max(0.0, 1.0 - deviation / 45.0)  # 45度為最大容忍偏差
            return score
        except:
            return 0.8

    def _assess_eccentricity_quality(self, orbital_element: Dict) -> float:
        """評估偏心率品質"""
        try:
            eccentricity = orbital_element.get('eccentricity', 0.001)
            # 偏心率越小越好（接近圓形軌道）
            score = max(0.0, 1.0 - min(eccentricity * 20, 1.0))
            return score
        except:
            return 0.9

    def _calculate_phase_contribution(self, satellite: Dict, all_satellites: List[Dict]) -> float:
        """計算相位貢獻度"""
        # 簡化實現
        return 0.7

    def _calculate_raan_contribution(self, satellite: Dict, all_satellites: List[Dict]) -> float:
        """計算RAAN貢獻度"""
        # 簡化實現
        return 0.6

    def _assess_orbital_stability(self, satellite: Dict) -> float:
        """評估軌道穩定性"""
        # 簡化實現，基於軌道參數
        return 0.8

    def _assess_selection_quality(self, selected_satellites: List[Dict]) -> Dict[str, float]:
        """評估選擇品質"""
        try:
            if not selected_satellites:
                return {'overall_quality': 0.0}

            diversity_score = self.calculate_phase_diversity_score(selected_satellites)
            avg_quality = np.mean([
                self.evaluate_satellite_coverage_quality(sat) for sat in selected_satellites
            ])

            return {
                'overall_quality': (diversity_score + avg_quality) / 2,
                'diversity_score': diversity_score,
                'average_individual_quality': avg_quality,
                'satellite_count': len(selected_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 選擇品質評估失敗: {e}")
            return {'overall_quality': 0.0}

    def _analyze_constellation_distribution(self, satellites: List[Dict]) -> Dict[str, int]:
        """分析星座分佈"""
        constellation_count = {}
        for sat in satellites:
            constellation = sat.get('constellation', 'unknown')
            constellation_count[constellation] = constellation_count.get(constellation, 0) + 1
        return constellation_count

    def _assess_requirement_compliance(self, satellite: Dict, requirements: Dict[str, Any]) -> float:
        """評估需求符合度"""
        # 簡化實現
        return 0.75

    def _estimate_coverage_improvement(self, selected_satellites: List[Dict]) -> float:
        """估算覆蓋改善度"""
        if not selected_satellites:
            return 0.0

        # 簡化實現：基於衛星數量和多樣性
        diversity = self.calculate_phase_diversity_score(selected_satellites)
        count_factor = min(len(selected_satellites) / 16, 1.0)

        return (diversity + count_factor) / 2

    def _validate_coverage_optimization(self, optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證覆蓋優化結果"""
        try:
            selected_satellites = optimization_result.get('selected_satellites', [])

            validation = {
                'optimization_valid': True,
                'validation_checks': {},
                'validation_timestamp': datetime.now().isoformat()
            }

            # 檢查衛星數量
            min_count = self.config['coverage_optimization']['min_satellite_count']
            max_count = self.config['coverage_optimization']['max_satellite_count']
            count_valid = min_count <= len(selected_satellites) <= max_count
            validation['validation_checks']['satellite_count'] = count_valid

            # 檢查多樣性
            diversity_score = self.calculate_phase_diversity_score(selected_satellites)
            min_diversity = self.config['diversity_thresholds']['minimum_phase_diversity']
            diversity_valid = diversity_score >= min_diversity
            validation['validation_checks']['phase_diversity'] = diversity_valid

            # 檢查覆蓋品質
            if selected_satellites:
                avg_quality = np.mean([
                    self.evaluate_satellite_coverage_quality(sat) for sat in selected_satellites
                ])
                quality_valid = avg_quality >= 0.6
                validation['validation_checks']['coverage_quality'] = quality_valid
            else:
                validation['validation_checks']['coverage_quality'] = False

            # 綜合驗證結果
            validation['optimization_valid'] = all(validation['validation_checks'].values())

            return validation

        except Exception as e:
            self.logger.error(f"❌ 覆蓋優化驗證失敗: {e}")
            return {'optimization_valid': False, 'error': str(e)}