#!/usr/bin/env python3
"""
NTN Stack 整合測試套件
整合原本 test_ntn_stack.py 的功能
"""

import pytest
import asyncio
import aiohttp
import os
import json
from typing import Dict, List, Optional
import time

class TestNTNStackIntegration:
    """NTN Stack 整合測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試設置"""
        self.netstack_url = os.getenv("NETSTACK_URL", "http://localhost:8081")
        self.simworld_url = os.getenv("SIMWORLD_URL", "http://localhost:8001") 
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.test_results = {}
    
    @pytest.mark.asyncio
    async def test_services_health(self):
        """測試所有服務的健康狀態"""
        services_health = {}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試 NetStack 健康狀態
            try:
                async with session.get(f"{self.netstack_url}/health") as response:
                    services_health["netstack"] = response.status == 200
            except Exception:
                services_health["netstack"] = False
            
            # 測試 SimWorld 健康狀態
            try:
                async with session.get(f"{self.simworld_url}/ping") as response:
                    services_health["simworld"] = response.status == 200
            except Exception:
                services_health["simworld"] = False
        
        # 確保至少一個服務是健康的
        assert any(services_health.values()), f"所有服務都不健康: {services_health}"
        
        # 記錄結果
        self.test_results["services_health"] = services_health
    
    @pytest.mark.asyncio
    async def test_satellite_to_gnb_integration(self):
        """測試衛星到 gNodeB 的完整流程"""
        test_satellite_id = 25544  # ISS
        test_uav_position = {
            "latitude": 24.787,
            "longitude": 121.005,
            "altitude": 100.0
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 步驟 1: 測試單個衛星映射
            mapping_params = {
                "satellite_id": test_satellite_id,
                "uav_latitude": test_uav_position["latitude"],
                "uav_longitude": test_uav_position["longitude"],
                "uav_altitude": test_uav_position["altitude"],
                "frequency": 2100,
                "bandwidth": 20
            }
            
            async with session.post(
                f"{self.netstack_url}/api/v1/satellite-gnb/mapping",
                params=mapping_params
            ) as response:
                assert response.status == 200
                mapping_result = await response.json()
                
                # 驗證映射結果結構
                if mapping_result.get("success"):
                    assert "gnb_config" in mapping_result
                    assert "network_parameters" in mapping_result
                    
                    gnb_config = mapping_result["gnb_config"]
                    assert "gnb_id" in gnb_config
                    assert "position" in gnb_config
                
                self.test_results["single_mapping"] = {
                    "success": mapping_result.get("success", False),
                    "satellite_id": test_satellite_id,
                    "has_gnb_config": "gnb_config" in mapping_result,
                    "response_time": response.headers.get("X-Response-Time", "unknown")
                }
            
            # 步驟 2: 測試批量衛星映射
            batch_params = {
                "satellite_ids": "25544,20580,43013",  # ISS, HUBBLE, NOAA-18
                "uav_latitude": test_uav_position["latitude"],
                "uav_longitude": test_uav_position["longitude"],
                "uav_altitude": test_uav_position["altitude"]
            }
            
            async with session.get(
                f"{self.netstack_url}/api/v1/satellite-gnb/batch-mapping",
                params=batch_params
            ) as response:
                assert response.status == 200
                batch_result = await response.json()
                
                if batch_result.get("success"):
                    assert "summary" in batch_result
                    assert "results" in batch_result
                    
                    summary = batch_result["summary"]
                    assert "total_satellites" in summary
                    assert "successful_conversions" in summary
                    assert "success_rate" in summary
                
                self.test_results["batch_mapping"] = {
                    "success": batch_result.get("success", False),
                    "total_satellites": batch_result.get("summary", {}).get("total_satellites", 0),
                    "successful_conversions": batch_result.get("summary", {}).get("successful_conversions", 0)
                }
    
    @pytest.mark.asyncio
    async def test_oneweb_constellation_workflow(self):
        """測試 OneWeb 星座的完整工作流程"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 步驟 1: 初始化 OneWeb 星座
            async with session.post(
                f"{self.netstack_url}/api/v1/oneweb/constellation/initialize"
            ) as response:
                assert response.status == 200
                init_result = await response.json()
                
                assert "success" in init_result
                if init_result["success"]:
                    assert "constellation_info" in init_result
                
                self.test_results["oneweb_initialization"] = {
                    "success": init_result.get("success", False),
                    "satellite_count": init_result.get("constellation_info", {}).get("total_satellites", 0)
                }
            
            # 步驟 2: 啟動軌道追蹤
            tracking_params = {
                "satellite_ids": "1,2,3,4,5",  # 前5顆衛星
                "update_interval": 60
            }
            
            task_id = None
            async with session.post(
                f"{self.netstack_url}/api/v1/oneweb/orbital-tracking/start",
                params=tracking_params
            ) as response:
                assert response.status == 200
                tracking_result = await response.json()
                
                if tracking_result.get("success"):
                    assert "tracking_info" in tracking_result
                    task_id = tracking_result["tracking_info"]["task_id"]
                
                self.test_results["oneweb_tracking_start"] = {
                    "success": tracking_result.get("success", False),
                    "task_id": task_id,
                    "satellite_count": len(tracking_params["satellite_ids"].split(","))
                }
            
            # 步驟 3: 檢查星座狀態
            async with session.get(
                f"{self.netstack_url}/api/v1/oneweb/constellation/status"
            ) as response:
                assert response.status == 200
                status_result = await response.json()
                
                assert "success" in status_result
                if status_result["success"]:
                    assert "constellation_status" in status_result
                
                self.test_results["oneweb_status"] = {
                    "success": status_result.get("success", False),
                    "active_tracking_tasks": status_result.get("constellation_status", {}).get("active_tracking_tasks", 0)
                }
            
            # 步驟 4: 停止追蹤（如果有任務ID）
            if task_id:
                async with session.delete(
                    f"{self.netstack_url}/api/v1/oneweb/orbital-tracking/stop/{task_id}"
                ) as response:
                    assert response.status == 200
                    stop_result = await response.json()
                    
                    self.test_results["oneweb_tracking_stop"] = {
                        "success": stop_result.get("success", False),
                        "task_id": task_id
                    }
    
    @pytest.mark.asyncio
    async def test_ueransim_configuration_generation(self):
        """測試 UERANSIM 配置生成的完整流程"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試配置生成
            config_request = {
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
            
            async with session.post(
                f"{self.netstack_url}/api/v1/ueransim/config/generate",
                json=config_request
            ) as response:
                assert response.status == 200
                config_result = await response.json()
                
                assert "success" in config_result
                if config_result["success"]:
                    assert "scenario_type" in config_result
                    assert "gnb_config" in config_result
                    assert "ue_config" in config_result
                
                self.test_results["ueransim_config"] = {
                    "success": config_result.get("success", False),
                    "scenario_type": config_result.get("scenario_type", "unknown"),
                    "has_configs": all(key in config_result for key in ["gnb_config", "ue_config"])
                }
    
    @pytest.mark.asyncio
    async def test_api_endpoints_availability(self):
        """測試重要 API 端點的可用性"""
        api_endpoints = [
            # NetStack 端點
            (self.netstack_url, "/health", "GET"),
            (self.netstack_url, "/api/v1/slice/types", "GET"),
            (self.netstack_url, "/api/v1/ueransim/templates", "GET"),
            (self.netstack_url, "/api/v1/ueransim/scenarios", "GET"),
            (self.netstack_url, "/metrics", "GET"),
            
            # SimWorld 端點
            (self.simworld_url, "/ping", "GET"),
            (self.simworld_url, "/docs", "GET"),
            (self.simworld_url, "/openapi.json", "GET"),
        ]
        
        endpoint_results = {}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for base_url, endpoint, method in api_endpoints:
                try:
                    if method == "GET":
                        async with session.get(f"{base_url}{endpoint}") as response:
                            endpoint_results[f"{base_url}{endpoint}"] = {
                                "status": response.status,
                                "available": response.status < 500
                            }
                    # 可以添加其他 HTTP 方法的測試
                except Exception as e:
                    endpoint_results[f"{base_url}{endpoint}"] = {
                        "status": 0,
                        "available": False,
                        "error": str(e)
                    }
        
        # 確保大部分端點都可用
        available_count = sum(1 for result in endpoint_results.values() if result["available"])
        total_count = len(endpoint_results)
        availability_rate = available_count / total_count
        
        assert availability_rate >= 0.7, f"API 端點可用率過低: {availability_rate:.2%}"
        
        self.test_results["api_endpoints"] = {
            "total_endpoints": total_count,
            "available_endpoints": available_count,
            "availability_rate": f"{availability_rate:.2%}",
            "details": endpoint_results
        }
    
    @pytest.mark.asyncio
    async def test_cross_service_communication(self):
        """測試跨服務通信"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試 NetStack 是否能夠與 SimWorld 通信
            # 通過衛星映射功能來驗證
            test_params = {
                "satellite_id": 25544,
                "uav_latitude": 24.787,
                "uav_longitude": 121.005,
                "uav_altitude": 100.0
            }
            
            async with session.post(
                f"{self.netstack_url}/api/v1/satellite-gnb/mapping",
                params=test_params
            ) as response:
                result = await response.json()
                
                # 如果成功，表示 NetStack 能與 SimWorld 通信
                # 如果失敗，檢查錯誤訊息是否指向連接問題
                communication_success = False
                error_type = "unknown"
                
                if response.status == 200 and result.get("success"):
                    communication_success = True
                elif response.status >= 500:
                    error_type = "server_error"
                elif "connection" in str(result).lower() or "timeout" in str(result).lower():
                    error_type = "connection_error"
                else:
                    error_type = "other_error"
                
                self.test_results["cross_service_communication"] = {
                    "success": communication_success,
                    "error_type": error_type,
                    "response_status": response.status,
                    "netstack_to_simworld": communication_success
                }
                
                # 至少不應該是連接錯誤
                assert error_type != "connection_error", "NetStack 無法連接到 SimWorld"
    
    @pytest.mark.asyncio 
    async def test_performance_benchmarks(self):
        """測試系統性能基準"""
        performance_results = {}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 測試單個衛星映射的響應時間
            start_time = time.time()
            async with session.post(
                f"{self.netstack_url}/api/v1/satellite-gnb/mapping",
                params={"satellite_id": 25544, "frequency": 2100, "bandwidth": 20}
            ) as response:
                response_time = time.time() - start_time
                
                performance_results["single_mapping_response_time"] = response_time
                assert response_time < 10.0, f"單個衛星映射響應時間過長: {response_time:.2f}s"
            
            # 測試批量映射的響應時間
            start_time = time.time()
            async with session.get(
                f"{self.netstack_url}/api/v1/satellite-gnb/batch-mapping",
                params={"satellite_ids": "25544,20580,43013"}
            ) as response:
                batch_response_time = time.time() - start_time
                
                performance_results["batch_mapping_response_time"] = batch_response_time
                assert batch_response_time < 30.0, f"批量衛星映射響應時間過長: {batch_response_time:.2f}s"
        
        self.test_results["performance"] = performance_results
    
    def teardown_method(self):
        """測試清理"""
        # 輸出測試結果摘要
        if hasattr(self, 'test_results') and self.test_results:
            print("\n=== 整合測試結果摘要 ===")
            print(json.dumps(self.test_results, indent=2, ensure_ascii=False)) 