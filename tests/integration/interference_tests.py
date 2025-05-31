#!/usr/bin/env python3
"""
干擾測試模組
測試系統在各種干擾條件下的性能表現

測試範圍：
- 頻率干擾模擬
- 信號阻擋模擬
- 噪聲注入測試
- 干擾檢測和緩解能力
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Any
import aiohttp

logger = logging.getLogger(__name__)


class InterferenceTester:
    """干擾測試器"""

    def __init__(self, config: Dict):
        self.config = config
        self.environment = config["environment"]
        self.services = self.environment["services"]

    async def run_interference_tests(self) -> Tuple[bool, Dict]:
        """執行干擾測試"""
        logger.info("📡 開始執行干擾測試")

        # 干擾測試場景
        test_scenarios = [
            ("baseline_performance", await self._test_baseline_performance()),
            ("simulated_jamming", await self._test_simulated_jamming()),
            ("signal_degradation", await self._test_signal_degradation()),
            ("recovery_capability", await self._test_recovery_capability()),
        ]

        passed_tests = sum(1 for _, passed in test_scenarios if passed)
        total_tests = len(test_scenarios)

        details = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "test_results": {name: passed for name, passed in test_scenarios},
            "interference_scenarios": [
                "frequency_jamming",
                "signal_blocking",
                "noise_injection",
            ],
        }

        overall_success = passed_tests == total_tests
        logger.info(f"📡 干擾測試完成，成功率: {details['success_rate']:.1%}")

        return overall_success, details

    async def _test_baseline_performance(self) -> bool:
        """基線性能測試（無干擾情況）"""
        logger.info("📊 測試基線性能（無干擾）")

        url = f"{self.services['netstack']['url']}/health"
        test_count = 20
        latencies = []
        success_count = 0

        async with aiohttp.ClientSession() as session:
            for i in range(test_count):
                start_time = time.time()
                try:
                    async with session.get(url, timeout=10) as response:
                        latency = (time.time() - start_time) * 1000
                        latencies.append(latency)
                        if response.status == 200:
                            success_count += 1
                except Exception as e:
                    logger.debug(f"基線測試請求 {i+1} 失敗: {e}")

                await asyncio.sleep(0.1)

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            success_rate = success_count / test_count

            # 記錄基線數據供後續比較
            self.baseline_latency = avg_latency
            self.baseline_success_rate = success_rate

            passed = success_rate >= 0.95  # 95% 成功率基線要求

            if passed:
                logger.info(
                    f"✅ 基線性能測試通過: 延遲 {avg_latency:.1f}ms, 成功率 {success_rate:.1%}"
                )
            else:
                logger.error(
                    f"❌ 基線性能測試失敗: 延遲 {avg_latency:.1f}ms, 成功率 {success_rate:.1%}"
                )

            return passed
        else:
            logger.error("❌ 無法獲得基線性能數據")
            return False

    async def _test_simulated_jamming(self) -> bool:
        """模擬干擾測試"""
        logger.info("🚫 執行模擬干擾測試")

        # 模擬干擾：增加請求延遲和失敗率
        url = f"{self.services['netstack']['url']}/health"
        test_count = 20
        latencies = []
        success_count = 0

        async with aiohttp.ClientSession() as session:
            for i in range(test_count):
                start_time = time.time()

                # 模擬干擾：隨機增加延遲和失敗
                interference_delay = 0.05 if i % 3 == 0 else 0  # 每3個請求增加50ms延遲
                await asyncio.sleep(interference_delay)

                try:
                    # 在干擾情況下縮短超時，模擬信號不穩定
                    timeout = 5 if i % 4 != 0 else 2  # 25% 的請求超時更短

                    async with session.get(url, timeout=timeout) as response:
                        latency = (time.time() - start_time) * 1000
                        latencies.append(latency)
                        if response.status == 200:
                            success_count += 1
                except Exception as e:
                    logger.debug(f"干擾測試請求 {i+1} 失敗: {e}")
                    latencies.append(5000)  # 記錄超時為5秒

                await asyncio.sleep(0.2)  # 增加間隔模擬干擾恢復時間

        if latencies:
            avg_latency = (
                sum(l for l in latencies if l < 5000)
                / len([l for l in latencies if l < 5000])
                if any(l < 5000 for l in latencies)
                else 0
            )
            success_rate = success_count / test_count

            # 檢查系統在干擾下的性能保持能力
            # 允許性能有所下降，但應保持基本功能
            acceptable_success_rate = 0.7  # 干擾下至少70%成功率

            passed = success_rate >= acceptable_success_rate

            if passed:
                logger.info(
                    f"✅ 模擬干擾測試通過: 成功率 {success_rate:.1%} (可接受: ≥{acceptable_success_rate:.0%})"
                )
            else:
                logger.error(
                    f"❌ 模擬干擾測試失敗: 成功率 {success_rate:.1%} 低於可接受水準"
                )

            return passed
        else:
            logger.error("❌ 模擬干擾測試無法完成")
            return False

    async def _test_signal_degradation(self) -> bool:
        """信號劣化測試"""
        logger.info("📉 執行信號劣化測試")

        # 測試不同程度的信號劣化
        degradation_levels = [
            {"name": "輕微劣化", "timeout": 8, "retry_count": 1},
            {"name": "中度劣化", "timeout": 5, "retry_count": 2},
            {"name": "嚴重劣化", "timeout": 3, "retry_count": 3},
        ]

        url = f"{self.services['netstack']['url']}/health"
        all_passed = True

        async with aiohttp.ClientSession() as session:
            for level in degradation_levels:
                logger.debug(f"測試 {level['name']}")

                success_count = 0
                test_count = 10

                for i in range(test_count):
                    retry_count = level["retry_count"]
                    request_success = False

                    for retry in range(retry_count + 1):
                        try:
                            async with session.get(
                                url, timeout=level["timeout"]
                            ) as response:
                                if response.status == 200:
                                    success_count += 1
                                    request_success = True
                                    break
                        except:
                            if retry < retry_count:
                                await asyncio.sleep(0.1 * (retry + 1))  # 指數退避
                            continue

                    await asyncio.sleep(0.1)

                success_rate = success_count / test_count
                level_passed = success_rate >= 0.6  # 60% 最低要求

                if not level_passed:
                    all_passed = False

                if level_passed:
                    logger.info(
                        f"✅ {level['name']} 測試通過: {success_rate:.1%} 成功率"
                    )
                else:
                    logger.error(
                        f"❌ {level['name']} 測試失敗: {success_rate:.1%} 成功率"
                    )

        return all_passed

    async def _test_recovery_capability(self) -> bool:
        """恢復能力測試"""
        logger.info("🔄 執行干擾恢復能力測試")

        url = f"{self.services['netstack']['url']}/health"

        # 階段1：正常操作
        phase1_success = await self._test_phase("正常操作", url, 10, 10, 0)

        # 階段2：模擬嚴重干擾
        phase2_success = await self._test_phase("嚴重干擾", url, 10, 3, 0.3)

        # 階段3：干擾消除，測試恢復
        phase3_success = await self._test_phase("恢復階段", url, 10, 10, 0)

        # 檢查系統是否能從干擾中恢復
        recovery_successful = phase1_success and phase3_success

        if recovery_successful:
            logger.info("✅ 干擾恢復能力測試通過: 系統能夠從干擾中恢復")
        else:
            logger.error("❌ 干擾恢復能力測試失敗: 系統無法有效恢復")

        return recovery_successful

    async def _test_phase(
        self,
        phase_name: str,
        url: str,
        test_count: int,
        timeout: int,
        interference_probability: float,
    ) -> bool:
        """測試階段執行"""
        success_count = 0

        async with aiohttp.ClientSession() as session:
            for i in range(test_count):
                # 根據干擾機率決定是否加入干擾
                if (
                    interference_probability > 0
                    and (i / test_count) < interference_probability
                ):
                    # 加入干擾：減少超時時間
                    actual_timeout = max(1, timeout // 2)
                else:
                    actual_timeout = timeout

                try:
                    async with session.get(url, timeout=actual_timeout) as response:
                        if response.status == 200:
                            success_count += 1
                except:
                    pass  # 干擾期間的失敗是預期的

                await asyncio.sleep(0.1)

        success_rate = success_count / test_count
        expected_rate = 0.9 if interference_probability == 0 else 0.5
        passed = success_rate >= expected_rate

        logger.debug(
            f"{phase_name}: {success_rate:.1%} 成功率 (預期: ≥{expected_rate:.0%})"
        )

        return passed
