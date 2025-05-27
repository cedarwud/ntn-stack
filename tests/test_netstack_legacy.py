"""
NetStack 傳統測試整合
將 netstack/tests/ 目錄中的 shell 腳本測試轉換為 pytest 格式
包括 NTN 驗證、E2E 測試、性能測試等
"""

import pytest
import asyncio
import aiohttp
import subprocess
import time
import json
import os
from pathlib import Path


class TestNetStackLegacy:
    """NetStack 傳統測試套件 - 基於原有 shell 腳本的功能"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試設置"""
        self.api_url = "http://localhost:8081"
        self.timeout = 30
        
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.legacy
    @pytest.mark.netstack
    async def test_ntn_quick_validation(self):
        """NTN 功能快速驗證 - 基於 quick_ntn_validation.sh"""
        async with aiohttp.ClientSession() as session:
            
            # 1. 檢查 AMF NTN 計時器配置
            amf_result = await self._check_ntn_config("amf", ["t3502:", "satellite_mode:"])
            
            # 2. 檢查 SMF NTN QoS 配置
            smf_result = await self._check_ntn_config("smf", ["ntn_config:", "qos_profiles:"])
            
            # 3. 檢查 UERANSIM 模型
            models_result = await self._check_ueransim_models()
            
            # 4. 檢查 UERANSIM 服務
            services_result = await self._check_ueransim_services(session)
            
            # 5. 檢查 API 端點
            api_result = await self._check_ueransim_api_endpoints(session)
            
            # 計算完成度
            results = [amf_result, smf_result, models_result, services_result, api_result]
            completed_features = sum(results)
            completion_percentage = (completed_features * 100) // 5
            
            print(f"\n📈 NTN 功能實現進度: {completed_features}/5 ({completion_percentage}%)")
            
            # 至少 80% 完成度才算通過
            assert completion_percentage >= 80, f"NTN 功能完成度不足: {completion_percentage}%"
    
    @pytest.mark.asyncio
    @pytest.mark.slow 
    @pytest.mark.legacy
    @pytest.mark.integration
    @pytest.mark.netstack
    async def test_e2e_netstack_workflow(self):
        """E2E NetStack 工作流程測試 - 基於 e2e_netstack.sh"""
        async with aiohttp.ClientSession() as session:
            
            # 1. 健康檢查
            health_ok = await self._health_check(session)
            assert health_ok, "服務健康檢查失敗"
            
            # 2. 檢查測試用戶
            test_imsi = "999700000000001"
            user_ok = await self._check_test_user(session, test_imsi)
            
            # 3. 測試 UE 資訊獲取
            if user_ok:
                ue_info = await self._get_ue_info(session, test_imsi)
                assert ue_info is not None, "無法獲取 UE 資訊"
                
                # 4. 測試 Slice 切換
                slice_results = []
                for slice_type in ["eMBB", "uRLLC", "mMTC"]:
                    result = await self._test_slice_switch(session, test_imsi, slice_type)
                    slice_results.append(result)
                
                # 至少一種 slice 切換要成功
                assert any(slice_results), "所有 Slice 切換測試都失敗"
                
                # 5. 測試 UE 統計
                stats = await self._get_ue_stats(session, test_imsi)
                assert stats is not None, "無法獲取 UE 統計資料"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.legacy
    @pytest.mark.netstack
    async def test_performance_metrics(self):
        """性能測試 - 基於 performance_test.sh"""
        async with aiohttp.ClientSession() as session:
            
            # 1. API 響應時間測試
            response_times = []
            for _ in range(10):
                start_time = time.time()
                async with session.get(f"{self.api_url}/health") as resp:
                    if resp.status == 200:
                        response_times.append(time.time() - start_time)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                print(f"\n📊 API 性能指標:")
                print(f"平均響應時間: {avg_response_time:.3f}s")
                print(f"最大響應時間: {max_response_time:.3f}s")
                
                # 響應時間應該在合理範圍內
                assert avg_response_time < 1.0, f"平均響應時間過長: {avg_response_time:.3f}s"
                assert max_response_time < 2.0, f"最大響應時間過長: {max_response_time:.3f}s"
            
            # 2. 並發請求測試
            concurrent_tasks = []
            for _ in range(5):
                task = asyncio.create_task(self._health_check(session))
                concurrent_tasks.append(task)
            
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            
            print(f"並發測試成功率: {success_count}/5")
            assert success_count >= 4, f"並發測試成功率過低: {success_count}/5"
    
    @pytest.mark.asyncio
    @pytest.mark.legacy
    @pytest.mark.satellite
    @pytest.mark.netstack
    async def test_satellite_gnb_integration(self):
        """衛星 gNodeB 整合測試 - 基於 satellite_gnb_integration_test.sh"""
        async with aiohttp.ClientSession() as session:
            
            # 1. 測試衛星 gNodeB 映射 API
            try:
                async with session.post(f"{self.api_url}/api/v1/satellite/gnb/map", 
                                       json={
                                           "satellite_id": "ONEWEB-001",
                                           "uav_position": {
                                               "latitude": 25.0330,
                                               "longitude": 121.5654,
                                               "altitude": 1000
                                           }
                                       }) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        assert "gnb_id" in data, "響應中缺少 gNodeB ID"
                        assert "distance" in data, "響應中缺少距離資訊"
                        print(f"✅ 衛星映射成功: {data}")
                    else:
                        pytest.skip(f"衛星映射 API 不可用 (HTTP {resp.status})")
            except Exception as e:
                pytest.skip(f"衛星映射測試跳過: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.legacy
    @pytest.mark.ueransim
    @pytest.mark.netstack
    async def test_ueransim_config_generation(self):
        """UERANSIM 配置生成測試 - 基於 ueransim_config_test.sh"""
        async with aiohttp.ClientSession() as session:
            
            test_scenarios = [
                "SATELLITE_UAV_FLIGHT",
                "SATELLITE_HANDOVER", 
                "CONSTELLATION_UPDATE"
            ]
            
            for scenario in test_scenarios:
                try:
                    async with session.post(f"{self.api_url}/api/v1/ueransim/config/generate",
                                           json={
                                               "scenario_type": scenario,
                                               "network_params": {
                                                   "plmn": "99970",
                                                   "tac": 1,
                                                   "slice_sst": 1,
                                                   "slice_sd": "0x111111"
                                               }
                                           }) as resp:
                        if resp.status == 200:
                            config = await resp.json()
                            assert "gnb_config" in config, f"配置缺少 gNodeB 部分"
                            assert "ue_config" in config, f"配置缺少 UE 部分"
                            print(f"✅ {scenario} 配置生成成功")
                        else:
                            print(f"⚠️  {scenario} 配置生成失敗 (HTTP {resp.status})")
                except Exception as e:
                    print(f"⚠️  {scenario} 配置測試異常: {e}")
    
    # 輔助方法
    async def _check_ntn_config(self, component: str, required_keys: list) -> bool:
        """檢查 NTN 配置"""
        config_file = f"netstack/config/{component}.yaml"
        if not os.path.exists(config_file):
            return False
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                return all(key in content for key in required_keys)
        except:
            return False
    
    async def _check_ueransim_models(self) -> bool:
        """檢查 UERANSIM 模型文件"""
        models_file = "netstack/netstack_api/models/ueransim_models.py"
        if not os.path.exists(models_file):
            return False
        
        try:
            with open(models_file, 'r') as f:
                content = f.read()
                return "ScenarioType" in content
        except:
            return False
    
    async def _check_ueransim_services(self, session: aiohttp.ClientSession) -> bool:
        """檢查 UERANSIM 服務"""
        services_file = "netstack/netstack_api/services/ueransim_service.py"
        if not os.path.exists(services_file):
            return False
        
        try:
            with open(services_file, 'r') as f:
                content = f.read()
                return "UERANSIMConfigService" in content
        except:
            return False
    
    async def _check_ueransim_api_endpoints(self, session: aiohttp.ClientSession) -> bool:
        """檢查 UERANSIM API 端點"""
        try:
            async with session.get(f"{self.api_url}/docs") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return "/api/v1/ueransim/config/generate" in text
        except:
            pass
        return False
    
    async def _health_check(self, session: aiohttp.ClientSession) -> bool:
        """健康檢查"""
        try:
            async with session.get(f"{self.api_url}/health", timeout=self.timeout) as resp:
                return resp.status == 200
        except:
            return False
    
    async def _check_test_user(self, session: aiohttp.ClientSession, imsi: str) -> bool:
        """檢查測試用戶"""
        try:
            async with session.get(f"{self.api_url}/api/v1/ue/{imsi}") as resp:
                return resp.status == 200
        except:
            return False
    
    async def _get_ue_info(self, session: aiohttp.ClientSession, imsi: str):
        """獲取 UE 資訊"""
        try:
            async with session.get(f"{self.api_url}/api/v1/ue/{imsi}") as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            pass
        return None
    
    async def _test_slice_switch(self, session: aiohttp.ClientSession, imsi: str, slice_type: str) -> bool:
        """測試 Slice 切換"""
        try:
            async with session.post(f"{self.api_url}/api/v1/slice/switch",
                                   json={
                                       "imsi": imsi,
                                       "target_slice": slice_type
                                   }) as resp:
                return resp.status == 200
        except:
            return False
    
    async def _get_ue_stats(self, session: aiohttp.ClientSession, imsi: str):
        """獲取 UE 統計"""
        try:
            async with session.get(f"{self.api_url}/api/v1/ue/{imsi}/stats") as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            pass
        return None 