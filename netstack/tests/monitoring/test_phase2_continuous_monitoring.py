"""
Phase 2 持續監控系統 - 系統健康和性能監控

實施持續監控系統，包括：
- 系統健康狀態監控
- 性能指標連續監控
- 異常檢測和告警
- 監控數據收集和報告
- 自動化監控執行
"""

import pytest
import sys
import os
import time
import requests
import psutil
import json
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import statistics

# 添加項目路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


@dataclass
class HealthMetric:
    """健康監控指標"""
    service_name: str
    endpoint: str
    response_time_ms: float
    status_code: int
    is_healthy: bool
    cpu_usage_percent: float
    memory_usage_mb: float
    timestamp: str


@dataclass
class PerformanceMetric:
    """性能監控指標"""
    metric_name: str
    value: float
    threshold: float
    is_within_threshold: bool
    unit: str
    timestamp: str


@dataclass
class SystemAlert:
    """系統告警"""
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    service_name: str
    metric_value: float
    threshold: float
    timestamp: str


class ContinuousMonitor:
    """持續監控系統"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8080"
        self.simworld_url = "http://localhost:8888"
        self.frontend_url = "http://localhost:5173"
        
        # 監控配置
        self.monitoring_config = {
            'health_check_interval': 30,  # 30秒
            'performance_check_interval': 60,  # 60秒
            'alert_thresholds': {
                'response_time_ms': 1000,
                'cpu_usage_percent': 80,
                'memory_usage_mb': 500,
                'success_rate': 0.95,
                'error_rate': 0.05
            }
        }
        
        # 監控數據存儲
        self.health_metrics = []
        self.performance_metrics = []
        self.system_alerts = []
        self.monitoring_active = False
    
    def check_service_health(self, service_name: str, endpoint: str) -> HealthMetric:
        """檢查服務健康狀態"""
        start_time = time.time()
        
        try:
            # 獲取系統資源使用情況
            memory_usage, cpu_usage = self._get_system_resources()
            
            # 發送健康檢查請求
            response = requests.get(endpoint, timeout=5)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            is_healthy = response.status_code == 200
            
            return HealthMetric(
                service_name=service_name,
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                is_healthy=is_healthy,
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=memory_usage,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return HealthMetric(
                service_name=service_name,
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=0,
                is_healthy=False,
                cpu_usage_percent=0,
                memory_usage_mb=0,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
    
    def _get_system_resources(self) -> Tuple[float, float]:
        """獲取系統資源使用情況"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)
            return memory_mb, cpu_percent
        except:
            return 0, 0
    
    def collect_performance_metrics(self) -> List[PerformanceMetric]:
        """收集性能指標"""
        metrics = []
        
        # 檢查各服務的性能指標
        services = [
            ("NetStack API", f"{self.api_base_url}/health"),
            ("SimWorld Backend", f"{self.simworld_url}/health"),
        ]
        
        for service_name, endpoint in services:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=3)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time_ms = (end_time - start_time) * 1000
                    
                    # 響應時間指標
                    metrics.append(PerformanceMetric(
                        metric_name=f"{service_name}_response_time",
                        value=response_time_ms,
                        threshold=self.monitoring_config['alert_thresholds']['response_time_ms'],
                        is_within_threshold=response_time_ms < self.monitoring_config['alert_thresholds']['response_time_ms'],
                        unit="ms",
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    
                    # 如果響應包含詳細信息，提取更多指標
                    try:
                        data = response.json()
                        if 'services' in data:
                            services_data = data['services']
                            
                            # MongoDB 響應時間
                            if 'mongodb' in services_data and 'response_time' in services_data['mongodb']:
                                db_time = services_data['mongodb']['response_time'] * 1000
                                metrics.append(PerformanceMetric(
                                    metric_name=f"{service_name}_mongodb_response_time",
                                    value=db_time,
                                    threshold=100,  # 100ms 門檻
                                    is_within_threshold=db_time < 100,
                                    unit="ms",
                                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ))
                            
                            # Redis 響應時間
                            if 'redis' in services_data and 'response_time' in services_data['redis']:
                                redis_time = services_data['redis']['response_time'] * 1000
                                metrics.append(PerformanceMetric(
                                    metric_name=f"{service_name}_redis_response_time",
                                    value=redis_time,
                                    threshold=50,  # 50ms 門檻
                                    is_within_threshold=redis_time < 50,
                                    unit="ms",
                                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ))
                    except:
                        pass
                        
            except requests.exceptions.RequestException:
                # 服務不可用時記錄失敗指標
                metrics.append(PerformanceMetric(
                    metric_name=f"{service_name}_availability",
                    value=0,
                    threshold=1,
                    is_within_threshold=False,
                    unit="boolean",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
        
        return metrics
    
    def detect_anomalies(self, metrics: List[PerformanceMetric]) -> List[SystemAlert]:
        """檢測異常並生成告警"""
        alerts = []
        
        for metric in metrics:
            if not metric.is_within_threshold:
                # 確定告警嚴重級別
                severity = self._determine_alert_severity(metric)
                
                alert = SystemAlert(
                    alert_type="performance_threshold_exceeded",
                    severity=severity,
                    message=f"{metric.metric_name} 超出門檻值：{metric.value:.2f} {metric.unit} > {metric.threshold} {metric.unit}",
                    service_name=metric.metric_name.split('_')[0],
                    metric_value=metric.value,
                    threshold=metric.threshold,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                alerts.append(alert)
        
        return alerts
    
    def _determine_alert_severity(self, metric: PerformanceMetric) -> str:
        """確定告警嚴重級別"""
        ratio = metric.value / metric.threshold if metric.threshold > 0 else 1
        
        if ratio >= 3.0:  # 超出門檻 3 倍
            return "critical"
        elif ratio >= 2.0:  # 超出門檻 2 倍
            return "high"
        elif ratio >= 1.5:  # 超出門檻 1.5 倍
            return "medium"
        else:
            return "low"
    
    def generate_monitoring_report(self) -> Dict:
        """生成監控報告"""
        # 計算統計數據
        current_time = datetime.now()
        report_period = timedelta(hours=1)  # 最近1小時的數據
        
        recent_health_metrics = [
            m for m in self.health_metrics 
            if datetime.strptime(m.timestamp, "%Y-%m-%d %H:%M:%S") > current_time - report_period
        ]
        
        recent_performance_metrics = [
            m for m in self.performance_metrics
            if datetime.strptime(m.timestamp, "%Y-%m-%d %H:%M:%S") > current_time - report_period
        ]
        
        recent_alerts = [
            a for a in self.system_alerts
            if datetime.strptime(a.timestamp, "%Y-%m-%d %H:%M:%S") > current_time - report_period
        ]
        
        # 計算系統健康度
        healthy_services = len([m for m in recent_health_metrics if m.is_healthy])
        total_services = len(recent_health_metrics)
        system_health_score = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        # 計算平均響應時間
        response_times = [m.response_time_ms for m in recent_health_metrics if m.is_healthy]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # 告警統計
        alert_counts = {
            'critical': len([a for a in recent_alerts if a.severity == 'critical']),
            'high': len([a for a in recent_alerts if a.severity == 'high']),
            'medium': len([a for a in recent_alerts if a.severity == 'medium']),
            'low': len([a for a in recent_alerts if a.severity == 'low'])
        }
        
        return {
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'report_period_hours': 1,
            'system_health': {
                'overall_score': system_health_score,
                'healthy_services': healthy_services,
                'total_services': total_services,
                'avg_response_time_ms': avg_response_time
            },
            'performance_metrics': {
                'total_metrics_collected': len(recent_performance_metrics),
                'metrics_within_threshold': len([m for m in recent_performance_metrics if m.is_within_threshold]),
                'metrics_exceeded_threshold': len([m for m in recent_performance_metrics if not m.is_within_threshold])
            },
            'alerts': {
                'total_alerts': len(recent_alerts),
                'by_severity': alert_counts
            },
            'recommendations': self._generate_recommendations(recent_alerts, recent_performance_metrics)
        }
    
    def _generate_recommendations(self, alerts: List[SystemAlert], metrics: List[PerformanceMetric]) -> List[str]:
        """生成監控建議"""
        recommendations = []
        
        # 基於告警生成建議
        if any(a.severity in ['critical', 'high'] for a in alerts):
            recommendations.append("檢測到高嚴重級別告警，建議立即檢查系統狀態")
        
        # 基於性能指標生成建議
        response_time_metrics = [m for m in metrics if 'response_time' in m.metric_name and not m.is_within_threshold]
        if response_time_metrics:
            recommendations.append("響應時間超出門檻，建議檢查網路連接和系統負載")
        
        # 資源使用建議
        db_metrics = [m for m in metrics if 'mongodb' in m.metric_name or 'redis' in m.metric_name]
        slow_db_metrics = [m for m in db_metrics if not m.is_within_threshold]
        if slow_db_metrics:
            recommendations.append("數據庫響應時間偏慢，建議檢查數據庫性能和索引")
        
        if not recommendations:
            recommendations.append("系統運行正常，無需特別關注")
        
        return recommendations


class TestContinuousMonitoringSystem:
    """持續監控系統測試"""
    
    def setup_method(self):
        """測試方法設置"""
        self.monitor = ContinuousMonitor()
    
    def test_service_health_monitoring(self):
        """測試服務健康監控"""
        # 測試 NetStack API 健康檢查
        health_metric = self.monitor.check_service_health(
            "NetStack API", 
            f"{self.monitor.api_base_url}/health"
        )
        
        assert health_metric.service_name == "NetStack API"
        assert health_metric.endpoint == f"{self.monitor.api_base_url}/health"
        assert health_metric.response_time_ms >= 0
        assert health_metric.timestamp is not None
        
        # 記錄監控數據
        self.monitor.health_metrics.append(health_metric)
        
        print(f"✅ NetStack API 健康檢查: {'健康' if health_metric.is_healthy else '異常'}")
        print(f"   響應時間: {health_metric.response_time_ms:.1f}ms")
        print(f"   狀態碼: {health_metric.status_code}")
        
        # 測試 SimWorld 健康檢查
        simworld_health = self.monitor.check_service_health(
            "SimWorld Backend",
            f"{self.monitor.simworld_url}/health"
        )
        
        self.monitor.health_metrics.append(simworld_health)
        
        print(f"✅ SimWorld Backend 健康檢查: {'健康' if simworld_health.is_healthy else '異常'}")
        if simworld_health.is_healthy:
            print(f"   響應時間: {simworld_health.response_time_ms:.1f}ms")
        
        # 至少有一個服務健康
        assert health_metric.is_healthy or simworld_health.is_healthy, "至少應有一個服務健康"
    
    def test_performance_metrics_collection(self):
        """測試性能指標收集"""
        metrics = self.monitor.collect_performance_metrics()
        
        assert len(metrics) > 0, "應該收集到性能指標"
        
        # 檢查指標結構
        for metric in metrics:
            assert metric.metric_name is not None
            assert metric.value >= 0
            assert metric.threshold > 0
            assert metric.unit is not None
            assert metric.timestamp is not None
        
        # 記錄性能指標
        self.monitor.performance_metrics.extend(metrics)
        
        print(f"✅ 收集到 {len(metrics)} 項性能指標:")
        for metric in metrics[:3]:  # 顯示前3個指標
            status = "正常" if metric.is_within_threshold else "超出門檻"
            print(f"   {metric.metric_name}: {metric.value:.2f} {metric.unit} ({status})")
    
    def test_anomaly_detection(self):
        """測試異常檢測"""
        # 收集性能指標
        metrics = self.monitor.collect_performance_metrics()
        self.monitor.performance_metrics.extend(metrics)
        
        # 檢測異常
        alerts = self.monitor.detect_anomalies(metrics)
        
        # 記錄告警
        self.monitor.system_alerts.extend(alerts)
        
        print(f"✅ 異常檢測完成，生成 {len(alerts)} 個告警")
        
        if alerts:
            print("   告警詳情:")
            for alert in alerts[:3]:  # 顯示前3個告警
                print(f"   - [{alert.severity.upper()}] {alert.message}")
        else:
            print("   無異常檢測到")
        
        # 驗證告警結構
        for alert in alerts:
            assert alert.alert_type is not None
            assert alert.severity in ['low', 'medium', 'high', 'critical']
            assert alert.message is not None
            assert alert.timestamp is not None
    
    def test_monitoring_report_generation(self):
        """測試監控報告生成"""
        # 先收集一些監控數據
        health_metric = self.monitor.check_service_health(
            "NetStack API", 
            f"{self.monitor.api_base_url}/health"
        )
        self.monitor.health_metrics.append(health_metric)
        
        metrics = self.monitor.collect_performance_metrics()
        self.monitor.performance_metrics.extend(metrics)
        
        alerts = self.monitor.detect_anomalies(metrics)
        self.monitor.system_alerts.extend(alerts)
        
        # 生成監控報告
        report = self.monitor.generate_monitoring_report()
        
        # 驗證報告結構
        assert 'timestamp' in report
        assert 'system_health' in report
        assert 'performance_metrics' in report
        assert 'alerts' in report
        assert 'recommendations' in report
        
        # 系統健康度驗證
        system_health = report['system_health']
        assert 'overall_score' in system_health
        assert 0 <= system_health['overall_score'] <= 100
        
        print(f"✅ 監控報告生成成功")
        print(f"   系統健康度: {system_health['overall_score']:.1f}%")
        print(f"   健康服務數: {system_health['healthy_services']}/{system_health['total_services']}")
        print(f"   平均響應時間: {system_health['avg_response_time_ms']:.1f}ms")
        print(f"   總告警數: {report['alerts']['total_alerts']}")
        
        if report['recommendations']:
            print("   建議:")
            for rec in report['recommendations']:
                print(f"     - {rec}")
        
        # 保存報告到文件
        report_file = "/home/sat/ntn-stack/netstack/tests/monitoring/monitoring_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 監控報告已保存: {report_file}")
    
    def test_monitoring_configuration_validation(self):
        """測試監控配置驗證"""
        config = self.monitor.monitoring_config
        
        # 驗證配置結構
        assert 'health_check_interval' in config
        assert 'performance_check_interval' in config
        assert 'alert_thresholds' in config
        
        # 驗證間隔設置合理性
        assert config['health_check_interval'] > 0
        assert config['performance_check_interval'] > 0
        assert config['health_check_interval'] <= config['performance_check_interval']
        
        # 驗證告警門檻設置
        thresholds = config['alert_thresholds']
        assert thresholds['response_time_ms'] > 0
        assert thresholds['cpu_usage_percent'] > 0
        assert thresholds['memory_usage_mb'] > 0
        assert 0 < thresholds['success_rate'] <= 1
        assert 0 <= thresholds['error_rate'] < 1
        
        print("✅ 監控配置驗證通過")
        print(f"   健康檢查間隔: {config['health_check_interval']}秒")
        print(f"   性能檢查間隔: {config['performance_check_interval']}秒")
        print(f"   響應時間門檻: {thresholds['response_time_ms']}ms")


class TestMonitoringIntegration:
    """監控系統整合測試"""
    
    def test_monitoring_system_integration(self):
        """測試監控系統整合"""
        monitor = ContinuousMonitor()
        
        # 執行完整的監控週期
        print("🔍 執行完整監控週期...")
        
        # 1. 健康檢查
        services = [
            ("NetStack API", f"{monitor.api_base_url}/health"),
            ("SimWorld Backend", f"{monitor.simworld_url}/health")
        ]
        
        for service_name, endpoint in services:
            health_metric = monitor.check_service_health(service_name, endpoint)
            monitor.health_metrics.append(health_metric)
            print(f"   {service_name}: {'✅' if health_metric.is_healthy else '❌'}")
        
        # 2. 性能指標收集
        metrics = monitor.collect_performance_metrics()
        monitor.performance_metrics.extend(metrics)
        print(f"   收集性能指標: {len(metrics)}項")
        
        # 3. 異常檢測
        alerts = monitor.detect_anomalies(metrics)
        monitor.system_alerts.extend(alerts)
        print(f"   異常檢測: {len(alerts)}個告警")
        
        # 4. 生成報告
        report = monitor.generate_monitoring_report()
        print(f"   系統健康度: {report['system_health']['overall_score']:.1f}%")
        
        # 驗證整合性
        assert len(monitor.health_metrics) > 0, "應該有健康監控數據"
        assert len(monitor.performance_metrics) > 0, "應該有性能監控數據"
        assert report['system_health']['overall_score'] >= 0, "系統健康度應該有效"
        
        print("✅ 監控系統整合測試通過")


if __name__ == "__main__":
    # 運行持續監控測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])