#!/usr/bin/env python3
"""
NetStack API 測試套件
整合原本 netstack/test_satellite_api.py 的功能
"""

import pytest
import asyncio
import aiohttp
import os
from typing import Dict, List, Optional
import json

class TestNetStackAPI:
    """NetStack API 測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試設置"""
        self.netstack_url = os.getenv("NETSTACK_URL", "http://localhost:8081")
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """測試健康檢查"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.netstack_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_satellite_gnb_mapping(self):
        """測試衛星 gNodeB 映射"""
        test_data = {
            "satellite_id": 25544,  # ISS
            "uav_latitude": 24.787,
            "uav_longitude": 121.005,
            "uav_altitude": 100.0,
            "frequency": 2100,
            "bandwidth": 20
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.netstack_url}/api/v1/satellite-gnb/mapping",
                params=test_data
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                if data["success"]:
                    assert "gnb_config" in data
                    assert "network_parameters" in data
    
    @pytest.mark.asyncio
    async def test_batch_satellite_mapping(self):
        """測試批量衛星映射"""
        test_params = {
            "satellite_ids": "25544,20580,43013",  # ISS, HUBBLE, NOAA-18
            "uav_latitude": 24.787,
            "uav_longitude": 121.005,
            "uav_altitude": 100.0
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/api/v1/satellite-gnb/batch-mapping",
                params=test_params
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "summary" in data
                assert "results" in data
    
    @pytest.mark.asyncio
    async def test_satellite_tracking(self):
        """測試衛星追蹤功能"""
        test_data = {
            "satellite_ids": "25544,20580",
            "update_interval": 60
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.netstack_url}/api/v1/satellite-gnb/start-tracking",
                json=test_data
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "tracking_info" in data
    
    @pytest.mark.asyncio
    async def test_ueransim_config_generation(self):
        """測試 UERANSIM 配置生成"""
        test_config = {
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
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.netstack_url}/api/v1/ueransim/config/generate",
                json=test_config
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "scenario_type" in data
    
    @pytest.mark.asyncio
    async def test_oneweb_constellation_initialize(self):
        """測試 OneWeb 星座初始化"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.netstack_url}/api/v1/oneweb/constellation/initialize"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "constellation_info" in data
    
    @pytest.mark.asyncio
    async def test_oneweb_orbital_tracking(self):
        """測試 OneWeb 軌道追蹤"""
        # 先初始化星座
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            await session.post(f"{self.netstack_url}/api/v1/oneweb/constellation/initialize")
            
            # 啟動追蹤
            test_params = {
                "satellite_ids": "1,2,3",
                "update_interval": 60
            }
            
            async with session.post(
                f"{self.netstack_url}/api/v1/oneweb/orbital-tracking/start",
                params=test_params
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "tracking_info" in data
                
                # 獲取 task_id 並停止追蹤
                task_id = data["tracking_info"]["task_id"]
                
                async with session.delete(
                    f"{self.netstack_url}/api/v1/oneweb/orbital-tracking/stop/{task_id}"
                ) as stop_response:
                    assert stop_response.status == 200
    
    @pytest.mark.asyncio
    async def test_oneweb_constellation_status(self):
        """測試 OneWeb 星座狀態"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/api/v1/oneweb/constellation/status"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "success" in data
                assert "constellation_status" in data
    
    @pytest.mark.asyncio
    async def test_oneweb_ueransim_deploy(self):
        """測試 OneWeb UERANSIM 部署"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.netstack_url}/api/v1/oneweb/ueransim/deploy"
            ) as response:
                # 可能會失敗如果沒有可用的衛星配置，但應該是有意義的錯誤
                assert response.status in [200, 400, 500]
                data = await response.json()
                assert "success" in data
    
    @pytest.mark.asyncio
    async def test_slice_types(self):
        """測試切片類型"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/api/v1/slice/types"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert isinstance(data, list)
                assert len(data) > 0
    
    @pytest.mark.asyncio
    async def test_ueransim_templates(self):
        """測試 UERANSIM 模板"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/api/v1/ueransim/templates"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "templates" in data
    
    @pytest.mark.asyncio
    async def test_ueransim_scenarios(self):
        """測試 UERANSIM 場景"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/api/v1/ueransim/scenarios"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "scenarios" in data
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """測試監控指標"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.netstack_url}/metrics"
            ) as response:
                assert response.status == 200
                # Prometheus 格式的指標 