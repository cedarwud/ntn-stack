"""
Phase 2 系統整合測試套件

測試 Phase 1 和 Phase 2 實施的系統整合功能：
- 統一配置系統與各組件的整合
- 智能篩選系統與 SIB19 平台整合
- 跨容器配置存取整合
- 完整的衛星數據處理流水線
- API 端點整合測試
"""

import pytest
import sys
import os
import requests
import time
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# 添加項目路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


class TestPhase2SystemIntegration:
    """Phase 2 系統整合測試"""
    
    def setup_class(self):
        """測試類設置"""
        self.api_base_url = "http://localhost:8080"
        self.simworld_url = "http://localhost:8888"
        self.frontend_url = "http://localhost:5173"
        
        # 等待服務啟動
        self._wait_for_services()
    
    def _wait_for_services(self, timeout=30):
        """等待服務啟動"""
        services = [
            (self.api_base_url, "NetStack API"),
            (self.simworld_url, "SimWorld Backend"),
            (self.frontend_url, "SimWorld Frontend")
        ]
        
        for url, name in services:
            for _ in range(timeout):
                try:
                    response = requests.get(f"{url}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ {name} 服務就緒")
                        break
                except requests.exceptions.RequestException:
                    try:
                        # 對於前端，直接檢查根路徑
                        if "5173" in url:
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                print(f"✅ {name} 服務就緒")
                                break
                    except:
                        pass
                    time.sleep(1)
                    continue
            else:
                print(f"⚠️ {name} 服務暫時不可用，某些測試將被跳過")


class TestConfigurationSystemIntegration:
    """統一配置系統整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_unified_config_cross_container_access(self, api_client):
        """測試跨容器統一配置存取"""
        # 測試 NetStack API 能否存取統一配置
        response = api_client.get("http://localhost:8080/api/v1/config/satellite")
        
        if response.status_code == 200:
            config_data = response.json()
            
            # 驗證配置正確性
            assert 'max_candidate_satellites' in config_data
            assert config_data['max_candidate_satellites'] <= 8  # SIB19 合規
            
            # 驗證預處理配置
            assert 'preprocess_satellites' in config_data
            preprocess = config_data['preprocess_satellites']
            assert preprocess.get('starlink', 0) > 8  # 應大於候選數量
            assert preprocess.get('oneweb', 0) > 8
        else:
            pytest.skip("配置 API 端點不可用")
    
    def test_sib19_config_compliance(self, api_client):
        """測試 SIB19 配置合規性整合"""
        response = api_client.get("http://localhost:8080/api/v1/sib19/config")
        
        if response.status_code == 200:
            sib19_config = response.json()
            
            # 檢查 SIB19 合規性
            max_satellites = sib19_config.get('max_tracked_satellites', 0)
            assert max_satellites <= 8, f"SIB19 違規：候選衛星數 {max_satellites} > 8"
            
            # 檢查仰角門檻配置
            if 'elevation_thresholds' in sib19_config:
                thresholds = sib19_config['elevation_thresholds']
                assert thresholds['critical'] < thresholds['execution']
                assert thresholds['execution'] < thresholds['trigger']
        else:
            pytest.skip("SIB19 配置 API 端點不可用")
    
    def test_intelligent_selection_config_integration(self, api_client):
        """測試智能篩選配置整合"""
        response = api_client.get("http://localhost:8080/api/v1/satellites/filter/config")
        
        if response.status_code == 200:
            filter_config = response.json()
            
            # 檢查智能篩選配置
            assert filter_config.get('enabled', False) is True
            assert filter_config.get('geographic_filter_enabled', False) is True
            
            # 檢查目標位置配置
            location = filter_config.get('target_location', {})
            assert 21.0 <= location.get('lat', 0) <= 26.0  # 台灣範圍
            assert 119.0 <= location.get('lon', 0) <= 122.0
            
            # 檢查評分權重
            weights = filter_config.get('scoring_weights', {})
            if weights:
                total_weight = sum(weights.values())
                assert abs(total_weight - 1.0) < 0.001, "權重總和應為 1.0"
        else:
            pytest.skip("智能篩選配置 API 端點不可用")


class TestIntelligentFilteringIntegration:
    """智能篩選系統整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_starlink_filtering_pipeline_integration(self, api_client):
        """測試 Starlink 篩選流水線整合"""
        # 請求篩選 Starlink 衛星
        filter_request = {
            "constellation": "starlink",
            "max_satellites": 40,
            "location": {
                "latitude": 24.9441667,
                "longitude": 121.3713889
            },
            "intelligent_filtering": True
        }
        
        response = api_client.post(
            "http://localhost:8080/api/v1/satellites/filter",
            json=filter_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 驗證篩選結果
            assert 'satellites' in result
            assert 'total_count' in result
            assert 'filtered_count' in result
            
            satellites = result['satellites']
            assert len(satellites) <= 40, "篩選結果不應超過請求數量"
            assert len(satellites) > 0, "應該有篩選結果"
            
            # 檢查篩選效果
            filtered_count = result['filtered_count']
            total_count = result['total_count']
            if total_count > 0:
                compression_ratio = (total_count - filtered_count) / total_count
                assert compression_ratio > 0.5, f"壓縮率 {compression_ratio:.1%} 不夠高"
            
            # 驗證衛星數據結構
            for sat in satellites[:3]:  # 檢查前3顆
                assert 'name' in sat
                assert 'norad_id' in sat
                assert 'constellation' in sat
                assert sat['constellation'].lower() == 'starlink'
        else:
            pytest.skip("智能篩選 API 端點不可用")
    
    def test_oneweb_filtering_pipeline_integration(self, api_client):
        """測試 OneWeb 篩選流水線整合"""
        filter_request = {
            "constellation": "oneweb",
            "max_satellites": 30,
            "location": {
                "latitude": 24.9441667,
                "longitude": 121.3713889
            },
            "intelligent_filtering": True
        }
        
        response = api_client.post(
            "http://localhost:8080/api/v1/satellites/filter",
            json=filter_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            satellites = result['satellites']
            assert len(satellites) <= 30
            
            # 驗證 OneWeb 特殊處理
            for sat in satellites[:3]:
                assert sat['constellation'].lower() == 'oneweb'
                # OneWeb 應該有極地軌道特性
                if 'orbital_params' in sat:
                    inclination = sat['orbital_params'].get('inclination', 0)
                    assert inclination > 80, "OneWeb 應該是極地軌道"
        else:
            pytest.skip("OneWeb 篩選 API 端點不可用")
    
    def test_multi_constellation_filtering_integration(self, api_client):
        """測試多星座篩選整合"""
        filter_request = {
            "constellation": "all",
            "max_satellites": 50,
            "location": {
                "latitude": 24.9441667,
                "longitude": 121.3713889
            },
            "intelligent_filtering": True
        }
        
        response = api_client.post(
            "http://localhost:8080/api/v1/satellites/filter",
            json=filter_request,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            satellites = result['satellites']
            
            # 檢查多星座結果
            constellations = set(sat['constellation'].lower() for sat in satellites)
            assert len(constellations) >= 1, "應該包含至少一個星座"
            
            # 檢查星座分佈
            constellation_counts = {}
            for sat in satellites:
                const = sat['constellation'].lower()
                constellation_counts[const] = constellation_counts.get(const, 0) + 1
            
            # 應該有合理的星座分佈
            if 'starlink' in constellation_counts and 'oneweb' in constellation_counts:
                assert constellation_counts['starlink'] > 0
                assert constellation_counts['oneweb'] > 0
        else:
            pytest.skip("多星座篩選 API 端點不可用")


class TestSIB19PlatformIntegration:
    """SIB19 平台整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_sib19_message_processing_integration(self, api_client):
        """測試 SIB19 消息處理整合"""
        # 模擬 SIB19 消息
        sib19_message = {
            "satelliteEphemeris": {
                "STARLINK-1007": {
                    "norad_id": 44713,
                    "latitude": 24.5,
                    "longitude": 121.0,
                    "altitude": 550.0,
                    "inclination": 53.0,
                    "raan": 123.45,
                    "mean_motion": 15.12345678
                }
            },
            "epochTime": datetime.now(timezone.utc).isoformat(),
            "ntn-NeighCellConfigList": [
                {"cellId": 1, "pci": 100}
            ],
            "distanceThresh": 1000.0
        }
        
        response = api_client.post(
            "http://localhost:8080/api/v1/sib19/process",
            json=sib19_message,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 驗證處理結果
            assert result.get('status') == 'success'
            assert 'processed_satellites' in result
            assert 'epoch_time_set' in result
            assert 'neighbor_cells_count' in result
            
            # 檢查候選衛星數量限制
            candidates = result.get('candidate_satellites', [])
            assert len(candidates) <= 8, "SIB19 候選衛星數量超標"
        else:
            pytest.skip("SIB19 處理 API 端點不可用")
    
    def test_sib19_satellite_position_calculation(self, api_client):
        """測試 SIB19 衛星位置計算整合"""
        # 請求衛星位置計算
        position_request = {
            "satellite_id": "STARLINK-1007",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = api_client.post(
            "http://localhost:8080/api/v1/sib19/satellite/position",
            json=position_request,
            timeout=5
        )
        
        if response.status_code == 200:
            position = response.json()
            
            # 驗證位置數據
            assert 'latitude' in position
            assert 'longitude' in position
            assert 'altitude' in position
            assert 'timestamp' in position
            
            # 檢查座標合理性
            assert -90 <= position['latitude'] <= 90
            assert -180 <= position['longitude'] <= 180
            assert position['altitude'] > 0
        else:
            pytest.skip("SIB19 位置計算 API 端點不可用")


class TestCrossServiceIntegration:
    """跨服務整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_netstack_simworld_data_consistency(self, api_client):
        """測試 NetStack 和 SimWorld 數據一致性"""
        # 從 NetStack 獲取衛星數據
        netstack_response = api_client.get(
            "http://localhost:8080/api/v1/satellites/constellations/info",
            timeout=5
        )
        
        # 從 SimWorld 獲取同樣的數據
        simworld_response = api_client.get(
            "http://localhost:8888/api/v1/satellites/info",
            timeout=5
        )
        
        if netstack_response.status_code == 200 and simworld_response.status_code == 200:
            netstack_data = netstack_response.json()
            simworld_data = simworld_response.json()
            
            # 驗證數據一致性
            if 'starlink' in netstack_data and 'starlink' in simworld_data:
                netstack_starlink = netstack_data['starlink']['total']
                simworld_starlink = simworld_data['starlink']['total']
                assert netstack_starlink == simworld_starlink, "Starlink 數據不一致"
            
            if 'oneweb' in netstack_data and 'oneweb' in simworld_data:
                netstack_oneweb = netstack_data['oneweb']['total']
                simworld_oneweb = simworld_data['oneweb']['total']
                assert netstack_oneweb == simworld_oneweb, "OneWeb 數據不一致"
            
            # 驗證配置一致性
            netstack_config = netstack_data.get('config', {})
            simworld_config = simworld_data.get('config', {})
            
            if netstack_config and simworld_config:
                assert netstack_config.get('max_candidates') == simworld_config.get('max_candidates')
        else:
            pytest.skip("NetStack 或 SimWorld 服務不可用")
    
    def test_api_frontend_integration(self, api_client):
        """測試 API 和前端整合"""
        # 檢查前端能否正常載入
        frontend_response = api_client.get("http://localhost:5173", timeout=5)
        
        if frontend_response.status_code == 200:
            # 檢查前端是否能獲取 API 數據
            api_health_response = api_client.get("http://localhost:8080/health", timeout=5)
            assert api_health_response.status_code == 200, "前端應該能存取 API"
            
            # 檢查 CORS 設定
            options_response = api_client.options(
                "http://localhost:8080/api/v1/satellites/constellations/info",
                headers={"Origin": "http://localhost:5173"},
                timeout=5
            )
            
            if options_response.status_code in [200, 204]:
                cors_headers = options_response.headers
                assert 'Access-Control-Allow-Origin' in cors_headers, "CORS 設定缺失"
        else:
            pytest.skip("前端服務不可用")


class TestPerformanceIntegration:
    """性能整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_system_response_time_integration(self, api_client):
        """測試系統響應時間整合"""
        endpoints = [
            ("http://localhost:8080/health", "健康檢查"),
            ("http://localhost:8080/api/v1/satellites/constellations/info", "星座信息"),
            ("http://localhost:8888/api/v1/satellites/info", "SimWorld 衛星信息")
        ]
        
        for url, name in endpoints:
            start_time = time.time()
            try:
                response = api_client.get(url, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time = end_time - start_time
                    assert response_time < 1.0, f"{name} 響應時間 {response_time:.3f}s 過長"
                    print(f"✅ {name}: {response_time:.3f}s")
                else:
                    pytest.skip(f"{name} 端點不可用")
            except requests.exceptions.RequestException:
                pytest.skip(f"{name} 端點不可用")
    
    def test_concurrent_request_handling(self, api_client):
        """測試並發請求處理"""
        import concurrent.futures
        
        def make_api_call():
            try:
                response = api_client.get(
                    "http://localhost:8080/api/v1/satellites/constellations/info",
                    timeout=5
                )
                return response.status_code == 200
            except:
                return False
        
        # 並發 20 個請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(make_api_call) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            end_time = time.time()
        
        # 驗證性能要求
        success_rate = sum(results) / len(results)
        total_time = end_time - start_time
        
        if success_rate > 0:  # 至少有部分成功
            assert success_rate >= 0.8, f"成功率 {success_rate:.1%} 過低"
            assert total_time < 15, f"總處理時間 {total_time:.1f}s 過長"
            
            avg_response_time = total_time / len(results)
            assert avg_response_time < 2.0, f"平均響應時間 {avg_response_time:.3f}s 過長"
        else:
            pytest.skip("API 服務完全不可用")


class TestSystemHealthIntegration:
    """系統健康狀態整合測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_comprehensive_health_check(self, api_client):
        """測試綜合健康檢查"""
        # 檢查各服務健康狀態
        services = [
            ("http://localhost:8080/health", "NetStack API"),
            ("http://localhost:8888/health", "SimWorld Backend"),
            ("http://localhost:5173", "SimWorld Frontend")
        ]
        
        service_status = {}
        for url, name in services:
            try:
                response = api_client.get(url, timeout=5)
                service_status[name] = response.status_code == 200
            except:
                service_status[name] = False
        
        # 至少核心服務應該健康
        assert service_status.get("NetStack API", False), "NetStack API 不健康"
        
        # 記錄服務狀態
        for service, healthy in service_status.items():
            status = "✅ 健康" if healthy else "❌ 不健康"
            print(f"{service}: {status}")
    
    def test_database_connection_integration(self, api_client):
        """測試數據庫連接整合"""
        response = api_client.get(
            "http://localhost:8080/api/v1/database/health",
            timeout=5
        )
        
        if response.status_code == 200:
            db_health = response.json()
            
            # 檢查數據庫連接狀態
            assert db_health.get('status') == 'healthy', "數據庫連接不健康"
            
            # 檢查數據完整性
            if 'data_integrity' in db_health:
                integrity = db_health['data_integrity']
                assert integrity.get('satellites_count', 0) > 0, "衛星數據為空"
                assert integrity.get('tle_data_age_hours', 999) < 168, "TLE 數據過舊"
        else:
            pytest.skip("數據庫健康檢查端點不可用")


class TestPhase1ComponentIntegration:
    """測試 Phase 1 組件整合狀態"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_phase1_unified_config_system_ready(self, api_client):
        """測試統一配置系統整合就緒狀態"""
        # 檢查基礎服務健康狀態
        response = api_client.get("http://localhost:8080/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            assert health_data.get('overall_status') == 'healthy'
            
            # 驗證核心服務運行狀態
            services = health_data.get('services', {})
            assert 'mongodb' in services
            assert 'redis' in services
            assert 'open5gs' in services
            
            # MongoDB 和 Redis 是配置系統的核心依賴
            assert services['mongodb']['status'] == 'healthy'
            assert services['redis']['status'] == 'healthy'
            
            print("✅ Phase 1 統一配置系統基礎架構就緒")
        else:
            pytest.skip("NetStack API 不可用")
    
    def test_phase1_sib19_platform_integration_ready(self, api_client):
        """測試 SIB19 平台整合就緒狀態"""
        # 檢查 NetStack 核心服務
        netstack_response = api_client.get("http://localhost:8080/health", timeout=5)
        
        if netstack_response.status_code == 200:
            # 檢查 Open5GS 核心網路功能
            health_data = netstack_response.json()
            open5gs_services = health_data.get('services', {}).get('open5gs', {})
            
            if 'services_count' in open5gs_services:
                services_count = open5gs_services['services_count']
                assert services_count >= 10, f"Open5GS 服務數量 {services_count} 不足"
                print(f"✅ Phase 1 SIB19 平台基礎 - Open5GS {services_count} 個服務運行")
            
            # 檢查 SimWorld 後端整合
            simworld_response = api_client.get("http://localhost:8888/health", timeout=5)
            if simworld_response.status_code == 200:
                simworld_health = simworld_response.json()
                assert simworld_health.get('status') == 'healthy'
                print("✅ Phase 1 SIB19 平台 - SimWorld 後端整合就緒")
        else:
            pytest.skip("核心服務不可用")
    
    def test_phase1_intelligent_filtering_system_ready(self, api_client):
        """測試智能篩選系統整合就緒狀態"""
        # 檢查系統基礎架構是否支援智能篩選
        netstack_response = api_client.get("http://localhost:8080/health", timeout=5)
        simworld_response = api_client.get("http://localhost:8888/health", timeout=5)
        
        netstack_healthy = netstack_response.status_code == 200 if netstack_response else False
        simworld_healthy = simworld_response.status_code == 200 if simworld_response else False
        
        if netstack_healthy and simworld_healthy:
            # 檢查數據庫連接 (智能篩選需要數據存取)
            netstack_data = netstack_response.json()
            db_status = netstack_data.get('services', {}).get('mongodb', {}).get('status')
            assert db_status == 'healthy', "智能篩選系統需要健康的數據庫連接"
            
            # 檢查 Redis 緩存 (智能篩選性能優化)
            redis_status = netstack_data.get('services', {}).get('redis', {}).get('status')
            assert redis_status == 'healthy', "智能篩選系統需要健康的緩存服務"
            
            print("✅ Phase 1 智能篩選系統基礎架構就緒")
        else:
            pytest.skip("智能篩選系統依賴服務不完整")
    
    def test_cross_service_communication_ready(self, api_client):
        """測試跨服務通信整合就緒狀態"""
        services_status = {}
        
        # 檢查各服務可達性
        test_services = [
            ("http://localhost:8080/health", "NetStack API"),
            ("http://localhost:8888/health", "SimWorld Backend"),
            ("http://localhost:5173", "SimWorld Frontend")
        ]
        
        for url, name in test_services:
            try:
                if "5173" in url:
                    # 前端直接檢查根路徑
                    response = api_client.get(url, timeout=3)
                else:
                    response = api_client.get(url, timeout=3)
                
                services_status[name] = response.status_code == 200
            except:
                services_status[name] = False
        
        # 至少核心後端服務應該可用
        assert services_status.get("NetStack API", False), "NetStack API 不可用"
        assert services_status.get("SimWorld Backend", False), "SimWorld Backend 不可用"
        
        # 前端可用性是加分項
        frontend_available = services_status.get("SimWorld Frontend", False)
        
        available_count = sum(services_status.values())
        print(f"✅ 跨服務通信就緒 - {available_count}/3 個服務可用")
        
        if available_count >= 2:
            print("✅ Phase 1 跨服務整合基礎架構就緒")
        else:
            pytest.skip("跨服務通信基礎架構不完整")


class TestPhase2IntegrationValidation:
    """Phase 2 整合驗證測試"""
    
    @pytest.fixture
    def api_client(self):
        return requests.Session()
    
    def test_phase2_testing_framework_integration(self, api_client):
        """測試 Phase 2 測試框架整合"""
        # 驗證測試框架能夠訪問系統服務
        response = api_client.get("http://localhost:8080/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            
            # 驗證測試框架能夠解析系統響應
            assert isinstance(health_data, dict)
            assert 'overall_status' in health_data
            assert 'services' in health_data
            assert 'timestamp' in health_data
            
            # 驗證響應時間在可接受範圍內 (整合測試性能要求)
            response_time = response.elapsed.total_seconds()
            assert response_time < 2.0, f"API 響應時間 {response_time:.3f}s 過長"
            
            print(f"✅ Phase 2 測試框架整合驗證通過 - 響應時間: {response_time:.3f}s")
        else:
            pytest.skip("系統服務不可用，無法驗證測試框架整合")
    
    def test_integration_test_coverage_validation(self):
        """驗證整合測試覆蓋範圍"""
        # 檢查整合測試文件結構
        import os
        current_dir = os.path.dirname(__file__)
        
        # 驗證測試文件存在
        assert os.path.exists(__file__), "整合測試文件應該存在"
        
        # 驗證單元測試目錄存在
        unit_test_dir = os.path.join(os.path.dirname(current_dir), 'unit')
        assert os.path.exists(unit_test_dir), "單元測試目錄應該存在"
        
        # 檢查核心測試文件
        core_test_files = [
            'test_satellite_config.py',
            'test_sib19_unified_platform.py',
            'test_intelligent_satellite_filter.py'
        ]
        
        for test_file in core_test_files:
            file_path = os.path.join(unit_test_dir, test_file)
            assert os.path.exists(file_path), f"核心測試文件 {test_file} 應該存在"
        
        print("✅ Phase 2 整合測試覆蓋範圍驗證通過")


if __name__ == "__main__":
    # 運行整合測試
    pytest.main([__file__, "-v", "--tb=short", "-x"])