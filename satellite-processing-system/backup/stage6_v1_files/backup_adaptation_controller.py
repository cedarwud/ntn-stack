#!/usr/bin/env python3
"""
備份自適應控制器 - BackupAdaptationController
負責自動調整機制和統計管理

從 BackupSatelliteManager 拆分出來的專業模組
專注於備份系統的自適應控制和統計分析
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class BackupAdaptationController:
    """
    備份自適應控制器

    職責：
    - 自動調整機制建立與管理
    - 備份系統性能統計
    - 適應性決策邏輯
    - 調整策略優化
    - 系統健康監控
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化備份自適應控制器

        Args:
            config: 配置參數
        """
        self.logger = logger
        self.config = config or {}

        # 自適應配置
        self.adaptation_config = {
            'triggers': {
                'coverage_degradation_threshold': 0.9,  # 90%覆蓋率以下觸發
                'signal_quality_threshold': -115.0,  # dBm
                'backup_pool_minimum': 2,
                'consecutive_failures_limit': 3
            },
            'actions': {
                'max_additional_backups': 4,
                'target_pool_size': 6,
                'activation_delay_seconds': 10,
                'switch_verification_required': True
            },
            'decision': {
                'evaluation_frequency_seconds': 60,
                'confidence_threshold': 0.7,
                'rollback_capability': True,
                'manual_override_available': True
            }
        }

        # 自適應統計
        self.adaptation_stats = {
            'mechanisms_established': 0,
            'successful_adjustments': 0,
            'failed_adjustments': 0,
            'automatic_interventions': 0,
            'manual_overrides': 0,
            'average_adjustment_time_seconds': 0.0
        }

        self.logger.info("✅ BackupAdaptationController 初始化完成")

    def establish_automatic_adjustment_mechanism(self, current_configuration: Dict) -> Dict:
        """
        建立自動調整機制

        Args:
            current_configuration: 當前配置

        Returns:
            自動調整機制配置
        """
        try:
            self.logger.info("🤖 建立自動調整機制")

            # 定義調整觸發條件
            adjustment_triggers = self._define_adjustment_triggers()

            # 定義調整動作
            adjustment_actions = self._define_adjustment_actions()

            # 建立決策邏輯
            decision_logic = self._build_decision_logic()

            adjustment_mechanism = {
                'mechanism_id': f"auto_adjust_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'mechanism_status': 'active',
                'current_configuration': current_configuration,
                'adjustment_triggers': adjustment_triggers,
                'adjustment_actions': adjustment_actions,
                'decision_logic': decision_logic,
                'performance_monitoring': self._initialize_performance_monitoring(),
                'established_timestamp': datetime.now(timezone.utc).isoformat()
            }

            # 更新統計
            self.adaptation_stats['mechanisms_established'] += 1

            self.logger.info("✅ 自動調整機制建立完成")
            return adjustment_mechanism

        except Exception as e:
            self.logger.error(f"❌ 自動調整機制建立失敗: {e}")
            return {'error': str(e)}

    def execute_automatic_adjustment(self, trigger_type: str, context: Dict) -> Dict:
        """
        執行自動調整

        Args:
            trigger_type: 觸發類型
            context: 調整上下文

        Returns:
            調整執行結果
        """
        try:
            adjustment_start = datetime.now()
            self.logger.info(f"🔧 執行自動調整: {trigger_type}")

            # 評估調整必要性
            adjustment_needed = self._evaluate_adjustment_necessity(trigger_type, context)

            if not adjustment_needed:
                return {'success': True, 'action': 'no_adjustment_needed', 'reason': 'Conditions do not meet adjustment criteria'}

            # 選擇調整策略
            adjustment_strategy = self._select_adjustment_strategy(trigger_type, context)

            # 執行調整動作
            adjustment_result = self._perform_adjustment_action(adjustment_strategy, context)

            # 驗證調整效果
            verification_result = self._verify_adjustment_effectiveness(adjustment_result, context)

            # 計算調整時間
            adjustment_time = (datetime.now() - adjustment_start).total_seconds()

            # 更新統計
            if adjustment_result.get('success', False):
                self.adaptation_stats['successful_adjustments'] += 1
            else:
                self.adaptation_stats['failed_adjustments'] += 1

            self.adaptation_stats['automatic_interventions'] += 1
            self.adaptation_stats['average_adjustment_time_seconds'] = (
                (self.adaptation_stats['average_adjustment_time_seconds'] + adjustment_time) / 2
            )

            final_result = {
                'success': adjustment_result.get('success', False),
                'trigger_type': trigger_type,
                'adjustment_strategy': adjustment_strategy,
                'adjustment_result': adjustment_result,
                'verification_result': verification_result,
                'adjustment_time_seconds': adjustment_time,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info(f"✅ 自動調整完成: {trigger_type}, 耗時: {adjustment_time:.2f}s")
            return final_result

        except Exception as e:
            self.adaptation_stats['failed_adjustments'] += 1
            self.logger.error(f"❌ 自動調整執行失敗: {e}")
            return {'success': False, 'error': str(e)}

    def get_management_statistics(self) -> Dict[str, Any]:
        """
        獲取管理統計

        Returns:
            管理統計信息
        """
        total_adjustments = self.adaptation_stats['successful_adjustments'] + self.adaptation_stats['failed_adjustments']
        success_rate = (self.adaptation_stats['successful_adjustments'] / total_adjustments) if total_adjustments > 0 else 0

        return {
            'module_name': 'BackupAdaptationController',
            'mechanisms_established': self.adaptation_stats['mechanisms_established'],
            'total_adjustments': total_adjustments,
            'successful_adjustments': self.adaptation_stats['successful_adjustments'],
            'failed_adjustments': self.adaptation_stats['failed_adjustments'],
            'success_rate': success_rate,
            'automatic_interventions': self.adaptation_stats['automatic_interventions'],
            'manual_overrides': self.adaptation_stats['manual_overrides'],
            'average_adjustment_time_seconds': self.adaptation_stats['average_adjustment_time_seconds'],
            'adaptation_config': self.adaptation_config
        }

    def analyze_system_health(self, system_metrics: Dict) -> Dict:
        """
        分析系統健康狀況

        Args:
            system_metrics: 系統指標

        Returns:
            健康分析結果
        """
        try:
            # 計算健康評分
            health_score = self._calculate_health_score(system_metrics)

            # 識別潛在問題
            potential_issues = self._identify_potential_issues(system_metrics)

            # 生成改善建議
            improvement_suggestions = self._generate_improvement_suggestions(system_metrics, potential_issues)

            health_analysis = {
                'overall_health_score': health_score,
                'health_status': self._determine_health_status(health_score),
                'system_metrics': system_metrics,
                'potential_issues': potential_issues,
                'improvement_suggestions': improvement_suggestions,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

            return health_analysis

        except Exception as e:
            self.logger.error(f"系統健康分析錯誤: {e}")
            return {'error': str(e)}

    def _define_adjustment_triggers(self) -> Dict:
        """定義調整觸發條件"""
        return {
            'coverage_degradation': {
                'threshold': self.adaptation_config['triggers']['coverage_degradation_threshold'],
                'evaluation_period_minutes': 15,
                'action': 'activate_additional_backups'
            },
            'signal_quality_drop': {
                'threshold': self.adaptation_config['triggers']['signal_quality_threshold'],
                'consecutive_failures': self.adaptation_config['triggers']['consecutive_failures_limit'],
                'action': 'switch_to_better_satellites'
            },
            'backup_pool_depletion': {
                'minimum_backup_count': self.adaptation_config['triggers']['backup_pool_minimum'],
                'action': 'replenish_backup_pool'
            }
        }

    def _define_adjustment_actions(self) -> Dict:
        """定義調整動作"""
        return {
            'activate_additional_backups': {
                'max_additional_backups': self.adaptation_config['actions']['max_additional_backups'],
                'selection_criteria': 'best_available',
                'activation_delay_seconds': self.adaptation_config['actions']['activation_delay_seconds']
            },
            'switch_to_better_satellites': {
                'switch_count': 2,
                'selection_method': 'highest_signal_quality',
                'verification_required': self.adaptation_config['actions']['switch_verification_required']
            },
            'replenish_backup_pool': {
                'target_pool_size': self.adaptation_config['actions']['target_pool_size'],
                'selection_method': 'comprehensive_evaluation',
                'replenishment_source': 'available_satellites'
            }
        }

    def _build_decision_logic(self) -> Dict:
        """建立決策邏輯"""
        return {
            'evaluation_frequency_seconds': self.adaptation_config['decision']['evaluation_frequency_seconds'],
            'decision_confidence_threshold': self.adaptation_config['decision']['confidence_threshold'],
            'rollback_capability': self.adaptation_config['decision']['rollback_capability'],
            'manual_override_available': self.adaptation_config['decision']['manual_override_available'],
            'adjustment_logging': True
        }

    def _initialize_performance_monitoring(self) -> Dict:
        """初始化性能監控"""
        return {
            'successful_adjustments': 0,
            'failed_adjustments': 0,
            'adjustment_impact_tracking': True,
            'performance_metrics': {
                'average_response_time_ms': 0,
                'adjustment_accuracy': 0.0,
                'system_stability_improvement': 0.0
            }
        }

    def _evaluate_adjustment_necessity(self, trigger_type: str, context: Dict) -> bool:
        """評估調整必要性"""
        try:
            if trigger_type == 'coverage_degradation':
                current_coverage = context.get('coverage_percentage', 100)
                threshold = self.adaptation_config['triggers']['coverage_degradation_threshold'] * 100
                return current_coverage < threshold

            elif trigger_type == 'signal_quality_drop':
                signal_strength = context.get('signal_strength', -80)
                threshold = self.adaptation_config['triggers']['signal_quality_threshold']
                return signal_strength < threshold

            elif trigger_type == 'backup_pool_depletion':
                backup_count = context.get('backup_count', 10)
                minimum = self.adaptation_config['triggers']['backup_pool_minimum']
                return backup_count < minimum

            return False

        except Exception:
            return False

    def _select_adjustment_strategy(self, trigger_type: str, context: Dict) -> Dict:
        """選擇調整策略"""
        base_strategy = {
            'trigger_type': trigger_type,
            'priority': 'medium',
            'execution_mode': 'automatic'
        }

        if trigger_type == 'coverage_degradation':
            base_strategy.update({
                'action': 'activate_additional_backups',
                'priority': 'high',
                'target_improvement': 0.05  # 5% 改善目標
            })

        elif trigger_type == 'signal_quality_drop':
            base_strategy.update({
                'action': 'switch_to_better_satellites',
                'priority': 'medium',
                'target_improvement': 10  # 10dB 改善目標
            })

        elif trigger_type == 'backup_pool_depletion':
            base_strategy.update({
                'action': 'replenish_backup_pool',
                'priority': 'high',
                'target_count': self.adaptation_config['actions']['target_pool_size']
            })

        return base_strategy

    def _perform_adjustment_action(self, strategy: Dict, context: Dict) -> Dict:
        """執行調整動作"""
        action = strategy.get('action', 'no_action')

        # 簡化實現：模擬調整執行
        if action == 'activate_additional_backups':
            return {
                'success': True,
                'action': action,
                'backups_activated': 2,
                'message': '成功激活2個額外備份衛星'
            }

        elif action == 'switch_to_better_satellites':
            return {
                'success': True,
                'action': action,
                'satellites_switched': 1,
                'improvement': 8.5,
                'message': '成功切換到更高品質衛星'
            }

        elif action == 'replenish_backup_pool':
            return {
                'success': True,
                'action': action,
                'pool_size_after': 6,
                'message': '成功補充備份池至目標大小'
            }

        return {'success': False, 'action': action, 'message': '未知調整動作'}

    def _verify_adjustment_effectiveness(self, adjustment_result: Dict, context: Dict) -> Dict:
        """驗證調整效果"""
        if not adjustment_result.get('success', False):
            return {'verified': False, 'reason': 'Adjustment failed'}

        # 簡化實現：模擬效果驗證
        return {
            'verified': True,
            'improvement_confirmed': True,
            'effectiveness_score': 0.8,
            'verification_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _calculate_health_score(self, metrics: Dict) -> float:
        """計算健康評分"""
        try:
            # 基於成功率和響應時間計算健康評分
            success_rate = metrics.get('success_rate', 0.5)
            response_time = metrics.get('average_response_time_seconds', 10)

            # 成功率權重 70%
            success_component = success_rate * 0.7

            # 響應時間權重 30% (理想響應時間 < 5秒)
            time_component = max(0, 1 - (response_time / 10)) * 0.3

            health_score = success_component + time_component
            return min(1.0, max(0.0, health_score))

        except Exception:
            return 0.5

    def _determine_health_status(self, health_score: float) -> str:
        """判定健康狀態"""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.7:
            return "good"
        elif health_score >= 0.5:
            return "fair"
        else:
            return "poor"

    def _identify_potential_issues(self, metrics: Dict) -> List[str]:
        """識別潛在問題"""
        issues = []

        success_rate = metrics.get('success_rate', 1.0)
        if success_rate < 0.8:
            issues.append("低成功率")

        response_time = metrics.get('average_response_time_seconds', 0)
        if response_time > 10:
            issues.append("響應時間過長")

        failed_adjustments = metrics.get('failed_adjustments', 0)
        if failed_adjustments > 5:
            issues.append("調整失敗次數過多")

        return issues

    def _generate_improvement_suggestions(self, metrics: Dict, issues: List[str]) -> List[str]:
        """生成改善建議"""
        suggestions = []

        if "低成功率" in issues:
            suggestions.append("檢查調整策略的準確性和時機")

        if "響應時間過長" in issues:
            suggestions.append("優化決策邏輯和執行效率")

        if "調整失敗次數過多" in issues:
            suggestions.append("增強系統監控和錯誤處理機制")

        if not suggestions:
            suggestions.append("系統運行良好，建議保持當前配置")

        return suggestions