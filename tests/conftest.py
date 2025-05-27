#!/usr/bin/env python3
"""
NTN Stack 測試配置和共用固件
"""

import pytest
import asyncio
import aiohttp
import os
import time
from typing import AsyncGenerator

# 測試環境配置
NETSTACK_URL = os.getenv("NETSTACK_URL", "http://localhost:8081")
SIMWORLD_URL = os.getenv("SIMWORLD_URL", "http://localhost:8001")
TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "60"))

@pytest.fixture(scope="session")
def event_loop():
    """創建事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """創建共用的 HTTP 會話"""
    timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session

@pytest.fixture(scope="session") 
async def wait_for_services(http_session: aiohttp.ClientSession):
    """等待所有服務啟動"""
    max_retries = 30
    retry_delay = 2
    
    services = {
        "netstack": f"{NETSTACK_URL}/health",
        "simworld": f"{SIMWORLD_URL}/ping"
    }
    
    for service_name, health_url in services.items():
        for attempt in range(max_retries):
            try:
                async with http_session.get(health_url) as response:
                    if response.status == 200:
                        print(f"✅ {service_name} 服務已啟動")
                        break
            except Exception as e:
                if attempt == max_retries - 1:
                    pytest.skip(f"❌ {service_name} 服務無法啟動: {e}")
                
                print(f"⏳ 等待 {service_name} 服務啟動 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)

@pytest.fixture
def test_satellite_id():
    """測試用衛星 ID"""
    return 25544  # ISS

@pytest.fixture
def test_uav_position():
    """測試用 UAV 位置"""
    return {
        "latitude": 24.787,
        "longitude": 121.005,
        "altitude": 100.0
    }

@pytest.fixture
def test_network_params():
    """測試用網路參數"""
    return {
        "frequency": 2100,
        "bandwidth": 20,
        "tx_power": 43.0
    }

@pytest.fixture
def test_oneweb_satellites():
    """測試用 OneWeb 衛星 ID"""
    return [1, 2, 3, 4, 5]

@pytest.fixture(scope="class")
def test_results():
    """測試結果收集器"""
    return {}

def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "slow: 標記為慢速測試（超過10秒）"
    )
    config.addinivalue_line(
        "markers", "integration: 標記為整合測試"
    )
    config.addinivalue_line(
        "markers", "requires_services: 需要外部服務運行的測試"
    )

def pytest_collection_modifyitems(config, items):
    """修改測試項目"""
    for item in items:
        # 為所有異步測試添加 asyncio 標記
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # 為整合測試添加 requires_services 標記
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.requires_services)

@pytest.fixture(autouse=True)
def test_timing():
    """測試執行時間追蹤"""
    start_time = time.time()
    yield
    duration = time.time() - start_time
    if duration > 10:
        print(f"\n⚠️  測試執行時間較長: {duration:.2f}s")

# 測試數據
@pytest.fixture
def sample_ueransim_config():
    """示例 UERANSIM 配置"""
    return {
        "scenario": "satellite_direct_link",
        "satellite": {
            "id": "SAT-001",
            "name": "OneWeb-001",
            "altitude": 1200.0,
            "inclination": 87.4
        },
        "uav": {
            "id": "UAV-001",
            "latitude": 24.787,
            "longitude": 121.005,
            "altitude": 100.0
        },
        "network_params": {
            "frequency": 2100,
            "bandwidth": 20,
            "tx_power": 43.0
        },
        "slices": ["embb", "urllc"]
    } 