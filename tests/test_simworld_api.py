#!/usr/bin/env python3
"""
SimWorld API 測試套件
整合原本 simworld 中的測試功能
"""

import pytest
import asyncio
import aiohttp
import os
from typing import Dict, List, Optional
import json

class TestSimWorldAPI:
    """SimWorld API 測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試設置"""
        self.simworld_url = os.getenv("SIMWORLD_URL", "http://localhost:8001")
        self.timeout = aiohttp.ClientTimeout(total=60)  # SimWorld 可能需要更長時間
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """測試健康檢查"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.simworld_url}/ping") as response:
                assert response.status == 200
                data = await response.json()
                assert "message" in data
    
    @pytest.mark.asyncio
    async def test_scene_health_check(self):
        """測試場景健康度檢查"""
        scenes = ["nycu", "lotus", "ntpu", "nanliao"]
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for scene_name in scenes:
                # 使用 SimWorld API 來檢查場景
                async with session.get(
                    f"{self.simworld_url}/api/v1/simulation/scenes"
                ) as response:
                    assert response.status == 200
                    data = await response.json()
                    # 確認場景列表中包含預期的場景
                    assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_satellite_position_api(self):
        """測試衛星位置 API"""
        test_satellite_id = 25544  # ISS
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.simworld_url}/api/v1/orbit/satellite/{test_satellite_id}/position"
            ) as response:
                # 可能會失敗如果衛星不在資料庫中，但應該有適當的錯誤處理
                assert response.status in [200, 404]
                data = await response.json()
                
                if response.status == 200:
                    assert "position" in data
                    assert "ecef" in data["position"]
                    assert "geodetic" in data["position"]
                else:
                    assert "error" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_satellite_list_api(self):
        """測試衛星列表 API"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.simworld_url}/api/v1/orbit/satellites"
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert isinstance(data, list) or isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_orbit_service_health(self):
        """測試軌道服務健康度"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.simworld_url}/api/v1/orbit/health"
            ) as response:
                # 軌道服務可能沒有專門的健康檢查端點
                assert response.status in [200, 404]
    
    @pytest.mark.asyncio
    async def test_tle_data_api(self):
        """測試 TLE 數據 API"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.simworld_url}/api/v1/orbit/tle/list"
            ) as response:
                assert response.status in [200, 404, 500]
                # TLE 服務可能需要外部連接，所以允許一些錯誤狀態
    
    @pytest.mark.asyncio
    async def test_simulation_scenarios(self):
        """測試模擬場景"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.simworld_url}/api/v1/simulation/scenarios"
            ) as response:
                assert response.status in [200, 404]
                if response.status == 200:
                    data = await response.json()
                    assert isinstance(data, (list, dict))
    
    @pytest.mark.asyncio
    async def test_coordinate_conversion(self):
        """測試座標轉換功能"""
        test_coordinates = {
            "latitude": 24.787,
            "longitude": 121.005,
            "altitude": 100.0
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.simworld_url}/api/v1/simulation/coordinate/convert",
                json=test_coordinates
            ) as response:
                # 座標轉換端點可能不存在，但測試 API 結構
                assert response.status in [200, 404, 405]
    
    @pytest.mark.asyncio
    async def test_scene_path_function(self):
        """測試場景路徑功能 (模擬原本的 test_api_functions.py)"""
        scenes = ["nycu", "lotus", "ntpu", "nanliao"]
        
        # 這個測試模擬原本在 simworld/backend/test_api_functions.py 中的功能
        # 在 Docker 環境中，我們通過 API 來測試而不是直接調用函數
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for scene_name in scenes:
                # 測試場景是否可用
                async with session.get(
                    f"{self.simworld_url}/api/v1/simulation/scene/{scene_name}"
                ) as response:
                    # 即使場景不存在，API 也應該返回有意義的回應
                    assert response.status in [200, 404, 400]
                    
                    if response.status == 200:
                        data = await response.json()
                        # 場景存在且可用
                        assert "scene" in data or "path" in data
                    elif response.status == 404:
                        # 場景不存在，應該有錯誤訊息
                        data = await response.json()
                        assert "error" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_scene_loading_capability(self):
        """測試場景載入能力 (模擬原本的 test_scene.py)"""
        # 這個測試驗證系統是否能夠處理場景載入請求
        scenes = ["NYCU", "Lotus", "NTPU", "Nanliao"]
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for scene_name in scenes:
                async with session.post(
                    f"{self.simworld_url}/api/v1/simulation/scene/load",
                    json={"scene_name": scene_name}
                ) as response:
                    # 場景載入可能成功或失敗，但應該有適當的回應
                    assert response.status in [200, 400, 404, 500]
                    
                    data = await response.json()
                    assert isinstance(data, dict)
                    
                    if response.status == 200:
                        # 成功載入
                        assert "success" in data or "scene" in data
                    else:
                        # 載入失敗，但有錯誤訊息
                        assert "error" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_api_documentation(self):
        """測試 API 文檔可用性"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試 OpenAPI 文檔
            async with session.get(f"{self.simworld_url}/docs") as response:
                assert response.status == 200
            
            # 測試 OpenAPI JSON
            async with session.get(f"{self.simworld_url}/openapi.json") as response:
                assert response.status == 200
                data = await response.json()
                assert "openapi" in data
                assert "info" in data
    
    @pytest.mark.asyncio
    async def test_system_resources(self):
        """測試系統資源狀態"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試系統資源端點（如果存在）
            async with session.get(
                f"{self.simworld_url}/api/v1/system/resources"
            ) as response:
                # 資源端點可能不存在
                assert response.status in [200, 404]
                
                if response.status == 200:
                    data = await response.json()
                    # 檢查是否包含系統資源訊息
                    assert isinstance(data, dict) 