#!/usr/bin/env python3
"""
備份監控服務 - BackupMonitoringService
負責實時監控、預測分析和異常檢測

從 BackupSatelliteManager 拆分出來的專業模組
專注於備份衛星的監控和預測功能
"""
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class BackupMonitoringService:
    """
    備份監控服務

    職責：
    - 實時覆蓋監控
    - 預測性覆蓋分析
    - 覆蓋趨勢分析
    - 預測性警報生成
    - 異常檢測和處理
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化備份監控服務

        Args:
            config: 配置參數
        """
        self.logger = logger
        self.config = config or {}

        # 監控配置
        self.monitoring_config = {
            'intervals': {
                'health_check_interval_seconds': 30,
                'performance_evaluation_interval_minutes': 5,
                'prediction_update_interval_minutes': 10
            },
            'thresholds': {
                'coverage_continuity_target': 95.0,
                'coverage_alert_threshold': 90.0,
                'signal_degradation_threshold': -110.0,
                'elevation_minimum': 5.0
            },
            'prediction': {
                'horizon_hours': 2,
                'verification_points': 240,
                'trend_analysis_window_minutes': 60
            }
        }

        # 監控統計
        self.monitoring_stats = {
            'monitoring_sessions_active': 0,
            'alerts_generated': 0,
            'predictions_made': 0,
            'anomalies_detected': 0,
            'average_coverage_percentage': 0.0
        }

        self.logger.info("✅ BackupMonitoringService 初始化完成")

    def establish_real_time_coverage_monitoring(self, monitoring_targets: List[Dict]) -> Dict:
        """
        建立即時覆蓋監控

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
                'monitoring_interval_seconds': self.monitoring_config['intervals']['health_check_interval_seconds'],
                'performance_evaluation_interval_minutes': self.monitoring_config['intervals']['performance_evaluation_interval_minutes'],
                'coverage_prediction_enabled': True,
                'real_time_alerts_enabled': True
            }

            # 建立監控指標
            monitoring_metrics = self._build_monitoring_metrics()

            # 配置預測性監控
            predictive_monitoring = self.implement_predictive_coverage_analysis(monitoring_targets)

            # 建立警報系統
            alert_system = self._configure_alert_system()

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

            # 更新統計
            self.monitoring_stats['monitoring_sessions_active'] += 1

            self.logger.info("✅ 即時覆蓋監控系統建立完成")
            return monitoring_system

        except Exception as e:
            self.logger.error(f"❌ 即時覆蓋監控建立失敗: {e}")
            return {'error': str(e)}

    def implement_predictive_coverage_analysis(self, satellites: List[Dict]) -> Dict:
        """
        實施預測性覆蓋分析

        Args:
            satellites: 衛星數據列表

        Returns:
            預測性覆蓋分析結果
        """
        try:
            self.logger.info("🔮 實施預測性覆蓋分析")

            if not satellites:
                return {'error': 'No satellites provided for predictive analysis'}

            # 計算預測時間範圍
            prediction_horizon = self.monitoring_config['prediction']['horizon_hours']
            current_time = datetime.now(timezone.utc)
            prediction_end_time = current_time + timedelta(hours=prediction_horizon)

            # 生成時間序列預測點
            time_points = self._generate_prediction_time_points(current_time, prediction_end_time)

            # 預測覆蓋情況
            coverage_predictions = []
            for time_point in time_points:
                expected_coverage = self.calculate_expected_coverage_at_time(satellites, time_point)
                coverage_predictions.append({
                    'timestamp': time_point.isoformat(),
                    'expected_coverage': expected_coverage
                })

            # 分析覆蓋趨勢
            trend_analysis = self.analyze_coverage_trends(coverage_predictions)

            # 生成預測性警報
            predictive_alerts = self.generate_predictive_alerts(coverage_predictions, trend_analysis)

            predictive_analysis = {
                'analysis_id': f"pred_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'prediction_horizon_hours': prediction_horizon,
                'total_satellites_analyzed': len(satellites),
                'coverage_predictions': coverage_predictions,
                'trend_analysis': trend_analysis,
                'predictive_alerts': predictive_alerts,
                'analysis_timestamp': current_time.isoformat(),
                'analysis_summary': {
                    'average_predicted_coverage': np.mean([p['expected_coverage']['coverage_percentage'] for p in coverage_predictions]),
                    'minimum_predicted_coverage': min([p['expected_coverage']['coverage_percentage'] for p in coverage_predictions]),
                    'coverage_stability': trend_analysis.get('stability_score', 0.0),
                    'alerts_count': len(predictive_alerts)
                }
            }

            # 更新統計
            self.monitoring_stats['predictions_made'] += 1

            self.logger.info(f"✅ 預測性覆蓋分析完成，生成 {len(coverage_predictions)} 個預測點")
            return predictive_analysis

        except Exception as e:
            self.logger.error(f"❌ 預測性覆蓋分析失敗: {e}")
            return {'error': str(e)}

    def calculate_expected_coverage_at_time(self, satellites: List[Dict], target_time: datetime) -> Dict:
        """
        計算指定時間的預期覆蓋

        Args:
            satellites: 衛星列表
            target_time: 目標時間

        Returns:
            預期覆蓋情況
        """
        try:
            visible_satellites = []
            total_signal_strength = 0
            coverage_quality_scores = []

            for satellite in satellites:
                # 簡化實現：基於當前位置預測未來可見性
                if self._predict_satellite_visibility(satellite, target_time):
                    visible_satellites.append(satellite)

                    # 計算預期信號強度
                    signal_strength = self._predict_signal_strength(satellite, target_time)
                    total_signal_strength += signal_strength
                    coverage_quality_scores.append(signal_strength)

            coverage_percentage = (len(visible_satellites) / len(satellites) * 100) if satellites else 0
            average_signal_strength = total_signal_strength / len(visible_satellites) if visible_satellites else 0

            coverage_assessment = self._assess_coverage_adequacy(coverage_percentage, average_signal_strength)

            return {
                'target_time': target_time.isoformat(),
                'visible_satellites_count': len(visible_satellites),
                'total_satellites': len(satellites),
                'coverage_percentage': coverage_percentage,
                'average_signal_strength': average_signal_strength,
                'coverage_quality': np.mean(coverage_quality_scores) if coverage_quality_scores else 0,
                'coverage_adequacy': coverage_assessment,
                'visible_satellite_ids': [sat.get('satellite_id') for sat in visible_satellites]
            }

        except Exception as e:
            self.logger.error(f"預期覆蓋計算錯誤: {e}")
            return {'error': str(e)}

    def analyze_coverage_trends(self, coverage_data: List[Dict]) -> Dict:
        """
        分析覆蓋趨勢

        Args:
            coverage_data: 覆蓋數據序列

        Returns:
            趨勢分析結果
        """
        try:
            if len(coverage_data) < 2:
                return {'error': 'Insufficient data for trend analysis'}

            coverage_values = [data['expected_coverage']['coverage_percentage'] for data in coverage_data]

            # 計算趨勢方向
            trend_direction = self._calculate_trend_direction(coverage_values)

            # 計算變異數
            variance = self.calculate_variance(coverage_values)

            # 計算穩定性評分
            stability_score = self._calculate_stability_score(coverage_values)

            # 檢測異常時期
            anomaly_periods = self._detect_anomaly_periods(coverage_data)

            trend_analysis = {
                'data_points': len(coverage_data),
                'trend_direction': trend_direction,
                'variance': variance,
                'stability_score': stability_score,
                'average_coverage': np.mean(coverage_values),
                'minimum_coverage': min(coverage_values),
                'maximum_coverage': max(coverage_values),
                'anomaly_periods': anomaly_periods,
                'trend_confidence': self._calculate_trend_confidence(coverage_values)
            }

            return trend_analysis

        except Exception as e:
            self.logger.error(f"覆蓋趨勢分析錯誤: {e}")
            return {'error': str(e)}

    def generate_predictive_alerts(self, coverage_predictions: List[Dict], trend_analysis: Dict) -> List[Dict]:
        """
        生成預測性警報

        Args:
            coverage_predictions: 覆蓋預測數據
            trend_analysis: 趨勢分析結果

        Returns:
            預測性警報列表
        """
        try:
            alerts = []
            alert_threshold = self.monitoring_config['thresholds']['coverage_alert_threshold']

            # 檢查覆蓋率低於閾值的時間點
            for prediction in coverage_predictions:
                coverage_pct = prediction['expected_coverage']['coverage_percentage']

                if coverage_pct < alert_threshold:
                    alert = {
                        'alert_type': 'low_coverage_prediction',
                        'severity': 'warning' if coverage_pct > 80 else 'critical',
                        'timestamp': prediction['timestamp'],
                        'predicted_coverage': coverage_pct,
                        'threshold': alert_threshold,
                        'message': f"預測覆蓋率 {coverage_pct:.1f}% 低於閾值 {alert_threshold:.1f}%"
                    }
                    alerts.append(alert)

            # 檢查趨勢警報
            if trend_analysis.get('trend_direction') == 'declining':
                alerts.append({
                    'alert_type': 'declining_trend',
                    'severity': 'warning',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'trend_stability': trend_analysis.get('stability_score', 0),
                    'message': f"檢測到覆蓋率下降趨勢，穩定性評分: {trend_analysis.get('stability_score', 0):.2f}"
                })

            # 檢查異常時期警報
            anomaly_periods = trend_analysis.get('anomaly_periods', [])
            if anomaly_periods:
                alerts.append({
                    'alert_type': 'anomaly_detected',
                    'severity': 'warning',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'anomaly_count': len(anomaly_periods),
                    'message': f"檢測到 {len(anomaly_periods)} 個異常時期"
                })

            # 更新統計
            self.monitoring_stats['alerts_generated'] += len(alerts)

            return alerts

        except Exception as e:
            self.logger.error(f"預測性警報生成錯誤: {e}")
            return []

    def calculate_variance(self, values: List[float]) -> float:
        """計算變異數"""
        try:
            if len(values) < 2:
                return 0.0

            mean_value = np.mean(values)
            variance = np.mean([(x - mean_value) ** 2 for x in values])
            return variance

        except Exception:
            return 0.0

    def _build_monitoring_metrics(self) -> Dict:
        """建立監控指標"""
        return {
            'coverage_continuity': {
                'target_percentage': self.monitoring_config['thresholds']['coverage_continuity_target'],
                'measurement_method': 'time_based_analysis',
                'alert_threshold': self.monitoring_config['thresholds']['coverage_alert_threshold']
            },
            'signal_quality': {
                'rsrp_threshold': self.monitoring_config['thresholds']['signal_degradation_threshold'],
                'rsrq_threshold': -15.0,
                'sinr_threshold': 3.0,
                'degradation_alert_enabled': True
            },
            'satellite_availability': {
                'elevation_threshold': self.monitoring_config['thresholds']['elevation_minimum'],
                'visibility_prediction': True,
                'handover_preparation': True
            }
        }

    def _configure_alert_system(self) -> Dict:
        """配置警報系統"""
        return {
            'coverage_gap_alerts': True,
            'signal_degradation_alerts': True,
            'satellite_loss_alerts': True,
            'backup_activation_alerts': True,
            'alert_delivery_methods': ['log', 'system_event'],
            'alert_priority_levels': ['info', 'warning', 'critical', 'emergency']
        }

    def _establish_monitoring_baseline(self, targets: List[Dict]) -> Dict:
        """建立監控基準"""
        try:
            current_coverage = len([t for t in targets if self._is_currently_visible(t)]) / len(targets) if targets else 0

            return {
                'baseline_coverage_percentage': current_coverage * 100,
                'baseline_satellite_count': len(targets),
                'baseline_timestamp': datetime.now(timezone.utc).isoformat(),
                'baseline_quality_score': 0.75  # 預設品質評分
            }

        except Exception:
            return {'baseline_coverage_percentage': 0, 'baseline_satellite_count': 0}

    def _generate_prediction_time_points(self, start_time: datetime, end_time: datetime) -> List[datetime]:
        """生成預測時間點"""
        time_points = []
        current_time = start_time
        interval = timedelta(minutes=30)  # 30分鐘間隔

        while current_time <= end_time:
            time_points.append(current_time)
            current_time += interval

        return time_points

    def _predict_satellite_visibility(self, satellite: Dict, target_time: datetime) -> bool:
        """預測衛星可見性"""
        # 簡化實現：基於當前可見性狀態
        return satellite.get('position', {}).get('elevation', 0) > self.monitoring_config['thresholds']['elevation_minimum']

    def _predict_signal_strength(self, satellite: Dict, target_time: datetime) -> float:
        """預測信號強度"""
        # 簡化實現：基於當前信號強度
        current_rsrp = satellite.get('signal_data', {}).get('rsrp', -100)
        return max(0, min(1, (current_rsrp + 120) / 30))

    def _assess_coverage_adequacy(self, coverage_percentage: float, signal_strength: float) -> str:
        """評估覆蓋充足性"""
        if coverage_percentage >= 95 and signal_strength >= 0.7:
            return "excellent"
        elif coverage_percentage >= 90 and signal_strength >= 0.6:
            return "good"
        elif coverage_percentage >= 80:
            return "fair"
        else:
            return "poor"

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """計算趨勢方向"""
        if len(values) < 2:
            return "stable"

        recent_avg = np.mean(values[-3:]) if len(values) >= 3 else values[-1]
        early_avg = np.mean(values[:3]) if len(values) >= 3 else values[0]

        if recent_avg > early_avg * 1.05:
            return "improving"
        elif recent_avg < early_avg * 0.95:
            return "declining"
        else:
            return "stable"

    def _calculate_stability_score(self, values: List[float]) -> float:
        """計算穩定性評分"""
        if len(values) < 2:
            return 1.0

        variance = self.calculate_variance(values)
        mean_value = np.mean(values)

        # 正規化變異數作為不穩定性指標
        instability = variance / (mean_value ** 2) if mean_value > 0 else 1.0
        stability = max(0, 1 - instability)

        return stability

    def _detect_anomaly_periods(self, coverage_data: List[Dict]) -> List[Dict]:
        """檢測異常時期"""
        anomalies = []
        threshold = self.monitoring_config['thresholds']['coverage_alert_threshold']

        for i, data in enumerate(coverage_data):
            coverage_pct = data['expected_coverage']['coverage_percentage']
            if coverage_pct < threshold * 0.8:  # 異常閾值：警報閾值的80%
                anomalies.append({
                    'period_index': i,
                    'timestamp': data['timestamp'],
                    'coverage_percentage': coverage_pct,
                    'severity': 'high' if coverage_pct < threshold * 0.6 else 'medium'
                })

        # 更新統計
        if anomalies:
            self.monitoring_stats['anomalies_detected'] += len(anomalies)

        return anomalies

    def _calculate_trend_confidence(self, values: List[float]) -> float:
        """計算趨勢信心度"""
        if len(values) < 3:
            return 0.5

        # 基於數據點數量和變異性計算信心度
        data_confidence = min(1.0, len(values) / 10)
        variance_penalty = self.calculate_variance(values) / (np.mean(values) ** 2) if np.mean(values) > 0 else 1.0

        confidence = data_confidence * (1 - min(1.0, variance_penalty))
        return max(0.1, confidence)

    def _is_currently_visible(self, target: Dict) -> bool:
        """判斷目標當前是否可見"""
        elevation = target.get('position', {}).get('elevation', 0)
        return elevation > self.monitoring_config['thresholds']['elevation_minimum']

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """獲取監控統計信息"""
        return {
            'module_name': 'BackupMonitoringService',
            'monitoring_sessions_active': self.monitoring_stats['monitoring_sessions_active'],
            'alerts_generated': self.monitoring_stats['alerts_generated'],
            'predictions_made': self.monitoring_stats['predictions_made'],
            'anomalies_detected': self.monitoring_stats['anomalies_detected'],
            'average_coverage_percentage': self.monitoring_stats['average_coverage_percentage'],
            'monitoring_config': self.monitoring_config
        }