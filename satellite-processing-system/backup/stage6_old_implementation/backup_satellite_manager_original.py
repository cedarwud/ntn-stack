"""
備份衛星管理器 - Stage 6 內部模組化拆分

從 temporal_spatial_analysis_engine.py 中提取的備份衛星池管理和切換邏輯功能
包含12個備份管理相關的方法，專注於備份衛星池的動態管理和故障切換

職責範圍:
- 備份衛星池建立和維護
- 智慧備份評估和選擇
- 快速切換機制實施
- 即時覆蓋監控
- 預測性覆蓋分析
- 自動調整機制
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np

# 導入共享核心模組
try:
    from ...shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    sys.path.append(str(src_path))
    from shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore

logger = logging.getLogger(__name__)

class BackupSatelliteManager:
    """
    備份衛星管理器類別

    負責所有與備份衛星池管理和切換邏輯相關的功能
    從原始 TemporalSpatialAnalysisEngine 中提取12個備份管理相關方法
    """

    def __init__(self, observer_config: Optional[Dict] = None):
        """
        初始化備份衛星管理器

        Args:
            observer_config: 觀測者配置，可以是直接配置或包含'observer'鍵的嵌套配置
        """
        self.logger = logger

        # 處理配置格式
        if observer_config and 'observer' in observer_config:
            # 嵌套配置格式
            actual_observer_config = observer_config['observer']
        else:
            # 直接配置格式
            actual_observer_config = observer_config

        # 初始化共享核心模組
        self.orbital_calc = OrbitalCalculationsCore(actual_observer_config)
        self.visibility_calc = VisibilityCalculationsCore(actual_observer_config)
        self.signal_calc = SignalCalculationsCore()

        # 備份管理配置
        self.backup_config = {
            'pool_management': {
                'default_pool_size': 6,  # 預設備份池大小
                'minimum_pool_size': 3,
                'maximum_pool_size': 12,
                'backup_ratio': 0.25  # 25%作為備份
            },
            'switching_criteria': {
                'signal_degradation_threshold': -110.0,  # dBm
                'elevation_minimum': 5.0,  # degrees
                'availability_threshold': 0.95,
                'switching_delay_seconds': 5,
                'max_switching_attempts': 3
            },
            'monitoring': {
                'health_check_interval_seconds': 30,
                'performance_evaluation_interval_minutes': 5,
                'coverage_prediction_horizon_hours': 2,
                'alert_threshold_minutes': 10
            }
        }

        # 當前備份池狀態
        self.backup_pool = {
            'active_backups': [],
            'standby_backups': [],
            'degraded_backups': [],
            'pool_status': 'initializing'
        }

        # 管理統計
        self.management_stats = {
            'backup_pools_established': 0,
            'successful_switches': 0,
            'failed_switches': 0,
            'coverage_predictions': 0,
            'automatic_adjustments': 0,
            'alerts_generated': 0
        }

        self.logger.info("🔄 備份衛星管理器初始化完成")

    def establish_backup_satellite_pool(self, satellites: List[Dict],
                                       primary_selection: List[Dict] = None) -> Dict:
        """
        建立備份衛星池 (原: _establish_backup_satellite_pool)

        Args:
            satellites: 候選衛星列表
            primary_selection: 主要選擇的衛星 (用於避免重複)

        Returns:
            備份池建立結果
        """
        try:
            self.logger.info(f"🏗️ 建立備份衛星池 (候選: {len(satellites)}顆)")

            # 排除主要選擇的衛星
            available_satellites = satellites
            if primary_selection:
                primary_ids = {sat.get('satellite_id') for sat in primary_selection}
                available_satellites = [
                    sat for sat in satellites
                    if sat.get('satellite_id') not in primary_ids
                ]

            if not available_satellites:
                return {'error': 'No satellites available for backup pool'}

            # 計算備份池大小
            target_pool_size = min(
                self.backup_config['pool_management']['default_pool_size'],
                len(available_satellites)
            )

            # 執行智慧備份評估選擇最佳備份候選
            backup_evaluation = self.implement_intelligent_backup_evaluation(available_satellites)

            if 'error' in backup_evaluation:
                return backup_evaluation

            # 選擇前N個最佳候選作為備份池
            evaluated_candidates = backup_evaluation.get('evaluated_candidates', [])
            selected_backups = evaluated_candidates[:target_pool_size]

            # 建立備份池結構
            backup_pool_structure = {
                'pool_id': f"backup_pool_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'established_timestamp': datetime.now(timezone.utc).isoformat(),
                'pool_configuration': {
                    'target_size': target_pool_size,
                    'actual_size': len(selected_backups),
                    'selection_method': 'intelligent_evaluation'
                },
                'backup_satellites': selected_backups,
                'pool_categories': self._categorize_backup_satellites(selected_backups),
                'switching_readiness': self._assess_switching_readiness(selected_backups),
                'performance_baseline': self._establish_performance_baseline(selected_backups),
                'pool_quality_metrics': {
                    'average_signal_quality': backup_evaluation.get('average_signal_quality', 0),
                    'coverage_redundancy': backup_evaluation.get('coverage_redundancy', 0),
                    'orbital_diversity': backup_evaluation.get('orbital_diversity', 0)
                }
            }

            # 更新內部狀態
            self.backup_pool['active_backups'] = selected_backups
            self.backup_pool['pool_status'] = 'operational'
            self.management_stats['backup_pools_established'] += 1

            self.logger.info(f"✅ 備份池建立成功: {len(selected_backups)}顆備份衛星")

            return backup_pool_structure

        except Exception as e:
            self.logger.error(f"❌ 備份衛星池建立失敗: {e}")
            return {'error': str(e)}

    def implement_intelligent_backup_evaluation(self, candidates: List[Dict]) -> Dict:
        """
        實施智慧備份評估 (原: _implement_intelligent_backup_evaluation)

        Args:
            candidates: 候選衛星列表

        Returns:
            智慧評估結果
        """
        try:
            self.logger.info(f"🧠 執行智慧備份評估 ({len(candidates)}個候選)")

            evaluated_candidates = []

            for candidate in candidates:
                # 綜合評估每個候選衛星
                evaluation_score = self._calculate_backup_suitability_score(candidate)

                # 評估信號品質
                signal_assessment = self._assess_candidate_signal_quality(candidate)

                # 評估覆蓋貢獻
                coverage_contribution = self._assess_backup_coverage_contribution(candidate)

                # 評估軌道穩定性
                orbital_stability = self._assess_backup_orbital_stability(candidate)

                evaluated_candidate = {
                    'satellite_id': candidate.get('satellite_id', 'unknown'),
                    'constellation': candidate.get('constellation', 'unknown'),
                    'evaluation_score': evaluation_score,
                    'signal_quality_assessment': signal_assessment,
                    'coverage_contribution': coverage_contribution,
                    'orbital_stability': orbital_stability,
                    'backup_suitability_grade': self._grade_backup_suitability(evaluation_score),
                    'recommended_role': self._recommend_backup_role(evaluation_score, signal_assessment),
                    'satellite_data': candidate
                }

                evaluated_candidates.append(evaluated_candidate)

            # 按評估分數排序
            evaluated_candidates.sort(key=lambda x: x['evaluation_score'], reverse=True)

            # 計算整體評估指標
            evaluation_result = {
                'evaluation_completed': True,
                'candidates_evaluated': len(candidates),
                'evaluated_candidates': evaluated_candidates,
                'evaluation_summary': {
                    'excellent_candidates': len([c for c in evaluated_candidates if c['backup_suitability_grade'] == 'excellent']),
                    'good_candidates': len([c for c in evaluated_candidates if c['backup_suitability_grade'] == 'good']),
                    'fair_candidates': len([c for c in evaluated_candidates if c['backup_suitability_grade'] == 'fair']),
                    'poor_candidates': len([c for c in evaluated_candidates if c['backup_suitability_grade'] == 'poor'])
                },
                'quality_metrics': {
                    'average_evaluation_score': np.mean([c['evaluation_score'] for c in evaluated_candidates]),
                    'average_signal_quality': np.mean([c['signal_quality_assessment'].get('quality_score', 0) for c in evaluated_candidates]),
                    'coverage_redundancy': np.mean([c['coverage_contribution'] for c in evaluated_candidates]),
                    'orbital_diversity': self._calculate_candidates_orbital_diversity(evaluated_candidates)
                },
                'evaluation_timestamp': datetime.now(timezone.utc).isoformat()
            }

            return evaluation_result

        except Exception as e:
            self.logger.error(f"❌ 智慧備份評估失敗: {e}")
            return {'error': str(e)}

    def establish_rapid_switching_mechanism(self, backup_pool: List[Dict]) -> Dict:
        """
        建立快速切換機制 (原: _establish_rapid_switching_mechanism)

        Args:
            backup_pool: 備份衛星池

        Returns:
            快速切換機制配置
        """
        try:
            self.logger.info("⚡ 建立快速切換機制")

            if not backup_pool:
                return {'error': 'Empty backup pool provided'}

            # 建立切換優先級排序
            switching_priorities = self._establish_switching_priorities(backup_pool)

            # 配置切換觸發條件
            switching_triggers = {
                'signal_degradation': {
                    'threshold': self.backup_config['switching_criteria']['signal_degradation_threshold'],
                    'evaluation_window_seconds': 30,
                    'confirmation_required': True
                },
                'elevation_loss': {
                    'threshold': self.backup_config['switching_criteria']['elevation_minimum'],
                    'prediction_horizon_seconds': 60,
                    'preemptive_switching': True
                },
                'availability_drop': {
                    'threshold': self.backup_config['switching_criteria']['availability_threshold'],
                    'assessment_period_minutes': 5,
                    'automatic_switching': True
                }
            }

            # 建立切換執行流程
            switching_procedure = {
                'phase_1_detection': {
                    'monitoring_active': True,
                    'trigger_evaluation': 'continuous',
                    'detection_latency_target_ms': 500
                },
                'phase_2_validation': {
                    'backup_readiness_check': True,
                    'signal_quality_verification': True,
                    'orbital_position_validation': True,
                    'validation_timeout_seconds': 3
                },
                'phase_3_execution': {
                    'switching_delay_seconds': self.backup_config['switching_criteria']['switching_delay_seconds'],
                    'rollback_capability': True,
                    'success_confirmation_required': True,
                    'max_switching_time_seconds': 10
                },
                'phase_4_verification': {
                    'post_switch_monitoring_seconds': 30,
                    'performance_validation': True,
                    'stability_assessment': True
                }
            }

            switching_mechanism = {
                'mechanism_id': f"switch_mech_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'backup_pool_size': len(backup_pool),
                'switching_priorities': switching_priorities,
                'switching_triggers': switching_triggers,
                'switching_procedure': switching_procedure,
                'mechanism_status': 'armed',
                'readiness_assessment': {
                    'total_ready_backups': len([b for b in switching_priorities if b['readiness_status'] == 'ready']),
                    'average_readiness_score': np.mean([b['readiness_score'] for b in switching_priorities]),
                    'mechanism_reliability': self._assess_mechanism_reliability(switching_priorities)
                },
                'established_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info(f"✅ 快速切換機制建立完成: {len(switching_priorities)}個備份優先級")

            return switching_mechanism

        except Exception as e:
            self.logger.error(f"❌ 快速切換機制建立失敗: {e}")
            return {'error': str(e)}

    def establish_real_time_coverage_monitoring(self, monitoring_targets: List[Dict]) -> Dict:
        """
        建立即時覆蓋監控 (原: _establish_real_time_coverage_monitoring)

        Args:
            monitoring_targets: 監控目標列表

        Returns:
            即時監控系統配置
        """
        try:
            self.logger.info(f"👁️ 建立即時覆蓋監控 (目標: {len(monitoring_targets)}個)")

            # 配置監控參數
            monitoring_configuration = {
                'monitoring_targets': len(monitoring_targets),
                'monitoring_interval_seconds': self.backup_config['monitoring']['health_check_interval_seconds'],
                'performance_evaluation_interval_minutes': self.backup_config['monitoring']['performance_evaluation_interval_minutes'],
                'coverage_prediction_enabled': True,
                'real_time_alerts_enabled': True
            }

            # 建立監控指標
            monitoring_metrics = {
                'coverage_continuity': {
                    'target_percentage': 95.0,
                    'measurement_method': 'time_based_analysis',
                    'alert_threshold': 90.0
                },
                'signal_quality': {
                    'rsrp_threshold': -110.0,
                    'rsrq_threshold': -15.0,
                    'sinr_threshold': 3.0,
                    'degradation_alert_enabled': True
                },
                'satellite_availability': {
                    'elevation_threshold': self.backup_config['switching_criteria']['elevation_minimum'],
                    'visibility_prediction': True,
                    'handover_preparation': True
                }
            }

            # 配置預測性監控
            predictive_monitoring = self.implement_predictive_coverage_analysis(monitoring_targets)

            # 建立警報系統
            alert_system = {
                'coverage_gap_alerts': True,
                'signal_degradation_alerts': True,
                'satellite_loss_alerts': True,
                'backup_activation_alerts': True,
                'alert_delivery_methods': ['log', 'system_event'],
                'alert_priority_levels': ['info', 'warning', 'critical', 'emergency']
            }

            monitoring_system = {
                'system_id': f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'monitoring_configuration': monitoring_configuration,
                'monitoring_metrics': monitoring_metrics,
                'predictive_monitoring': predictive_monitoring,
                'alert_system': alert_system,
                'system_status': 'operational',
                'monitoring_baseline': self._establish_monitoring_baseline(monitoring_targets),
                'established_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info("✅ 即時覆蓋監控系統建立完成")

            return monitoring_system

        except Exception as e:
            self.logger.error(f"❌ 即時覆蓋監控建立失敗: {e}")
            return {'error': str(e)}

    def calculate_expected_coverage_at_time(self, satellites: List[Dict],
                                          target_time: datetime) -> Dict:
        """
        計算特定時間的預期覆蓋 (原: _calculate_expected_coverage_at_time)

        Args:
            satellites: 衛星列表
            target_time: 目標時間

        Returns:
            預期覆蓋計算結果
        """
        try:
            self.logger.debug(f"📊 計算預期覆蓋 (時間: {target_time.isoformat()})")

            # 分析衛星可見性窗口
            coverage_analysis = self.visibility_calc.analyze_coverage_windows(satellites)

            if 'error' in coverage_analysis:
                return coverage_analysis

            # 估算目標時間的覆蓋狀況
            visibility_windows = coverage_analysis.get('visibility_windows', [])

            # 計算目標時間點的覆蓋衛星
            target_timestamp = target_time.timestamp()
            covering_satellites = []

            for window in visibility_windows:
                window_start = window.get('start_time', 0)
                window_end = window.get('end_time', 0)

                if window_start <= target_timestamp <= window_end:
                    covering_satellites.append({
                        'satellite_id': window.get('satellite_id'),
                        'window_info': window,
                        'coverage_quality': window.get('max_elevation', 0)
                    })

            # 計算覆蓋品質指標
            coverage_metrics = {
                'covering_satellite_count': len(covering_satellites),
                'coverage_available': len(covering_satellites) > 0,
                'coverage_redundancy': max(0, len(covering_satellites) - 1),
                'average_coverage_quality': np.mean([
                    sat['coverage_quality'] for sat in covering_satellites
                ]) if covering_satellites else 0,
                'coverage_confidence': min(len(covering_satellites) / 3.0, 1.0)  # 3顆為滿信心
            }

            expected_coverage = {
                'target_time': target_time.isoformat(),
                'target_timestamp': target_timestamp,
                'covering_satellites': covering_satellites,
                'coverage_metrics': coverage_metrics,
                'coverage_assessment': self._assess_coverage_adequacy(coverage_metrics),
                'calculation_timestamp': datetime.now(timezone.utc).isoformat()
            }

            return expected_coverage

        except Exception as e:
            self.logger.error(f"❌ 預期覆蓋計算失敗: {e}")
            return {'error': str(e)}

    def implement_predictive_coverage_analysis(self, satellites: List[Dict]) -> Dict:
        """
        實施預測性覆蓋分析 (原: _implement_predictive_coverage_analysis)

        Args:
            satellites: 衛星列表

        Returns:
            預測性覆蓋分析結果
        """
        try:
            self.logger.info("🔮 實施預測性覆蓋分析")

            prediction_horizon = self.backup_config['monitoring']['coverage_prediction_horizon_hours']
            current_time = datetime.now(timezone.utc)

            # 生成預測時間點
            prediction_times = []
            for hour_offset in range(int(prediction_horizon * 2)):  # 每30分鐘一個預測點
                prediction_time = current_time + timedelta(minutes=30 * hour_offset)
                prediction_times.append(prediction_time)

            # 計算每個時間點的預期覆蓋
            coverage_predictions = []
            for pred_time in prediction_times:
                coverage_prediction = self.calculate_expected_coverage_at_time(satellites, pred_time)
                if 'error' not in coverage_prediction:
                    coverage_predictions.append(coverage_prediction)

            # 分析覆蓋趨勢
            coverage_trends = self.analyze_coverage_trends(coverage_predictions)

            # 生成預測性警報
            predictive_alerts = self.generate_predictive_alerts(coverage_predictions, coverage_trends)

            predictive_analysis = {
                'analysis_type': 'predictive_coverage',
                'prediction_horizon_hours': prediction_horizon,
                'prediction_points': len(prediction_times),
                'successful_predictions': len(coverage_predictions),
                'coverage_predictions': coverage_predictions,
                'coverage_trends': coverage_trends,
                'predictive_alerts': predictive_alerts,
                'analysis_summary': {
                    'average_future_coverage': np.mean([
                        p['coverage_metrics']['covering_satellite_count']
                        for p in coverage_predictions
                    ]) if coverage_predictions else 0,
                    'coverage_stability': coverage_trends.get('stability_score', 0),
                    'gap_predictions': len(predictive_alerts.get('gap_alerts', []))
                },
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.management_stats['coverage_predictions'] += 1

            return predictive_analysis

        except Exception as e:
            self.logger.error(f"❌ 預測性覆蓋分析失敗: {e}")
            return {'error': str(e)}

    def analyze_coverage_trends(self, coverage_predictions: List[Dict]) -> Dict:
        """
        分析覆蓋趨勢 (原: _analyze_coverage_trends)

        Args:
            coverage_predictions: 覆蓋預測列表

        Returns:
            覆蓋趨勢分析結果
        """
        try:
            if not coverage_predictions:
                return {'error': 'No predictions to analyze'}

            # 提取覆蓋數據時序
            coverage_counts = [
                pred['coverage_metrics']['covering_satellite_count']
                for pred in coverage_predictions
            ]

            coverage_qualities = [
                pred['coverage_metrics']['average_coverage_quality']
                for pred in coverage_predictions
            ]

            # 計算趨勢指標
            trend_analysis = {
                'coverage_count_trend': {
                    'mean': np.mean(coverage_counts),
                    'std': np.std(coverage_counts),
                    'min': min(coverage_counts),
                    'max': max(coverage_counts),
                    'trend_direction': self._calculate_trend_direction(coverage_counts)
                },
                'coverage_quality_trend': {
                    'mean': np.mean(coverage_qualities),
                    'std': np.std(coverage_qualities),
                    'min': min(coverage_qualities),
                    'max': max(coverage_qualities),
                    'trend_direction': self._calculate_trend_direction(coverage_qualities)
                },
                'stability_metrics': {
                    'coverage_variance': self.calculate_variance(coverage_counts),
                    'quality_variance': self.calculate_variance(coverage_qualities),
                    'stability_score': self._calculate_stability_score(coverage_counts, coverage_qualities)
                },
                'anomaly_detection': {
                    'coverage_gaps_detected': len([c for c in coverage_counts if c == 0]),
                    'quality_drops_detected': len([q for q in coverage_qualities if q < 10.0]),
                    'anomaly_periods': self._detect_anomaly_periods(coverage_predictions)
                }
            }

            return trend_analysis

        except Exception as e:
            self.logger.error(f"❌ 覆蓋趨勢分析失敗: {e}")
            return {'error': str(e)}

    def calculate_variance(self, data: List[float]) -> float:
        """
        計算變異數 (原: _calculate_variance)

        Args:
            data: 數據列表

        Returns:
            變異數
        """
        try:
            if not data or len(data) < 2:
                return 0.0

            return float(np.var(data))

        except Exception:
            return 0.0

    def generate_predictive_alerts(self, coverage_predictions: List[Dict],
                                 coverage_trends: Dict) -> Dict:
        """
        生成預測性警報 (原: _generate_predictive_alerts)

        Args:
            coverage_predictions: 覆蓋預測列表
            coverage_trends: 覆蓋趨勢分析

        Returns:
            預測性警報配置
        """
        try:
            alerts = {
                'gap_alerts': [],
                'quality_alerts': [],
                'trend_alerts': [],
                'system_alerts': []
            }

            alert_threshold_minutes = self.backup_config['monitoring']['alert_threshold_minutes']

            # 檢查覆蓋間隙警報
            for i, prediction in enumerate(coverage_predictions):
                covering_count = prediction['coverage_metrics']['covering_satellite_count']
                if covering_count == 0:
                    alerts['gap_alerts'].append({
                        'alert_type': 'coverage_gap',
                        'severity': 'critical',
                        'predicted_time': prediction['target_time'],
                        'message': f'預測在 {prediction["target_time"]} 將出現覆蓋間隙'
                    })

            # 檢查品質下降警報
            quality_threshold = 15.0  # 15度仰角作為品質門檻
            for prediction in coverage_predictions:
                avg_quality = prediction['coverage_metrics']['average_coverage_quality']
                if 0 < avg_quality < quality_threshold:
                    alerts['quality_alerts'].append({
                        'alert_type': 'quality_degradation',
                        'severity': 'warning',
                        'predicted_time': prediction['target_time'],
                        'quality_value': avg_quality,
                        'message': f'預測在 {prediction["target_time"]} 覆蓋品質將下降至 {avg_quality:.1f}°'
                    })

            # 檢查趨勢警報
            coverage_trend = coverage_trends.get('coverage_count_trend', {}).get('trend_direction', 'stable')
            if coverage_trend == 'declining':
                alerts['trend_alerts'].append({
                    'alert_type': 'coverage_declining_trend',
                    'severity': 'warning',
                    'message': '檢測到覆蓋數量下降趨勢'
                })

            # 系統警報
            total_alerts = sum(len(alert_list) for alert_list in alerts.values() if isinstance(alert_list, list))
            if total_alerts > 5:
                alerts['system_alerts'].append({
                    'alert_type': 'high_alert_volume',
                    'severity': 'info',
                    'alert_count': total_alerts,
                    'message': f'生成了 {total_alerts} 個預測性警報'
                })

            self.management_stats['alerts_generated'] += total_alerts

            return alerts

        except Exception as e:
            self.logger.error(f"❌ 預測性警報生成失敗: {e}")
            return {'error': str(e)}

    def establish_automatic_adjustment_mechanism(self, current_configuration: Dict) -> Dict:
        """
        建立自動調整機制 (原: _establish_automatic_adjustment_mechanism)

        Args:
            current_configuration: 當前配置

        Returns:
            自動調整機制配置
        """
        try:
            self.logger.info("🤖 建立自動調整機制")

            # 定義調整觸發條件
            adjustment_triggers = {
                'coverage_degradation': {
                    'threshold': 0.9,  # 90%覆蓋率以下觸發
                    'evaluation_period_minutes': 15,
                    'action': 'activate_additional_backups'
                },
                'signal_quality_drop': {
                    'threshold': -115.0,  # dBm
                    'consecutive_failures': 3,
                    'action': 'switch_to_better_satellites'
                },
                'backup_pool_depletion': {
                    'minimum_backup_count': 2,
                    'action': 'replenish_backup_pool'
                }
            }

            # 定義調整動作
            adjustment_actions = {
                'activate_additional_backups': {
                    'max_additional_backups': 4,
                    'selection_criteria': 'best_available',
                    'activation_delay_seconds': 10
                },
                'switch_to_better_satellites': {
                    'switch_count': 2,
                    'selection_method': 'highest_signal_quality',
                    'verification_required': True
                },
                'replenish_backup_pool': {
                    'target_pool_size': self.backup_config['pool_management']['default_pool_size'],
                    'selection_method': 'comprehensive_evaluation',
                    'replenishment_source': 'available_satellites'
                }
            }

            # 建立決策邏輯
            decision_logic = {
                'evaluation_frequency_seconds': 60,
                'decision_confidence_threshold': 0.7,
                'rollback_capability': True,
                'manual_override_available': True,
                'adjustment_logging': True
            }

            adjustment_mechanism = {
                'mechanism_id': f"auto_adjust_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'mechanism_status': 'active',
                'adjustment_triggers': adjustment_triggers,
                'adjustment_actions': adjustment_actions,
                'decision_logic': decision_logic,
                'performance_monitoring': {
                    'successful_adjustments': 0,
                    'failed_adjustments': 0,
                    'adjustment_impact_tracking': True
                },
                'established_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info("✅ 自動調整機制建立完成")

            return adjustment_mechanism

        except Exception as e:
            self.logger.error(f"❌ 自動調整機制建立失敗: {e}")
            return {'error': str(e)}

    def get_management_statistics(self) -> Dict:
        """獲取管理統計信息"""
        stats = self.management_stats.copy()
        stats.update({
            'current_backup_pool_status': self.backup_pool['pool_status'],
            'active_backups_count': len(self.backup_pool['active_backups']),
            'standby_backups_count': len(self.backup_pool['standby_backups']),
            'degraded_backups_count': len(self.backup_pool['degraded_backups'])
        })
        return stats

    # =============== 私有輔助方法 ===============

    def _calculate_backup_suitability_score(self, satellite: Dict) -> float:
        """計算備份適用性分數"""
        try:
            # 基礎分數
            base_score = 0.5

            # 星座品質權重
            constellation = satellite.get('constellation', 'unknown').lower()
            constellation_bonus = 0.1 if constellation in ['starlink', 'oneweb'] else 0

            # 軌道位置品質 (簡化評估)
            if 'position_timeseries' in satellite and satellite['position_timeseries']:
                position_bonus = 0.2
            else:
                position_bonus = 0

            # 可見性評估
            visibility_bonus = 0.1  # 簡化實現

            total_score = base_score + constellation_bonus + position_bonus + visibility_bonus

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.error(f"❌ 備份適用性分數計算失敗: {e}")
            return 0.5

    def _assess_candidate_signal_quality(self, candidate: Dict) -> Dict:
        """評估候選衛星信號品質"""
        try:
            # 使用信號計算核心進行評估
            signal_data = {
                'satellite_id': candidate.get('satellite_id'),
                'constellation': candidate.get('constellation', 'starlink'),
                'distance_km': 800.0,  # 假設距離
                'elevation_deg': 30.0,  # 假設仰角
                'is_visible': True
            }

            signal_assessment = self.signal_calc.calculate_signal_quality(signal_data)

            if 'error' not in signal_assessment:
                return {
                    'quality_available': True,
                    'quality_score': signal_assessment.get('quality_assessment', {}).get('overall_score', 0.5),
                    'signal_metrics': signal_assessment.get('signal_metrics', {}),
                    'assessment_grade': signal_assessment.get('quality_assessment', {}).get('quality_grade', 'fair')
                }
            else:
                return {
                    'quality_available': False,
                    'quality_score': 0.5,
                    'signal_metrics': {},
                    'assessment_grade': 'unknown'
                }

        except Exception as e:
            self.logger.error(f"❌ 信號品質評估失敗: {e}")
            return {'quality_available': False, 'quality_score': 0.5}

    def _assess_backup_coverage_contribution(self, satellite: Dict) -> float:
        """評估備份覆蓋貢獻度"""
        try:
            # 簡化實現：基於衛星類型和軌道高度
            constellation = satellite.get('constellation', 'unknown').lower()

            if constellation == 'starlink':
                return 0.8  # Starlink通常有較好的覆蓋
            elif constellation == 'oneweb':
                return 0.7  # OneWeb也有良好覆蓋
            else:
                return 0.6  # 其他星座的預設評估

        except Exception as e:
            self.logger.error(f"❌ 覆蓋貢獻評估失敗: {e}")
            return 0.6

    def _assess_backup_orbital_stability(self, satellite: Dict) -> float:
        """評估備份軌道穩定性"""
        # 簡化實現：假設大部分現代衛星都相對穩定
        return 0.85

    def _grade_backup_suitability(self, score: float) -> str:
        """為備份適用性評分分級"""
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'fair'
        else:
            return 'poor'

    def _recommend_backup_role(self, evaluation_score: float, signal_assessment: Dict) -> str:
        """推薦備份角色"""
        if evaluation_score >= 0.8 and signal_assessment.get('quality_score', 0) >= 0.8:
            return 'primary_backup'
        elif evaluation_score >= 0.6:
            return 'secondary_backup'
        else:
            return 'standby_backup'

    def _categorize_backup_satellites(self, backups: List[Dict]) -> Dict:
        """將備份衛星分類"""
        categories = {
            'primary_backups': [],
            'secondary_backups': [],
            'standby_backups': []
        }

        for backup in backups:
            role = backup.get('recommended_role', 'standby_backup')
            if role in categories:
                categories[role].append(backup)

        return categories

    def _assess_switching_readiness(self, backups: List[Dict]) -> Dict:
        """評估切換就緒狀態"""
        ready_count = len([b for b in backups if b.get('backup_suitability_grade') in ['excellent', 'good']])

        return {
            'total_backups': len(backups),
            'ready_backups': ready_count,
            'readiness_percentage': (ready_count / len(backups) * 100) if backups else 0,
            'overall_readiness': 'high' if ready_count >= len(backups) * 0.7 else 'medium'
        }

    def _establish_performance_baseline(self, backups: List[Dict]) -> Dict:
        """建立性能基準線"""
        if not backups:
            return {}

        evaluation_scores = [b.get('evaluation_score', 0.5) for b in backups]

        return {
            'baseline_timestamp': datetime.now(timezone.utc).isoformat(),
            'average_evaluation_score': np.mean(evaluation_scores),
            'minimum_acceptable_score': 0.6,
            'baseline_satellite_count': len(backups),
            'performance_variance': np.var(evaluation_scores)
        }

    def _calculate_candidates_orbital_diversity(self, candidates: List[Dict]) -> float:
        """計算候選衛星軌道多樣性"""
        try:
            # 提取軌道元素
            satellites = [c['satellite_data'] for c in candidates]
            orbital_elements = self.orbital_calc.extract_orbital_elements(satellites)

            if not orbital_elements:
                return 0.5

            # 使用軌道計算核心計算多樣性
            return self.orbital_calc.calculate_constellation_phase_diversity(orbital_elements)

        except Exception as e:
            self.logger.error(f"❌ 軌道多樣性計算失敗: {e}")
            return 0.5

    def _establish_switching_priorities(self, backup_pool: List[Dict]) -> List[Dict]:
        """建立切換優先級"""
        priorities = []

        for i, backup in enumerate(backup_pool):
            priority = {
                'priority_rank': i + 1,
                'satellite_id': backup.get('satellite_id'),
                'evaluation_score': backup.get('evaluation_score', 0.5),
                'readiness_score': backup.get('evaluation_score', 0.5) * 0.9,  # 稍微降低作為就緒分數
                'readiness_status': 'ready' if backup.get('evaluation_score', 0) > 0.6 else 'standby',
                'estimated_switching_time_seconds': 5 + i  # 優先級越低切換時間稍長
            }
            priorities.append(priority)

        return priorities

    def _assess_mechanism_reliability(self, priorities: List[Dict]) -> float:
        """評估機制可靠性"""
        if not priorities:
            return 0.0

        ready_ratio = len([p for p in priorities if p['readiness_status'] == 'ready']) / len(priorities)
        avg_readiness = np.mean([p['readiness_score'] for p in priorities])

        return (ready_ratio * 0.6 + avg_readiness * 0.4)

    def _establish_monitoring_baseline(self, targets: List[Dict]) -> Dict:
        """建立監控基準線"""
        return {
            'baseline_established': datetime.now(timezone.utc).isoformat(),
            'target_count': len(targets),
            'baseline_coverage_expectation': 0.95,
            'baseline_signal_threshold': -110.0,
            'baseline_availability_threshold': 0.95
        }

    def _assess_coverage_adequacy(self, metrics: Dict) -> str:
        """評估覆蓋充足性"""
        satellite_count = metrics.get('covering_satellite_count', 0)

        if satellite_count >= 3:
            return 'excellent'
        elif satellite_count >= 2:
            return 'good'
        elif satellite_count >= 1:
            return 'adequate'
        else:
            return 'insufficient'

    def _calculate_trend_direction(self, data: List[float]) -> str:
        """計算趨勢方向"""
        if len(data) < 3:
            return 'stable'

        # 簡單線性趨勢計算
        x = list(range(len(data)))
        slope = np.polyfit(x, data, 1)[0]

        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'

    def _calculate_stability_score(self, coverage_counts: List[float], coverage_qualities: List[float]) -> float:
        """計算穩定性分數"""
        try:
            count_variance = self.calculate_variance(coverage_counts)
            quality_variance = self.calculate_variance(coverage_qualities)

            # 變異數越小，穩定性越高
            count_stability = max(0, 1 - count_variance / 10)  # 假設10為高變異數
            quality_stability = max(0, 1 - quality_variance / 100)  # 假設100為高變異數

            return (count_stability + quality_stability) / 2

        except Exception:
            return 0.5

    def _detect_anomaly_periods(self, predictions: List[Dict]) -> List[Dict]:
        """檢測異常期間"""
        anomalies = []

        for i, pred in enumerate(predictions):
            covering_count = pred['coverage_metrics']['covering_satellite_count']
            avg_quality = pred['coverage_metrics']['average_coverage_quality']

            if covering_count == 0:
                anomalies.append({
                    'anomaly_type': 'coverage_gap',
                    'time': pred['target_time'],
                    'severity': 'critical'
                })
            elif avg_quality < 10.0 and covering_count > 0:
                anomalies.append({
                    'anomaly_type': 'quality_degradation',
                    'time': pred['target_time'],
                    'severity': 'warning',
                    'quality_value': avg_quality
                })

        return anomalies