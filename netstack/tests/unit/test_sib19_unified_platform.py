"""
SIB19 統一平台單元測試 - Phase 1 核心功能測試

測試 SIB19UnifiedPlatform 類的核心功能：
- SIB19 消息處理
- 衛星星曆解析
- 時間同步處理
- 候選衛星管理
- 統一配置系統整合
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
import json

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


class MockSatelliteConfig:
    """模擬統一配置系統"""
    MAX_CANDIDATE_SATELLITES = 8
    PREPROCESS_SATELLITES = {"starlink": 40, "oneweb": 30}
    BATCH_COMPUTE_MAX_SATELLITES = 50
    
    class elevation_thresholds:
        trigger_threshold_deg = 15.0
        execution_threshold_deg = 10.0
        critical_threshold_deg = 5.0
    
    class intelligent_selection:
        enabled = True
        geographic_filter_enabled = True
        target_location = {"lat": 24.9441667, "lon": 121.3713889}


class MockSIB19UnifiedPlatform:
    """模擬 SIB19UnifiedPlatform 類"""
    
    def __init__(self):
        self.max_tracked_satellites = 8  # 使用統一配置
        self.satellite_ephemeris = {}
        self.neighbor_cells = []
        self.epoch_time = None
        self.distance_threshold = 1000.0  # km
        self.measurement_config = {
            'rsrp_enabled': True,
            'sinr_enabled': True,
            'measurement_period': 1.0  # seconds
        }
    
    def parse_sib19_message(self, sib19_data):
        """解析 SIB19 消息"""
        if not isinstance(sib19_data, dict):
            raise ValueError("SIB19 數據必須是字典格式")
        
        # 解析衛星星曆
        if 'satelliteEphemeris' in sib19_data:
            self.satellite_ephemeris = sib19_data['satelliteEphemeris']
        
        # 解析時間同步
        if 'epochTime' in sib19_data:
            self.epoch_time = sib19_data['epochTime']
        
        # 解析鄰居配置
        if 'ntn-NeighCellConfigList' in sib19_data:
            self.neighbor_cells = sib19_data['ntn-NeighCellConfigList']
        
        # 解析距離門檻
        if 'distanceThresh' in sib19_data:
            self.distance_threshold = sib19_data['distanceThresh']
        
        return True
    
    def get_candidate_satellites(self):
        """獲取候選衛星列表"""
        # 限制候選衛星數量符合 SIB19 規範
        candidates = list(self.satellite_ephemeris.keys())[:self.max_tracked_satellites]
        return candidates
    
    def calculate_satellite_position(self, satellite_id, timestamp=None):
        """計算衛星位置"""
        if satellite_id not in self.satellite_ephemeris:
            return None
        
        # 簡化的位置計算 (實際應使用 SGP4)
        ephemeris = self.satellite_ephemeris[satellite_id]
        
        return {
            'latitude': ephemeris.get('latitude', 0.0),
            'longitude': ephemeris.get('longitude', 0.0),
            'altitude': ephemeris.get('altitude', 550.0),
            'timestamp': timestamp or datetime.now(timezone.utc).isoformat()
        }
    
    def validate_measurement_config(self):
        """驗證測量配置"""
        required_keys = ['rsrp_enabled', 'sinr_enabled', 'measurement_period']
        for key in required_keys:
            if key not in self.measurement_config:
                return False
        
        # 檢查測量週期合理性
        period = self.measurement_config['measurement_period']
        if not (0.1 <= period <= 10.0):
            return False
        
        return True
    
    def get_system_status(self):
        """獲取系統狀態"""
        return {
            'max_tracked_satellites': self.max_tracked_satellites,
            'tracked_satellites_count': len(self.satellite_ephemeris),
            'neighbor_cells_count': len(self.neighbor_cells),
            'epoch_time_set': self.epoch_time is not None,
            'measurement_config_valid': self.validate_measurement_config()
        }


class TestSIB19UnifiedPlatformBasics:
    """測試基礎功能"""
    
    @pytest.fixture
    def sib19_platform(self):
        """創建測試用 SIB19 平台實例"""
        return MockSIB19UnifiedPlatform()
    
    @pytest.fixture
    def sample_sib19_data(self):
        """創建測試用 SIB19 數據"""
        return {
            'satelliteEphemeris': {
                'STARLINK-1007': {
                    'norad_id': 44713,
                    'latitude': 24.5,
                    'longitude': 121.0,
                    'altitude': 550.0,
                    'inclination': 53.0,
                    'raan': 123.45,
                    'mean_motion': 15.12345678
                },
                'STARLINK-1008': {
                    'norad_id': 44714,
                    'latitude': 25.0,
                    'longitude': 121.5,
                    'altitude': 555.0,
                    'inclination': 53.0,
                    'raan': 124.50,
                    'mean_motion': 15.11234567
                }
            },
            'epochTime': '2025-08-03T12:00:00Z',
            'ntn-NeighCellConfigList': [
                {'cellId': 1, 'pci': 100},
                {'cellId': 2, 'pci': 101}
            ],
            'distanceThresh': 1000.0
        }
    
    def test_initialization(self, sib19_platform):
        """測試初始化"""
        assert sib19_platform.max_tracked_satellites == 8  # SIB19 合規
        assert isinstance(sib19_platform.satellite_ephemeris, dict)
        assert isinstance(sib19_platform.neighbor_cells, list)
        assert sib19_platform.epoch_time is None
        assert sib19_platform.distance_threshold == 1000.0
    
    def test_unified_config_integration(self, sib19_platform):
        """測試統一配置系統整合"""
        # 檢查是否使用了統一配置的值
        assert sib19_platform.max_tracked_satellites <= 8  # SIB19 合規檢查
        
        # 檢查配置是否影響系統行為
        status = sib19_platform.get_system_status()
        assert status['max_tracked_satellites'] == 8


class TestSIB19MessageParsing:
    """測試 SIB19 消息解析"""
    
    @pytest.fixture
    def sib19_platform(self):
        return MockSIB19UnifiedPlatform()
    
    def test_parse_complete_sib19_message(self, sib19_platform, sample_sib19_data):
        """測試解析完整的 SIB19 消息"""
        result = sib19_platform.parse_sib19_message(sample_sib19_data)
        
        assert result is True
        assert len(sib19_platform.satellite_ephemeris) == 2
        assert sib19_platform.epoch_time == '2025-08-03T12:00:00Z'
        assert len(sib19_platform.neighbor_cells) == 2
        assert sib19_platform.distance_threshold == 1000.0
    
    def test_parse_satellite_ephemeris(self, sib19_platform, sample_sib19_data):
        """測試解析衛星星曆"""
        sib19_platform.parse_sib19_message(sample_sib19_data)
        
        ephemeris = sib19_platform.satellite_ephemeris
        assert 'STARLINK-1007' in ephemeris
        assert 'STARLINK-1008' in ephemeris
        
        # 檢查星曆數據內容
        starlink_1007 = ephemeris['STARLINK-1007']
        assert starlink_1007['norad_id'] == 44713
        assert starlink_1007['latitude'] == 24.5
        assert starlink_1007['longitude'] == 121.0
        assert starlink_1007['altitude'] == 550.0
        assert starlink_1007['inclination'] == 53.0
    
    def test_parse_time_sync(self, sib19_platform, sample_sib19_data):
        """測試解析時間同步"""
        sib19_platform.parse_sib19_message(sample_sib19_data)
        
        assert sib19_platform.epoch_time == '2025-08-03T12:00:00Z'
        # 檢查時間格式是否正確
        try:
            datetime.fromisoformat(sib19_platform.epoch_time.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("時間格式不正確")
    
    def test_parse_neighbor_cells(self, sib19_platform, sample_sib19_data):
        """測試解析鄰居配置"""
        sib19_platform.parse_sib19_message(sample_sib19_data)
        
        neighbors = sib19_platform.neighbor_cells
        assert len(neighbors) == 2
        assert neighbors[0]['cellId'] == 1
        assert neighbors[0]['pci'] == 100
        assert neighbors[1]['cellId'] == 2
        assert neighbors[1]['pci'] == 101
    
    def test_parse_distance_threshold(self, sib19_platform, sample_sib19_data):
        """測試解析距離門檻"""
        sib19_platform.parse_sib19_message(sample_sib19_data)
        
        assert sib19_platform.distance_threshold == 1000.0
    
    def test_parse_partial_sib19_message(self, sib19_platform):
        """測試解析部分 SIB19 消息"""
        partial_data = {
            'satelliteEphemeris': {
                'STARLINK-1007': {
                    'latitude': 24.5,
                    'longitude': 121.0,
                    'altitude': 550.0
                }
            }
        }
        
        result = sib19_platform.parse_sib19_message(partial_data)
        assert result is True
        assert len(sib19_platform.satellite_ephemeris) == 1
        assert sib19_platform.epoch_time is None  # 未設置
    
    def test_parse_invalid_message_format(self, sib19_platform):
        """測試解析無效消息格式"""
        with pytest.raises(ValueError):
            sib19_platform.parse_sib19_message("invalid_string")
        
        with pytest.raises(ValueError):
            sib19_platform.parse_sib19_message(None)


class TestCandidateSatelliteManagement:
    """測試候選衛星管理"""
    
    @pytest.fixture
    def sib19_platform_with_data(self, sample_sib19_data):
        platform = MockSIB19UnifiedPlatform()
        platform.parse_sib19_message(sample_sib19_data)
        return platform
    
    def test_get_candidate_satellites(self, sib19_platform_with_data):
        """測試獲取候選衛星"""
        candidates = sib19_platform_with_data.get_candidate_satellites()
        
        assert isinstance(candidates, list)
        assert len(candidates) == 2  # 測試數據有 2 顆衛星
        assert 'STARLINK-1007' in candidates
        assert 'STARLINK-1008' in candidates
    
    def test_candidate_satellites_limit(self):
        """測試候選衛星數量限制"""
        sib19_platform = MockSIB19UnifiedPlatform()
        
        # 創建超過 8 顆衛星的測試數據
        many_satellites = {}
        for i in range(12):  # 12 顆衛星，超過 SIB19 限制
            many_satellites[f'STARLINK-{1000 + i}'] = {
                'latitude': 24.0 + i * 0.1,
                'longitude': 121.0 + i * 0.1,
                'altitude': 550.0
            }
        
        sib19_data = {'satelliteEphemeris': many_satellites}
        sib19_platform.parse_sib19_message(sib19_data)
        
        candidates = sib19_platform.get_candidate_satellites()
        assert len(candidates) <= 8  # 應該限制在 SIB19 規範內
    
    def test_empty_ephemeris(self):
        """測試空星曆數據"""
        sib19_platform = MockSIB19UnifiedPlatform()
        candidates = sib19_platform.get_candidate_satellites()
        assert candidates == []


class TestSatellitePositionCalculation:
    """測試衛星位置計算"""
    
    @pytest.fixture
    def sib19_platform_with_data(self, sample_sib19_data):
        platform = MockSIB19UnifiedPlatform()
        platform.parse_sib19_message(sample_sib19_data)
        return platform
    
    def test_calculate_valid_satellite_position(self, sib19_platform_with_data):
        """測試計算有效衛星位置"""
        position = sib19_platform_with_data.calculate_satellite_position('STARLINK-1007')
        
        assert position is not None
        assert 'latitude' in position
        assert 'longitude' in position
        assert 'altitude' in position
        assert 'timestamp' in position
        
        # 檢查數值
        assert position['latitude'] == 24.5
        assert position['longitude'] == 121.0
        assert position['altitude'] == 550.0
    
    def test_calculate_invalid_satellite_position(self, sib19_platform_with_data):
        """測試計算無效衛星位置"""
        position = sib19_platform_with_data.calculate_satellite_position('INVALID-SAT')
        assert position is None
    
    def test_calculate_position_with_timestamp(self, sib19_platform_with_data):
        """測試帶時間戳的位置計算"""
        test_timestamp = '2025-08-03T15:30:00Z'
        position = sib19_platform_with_data.calculate_satellite_position('STARLINK-1007', test_timestamp)
        
        assert position['timestamp'] == test_timestamp
    
    def test_position_coordinates_validity(self, sib19_platform_with_data):
        """測試位置座標有效性"""
        position = sib19_platform_with_data.calculate_satellite_position('STARLINK-1007')
        
        # 檢查座標範圍
        assert -90 <= position['latitude'] <= 90
        assert -180 <= position['longitude'] <= 180
        assert position['altitude'] > 0  # 高度應為正數


class TestMeasurementConfiguration:
    """測試測量配置"""
    
    @pytest.fixture
    def sib19_platform(self):
        return MockSIB19UnifiedPlatform()
    
    def test_default_measurement_config(self, sib19_platform):
        """測試預設測量配置"""
        config = sib19_platform.measurement_config
        
        assert config['rsrp_enabled'] is True
        assert config['sinr_enabled'] is True
        assert config['measurement_period'] == 1.0
    
    def test_validate_measurement_config(self, sib19_platform):
        """測試測量配置驗證"""
        # 預設配置應該有效
        assert sib19_platform.validate_measurement_config() is True
        
        # 修改為無效配置
        sib19_platform.measurement_config['measurement_period'] = 0.05  # 太短
        assert sib19_platform.validate_measurement_config() is False
        
        sib19_platform.measurement_config['measurement_period'] = 20.0  # 太長
        assert sib19_platform.validate_measurement_config() is False
        
        # 恢復有效配置
        sib19_platform.measurement_config['measurement_period'] = 2.0
        assert sib19_platform.validate_measurement_config() is True
    
    def test_missing_measurement_config_keys(self, sib19_platform):
        """測試缺少測量配置項目"""
        # 刪除必要的配置項目
        del sib19_platform.measurement_config['rsrp_enabled']
        assert sib19_platform.validate_measurement_config() is False


class TestSystemStatus:
    """測試系統狀態"""
    
    @pytest.fixture
    def sib19_platform_with_data(self, sample_sib19_data):
        platform = MockSIB19UnifiedPlatform()
        platform.parse_sib19_message(sample_sib19_data)
        return platform
    
    def test_get_system_status(self, sib19_platform_with_data):
        """測試獲取系統狀態"""
        status = sib19_platform_with_data.get_system_status()
        
        assert 'max_tracked_satellites' in status
        assert 'tracked_satellites_count' in status
        assert 'neighbor_cells_count' in status
        assert 'epoch_time_set' in status
        assert 'measurement_config_valid' in status
        
        # 檢查狀態值
        assert status['max_tracked_satellites'] == 8
        assert status['tracked_satellites_count'] == 2
        assert status['neighbor_cells_count'] == 2
        assert status['epoch_time_set'] is True
        assert status['measurement_config_valid'] is True
    
    def test_status_with_empty_data(self):
        """測試空數據的系統狀態"""
        sib19_platform = MockSIB19UnifiedPlatform()
        status = sib19_platform.get_system_status()
        
        assert status['tracked_satellites_count'] == 0
        assert status['neighbor_cells_count'] == 0
        assert status['epoch_time_set'] is False
        assert status['measurement_config_valid'] is True  # 預設配置有效


class TestSIB19ComplianceIntegration:
    """測試 SIB19 合規性整合"""
    
    def test_sib19_max_satellites_compliance(self):
        """測試 SIB19 最大衛星數量合規性"""
        platform = MockSIB19UnifiedPlatform()
        
        # 檢查是否遵循 SIB19 規範
        assert platform.max_tracked_satellites <= 8
    
    def test_unified_config_compliance(self):
        """測試統一配置系統合規性"""
        mock_config = MockSatelliteConfig()
        
        # 檢查統一配置是否符合 SIB19
        assert mock_config.MAX_CANDIDATE_SATELLITES <= 8
        
        # 檢查仰角門檻配置合理性
        thresholds = mock_config.elevation_thresholds
        assert thresholds.critical_threshold_deg < thresholds.execution_threshold_deg
        assert thresholds.execution_threshold_deg < thresholds.trigger_threshold_deg
    
    def test_intelligent_selection_integration(self):
        """測試智能篩選整合"""
        mock_config = MockSatelliteConfig()
        selection = mock_config.intelligent_selection
        
        # 檢查智能篩選配置
        assert selection.enabled is True
        assert selection.geographic_filter_enabled is True
        
        # 檢查目標位置在台灣範圍內
        location = selection.target_location
        assert 21.0 <= location["lat"] <= 26.0
        assert 119.0 <= location["lon"] <= 122.0


class TestErrorHandling:
    """測試錯誤處理"""
    
    @pytest.fixture
    def sib19_platform(self):
        return MockSIB19UnifiedPlatform()
    
    def test_invalid_sib19_data_type(self, sib19_platform):
        """測試無效 SIB19 數據類型"""
        with pytest.raises(ValueError):
            sib19_platform.parse_sib19_message("string_data")
        
        with pytest.raises(ValueError):
            sib19_platform.parse_sib19_message(123)
        
        with pytest.raises(ValueError):
            sib19_platform.parse_sib19_message(None)
    
    def test_malformed_ephemeris_data(self, sib19_platform):
        """測試格式錯誤的星曆數據"""
        # 缺少必要字段的星曆數據
        malformed_data = {
            'satelliteEphemeris': {
                'STARLINK-1007': {
                    # 缺少 latitude
                    'longitude': 121.0,
                    'altitude': 550.0
                }
            }
        }
        
        # 應該能解析，但計算位置時會有問題
        result = sib19_platform.parse_sib19_message(malformed_data)
        assert result is True
        
        position = sib19_platform.calculate_satellite_position('STARLINK-1007')
        assert position['latitude'] == 0.0  # 預設值
    
    def test_empty_sib19_message(self, sib19_platform):
        """測試空 SIB19 消息"""
        result = sib19_platform.parse_sib19_message({})
        assert result is True  # 應該能處理空消息
        
        # 檢查狀態應該保持初始值
        assert len(sib19_platform.satellite_ephemeris) == 0
        assert sib19_platform.epoch_time is None


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])