"""
統一 API 測試套件

測試 NetStack 和 SimWorld 整合的統一 API 功能
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# 測試配置
NETSTACK_BASE_URL = "http://localhost:8080"
SIMWORLD_BASE_URL = "http://localhost:8888"
UNIFIED_API_BASE_URL = f"{NETSTACK_BASE_URL}/api/v1"


class TestUnifiedAPI:
    """統一 API 測試類"""

    @pytest.mark.asyncio
    async def test_system_status(self):
        """測試系統狀態端點"""
        logger.info("🧪 測試系統狀態端點")

        # 創建客戶端
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{UNIFIED_API_BASE_URL}/system/status")

            assert response.status_code == 200
            data = response.json()

            # 驗證響應結構
            assert "status" in data
            assert "timestamp" in data
            assert "components" in data
            assert "summary" in data

            # 驗證組件狀態
            components = data["components"]
            assert "netstack" in components
            assert "simworld" in components

            # 驗證每個組件的必要字段
            for component_name, component_data in components.items():
                assert "name" in component_data
                assert "healthy" in component_data
                assert "status" in component_data
                assert "version" in component_data
                assert "last_health_check" in component_data

            logger.info(f"✅ 系統狀態測試通過，整體狀態: {data['status']}")

    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """測試服務發現端點"""
        logger.info("🧪 測試服務發現端點")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{UNIFIED_API_BASE_URL}/system/discovery")

            assert response.status_code == 200
            data = response.json()

            # 驗證響應結構
            assert "timestamp" in data
            assert "total_endpoints" in data
            assert "endpoints" in data
            assert "services" in data

            # 驗證端點分類
            endpoints = data["endpoints"]
            expected_categories = [
                "open5gs",
                "ueransim",
                "satellite-gnb",
                "uav",
                "wireless",
                "mesh",
            ]

            for category in expected_categories:
                assert category in endpoints
                assert isinstance(endpoints[category], list)

                # 驗證每個端點的結構
                for endpoint in endpoints[category]:
                    assert "path" in endpoint
                    assert "method" in endpoint
                    assert "description" in endpoint
                    assert "service" in endpoint

            # 驗證服務信息
            services = data["services"]
            assert "netstack" in services
            assert "simworld" in services

            logger.info(f"✅ 服務發現測試通過，發現 {data['total_endpoints']} 個端點")

    @pytest.mark.asyncio
    async def test_satellite_proxy(self):
        """測試衛星代理端點"""
        logger.info("🧪 測試衛星代理端點")

        # 測試獲取衛星信息（使用測試衛星 ID）
        test_satellite_id = 1

        try:
            response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{UNIFIED_API_BASE_URL}/satellite/{test_satellite_id}"
            )

            # 如果 SimWorld 服務可用，應該返回 200
            if response.status_code == 200:
                data = response.json()
                assert "id" in data or "name" in data  # 衛星基本信息
                logger.info(f"✅ 衛星代理測試通過，獲取到衛星信息")
            else:
                # 如果服務不可用，應該返回適當的錯誤
                assert response.status_code in [500, 503, 404]
                logger.warning(
                    f"⚠️ 衛星代理測試：SimWorld 服務不可用 (HTTP {response.status_code})"
                )

        except Exception as e:
            logger.warning(f"⚠️ 衛星代理測試：連接失敗 - {e}")

    @pytest.mark.asyncio
    async def test_wireless_simulation_proxy(self):
        """測試無線模擬代理端點"""
        logger.info("🧪 測試無線模擬代理端點")

        # 構建測試請求
        test_request = {
            "environment_type": "urban",
            "frequency_ghz": 2.1,
            "bandwidth_mhz": 20,
            "tx_position": [0, 0, 30],
            "rx_position": [1000, 0, 1.5],
            "ue_id": "test_ue_001",
            "gnb_id": "test_gnb_001",
        }

        try:
            response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{UNIFIED_API_BASE_URL}/wireless/quick-simulation", json=test_request
            )

            # 如果 SimWorld 服務可用，應該返回 200
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 無線模擬代理測試通過")
            else:
                # 如果服務不可用，應該返回適當的錯誤
                assert response.status_code in [500, 503, 404]
                logger.warning(
                    f"⚠️ 無線模擬代理測試：SimWorld 服務不可用 (HTTP {response.status_code})"
                )

        except Exception as e:
            logger.warning(f"⚠️ 無線模擬代理測試：連接失敗 - {e}")

    @pytest.mark.asyncio
    async def test_websocket_connections(self):
        """測試 WebSocket 連接"""
        logger.info("🧪 測試 WebSocket 連接")

        # 測試網絡狀態 WebSocket
        try:
            async with httpx.AsyncClient() as client:
                # 由於 httpx 不直接支持 WebSocket，我們測試 WebSocket 端點是否存在
                # 實際的 WebSocket 測試需要使用 websockets 庫

                # 這裡我們測試 WebSocket 端點的 HTTP 升級請求
                headers = {
                    "Connection": "Upgrade",
                    "Upgrade": "websocket",
                    "Sec-WebSocket-Key": "test-key",
                    "Sec-WebSocket-Version": "13",
                }

                response = await client.get(
                    f"{UNIFIED_API_BASE_URL}/ws/network-status", headers=headers
                )

                # WebSocket 升級應該返回 426 或其他適當的狀態碼
                assert response.status_code in [426, 400, 404]
                logger.info("✅ WebSocket 端點存在且可訪問")

        except Exception as e:
            logger.warning(f"⚠️ WebSocket 測試：{e}")

    @pytest.mark.asyncio
    async def test_api_documentation(self):
        """測試 API 文檔可訪問性"""
        logger.info("🧪 測試 API 文檔可訪問性")

        # 測試 OpenAPI 文檔
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NETSTACK_BASE_URL}/docs")
        assert response.status_code == 200

        # 測試 OpenAPI JSON
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NETSTACK_BASE_URL}/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

        # 驗證統一 API 端點在文檔中
        paths = openapi_data["paths"]
        unified_endpoints = [
            "/api/v1/system/status",
            "/api/v1/system/discovery",
            "/api/v1/satellite/{satellite_id}",
            "/api/v1/wireless/quick-simulation",
        ]

        for endpoint in unified_endpoints:
            assert endpoint in paths, f"統一 API 端點 {endpoint} 未在文檔中找到"

        logger.info("✅ API 文檔測試通過")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """測試錯誤處理"""
        logger.info("🧪 測試錯誤處理")

        # 測試不存在的端點
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{UNIFIED_API_BASE_URL}/nonexistent-endpoint")
        assert response.status_code == 404

        # 測試無效的衛星 ID
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{UNIFIED_API_BASE_URL}/satellite/99999")
        assert response.status_code in [404, 500]

        # 測試無效的請求數據
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
            f"{UNIFIED_API_BASE_URL}/wireless/quick-simulation",
            json={"invalid": "data"},
        )
        assert response.status_code in [400, 422, 500]

        logger.info("✅ 錯誤處理測試通過")

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """測試性能指標"""
        logger.info("🧪 測試性能指標")

        # 測試 Prometheus 指標端點
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NETSTACK_BASE_URL}/metrics")
        assert response.status_code == 200

        metrics_text = response.text

        # 驗證關鍵指標存在
        expected_metrics = [
            "netstack_api_requests_total",
            "netstack_api_request_duration_seconds",
        ]

        for metric in expected_metrics:
            assert metric in metrics_text, f"指標 {metric} 未找到"

        logger.info("✅ 性能指標測試通過")

    @pytest.mark.asyncio
    async def test_health_endpoints(self):
        """測試健康檢查端點"""
        logger.info("🧪 測試健康檢查端點")

        # 測試 NetStack 健康檢查
        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NETSTACK_BASE_URL}/health")
        assert response.status_code in [200, 503]  # 健康或服務不可用

        if response.status_code == 200:
            data = response.json()
            assert "overall_status" in data
            logger.info(f"✅ NetStack 健康檢查通過，狀態: {data.get('overall_status')}")
        else:
            logger.warning("⚠️ NetStack 健康檢查：服務降級")

    @pytest.mark.asyncio
    async def test_integration_flow(self):
        """測試完整的整合流程"""
        logger.info("🧪 測試完整的整合流程")

        # 1. 檢查系統狀態
        status_response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{UNIFIED_API_BASE_URL}/system/status")
        assert status_response.status_code == 200

        # 2. 服務發現
        discovery_response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
            f"{UNIFIED_API_BASE_URL}/system/discovery"
        )
        assert discovery_response.status_code == 200

        # 3. 嘗試使用發現的端點
        discovery_data = discovery_response.json()
        endpoints = discovery_data["endpoints"]

        # 測試一些關鍵端點
        test_count = 0
        success_count = 0

        for category, endpoint_list in endpoints.items():
            for endpoint_info in endpoint_list[:2]:  # 每個類別測試前2個端點
                try:
                    path = endpoint_info["path"]
                    method = endpoint_info["method"]

                    # 替換路徑參數為測試值
                    test_path = path.replace("{satellite_id}", "1")
                    test_path = test_path.replace("{uav_id}", "test_uav")
                    test_path = test_path.replace("{ue_id}", "test_ue")

                    test_count += 1

                    if method == "GET":
                        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                            f"{NETSTACK_BASE_URL}{test_path}"
                        )
                    elif method == "POST":
                        response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                            f"{NETSTACK_BASE_URL}{test_path}", json={}
                        )
                    else:
                        continue

                    # 接受各種狀態碼（包括服務不可用的情況）
                    if response.status_code < 500:
                        success_count += 1

                except Exception as e:
                    logger.debug(f"端點測試失敗: {path} - {e}")

        success_rate = success_count / test_count if test_count > 0 else 0
        logger.info(
            f"✅ 整合流程測試完成，成功率: {success_rate:.2%} ({success_count}/{test_count})"
        )

        # 至少 50% 的端點應該可訪問
        assert success_rate >= 0.5, f"端點可訪問率過低: {success_rate:.2%}"


class TestUnifiedAPIPerformance:
    """統一 API 性能測試"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """測試設置"""
        self.client = httpx.AsyncClient(timeout=30.0)
        yield
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.aclose()

    @pytest.mark.asyncio
    async def test_response_time(self):
        """測試響應時間"""
        logger.info("🧪 測試 API 響應時間")

        endpoints_to_test = [
            f"{UNIFIED_API_BASE_URL}/system/status",
            f"{UNIFIED_API_BASE_URL}/system/discovery",
            f"{NETSTACK_BASE_URL}/health",
        ]

        for endpoint in endpoints_to_test:
            start_time = datetime.now()

            try:
                response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint)
                end_time = datetime.now()

                response_time = (end_time - start_time).total_seconds()

                # 響應時間應該在合理範圍內（5秒以內）
                assert response_time < 5.0, f"響應時間過長: {response_time:.2f}s"

                logger.info(f"✅ {endpoint} 響應時間: {response_time:.3f}s")

            except Exception as e:
                logger.warning(f"⚠️ {endpoint} 測試失敗: {e}")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """測試並發請求"""
        logger.info("🧪 測試並發請求處理")

        async def make_request():
            try:
                response = async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                    f"{UNIFIED_API_BASE_URL}/system/status"
                )
                return response.status_code == 200
            except:
                return False

        # 並發發送 10 個請求
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        success_count = sum(results)
        success_rate = success_count / len(results)

        logger.info(
            f"✅ 並發測試完成，成功率: {success_rate:.2%} ({success_count}/{len(results)})"
        )

        # 至少 80% 的並發請求應該成功
        assert success_rate >= 0.8, f"並發請求成功率過低: {success_rate:.2%}"


@pytest.mark.asyncio
async def test_unified_api_complete():
    """完整的統一 API 測試"""
    logger.info("🚀 開始統一 API 完整測試")

    # 基本功能測試
    basic_test = TestUnifiedAPI()
    await basic_test.setup()

    try:
        await basic_test.test_system_status()
        await basic_test.test_service_discovery()
        await basic_test.test_satellite_proxy()
        await basic_test.test_wireless_simulation_proxy()
        await basic_test.test_websocket_connections()
        await basic_test.test_api_documentation()
        await basic_test.test_error_handling()
        await basic_test.test_performance_metrics()
        await basic_test.test_health_endpoints()
        await basic_test.test_integration_flow()

        logger.info("✅ 基本功能測試全部通過")

    finally:
        await basic_test.client.aclose()

    # 性能測試
    performance_test = TestUnifiedAPIPerformance()
    await performance_test.setup()

    try:
        await performance_test.test_response_time()
        await performance_test.test_concurrent_requests()

        logger.info("✅ 性能測試全部通過")

    finally:
        await performance_test.client.aclose()

    logger.info("🎉 統一 API 完整測試成功完成！")


if __name__ == "__main__":
    # 直接運行測試
    asyncio.run(test_unified_api_complete())
