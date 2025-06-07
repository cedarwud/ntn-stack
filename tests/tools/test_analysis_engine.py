"""
測試趨勢分析和回歸檢測引擎
Test Trend Analysis and Regression Detection Engine
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

from .test_data_collector import TestResult, TestSuite, PerformanceMetrics, TestDataManager


@dataclass
class TrendPoint:
    """趨勢點數據"""
    timestamp: datetime
    value: float
    label: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TrendAnalysis:
    """趨勢分析結果"""
    metric_name: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0-1
    slope: float
    r_squared: float
    p_value: float
    confidence_interval: Tuple[float, float]
    data_points: List[TrendPoint]
    anomalies: List[TrendPoint]
    seasonal_pattern: Optional[Dict[str, Any]] = None


@dataclass
class RegressionAlert:
    """回歸警報"""
    alert_type: str  # performance_degradation, quality_regression, test_failure_spike
    severity: str  # low, medium, high, critical
    metric_name: str
    current_value: float
    baseline_value: float
    change_percentage: float
    detected_at: datetime
    description: str
    recommendations: List[str]
    affected_tests: List[str] = None
    
    def __post_init__(self):
        if self.affected_tests is None:
            self.affected_tests = []


@dataclass
class AnalysisReport:
    """分析報告"""
    generated_at: datetime
    analysis_period: Tuple[datetime, datetime]
    trend_analyses: List[TrendAnalysis]
    regression_alerts: List[RegressionAlert]
    summary_metrics: Dict[str, Any]
    recommendations: List[str]


class StatisticalAnalyzer:
    """統計分析器"""
    
    @staticmethod
    def calculate_trend(data: List[float], timestamps: List[datetime]) -> Tuple[float, float, float, float]:
        """計算趨勢統計"""
        if len(data) < 3:
            return 0.0, 0.0, 0.0, 1.0
        
        # 轉換時間戳為數值
        time_numeric = [(ts - timestamps[0]).total_seconds() for ts in timestamps]
        
        # 線性回歸
        X = np.array(time_numeric).reshape(-1, 1)
        y = np.array(data)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 計算統計指標
        y_pred = model.predict(X)
        slope = model.coef_[0]
        r_squared = model.score(X, y)
        
        # 計算p值
        n = len(data)
        if n > 2:
            residuals = y - y_pred
            mse = np.mean(residuals ** 2)
            se_slope = np.sqrt(mse / np.sum((time_numeric - np.mean(time_numeric)) ** 2))
            t_stat = slope / se_slope if se_slope != 0 else 0
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        else:
            p_value = 1.0
        
        return slope, r_squared, p_value, np.std(residuals) if n > 2 else 0
    
    @staticmethod
    def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[int]:
        """檢測異常值"""
        if len(data) < 3:
            return []
        
        z_scores = np.abs(stats.zscore(data))
        return [i for i, z in enumerate(z_scores) if z > threshold]
    
    @staticmethod
    def calculate_change_point(data: List[float], min_size: int = 5) -> Optional[int]:
        """檢測變化點"""
        if len(data) < min_size * 2:
            return None
        
        best_split = None
        best_score = float('inf')
        
        for i in range(min_size, len(data) - min_size):
            left_data = data[:i]
            right_data = data[i:]
            
            # 計算分割後的方差
            left_var = np.var(left_data) if len(left_data) > 1 else 0
            right_var = np.var(right_data) if len(right_data) > 1 else 0
            
            score = len(left_data) * left_var + len(right_data) * right_var
            
            if score < best_score:
                best_score = score
                best_split = i
        
        return best_split
    
    @staticmethod
    def seasonal_decomposition(data: List[float], timestamps: List[datetime], period: int = 7) -> Dict[str, Any]:
        """季節性分解"""
        if len(data) < period * 2:
            return {}
        
        # 簡單的移動平均季節性分解
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': data
        })
        
        # 按週期分組計算平均值
        df['period_index'] = [i % period for i in range(len(df))]
        seasonal_pattern = df.groupby('period_index')['value'].mean().to_dict()
        
        # 計算趨勢（移動平均）
        window_size = min(period, len(data) // 2)
        trend = df['value'].rolling(window=window_size, center=True).mean()
        
        # 計算殘差
        seasonal_values = [seasonal_pattern[i % period] for i in range(len(data))]
        residuals = [data[i] - trend.iloc[i] - seasonal_values[i] 
                    for i in range(len(data)) if not pd.isna(trend.iloc[i])]
        
        return {
            'seasonal_pattern': seasonal_pattern,
            'trend_values': trend.dropna().tolist(),
            'residual_std': np.std(residuals) if residuals else 0,
            'seasonality_strength': np.std(list(seasonal_pattern.values())) / np.std(data) if np.std(data) > 0 else 0
        }


class TrendAnalysisEngine:
    """趨勢分析引擎"""
    
    def __init__(self, data_manager: TestDataManager):
        self.data_manager = data_manager
        self.analyzer = StatisticalAnalyzer()
    
    def analyze_test_success_rate_trend(self, 
                                       start_date: datetime,
                                       end_date: datetime,
                                       test_suite: Optional[str] = None) -> TrendAnalysis:
        """分析測試成功率趨勢"""
        
        # 獲取測試數據
        test_data = self.data_manager.get_test_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if test_suite:
            test_data = test_data[test_data['suite_name'] == test_suite]
        
        if test_data.empty:
            return self._create_empty_trend_analysis("Test Success Rate")
        
        # 按日期聚合成功率
        test_data['date'] = pd.to_datetime(test_data['timestamp']).dt.date
        daily_stats = test_data.groupby('date').apply(
            lambda x: (x['status'] == 'passed').sum() / len(x) * 100
        ).reset_index()
        daily_stats.columns = ['date', 'success_rate']
        daily_stats['timestamp'] = pd.to_datetime(daily_stats['date'])
        
        # 創建趨勢點
        data_points = [
            TrendPoint(
                timestamp=row['timestamp'],
                value=row['success_rate'],
                label=f"Success Rate: {row['success_rate']:.1f}%",
                metadata={'date': str(row['date'])}
            )
            for _, row in daily_stats.iterrows()
        ]
        
        # 統計分析
        values = daily_stats['success_rate'].tolist()
        timestamps = daily_stats['timestamp'].tolist()
        
        slope, r_squared, p_value, std_error = self.analyzer.calculate_trend(values, timestamps)
        
        # 檢測異常
        anomaly_indices = self.analyzer.detect_anomalies(values)
        anomalies = [data_points[i] for i in anomaly_indices if i < len(data_points)]
        
        # 確定趨勢方向
        if abs(slope) < std_error:
            trend_direction = "stable"
            trend_strength = 0.0
        elif slope > 0:
            trend_direction = "increasing"
            trend_strength = min(abs(slope) / (std_error * 2), 1.0)
        else:
            trend_direction = "decreasing"
            trend_strength = min(abs(slope) / (std_error * 2), 1.0)
        
        # 季節性分析
        seasonal_pattern = self.analyzer.seasonal_decomposition(values, timestamps)
        
        return TrendAnalysis(
            metric_name="Test Success Rate",
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            slope=slope,
            r_squared=r_squared,
            p_value=p_value,
            confidence_interval=(slope - 1.96 * std_error, slope + 1.96 * std_error),
            data_points=data_points,
            anomalies=anomalies,
            seasonal_pattern=seasonal_pattern
        )
    
    def analyze_performance_trends(self,
                                 start_date: datetime,
                                 end_date: datetime) -> List[TrendAnalysis]:
        """分析性能趨勢"""
        
        performance_data = self.data_manager.get_performance_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if performance_data.empty:
            return []
        
        # 分析不同性能指標
        metrics = ['response_time', 'throughput', 'error_rate', 'cpu_usage', 'memory_usage']
        trend_analyses = []
        
        for metric in metrics:
            if metric not in performance_data.columns:
                continue
            
            # 按日期聚合
            performance_data['date'] = pd.to_datetime(performance_data['timestamp']).dt.date
            daily_avg = performance_data.groupby('date')[metric].mean().reset_index()
            daily_avg['timestamp'] = pd.to_datetime(daily_avg['date'])
            
            if len(daily_avg) < 3:
                continue
            
            # 創建趨勢點
            data_points = [
                TrendPoint(
                    timestamp=row['timestamp'],
                    value=row[metric],
                    label=f"{metric}: {row[metric]:.2f}",
                    metadata={'date': str(row['date'])}
                )
                for _, row in daily_avg.iterrows()
            ]
            
            # 統計分析
            values = daily_avg[metric].tolist()
            timestamps = daily_avg['timestamp'].tolist()
            
            slope, r_squared, p_value, std_error = self.analyzer.calculate_trend(values, timestamps)
            
            # 檢測異常
            anomaly_indices = self.analyzer.detect_anomalies(values)
            anomalies = [data_points[i] for i in anomaly_indices if i < len(data_points)]
            
            # 趨勢方向和強度
            if abs(slope) < std_error:
                trend_direction = "stable"
                trend_strength = 0.0
            elif slope > 0:
                trend_direction = "increasing"
                trend_strength = min(abs(slope) / (std_error * 2), 1.0)
            else:
                trend_direction = "decreasing"
                trend_strength = min(abs(slope) / (std_error * 2), 1.0)
            
            trend_analyses.append(TrendAnalysis(
                metric_name=metric,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                slope=slope,
                r_squared=r_squared,
                p_value=p_value,
                confidence_interval=(slope - 1.96 * std_error, slope + 1.96 * std_error),
                data_points=data_points,
                anomalies=anomalies
            ))
        
        return trend_analyses
    
    def _create_empty_trend_analysis(self, metric_name: str) -> TrendAnalysis:
        """創建空的趨勢分析"""
        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction="stable",
            trend_strength=0.0,
            slope=0.0,
            r_squared=0.0,
            p_value=1.0,
            confidence_interval=(0.0, 0.0),
            data_points=[],
            anomalies=[]
        )


class RegressionDetector:
    """回歸檢測器"""
    
    def __init__(self, data_manager: TestDataManager):
        self.data_manager = data_manager
        self.analyzer = StatisticalAnalyzer()
    
    def detect_performance_regression(self,
                                    current_period_days: int = 7,
                                    baseline_period_days: int = 14,
                                    threshold: float = 0.1) -> List[RegressionAlert]:
        """檢測性能回歸"""
        
        alerts = []
        end_date = datetime.now()
        current_start = end_date - timedelta(days=current_period_days)
        baseline_start = current_start - timedelta(days=baseline_period_days)
        
        # 獲取當前期間和基線期間的性能數據
        current_data = self.data_manager.get_performance_data(
            start_date=current_start,
            end_date=end_date
        )
        
        baseline_data = self.data_manager.get_performance_data(
            start_date=baseline_start,
            end_date=current_start
        )
        
        if current_data.empty or baseline_data.empty:
            return alerts
        
        # 分析各項性能指標
        metrics = ['response_time', 'throughput', 'error_rate', 'cpu_usage', 'memory_usage']
        
        for metric in metrics:
            if metric not in current_data.columns or metric not in baseline_data.columns:
                continue
            
            current_avg = current_data[metric].mean()
            baseline_avg = baseline_data[metric].mean()
            
            if baseline_avg == 0:
                continue
            
            change_percentage = (current_avg - baseline_avg) / baseline_avg
            
            # 判斷是否為回歸（不同指標的回歸方向不同）
            is_regression = False
            if metric in ['response_time', 'error_rate', 'cpu_usage', 'memory_usage']:
                # 這些指標增加是回歸
                is_regression = change_percentage > threshold
            elif metric == 'throughput':
                # 吞吐量減少是回歸
                is_regression = change_percentage < -threshold
            
            if is_regression:
                # 確定嚴重程度
                abs_change = abs(change_percentage)
                if abs_change > 0.5:
                    severity = "critical"
                elif abs_change > 0.3:
                    severity = "high"
                elif abs_change > 0.2:
                    severity = "medium"
                else:
                    severity = "low"
                
                # 生成建議
                recommendations = self._generate_performance_recommendations(metric, change_percentage)
                
                alert = RegressionAlert(
                    alert_type="performance_degradation",
                    severity=severity,
                    metric_name=metric,
                    current_value=current_avg,
                    baseline_value=baseline_avg,
                    change_percentage=change_percentage * 100,
                    detected_at=datetime.now(),
                    description=f"{metric} has degraded by {abs(change_percentage * 100):.1f}% compared to baseline",
                    recommendations=recommendations
                )
                
                alerts.append(alert)
        
        return alerts
    
    def detect_test_quality_regression(self,
                                     current_period_days: int = 7,
                                     baseline_period_days: int = 14) -> List[RegressionAlert]:
        """檢測測試質量回歸"""
        
        alerts = []
        end_date = datetime.now()
        current_start = end_date - timedelta(days=current_period_days)
        baseline_start = current_start - timedelta(days=baseline_period_days)
        
        # 獲取測試數據
        current_data = self.data_manager.get_test_data(
            start_date=current_start,
            end_date=end_date
        )
        
        baseline_data = self.data_manager.get_test_data(
            start_date=baseline_start,
            end_date=current_start
        )
        
        if current_data.empty or baseline_data.empty:
            return alerts
        
        # 分析成功率
        current_success_rate = (current_data['status'] == 'passed').mean()
        baseline_success_rate = (baseline_data['status'] == 'passed').mean()
        
        if baseline_success_rate > 0:
            success_rate_change = (current_success_rate - baseline_success_rate) / baseline_success_rate
            
            if success_rate_change < -0.05:  # 成功率下降超過5%
                severity = "high" if success_rate_change < -0.15 else "medium"
                
                # 找出失敗增加的測試
                current_failures = current_data[current_data['status'] != 'passed']['test_name'].value_counts()
                baseline_failures = baseline_data[baseline_data['status'] != 'passed']['test_name'].value_counts()
                
                affected_tests = []
                for test_name in current_failures.index:
                    current_count = current_failures[test_name]
                    baseline_count = baseline_failures.get(test_name, 0)
                    if current_count > baseline_count:
                        affected_tests.append(test_name)
                
                alert = RegressionAlert(
                    alert_type="quality_regression",
                    severity=severity,
                    metric_name="test_success_rate",
                    current_value=current_success_rate * 100,
                    baseline_value=baseline_success_rate * 100,
                    change_percentage=success_rate_change * 100,
                    detected_at=datetime.now(),
                    description=f"Test success rate decreased by {abs(success_rate_change * 100):.1f}%",
                    recommendations=self._generate_quality_recommendations(),
                    affected_tests=affected_tests[:10]  # 限制顯示前10個
                )
                
                alerts.append(alert)
        
        return alerts
    
    def detect_test_failure_spikes(self, window_hours: int = 24) -> List[RegressionAlert]:
        """檢測測試失敗激增"""
        
        alerts = []
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=window_hours)
        
        test_data = self.data_manager.get_test_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if test_data.empty:
            return alerts
        
        # 按小時分組計算失敗率
        test_data['hour'] = pd.to_datetime(test_data['timestamp']).dt.floor('H')
        hourly_stats = test_data.groupby('hour').agg({
            'status': [
                lambda x: (x != 'passed').sum(),  # 失敗數
                'count'  # 總數
            ]
        }).reset_index()
        
        hourly_stats.columns = ['hour', 'failures', 'total']
        hourly_stats['failure_rate'] = hourly_stats['failures'] / hourly_stats['total']
        
        if len(hourly_stats) < 3:
            return alerts
        
        # 檢測異常失敗率
        failure_rates = hourly_stats['failure_rate'].tolist()
        anomaly_indices = self.analyzer.detect_anomalies(failure_rates, threshold=1.5)
        
        for idx in anomaly_indices:
            if idx < len(hourly_stats):
                hour_data = hourly_stats.iloc[idx]
                
                if hour_data['failure_rate'] > 0.2:  # 失敗率超過20%
                    severity = "critical" if hour_data['failure_rate'] > 0.5 else "high"
                    
                    alert = RegressionAlert(
                        alert_type="test_failure_spike",
                        severity=severity,
                        metric_name="failure_rate",
                        current_value=hour_data['failure_rate'] * 100,
                        baseline_value=np.mean(failure_rates) * 100,
                        change_percentage=((hour_data['failure_rate'] - np.mean(failure_rates)) / np.mean(failure_rates)) * 100,
                        detected_at=hour_data['hour'],
                        description=f"Test failure spike detected at {hour_data['hour']} with {hour_data['failure_rate']*100:.1f}% failure rate",
                        recommendations=[
                            "Investigate recent code changes",
                            "Check infrastructure status",
                            "Review test environment configuration"
                        ]
                    )
                    
                    alerts.append(alert)
        
        return alerts
    
    def _generate_performance_recommendations(self, metric: str, change_percentage: float) -> List[str]:
        """生成性能改進建議"""
        recommendations = []
        
        if metric == 'response_time':
            recommendations.extend([
                "Profile application performance bottlenecks",
                "Check database query performance",
                "Review caching strategies",
                "Monitor network latency"
            ])
        elif metric == 'throughput':
            recommendations.extend([
                "Scale up/out infrastructure resources",
                "Optimize concurrent processing",
                "Review load balancing configuration"
            ])
        elif metric == 'error_rate':
            recommendations.extend([
                "Review error logs for common patterns",
                "Check service dependencies",
                "Validate input data quality"
            ])
        elif metric in ['cpu_usage', 'memory_usage']:
            recommendations.extend([
                "Profile resource-intensive operations",
                "Check for memory leaks",
                "Optimize algorithms and data structures",
                "Consider vertical scaling"
            ])
        
        return recommendations
    
    def _generate_quality_recommendations(self) -> List[str]:
        """生成測試質量改進建議"""
        return [
            "Review recent code changes for potential bugs",
            "Check test environment stability",
            "Analyze failing test patterns",
            "Update test data and fixtures",
            "Review test dependencies and timing",
            "Consider flaky test identification and fixes"
        ]


class TestAnalysisEngine:
    """測試分析引擎主類"""
    
    def __init__(self, data_manager: TestDataManager):
        self.data_manager = data_manager
        self.trend_analyzer = TrendAnalysisEngine(data_manager)
        self.regression_detector = RegressionDetector(data_manager)
    
    def run_comprehensive_analysis(self,
                                 analysis_period_days: int = 30) -> AnalysisReport:
        """運行綜合分析"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=analysis_period_days)
        
        # 趨勢分析
        trend_analyses = []
        
        # 測試成功率趨勢
        success_rate_trend = self.trend_analyzer.analyze_test_success_rate_trend(start_date, end_date)
        trend_analyses.append(success_rate_trend)
        
        # 性能趨勢
        performance_trends = self.trend_analyzer.analyze_performance_trends(start_date, end_date)
        trend_analyses.extend(performance_trends)
        
        # 回歸檢測
        regression_alerts = []
        
        # 性能回歸
        perf_alerts = self.regression_detector.detect_performance_regression()
        regression_alerts.extend(perf_alerts)
        
        # 質量回歸
        quality_alerts = self.regression_detector.detect_test_quality_regression()
        regression_alerts.extend(quality_alerts)
        
        # 失敗激增
        spike_alerts = self.regression_detector.detect_test_failure_spikes()
        regression_alerts.extend(spike_alerts)
        
        # 生成摘要指標
        summary_metrics = self._generate_summary_metrics(trend_analyses, regression_alerts)
        
        # 生成建議
        recommendations = self._generate_comprehensive_recommendations(trend_analyses, regression_alerts)
        
        return AnalysisReport(
            generated_at=datetime.now(),
            analysis_period=(start_date, end_date),
            trend_analyses=trend_analyses,
            regression_alerts=regression_alerts,
            summary_metrics=summary_metrics,
            recommendations=recommendations
        )
    
    def _generate_summary_metrics(self, 
                                trend_analyses: List[TrendAnalysis],
                                regression_alerts: List[RegressionAlert]) -> Dict[str, Any]:
        """生成摘要指標"""
        
        # 趨勢摘要
        improving_trends = len([t for t in trend_analyses if t.trend_direction == "increasing" and "success" in t.metric_name.lower()])
        degrading_trends = len([t for t in trend_analyses if t.trend_direction == "decreasing" and "success" in t.metric_name.lower()])
        stable_trends = len([t for t in trend_analyses if t.trend_direction == "stable"])
        
        # 警報摘要
        critical_alerts = len([a for a in regression_alerts if a.severity == "critical"])
        high_alerts = len([a for a in regression_alerts if a.severity == "high"])
        total_alerts = len(regression_alerts)
        
        # 健康評分（0-100）
        health_score = 100
        health_score -= critical_alerts * 25
        health_score -= high_alerts * 15
        health_score -= degrading_trends * 10
        health_score = max(0, health_score)
        
        return {
            'total_trends_analyzed': len(trend_analyses),
            'improving_trends': improving_trends,
            'degrading_trends': degrading_trends,
            'stable_trends': stable_trends,
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'high_alerts': high_alerts,
            'health_score': health_score,
            'analysis_quality': 'good' if len(trend_analyses) > 0 else 'limited'
        }
    
    def _generate_comprehensive_recommendations(self,
                                              trend_analyses: List[TrendAnalysis],
                                              regression_alerts: List[RegressionAlert]) -> List[str]:
        """生成綜合建議"""
        recommendations = []
        
        # 基於警報的建議
        if any(a.severity == "critical" for a in regression_alerts):
            recommendations.append("🚨 Critical issues detected - immediate investigation required")
        
        # 基於趨勢的建議
        degrading_metrics = [t.metric_name for t in trend_analyses if t.trend_direction == "decreasing"]
        if degrading_metrics:
            recommendations.append(f"📉 Monitor degrading metrics: {', '.join(degrading_metrics)}")
        
        # 基於異常的建議
        total_anomalies = sum(len(t.anomalies) for t in trend_analyses)
        if total_anomalies > 5:
            recommendations.append("🔍 High number of anomalies detected - review test stability")
        
        # 性能特定建議
        perf_alerts = [a for a in regression_alerts if a.alert_type == "performance_degradation"]
        if perf_alerts:
            recommendations.append("⚡ Performance optimization needed - check infrastructure and code")
        
        # 質量特定建議
        quality_alerts = [a for a in regression_alerts if a.alert_type == "quality_regression"]
        if quality_alerts:
            recommendations.append("🐛 Test quality issues - review recent changes and test reliability")
        
        return recommendations


if __name__ == "__main__":
    # 示例使用
    data_manager = TestDataManager()
    analysis_engine = TestAnalysisEngine(data_manager)
    
    # 運行綜合分析
    report = analysis_engine.run_comprehensive_analysis(analysis_period_days=14)
    
    print(f"Analysis Report Generated at: {report.generated_at}")
    print(f"Analysis Period: {report.analysis_period[0]} to {report.analysis_period[1]}")
    print(f"Health Score: {report.summary_metrics['health_score']}/100")
    print(f"Total Alerts: {report.summary_metrics['total_alerts']}")
    print(f"Critical Alerts: {report.summary_metrics['critical_alerts']}")
    
    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")
    
    print("\nTrend Analyses:")
    for trend in report.trend_analyses:
        print(f"  - {trend.metric_name}: {trend.trend_direction} (strength: {trend.trend_strength:.2f})")
    
    print("\nRegression Alerts:")
    for alert in report.regression_alerts:
        print(f"  - {alert.severity.upper()}: {alert.description}")