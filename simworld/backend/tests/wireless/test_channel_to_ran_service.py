"""
無線通道到 RAN 參數轉換服務測試

測試 Sionna 通道參數到 UERANSIM RAN 參數的轉換功能。
"""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from app.domains.wireless.models.channel_model import (
    ChannelParameters,
    ChannelToRANMappingRequest,
    ChannelToRANMappingResponse,
    RANParameters,
    UERANSIMConfiguration,
    ChannelQualityMetrics,
    ChannelType,
)
from app.domains.wireless.services.channel_to_ran_service import ChannelToRANService


class TestChannelToRANService:
    """無線通道到 RAN 參數轉換服務測試類別"""

    def setup_method(self):
        """設置測試環境"""
        self.service = ChannelToRANService()

        # 創建測試用的通道參數
        self.test_channel = ChannelParameters(
            channel_id="test_channel_001",
            channel_type=ChannelType.LOS,
            frequency_hz=3.5e9,
            path_loss_db=120.0,
            shadow_fading_db=3.0,
            delay_spread_s=1e-6,
            azimuth_spread_deg=30.0,
            elevation_spread_deg=15.0,
            doppler_shift_hz=50.0,
            doppler_spread_hz=10.0,
            sinr_db=15.0,
            snr_db=20.0,
            tx_position=(0.0, 0.0, 30.0),
            rx_position=(1000.0, 0.0, 1.5),
        )

    @pytest.mark.asyncio
    async def test_convert_channel_to_ran_parameters(self):
        """測試通道參數到 RAN 參數的轉換"""
        # 準備轉換請求
        request = ChannelToRANMappingRequest(
            request_id=f"test_req_{uuid.uuid4().hex[:8]}",
            channel_parameters=self.test_channel,
            target_gnb_id=1,
            target_cell_id=1,
            mapping_mode="automatic",
        )

        # 執行轉換
        response = await self.service.convert_channel_to_ran_parameters(request)

        # 驗證轉換結果
        assert response.success is True
        assert response.request_id == request.request_id
        assert response.ran_parameters is not None
        assert response.mapping_quality_score > 0
        assert response.confidence_level > 0
        assert response.processing_time_ms > 0

        # 驗證 RAN 參數的合理性
        ran_params = response.ran_parameters
        assert ran_params.gnb_id == 1
        assert ran_params.cell_id == 1
        assert 10.0 <= ran_params.tx_power_dbm <= 46.0
        assert ran_params.frequency_hz == self.test_channel.frequency_hz
        assert ran_params.cell_range_km > 0

    @pytest.mark.asyncio
    async def test_convert_satellite_channel(self):
        """測試衛星通道參數的轉換"""
        # 創建衛星通道參數
        satellite_channel = ChannelParameters(
            channel_id="satellite_channel_001",
            channel_type=ChannelType.SATELLITE,
            frequency_hz=4.7e9,
            path_loss_db=200.0,  # 典型衛星路徑損耗
            doppler_shift_hz=1500.0,  # 大多普勒偏移
            sinr_db=10.0,
            tx_position=(0.0, 0.0, 600000.0),  # 600km 高度
            rx_position=(0.0, 0.0, 0.0),
        )

        request = ChannelToRANMappingRequest(
            request_id=f"sat_req_{uuid.uuid4().hex[:8]}",
            channel_parameters=satellite_channel,
            target_gnb_id=2,
            target_cell_id=2,
        )

        response = await self.service.convert_channel_to_ran_parameters(request)

        assert response.success is True
        ran_params = response.ran_parameters

        # 驗證衛星特殊參數
        assert ran_params.elevation_angle_deg is not None
        assert ran_params.doppler_compensation is True
        assert ran_params.beam_steering is True
        assert (
            "衛星" in response.recommendations[0] if response.recommendations else True
        )

    @pytest.mark.asyncio
    async def test_generate_ueransim_configuration(self):
        """測試 UERANSIM 配置生成"""
        # 首先轉換通道參數到 RAN 參數
        request = ChannelToRANMappingRequest(
            request_id=f"config_req_{uuid.uuid4().hex[:8]}",
            channel_parameters=self.test_channel,
            target_gnb_id=3,
            target_cell_id=3,
        )

        conversion_response = await self.service.convert_channel_to_ran_parameters(
            request
        )
        assert conversion_response.success is True

        # 生成 UERANSIM 配置
        config = await self.service.generate_ueransim_configuration(
            conversion_response.ran_parameters, ue_count=5, deployment_mode="container"
        )

        # 驗證配置
        assert config.config_id is not None
        assert config.gnb_config.gnb_id == 3
        assert len(config.ue_configs) == 5
        assert config.deployment_mode == "container"
        assert config.container_name is not None

        # 驗證 UE 配置
        for i, ue_config in enumerate(config.ue_configs):
            assert ue_config["ue_id"] == i + 1
            assert "imsi" in ue_config
            assert "sessions" in ue_config

    @pytest.mark.asyncio
    async def test_deploy_ueransim_configuration_container(self):
        """測試容器模式的 UERANSIM 部署"""
        # 創建測試配置
        ran_params = RANParameters(
            ran_config_id="test_config_001",
            gnb_id=4,
            cell_id=4,
            tx_power_dbm=30.0,
            dl_arfcn=632628,
            ul_arfcn=512628,
            band=77,
            cell_range_km=5.0,
            reference_signal_power_dbm=27.0,
            gnb_position=(24.0, 121.0, 100.0),
        )

        config = UERANSIMConfiguration(
            config_id="test_deploy_001",
            config_name="Test Container Deploy",
            gnb_config=ran_params,
            deployment_mode="container",
            container_name="test-ueransim-gnb-4",
        )

        # 執行部署
        result = await self.service.deploy_ueransim_configuration(config)

        # 驗證部署結果
        assert result["deployment_status"] == "success"
        assert "container_id" in result
        assert "gnb_endpoint" in result
        assert result["container_name"] == "test-ueransim-gnb-4"

    @pytest.mark.asyncio
    async def test_monitor_channel_quality(self):
        """測試通道品質監控"""
        channel_id = "test_channel_quality_001"

        metrics = await self.service.monitor_channel_quality(
            channel_id, measurement_duration_s=1.0
        )

        # 驗證監控結果
        assert metrics.channel_id == channel_id
        assert metrics.rsrp_dbm is not None
        assert metrics.rsrq_db is not None
        assert metrics.sinr_db is not None
        assert metrics.theoretical_throughput_mbps is not None
        assert metrics.measurement_duration_s == 1.0

    @pytest.mark.asyncio
    async def test_calculate_interference_impact(self):
        """測試干擾影響計算"""
        # 創建干擾通道
        interferer1 = ChannelParameters(
            channel_id="interferer_001",
            channel_type=ChannelType.URBAN,
            frequency_hz=3.6e9,  # 相近頻率
            path_loss_db=110.0,
            sinr_db=12.0,
            tx_position=(500.0, 0.0, 30.0),
            rx_position=(1000.0, 0.0, 1.5),
        )

        interferer2 = ChannelParameters(
            channel_id="interferer_002",
            channel_type=ChannelType.NLOS,
            frequency_hz=3.7e9,  # 不同頻率
            path_loss_db=125.0,
            sinr_db=8.0,
            tx_position=(800.0, 200.0, 30.0),
            rx_position=(1000.0, 0.0, 1.5),
        )

        # 計算干擾影響
        impact = await self.service.calculate_interference_impact(
            self.test_channel, [interferer1, interferer2]
        )

        # 驗證干擾分析結果
        assert "sir_degradation_db" in impact
        assert "total_interference_power_dbm" in impact
        assert "frequency_separation_benefit_db" in impact
        assert "interference_source_count" in impact
        assert impact["interference_source_count"] == 2
        assert impact["sir_degradation_db"] >= 0

    @pytest.mark.asyncio
    async def test_optimize_ran_configuration(self):
        """測試 RAN 配置優化"""
        # 創建當前 RAN 配置
        current_ran = RANParameters(
            ran_config_id="optimize_test_001",
            gnb_id=5,
            cell_id=5,
            tx_power_dbm=25.0,
            dl_arfcn=632628,
            ul_arfcn=512628,
            band=77,
            cell_range_km=3.0,
            reference_signal_power_dbm=22.0,
            sinr_threshold_db=5.0,
            gnb_position=(25.0, 121.0, 50.0),
        )

        # 設定優化目標
        target_metrics = {
            "target_sinr_db": 12.0,
            "target_coverage_km": 5.0,
        }

        constraints = {
            "max_power_dbm": 40.0,
            "min_sinr_db": 0.0,
        }

        # 執行優化
        optimized_ran = await self.service.optimize_ran_configuration(
            current_ran, target_metrics, constraints
        )

        # 驗證優化結果
        assert optimized_ran.gnb_id == current_ran.gnb_id
        assert optimized_ran.ran_config_id != current_ran.ran_config_id
        assert optimized_ran.sinr_threshold_db >= target_metrics["target_sinr_db"]
        assert optimized_ran.cell_range_km == target_metrics["target_coverage_km"]
        assert optimized_ran.tx_power_dbm <= constraints["max_power_dbm"]

    def test_frequency_to_arfcn_mapping(self):
        """測試頻率到 ARFCN 的映射"""
        details = {}

        # 測試 3.5 GHz 頻率
        dl_arfcn, ul_arfcn, band = self.service._map_frequency_to_arfcn(3.5e9, details)

        assert dl_arfcn == 632628
        assert ul_arfcn == dl_arfcn - 120000
        assert band == 77
        assert "frequency_mapping" in details

    def test_calculate_tx_power(self):
        """測試發射功率計算"""
        details = {}

        # 測試一般場景
        tx_power = self.service._calculate_tx_power(120.0, ChannelType.LOS, details)
        assert 10.0 <= tx_power <= 46.0
        assert "power_budget" in details

        # 測試衛星場景
        sat_power = self.service._calculate_tx_power(
            200.0, ChannelType.SATELLITE, details
        )
        assert sat_power > tx_power  # 衛星需要更高功率

    def test_calculate_cell_range(self):
        """測試小區覆蓋範圍計算"""
        details = {}

        range_km = self.service._calculate_cell_range(
            30.0, 120.0, ChannelType.LOS, details
        )

        assert range_km > 0
        assert range_km <= 20  # 一般限制
        assert "coverage_calculation" in details

    def test_assess_mapping_quality(self):
        """測試映射品質評估"""
        ran_params = RANParameters(
            ran_config_id="quality_test_001",
            gnb_id=6,
            cell_id=6,
            tx_power_dbm=30.0,
            dl_arfcn=632628,
            ul_arfcn=512628,
            band=77,
            cell_range_km=5.0,
            reference_signal_power_dbm=27.0,
            gnb_position=(25.0, 121.0, 50.0),
        )

        details = {}
        quality_score, confidence = self.service._assess_mapping_quality(
            self.test_channel, ran_params, details
        )

        assert 0.0 <= quality_score <= 1.0
        assert 0.0 <= confidence <= 1.0
        assert "quality_assessment" in details

    @pytest.mark.asyncio
    async def test_extract_channel_parameters_from_sionna(self):
        """測試從 Sionna 提取通道參數（模擬）"""
        # 注意：這裡使用 None 作為 session，因為我們使用模擬實現
        channel_params = await self.service.extract_channel_parameters_from_sionna(
            None, "urban_scene", 1, 2, 3.6e9
        )

        assert channel_params.channel_id is not None
        assert channel_params.channel_type == ChannelType.URBAN
        assert channel_params.frequency_hz == 3.6e9
        assert channel_params.path_loss_db > 0
        assert channel_params.tx_position is not None
        assert channel_params.rx_position is not None

    @pytest.mark.asyncio
    async def test_update_ran_parameters_realtime(self):
        """測試即時更新 RAN 參數"""
        success = await self.service.update_ran_parameters_realtime(
            7, self.test_channel
        )

        # 模擬實現應該返回 True
        assert success is True

    def test_calculate_distance(self):
        """測試距離計算"""
        pos1 = (0.0, 0.0, 0.0)
        pos2 = (3.0, 4.0, 0.0)

        distance = self.service._calculate_distance(pos1, pos2)
        assert distance == 5.0  # 3-4-5 三角形

    def test_channel_types_coverage(self):
        """測試所有通道類型的處理"""
        details = {}

        for channel_type in ChannelType:
            # 測試天線增益獲取
            gain = self.service._get_antenna_gain(channel_type)
            assert gain > 0

            # 測試發射功率計算
            power = self.service._calculate_tx_power(120.0, channel_type, details)
            assert 10.0 <= power <= 46.0
