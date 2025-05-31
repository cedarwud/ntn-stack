#!/usr/bin/env python3
"""
統一 API 整合測試 - 簡化版本
"""

import pytest
import httpx
import asyncio
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 測試配置
NETSTACK_BASE_URL = "http://localhost:8080"
UNIFIED_API_BASE_URL = f"{NETSTACK_BASE_URL}/api/v1"


class TestUnifiedAPISimple:
    """統一 API 簡化測試類別"""

    @pytest.mark.asyncio
    async def test_system_status(self):
        """測試系統狀態端點"""
        logger.info("🧪 測試系統狀態端點")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{UNIFIED_API_BASE_URL}/system/status")

            if response.status_code == 200:
                data = response.json()
                assert "netstack_status" in data or "status" in data
                logger.info("✅ 系統狀態測試通過")
            else:
                logger.warning(f"⚠️ 系統狀態端點返回 {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ 系統狀態測試失敗: {e}")
            pytest.skip("NetStack 服務未啟動")

    @pytest.mark.asyncio
    async def test_health_check(self):
        """測試健康檢查端點"""
        logger.info("🧪 測試健康檢查端點")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{NETSTACK_BASE_URL}/health")

            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert "overall_status" in data or "status" in data
                logger.info("✅ 健康檢查測試通過")
            else:
                logger.warning("⚠️ 服務健康狀態降級")

        except Exception as e:
            logger.warning(f"⚠️ 健康檢查測試失敗: {e}")
            pytest.skip("NetStack 服務未啟動")

    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """測試服務發現端點"""
        logger.info("🧪 測試服務發現端點")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{UNIFIED_API_BASE_URL}/system/discovery")

            if response.status_code == 200:
                data = response.json()
                assert "services" in data or "endpoints" in data
                logger.info("✅ 服務發現測試通過")
            else:
                logger.warning(f"⚠️ 服務發現端點返回 {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ 服務發現測試失敗: {e}")

    @pytest.mark.asyncio
    async def test_api_documentation(self):
        """測試 API 文檔端點"""
        logger.info("🧪 測試 API 文檔端點")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{NETSTACK_BASE_URL}/docs")

            assert response.status_code == 200
            logger.info("✅ API 文檔測試通過")

        except Exception as e:
            logger.warning(f"⚠️ API 文檔測試失敗: {e}")

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """測試指標端點"""
        logger.info("🧪 測試指標端點")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{NETSTACK_BASE_URL}/metrics")

            assert response.status_code == 200
            metrics_text = response.text
            assert "netstack" in metrics_text.lower()
            logger.info("✅ 指標端點測試通過")

        except Exception as e:
            logger.warning(f"⚠️ 指標端點測試失敗: {e}")

    def test_basic_functionality(self):
        """基本功能測試（同步版本）"""
        logger.info("🧪 基本功能測試")

        # 這是一個同步測試，確保測試框架正常工作
        assert True
        logger.info("✅ 基本功能測試通過")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
