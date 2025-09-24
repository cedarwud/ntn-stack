#!/usr/bin/env python3
"""
備份衛星管理器 - BackupSatelliteManager (重構版)
協調器模式實現，委派給專業模組

重構後的協調器負責：
- 統一接口維護 (向後兼容)
- 模組間協調
- 統一配置管理
- 統計信息聚合
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# 導入專業模組
try:
    from .backup_pool_manager import BackupPoolManager
    from .backup_switching_engine import BackupSwitchingEngine
    from .backup_monitoring_service import BackupMonitoringService
    from .backup_adaptation_controller import BackupAdaptationController
except ImportError:
    from backup_pool_manager import BackupPoolManager
    from backup_switching_engine import BackupSwitchingEngine
    from backup_monitoring_service import BackupMonitoringService
    from backup_adaptation_controller import BackupAdaptationController

try:
    from ...shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore
except ImportError:
    from shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore

logger = logging.getLogger(__name__)

class BackupSatelliteManager:
    """
    備份衛星管理器 - 協調器模式

    重構設計：
    - 保持原有公開接口，確保向後兼容
    - 內部委派給四個專業模組
    - 統一配置和統計管理
    - 提供模組間協調功能
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
            actual_observer_config = observer_config['observer']
        else:
            actual_observer_config = observer_config

        # 初始化共享核心模組 (保持向後兼容)
        self.orbital_calc = OrbitalCalculationsCore(actual_observer_config)
        self.visibility_calc = VisibilityCalculationsCore(actual_observer_config)
        self.signal_calc = SignalCalculationsCore()

        # 統一配置 (整合四個模組的配置需求)
        self.unified_config = self._build_unified_config(observer_config)

        # 初始化專業模組
        self.pool_manager = BackupPoolManager(self.unified_config)
        self.switching_engine = BackupSwitchingEngine(self.unified_config)
        self.monitoring_service = BackupMonitoringService(self.unified_config)
        self.adaptation_controller = BackupAdaptationController(self.unified_config)

        # 備份管理配置 (保持向後兼容)
        self.backup_config = {
            'pool_management': {
                'default_pool_size': 6,
                'minimum_pool_size': 3,
                'maximum_pool_size': 12,
                'backup_ratio': 0.25
            },
            'switching_criteria': {
                'signal_degradation_threshold': -110.0,
                'elevation_minimum': 5.0,
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

        # 當前備份池狀態 (保持向後兼容)
        self.backup_pool = {
            'active_backups': [],
            'standby_backups': [],
            'degraded_backups': [],
            'pool_status': 'initializing'
        }

        # 管理統計 (聚合四個模組的統計)
        self.management_stats = {
            'backup_pools_established': 0,
            'successful_switches': 0,
            'failed_switches': 0,
            'coverage_predictions': 0,
            'automatic_adjustments': 0,
            'alerts_generated': 0
        }

        self.logger.info("🔄 備份衛星管理器初始化完成 (協調器模式)")

    # ==================== 公開接口方法 (保持向後兼容) ====================

    def establish_backup_satellite_pool(self, satellites: List[Dict],
                                      primary_selection: List[Dict] = None) -> Dict:
        """
        建立備份衛星池 (委派給 BackupPoolManager)

        Args:
            satellites: 候選衛星列表
            primary_selection: 主要選擇的衛星 (用於避免重複)

        Returns:
            備份池建立結果
        """
        try:
            # 委派給專業模組
            result = self.pool_manager.establish_backup_satellite_pool(satellites, primary_selection)

            # 更新協調器狀態
            if 'backup_satellites' in result:
                self.backup_pool['active_backups'] = result['backup_satellites']
                self.backup_pool['pool_status'] = 'operational'
                self.management_stats['backup_pools_established'] += 1

            return result

        except Exception as e:
            self.logger.error(f"❌ 備份衛星池建立失敗 (協調器): {e}")
            return {'error': str(e)}

    def implement_intelligent_backup_evaluation(self, candidates: List[Dict]) -> Dict:
        """
        實施智能備份評估 (委派給 BackupPoolManager)

        Args:
            candidates: 備份候選衛星列表

        Returns:
            評估結果
        """
        return self.pool_manager.implement_intelligent_backup_evaluation(candidates)

    def establish_rapid_switching_mechanism(self, backup_pool: List[Dict]) -> Dict:
        """
        建立快速切換機制 (委派給 BackupSwitchingEngine)

        Args:
            backup_pool: 備份衛星池

        Returns:
            快速切換機制配置
        """
        return self.switching_engine.establish_rapid_switching_mechanism(backup_pool)

    def establish_real_time_coverage_monitoring(self, monitoring_targets: List[Dict]) -> Dict:
        """
        建立即時覆蓋監控 (委派給 BackupMonitoringService)

        Args:
            monitoring_targets: 監控目標列表

        Returns:
            即時監控系統配置
        """
        return self.monitoring_service.establish_real_time_coverage_monitoring(monitoring_targets)

    def calculate_expected_coverage_at_time(self, satellites: List[Dict], target_time: datetime) -> Dict:
        """
        計算指定時間的預期覆蓋 (委派給 BackupMonitoringService)

        Args:
            satellites: 衛星列表
            target_time: 目標時間

        Returns:
            預期覆蓋情況
        """
        return self.monitoring_service.calculate_expected_coverage_at_time(satellites, target_time)

    def implement_predictive_coverage_analysis(self, satellites: List[Dict]) -> Dict:
        """
        實施預測性覆蓋分析 (委派給 BackupMonitoringService)

        Args:
            satellites: 衛星數據列表

        Returns:
            預測性覆蓋分析結果
        """
        result = self.monitoring_service.implement_predictive_coverage_analysis(satellites)

        # 更新統計
        if 'coverage_predictions' in result:
            self.management_stats['coverage_predictions'] += 1

        return result

    def analyze_coverage_trends(self, coverage_data: List[Dict]) -> Dict:
        """
        分析覆蓋趨勢 (委派給 BackupMonitoringService)

        Args:
            coverage_data: 覆蓋數據序列

        Returns:
            趨勢分析結果
        """
        return self.monitoring_service.analyze_coverage_trends(coverage_data)

    def calculate_variance(self, values: List[float]) -> float:
        """
        計算變異數 (委派給 BackupMonitoringService)

        Args:
            values: 數值列表

        Returns:
            變異數
        """
        return self.monitoring_service.calculate_variance(values)

    def generate_predictive_alerts(self, coverage_predictions: List[Dict], trend_analysis: Dict) -> List[Dict]:
        """
        生成預測性警報 (委派給 BackupMonitoringService)

        Args:
            coverage_predictions: 覆蓋預測數據
            trend_analysis: 趨勢分析結果

        Returns:
            預測性警報列表
        """
        alerts = self.monitoring_service.generate_predictive_alerts(coverage_predictions, trend_analysis)

        # 更新統計
        self.management_stats['alerts_generated'] += len(alerts)

        return alerts

    def establish_automatic_adjustment_mechanism(self, current_configuration: Dict) -> Dict:
        """
        建立自動調整機制 (委派給 BackupAdaptationController)

        Args:
            current_configuration: 當前配置

        Returns:
            自動調整機制配置
        """
        return self.adaptation_controller.establish_automatic_adjustment_mechanism(current_configuration)

    def get_management_statistics(self) -> Dict[str, Any]:
        """
        獲取管理統計 (聚合四個模組的統計)

        Returns:
            聚合的管理統計信息
        """
        # 聚合各模組統計
        aggregated_stats = {
            'coordinator_stats': self.management_stats.copy(),
            'pool_manager_stats': self.pool_manager.get_pool_statistics(),
            'switching_engine_stats': self.switching_engine.get_switching_statistics(),
            'monitoring_service_stats': self.monitoring_service.get_monitoring_statistics(),
            'adaptation_controller_stats': self.adaptation_controller.get_management_statistics()
        }

        # 計算總體統計
        total_stats = {
            'module_name': 'BackupSatelliteManager_Coordinator',
            'architecture': 'modular_coordinator',
            'total_pools_established': self.management_stats['backup_pools_established'],
            'total_successful_switches': self.management_stats['successful_switches'],
            'total_failed_switches': self.management_stats['failed_switches'],
            'total_predictions': self.management_stats['coverage_predictions'],
            'total_adjustments': self.management_stats['automatic_adjustments'],
            'total_alerts': self.management_stats['alerts_generated'],
            'module_statistics': aggregated_stats
        }

        return total_stats

    # ==================== 協調器專用方法 ====================

    def execute_coordinated_backup_operation(self, operation_type: str, parameters: Dict) -> Dict:
        """
        執行協調的備份操作 (跨模組協調)

        Args:
            operation_type: 操作類型
            parameters: 操作參數

        Returns:
            協調操作結果
        """
        try:
            self.logger.info(f"🔄 執行協調備份操作: {operation_type}")

            if operation_type == 'full_backup_lifecycle':
                return self._execute_full_backup_lifecycle(parameters)
            elif operation_type == 'emergency_backup_activation':
                return self._execute_emergency_backup_activation(parameters)
            elif operation_type == 'predictive_adjustment':
                return self._execute_predictive_adjustment(parameters)
            else:
                return {'error': f'Unknown operation type: {operation_type}'}

        except Exception as e:
            self.logger.error(f"❌ 協調備份操作失敗: {e}")
            return {'error': str(e)}

    def _execute_full_backup_lifecycle(self, parameters: Dict) -> Dict:
        """執行完整備份生命週期"""
        # 1. 建立備份池
        pool_result = self.pool_manager.establish_backup_satellite_pool(
            parameters.get('satellites', []),
            parameters.get('primary_selection', [])
        )

        if 'error' in pool_result:
            return pool_result

        # 2. 建立切換機制
        switch_result = self.switching_engine.establish_rapid_switching_mechanism(
            pool_result.get('backup_satellites', [])
        )

        # 3. 啟動監控
        monitor_result = self.monitoring_service.establish_real_time_coverage_monitoring(
            pool_result.get('backup_satellites', [])
        )

        # 4. 啟動自適應控制
        adapt_result = self.adaptation_controller.establish_automatic_adjustment_mechanism(
            parameters.get('configuration', {})
        )

        return {
            'lifecycle_completed': True,
            'pool_result': pool_result,
            'switching_result': switch_result,
            'monitoring_result': monitor_result,
            'adaptation_result': adapt_result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _execute_emergency_backup_activation(self, parameters: Dict) -> Dict:
        """執行緊急備份激活"""
        # 緊急情況下的快速備份激活
        emergency_satellites = parameters.get('emergency_satellites', [])

        if not emergency_satellites:
            return {'error': 'No emergency satellites provided'}

        # 快速切換到緊急備份
        switch_result = self.switching_engine.execute_satellite_switch(
            parameters.get('current_satellite', {}),
            emergency_satellites[0]  # 選擇第一個緊急備份
        )

        return {
            'emergency_activation_completed': True,
            'switch_result': switch_result,
            'emergency_satellite': emergency_satellites[0].get('satellite_id'),
            'activation_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _execute_predictive_adjustment(self, parameters: Dict) -> Dict:
        """執行預測性調整"""
        # 基於預測結果進行自適應調整
        prediction_data = parameters.get('prediction_data', {})

        # 執行自動調整
        adjustment_result = self.adaptation_controller.execute_automatic_adjustment(
            parameters.get('trigger_type', 'predictive'),
            prediction_data
        )

        return {
            'predictive_adjustment_completed': True,
            'adjustment_result': adjustment_result,
            'prediction_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _build_unified_config(self, base_config: Optional[Dict]) -> Dict:
        """構建統一配置 (整合四個模組需求)"""
        return {
            'observer': base_config.get('observer') if base_config and 'observer' in base_config else base_config,
            'pool_management': {
                'default_pool_size': 6,
                'evaluation_criteria_weights': {
                    'signal_quality': 0.4,
                    'coverage_contribution': 0.3,
                    'orbital_stability': 0.2,
                    'diversity': 0.1
                }
            },
            'switching': {
                'detection_latency_target_ms': 500,
                'max_switching_time_seconds': 10,
                'rollback_capability': True
            },
            'monitoring': {
                'prediction_horizon_hours': 2,
                'alert_threshold': 90.0,
                'update_intervals': {
                    'health_check_seconds': 30,
                    'prediction_minutes': 10
                }
            },
            'adaptation': {
                'evaluation_frequency_seconds': 60,
                'confidence_threshold': 0.7,
                'auto_adjustment_enabled': True
            }
        }

    # ==================== 向後兼容的私有方法存根 ====================
    # 這些方法被重構為委派給專業模組，但保持接口兼容

    def _calculate_backup_suitability_score(self, candidate: Dict) -> float:
        """委派給 BackupPoolManager"""
        return self.pool_manager._calculate_backup_suitability_score(candidate)

    def _assess_candidate_signal_quality(self, candidate: Dict) -> float:
        """委派給 BackupPoolManager"""
        return self.pool_manager._assess_candidate_signal_quality(candidate)

    def _assess_backup_coverage_contribution(self, candidate: Dict) -> float:
        """委派給 BackupPoolManager"""
        return self.pool_manager._assess_backup_coverage_contribution(candidate)

    def _assess_backup_orbital_stability(self, candidate: Dict) -> float:
        """委派給 BackupPoolManager"""
        return self.pool_manager._assess_backup_orbital_stability(candidate)

    def _grade_backup_suitability(self, score: float) -> str:
        """委派給 BackupPoolManager"""
        return self.pool_manager._grade_backup_suitability(score)

    def _recommend_backup_role(self, score: float) -> str:
        """委派給 BackupPoolManager"""
        return self.pool_manager._recommend_backup_role(score)

    def _categorize_backup_satellites(self, backup_satellites: List[Dict]) -> Dict:
        """委派給 BackupPoolManager"""
        return self.pool_manager._categorize_backup_satellites(backup_satellites)