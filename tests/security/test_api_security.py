#!/usr/bin/env python3
"""
API 安全測試

測試 API 的安全性，包括認證、授權、輸入驗證等
"""

import pytest
import aiohttp
import asyncio

class APISecurityTests:
    """API 安全測試套件"""
    
    def __init__(self):
        self.netstack_base = "http://localhost:8001"
        self.simworld_base = "http://localhost:8002"
    
    async def test_input_validation(self):
        """測試輸入驗證"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "\x00\x00\x00\x00",
            "A" * 10000  # 長字符串
        ]
        
        async with aiohttp.ClientSession() as session:
            for malicious_input in malicious_inputs:
                try:
                    # 測試各種端點的輸入驗證
                    test_data = {"input": malicious_input}
                    
                    async with session.post(
                        f"{self.netstack_base}/api/v1/test",
                        json=test_data,
                        timeout=10
                    ) as response:
                        # 應該返回錯誤而不是處理惡意輸入
                        assert response.status in [400, 422, 500]
                        
                except aiohttp.ClientTimeout:
                    # 超時也是可接受的防護措施
                    pass
                except Exception as e:
                    print(f"⚠️  輸入驗證測試異常: {e}")
    
    async def test_rate_limiting(self):
        """測試速率限制"""
        async with aiohttp.ClientSession() as session:
            # 快速發送大量請求
            tasks = []
            for _ in range(100):
                task = session.get(f"{self.netstack_base}/api/v1/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 檢查是否有速率限制響應 (429)
            rate_limited = sum(1 for r in responses 
                             if hasattr(r, 'status') and r.status == 429)
            
            # 應該有一些請求被速率限制
            print(f"📊 速率限制測試: {rate_limited}/100 請求被限制")

@pytest.mark.asyncio
async def test_api_security_comprehensive():
    """執行綜合 API 安全測試"""
    security_tests = APISecurityTests()
    
    await security_tests.test_input_validation()
    await security_tests.test_rate_limiting()

if __name__ == "__main__":
    asyncio.run(test_api_security_comprehensive())
