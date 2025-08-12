#!/usr/bin/env python3
"""
Phase 1 性能監控系統

功能:
1. 實時監控 Phase 1 系統性能
2. 追蹤 SGP4 計算性能和準確性
3. 提供性能分析和優化建議
4. 支援告警和自動調優

符合 CLAUDE.md 原則:
- 監控真實 SGP4 計算性能
- 確保系統穩定性和可靠性
- 提供詳細的性能指標
"""

import logging
import time
import psutil
import threading
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指標"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    context: Optional[Dict[str, Any]] = None

@dataclass
class SystemSnapshot:
    """系統快照"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    active_threads: int
    
@dataclass
class CalculationMetrics:
    """計算性能指標"""
    timestamp: datetime
    total_calculations: int
    successful_calculations: int
    failed_calculations: int
    average_calculation_time: float
    calculations_per_second: float
    cache_hit_rate: float
    active_satellites: int

@dataclass
class APIMetrics:
    """API 性能指標"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    requests_per_second: float
    active_connections: int
    error_rate: float

class PerformanceCollector:
    """性能數據收集器"""
    
    def __init__(self, collection_interval: float = 1.0):
        """
        初始化收集器
        
        Args:
            collection_interval: 數據收集間隔（秒）
        """
        self.collection_interval = collection_interval
        self.is_collecting = False
        self.collection_thread = None
        
        # 數據存儲（使用 deque 限制內存使用）
        self.metrics = deque(maxlen=3600)  # 保存最近1小時數據
        self.system_snapshots = deque(maxlen=1200)  # 保存最近20分鐘系統快照
        self.calculation_metrics = deque(maxlen=300)  # 保存最近5分鐘計算指標
        self.api_metrics = deque(maxlen=300)  # 保存最近5分鐘API指標
        
        # 回調函數
        self.alert_callbacks: List[Callable[[str, Dict], None]] = []
        
        logger.info("性能收集器初始化完成")
    
    def add_metric(self, name: str, value: float, unit: str, context: Dict[str, Any] = None):
        """添加性能指標"""
        metric = PerformanceMetric(
            timestamp=datetime.now(timezone.utc),
            metric_name=name,
            value=value,
            unit=unit,
            context=context or {}
        )
        self.metrics.append(metric)
    
    def collect_system_metrics(self):
        """收集系統性能指標"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # 內存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # 磁盤使用
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # 活躍線程數
            active_threads = threading.active_count()
            
            snapshot = SystemSnapshot(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                active_threads=active_threads
            )
            
            self.system_snapshots.append(snapshot)
            
            # 添加個別指標
            self.add_metric("cpu_usage", cpu_percent, "percent")
            self.add_metric("memory_usage", memory_percent, "percent")
            self.add_metric("memory_available", memory_available_mb, "MB")
            self.add_metric("active_threads", active_threads, "count")
            
            # 檢查告警閾值
            self._check_system_alerts(snapshot)
            
        except Exception as e:
            logger.error(f"收集系統指標失敗: {e}")
    
    def collect_sgp4_metrics(self, sgp4_engine):
        """收集 SGP4 引擎性能指標"""
        try:
            if not sgp4_engine:
                return
                
            stats = sgp4_engine.get_statistics()
            
            # 計算性能指標
            total_calc = stats.get("total_calculations", 0)
            successful_calc = stats.get("successful_calculations", 0)
            failed_calc = stats.get("failed_calculations", 0)
            cache_hits = stats.get("cache_hits", 0)
            cached_satellites = stats.get("cached_satellites", 0)
            
            # 計算速率（需要歷史數據）
            calc_per_second = 0.0
            avg_calc_time = 0.0
            cache_hit_rate = (cache_hits / max(total_calc, 1)) * 100
            
            if len(self.calculation_metrics) > 0:
                prev_metrics = self.calculation_metrics[-1]
                time_diff = (datetime.now(timezone.utc) - prev_metrics.timestamp).total_seconds()
                calc_diff = total_calc - prev_metrics.total_calculations
                
                if time_diff > 0:
                    calc_per_second = calc_diff / time_diff
                    avg_calc_time = time_diff / max(calc_diff, 1)
            
            metrics = CalculationMetrics(
                timestamp=datetime.now(timezone.utc),
                total_calculations=total_calc,
                successful_calculations=successful_calc,
                failed_calculations=failed_calc,
                average_calculation_time=avg_calc_time,
                calculations_per_second=calc_per_second,
                cache_hit_rate=cache_hit_rate,
                active_satellites=cached_satellites
            )
            
            self.calculation_metrics.append(metrics)
            
            # 添加個別指標
            self.add_metric("sgp4_calculations_per_second", calc_per_second, "ops/sec")
            self.add_metric("sgp4_cache_hit_rate", cache_hit_rate, "percent")
            self.add_metric("sgp4_active_satellites", cached_satellites, "count")
            self.add_metric("sgp4_success_rate", (successful_calc / max(total_calc, 1)) * 100, "percent")
            
            # 檢查 SGP4 性能告警
            self._check_sgp4_alerts(metrics)
            
        except Exception as e:
            logger.error(f"收集 SGP4 指標失敗: {e}")
    
    def record_api_request(self, success: bool, response_time: float, endpoint: str = ""):
        """記錄 API 請求指標"""
        try:
            context = {"endpoint": endpoint, "success": success}
            
            # 記錄響應時間
            self.add_metric("api_response_time", response_time, "seconds", context)
            
            # 記錄請求計數
            self.add_metric("api_request_count", 1, "count", context)
            
        except Exception as e:
            logger.error(f"記錄 API 請求失敗: {e}")
    
    def _check_system_alerts(self, snapshot: SystemSnapshot):
        """檢查系統告警"""
        alerts = []
        
        # CPU 使用率告警
        if snapshot.cpu_percent > 80:
            alerts.append({
                "type": "high_cpu_usage",
                "severity": "warning" if snapshot.cpu_percent < 90 else "critical",
                "value": snapshot.cpu_percent,
                "threshold": 80,
                "message": f"CPU 使用率過高: {snapshot.cpu_percent:.1f}%"
            })
        
        # 內存使用率告警
        if snapshot.memory_percent > 85:
            alerts.append({
                "type": "high_memory_usage",
                "severity": "warning" if snapshot.memory_percent < 95 else "critical",
                "value": snapshot.memory_percent,
                "threshold": 85,
                "message": f"內存使用率過高: {snapshot.memory_percent:.1f}%"
            })
        
        # 可用內存告警
        if snapshot.memory_available_mb < 500:
            alerts.append({
                "type": "low_available_memory",
                "severity": "critical",
                "value": snapshot.memory_available_mb,
                "threshold": 500,
                "message": f"可用內存過低: {snapshot.memory_available_mb:.0f}MB"
            })
        
        # 觸發告警回調
        for alert in alerts:
            self._trigger_alert("system_alert", alert)
    
    def _check_sgp4_alerts(self, metrics: CalculationMetrics):
        """檢查 SGP4 性能告警"""
        alerts = []
        
        # 計算成功率告警
        success_rate = (metrics.successful_calculations / max(metrics.total_calculations, 1)) * 100
        if success_rate < 95:
            alerts.append({
                "type": "low_sgp4_success_rate",
                "severity": "warning" if success_rate > 90 else "critical",
                "value": success_rate,
                "threshold": 95,
                "message": f"SGP4 計算成功率過低: {success_rate:.1f}%"
            })
        
        # 計算速度告警
        if metrics.calculations_per_second > 0 and metrics.calculations_per_second < 100:
            alerts.append({
                "type": "slow_sgp4_calculations",
                "severity": "warning",
                "value": metrics.calculations_per_second,
                "threshold": 100,
                "message": f"SGP4 計算速度過慢: {metrics.calculations_per_second:.1f} ops/sec"
            })
        
        # 緩存命中率告警
        if metrics.cache_hit_rate < 80:
            alerts.append({
                "type": "low_cache_hit_rate",
                "severity": "warning",
                "value": metrics.cache_hit_rate,
                "threshold": 80,
                "message": f"SGP4 緩存命中率過低: {metrics.cache_hit_rate:.1f}%"
            })
        
        # 觸發告警回調
        for alert in alerts:
            self._trigger_alert("sgp4_alert", alert)
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict):
        """觸發告警回調"""
        try:
            for callback in self.alert_callbacks:
                callback(alert_type, alert_data)
        except Exception as e:
            logger.error(f"觸發告警回調失敗: {e}")
    
    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """添加告警回調函數"""
        self.alert_callbacks.append(callback)
    
    def start_collection(self):
        """開始性能數據收集"""
        if self.is_collecting:
            logger.warning("性能收集已在運行中")
            return
        
        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info("性能數據收集已開始")
    
    def stop_collection(self):
        """停止性能數據收集"""
        self.is_collecting = False
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5)
        
        logger.info("性能數據收集已停止")
    
    def _collection_loop(self):
        """性能收集循環"""
        while self.is_collecting:
            try:
                # 收集系統指標
                self.collect_system_metrics()
                
                # 等待下次收集
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"性能收集循環異常: {e}")
                time.sleep(5)  # 錯誤後等待更長時間

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, collector: PerformanceCollector):
        """
        初始化分析器
        
        Args:
            collector: 性能收集器實例
        """
        self.collector = collector
        logger.info("性能分析器初始化完成")
    
    def analyze_system_trends(self, time_window_minutes: int = 30) -> Dict[str, Any]:
        """分析系統性能趨勢"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
            
            # 篩選時間窗口內的數據
            recent_snapshots = [
                s for s in self.collector.system_snapshots 
                if s.timestamp >= cutoff_time
            ]
            
            if not recent_snapshots:
                return {"error": "沒有足夠的數據進行趨勢分析"}
            
            # CPU 使用趨勢
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            cpu_trend = self._calculate_trend(cpu_values)
            
            # 內存使用趨勢
            memory_values = [s.memory_percent for s in recent_snapshots]
            memory_trend = self._calculate_trend(memory_values)
            
            # 計算統計數據
            analysis = {
                "time_window_minutes": time_window_minutes,
                "sample_count": len(recent_snapshots),
                "cpu_analysis": {
                    "current": cpu_values[-1] if cpu_values else 0,
                    "average": np.mean(cpu_values) if cpu_values else 0,
                    "max": np.max(cpu_values) if cpu_values else 0,
                    "min": np.min(cpu_values) if cpu_values else 0,
                    "trend": cpu_trend
                },
                "memory_analysis": {
                    "current": memory_values[-1] if memory_values else 0,
                    "average": np.mean(memory_values) if memory_values else 0,
                    "max": np.max(memory_values) if memory_values else 0,
                    "min": np.min(memory_values) if memory_values else 0,
                    "trend": memory_trend
                },
                "thread_analysis": {
                    "current": recent_snapshots[-1].active_threads if recent_snapshots else 0,
                    "average": np.mean([s.active_threads for s in recent_snapshots]) if recent_snapshots else 0
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"系統趨勢分析失敗: {e}")
            return {"error": f"分析失敗: {e}"}
    
    def analyze_sgp4_performance(self, time_window_minutes: int = 15) -> Dict[str, Any]:
        """分析 SGP4 性能"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
            
            # 篩選時間窗口內的數據
            recent_metrics = [
                m for m in self.collector.calculation_metrics
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {"error": "沒有足夠的 SGP4 性能數據"}
            
            # 計算性能指標
            calc_rates = [m.calculations_per_second for m in recent_metrics if m.calculations_per_second > 0]
            cache_rates = [m.cache_hit_rate for m in recent_metrics]
            success_rates = [
                (m.successful_calculations / max(m.total_calculations, 1)) * 100 
                for m in recent_metrics
            ]
            
            analysis = {
                "time_window_minutes": time_window_minutes,
                "sample_count": len(recent_metrics),
                "calculation_performance": {
                    "current_rate": calc_rates[-1] if calc_rates else 0,
                    "average_rate": np.mean(calc_rates) if calc_rates else 0,
                    "max_rate": np.max(calc_rates) if calc_rates else 0,
                    "rate_trend": self._calculate_trend(calc_rates) if calc_rates else "stable"
                },
                "cache_performance": {
                    "current_hit_rate": cache_rates[-1] if cache_rates else 0,
                    "average_hit_rate": np.mean(cache_rates) if cache_rates else 0,
                    "hit_rate_trend": self._calculate_trend(cache_rates) if cache_rates else "stable"
                },
                "accuracy_performance": {
                    "current_success_rate": success_rates[-1] if success_rates else 0,
                    "average_success_rate": np.mean(success_rates) if success_rates else 0,
                    "success_rate_trend": self._calculate_trend(success_rates) if success_rates else "stable"
                },
                "active_satellites": recent_metrics[-1].active_satellites if recent_metrics else 0
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"SGP4 性能分析失敗: {e}")
            return {"error": f"分析失敗: {e}"}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """計算數值趨勢"""
        if len(values) < 2:
            return "stable"
        
        try:
            # 使用線性回歸計算趨勢
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            # 根據斜率判斷趨勢
            if slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能報告"""
        try:
            # 系統趨勢分析
            system_analysis = self.analyze_system_trends(30)
            
            # SGP4 性能分析
            sgp4_analysis = self.analyze_sgp4_performance(15)
            
            # 最近的指標
            recent_metrics = list(self.collector.metrics)[-100:] if self.collector.metrics else []
            
            # 按類型分組指標
            metric_groups = defaultdict(list)
            for metric in recent_metrics:
                metric_groups[metric.metric_name].append(metric.value)
            
            # 計算指標統計
            metric_stats = {}
            for name, values in metric_groups.items():
                if values:
                    metric_stats[name] = {
                        "current": values[-1],
                        "average": np.mean(values),
                        "max": np.max(values),
                        "min": np.min(values)
                    }
            
            report = {
                "report_timestamp": datetime.now(timezone.utc).isoformat(),
                "report_period": "Last 30 minutes",
                "system_analysis": system_analysis,
                "sgp4_analysis": sgp4_analysis,
                "metric_statistics": metric_stats,
                "data_points": {
                    "total_metrics": len(self.collector.metrics),
                    "system_snapshots": len(self.collector.system_snapshots),
                    "calculation_metrics": len(self.collector.calculation_metrics)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成性能報告失敗: {e}")
            return {"error": f"報告生成失敗: {e}"}

class PerformanceMonitor:
    """Phase 1 性能監控主類"""
    
    def __init__(self, collection_interval: float = 1.0):
        """
        初始化性能監控器
        
        Args:
            collection_interval: 數據收集間隔（秒）
        """
        self.collector = PerformanceCollector(collection_interval)
        self.analyzer = PerformanceAnalyzer(self.collector)
        self.sgp4_engine = None
        
        # 設置默認告警處理
        self.collector.add_alert_callback(self._default_alert_handler)
        
        logger.info("✅ Phase 1 性能監控器初始化完成")
    
    def set_sgp4_engine(self, sgp4_engine):
        """設置要監控的 SGP4 引擎"""
        self.sgp4_engine = sgp4_engine
        logger.info("SGP4 引擎已設置為監控目標")
    
    def start_monitoring(self):
        """開始性能監控"""
        try:
            self.collector.start_collection()
            
            # 啟動定期 SGP4 指標收集
            if self.sgp4_engine:
                self._start_sgp4_monitoring()
            
            logger.info("✅ Phase 1 性能監控已啟動")
            
        except Exception as e:
            logger.error(f"啟動性能監控失敗: {e}")
            raise
    
    def stop_monitoring(self):
        """停止性能監控"""
        try:
            self.collector.stop_collection()
            logger.info("Phase 1 性能監控已停止")
            
        except Exception as e:
            logger.error(f"停止性能監控失敗: {e}")
    
    def _start_sgp4_monitoring(self):
        """啟動 SGP4 監控線程"""
        def sgp4_monitor_loop():
            while self.collector.is_collecting:
                try:
                    if self.sgp4_engine:
                        self.collector.collect_sgp4_metrics(self.sgp4_engine)
                    time.sleep(5)  # SGP4 指標每5秒收集一次
                except Exception as e:
                    logger.error(f"SGP4 監控循環異常: {e}")
                    time.sleep(10)
        
        sgp4_thread = threading.Thread(target=sgp4_monitor_loop, daemon=True)
        sgp4_thread.start()
        logger.info("SGP4 性能監控線程已啟動")
    
    def record_api_request(self, success: bool, response_time: float, endpoint: str = ""):
        """記錄 API 請求（供外部調用）"""
        self.collector.record_api_request(success, response_time, endpoint)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前性能指標"""
        try:
            return {
                "system": self.analyzer.analyze_system_trends(5),
                "sgp4": self.analyzer.analyze_sgp4_performance(5),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"獲取當前指標失敗: {e}")
            return {"error": str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取詳細性能報告"""
        return self.analyzer.generate_performance_report()
    
    def _default_alert_handler(self, alert_type: str, alert_data: Dict):
        """默認告警處理器"""
        severity = alert_data.get("severity", "info")
        message = alert_data.get("message", "性能告警")
        
        log_func = logger.warning if severity == "warning" else logger.error
        log_func(f"[{alert_type}] {message}")
    
    def add_custom_alert_handler(self, handler: Callable[[str, Dict], None]):
        """添加自定義告警處理器"""
        self.collector.add_alert_callback(handler)
    
    def export_metrics(self, output_path: str):
        """導出性能指標到文件"""
        try:
            report = self.get_performance_report()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"性能指標已導出到: {output_path}")
            
        except Exception as e:
            logger.error(f"導出性能指標失敗: {e}")

# 便利函數
def create_performance_monitor(collection_interval: float = 1.0) -> PerformanceMonitor:
    """創建性能監控器實例"""
    return PerformanceMonitor(collection_interval)

if __name__ == "__main__":
    # 測試用例
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("Phase 1 性能監控系統測試")
        print("=" * 40)
        
        # 創建監控器
        monitor = create_performance_monitor(0.5)  # 0.5秒間隔快速測試
        
        # 開始監控
        monitor.start_monitoring()
        
        # 運行一段時間收集數據
        print("收集性能數據中...")
        time.sleep(10)
        
        # 獲取當前指標
        current = monitor.get_current_metrics()
        print(f"當前系統指標: CPU {current.get('system', {}).get('cpu_analysis', {}).get('current', 0):.1f}%")
        
        # 生成性能報告
        report = monitor.get_performance_report()
        print(f"性能報告生成: {len(report)} 個部分")
        
        # 導出指標
        export_path = "/tmp/phase1_performance_test.json"
        monitor.export_metrics(export_path)
        print(f"性能指標已導出: {export_path}")
        
        # 停止監控
        monitor.stop_monitoring()
        print("✅ 性能監控測試完成")
        
    except Exception as e:
        print(f"❌ 性能監控測試失敗: {e}")
        import traceback
        traceback.print_exc()