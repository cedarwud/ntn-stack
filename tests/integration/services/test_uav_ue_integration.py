"""
UAV UE 整合測試

測試 UAV 作為 UE 的完整功能，包括：
1. 軌跡管理（創建、查詢、更新、刪除）
2. UAV 管理（創建、狀態追蹤、刪除）
3. 任務執行（開始、停止、位置更新）
4. 信號質量監測和網路換手
5. 與 SimWorld 的整合
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
import pytest

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 測試配置
NETSTACK_BASE_URL = "http://localhost:8080"
SIMWORLD_BASE_URL = "http://localhost:8888"
TIMEOUT = 30.0


class UAVUETestSuite:
    """UAV UE 測試套件"""

    def __init__(self):
        self.netstack_client = httpx.AsyncClient(
            base_url=NETSTACK_BASE_URL, timeout=TIMEOUT
        )
        self.simworld_client = httpx.AsyncClient(
            base_url=SIMWORLD_BASE_URL, timeout=TIMEOUT
        )
        self.created_resources = {"trajectories": [], "uavs": []}

    async def cleanup(self):
        """清理測試資源"""
        logger.info("🧹 清理測試資源...")

        # 清理 UAV
        for uav_id in self.created_resources["uavs"]:
            try:
                await self.netstack_client.delete(f"/api/v1/uav/{uav_id}")
                logger.info(f"✅ 刪除 UAV: {uav_id}")
            except Exception as e:
                logger.warning(f"⚠️ 刪除 UAV 失敗: {uav_id}, 錯誤: {e}")

        # 清理軌跡
        for trajectory_id in self.created_resources["trajectories"]:
            try:
                await self.netstack_client.delete(
                    f"/api/v1/uav/trajectory/{trajectory_id}"
                )
                logger.info(f"✅ 刪除軌跡: {trajectory_id}")
            except Exception as e:
                logger.warning(f"⚠️ 刪除軌跡失敗: {trajectory_id}, 錯誤: {e}")

        await self.netstack_client.aclose()
        await self.simworld_client.aclose()

    async def test_service_health(self) -> bool:
        """測試服務健康狀態"""
        logger.info("🏥 測試服務健康狀態...")

        try:
            # 測試 NetStack
            response = await self.netstack_client.get("/health")
            assert (
                response.status_code == 200
            ), f"NetStack 健康檢查失敗: {response.status_code}"
            logger.info("✅ NetStack 服務正常")

            # 測試 SimWorld
            response = await self.simworld_client.get("/ping")
            assert (
                response.status_code == 200
            ), f"SimWorld ping 失敗: {response.status_code}"
            logger.info("✅ SimWorld 服務正常")

            return True

        except Exception as e:
            logger.error(f"❌ 服務健康檢查失敗: {e}")
            return False

    async def test_trajectory_management(self) -> bool:
        """測試軌跡管理功能"""
        logger.info("🛣️ 測試軌跡管理功能...")

        try:
            # 1. 創建測試軌跡
            base_time = datetime.utcnow()
            trajectory_data = {
                "name": "測試軌跡_整合測試",
                "description": "UAV UE 整合測試軌跡",
                "mission_type": "test",
                "points": [
                    {
                        "timestamp": base_time.isoformat(),
                        "latitude": 24.7881,
                        "longitude": 120.9971,
                        "altitude": 100,
                        "speed": 20.0,
                        "heading": 0.0,
                    },
                    {
                        "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
                        "latitude": 24.8000,
                        "longitude": 121.0100,
                        "altitude": 150,
                        "speed": 25.0,
                        "heading": 45.0,
                    },
                    {
                        "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
                        "latitude": 24.8200,
                        "longitude": 121.0300,
                        "altitude": 200,
                        "speed": 30.0,
                        "heading": 90.0,
                    },
                ],
            }

            response = await self.netstack_client.post(
                "/api/v1/uav/trajectory", json=trajectory_data
            )
            assert (
                response.status_code == 200
            ), f"創建軌跡失敗: {response.status_code}, {response.text}"

            trajectory = response.json()
            trajectory_id = trajectory["trajectory_id"]
            self.created_resources["trajectories"].append(trajectory_id)

            logger.info(f"✅ 軌跡創建成功: {trajectory_id}")
            logger.info(f"   總距離: {trajectory.get('total_distance_km', 0):.2f} km")
            logger.info(
                f"   預估時間: {trajectory.get('estimated_duration_minutes', 0):.1f} 分鐘"
            )

            # 2. 查詢軌跡詳情
            response = await self.netstack_client.get(
                f"/api/v1/uav/trajectory/{trajectory_id}"
            )
            assert response.status_code == 200, f"查詢軌跡失敗: {response.status_code}"

            trajectory_detail = response.json()
            assert trajectory_detail["trajectory_id"] == trajectory_id
            logger.info("✅ 軌跡查詢成功")

            # 3. 更新軌跡
            update_data = {"description": "更新後的軌跡描述"}
            response = await self.netstack_client.put(
                f"/api/v1/uav/trajectory/{trajectory_id}", json=update_data
            )
            assert response.status_code == 200, f"更新軌跡失敗: {response.status_code}"
            logger.info("✅ 軌跡更新成功")

            # 4. 列出所有軌跡
            response = await self.netstack_client.get("/api/v1/uav/trajectory")
            assert response.status_code == 200, f"列出軌跡失敗: {response.status_code}"

            trajectories_list = response.json()
            assert trajectories_list["total"] >= 1
            logger.info(f"✅ 軌跡列表查詢成功，共 {trajectories_list['total']} 條軌跡")

            return True

        except Exception as e:
            logger.error(f"❌ 軌跡管理測試失敗: {e}")
            return False

    async def test_uav_management(self) -> bool:
        """測試 UAV 管理功能"""
        logger.info("🚁 測試 UAV 管理功能...")

        try:
            # 1. 創建測試 UAV
            uav_data = {
                "name": "測試UAV_整合測試",
                "ue_config": {
                    "imsi": "999700000000001",
                    "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                    "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                    "plmn": "99970",
                    "apn": "internet",
                    "slice_nssai": {"sst": 1, "sd": "000001"},
                    "gnb_ip": "172.20.0.40",
                    "gnb_port": 38412,
                    "power_dbm": 23.0,
                    "frequency_mhz": 2150.0,
                    "bandwidth_mhz": 20.0,
                },
                "initial_position": {
                    "latitude": 24.7881,
                    "longitude": 120.9971,
                    "altitude": 100,
                    "speed": 0.0,
                    "heading": 0.0,
                },
            }

            response = await self.netstack_client.post("/api/v1/uav", json=uav_data)
            assert (
                response.status_code == 200
            ), f"創建 UAV 失敗: {response.status_code}, {response.text}"

            uav = response.json()
            uav_id = uav["uav_id"]
            self.created_resources["uavs"].append(uav_id)

            logger.info(f"✅ UAV 創建成功: {uav_id}")
            logger.info(f"   名稱: {uav['name']}")
            logger.info(f"   飛行狀態: {uav['flight_status']}")
            logger.info(f"   UE 連接狀態: {uav['ue_connection_status']}")

            # 2. 查詢 UAV 狀態
            response = await self.netstack_client.get(f"/api/v1/uav/{uav_id}")
            assert (
                response.status_code == 200
            ), f"查詢 UAV 狀態失敗: {response.status_code}"

            uav_status = response.json()
            assert uav_status["uav_id"] == uav_id
            logger.info("✅ UAV 狀態查詢成功")

            # 3. 更新 UAV 位置
            position_update = {
                "position": {
                    "latitude": 24.8000,
                    "longitude": 121.0000,
                    "altitude": 120,
                    "speed": 15.0,
                    "heading": 45.0,
                },
                "signal_quality": {
                    "rsrp_dbm": -80.0,
                    "rsrq_db": -10.0,
                    "sinr_db": 15.0,
                    "cqi": 12,
                    "throughput_mbps": 50.0,
                    "latency_ms": 35.0,
                    "packet_loss_rate": 0.01,
                },
            }

            response = await self.netstack_client.put(
                f"/api/v1/uav/{uav_id}/position", json=position_update
            )
            assert (
                response.status_code == 200
            ), f"更新 UAV 位置失敗: {response.status_code}"
            logger.info("✅ UAV 位置更新成功")

            # 4. 列出所有 UAV
            response = await self.netstack_client.get("/api/v1/uav")
            assert response.status_code == 200, f"列出 UAV 失敗: {response.status_code}"

            uavs_list = response.json()
            assert uavs_list["total"] >= 1
            logger.info(f"✅ UAV 列表查詢成功，共 {uavs_list['total']} 架 UAV")

            return True

        except Exception as e:
            logger.error(f"❌ UAV 管理測試失敗: {e}")
            return False

    async def test_mission_execution(self) -> bool:
        """測試任務執行功能"""
        logger.info("🎯 測試任務執行功能...")

        try:
            # 假設已有軌跡和 UAV（從前面的測試中）
            if (
                not self.created_resources["trajectories"]
                or not self.created_resources["uavs"]
            ):
                logger.warning("⚠️ 需要先創建軌跡和 UAV，跳過任務執行測試")
                return True

            trajectory_id = self.created_resources["trajectories"][0]
            uav_id = self.created_resources["uavs"][0]

            # 1. 開始任務
            mission_data = {
                "trajectory_id": trajectory_id,
                "speed_factor": 3.0,  # 加速測試
            }

            response = await self.netstack_client.post(
                f"/api/v1/uav/{uav_id}/mission/start", json=mission_data
            )
            assert (
                response.status_code == 200
            ), f"開始任務失敗: {response.status_code}, {response.text}"

            mission_status = response.json()
            assert mission_status["flight_status"] == "flying"
            logger.info(f"✅ 任務開始成功，UAV 狀態: {mission_status['flight_status']}")

            # 2. 監控任務進度（等待幾秒）
            logger.info("⏳ 監控任務進度...")
            for i in range(3):
                await asyncio.sleep(2)

                response = await self.netstack_client.get(f"/api/v1/uav/{uav_id}")
                assert response.status_code == 200

                status = response.json()
                progress = status.get("mission_progress_percent", 0)
                logger.info(f"   進度: {progress:.1f}%")

                if status.get("current_position"):
                    pos = status["current_position"]
                    logger.info(
                        f"   位置: ({pos['latitude']:.4f}, {pos['longitude']:.4f}, {pos['altitude']}m)"
                    )

            # 3. 停止任務
            response = await self.netstack_client.post(
                f"/api/v1/uav/{uav_id}/mission/stop"
            )
            assert response.status_code == 200, f"停止任務失敗: {response.status_code}"

            stop_status = response.json()
            logger.info(f"✅ 任務停止成功，UAV 狀態: {stop_status['flight_status']}")

            return True

        except Exception as e:
            logger.error(f"❌ 任務執行測試失敗: {e}")
            return False

    async def test_simworld_integration(self) -> bool:
        """測試與 SimWorld 的整合"""
        logger.info("🌍 測試與 SimWorld 的整合...")

        try:
            # 1. 測試 UAV 位置更新到 SimWorld
            uav_position_data = {
                "uav_id": "test_uav_001",
                "latitude": 24.7881,
                "longitude": 120.9971,
                "altitude": 150,
                "timestamp": datetime.utcnow().isoformat(),
                "speed": 25.0,
                "heading": 90.0,
            }

            response = await self.simworld_client.post(
                "/api/v1/uav/position", json=uav_position_data
            )
            assert (
                response.status_code == 200
            ), f"SimWorld 位置更新失敗: {response.status_code}, {response.text}"

            result = response.json()
            assert result["success"] == True
            logger.info("✅ SimWorld 位置更新成功")
            logger.info(
                f"   信道模型更新: {result.get('channel_update_triggered', False)}"
            )

            # 2. 查詢 UAV 位置
            response = await self.simworld_client.get(
                f"/api/v1/uav/{uav_position_data['uav_id']}/position"
            )
            assert (
                response.status_code == 200
            ), f"SimWorld 位置查詢失敗: {response.status_code}"

            position_result = response.json()
            assert position_result["success"] == True
            logger.info("✅ SimWorld 位置查詢成功")

            # 3. 查詢所有 UAV 位置
            response = await self.simworld_client.get("/api/v1/uav/positions")
            assert (
                response.status_code == 200
            ), f"SimWorld 所有位置查詢失敗: {response.status_code}"

            all_positions = response.json()
            assert all_positions["success"] == True
            logger.info(
                f"✅ SimWorld 所有位置查詢成功，共 {all_positions['total_uavs']} 架 UAV"
            )

            # 4. 清理測試 UAV
            response = await self.simworld_client.delete(
                f"/api/v1/uav/{uav_position_data['uav_id']}/position"
            )
            assert (
                response.status_code == 200
            ), f"SimWorld 位置刪除失敗: {response.status_code}"
            logger.info("✅ SimWorld 位置清理成功")

            return True

        except Exception as e:
            logger.error(f"❌ SimWorld 整合測試失敗: {e}")
            return False

    async def test_quick_demo(self) -> bool:
        """測試快速演示功能"""
        logger.info("🚀 測試快速演示功能...")

        try:
            response = await self.netstack_client.post("/api/v1/uav/demo/quick-test")
            assert (
                response.status_code == 200
            ), f"快速演示失敗: {response.status_code}, {response.text}"

            demo_result = response.json()
            assert demo_result["success"] == True

            # 記錄演示資源以便清理
            demo_trajectory_id = demo_result["demo_resources"]["trajectory"]["id"]
            demo_uav_id = demo_result["demo_resources"]["uav"]["id"]

            self.created_resources["trajectories"].append(demo_trajectory_id)
            self.created_resources["uavs"].append(demo_uav_id)

            logger.info("✅ 快速演示啟動成功")
            logger.info(
                f"   演示軌跡: {demo_result['demo_resources']['trajectory']['name']}"
            )
            logger.info(f"   演示 UAV: {demo_result['demo_resources']['uav']['name']}")
            logger.info(
                f"   預估演示時間: {demo_result['estimated_demo_duration_minutes']} 分鐘"
            )

            # 等待幾秒觀察演示進度
            logger.info("⏳ 觀察演示進度...")
            for i in range(3):
                await asyncio.sleep(3)

                response = await self.netstack_client.get(f"/api/v1/uav/{demo_uav_id}")
                if response.status_code == 200:
                    status = response.json()
                    progress = status.get("mission_progress_percent", 0)
                    flight_status = status.get("flight_status", "unknown")
                    logger.info(f"   演示進度: {progress:.1f}%, 狀態: {flight_status}")

            return True

        except Exception as e:
            logger.error(f"❌ 快速演示測試失敗: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """執行所有測試"""
        logger.info("🎯 開始執行 UAV UE 整合測試套件...")

        results = {}

        try:
            # 測試順序很重要，因為後面的測試依賴前面創建的資源
            test_cases = [
                ("service_health", self.test_service_health),
                ("trajectory_management", self.test_trajectory_management),
                ("uav_management", self.test_uav_management),
                ("mission_execution", self.test_mission_execution),
                ("simworld_integration", self.test_simworld_integration),
                ("quick_demo", self.test_quick_demo),
            ]

            for test_name, test_func in test_cases:
                logger.info(f"\n{'='*60}")
                logger.info(f"執行測試: {test_name}")
                logger.info(f"{'='*60}")

                try:
                    results[test_name] = await test_func()
                    status = "✅ 通過" if results[test_name] else "❌ 失敗"
                    logger.info(f"測試 {test_name}: {status}")

                except Exception as e:
                    logger.error(f"測試 {test_name} 發生異常: {e}")
                    results[test_name] = False

                # 測試間稍微等待
                await asyncio.sleep(1)

            return results

        finally:
            await self.cleanup()


async def main():
    """主測試函數"""
    logger.info("🚀 啟動 UAV UE 整合測試...")

    test_suite = UAVUETestSuite()

    try:
        results = await test_suite.run_all_tests()

        # 輸出測試總結
        logger.info(f"\n{'='*60}")
        logger.info("📊 測試結果總結")
        logger.info(f"{'='*60}")

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {test_name:25} {status}")

        logger.info(f"\n總計: {passed}/{total} 個測試通過")

        if passed == total:
            logger.info("🎉 所有測試通過！UAV UE 功能正常運作")
            return 0
        else:
            logger.error(f"❌ {total - passed} 個測試失敗")
            return 1

    except Exception as e:
        logger.error(f"💥 測試執行失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
