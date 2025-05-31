#!/usr/bin/env python3
"""
壓力測試模組
測試系統在極限條件下的性能表現和穩定性

測試範圍：
- 極高負載測試
- 長時間運行穩定性
- 記憶體和 CPU 極限測試
- 同時連接數極限測試
- 系統恢復能力測試
"""

import asyncio
import logging
import psutil
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """壓力測試結果"""

    test_name: str
    peak_load: int
    duration_seconds: float
    success_rate: float
    max_response_time_ms: float
    avg_response_time_ms: float
    memory_peak_mb: float
    cpu_peak_percent: float
    errors_count: int
    system_stable: bool
    recovery_successful: bool


class StressTester:
    """壓力測試器"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]
        self.results: List[StressTestResult] = []

        # 壓力測試參數
        self.max_concurrent_requests = 500
        self.test_duration_seconds = 120
        self.ramp_up_time_seconds = 30

    async def run_stress_tests(self) -> Tuple[bool, Dict]:
        """執行壓力測試套件"""
        logger.info("💥 開始執行壓力測試")

        test_scenarios = [
            ("extreme_load_test", await self._test_extreme_load()),
            ("memory_stress_test", await self._test_memory_stress()),
            ("long_duration_stability", await self._test_long_duration_stability()),
            (
                "concurrent_connections_limit",
                await self._test_concurrent_connections_limit(),
            ),
            ("recovery_after_overload", await self._test_recovery_after_overload()),
        ]

        passed_tests = sum(1 for _, passed in test_scenarios if passed)
        total_tests = len(test_scenarios)

        details = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "test_results": {name: passed for name, passed in test_scenarios},
            "detailed_results": [
                {
                    "test": r.test_name,
                    "peak_load": r.peak_load,
                    "duration": r.duration_seconds,
                    "success_rate": r.success_rate,
                    "avg_response_ms": r.avg_response_time_ms,
                    "system_stable": r.system_stable,
                }
                for r in self.results
            ],
        }

        overall_success = passed_tests == total_tests
        logger.info(f"💥 壓力測試完成，成功率: {details['success_rate']:.1%}")

        return overall_success, details

    async def _test_extreme_load(self) -> bool:
        """極限負載測試"""
        logger.info("🔥 執行極限負載測試")

        test_name = "extreme_load_test"
        start_time = time.time()
        url = f"{self.services['netstack']['url']}/health"

        # 記錄系統資源狀態
        initial_memory = psutil.virtual_memory().used / 1024 / 1024
        peak_memory = initial_memory
        peak_cpu = 0

        response_times = []
        success_count = 0
        total_requests = 0
        errors_count = 0

        # 創建大量並發請求
        semaphore = asyncio.Semaphore(100)  # 限制同時進行的請求數

        async def make_request(session):
            nonlocal success_count, total_requests, errors_count, peak_memory, peak_cpu

            async with semaphore:
                start_req = time.time()
                try:
                    async with session.get(url, timeout=10) as response:
                        response_time = (time.time() - start_req) * 1000
                        response_times.append(response_time)
                        total_requests += 1

                        if response.status == 200:
                            success_count += 1
                        else:
                            errors_count += 1

                        # 監控系統資源
                        current_memory = psutil.virtual_memory().used / 1024 / 1024
                        current_cpu = psutil.cpu_percent()
                        peak_memory = max(peak_memory, current_memory)
                        peak_cpu = max(peak_cpu, current_cpu)

                except Exception as e:
                    total_requests += 1
                    errors_count += 1
                    logger.debug(f"請求失敗: {e}")

        # 逐步增加負載
        async with aiohttp.ClientSession() as session:
            for load_level in [50, 100, 200, 300, 500]:
                logger.debug(f"測試負載級別: {load_level} 並發請求")

                # 創建指定數量的並發請求
                tasks = [make_request(session) for _ in range(load_level)]
                await asyncio.gather(*tasks, return_exceptions=True)

                # 短暫間隔讓系統穩定
                await asyncio.sleep(2)

        total_duration = time.time() - start_time
        success_rate = success_count / total_requests if total_requests > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        # 判斷系統是否穩定
        system_stable = (
            success_rate >= 0.8
            and peak_cpu < 95
            and errors_count < total_requests * 0.2
        )

        result = StressTestResult(
            test_name=test_name,
            peak_load=500,
            duration_seconds=total_duration,
            success_rate=success_rate,
            max_response_time_ms=max_response_time,
            avg_response_time_ms=avg_response_time,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            errors_count=errors_count,
            system_stable=system_stable,
            recovery_successful=True,  # 暫時設為 True
        )

        self.results.append(result)

        if system_stable:
            logger.info(
                f"✅ 極限負載測試通過 - 成功率: {success_rate:.1%}, 峰值負載: 500"
            )
        else:
            logger.error(
                f"❌ 極限負載測試失敗 - 成功率: {success_rate:.1%}, 錯誤數: {errors_count}"
            )

        return system_stable

    async def _test_memory_stress(self) -> bool:
        """記憶體壓力測試"""
        logger.info("🧠 執行記憶體壓力測試")

        test_name = "memory_stress_test"
        start_time = time.time()

        initial_memory = psutil.virtual_memory().used / 1024 / 1024
        peak_memory = initial_memory

        # 持續發送大量請求以增加記憶體使用
        url = f"{self.services['netstack']['url']}/health"
        success_count = 0
        total_requests = 0
        response_times = []

        async with aiohttp.ClientSession() as session:
            # 持續 60 秒的記憶體壓力測試
            end_time = time.time() + 60

            while time.time() < end_time:
                # 批量創建請求
                tasks = []
                for _ in range(20):  # 每批 20 個請求
                    tasks.append(self._memory_stress_request(session, url))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 處理結果
                for result in results:
                    total_requests += 1
                    if isinstance(result, tuple) and result[0]:
                        success_count += 1
                        response_times.append(result[1])

                # 監控記憶體使用
                current_memory = psutil.virtual_memory().used / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)

                # 短暫休息
                await asyncio.sleep(0.5)

        total_duration = time.time() - start_time
        memory_growth = peak_memory - initial_memory
        success_rate = success_count / total_requests if total_requests > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0

        # 判斷記憶體是否穩定（成長不超過 200MB）
        memory_stable = memory_growth < 200
        performance_stable = success_rate >= 0.9

        result = StressTestResult(
            test_name=test_name,
            peak_load=total_requests,
            duration_seconds=total_duration,
            success_rate=success_rate,
            max_response_time_ms=max(response_times) if response_times else 0,
            avg_response_time_ms=avg_response_time,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=psutil.cpu_percent(),
            errors_count=total_requests - success_count,
            system_stable=memory_stable and performance_stable,
            recovery_successful=True,
        )

        self.results.append(result)

        if memory_stable and performance_stable:
            logger.info(
                f"✅ 記憶體壓力測試通過 - 記憶體成長: {memory_growth:.1f}MB, 成功率: {success_rate:.1%}"
            )
        else:
            logger.error(
                f"❌ 記憶體壓力測試失敗 - 記憶體成長: {memory_growth:.1f}MB, 成功率: {success_rate:.1%}"
            )

        return memory_stable and performance_stable

    async def _test_long_duration_stability(self) -> bool:
        """長時間運行穩定性測試"""
        logger.info("⏰ 執行長時間運行穩定性測試 (5分鐘)")

        test_name = "long_duration_stability"
        start_time = time.time()
        test_duration = 300  # 5 分鐘

        url = f"{self.services['netstack']['url']}/health"
        success_count = 0
        total_requests = 0
        response_times = []
        memory_samples = []
        cpu_samples = []

        async with aiohttp.ClientSession() as session:
            end_time = time.time() + test_duration

            while time.time() < end_time:
                # 持續發送穩定負載
                batch_start = time.time()

                # 每秒 5 個請求的穩定負載
                for _ in range(5):
                    start_req = time.time()
                    try:
                        async with session.get(url, timeout=10) as response:
                            response_time = (time.time() - start_req) * 1000
                            response_times.append(response_time)
                            total_requests += 1

                            if response.status == 200:
                                success_count += 1
                    except Exception:
                        total_requests += 1

                # 記錄系統資源
                memory_samples.append(psutil.virtual_memory().used / 1024 / 1024)
                cpu_samples.append(psutil.cpu_percent())

                # 等待到下一秒
                elapsed = time.time() - batch_start
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)

        total_duration = time.time() - start_time
        success_rate = success_count / total_requests if total_requests > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0

        # 分析穩定性
        memory_trend = self._calculate_trend(memory_samples)
        cpu_stability = statistics.stdev(cpu_samples) if len(cpu_samples) > 1 else 0

        # 穩定性判斷標準
        stability_good = (
            success_rate >= 0.95
            and memory_trend < 5.0  # 記憶體成長斜率小於 5MB/分鐘
            and cpu_stability < 20  # CPU 使用率標準差小於 20%
            and avg_response_time < 100  # 平均響應時間小於 100ms
        )

        result = StressTestResult(
            test_name=test_name,
            peak_load=5,  # 每秒 5 個請求
            duration_seconds=total_duration,
            success_rate=success_rate,
            max_response_time_ms=max(response_times) if response_times else 0,
            avg_response_time_ms=avg_response_time,
            memory_peak_mb=max(memory_samples) if memory_samples else 0,
            cpu_peak_percent=max(cpu_samples) if cpu_samples else 0,
            errors_count=total_requests - success_count,
            system_stable=stability_good,
            recovery_successful=True,
        )

        self.results.append(result)

        if stability_good:
            logger.info(
                f"✅ 長時間穩定性測試通過 - 成功率: {success_rate:.1%}, 記憶體趨勢: {memory_trend:.2f}MB/min"
            )
        else:
            logger.error(
                f"❌ 長時間穩定性測試失敗 - 成功率: {success_rate:.1%}, 記憶體趨勢: {memory_trend:.2f}MB/min"
            )

        return stability_good

    async def _test_concurrent_connections_limit(self) -> bool:
        """同時連接數極限測試"""
        logger.info("🔀 執行同時連接數極限測試")

        test_name = "concurrent_connections_limit"
        start_time = time.time()
        url = f"{self.services['netstack']['url']}/health"

        max_successful_connections = 0

        # 測試不同的同時連接數
        for connection_count in [10, 25, 50, 100, 200, 300]:
            logger.debug(f"測試 {connection_count} 同時連接")

            success_count = 0
            tasks = []

            # 創建長時間保持的連接
            async def maintain_connection():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                nonlocal success_count
                                success_count += 1
                                # 保持連接一段時間
                                await asyncio.sleep(5)
                            return True
                except Exception:
                    return False

            # 同時建立指定數量的連接
            tasks = [maintain_connection() for _ in range(connection_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_rate = success_count / connection_count

            if success_rate >= 0.8:  # 80% 成功率
                max_successful_connections = connection_count
                logger.debug(
                    f"✅ {connection_count} 連接測試通過 (成功率: {success_rate:.1%})"
                )
            else:
                logger.debug(
                    f"❌ {connection_count} 連接測試失敗 (成功率: {success_rate:.1%})"
                )
                break

            # 給系統時間恢復
            await asyncio.sleep(3)

        total_duration = time.time() - start_time

        # 判斷是否達到合理的連接數限制
        connection_limit_reasonable = max_successful_connections >= 50

        result = StressTestResult(
            test_name=test_name,
            peak_load=max_successful_connections,
            duration_seconds=total_duration,
            success_rate=1.0 if connection_limit_reasonable else 0.0,
            max_response_time_ms=0,
            avg_response_time_ms=0,
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            errors_count=0,
            system_stable=connection_limit_reasonable,
            recovery_successful=True,
        )

        self.results.append(result)

        if connection_limit_reasonable:
            logger.info(
                f"✅ 同時連接數極限測試通過 - 最大成功連接數: {max_successful_connections}"
            )
        else:
            logger.error(
                f"❌ 同時連接數極限測試失敗 - 最大成功連接數: {max_successful_connections}"
            )

        return connection_limit_reasonable

    async def _test_recovery_after_overload(self) -> bool:
        """超載後恢復能力測試"""
        logger.info("🔄 執行超載後恢復能力測試")

        test_name = "recovery_after_overload"
        start_time = time.time()
        url = f"{self.services['netstack']['url']}/health"

        # 階段 1: 正常負載基線測試
        baseline_success_rate = await self._measure_baseline_performance(url)

        # 階段 2: 超載測試
        await self._apply_overload(url)

        # 階段 3: 恢復期等待
        await asyncio.sleep(10)  # 等待系統恢復

        # 階段 4: 恢復後性能測試
        recovery_success_rate = await self._measure_recovery_performance(url)

        total_duration = time.time() - start_time

        # 判斷恢復是否成功（恢復後性能應該接近基線）
        recovery_successful = recovery_success_rate >= baseline_success_rate * 0.9

        result = StressTestResult(
            test_name=test_name,
            peak_load=1000,  # 超載階段的負載
            duration_seconds=total_duration,
            success_rate=recovery_success_rate,
            max_response_time_ms=0,
            avg_response_time_ms=0,
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            errors_count=0,
            system_stable=True,
            recovery_successful=recovery_successful,
        )

        self.results.append(result)

        if recovery_successful:
            logger.info(
                f"✅ 超載後恢復測試通過 - 基線: {baseline_success_rate:.1%}, 恢復: {recovery_success_rate:.1%}"
            )
        else:
            logger.error(
                f"❌ 超載後恢復測試失敗 - 基線: {baseline_success_rate:.1%}, 恢復: {recovery_success_rate:.1%}"
            )

        return recovery_successful

    # ===== 輔助方法 =====

    async def _memory_stress_request(self, session, url) -> Tuple[bool, float]:
        """記憶體壓力測試的單個請求"""
        start_time = time.time()
        try:
            async with session.get(url, timeout=5) as response:
                response_time = (time.time() - start_time) * 1000
                return response.status == 200, response_time
        except Exception:
            response_time = (time.time() - start_time) * 1000
            return False, response_time

    def _calculate_trend(self, values: List[float]) -> float:
        """計算數值序列的趨勢（斜率）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_values = list(range(n))

        # 計算線性回歸斜率
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope  # 每個時間單位的變化量

    async def _measure_baseline_performance(self, url: str) -> float:
        """測量基線性能"""
        success_count = 0
        total_requests = 20

        async with aiohttp.ClientSession() as session:
            for _ in range(total_requests):
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            success_count += 1
                except Exception:
                    pass
                await asyncio.sleep(0.1)

        return success_count / total_requests

    async def _apply_overload(self, url: str):
        """應用超載壓力"""
        logger.debug("應用超載壓力...")

        async def overload_request(session):
            try:
                async with session.get(url, timeout=1) as response:
                    pass
            except Exception:
                pass

        async with aiohttp.ClientSession() as session:
            # 創建大量並發請求造成超載
            tasks = [overload_request(session) for _ in range(1000)]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _measure_recovery_performance(self, url: str) -> float:
        """測量恢復後性能"""
        success_count = 0
        total_requests = 20

        async with aiohttp.ClientSession() as session:
            for _ in range(total_requests):
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            success_count += 1
                except Exception:
                    pass
                await asyncio.sleep(0.2)

        return success_count / total_requests
