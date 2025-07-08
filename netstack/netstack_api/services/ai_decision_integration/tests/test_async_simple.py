"""
簡單異步測試驗證
"""
import asyncio
import pytest


class TestAsyncFunction:
    """測試異步功能"""

    def test_sync_function(self):
        """同步測試 - 應該正常執行"""
        assert True

    @pytest.mark.asyncio
    async def test_async_function(self):
        """異步測試 - 測試 pytest-asyncio 是否工作"""
        await asyncio.sleep(0.001)
        assert True

    @pytest.mark.asyncio  
    async def test_async_with_timeout(self):
        """帶超時的異步測試"""
        start_time = asyncio.get_event_loop().time()
        await asyncio.sleep(0.01)
        end_time = asyncio.get_event_loop().time()
        assert (end_time - start_time) >= 0.01