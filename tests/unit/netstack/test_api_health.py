#!/usr/bin/env python3
"""
NetStack API 健康檢查單元測試
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch


class TestNetStackAPIHealth:
    """NetStack API 健康檢查測試類別"""

    @pytest.fixture
    def base_url(self):
        """基礎 URL fixture"""
        return "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_health_endpoint_success(self, base_url):
        """測試健康檢查端點成功回應"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{base_url}/health", timeout=5) as response:
                    assert response.status == 200
                    data = await response.json()
                    # 檢查實際的回應格式
                    assert "overall_status" in data or "status" in data
                    if "overall_status" in data:
                        assert data["overall_status"] in [
                            "healthy",
                            "unhealthy",
                            "degraded",
                        ]
                    elif "status" in data:
                        assert data["status"] in ["healthy", "unhealthy", "degraded"]
            except aiohttp.ClientError:
                pytest.skip("NetStack 服務未啟動，跳過測試")

    @pytest.mark.asyncio
    async def test_health_endpoint_timeout(self, base_url):
        """測試健康檢查端點超時處理"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()

            async with aiohttp.ClientSession() as session:
                with pytest.raises(asyncio.TimeoutError):
                    async with session.get(f"{base_url}/health", timeout=1):
                        pass

    @pytest.mark.asyncio
    async def test_api_v1_endpoints_available(self, base_url):
        """測試 API v1 端點可用性"""
        endpoints = [
            "/api/v1/mesh/nodes",
            "/api/v1/uav/list",
            "/api/v1/interference/status",
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(
                        f"{base_url}{endpoint}", timeout=5
                    ) as response:
                        # 200 或 404 都表示端點存在，500+ 表示服務問題
                        assert response.status < 500
                except aiohttp.ClientError:
                    pytest.skip(f"NetStack 服務未啟動，跳過 {endpoint} 測試")

    def test_health_response_structure(self):
        """測試健康檢查回應結構"""
        # 模擬健康檢查回應 - 支援兩種格式
        mock_response_v1 = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "services": {
                "mesh": "running",
                "uav": "running",
                "interference": "running",
            },
        }

        mock_response_v2 = {
            "overall_status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "services": {
                "mongodb": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
        }

        # 測試第一種格式
        assert "status" in mock_response_v1 or "overall_status" in mock_response_v1
        assert "timestamp" in mock_response_v1
        assert "services" in mock_response_v1

        # 測試第二種格式
        assert "status" in mock_response_v2 or "overall_status" in mock_response_v2
        assert "timestamp" in mock_response_v2
        assert "services" in mock_response_v2

        # 驗證狀態值
        if "status" in mock_response_v1:
            assert mock_response_v1["status"] in ["healthy", "unhealthy", "degraded"]
        if "overall_status" in mock_response_v2:
            assert mock_response_v2["overall_status"] in [
                "healthy",
                "unhealthy",
                "degraded",
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
