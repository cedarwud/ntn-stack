"""
無線通道 API 測試

測試無線通道相關的 REST API 端點。
"""

import pytest
import uuid
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.domains.wireless.models.channel_model import (
    ChannelParameters,
    ChannelToRANMappingRequest,
    RANParameters,
    UERANSIMConfiguration,
    ChannelType,
)


class TestWirelessAPI:
    """無線通道 API 測試類別"""

    def setup_method(self):
        """設置測試環境"""
        self.client = TestClient(app)

        # 創建測試用的通道參數
        self.test_channel = {
            "channel_id": "api_test_channel_001",
            "channel_type": "line_of_sight",
            "frequency_hz": 3.5e9,
            "path_loss_db": 120.0,
            "shadow_fading_db": 3.0,
            "delay_spread_s": 1e-6,
            "azimuth_spread_deg": 30.0,
            "elevation_spread_deg": 15.0,
            "doppler_shift_hz": 50.0,
            "doppler_spread_hz": 10.0,
            "sinr_db": 15.0,
            "snr_db": 20.0,
            "tx_position": [0.0, 0.0, 30.0],
            "rx_position": [1000.0, 0.0, 1.5],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def test_health_check(self):
        """測試健康檢查端點"""
        response = self.client.get("/api/v1/wireless/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "wireless_channel_service"
        assert "timestamp" in data

    def test_get_supported_channel_types(self):
        """測試獲取支援的通道類型"""
        response = self.client.get("/api/v1/wireless/channel-types")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "line_of_sight" in data
        assert "satellite" in data
        assert "urban" in data

    def test_convert_channel_to_ran(self):
        """測試通道參數到 RAN 參數轉換 API"""
        # 準備轉換請求
        request_data = {
            "request_id": f"api_test_req_{uuid.uuid4().hex[:8]}",
            "channel_parameters": self.test_channel,
            "target_gnb_id": 1,
            "target_cell_id": 1,
            "mapping_mode": "automatic",
            "preserve_coverage": True,
            "requested_at": datetime.utcnow().isoformat(),
        }

        response = self.client.post(
            "/api/v1/wireless/channel-to-ran", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證回應結構
        assert data["success"] is True
        assert data["request_id"] == request_data["request_id"]
        assert "ran_parameters" in data
        assert "mapping_quality_score" in data
        assert "confidence_level" in data
        assert "processing_time_ms" in data

        # 驗證 RAN 參數
        ran_params = data["ran_parameters"]
        assert ran_params["gnb_id"] == 1
        assert ran_params["cell_id"] == 1
        assert "tx_power_dbm" in ran_params
        assert "dl_arfcn" in ran_params

    def test_extract_sionna_channel(self):
        """測試從 Sionna 提取通道參數 API"""
        response = self.client.post(
            "/api/v1/wireless/extract-sionna-channel",
            params={
                "scene_name": "nycu",
                "tx_device_id": 1,
                "rx_device_id": 2,
                "frequency_hz": 3.6e9,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證通道參數
        assert "channel_id" in data
        assert data["frequency_hz"] == 3.6e9
        assert "path_loss_db" in data
        assert "tx_position" in data
        assert "rx_position" in data

    def test_generate_ueransim_config(self):
        """測試生成 UERANSIM 配置 API"""
        # 首先獲取 RAN 參數
        convert_request = {
            "request_id": f"config_test_{uuid.uuid4().hex[:8]}",
            "channel_parameters": self.test_channel,
            "target_gnb_id": 2,
            "target_cell_id": 2,
        }

        convert_response = self.client.post(
            "/api/v1/wireless/channel-to-ran", json=convert_request
        )

        assert convert_response.status_code == 200
        ran_params = convert_response.json()["ran_parameters"]

        # 生成 UERANSIM 配置
        response = self.client.post(
            "/api/v1/wireless/generate-ueransim-config",
            json=ran_params,
            params={"ue_count": 3, "deployment_mode": "container"},
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證配置
        assert "config_id" in data
        assert data["gnb_config"]["gnb_id"] == 2
        assert len(data["ue_configs"]) == 3
        assert data["deployment_mode"] == "container"

    def test_deploy_ueransim(self):
        """測試部署 UERANSIM 配置 API"""
        # 創建測試配置
        config_data = {
            "config_id": f"deploy_test_{uuid.uuid4().hex[:8]}",
            "config_name": "API Test Deploy",
            "config_version": "1.0",
            "gnb_config": {
                "ran_config_id": "test_ran_001",
                "gnb_id": 3,
                "cell_id": 3,
                "tx_power_dbm": 30.0,
                "antenna_gain_dbi": 15.0,
                "noise_figure_db": 7.0,
                "dl_arfcn": 632628,
                "ul_arfcn": 512628,
                "band": 77,
                "cell_range_km": 5.0,
                "reference_signal_power_dbm": 27.0,
                "sinr_threshold_db": 10.0,
                "path_loss_model": "freespace",
                "fading_model": "rayleigh",
                "elevation_angle_deg": null,
                "doppler_compensation": false,
                "beam_steering": false,
                "gnb_position": [25.0, 121.0, 50.0],
                "config_timestamp": datetime.utcnow().isoformat(),
                "is_active": true,
            },
            "ue_configs": [],
            "amf_address": "127.0.0.1",
            "plmn_list": [{"mcc": "001", "mnc": "01"}],
            "deployment_mode": "container",
            "container_name": "test-ueransim-gnb-3",
            "is_deployed": false,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = self.client.post(
            "/api/v1/wireless/deploy-ueransim", json=config_data
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證部署結果
        assert data["deployment_status"] == "success"
        assert "container_id" in data
        assert "gnb_endpoint" in data

    def test_monitor_channel_quality(self):
        """測試監控通道品質 API"""
        channel_id = "api_test_channel_quality"

        response = self.client.get(
            f"/api/v1/wireless/channel-quality/{channel_id}",
            params={"measurement_duration_s": 2.0},
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證品質指標
        assert data["channel_id"] == channel_id
        assert "rsrp_dbm" in data
        assert "rsrq_db" in data
        assert "sinr_db" in data
        assert "theoretical_throughput_mbps" in data
        assert data["measurement_duration_s"] == 2.0

    def test_update_ran_parameters_realtime(self):
        """測試即時更新 RAN 參數 API"""
        gnb_id = 4

        response = self.client.put(
            f"/api/v1/wireless/ran-parameters/{gnb_id}/update", json=self.test_channel
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_interference_analysis(self):
        """測試干擾分析 API"""
        # 創建干擾通道
        interferer1 = {
            "channel_id": "interferer_api_001",
            "channel_type": "urban",
            "frequency_hz": 3.6e9,
            "path_loss_db": 110.0,
            "sinr_db": 12.0,
            "tx_position": [500.0, 0.0, 30.0],
            "rx_position": [1000.0, 0.0, 1.5],
            "timestamp": datetime.utcnow().isoformat(),
        }

        request_data = {
            "target_channel": self.test_channel,
            "interfering_channels": [interferer1],
        }

        response = self.client.post(
            "/api/v1/wireless/interference-analysis", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證干擾分析結果
        assert "sir_degradation_db" in data
        assert "total_interference_power_dbm" in data
        assert "interference_source_count" in data
        assert data["interference_source_count"] == 1

    def test_optimize_ran_configuration(self):
        """測試 RAN 配置優化 API"""
        # 當前 RAN 配置
        current_ran = {
            "ran_config_id": "optimize_api_test",
            "gnb_id": 5,
            "cell_id": 5,
            "tx_power_dbm": 25.0,
            "antenna_gain_dbi": 15.0,
            "noise_figure_db": 7.0,
            "dl_arfcn": 632628,
            "ul_arfcn": 512628,
            "band": 77,
            "cell_range_km": 3.0,
            "reference_signal_power_dbm": 22.0,
            "sinr_threshold_db": 5.0,
            "path_loss_model": "freespace",
            "fading_model": "rayleigh",
            "gnb_position": [25.0, 121.0, 50.0],
            "config_timestamp": datetime.utcnow().isoformat(),
            "is_active": true,
        }

        request_data = {
            "current_ran": current_ran,
            "target_metrics": {"target_sinr_db": 12.0, "target_coverage_km": 5.0},
            "constraints": {"max_power_dbm": 40.0},
        }

        response = self.client.post("/api/v1/wireless/optimize-ran", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 驗證優化結果
        assert data["gnb_id"] == 5
        assert data["ran_config_id"] != "optimize_api_test"  # 應該生成新 ID
        assert data["sinr_threshold_db"] >= 12.0
        assert data["cell_range_km"] == 5.0

    def test_batch_convert(self):
        """測試批量轉換 API"""
        # 創建多個轉換請求
        requests = []
        for i in range(3):
            channel = self.test_channel.copy()
            channel["channel_id"] = f"batch_test_{i}"

            request = {
                "request_id": f"batch_req_{i}",
                "channel_parameters": channel,
                "target_gnb_id": i + 1,
                "target_cell_id": i + 1,
            }
            requests.append(request)

        response = self.client.post(
            "/api/v1/wireless/batch-convert",
            json=requests,
            params={"max_concurrent": 3},
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證批量結果
        assert len(data) == 3
        for i, result in enumerate(data):
            assert result["request_id"] == f"batch_req_{i}"
            assert result["success"] is True

    def test_get_service_statistics(self):
        """測試獲取服務統計 API"""
        response = self.client.get("/api/v1/wireless/statistics")

        assert response.status_code == 200
        data = response.json()

        # 驗證統計資料
        assert "total_conversions" in data
        assert "successful_conversions" in data
        assert "average_processing_time_ms" in data
        assert "supported_channel_types" in data
        assert "last_update" in data

    def test_invalid_channel_type(self):
        """測試無效通道類型的處理"""
        invalid_channel = self.test_channel.copy()
        invalid_channel["channel_type"] = "invalid_type"

        request_data = {
            "request_id": "invalid_test",
            "channel_parameters": invalid_channel,
            "target_gnb_id": 1,
            "target_cell_id": 1,
        }

        response = self.client.post(
            "/api/v1/wireless/channel-to-ran", json=request_data
        )

        # 應該返回驗證錯誤
        assert response.status_code == 422

    def test_missing_required_fields(self):
        """測試缺少必要欄位的處理"""
        incomplete_channel = {
            "channel_id": "incomplete_test",
            "channel_type": "line_of_sight",
            # 缺少 frequency_hz 等必要欄位
        }

        request_data = {
            "request_id": "incomplete_test",
            "channel_parameters": incomplete_channel,
            "target_gnb_id": 1,
            "target_cell_id": 1,
        }

        response = self.client.post(
            "/api/v1/wireless/channel-to-ran", json=request_data
        )

        # 應該返回驗證錯誤
        assert response.status_code == 422

    def test_large_batch_size_limit(self):
        """測試批量大小限制"""
        # 創建超過限制的請求數量（>50）
        requests = []
        for i in range(51):
            request = {
                "request_id": f"limit_test_{i}",
                "channel_parameters": self.test_channel,
                "target_gnb_id": 1,
                "target_cell_id": 1,
            }
            requests.append(request)

        response = self.client.post("/api/v1/wireless/batch-convert", json=requests)

        # 應該返回 400 錯誤
        assert response.status_code == 400
        assert "批量請求數量不能超過 50 個" in response.json()["detail"]

    def test_satellite_channel_conversion(self):
        """測試衛星通道轉換的完整流程"""
        # 創建衛星通道參數
        satellite_channel = {
            "channel_id": "satellite_api_test",
            "channel_type": "satellite",
            "frequency_hz": 4.7e9,
            "path_loss_db": 200.0,
            "doppler_shift_hz": 1500.0,
            "sinr_db": 10.0,
            "tx_position": [0.0, 0.0, 600000.0],  # 600km 高度
            "rx_position": [0.0, 0.0, 0.0],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 1. 轉換通道參數到 RAN 參數
        convert_request = {
            "request_id": "satellite_test",
            "channel_parameters": satellite_channel,
            "target_gnb_id": 10,
            "target_cell_id": 10,
        }

        convert_response = self.client.post(
            "/api/v1/wireless/channel-to-ran", json=convert_request
        )

        assert convert_response.status_code == 200
        convert_data = convert_response.json()
        assert convert_data["success"] is True

        ran_params = convert_data["ran_parameters"]
        assert ran_params["elevation_angle_deg"] is not None
        assert ran_params["doppler_compensation"] is True
        assert ran_params["beam_steering"] is True

        # 2. 生成 UERANSIM 配置
        config_response = self.client.post(
            "/api/v1/wireless/generate-ueransim-config",
            json=ran_params,
            params={"ue_count": 2, "deployment_mode": "container"},
        )

        assert config_response.status_code == 200
        config_data = config_response.json()
        assert config_data["gnb_config"]["gnb_id"] == 10

        # 3. 模擬部署（在真實環境中會實際部署）
        deploy_response = self.client.post(
            "/api/v1/wireless/deploy-ueransim", json=config_data
        )

        assert deploy_response.status_code == 200
        deploy_data = deploy_response.json()
        assert deploy_data["deployment_status"] == "success"
