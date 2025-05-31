#!/usr/bin/env python3
"""
負載測試模組
測試系統在高負載情況下的性能表現

測試範圍：
- 高並發負載測試
- 持續負載測試
- 資源消耗測試
- 負載下的延遲測試
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Any
import aiohttp

logger = logging.getLogger(__name__)


class LoadTester:
    """負載測試器"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]

    async def run_load_tests(self) -> Tuple[bool, Dict]:
        """執行負載測試"""
        logger.info("🔥 開始執行負載測試")

        # 負載測試場景
        test_scenarios = [
            ("high_concurrency", await self._test_high_concurrency()),
            ("sustained_load", await self._test_sustained_load()),
            ("spike_load", await self._test_spike_load()),
        ]

        passed_tests = sum(1 for _, passed in test_scenarios if passed)
        total_tests = len(test_scenarios)

        details = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "test_results": {name: passed for name, passed in test_scenarios},
        }

        overall_success = passed_tests == total_tests
        logger.info(f"🔥 負載測試完成，成功率: {details['success_rate']:.1%}")

        return overall_success, details

    async def _test_high_concurrency(self) -> bool:
        """高並發測試"""
        logger.info("⚡ 執行高並發測試")

        concurrent_requests = 100
        url = f"{self.services['netstack']['url']}/health"

        async def make_request(session):
            try:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
            except:
                return False

        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if r is True)
            success_rate = success_count / concurrent_requests

            passed = success_rate >= 0.8  # 80% 成功率門檻

            if passed:
                logger.info(f"✅ 高並發測試通過: {success_rate:.1%} 成功率")
            else:
                logger.error(f"❌ 高並發測試失敗: {success_rate:.1%} 成功率")

            return passed

    async def _test_sustained_load(self) -> bool:
        """持續負載測試"""
        logger.info("⏱️ 執行持續負載測試")

        duration = 30  # 30 秒持續負載
        request_interval = 0.1  # 每 100ms 一個請求
        url = f"{self.services['netstack']['url']}/health"

        start_time = time.time()
        success_count = 0
        total_count = 0

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                try:
                    async with session.get(url, timeout=5) as response:
                        total_count += 1
                        if response.status == 200:
                            success_count += 1
                except:
                    total_count += 1

                await asyncio.sleep(request_interval)

        success_rate = success_count / total_count if total_count > 0 else 0
        passed = success_rate >= 0.9  # 90% 成功率門檻

        if passed:
            logger.info(f"✅ 持續負載測試通過: {success_rate:.1%} 成功率")
        else:
            logger.error(f"❌ 持續負載測試失敗: {success_rate:.1%} 成功率")

        return passed

    async def _test_spike_load(self) -> bool:
        """突增負載測試"""
        logger.info("📈 執行突增負載測試")

        # 模擬流量突增：正常負載 -> 高負載 -> 正常負載
        url = f"{self.services['netstack']['url']}/health"

        async def burst_requests(session, count):
            tasks = []
            for _ in range(count):
                tasks.append(session.get(url, timeout=10))

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(
                1 for r in responses if hasattr(r, "status") and r.status == 200
            )

            # 關閉所有響應
            for r in responses:
                if hasattr(r, "close"):
                    r.close()

            return success_count, len(responses)

        async with aiohttp.ClientSession() as session:
            # 正常負載
            normal_success, normal_total = await burst_requests(session, 10)
            await asyncio.sleep(1)

            # 突增負載
            spike_success, spike_total = await burst_requests(session, 50)
            await asyncio.sleep(1)

            # 恢復正常
            recovery_success, recovery_total = await burst_requests(session, 10)

        # 檢查系統是否能處理突增並恢復
        spike_success_rate = spike_success / spike_total if spike_total > 0 else 0
        recovery_success_rate = (
            recovery_success / recovery_total if recovery_total > 0 else 0
        )

        passed = spike_success_rate >= 0.7 and recovery_success_rate >= 0.9

        if passed:
            logger.info(
                f"✅ 突增負載測試通過: 突增期 {spike_success_rate:.1%}, 恢復期 {recovery_success_rate:.1%}"
            )
        else:
            logger.error(
                f"❌ 突增負載測試失敗: 突增期 {spike_success_rate:.1%}, 恢復期 {recovery_success_rate:.1%}"
            )

        return passed
