"""
Sionna 整合系統測試

測試範圍：
1. SimWorld Sionna 通道模擬 API
2. NetStack Sionna 整合服務
3. UERANSIM 配置動態更新
4. 通道模型應用
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List


class TestSionnaIntegration:
    """Sionna 整合系統測試類"""

    SIMWORLD_BASE_URL = "http://localhost:8888"
    NETSTACK_BASE_URL = "http://localhost:8080"

    async def setup_session(self):
        """設置 HTTP 會話"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """清理 HTTP 會話"""
        if hasattr(self, "session"):
            await self.session.close()

    async def test_simworld_sionna_quick_test(self):
        """測試 SimWorld Sionna 快速測試"""
        async with self.session.post(
            f"{self.SIMWORLD_BASE_URL}/api/v1/sionna/quick-test"
        ) as response:
            assert response.status == 200
            data = await response.json()

            # 驗證基本回應結構
            assert data["success"] is True
            assert "channel_simulation" in data

            # 驗證通道模擬結果
            sim_result = data["channel_simulation"]
            assert sim_result["success"] is True
            assert "channel_coefficients" in sim_result
            assert "path_gains" in sim_result
            assert "processing_time_ms" in sim_result

            # 驗證路徑增益
            path_gains = sim_result["path_gains"]
            assert len(path_gains) > 0
            for gain in path_gains:
                assert "ue_id" in gain
                assert "gnb_id" in gain
                assert "path_gain_db" in gain

    async def test_simworld_sionna_channel_simulation(self):
        """測試 SimWorld Sionna 通道模擬功能"""
        # 構建測試請求
        simulation_request = {
            "request_id": "test_sionna_001",
            "ue_positions": [
                {"position": [100, 0, 1.5], "ue_id": "test_ue_1"},
                {"position": [200, 100, 1.5], "ue_id": "test_ue_2"},
            ],
            "gnb_positions": [{"position": [0, 0, 30], "gnb_id": "test_gnb_1"}],
            "environment_type": "urban",
            "frequency_ghz": 2.1,
            "bandwidth_mhz": 20,
            "num_time_samples": 100,
            "enable_gpu": True,
        }

        async with self.session.post(
            f"{self.SIMWORLD_BASE_URL}/api/v1/sionna/simulate", json=simulation_request
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert data["success"] is True
            assert "simulation_id" in data
            assert "channel_simulation" in data

            sim_result = data["channel_simulation"]
            assert sim_result["success"] is True
            assert "channel_coefficients" in sim_result
            assert "path_gains" in sim_result

            # 驗證通道係數
            coefficients = sim_result["channel_coefficients"]
            assert len(coefficients) > 0

            # 驗證路徑增益匹配請求的 UE 數量
            path_gains = sim_result["path_gains"]
            assert len(path_gains) == 2  # 對應兩個 UE

    async def test_simworld_sionna_environment_types(self):
        """測試 SimWorld 支援的環境類型"""
        environments = ["urban", "rural", "indoor", "highway"]

        for env_type in environments:
            simulation_request = {
                "request_id": f"env_test_{env_type}",
                "ue_positions": [{"position": [50, 0, 1.5], "ue_id": "env_ue"}],
                "gnb_positions": [{"position": [0, 0, 30], "gnb_id": "env_gnb"}],
                "environment_type": env_type,
                "frequency_ghz": 2.1,
                "bandwidth_mhz": 20,
            }

            async with self.session.post(
                f"{self.SIMWORLD_BASE_URL}/api/v1/sionna/simulate",
                json=simulation_request,
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data["success"] is True

    async def test_netstack_sionna_service_status(self):
        """測試 NetStack Sionna 整合服務狀態"""
        async with self.session.get(
            f"{self.NETSTACK_BASE_URL}/api/v1/sionna/status"
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert "service_status" in data
            status = data["service_status"]
            assert status["service_name"] == "SionnaIntegrationService"
            assert "simworld_api_url" in status
            assert "update_interval_sec" in status

    async def test_netstack_sionna_active_models(self):
        """測試 NetStack 活躍通道模型查詢"""
        async with self.session.get(
            f"{self.NETSTACK_BASE_URL}/api/v1/sionna/active-models"
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert "active_models" in data
            assert "count" in data
            assert isinstance(data["active_models"], list)
            assert data["count"] >= 0

    async def test_netstack_sionna_channel_simulation(self):
        """測試 NetStack Sionna 通道模擬請求"""
        ue_positions = [{"position": [100, 0, 1.5]}, {"position": [200, 100, 1.5]}]
        gnb_positions = [{"position": [0, 0, 30]}]

        async with self.session.post(
            f"{self.NETSTACK_BASE_URL}/api/v1/sionna/channel-simulation",
            json={
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "environment_type": "urban",
                "frequency_ghz": 2.1,
                "bandwidth_mhz": 20,
            },
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert data["success"] is True
            assert "channel_simulation_result" in data

    async def test_netstack_sionna_quick_test(self):
        """測試 NetStack Sionna 快速測試"""
        async with self.session.post(
            f"{self.NETSTACK_BASE_URL}/api/v1/sionna/quick-test"
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert data["test_completed"] is True
            assert "test_config" in data
            assert "result" in data

            test_config = data["test_config"]
            assert test_config["ue_count"] >= 2
            assert test_config["gnb_count"] >= 1
            assert test_config["environment"] == "urban"

    async def test_sionna_performance_requirements(self):
        """測試 Sionna 模擬性能要求"""
        start_time = time.time()

        # 標準測試案例
        simulation_request = {
            "request_id": "perf_test_sionna",
            "ue_positions": [
                {"position": [i * 50, 0, 1.5], "ue_id": f"perf_ue_{i}"}
                for i in range(5)  # 5 個 UE
            ],
            "gnb_positions": [
                {"position": [0, 0, 30], "gnb_id": "perf_gnb_1"},
                {"position": [500, 0, 30], "gnb_id": "perf_gnb_2"},
            ],
            "environment_type": "urban",
            "frequency_ghz": 2.1,
            "bandwidth_mhz": 20,
            "num_time_samples": 50,
            "enable_gpu": True,
        }

        async with self.session.post(
            f"{self.SIMWORLD_BASE_URL}/api/v1/sionna/simulate", json=simulation_request
        ) as response:
            end_time = time.time()
            total_time_ms = (end_time - start_time) * 1000

            assert response.status == 200
            data = await response.json()

            # 驗證處理時間 (GPU 加速應該比較快)
            assert total_time_ms < 5000  # HTTP 往返時間應小於 5 秒

            if data["success"]:
                sim_result = data["channel_simulation"]
                if "processing_time_ms" in sim_result:
                    # Sionna 模擬時間應該合理
                    processing_time = sim_result["processing_time_ms"]
                    assert processing_time < 3000  # 實際模擬時間 < 3 秒

    async def test_sionna_channel_coefficient_validity(self):
        """測試 Sionna 通道係數有效性"""
        simulation_request = {
            "request_id": "coeff_test",
            "ue_positions": [{"position": [100, 0, 1.5], "ue_id": "coeff_ue"}],
            "gnb_positions": [{"position": [0, 0, 30], "gnb_id": "coeff_gnb"}],
            "environment_type": "urban",
            "frequency_ghz": 2.1,
            "bandwidth_mhz": 20,
        }

        async with self.session.post(
            f"{self.SIMWORLD_BASE_URL}/api/v1/sionna/simulate", json=simulation_request
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert data["success"] is True
            sim_result = data["channel_simulation"]

            # 驗證通道係數結構
            coefficients = sim_result["channel_coefficients"]
            assert len(coefficients) > 0

            for coeff in coefficients:
                assert "ue_id" in coeff
                assert "gnb_id" in coeff
                assert "coefficients" in coeff

                # 驗證係數是複數格式
                coeffs = coeff["coefficients"]
                assert isinstance(coeffs, list)
                if coeffs:
                    # 每個係數應該有實部和虛部
                    for c in coeffs[:3]:  # 檢查前3個係數
                        assert isinstance(c, (list, dict))

    async def test_sionna_integration_with_ueransim(self):
        """測試 Sionna 與 UERANSIM 的整合"""
        # 模擬通道並應用到 UERANSIM 配置
        ue_positions = [{"position": [100, 0, 1.5]}, {"position": [300, 200, 1.5]}]
        gnb_positions = [{"position": [0, 0, 30]}, {"position": [500, 0, 30]}]

        async with self.session.post(
            f"{self.NETSTACK_BASE_URL}/api/v1/sionna/channel-simulation",
            json={
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "environment_type": "urban",
                "frequency_ghz": 2.1,
                "bandwidth_mhz": 20,
            },
        ) as response:
            assert response.status == 200
            data = await response.json()

            assert data["success"] is True

            # 檢查是否有配置更新指示
            result = data["channel_simulation_result"]
            if "ueransim_config_updates" in result:
                updates = result["ueransim_config_updates"]
                assert isinstance(updates, list)

    def test_sionna_system_integration(self):
        """同步測試包裝器 - 整合所有 Sionna 測試"""

        async def run_all_tests():
            await self.setup_session()

            try:
                # SimWorld Sionna 功能測試
                await self.test_simworld_sionna_quick_test()
                await self.test_simworld_sionna_channel_simulation()
                await self.test_simworld_sionna_environment_types()

                # NetStack Sionna 功能測試
                await self.test_netstack_sionna_service_status()
                await self.test_netstack_sionna_active_models()
                await self.test_netstack_sionna_channel_simulation()
                await self.test_netstack_sionna_quick_test()

                # 性能和有效性測試
                await self.test_sionna_performance_requirements()
                await self.test_sionna_channel_coefficient_validity()

                # 整合測試
                await self.test_sionna_integration_with_ueransim()

            finally:
                await self.cleanup_session()

        # 運行異步測試
        asyncio.run(run_all_tests())


if __name__ == "__main__":
    # 直接運行測試
    test_instance = TestSionnaIntegration()
    test_instance.test_sionna_system_integration()
    print("✅ Sionna 整合系統測試完成")
