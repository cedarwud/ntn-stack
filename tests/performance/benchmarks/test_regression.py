#!/usr/bin/env python3
"""
自動化性能回歸測試機制
實現階段七要求的性能基準線比較和自動化回歸檢測

功能：
1. 建立性能基準線
2. 自動化性能回歸檢測
3. 性能趨勢分析
4. 自動化回歸測試執行
5. 性能基準管理
6. 回歸測試報告生成
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import numpy as np
import sqlite3
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import structlog

from .load_tests import LoadTestSuite, LoadTestResult
from .stress_tests import StressTestSuite, StressTestResult
from ..e2e.e2e_test_framework import E2ETestFramework

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceBenchmark:
    """性能基準線"""
    
    test_name: str
    version: str
    timestamp: datetime
    metrics: Dict[str, float]
    environment: str
    test_config: Dict[str, Any]
    baseline_type: str = "stable"  # stable, development, release
    confidence_interval: float = 0.95
    
    
@dataclass 
class RegressionTestResult:
    """回歸測試結果"""
    
    test_name: str
    current_version: str
    baseline_version: str
    test_timestamp: datetime
    regression_detected: bool
    performance_change_percent: Dict[str, float]
    significance_level: float
    degraded_metrics: List[str] = field(default_factory=list)
    improved_metrics: List[str] = field(default_factory=list)
    stable_metrics: List[str] = field(default_factory=list)
    test_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """性能趨勢分析"""
    
    metric_name: str
    trend_direction: str  # improving, degrading, stable
    trend_slope: float
    confidence: float
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)
    prediction: Optional[float] = None
    

class PerformanceBenchmarkManager:
    """性能基準管理器"""
    
    def __init__(self, db_path: str = "tests/reports/performance_benchmarks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="benchmark_manager")
        self._init_database()
    
    def _init_database(self):
        """初始化數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建基準線表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                version TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metrics TEXT NOT NULL,
                environment TEXT NOT NULL,
                test_config TEXT NOT NULL,
                baseline_type TEXT NOT NULL,
                confidence_interval REAL NOT NULL,
                UNIQUE(test_name, version, environment, baseline_type)
            )
        ''')
        
        # 創建回歸測試結果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regression_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                current_version TEXT NOT NULL,
                baseline_version TEXT NOT NULL,
                test_timestamp TEXT NOT NULL,
                regression_detected INTEGER NOT NULL,
                performance_change TEXT NOT NULL,
                significance_level REAL NOT NULL,
                degraded_metrics TEXT,
                improved_metrics TEXT,
                stable_metrics TEXT,
                test_details TEXT
            )
        ''')
        
        # 創建性能趨勢表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                test_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                value REAL NOT NULL,
                version TEXT NOT NULL,
                environment TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("性能基準數據庫初始化完成")
    
    async def save_benchmark(self, benchmark: PerformanceBenchmark):
        """保存性能基準線"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO benchmarks 
                (test_name, version, timestamp, metrics, environment, test_config, baseline_type, confidence_interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                benchmark.test_name,
                benchmark.version,
                benchmark.timestamp.isoformat(),
                json.dumps(benchmark.metrics),
                benchmark.environment,
                json.dumps(benchmark.test_config),
                benchmark.baseline_type,
                benchmark.confidence_interval
            ))
            
            # 同時保存到趨勢數據
            for metric_name, value in benchmark.metrics.items():
                cursor.execute('''
                    INSERT INTO performance_trends 
                    (metric_name, test_name, timestamp, value, version, environment)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric_name,
                    benchmark.test_name,
                    benchmark.timestamp.isoformat(),
                    value,
                    benchmark.version,
                    benchmark.environment
                ))
            
            conn.commit()
            self.logger.info(f"已保存性能基準線: {benchmark.test_name} v{benchmark.version}")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"保存基準線失敗: {e}")
            raise
        finally:
            conn.close()
    
    async def get_baseline(self, test_name: str, environment: str = "development", 
                          baseline_type: str = "stable") -> Optional[PerformanceBenchmark]:
        """獲取性能基準線"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT test_name, version, timestamp, metrics, environment, test_config, baseline_type, confidence_interval
                FROM benchmarks 
                WHERE test_name = ? AND environment = ? AND baseline_type = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (test_name, environment, baseline_type))
            
            row = cursor.fetchone()
            if row:
                return PerformanceBenchmark(
                    test_name=row[0],
                    version=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    metrics=json.loads(row[3]),
                    environment=row[4],
                    test_config=json.loads(row[5]),
                    baseline_type=row[6],
                    confidence_interval=row[7]
                )
            return None
            
        except Exception as e:
            self.logger.error(f"獲取基準線失敗: {e}")
            return None
        finally:
            conn.close()
    
    async def save_regression_result(self, result: RegressionTestResult):
        """保存回歸測試結果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO regression_results 
                (test_name, current_version, baseline_version, test_timestamp, regression_detected,
                 performance_change, significance_level, degraded_metrics, improved_metrics, 
                 stable_metrics, test_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.test_name,
                result.current_version,
                result.baseline_version,
                result.test_timestamp.isoformat(),
                1 if result.regression_detected else 0,
                json.dumps(result.performance_change_percent),
                result.significance_level,
                json.dumps(result.degraded_metrics),
                json.dumps(result.improved_metrics),
                json.dumps(result.stable_metrics),
                json.dumps(result.test_details)
            ))
            
            conn.commit()
            self.logger.info(f"已保存回歸測試結果: {result.test_name}")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"保存回歸測試結果失敗: {e}")
            raise
        finally:
            conn.close()
    
    async def get_performance_trends(self, test_name: str, metric_name: str, 
                                   days: int = 30) -> List[Tuple[datetime, float]]:
        """獲取性能趨勢數據"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT timestamp, value FROM performance_trends 
                WHERE test_name = ? AND metric_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            ''', (test_name, metric_name, since_date))
            
            return [(datetime.fromisoformat(row[0]), row[1]) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"獲取性能趨勢失敗: {e}")
            return []
        finally:
            conn.close()


class StatisticalAnalyzer:
    """統計分析器"""
    
    @staticmethod
    def detect_regression(baseline_metrics: Dict[str, float], current_metrics: Dict[str, float],
                         significance_threshold: float = 0.05) -> Tuple[bool, Dict[str, float], List[str], List[str]]:
        """檢測性能回歸"""
        
        performance_changes = {}
        degraded_metrics = []
        improved_metrics = []
        
        for metric_name in baseline_metrics:
            if metric_name not in current_metrics:
                continue
                
            baseline_value = baseline_metrics[metric_name]
            current_value = current_metrics[metric_name]
            
            if baseline_value == 0:
                change_percent = 0
            else:
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
            
            performance_changes[metric_name] = change_percent
            
            # 根據指標類型判斷是否為回歸
            # 對於延遲、錯誤率等指標，增加是回歸
            # 對於吞吐量、成功率等指標，減少是回歸
            if metric_name in ['latency_ms', 'response_time_ms', 'error_rate', 'cpu_usage_percent', 'memory_usage_mb']:
                if change_percent > significance_threshold * 100:  # 增加超過閾值為回歸
                    degraded_metrics.append(metric_name)
                elif change_percent < -significance_threshold * 100:  # 減少超過閾值為改善
                    improved_metrics.append(metric_name)
            else:  # throughput, success_rate 等
                if change_percent < -significance_threshold * 100:  # 減少超過閾值為回歸
                    degraded_metrics.append(metric_name)
                elif change_percent > significance_threshold * 100:  # 增加超過閾值為改善
                    improved_metrics.append(metric_name)
        
        regression_detected = len(degraded_metrics) > 0
        
        return regression_detected, performance_changes, degraded_metrics, improved_metrics
    
    @staticmethod
    def analyze_trend(data_points: List[Tuple[datetime, float]]) -> PerformanceTrend:
        """分析性能趨勢"""
        if len(data_points) < 3:
            return PerformanceTrend(
                metric_name="unknown",
                trend_direction="insufficient_data",
                trend_slope=0.0,
                confidence=0.0,
                data_points=data_points
            )
        
        # 將時間轉換為數值進行線性回歸
        timestamps = [dp[0] for dp in data_points]
        values = [dp[1] for dp in data_points]
        
        # 轉換時間為相對秒數
        base_time = timestamps[0]
        x_values = [(ts - base_time).total_seconds() for ts in timestamps]
        
        # 執行線性回歸
        slope, intercept = np.polyfit(x_values, values, 1)
        
        # 計算相關係數作為信心度
        correlation = np.corrcoef(x_values, values)[0, 1]
        confidence = abs(correlation)
        
        # 確定趨勢方向
        if abs(slope) < 0.001:  # 幾乎沒有變化
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        # 預測下一個時間點的值
        next_time = x_values[-1] + 3600  # 1小時後
        prediction = slope * next_time + intercept
        
        return PerformanceTrend(
            metric_name="unknown",
            trend_direction=direction,
            trend_slope=slope,
            confidence=confidence,
            data_points=data_points,
            prediction=prediction
        )


class PerformanceRegressionTester:
    """性能回歸測試器"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.logger = logger.bind(component="regression_tester")
        self.benchmark_manager = PerformanceBenchmarkManager()
        self.statistical_analyzer = StatisticalAnalyzer()
        
        # 測試套件
        self.load_test_suite = LoadTestSuite()
        self.stress_test_suite = StressTestSuite()
        self.e2e_test_framework = E2ETestFramework()
        
        # 報告目錄
        self.reports_dir = Path("tests/reports/regression")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def establish_baseline(self, version: str, test_config: Dict[str, Any],
                               baseline_type: str = "stable") -> Dict[str, PerformanceBenchmark]:
        """建立性能基準線"""
        self.logger.info(f"開始建立性能基準線 v{version} ({baseline_type})")
        
        benchmarks = {}
        
        # 執行負載測試基準
        load_baseline = await self._establish_load_test_baseline(version, test_config, baseline_type)
        if load_baseline:
            benchmarks["load_test"] = load_baseline
        
        # 執行壓力測試基準
        stress_baseline = await self._establish_stress_test_baseline(version, test_config, baseline_type)
        if stress_baseline:
            benchmarks["stress_test"] = stress_baseline
        
        # 執行E2E測試基準
        e2e_baseline = await self._establish_e2e_test_baseline(version, test_config, baseline_type)
        if e2e_baseline:
            benchmarks["e2e_test"] = e2e_baseline
        
        self.logger.info(f"完成基準線建立，共 {len(benchmarks)} 個測試類型")
        return benchmarks
    
    async def _establish_load_test_baseline(self, version: str, test_config: Dict[str, Any], 
                                          baseline_type: str) -> Optional[PerformanceBenchmark]:
        """建立負載測試基準線"""
        try:
            # 執行多次測試以獲得穩定基準
            results = []
            for i in range(3):  # 執行3次
                self.logger.info(f"執行負載測試基準線 - 第 {i+1} 次")
                result = await self.load_test_suite.run_concurrent_load_test(
                    concurrent_users=test_config.get("load_concurrent_users", 50),
                    duration_seconds=test_config.get("load_duration_seconds", 60),
                    base_url=test_config.get("base_url", "http://localhost:8080")
                )
                results.append(result)
                await asyncio.sleep(10)  # 間隔10秒
            
            # 計算平均值作為基準
            metrics = {
                "success_rate": statistics.mean([r["success_rate"] for r in results]),
                "avg_response_time_ms": statistics.mean([r["avg_response_time_ms"] for r in results]),
                "requests_per_second": statistics.mean([r["requests_per_second"] for r in results])
            }
            
            benchmark = PerformanceBenchmark(
                test_name="load_test_concurrent",
                version=version,
                timestamp=datetime.now(),
                metrics=metrics,
                environment=self.environment,
                test_config=test_config,
                baseline_type=baseline_type
            )
            
            await self.benchmark_manager.save_benchmark(benchmark)
            return benchmark
            
        except Exception as e:
            self.logger.error(f"建立負載測試基準線失敗: {e}")
            return None
    
    async def _establish_stress_test_baseline(self, version: str, test_config: Dict[str, Any], 
                                           baseline_type: str) -> Optional[PerformanceBenchmark]:
        """建立壓力測試基準線"""
        try:
            stress_config = {
                "base_url": test_config.get("base_url", "http://localhost:8080"),
                "max_concurrent_requests": test_config.get("stress_max_concurrent", 200),
                "test_duration_seconds": test_config.get("stress_duration_seconds", 120)
            }
            
            result = await self.stress_test_suite.run_comprehensive_stress_tests(stress_config)
            
            # 從壓力測試結果中提取關鍵指標
            stress_details = result.get("stress_test_details", [])
            if not stress_details:
                return None
            
            # 計算綜合指標
            success_rates = [detail["success_rate"] for detail in stress_details]
            response_times = [detail["avg_response_time_ms"] for detail in stress_details]
            cpu_usages = [detail["cpu_peak_percent"] for detail in stress_details]
            
            metrics = {
                "avg_success_rate": statistics.mean(success_rates) if success_rates else 0,
                "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
                "peak_cpu_usage_percent": max(cpu_usages) if cpu_usages else 0,
                "overall_success_rate": result["success_rate"]
            }
            
            benchmark = PerformanceBenchmark(
                test_name="stress_test_comprehensive",
                version=version,
                timestamp=datetime.now(),
                metrics=metrics,
                environment=self.environment,
                test_config=stress_config,
                baseline_type=baseline_type
            )
            
            await self.benchmark_manager.save_benchmark(benchmark)
            return benchmark
            
        except Exception as e:
            self.logger.error(f"建立壓力測試基準線失敗: {e}")
            return None
    
    async def _establish_e2e_test_baseline(self, version: str, test_config: Dict[str, Any], 
                                        baseline_type: str) -> Optional[PerformanceBenchmark]:
        """建立E2E測試基準線"""
        try:
            # 執行E2E測試
            success = await self.e2e_test_framework.run_all_scenarios()
            
            # 從性能監控器獲取指標
            performance_metrics = self.e2e_test_framework.performance_monitor.get_average_metrics(5)
            
            if not performance_metrics:
                return None
            
            metrics = {
                "e2e_success": 1.0 if success else 0.0,
                "avg_latency_ms": performance_metrics.get("avg_latency_ms", 0),
                "avg_throughput_mbps": performance_metrics.get("avg_throughput_mbps", 0),
                "avg_cpu_usage_percent": performance_metrics.get("avg_cpu_usage_percent", 0),
                "avg_memory_usage_mb": performance_metrics.get("avg_memory_usage_mb", 0),
                "avg_error_rate": performance_metrics.get("avg_error_rate", 0)
            }
            
            benchmark = PerformanceBenchmark(
                test_name="e2e_test_comprehensive",
                version=version,
                timestamp=datetime.now(),
                metrics=metrics,
                environment=self.environment,
                test_config=test_config,
                baseline_type=baseline_type
            )
            
            await self.benchmark_manager.save_benchmark(benchmark)
            return benchmark
            
        except Exception as e:
            self.logger.error(f"建立E2E測試基準線失敗: {e}")
            return None
    
    async def run_regression_test(self, current_version: str, test_config: Dict[str, Any],
                                significance_threshold: float = 0.1) -> Dict[str, RegressionTestResult]:
        """執行回歸測試"""
        self.logger.info(f"開始執行性能回歸測試 v{current_version}")
        
        regression_results = {}
        
        # 測試負載測試回歸
        load_regression = await self._test_load_regression(current_version, test_config, significance_threshold)
        if load_regression:
            regression_results["load_test"] = load_regression
        
        # 測試壓力測試回歸
        stress_regression = await self._test_stress_regression(current_version, test_config, significance_threshold)
        if stress_regression:
            regression_results["stress_test"] = stress_regression
        
        # 測試E2E測試回歸
        e2e_regression = await self._test_e2e_regression(current_version, test_config, significance_threshold)
        if e2e_regression:
            regression_results["e2e_test"] = e2e_regression
        
        # 生成回歸測試報告
        await self._generate_regression_report(regression_results, current_version)
        
        self.logger.info(f"完成回歸測試，檢測到 {sum(1 for r in regression_results.values() if r.regression_detected)} 個回歸")
        
        return regression_results
    
    async def _test_load_regression(self, current_version: str, test_config: Dict[str, Any],
                                  significance_threshold: float) -> Optional[RegressionTestResult]:
        """測試負載測試回歸"""
        try:
            # 獲取基準線
            baseline = await self.benchmark_manager.get_baseline("load_test_concurrent", self.environment)
            if not baseline:
                self.logger.warning("未找到負載測試基準線")
                return None
            
            # 執行當前測試
            current_result = await self.load_test_suite.run_concurrent_load_test(
                concurrent_users=test_config.get("load_concurrent_users", 50),
                duration_seconds=test_config.get("load_duration_seconds", 60),
                base_url=test_config.get("base_url", "http://localhost:8080")
            )
            
            current_metrics = {
                "success_rate": current_result["success_rate"],
                "avg_response_time_ms": current_result["avg_response_time_ms"],
                "requests_per_second": current_result["requests_per_second"]
            }
            
            # 檢測回歸
            regression_detected, performance_changes, degraded_metrics, improved_metrics = \
                self.statistical_analyzer.detect_regression(
                    baseline.metrics, current_metrics, significance_threshold
                )
            
            stable_metrics = [m for m in current_metrics.keys() 
                            if m not in degraded_metrics and m not in improved_metrics]
            
            result = RegressionTestResult(
                test_name="load_test_concurrent",
                current_version=current_version,
                baseline_version=baseline.version,
                test_timestamp=datetime.now(),
                regression_detected=regression_detected,
                performance_change_percent=performance_changes,
                significance_level=significance_threshold,
                degraded_metrics=degraded_metrics,
                improved_metrics=improved_metrics,
                stable_metrics=stable_metrics,
                test_details={
                    "baseline_metrics": baseline.metrics,
                    "current_metrics": current_metrics,
                    "test_config": test_config
                }
            )
            
            await self.benchmark_manager.save_regression_result(result)
            return result
            
        except Exception as e:
            self.logger.error(f"負載測試回歸檢測失敗: {e}")
            return None
    
    async def _test_stress_regression(self, current_version: str, test_config: Dict[str, Any],
                                    significance_threshold: float) -> Optional[RegressionTestResult]:
        """測試壓力測試回歸"""
        try:
            # 獲取基準線
            baseline = await self.benchmark_manager.get_baseline("stress_test_comprehensive", self.environment)
            if not baseline:
                self.logger.warning("未找到壓力測試基準線")
                return None
            
            # 執行當前測試
            stress_config = {
                "base_url": test_config.get("base_url", "http://localhost:8080"),
                "max_concurrent_requests": test_config.get("stress_max_concurrent", 200),
                "test_duration_seconds": test_config.get("stress_duration_seconds", 120)
            }
            
            current_result = await self.stress_test_suite.run_comprehensive_stress_tests(stress_config)
            
            # 提取當前指標
            stress_details = current_result.get("stress_test_details", [])
            if not stress_details:
                return None
            
            success_rates = [detail["success_rate"] for detail in stress_details]
            response_times = [detail["avg_response_time_ms"] for detail in stress_details]
            cpu_usages = [detail["cpu_peak_percent"] for detail in stress_details]
            
            current_metrics = {
                "avg_success_rate": statistics.mean(success_rates) if success_rates else 0,
                "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
                "peak_cpu_usage_percent": max(cpu_usages) if cpu_usages else 0,
                "overall_success_rate": current_result["success_rate"]
            }
            
            # 檢測回歸
            regression_detected, performance_changes, degraded_metrics, improved_metrics = \
                self.statistical_analyzer.detect_regression(
                    baseline.metrics, current_metrics, significance_threshold
                )
            
            stable_metrics = [m for m in current_metrics.keys() 
                            if m not in degraded_metrics and m not in improved_metrics]
            
            result = RegressionTestResult(
                test_name="stress_test_comprehensive",
                current_version=current_version,
                baseline_version=baseline.version,
                test_timestamp=datetime.now(),
                regression_detected=regression_detected,
                performance_change_percent=performance_changes,
                significance_level=significance_threshold,
                degraded_metrics=degraded_metrics,
                improved_metrics=improved_metrics,
                stable_metrics=stable_metrics,
                test_details={
                    "baseline_metrics": baseline.metrics,
                    "current_metrics": current_metrics,
                    "test_config": stress_config
                }
            )
            
            await self.benchmark_manager.save_regression_result(result)
            return result
            
        except Exception as e:
            self.logger.error(f"壓力測試回歸檢測失敗: {e}")
            return None
    
    async def _test_e2e_regression(self, current_version: str, test_config: Dict[str, Any],
                                 significance_threshold: float) -> Optional[RegressionTestResult]:
        """測試E2E測試回歸"""
        try:
            # 獲取基準線
            baseline = await self.benchmark_manager.get_baseline("e2e_test_comprehensive", self.environment)
            if not baseline:
                self.logger.warning("未找到E2E測試基準線")
                return None
            
            # 執行當前測試
            success = await self.e2e_test_framework.run_all_scenarios()
            performance_metrics = self.e2e_test_framework.performance_monitor.get_average_metrics(5)
            
            if not performance_metrics:
                return None
            
            current_metrics = {
                "e2e_success": 1.0 if success else 0.0,
                "avg_latency_ms": performance_metrics.get("avg_latency_ms", 0),
                "avg_throughput_mbps": performance_metrics.get("avg_throughput_mbps", 0),
                "avg_cpu_usage_percent": performance_metrics.get("avg_cpu_usage_percent", 0),
                "avg_memory_usage_mb": performance_metrics.get("avg_memory_usage_mb", 0),
                "avg_error_rate": performance_metrics.get("avg_error_rate", 0)
            }
            
            # 檢測回歸
            regression_detected, performance_changes, degraded_metrics, improved_metrics = \
                self.statistical_analyzer.detect_regression(
                    baseline.metrics, current_metrics, significance_threshold
                )
            
            stable_metrics = [m for m in current_metrics.keys() 
                            if m not in degraded_metrics and m not in improved_metrics]
            
            result = RegressionTestResult(
                test_name="e2e_test_comprehensive",
                current_version=current_version,
                baseline_version=baseline.version,
                test_timestamp=datetime.now(),
                regression_detected=regression_detected,
                performance_change_percent=performance_changes,
                significance_level=significance_threshold,
                degraded_metrics=degraded_metrics,
                improved_metrics=improved_metrics,
                stable_metrics=stable_metrics,
                test_details={
                    "baseline_metrics": baseline.metrics,
                    "current_metrics": current_metrics,
                    "test_config": test_config
                }
            )
            
            await self.benchmark_manager.save_regression_result(result)
            return result
            
        except Exception as e:
            self.logger.error(f"E2E測試回歸檢測失敗: {e}")
            return None
    
    async def analyze_performance_trends(self, days: int = 30) -> Dict[str, List[PerformanceTrend]]:
        """分析性能趨勢"""
        self.logger.info(f"分析最近 {days} 天的性能趨勢")
        
        trends = {}
        test_names = ["load_test_concurrent", "stress_test_comprehensive", "e2e_test_comprehensive"]
        
        for test_name in test_names:
            test_trends = []
            
            # 獲取不同指標的趨勢數據
            metric_names = ["success_rate", "avg_response_time_ms", "avg_latency_ms", 
                          "avg_cpu_usage_percent", "avg_memory_usage_mb"]
            
            for metric_name in metric_names:
                data_points = await self.benchmark_manager.get_performance_trends(
                    test_name, metric_name, days
                )
                
                if len(data_points) >= 3:
                    trend = self.statistical_analyzer.analyze_trend(data_points)
                    trend.metric_name = metric_name
                    test_trends.append(trend)
            
            if test_trends:
                trends[test_name] = test_trends
        
        return trends
    
    async def _generate_regression_report(self, regression_results: Dict[str, RegressionTestResult], 
                                        current_version: str):
        """生成回歸測試報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"regression_report_{current_version}_{timestamp}.json"
        
        # 計算總體統計
        total_tests = len(regression_results)
        regression_count = sum(1 for r in regression_results.values() if r.regression_detected)
        improvement_count = sum(1 for r in regression_results.values() if r.improved_metrics)
        
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "current_version": current_version,
                "environment": self.environment,
                "total_tests": total_tests,
                "regressions_detected": regression_count,
                "improvements_detected": improvement_count
            },
            "summary": {
                "overall_status": "PASS" if regression_count == 0 else "FAIL",
                "regression_rate": regression_count / total_tests if total_tests > 0 else 0,
                "critical_regressions": [],
                "notable_improvements": []
            },
            "detailed_results": {},
            "recommendations": []
        }
        
        # 填充詳細結果
        for test_name, result in regression_results.items():
            report_data["detailed_results"][test_name] = {
                "regression_detected": result.regression_detected,
                "baseline_version": result.baseline_version,
                "performance_changes": result.performance_change_percent,
                "degraded_metrics": result.degraded_metrics,
                "improved_metrics": result.improved_metrics,
                "stable_metrics": result.stable_metrics,
                "significance_level": result.significance_level
            }
            
            # 識別關鍵回歸
            if result.regression_detected:
                critical_metrics = [m for m in result.degraded_metrics 
                                  if abs(result.performance_change_percent.get(m, 0)) > 20]
                if critical_metrics:
                    report_data["summary"]["critical_regressions"].append({
                        "test": test_name,
                        "metrics": critical_metrics,
                        "max_degradation": max([abs(result.performance_change_percent.get(m, 0)) 
                                              for m in critical_metrics])
                    })
            
            # 識別顯著改善
            if result.improved_metrics:
                significant_improvements = [m for m in result.improved_metrics 
                                          if abs(result.performance_change_percent.get(m, 0)) > 10]
                if significant_improvements:
                    report_data["summary"]["notable_improvements"].append({
                        "test": test_name,
                        "metrics": significant_improvements,
                        "max_improvement": max([abs(result.performance_change_percent.get(m, 0)) 
                                              for m in significant_improvements])
                    })
        
        # 生成建議
        if regression_count > 0:
            report_data["recommendations"].append("發現性能回歸，建議回滾或修復相關變更")
        if improvement_count > 0:
            report_data["recommendations"].append("檢測到性能改善，考慮將此版本設為新基準線")
        if regression_count == 0 and improvement_count == 0:
            report_data["recommendations"].append("性能表現穩定，可以繼續部署")
        
        # 保存報告
        async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report_data, indent=2, ensure_ascii=False, default=str))
        
        self.logger.info(f"回歸測試報告已生成: {report_path}")
        
        # 輸出摘要到日誌
        self.logger.info("=" * 80)
        self.logger.info("📊 性能回歸測試報告摘要")
        self.logger.info("=" * 80)
        self.logger.info(f"版本: {current_version}")
        self.logger.info(f"總測試數: {total_tests}")
        self.logger.info(f"檢測到回歸: {regression_count}")
        self.logger.info(f"檢測到改善: {improvement_count}")
        self.logger.info(f"整體狀態: {report_data['summary']['overall_status']}")
        
        if report_data["summary"]["critical_regressions"]:
            self.logger.warning("⚠️ 關鍵回歸:")
            for cr in report_data["summary"]["critical_regressions"]:
                self.logger.warning(f"  - {cr['test']}: {cr['metrics']} (最大退化: {cr['max_degradation']:.1f}%)")
        
        if report_data["summary"]["notable_improvements"]:
            self.logger.info("✅ 顯著改善:")
            for ni in report_data["summary"]["notable_improvements"]:
                self.logger.info(f"  - {ni['test']}: {ni['metrics']} (最大改善: {ni['max_improvement']:.1f}%)")
        
        self.logger.info("=" * 80)


async def main():
    """主函數 - 示例用法"""
    regression_tester = PerformanceRegressionTester()
    
    test_config = {
        "base_url": "http://localhost:8080",
        "load_concurrent_users": 50,
        "load_duration_seconds": 60,
        "stress_max_concurrent": 200,
        "stress_duration_seconds": 120
    }
    
    # 建立基準線
    print("🎯 建立性能基準線...")
    baselines = await regression_tester.establish_baseline("1.0.0", test_config, "stable")
    print(f"已建立 {len(baselines)} 個基準線")
    
    # 執行回歸測試
    print("\n🔍 執行回歸測試...")
    regression_results = await regression_tester.run_regression_test("1.1.0", test_config)
    
    # 分析性能趨勢
    print("\n📈 分析性能趨勢...")
    trends = await regression_tester.analyze_performance_trends(30)
    
    print(f"\n📊 趨勢分析結果:")
    for test_name, test_trends in trends.items():
        print(f"  {test_name}:")
        for trend in test_trends:
            print(f"    - {trend.metric_name}: {trend.trend_direction} (斜率: {trend.trend_slope:.6f}, 信心度: {trend.confidence:.2f})")


if __name__ == "__main__":
    asyncio.run(main())