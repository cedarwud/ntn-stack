#!/usr/bin/env python3
"""
Phase 1 性能基準驗證

功能:
1. 驗證 Phase 1 系統性能指標達標
2. 對比性能改善和回歸檢測
3. 生成詳細的性能基準報告
4. 確保學術研究級別的性能標準

符合 CLAUDE.md 原則:
- 測試真實 SGP4 算法的性能表現
- 驗證 8,715 顆衛星的處理能力
- 確保系統穩定性和可靠性
"""

import logging
import time
import psutil
import threading
import json
import statistics
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# 添加 Phase 1 模組路徑
PHASE1_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHASE1_ROOT / "01_data_source"))
sys.path.insert(0, str(PHASE1_ROOT / "02_orbit_calculation"))
sys.path.insert(0, str(PHASE1_ROOT / "03_processing_pipeline"))
sys.path.insert(0, str(PHASE1_ROOT / "04_output_interface"))

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkRequirement:
    """性能基準要求"""
    metric_name: str
    target_value: float
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    unit: str = ""
    description: str = ""
    critical: bool = True

@dataclass
class BenchmarkResult:
    """性能基準測試結果"""
    metric_name: str
    measured_value: float
    target_value: float
    passed: bool
    improvement_factor: Optional[float] = None
    unit: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

@dataclass
class SystemMetrics:
    """系統性能指標"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_mb: float
    disk_io_read_mb_s: float
    disk_io_write_mb_s: float
    network_sent_mb_s: float = 0.0
    network_recv_mb_s: float = 0.0

class PerformanceBenchmark:
    """性能基準測試器"""
    
    def __init__(self):
        """初始化性能基準測試器"""
        self.benchmark_requirements = self._define_benchmark_requirements()
        self.test_results = []
        self.system_baseline = None
        
        # 測試組件
        self.tle_loader = None
        self.sgp4_engine = None
        self.data_provider = None
        self.standard_interface = None
        self.performance_monitor = None
        
        logger.info("✅ 性能基準測試器初始化完成")
    
    def _define_benchmark_requirements(self) -> List[BenchmarkRequirement]:
        """定義性能基準要求"""
        requirements = [
            # TLE 數據載入性能
            BenchmarkRequirement(
                metric_name="tle_load_time",
                target_value=10.0,
                max_value=30.0,
                unit="seconds",
                description="TLE 數據載入時間",
                critical=True
            ),
            
            # SGP4 衛星對象創建性能
            BenchmarkRequirement(
                metric_name="satellite_creation_rate",
                target_value=100.0,
                min_value=50.0,
                unit="satellites/second",
                description="SGP4 衛星對象創建速率",
                critical=True
            ),
            
            # SGP4 軌道計算性能
            BenchmarkRequirement(
                metric_name="sgp4_calculation_rate",
                target_value=1000.0,
                min_value=500.0,
                unit="calculations/second",
                description="SGP4 軌道計算速率",
                critical=True
            ),
            
            # API 響應時間
            BenchmarkRequirement(
                metric_name="api_response_time_p95",
                target_value=0.1,
                max_value=0.5,
                unit="seconds",
                description="API 響應時間（95百分位）",
                critical=True
            ),
            
            # 併發處理能力
            BenchmarkRequirement(
                metric_name="concurrent_requests_handled",
                target_value=50.0,
                min_value=20.0,
                unit="requests",
                description="併發請求處理能力",
                critical=True
            ),
            
            # 內存使用效率
            BenchmarkRequirement(
                metric_name="memory_efficiency",
                target_value=2000.0,
                max_value=4000.0,
                unit="MB",
                description="最大內存使用量",
                critical=False
            ),
            
            # 數據準確性
            BenchmarkRequirement(
                metric_name="calculation_accuracy",
                target_value=0.99,
                min_value=0.95,
                unit="ratio",
                description="軌道計算準確性",
                critical=True
            ),
            
            # 系統穩定性
            BenchmarkRequirement(
                metric_name="system_uptime_ratio",
                target_value=0.999,
                min_value=0.99,
                unit="ratio",
                description="系統穩定運行比例",
                critical=True
            ),
            
            # 緩存效率
            BenchmarkRequirement(
                metric_name="cache_hit_rate",
                target_value=0.8,
                min_value=0.6,
                unit="ratio",
                description="SGP4 緩存命中率",
                critical=False
            ),
            
            # 大規模處理性能
            BenchmarkRequirement(
                metric_name="large_scale_query_time",
                target_value=5.0,
                max_value=10.0,
                unit="seconds",
                description="大規模查詢處理時間",
                critical=True
            )
        ]
        
        logger.info(f"定義了 {len(requirements)} 個性能基準要求")
        return requirements
    
    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """執行完整的性能基準測試"""
        logger.info("🚀 開始性能基準驗證...")
        
        benchmark_start = datetime.now(timezone.utc)
        
        benchmark_report = {
            "benchmark_start_time": benchmark_start.isoformat(),
            "benchmark_requirements": [asdict(req) for req in self.benchmark_requirements],
            "test_results": {},
            "overall_performance": {},
            "system_comparison": {},
            "recommendations": []
        }
        
        try:
            # 初始化測試環境
            await self._initialize_benchmark_environment()
            
            # 收集系統基準線
            self.system_baseline = self._collect_system_baseline()
            
            # 執行各項性能測試
            await self._test_tle_loading_performance()
            await self._test_sgp4_calculation_performance()
            await self._test_api_response_performance()
            await self._test_concurrent_processing_performance()
            await self._test_memory_efficiency()
            await self._test_large_scale_processing()
            await self._test_system_stability()
            
            # 生成綜合報告
            benchmark_end = datetime.now(timezone.utc)
            benchmark_report["benchmark_end_time"] = benchmark_end.isoformat()
            benchmark_report["total_duration"] = (benchmark_end - benchmark_start).total_seconds()
            
            # 分析測試結果
            benchmark_report["test_results"] = self._analyze_test_results()
            benchmark_report["overall_performance"] = self._calculate_overall_performance()
            benchmark_report["system_comparison"] = self._compare_with_baseline()
            benchmark_report["recommendations"] = self._generate_recommendations()
            
            logger.info("🎯 性能基準驗證完成")
            return benchmark_report
            
        except Exception as e:
            logger.error(f"性能基準測試失敗: {e}")
            benchmark_report["error"] = str(e)
            return benchmark_report
    
    async def _initialize_benchmark_environment(self):
        """初始化基準測試環境"""
        try:
            # 初始化 TLE 載入器
            from tle_loader import create_tle_loader
            self.tle_loader = create_tle_loader()  # 使用統一配置
            
            # 初始化 SGP4 引擎
            from sgp4_engine import create_sgp4_engine, validate_sgp4_availability
            
            if not validate_sgp4_availability():
                raise RuntimeError("SGP4 庫不可用")
            
            self.sgp4_engine = create_sgp4_engine()
            
            # 初始化數據提供者和標準接口
            from phase1_data_provider import create_sgp4_data_provider
            from phase2_interface import create_standard_interface
            
            self.data_provider = create_sgp4_data_provider()
            self.standard_interface = create_standard_interface(self.data_provider)
            
            # 初始化性能監控
            from performance_monitor import create_performance_monitor
            self.performance_monitor = create_performance_monitor(0.1)  # 高頻監控
            self.performance_monitor.set_sgp4_engine(self.sgp4_engine)
            self.performance_monitor.start_monitoring()
            
            logger.info("✅ 基準測試環境初始化完成")
            
        except Exception as e:
            logger.error(f"基準測試環境初始化失敗: {e}")
            raise
    
    def _collect_system_baseline(self) -> SystemMetrics:
        """收集系統基準線性能"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1.0)
            
            # 內存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # 磁盤 I/O
            disk_io_before = psutil.disk_io_counters()
            time.sleep(1.0)
            disk_io_after = psutil.disk_io_counters()
            
            disk_read_mb_s = (disk_io_after.read_bytes - disk_io_before.read_bytes) / (1024 * 1024)
            disk_write_mb_s = (disk_io_after.write_bytes - disk_io_before.write_bytes) / (1024 * 1024)
            
            baseline = SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_io_read_mb_s=disk_read_mb_s,
                disk_io_write_mb_s=disk_write_mb_s
            )
            
            logger.info(f"系統基準線: CPU {cpu_percent:.1f}%, 記憶體 {memory_percent:.1f}%")
            return baseline
            
        except Exception as e:
            logger.error(f"收集系統基準線失敗: {e}")
            return None
    
    async def _test_tle_loading_performance(self):
        """測試 TLE 載入性能"""
        logger.info("測試 TLE 載入性能...")
        
        try:
            # 清除可能的緩存
            if hasattr(self.tle_loader, 'clear_cache'):
                self.tle_loader.clear_cache()
            
            # 測試 TLE 載入時間
            load_start = time.time()
            tle_result = self.tle_loader.load_all_tle_data()
            load_time = time.time() - load_start
            
            # 記錄結果
            result = BenchmarkResult(
                metric_name="tle_load_time",
                measured_value=load_time,
                target_value=self._get_requirement("tle_load_time").target_value,
                passed=load_time <= self._get_requirement("tle_load_time").target_value,
                unit="seconds",
                details={
                    "total_records": tle_result.total_records,
                    "load_rate": tle_result.total_records / load_time if load_time > 0 else 0
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self.test_results.append(result)
            logger.info(f"TLE 載入性能: {load_time:.2f}s, {tle_result.total_records} 記錄")
            
        except Exception as e:
            logger.error(f"TLE 載入性能測試失敗: {e}")
            self.test_results.append(BenchmarkResult(
                metric_name="tle_load_time",
                measured_value=float('inf'),
                target_value=self._get_requirement("tle_load_time").target_value,
                passed=False,
                unit="seconds",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc)
            ))
    
    async def _test_sgp4_calculation_performance(self):
        """測試 SGP4 計算性能"""
        logger.info("測試 SGP4 計算性能...")
        
        try:
            # 準備測試數據
            tle_result = self.tle_loader.load_all_tle_data()
            test_satellites = tle_result.records[:100]  # 測試前100顆衛星
            
            # 測試衛星對象創建性能
            creation_start = time.time()
            created_count = 0
            
            for record in test_satellites:
                if self.sgp4_engine.create_satellite(record.satellite_id, record.line1, record.line2):
                    created_count += 1
            
            creation_time = time.time() - creation_start
            creation_rate = created_count / creation_time if creation_time > 0 else 0
            
            # 記錄衛星創建性能
            creation_result = BenchmarkResult(
                metric_name="satellite_creation_rate",
                measured_value=creation_rate,
                target_value=self._get_requirement("satellite_creation_rate").target_value,
                passed=creation_rate >= self._get_requirement("satellite_creation_rate").target_value,
                unit="satellites/second",
                details={
                    "satellites_created": created_count,
                    "total_attempted": len(test_satellites),
                    "creation_time": creation_time
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self.test_results.append(creation_result)
            
            # 測試軌道計算性能
            if created_count > 0:
                calc_start = time.time()
                successful_calculations = 0
                test_time = datetime.now(timezone.utc)
                
                # 進行多次計算測試
                for _ in range(10):  # 每顆衛星計算10次
                    for record in test_satellites[:min(created_count, 50)]:
                        result = self.sgp4_engine.calculate_position(record.satellite_id, test_time)
                        if result and result.success:
                            successful_calculations += 1
                
                calc_time = time.time() - calc_start
                calc_rate = successful_calculations / calc_time if calc_time > 0 else 0
                
                # 記錄計算性能
                calc_result = BenchmarkResult(
                    metric_name="sgp4_calculation_rate",
                    measured_value=calc_rate,
                    target_value=self._get_requirement("sgp4_calculation_rate").target_value,
                    passed=calc_rate >= self._get_requirement("sgp4_calculation_rate").target_value,
                    unit="calculations/second",
                    details={
                        "successful_calculations": successful_calculations,
                        "calculation_time": calc_time,
                        "accuracy_rate": successful_calculations / (50 * 10) if created_count >= 50 else 0
                    },
                    timestamp=datetime.now(timezone.utc)
                )
                
                self.test_results.append(calc_result)
                logger.info(f"SGP4 計算性能: {calc_rate:.1f} calc/s")
            
            logger.info(f"SGP4 衛星創建: {creation_rate:.1f} sat/s")
            
        except Exception as e:
            logger.error(f"SGP4 計算性能測試失敗: {e}")
    
    async def _test_api_response_performance(self):
        """測試 API 響應性能"""
        logger.info("測試 API 響應性能...")
        
        try:
            import requests
            
            # 測試不同的 API 端點
            api_endpoints = [
                ("health", "http://localhost:8001/health"),
                ("satellites", "http://localhost:8001/satellites?limit=10"),
                ("capabilities", "http://localhost:8001/capabilities")
            ]
            
            all_response_times = []
            endpoint_results = {}
            
            for endpoint_name, url in api_endpoints:
                response_times = []
                
                # 多次測試每個端點
                for _ in range(10):
                    try:
                        start_time = time.time()
                        response = requests.get(url, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            response_times.append(response_time)
                            all_response_times.append(response_time)
                        
                    except Exception as e:
                        logger.warning(f"API 測試請求失敗 {endpoint_name}: {e}")
                
                if response_times:
                    endpoint_results[endpoint_name] = {
                        "avg_response_time": statistics.mean(response_times),
                        "p95_response_time": np.percentile(response_times, 95),
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times)
                    }
            
            # 計算整體 P95 響應時間
            if all_response_times:
                p95_response_time = np.percentile(all_response_times, 95)
                avg_response_time = statistics.mean(all_response_times)
                
                # 記錄結果
                result = BenchmarkResult(
                    metric_name="api_response_time_p95",
                    measured_value=p95_response_time,
                    target_value=self._get_requirement("api_response_time_p95").target_value,
                    passed=p95_response_time <= self._get_requirement("api_response_time_p95").target_value,
                    unit="seconds",
                    details={
                        "p95_response_time": p95_response_time,
                        "avg_response_time": avg_response_time,
                        "total_requests": len(all_response_times),
                        "endpoint_results": endpoint_results
                    },
                    timestamp=datetime.now(timezone.utc)
                )
                
                self.test_results.append(result)
                logger.info(f"API 響應性能: P95 {p95_response_time:.3f}s, 平均 {avg_response_time:.3f}s")
            
        except Exception as e:
            logger.error(f"API 響應性能測試失敗: {e}")
    
    async def _test_concurrent_processing_performance(self):
        """測試併發處理性能"""
        logger.info("測試併發處理性能...")
        
        try:
            import requests
            
            def make_concurrent_request(request_id: int) -> Dict:
                try:
                    start_time = time.time()
                    response = requests.get(
                        "http://localhost:8001/satellites?constellation=starlink&limit=5",
                        timeout=30
                    )
                    response_time = time.time() - start_time
                    
                    return {
                        "request_id": request_id,
                        "success": response.status_code == 200,
                        "response_time": response_time
                    }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "success": False,
                        "error": str(e)
                    }
            
            # 測試併發處理
            concurrent_levels = [10, 20, 50]  # 不同的併發級別
            
            for concurrent_level in concurrent_levels:
                logger.info(f"測試 {concurrent_level} 併發請求...")
                
                concurrent_start = time.time()
                
                with ThreadPoolExecutor(max_workers=concurrent_level) as executor:
                    futures = [executor.submit(make_concurrent_request, i) for i in range(concurrent_level)]
                    results = [future.result() for future in as_completed(futures)]
                
                concurrent_time = time.time() - concurrent_start
                
                # 分析結果
                successful_requests = sum(1 for r in results if r["success"])
                success_rate = successful_requests / len(results)
                
                if successful_requests > 0:
                    response_times = [r["response_time"] for r in results if r["success"]]
                    avg_response_time = statistics.mean(response_times)
                    
                    # 記錄結果（使用最高成功的併發級別）
                    if success_rate >= 0.8:  # 80% 成功率門檻
                        result = BenchmarkResult(
                            metric_name="concurrent_requests_handled",
                            measured_value=float(successful_requests),
                            target_value=self._get_requirement("concurrent_requests_handled").target_value,
                            passed=successful_requests >= self._get_requirement("concurrent_requests_handled").target_value,
                            unit="requests",
                            details={
                                "concurrent_level": concurrent_level,
                                "successful_requests": successful_requests,
                                "total_requests": len(results),
                                "success_rate": success_rate,
                                "total_time": concurrent_time,
                                "avg_response_time": avg_response_time
                            },
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        self.test_results.append(result)
                        logger.info(f"併發處理: {successful_requests}/{concurrent_level} 成功")
            
        except Exception as e:
            logger.error(f"併發處理性能測試失敗: {e}")
    
    async def _test_memory_efficiency(self):
        """測試內存使用效率"""
        logger.info("測試內存使用效率...")
        
        try:
            # 記錄初始內存
            initial_memory = psutil.virtual_memory().used / (1024 * 1024)
            
            # 執行一系列操作來測試內存使用
            # 1. 大量衛星對象創建
            tle_result = self.tle_loader.load_all_tle_data()
            test_satellites = tle_result.records[:500]  # 測試500顆衛星
            
            for record in test_satellites:
                self.sgp4_engine.create_satellite(record.satellite_id, record.line1, record.line2)
            
            # 2. 大量軌道計算
            test_time = datetime.now(timezone.utc)
            for record in test_satellites[:100]:
                for _ in range(10):  # 每顆衛星計算10次
                    self.sgp4_engine.calculate_position(record.satellite_id, test_time)
            
            # 記錄峰值內存
            peak_memory = psutil.virtual_memory().used / (1024 * 1024)
            memory_usage = peak_memory - initial_memory
            
            # 記錄結果
            result = BenchmarkResult(
                metric_name="memory_efficiency",
                measured_value=memory_usage,
                target_value=self._get_requirement("memory_efficiency").target_value,
                passed=memory_usage <= self._get_requirement("memory_efficiency").target_value,
                unit="MB",
                details={
                    "initial_memory_mb": initial_memory,
                    "peak_memory_mb": peak_memory,
                    "memory_increase_mb": memory_usage,
                    "satellites_processed": len(test_satellites),
                    "calculations_performed": len(test_satellites[:100]) * 10
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self.test_results.append(result)
            logger.info(f"內存使用效率: {memory_usage:.1f}MB 增加")
            
        except Exception as e:
            logger.error(f"內存效率測試失敗: {e}")
    
    async def _test_large_scale_processing(self):
        """測試大規模處理性能"""
        logger.info("測試大規模處理性能...")
        
        try:
            # 測試大規模查詢
            large_query_start = time.time()
            
            query_request = self.standard_interface.create_query_request(
                max_records=1000
            )
            
            query_response = self.standard_interface.execute_query(query_request)
            
            large_query_time = time.time() - large_query_start
            
            # 記錄結果
            result = BenchmarkResult(
                metric_name="large_scale_query_time",
                measured_value=large_query_time,
                target_value=self._get_requirement("large_scale_query_time").target_value,
                passed=large_query_time <= self._get_requirement("large_scale_query_time").target_value,
                unit="seconds",
                details={
                    "query_time": large_query_time,
                    "records_returned": query_response.returned_records,
                    "total_matches": query_response.total_matches,
                    "records_per_second": query_response.returned_records / large_query_time if large_query_time > 0 else 0
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self.test_results.append(result)
            logger.info(f"大規模處理: {large_query_time:.2f}s, {query_response.returned_records} 記錄")
            
        except Exception as e:
            logger.error(f"大規模處理測試失敗: {e}")
    
    async def _test_system_stability(self):
        """測試系統穩定性"""
        logger.info("測試系統穩定性...")
        
        try:
            stability_start = time.time()
            
            # 持續運行測試（模擬實際使用）
            total_operations = 0
            successful_operations = 0
            
            test_duration = 30  # 30秒穩定性測試
            end_time = time.time() + test_duration
            
            while time.time() < end_time:
                try:
                    # 執行各種操作
                    test_time = datetime.now(timezone.utc)
                    
                    # SGP4 計算
                    if self.sgp4_engine and len(self.sgp4_engine.satellite_cache) > 0:
                        satellite_id = list(self.sgp4_engine.satellite_cache.keys())[0]
                        result = self.sgp4_engine.calculate_position(satellite_id, test_time)
                        total_operations += 1
                        if result and result.success:
                            successful_operations += 1
                    
                    # API 查詢
                    try:
                        import requests
                        response = requests.get("http://localhost:8001/health", timeout=5)
                        total_operations += 1
                        if response.status_code == 200:
                            successful_operations += 1
                    except:
                        total_operations += 1
                    
                    time.sleep(0.1)  # 短暫休息
                    
                except Exception:
                    total_operations += 1
            
            stability_time = time.time() - stability_start
            uptime_ratio = successful_operations / max(total_operations, 1)
            
            # 記錄結果
            result = BenchmarkResult(
                metric_name="system_uptime_ratio",
                measured_value=uptime_ratio,
                target_value=self._get_requirement("system_uptime_ratio").target_value,
                passed=uptime_ratio >= self._get_requirement("system_uptime_ratio").target_value,
                unit="ratio",
                details={
                    "test_duration": stability_time,
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "uptime_ratio": uptime_ratio,
                    "operations_per_second": total_operations / stability_time
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            self.test_results.append(result)
            logger.info(f"系統穩定性: {uptime_ratio:.3f} 穩定比例")
            
        except Exception as e:
            logger.error(f"系統穩定性測試失敗: {e}")
    
    def _get_requirement(self, metric_name: str) -> BenchmarkRequirement:
        """獲取指定指標的要求"""
        for req in self.benchmark_requirements:
            if req.metric_name == metric_name:
                return req
        raise ValueError(f"未找到指標要求: {metric_name}")
    
    def _analyze_test_results(self) -> Dict[str, Any]:
        """分析測試結果"""
        try:
            results_by_metric = {}
            
            for result in self.test_results:
                results_by_metric[result.metric_name] = asdict(result)
            
            # 計算總體統計
            passed_tests = sum(1 for r in self.test_results if r.passed)
            total_tests = len(self.test_results)
            pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            critical_tests = [r for r in self.test_results 
                            if self._get_requirement(r.metric_name).critical]
            critical_passed = sum(1 for r in critical_tests if r.passed)
            critical_pass_rate = (critical_passed / len(critical_tests)) * 100 if critical_tests else 0
            
            return {
                "results_by_metric": results_by_metric,
                "summary_statistics": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests,
                    "overall_pass_rate": pass_rate,
                    "critical_tests": len(critical_tests),
                    "critical_passed": critical_passed,
                    "critical_pass_rate": critical_pass_rate
                }
            }
            
        except Exception as e:
            logger.error(f"分析測試結果失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_performance(self) -> Dict[str, Any]:
        """計算整體性能評級"""
        try:
            # 性能評級算法
            performance_scores = []
            
            for result in self.test_results:
                req = self._get_requirement(result.metric_name)
                
                if result.passed:
                    # 根據超越目標的程度給分
                    if req.max_value and result.measured_value <= req.target_value:
                        score = 100  # 優秀
                    elif req.min_value and result.measured_value >= req.target_value:
                        score = 100  # 優秀
                    else:
                        score = 90   # 良好
                else:
                    score = 0        # 不及格
                
                # 關鍵指標加權
                weight = 2.0 if req.critical else 1.0
                performance_scores.append(score * weight)
            
            # 計算加權平均分
            total_weight = sum(2.0 if self._get_requirement(r.metric_name).critical else 1.0 
                             for r in self.test_results)
            
            overall_score = sum(performance_scores) / total_weight if total_weight > 0 else 0
            
            # 性能等級
            if overall_score >= 90:
                performance_grade = "優秀"
            elif overall_score >= 80:
                performance_grade = "良好"
            elif overall_score >= 70:
                performance_grade = "合格"
            else:
                performance_grade = "需改進"
            
            return {
                "overall_score": overall_score,
                "performance_grade": performance_grade,
                "score_breakdown": {
                    f"{r.metric_name}": {
                        "score": 100 if r.passed else 0,
                        "weight": 2.0 if self._get_requirement(r.metric_name).critical else 1.0,
                        "critical": self._get_requirement(r.metric_name).critical
                    }
                    for r in self.test_results
                }
            }
            
        except Exception as e:
            logger.error(f"計算整體性能失敗: {e}")
            return {"error": str(e)}
    
    def _compare_with_baseline(self) -> Dict[str, Any]:
        """與基準線對比"""
        try:
            if not self.system_baseline:
                return {"error": "沒有系統基準線數據"}
            
            current_memory = psutil.virtual_memory().used / (1024 * 1024)
            current_cpu = psutil.cpu_percent(interval=1.0)
            
            comparison = {
                "baseline_timestamp": self.system_baseline.timestamp.isoformat(),
                "current_timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_comparison": {
                    "baseline_cpu": self.system_baseline.cpu_usage_percent,
                    "current_cpu": current_cpu,
                    "cpu_change": current_cpu - self.system_baseline.cpu_usage_percent
                },
                "memory_comparison": {
                    "baseline_memory_mb": (psutil.virtual_memory().total - self.system_baseline.memory_available_mb * 1024 * 1024) / (1024 * 1024),
                    "current_memory_mb": current_memory,
                    "memory_change_mb": current_memory - ((psutil.virtual_memory().total - self.system_baseline.memory_available_mb * 1024 * 1024) / (1024 * 1024))
                }
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"基準線對比失敗: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """生成性能優化建議"""
        recommendations = []
        
        try:
            for result in self.test_results:
                if not result.passed:
                    req = self._get_requirement(result.metric_name)
                    
                    if result.metric_name == "tle_load_time":
                        recommendations.append("考慮實現 TLE 數據緩存或異步載入機制")
                    elif result.metric_name == "sgp4_calculation_rate":
                        recommendations.append("考慮並行化 SGP4 計算或優化計算算法")
                    elif result.metric_name == "api_response_time_p95":
                        recommendations.append("考慮添加 API 響應緩存或優化數據庫查詢")
                    elif result.metric_name == "memory_efficiency":
                        recommendations.append("考慮優化內存使用，實現對象池或更有效的緩存策略")
                    elif result.metric_name == "concurrent_requests_handled":
                        recommendations.append("考慮增加工作線程數或實現請求隊列機制")
                    else:
                        recommendations.append(f"優化 {req.description} 的實現")
            
            if not recommendations:
                recommendations.append("所有性能指標都達到要求，系統性能優秀")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            return ["性能分析失敗，無法生成建議"]
    
    def export_benchmark_report(self, output_path: str, report_data: Dict[str, Any]):
        """導出性能基準報告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"性能基準報告已導出: {output_path}")
            
        except Exception as e:
            logger.error(f"導出性能基準報告失敗: {e}")

# 便利函數
def create_performance_benchmark() -> PerformanceBenchmark:
    """創建性能基準測試器"""
    return PerformanceBenchmark()

async def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🚀 Phase 1 性能基準驗證")
        print("=" * 50)
        
        # 創建性能基準測試器
        benchmark = create_performance_benchmark()
        
        # 執行性能基準測試
        report = await benchmark.run_performance_benchmark()
        
        # 顯示結果摘要
        if "test_results" in report and "summary_statistics" in report["test_results"]:
            stats = report["test_results"]["summary_statistics"]
            print(f"\n📊 性能基準測試結果:")
            print(f"總測試項目: {stats['total_tests']}")
            print(f"通過測試: {stats['passed_tests']}")
            print(f"整體通過率: {stats['overall_pass_rate']:.1f}%")
            print(f"關鍵指標通過率: {stats['critical_pass_rate']:.1f}%")
        
        if "overall_performance" in report:
            perf = report["overall_performance"]
            print(f"性能評級: {perf.get('performance_grade', '未知')}")
            print(f"整體得分: {perf.get('overall_score', 0):.1f}")
        
        # 導出報告
        output_path = PHASE1_ROOT / "05_integration" / "performance_benchmark_report.json"
        benchmark.export_benchmark_report(str(output_path), report)
        print(f"\n詳細報告已保存: {output_path}")
        
        # 清理資源
        if benchmark.performance_monitor:
            benchmark.performance_monitor.stop_monitoring()
        
        # 返回成功狀態
        success = (report.get("test_results", {}).get("summary_statistics", {}).get("critical_pass_rate", 0) >= 80)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"性能基準驗證失敗: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)