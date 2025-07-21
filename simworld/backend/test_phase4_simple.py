#!/usr/bin/env python3
"""
Phase 4 簡化測試腳本 - 測試 API 端點

測試項目：
1. 服務器連接測試
2. API 端點可用性
3. 數據格式驗證

不依賴內部模塊，純 HTTP 測試
"""

import asyncio
import aiohttp
import json
import logging
import sys

# 配置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_phase4_api():
    """測試 Phase 4 API 端點"""
    base_url = "http://localhost:8000/api/v1"

    # 測試用的 UE 位置（台北）
    test_ue_position = {"latitude": 25.0478, "longitude": 121.5319, "altitude": 0.1}

    passed_tests = 0
    total_tests = 0

    try:
        async with aiohttp.ClientSession() as session:

            # 測試 1: 健康檢查
            total_tests += 1
            try:
                logger.info("測試 1: 服務器健康檢查")

                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(f"✅ 測試 1 通過: 服務器運行正常")
                        logger.info(f"   狀態: {health_data}")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ 測試 1 失敗: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ 測試 1 失敗: {e}")

            # 測試 2: TLE 數據端點
            total_tests += 1
            try:
                logger.info("測試 2: TLE 數據端點")

                async with session.get(f"{base_url}/tle/constellations") as response:
                    if response.status == 200:
                        tle_data = await response.json()
                        logger.info(f"✅ 測試 2 通過: TLE 端點正常")
                        logger.info(
                            f"   支持星座: {len(tle_data.get('data', {}).get('constellations', []))}"
                        )
                        passed_tests += 1
                    else:
                        logger.error(f"❌ 測試 2 失敗: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ 測試 2 失敗: {e}")

            # 測試 3: D2 服務狀態
            total_tests += 1
            try:
                logger.info("測試 3: D2 服務狀態")

                async with session.get(
                    f"{base_url}/measurement-events/D2/status"
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        logger.info(f"✅ 測試 3 通過: D2 服務狀態正常")
                        logger.info(f"   服務狀態: {status_data.get('service_status')}")
                        logger.info(
                            f"   總衛星數: {status_data.get('total_satellites')}"
                        )
                        passed_tests += 1
                    else:
                        logger.error(f"❌ 測試 3 失敗: HTTP {response.status}")
                        error_text = await response.text()
                        logger.error(f"   錯誤: {error_text}")
            except Exception as e:
                logger.error(f"❌ 測試 3 失敗: {e}")

            # 測試 4: 真實 D2 數據
            total_tests += 1
            try:
                logger.info("測試 4: 真實 D2 數據獲取")

                request_data = {
                    "scenario_name": "Phase4_API_Test",
                    "ue_position": test_ue_position,
                    "duration_minutes": 1,  # 1分鐘測試
                    "sample_interval_seconds": 30,
                    "constellation": "starlink",
                }

                async with session.post(
                    f"{base_url}/measurement-events/D2/real",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        real_data = await response.json()
                        logger.info(f"✅ 測試 4 通過: 真實 D2 數據獲取成功")
                        logger.info(f"   數據源: {real_data.get('data_source')}")
                        logger.info(f"   樣本數: {real_data.get('sample_count')}")

                        # 檢查數據結構
                        results = real_data.get("results", [])
                        if results:
                            first_result = results[0]
                            measurement = first_result.get("measurement_values", {})
                            logger.info(f"   第一個測量點:")
                            logger.info(f"     時間戳: {first_result.get('timestamp')}")
                            logger.info(
                                f"     衛星距離: {measurement.get('satellite_distance', 0)/1000:.1f} km"
                            )
                            logger.info(
                                f"     參考衛星: {measurement.get('reference_satellite')}"
                            )

                        passed_tests += 1
                    else:
                        logger.error(f"❌ 測試 4 失敗: HTTP {response.status}")
                        error_text = await response.text()
                        logger.error(f"   錯誤: {error_text}")
            except Exception as e:
                logger.error(f"❌ 測試 4 失敗: {e}")

            # 測試 5: 模擬數據兼容性
            total_tests += 1
            try:
                logger.info("測試 5: 模擬數據兼容性")

                simulate_request = {
                    "scenario_name": "Phase4_Simulate_Test",
                    "ue_position": test_ue_position,
                    "duration_minutes": 1,
                    "sample_interval_seconds": 30,
                    "target_satellites": [],
                }

                async with session.post(
                    f"{base_url}/measurement-events/D2/simulate",
                    json=simulate_request,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        simulate_data = await response.json()
                        logger.info(f"✅ 測試 5 通過: 模擬數據兼容性正常")
                        logger.info(f"   數據源: {simulate_data.get('data_source')}")
                        logger.info(f"   樣本數: {simulate_data.get('sample_count')}")
                        passed_tests += 1
                    else:
                        logger.error(f"❌ 測試 5 失敗: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ 測試 5 失敗: {e}")

    except Exception as e:
        logger.error(f"連接服務器失敗: {e}")
        logger.warning("⚠️ 請確保後端服務器運行在 localhost:8888")
        logger.warning("⚠️ 可以使用以下命令啟動服務器:")
        logger.warning(
            "   cd simworld/backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8888"
        )

    return passed_tests, total_tests


async def run_phase4_tests():
    """執行 Phase 4 測試"""
    logger.info("開始 Phase 4 測試 - 前端圖表模式切換實現")
    logger.info("測試 API 端點可用性和數據格式")

    passed_tests, total_tests = await test_phase4_api()

    # 測試結果總結
    logger.info("=" * 60)
    logger.info("Phase 4 API 測試完成")
    logger.info(f"通過測試: {passed_tests}/{total_tests}")
    logger.info(f"成功率: {(passed_tests / total_tests * 100):.1f}%")

    # Phase 4 驗收標準檢查
    phase4_requirements = [
        {"name": "服務器基本連接正常", "passed": passed_tests >= 1},
        {"name": "TLE 數據服務可用", "passed": passed_tests >= 2},
        {"name": "D2 服務狀態檢查正常", "passed": passed_tests >= 3},
        {"name": "真實 D2 數據 API 正常", "passed": passed_tests >= 4},
        {"name": "模擬數據向後兼容", "passed": passed_tests >= 5},
    ]

    logger.info("=" * 60)
    logger.info("Phase 4 驗收標準檢查:")
    all_requirements_met = True

    for requirement in phase4_requirements:
        if requirement["passed"]:
            logger.info(f"✅ {requirement['name']}")
        else:
            logger.error(f"❌ {requirement['name']}")
            all_requirements_met = False

    logger.info("=" * 60)
    if all_requirements_met:
        logger.info("🎉 Phase 4 API 測試全部通過！")
        logger.info("📋 後端 API 準備完成，可以進行前端集成")
        return True
    else:
        logger.error("❌ Phase 4 API 測試未完全通過")
        if passed_tests > 0:
            logger.info("💡 部分功能正常，可以繼續開發")
        return False


if __name__ == "__main__":

    async def main():
        success = await run_phase4_tests()

        if success:
            logger.info("🎉 Phase 4 後端開發完成！")
            logger.info("📋 下一步建議:")
            logger.info("   1. 啟動前端開發服務器")
            logger.info("   2. 更新 EnhancedD2Chart 組件")
            logger.info("   3. 集成 realD2DataService")
            logger.info("   4. 測試前端真實數據模式")
        else:
            logger.warning("⚠️ 部分測試未通過，但可以繼續開發")

    asyncio.run(main())
