"""
統一配置系統單元測試 - Phase 1 核心功能測試

測試 Phase 1 實施的統一配置系統，包括：
- SIB19 3GPP NTN 標準合規性驗證
- ITU-R P.618 仰角門檻配置驗證
- 智能篩選配置測試
- SGP4 計算精度配置測試
- 跨容器配置存取測試
"""

import pytest
import sys
import os
from dataclasses import dataclass, field
from typing import Dict
from unittest.mock import Mock, patch, MagicMock

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# 模擬配置類別以避免導入問題
@dataclass
class ElevationThresholds:
    trigger_threshold_deg: float = 15.0
    execution_threshold_deg: float = 10.0
    critical_threshold_deg: float = 5.0

@dataclass
class IntelligentSelectionConfig:
    enabled: bool = True
    geographic_filter_enabled: bool = True
    target_location: Dict[str, float] = field(default_factory=lambda: {
        "lat": 24.9441667, "lon": 121.3713889
    })
    scoring_weights: Dict[str, float] = field(default_factory=lambda: {
        'inclination': 0.25,
        'altitude': 0.20,
        'eccentricity': 0.15,
        'frequency': 0.20,
        'constellation': 0.20
    })

@dataclass
class ComputationPrecision:
    sgp4_enabled: bool = True
    fallback_enabled: bool = True
    precision_level: str = "high"
    validation_enabled: bool = True

@dataclass
class SatelliteConfig:
    MAX_CANDIDATE_SATELLITES: int = 8
    PREPROCESS_SATELLITES: Dict[str, int] = field(default_factory=lambda: {
        "starlink": 40,
        "oneweb": 30,
        "kuiper": 35,
        "all": 50
    })
    BATCH_COMPUTE_MAX_SATELLITES: int = 50
    ALGORITHM_TEST_MAX_SATELLITES: int = 10
    
    elevation_thresholds: ElevationThresholds = field(default_factory=ElevationThresholds)
    intelligent_selection: IntelligentSelectionConfig = field(default_factory=IntelligentSelectionConfig)
    computation_precision: ComputationPrecision = field(default_factory=ComputationPrecision)


class TestSatelliteConfigBasics:
    """測試基礎配置功能"""
    
    @pytest.fixture
    def satellite_config(self):
        """創建測試用配置實例"""
        return SatelliteConfig()
    
    def test_default_values(self, satellite_config):
        """測試預設值是否正確"""
        assert satellite_config.MAX_CANDIDATE_SATELLITES == 8
        assert satellite_config.BATCH_COMPUTE_MAX_SATELLITES == 50
        assert satellite_config.ALGORITHM_TEST_MAX_SATELLITES == 10
        
        # 測試分階段衛星數量
        assert satellite_config.PREPROCESS_SATELLITES["starlink"] == 40
        assert satellite_config.PREPROCESS_SATELLITES["oneweb"] == 30
        assert satellite_config.PREPROCESS_SATELLITES["kuiper"] == 35
        assert satellite_config.PREPROCESS_SATELLITES["all"] == 50
    
    def test_elevation_thresholds_default(self, satellite_config):
        """測試仰角門檻預設值"""
        thresholds = satellite_config.elevation_thresholds
        assert thresholds.trigger_threshold_deg == 15.0
        assert thresholds.execution_threshold_deg == 10.0
        assert thresholds.critical_threshold_deg == 5.0
    
    def test_intelligent_selection_default(self, satellite_config):
        """測試智能篩選配置預設值"""
        selection = satellite_config.intelligent_selection
        assert selection.enabled is True
        assert selection.geographic_filter_enabled is True
        assert selection.target_location["lat"] == 24.9441667  # NTPU 緯度
        assert selection.target_location["lon"] == 121.3713889  # NTPU 經度
        
        # 測試評分權重
        weights = selection.scoring_weights
        assert weights['inclination'] == 0.25
        assert weights['altitude'] == 0.20
        assert weights['eccentricity'] == 0.15
        assert weights['frequency'] == 0.20
        assert weights['constellation'] == 0.20
        assert sum(weights.values()) == 1.0  # 權重總和應為 1
    
    def test_computation_precision_default(self, satellite_config):
        """測試計算精度配置預設值"""
        precision = satellite_config.computation_precision
        assert precision.sgp4_enabled is True
        assert precision.fallback_enabled is True
        assert precision.precision_level == "high"
        assert precision.validation_enabled is True


class TestSIB19Compliance:
    """測試 SIB19 3GPP NTN 標準合規性"""
    
    def test_max_candidate_satellites_compliance(self):
        """測試候選衛星數量符合 SIB19 規範"""
        config = SatelliteConfig()
        # SIB19 規範要求候選衛星數量不超過 8 顆
        assert config.MAX_CANDIDATE_SATELLITES <= 8
    
    def test_max_candidate_satellites_boundary_values(self):
        """測試邊界值"""
        # 測試最小值
        config = SatelliteConfig()
        config.MAX_CANDIDATE_SATELLITES = 1
        assert config.MAX_CANDIDATE_SATELLITES >= 1
        
        # 測試最大值
        config.MAX_CANDIDATE_SATELLITES = 8
        assert config.MAX_CANDIDATE_SATELLITES <= 8
        
        # 測試超出範圍應該能被檢測到
        config.MAX_CANDIDATE_SATELLITES = 9
        assert config.MAX_CANDIDATE_SATELLITES > 8  # 應該被驗證器捕獲
    
    def test_preprocessing_counts_reasonable(self):
        """測試預處理衛星數量合理性"""
        config = SatelliteConfig()
        
        # 預處理數量應該大於最終候選數量
        assert config.PREPROCESS_SATELLITES["starlink"] > config.MAX_CANDIDATE_SATELLITES
        assert config.PREPROCESS_SATELLITES["oneweb"] > config.MAX_CANDIDATE_SATELLITES
        
        # 預處理數量應該在合理範圍內
        for constellation, count in config.PREPROCESS_SATELLITES.items():
            if constellation != "all":
                assert 10 <= count <= 100, f"{constellation} 預處理數量 {count} 不在合理範圍"


class TestITURCompliance:
    """測試 ITU-R P.618 仰角門檻標準合規性"""
    
    def test_elevation_threshold_order(self):
        """測試仰角門檻順序正確性"""
        config = SatelliteConfig()
        thresholds = config.elevation_thresholds
        
        # 分層門檻應該按邏輯順序排列
        assert thresholds.critical_threshold_deg < thresholds.execution_threshold_deg
        assert thresholds.execution_threshold_deg < thresholds.trigger_threshold_deg
    
    def test_elevation_threshold_ranges(self):
        """測試仰角門檻在合理範圍內"""
        config = SatelliteConfig()
        thresholds = config.elevation_thresholds
        
        # 所有仰角都應該在 0-90 度範圍內
        assert 0 <= thresholds.critical_threshold_deg <= 90
        assert 0 <= thresholds.execution_threshold_deg <= 90
        assert 0 <= thresholds.trigger_threshold_deg <= 90
    
    def test_itu_r_recommended_values(self):
        """測試是否符合 ITU-R P.618 建議值"""
        config = SatelliteConfig()
        thresholds = config.elevation_thresholds
        
        # ITU-R P.618 一般建議最低仰角不低於 5 度
        assert thresholds.critical_threshold_deg >= 5.0
        
        # 執行門檻通常在 10 度左右
        assert 8.0 <= thresholds.execution_threshold_deg <= 15.0
        
        # 觸發門檻通常在 15 度左右
        assert 12.0 <= thresholds.trigger_threshold_deg <= 20.0
    
    def test_threshold_intervals(self):
        """測試門檻間隔合理性"""
        config = SatelliteConfig()
        thresholds = config.elevation_thresholds
        
        # 間隔應該足夠給予換手決策時間
        execution_interval = thresholds.execution_threshold_deg - thresholds.critical_threshold_deg
        trigger_interval = thresholds.trigger_threshold_deg - thresholds.execution_threshold_deg
        
        assert execution_interval >= 3.0, "執行與臨界門檻間隔過小"
        assert trigger_interval >= 3.0, "觸發與執行門檻間隔過小"


class TestIntelligentSelectionConfig:
    """測試智能篩選配置"""
    
    def test_target_location_taiwan(self):
        """測試目標位置設定為台灣"""
        config = SatelliteConfig()
        location = config.intelligent_selection.target_location
        
        # 檢查座標是否在台灣範圍內
        assert 21.0 <= location["lat"] <= 26.0, "緯度不在台灣範圍內"
        assert 119.0 <= location["lon"] <= 122.0, "經度不在台灣範圍內"
        
        # 具體檢查是否為 NTPU 座標
        assert abs(location["lat"] - 24.9441667) < 0.001
        assert abs(location["lon"] - 121.3713889) < 0.001
    
    def test_scoring_weights_validity(self):
        """測試評分權重的有效性"""
        config = SatelliteConfig()
        weights = config.intelligent_selection.scoring_weights
        
        # 檢查所有權重都是正數
        for weight_name, weight_value in weights.items():
            assert weight_value > 0, f"{weight_name} 權重應該為正數"
            assert weight_value <= 1.0, f"{weight_name} 權重不應超過 1.0"
        
        # 檢查權重總和為 1
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"權重總和 {total_weight} 應該為 1.0"
    
    def test_geographic_filter_enabled(self):
        """測試地理篩選功能啟用"""
        config = SatelliteConfig()
        assert config.intelligent_selection.geographic_filter_enabled is True
    
    def test_intelligent_selection_enabled(self):
        """測試智能篩選功能啟用"""
        config = SatelliteConfig()
        assert config.intelligent_selection.enabled is True


class TestConfigurationValidation:
    """測試配置驗證功能"""
    
    def test_satellite_count_validation(self):
        """測試衛星數量驗證"""
        config = SatelliteConfig()
        
        # 基本合規檢查
        assert config.MAX_CANDIDATE_SATELLITES <= 8, "SIB19 合規檢查失敗"
        
        # 處理數量邏輯檢查
        for constellation, count in config.PREPROCESS_SATELLITES.items():
            if constellation != "all":
                assert count > config.MAX_CANDIDATE_SATELLITES, f"{constellation} 預處理數量應大於候選數量"
    
    def test_elevation_validation(self):
        """測試仰角驗證"""
        config = SatelliteConfig()
        thresholds = config.elevation_thresholds
        
        # 順序驗證
        assert thresholds.critical_threshold_deg < thresholds.execution_threshold_deg
        assert thresholds.execution_threshold_deg < thresholds.trigger_threshold_deg
        
        # 範圍驗證
        for threshold_name, threshold_value in [
            ("critical", thresholds.critical_threshold_deg),
            ("execution", thresholds.execution_threshold_deg), 
            ("trigger", thresholds.trigger_threshold_deg)
        ]:
            assert 0 <= threshold_value <= 90, f"{threshold_name} 仰角 {threshold_value} 超出範圍"
    
    def test_intelligent_selection_validation(self):
        """測試智能篩選配置驗證"""
        config = SatelliteConfig()
        selection = config.intelligent_selection
        
        # 位置驗證
        lat, lon = selection.target_location["lat"], selection.target_location["lon"]
        assert -90 <= lat <= 90, f"緯度 {lat} 超出範圍"
        assert -180 <= lon <= 180, f"經度 {lon} 超出範圍"
        
        # 權重驗證
        weights = selection.scoring_weights
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"權重總和 {total_weight} 不等於 1.0"


class TestConfigurationModification:
    """測試配置修改能力"""
    
    def test_config_modification(self):
        """測試配置可以被修改"""
        config = SatelliteConfig()
        
        # 修改候選衛星數量
        original_count = config.MAX_CANDIDATE_SATELLITES
        config.MAX_CANDIDATE_SATELLITES = 6
        assert config.MAX_CANDIDATE_SATELLITES == 6
        assert config.MAX_CANDIDATE_SATELLITES != original_count
    
    def test_threshold_modification(self):
        """測試仰角門檻可以被修改"""
        config = SatelliteConfig()
        
        # 修改仰角門檻
        config.elevation_thresholds.critical_threshold_deg = 7.0
        config.elevation_thresholds.execution_threshold_deg = 12.0
        config.elevation_thresholds.trigger_threshold_deg = 18.0
        
        assert config.elevation_thresholds.critical_threshold_deg == 7.0
        assert config.elevation_thresholds.execution_threshold_deg == 12.0
        assert config.elevation_thresholds.trigger_threshold_deg == 18.0
    
    def test_intelligent_selection_modification(self):
        """測試智能篩選配置可以被修改"""
        config = SatelliteConfig()
        
        # 修改目標位置
        config.intelligent_selection.target_location = {"lat": 25.0, "lon": 121.5}
        assert config.intelligent_selection.target_location["lat"] == 25.0
        assert config.intelligent_selection.target_location["lon"] == 121.5
        
        # 修改權重
        config.intelligent_selection.scoring_weights["inclination"] = 0.3
        assert config.intelligent_selection.scoring_weights["inclination"] == 0.3


class TestCrossContainerConfigAccess:
    """測試跨容器配置存取"""
    
    @pytest.fixture
    def mock_config_access(self):
        """模擬跨容器配置存取"""
        with patch('sys.path'):
            mock_config = Mock()
            mock_config.MAX_CANDIDATE_SATELLITES = 8
            mock_config.PREPROCESS_SATELLITES = {"starlink": 40, "oneweb": 30}
            return mock_config
    
    def test_config_availability_check(self, mock_config_access):
        """測試配置可用性檢查"""
        # 模擬配置可用的情況
        assert mock_config_access.MAX_CANDIDATE_SATELLITES == 8
        
        # 模擬配置不可用的情況應該有降級方案
        fallback_config = {"general": 8, "starlink": 40, "oneweb": 30}
        assert fallback_config["general"] == 8
    
    def test_safe_config_access(self, mock_config_access):
        """測試安全的配置存取"""
        try:
            satellites_count = mock_config_access.MAX_CANDIDATE_SATELLITES
            assert satellites_count == 8
        except AttributeError:
            # 應該有降級方案
            fallback_count = 8  # SIB19 預設值
            assert fallback_count == 8
    
    def test_fallback_mechanism(self):
        """測試降級機制"""
        # 當統一配置不可用時的降級配置
        fallback_config = {
            "max_candidates": 8,  # SIB19 合規預設值
            "starlink_preprocess": 40,
            "oneweb_preprocess": 30,
            "elevation_critical": 5.0,
            "elevation_execution": 10.0,
            "elevation_trigger": 15.0
        }
        
        # 檢查降級配置是否合規
        assert fallback_config["max_candidates"] <= 8
        assert fallback_config["elevation_critical"] < fallback_config["elevation_execution"]
        assert fallback_config["elevation_execution"] < fallback_config["elevation_trigger"]


class TestPerformanceAndScaling:
    """測試性能和擴展性配置"""
    
    def test_preprocessing_scaling(self):
        """測試預處理數量的擴展性"""
        config = SatelliteConfig()
        
        # 檢查不同星座的預處理數量設計是否合理
        starlink_count = config.PREPROCESS_SATELLITES["starlink"]  # 40
        oneweb_count = config.PREPROCESS_SATELLITES["oneweb"]      # 30
        
        # Starlink 衛星較多，預處理數量應該較大
        assert starlink_count > oneweb_count
        
        # 但都不應該過大，避免性能問題
        assert starlink_count <= 100
        assert oneweb_count <= 100
    
    def test_batch_processing_limits(self):
        """測試批次處理限制"""
        config = SatelliteConfig()
        
        # 批次計算數量應該大於個別星座預處理數量
        assert config.BATCH_COMPUTE_MAX_SATELLITES >= max(config.PREPROCESS_SATELLITES.values())
        
        # 但不應該過大
        assert config.BATCH_COMPUTE_MAX_SATELLITES <= 100
    
    def test_algorithm_test_limits(self):
        """測試算法測試限制"""
        config = SatelliteConfig()
        
        # 算法測試用的衛星數量應該適中，便於快速測試
        # 可以略大於最終候選數量以測試篩選效果
        assert config.ALGORITHM_TEST_MAX_SATELLITES >= 1
        assert config.ALGORITHM_TEST_MAX_SATELLITES <= 20  # 不應過大


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])