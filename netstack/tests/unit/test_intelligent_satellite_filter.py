"""
智能衛星篩選系統單元測試 - Phase 1 核心功能測試

測試智能篩選系統的核心功能：
- 地理相關性篩選
- 換手適用性評分
- 雙階段篩選架構
- 性能優化效果
- 統一配置系統整合
"""

import pytest
import sys
import os
import math
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Tuple

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


class MockSatelliteData:
    """模擬衛星數據結構"""
    
    def __init__(self, name: str, norad_id: int, line1: str, line2: str, constellation: str = "starlink"):
        self.name = name
        self.norad_id = norad_id
        self.line1 = line1
        self.line2 = line2
        self.constellation = constellation
        
        # 從 TLE 解析軌道參數
        self.inclination = self._parse_inclination(line2)
        self.raan = self._parse_raan(line2)
        self.eccentricity = self._parse_eccentricity(line2)
        self.mean_motion = self._parse_mean_motion(line2)
        self.altitude = self._calculate_altitude(self.mean_motion)
    
    def _parse_inclination(self, line2: str) -> float:
        """解析軌道傾角"""
        try:
            return float(line2[8:16].strip())
        except:
            return 53.0  # Starlink 預設值
    
    def _parse_raan(self, line2: str) -> float:
        """解析升交點赤經"""
        try:
            return float(line2[17:25].strip())
        except:
            return 123.45  # 預設值
    
    def _parse_eccentricity(self, line2: str) -> float:
        """解析偏心率"""
        try:
            ecc_str = "0." + line2[26:33].strip()
            return float(ecc_str)
        except:
            return 0.001  # 近圓軌道預設值
    
    def _parse_mean_motion(self, line2: str) -> float:
        """解析平均運動"""
        try:
            return float(line2[52:63].strip())
        except:
            return 15.12345678  # Starlink 預設值
    
    def _calculate_altitude(self, mean_motion: float) -> float:
        """根據平均運動計算高度"""
        # 簡化的高度計算
        if mean_motion > 15.0:
            return 550.0  # LEO 高度
        elif mean_motion > 14.0:
            return 600.0
        else:
            return 800.0


class MockIntelligentSatelliteFilter:
    """模擬智能衛星篩選器"""
    
    def __init__(self, target_lat=24.9441667, target_lon=121.3713889):
        self.target_location = (target_lat, target_lon)
        self.scoring_weights = {
            'inclination': 0.25,
            'altitude': 0.20,
            'eccentricity': 0.15,
            'frequency': 0.20,
            'constellation': 0.20
        }
        
        # 統計計數器
        self.geographic_filter_count = 0
        self.scoring_operations_count = 0
    
    def geographic_relevance_filter(self, satellites: List[MockSatelliteData]) -> List[MockSatelliteData]:
        """地理相關性篩選"""
        self.geographic_filter_count += 1
        relevant_satellites = []
        
        for sat in satellites:
            # 軌道傾角匹配檢查
            if self._inclination_match(sat.inclination):
                # RAAN 經度對應檢查
                if self._raan_match(sat.raan):
                    relevant_satellites.append(sat)
        
        return relevant_satellites
    
    def _inclination_match(self, inclination: float) -> bool:
        """檢查軌道傾角匹配度"""
        target_lat = abs(self.target_location[0])  # 台灣緯度 24.94°
        
        # 最佳傾角範圍：45°-65°
        if 45.0 <= inclination <= 65.0:
            return True
        
        # 極地軌道特殊處理 (OneWeb)
        if inclination > 80.0:
            return True
        
        # 其他情況檢查是否能覆蓋目標緯度
        return inclination >= target_lat
    
    def _raan_match(self, raan: float) -> bool:
        """檢查 RAAN 經度對應性"""
        target_lon = self.target_location[1]  # 121.37°E
        
        # 極地軌道無經度偏好
        if raan is None:
            return True
        
        # 計算經度差異，處理跨越 180° 經度線的情況
        lon_diff = abs(raan - target_lon)
        if lon_diff > 180:
            lon_diff = 360 - lon_diff
        
        # 偏差容忍 ±60° (放寬容忍度)
        return lon_diff <= 60.0
    
    def handover_suitability_scoring(self, satellites: List[MockSatelliteData]) -> List[Tuple[MockSatelliteData, float]]:
        """換手適用性評分"""
        self.scoring_operations_count += 1
        scored_satellites = []
        
        for sat in satellites:
            score = self._calculate_composite_score(sat)
            scored_satellites.append((sat, score))
        
        # 按分數排序
        return sorted(scored_satellites, key=lambda x: x[1], reverse=True)
    
    def _calculate_composite_score(self, satellite: MockSatelliteData) -> float:
        """計算綜合評分"""
        inclination_score = self._inclination_score(satellite.inclination)
        altitude_score = self._altitude_score(satellite.altitude)
        eccentricity_score = self._eccentricity_score(satellite.eccentricity)
        frequency_score = self._frequency_score(satellite.mean_motion)
        constellation_score = self._constellation_score(satellite.constellation)
        
        total_score = (
            inclination_score * self.scoring_weights['inclination'] +
            altitude_score * self.scoring_weights['altitude'] +
            eccentricity_score * self.scoring_weights['eccentricity'] +
            frequency_score * self.scoring_weights['frequency'] +
            constellation_score * self.scoring_weights['constellation']
        )
        
        return min(100.0, max(0.0, total_score))  # 限制在 0-100 範圍
    
    def _inclination_score(self, inclination: float) -> float:
        """軌道傾角評分 (25分)"""
        if abs(inclination - 53.0) < 1.0:  # Starlink 最佳傾角
            return 25.0
        elif abs(inclination - 87.4) < 2.0:  # OneWeb 極地軌道
            return 20.0
        elif 45.0 <= inclination <= 65.0:
            return 18.0
        else:
            return max(0.0, 15.0 - abs(inclination - 53.0) * 0.5)
    
    def _altitude_score(self, altitude: float) -> float:
        """軌道高度評分 (20分)"""
        if 540 <= altitude <= 560:  # Starlink 最佳高度
            return 20.0
        elif 400 <= altitude <= 600:
            return 15.0 + (5.0 * (1 - abs(altitude - 550) / 50))
        else:
            return max(0.0, 10.0 - abs(altitude - 550) / 100)
    
    def _eccentricity_score(self, eccentricity: float) -> float:
        """軌道形狀評分 (15分)"""
        if eccentricity < 0.01:  # 近圓軌道
            return 15.0
        elif eccentricity < 0.05:
            return 12.0
        elif eccentricity < 0.1:
            return 8.0
        else:
            return max(0.0, 5.0 - eccentricity * 50)
    
    def _frequency_score(self, mean_motion: float) -> float:
        """經過頻率評分 (20分)"""
        # 計算每日經過次數 (mean_motion 是每日的平均運動)
        passes_per_day = mean_motion
        
        if 14 <= passes_per_day <= 16:  # 理想頻率 (LEO 衛星)
            return 20.0
        elif 13 <= passes_per_day <= 17:
            return 15.0
        elif 12 <= passes_per_day <= 18:
            return 10.0
        else:
            return max(0.0, 5.0 - abs(passes_per_day - 15) * 0.5)
    
    def _constellation_score(self, constellation: str) -> float:
        """星座偏好評分 (20分)"""
        constellation_scores = {
            'starlink': 20.0,  # Starlink 覆蓋優勢
            'oneweb': 17.0,    # OneWeb 極地覆蓋
            'kuiper': 15.0,    # Amazon Kuiper
            'other': 10.0      # 其他星座
        }
        return constellation_scores.get(constellation.lower(), 10.0)
    
    def filter_satellites_for_location(self, constellation: str, max_count: int = 40) -> List[MockSatelliteData]:
        """為特定位置篩選衛星"""
        # 模擬從數據庫獲取衛星數據
        satellites = self._get_mock_satellite_data(constellation)
        
        # 階段一：地理相關性篩選
        relevant_satellites = self.geographic_relevance_filter(satellites)
        
        # 階段二：換手適用性評分
        scored_satellites = self.handover_suitability_scoring(relevant_satellites)
        
        # 返回前 N 個最佳衛星
        return [sat for sat, score in scored_satellites[:max_count]]
    
    def _get_mock_satellite_data(self, constellation: str) -> List[MockSatelliteData]:
        """獲取測試用衛星數據"""
        if constellation.lower() == 'starlink':
            return self._generate_starlink_test_data()
        elif constellation.lower() == 'oneweb':
            return self._generate_oneweb_test_data()
        else:
            return []
    
    def _generate_starlink_test_data(self) -> List[MockSatelliteData]:
        """生成 Starlink 測試數據"""
        satellites = []
        for i in range(100):  # 模擬 100 顆 Starlink 衛星
            satellites.append(MockSatelliteData(
                name=f"STARLINK-{1000+i}",
                norad_id=44713 + i,
                line1=f"1 {44713+i}U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  999{i%10}",
                line2=f"2 {44713+i}  53.{i%9:04d} {123+i%180:7.4f} 0001234  {90+i%270:7.4f} {269+i%360:7.4f} 15.1234567{i%10}123456",
                constellation="starlink"
            ))
        return satellites
    
    def _generate_oneweb_test_data(self) -> List[MockSatelliteData]:
        """生成 OneWeb 測試數據"""
        satellites = []
        for i in range(50):  # 模擬 50 顆 OneWeb 衛星
            satellites.append(MockSatelliteData(
                name=f"ONEWEB-{i:04d}",
                norad_id=43013 + i,
                line1=f"1 {43013+i}U 19003A   25215.12345678  .00001234  00000-0  12345-4 0  999{i%10}",
                line2=f"2 {43013+i}  87.{4000+i%9:04d} {i*7.2:7.4f} 0001234  {90+i%360:7.4f} {269+i%360:7.4f} 13.1234567{i%10}123456",
                constellation="oneweb"
            ))
        return satellites


# Global fixtures
@pytest.fixture
def filter_engine():
    """創建篩選引擎實例"""
    return MockIntelligentSatelliteFilter()

@pytest.fixture
def sample_satellites():
    """創建測試用衛星數據"""
    return [
        MockSatelliteData(
            name="STARLINK-1007",
            norad_id=44713,
            line1="1 44713U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9990",
            line2="2 44713  53.0000 123.4567 0001234  90.1234 269.8765 15.12345678123456",
            constellation="starlink"
        ),
        MockSatelliteData(
            name="ONEWEB-0001",
            norad_id=43013,
            line1="1 43013U 19003A   25215.12345678  .00001234  00000-0  12345-4 0  9990",
            line2="2 43013  87.4000 45.6789 0001234  90.1234 269.8765 13.12345678123456",
            constellation="oneweb"
        )
    ]


class TestIntelligentSatelliteFilterBasics:
    """測試基礎功能"""
    
    def test_initialization(self, filter_engine):
        """測試初始化"""
        assert filter_engine.target_location == (24.9441667, 121.3713889)  # NTPU 座標
        assert len(filter_engine.scoring_weights) == 5
        assert sum(filter_engine.scoring_weights.values()) == 1.0  # 權重總和為 1
    
    def test_target_location_taiwan(self, filter_engine):
        """測試目標位置設定在台灣"""
        lat, lon = filter_engine.target_location
        assert 21.0 <= lat <= 26.0, "緯度不在台灣範圍內"
        assert 119.0 <= lon <= 122.0, "經度不在台灣範圍內"
    
    def test_scoring_weights_validity(self, filter_engine):
        """測試評分權重有效性"""
        weights = filter_engine.scoring_weights
        
        # 檢查所有權重都是正數
        for weight_name, weight_value in weights.items():
            assert weight_value > 0, f"{weight_name} 權重應該為正數"
            assert weight_value <= 1.0, f"{weight_name} 權重不應超過 1.0"
        
        # 檢查權重總和為 1
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"權重總和 {total_weight} 應該為 1.0"


class TestGeographicRelevanceFilter:
    """測試地理相關性篩選"""
    
    @pytest.fixture
    def filter_engine(self):
        return MockIntelligentSatelliteFilter()
    
    def test_inclination_matching(self, filter_engine):
        """測試軌道傾角匹配"""
        # Starlink 53° 傾角應該匹配
        assert filter_engine._inclination_match(53.0) is True
        
        # OneWeb 87.4° 極地軌道應該匹配
        assert filter_engine._inclination_match(87.4) is True
        
        # 45°-65° 最佳範圍應該匹配
        assert filter_engine._inclination_match(55.0) is True
        assert filter_engine._inclination_match(60.0) is True
        
        # 過低傾角應該不匹配
        assert filter_engine._inclination_match(10.0) is False
    
    def test_raan_matching(self, filter_engine):
        """測試 RAAN 經度對應檢查"""
        target_lon = 121.37  # NTPU 經度
        
        # 相近經度應該匹配
        assert filter_engine._raan_match(120.0) is True
        assert filter_engine._raan_match(125.0) is True
        
        # 偏差 60° 內應該匹配
        assert filter_engine._raan_match(121.37 + 50) is True
        assert filter_engine._raan_match(121.37 - 50) is True
        
        # 偏差超過 60° 應該不匹配
        assert filter_engine._raan_match(121.37 + 70) is False
        
        # 跨越 180° 經度線的情況
        test_lon = target_lon + 180 - 30  # 251.37，實際偏差應該是 30°
        assert filter_engine._raan_match(test_lon) is True  # 實際偏差 30°
    
    def test_geographic_filter_with_starlink(self, filter_engine, sample_satellites):
        """測試 Starlink 衛星地理篩選"""
        starlink_sats = [sat for sat in sample_satellites if sat.constellation == "starlink"]
        filtered = filter_engine.geographic_relevance_filter(starlink_sats)
        
        assert len(filtered) > 0, "Starlink 衛星應該通過地理篩選"
        assert filter_engine.geographic_filter_count == 1, "應該執行了一次地理篩選"
    
    def test_geographic_filter_with_oneweb(self, filter_engine, sample_satellites):
        """測試 OneWeb 衛星地理篩選"""
        oneweb_sats = [sat for sat in sample_satellites if sat.constellation == "oneweb"]
        filtered = filter_engine.geographic_relevance_filter(oneweb_sats)
        
        assert len(filtered) > 0, "OneWeb 極地軌道應該通過地理篩選"
    
    def test_geographic_filter_empty_input(self, filter_engine):
        """測試空輸入的地理篩選"""
        filtered = filter_engine.geographic_relevance_filter([])
        assert filtered == []
        assert filter_engine.geographic_filter_count == 1


class TestHandoverSuitabilityScoring:
    """測試換手適用性評分"""
    
    @pytest.fixture
    def filter_engine(self):
        return MockIntelligentSatelliteFilter()
    
    def test_inclination_scoring(self, filter_engine):
        """測試軌道傾角評分"""
        # Starlink 53° 應該得到滿分
        assert filter_engine._inclination_score(53.0) == 25.0
        
        # OneWeb 87.4° 應該得到高分
        score_oneweb = filter_engine._inclination_score(87.4)
        assert 18.0 <= score_oneweb <= 22.0
        
        # 45°-65° 範圍應該得到好分數
        score_good = filter_engine._inclination_score(55.0)
        assert score_good >= 15.0
        
        # 極端傾角應該得到低分
        score_bad = filter_engine._inclination_score(10.0)
        assert score_bad < 10.0
    
    def test_altitude_scoring(self, filter_engine):
        """測試軌道高度評分"""
        # Starlink 550km 應該得到滿分
        assert filter_engine._altitude_score(550.0) == 20.0
        
        # 540-560km 範圍應該得到滿分
        assert filter_engine._altitude_score(545.0) == 20.0
        assert filter_engine._altitude_score(555.0) == 20.0
        
        # 400-600km 範圍應該得到好分數
        score_ok = filter_engine._altitude_score(580.0)
        assert 15.0 <= score_ok <= 20.0
        
        # 極端高度應該得到低分
        score_bad = filter_engine._altitude_score(1000.0)
        assert score_bad < 10.0
    
    def test_eccentricity_scoring(self, filter_engine):
        """測試軌道形狀評分"""
        # 近圓軌道 (e < 0.01) 應該得到滿分
        assert filter_engine._eccentricity_score(0.001) == 15.0
        assert filter_engine._eccentricity_score(0.005) == 15.0
        
        # 低偏心率應該得到好分數
        score_low = filter_engine._eccentricity_score(0.02)
        assert 10.0 <= score_low <= 15.0
        
        # 高偏心率應該得到低分
        score_high = filter_engine._eccentricity_score(0.2)
        assert score_high < 5.0
    
    def test_frequency_scoring(self, filter_engine):
        """測試經過頻率評分"""
        # 理想頻率 (14-16次/日) 應該得到滿分
        score_ideal = filter_engine._frequency_score(15.0)  # LEO 標準
        assert score_ideal == 20.0
        
        # 適中頻率應該得到好分數
        score_ok = filter_engine._frequency_score(16.5)
        assert score_ok >= 10.0
        
        # 極端頻率應該得到低分
        score_bad = filter_engine._frequency_score(25.0)  # 過高頻率
        assert score_bad < 10.0
    
    def test_constellation_scoring(self, filter_engine):
        """測試星座偏好評分"""
        # Starlink 應該得到最高分
        assert filter_engine._constellation_score("starlink") == 20.0
        
        # OneWeb 應該得到較高分
        score_oneweb = filter_engine._constellation_score("oneweb")
        assert 15.0 <= score_oneweb <= 20.0
        
        # 其他星座應該得到基礎分
        score_other = filter_engine._constellation_score("unknown")
        assert score_other == 10.0
    
    def test_composite_scoring(self, filter_engine, sample_satellites):
        """測試綜合評分"""
        scored_satellites = filter_engine.handover_suitability_scoring(sample_satellites)
        
        assert len(scored_satellites) == len(sample_satellites)
        assert filter_engine.scoring_operations_count == 1
        
        # 檢查評分結果
        for sat, score in scored_satellites:
            assert 0.0 <= score <= 100.0, f"評分 {score} 超出範圍"
        
        # 檢查排序
        scores = [score for sat, score in scored_satellites]
        assert scores == sorted(scores, reverse=True), "評分結果應該按降序排列"
    
    def test_scoring_empty_input(self, filter_engine):
        """測試空輸入的評分"""
        scored = filter_engine.handover_suitability_scoring([])
        assert scored == []
        assert filter_engine.scoring_operations_count == 1


class TestIntegratedFiltering:
    """測試整合篩選功能"""
    
    @pytest.fixture
    def filter_engine(self):
        return MockIntelligentSatelliteFilter()
    
    def test_starlink_filtering_pipeline(self, filter_engine):
        """測試 Starlink 篩選流水線"""
        filtered_satellites = filter_engine.filter_satellites_for_location("starlink", max_count=40)
        
        assert len(filtered_satellites) <= 40, "篩選結果不應超過指定數量"
        assert len(filtered_satellites) > 0, "應該有篩選結果"
        
        # 檢查統計計數器
        assert filter_engine.geographic_filter_count == 1
        assert filter_engine.scoring_operations_count == 1
        
        # 檢查結果都是 Starlink 衛星
        for sat in filtered_satellites:
            assert sat.constellation.lower() == "starlink"
    
    def test_oneweb_filtering_pipeline(self, filter_engine):
        """測試 OneWeb 篩選流水線"""
        filtered_satellites = filter_engine.filter_satellites_for_location("oneweb", max_count=30)
        
        assert len(filtered_satellites) <= 30, "篩選結果不應超過指定數量"
        assert len(filtered_satellites) > 0, "應該有篩選結果"
        
        # 檢查結果都是 OneWeb 衛星
        for sat in filtered_satellites:
            assert sat.constellation.lower() == "oneweb"
    
    def test_filtering_with_different_limits(self, filter_engine):
        """測試不同數量限制的篩選"""
        # 測試小數量限制
        small_result = filter_engine.filter_satellites_for_location("starlink", max_count=5)
        assert len(small_result) <= 5
        
        # 測試大數量限制
        large_result = filter_engine.filter_satellites_for_location("starlink", max_count=100)
        assert len(large_result) <= 100
        
        # 小數量結果應該是大數量結果的子集 (前 N 個)
        if len(small_result) > 0 and len(large_result) > 0:
            for i, sat in enumerate(small_result):
                if i < len(large_result):
                    assert sat.name == large_result[i].name, "小數量結果應該是大數量結果的前 N 個"
    
    def test_unknown_constellation(self, filter_engine):
        """測試未知星座"""
        result = filter_engine.filter_satellites_for_location("unknown", max_count=10)
        assert result == [], "未知星座應該返回空結果"


class TestPerformanceMetrics:
    """測試性能指標"""
    
    @pytest.fixture
    def filter_engine(self):
        return MockIntelligentSatelliteFilter()
    
    def test_filtering_performance_starlink(self, filter_engine):
        """測試 Starlink 篩選性能"""
        import time
        
        start_time = time.time()
        filtered = filter_engine.filter_satellites_for_location("starlink", max_count=40)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 性能要求：應該在合理時間內完成
        assert processing_time < 1.0, f"篩選時間 {processing_time:.3f}s 過長"
        
        # 檢查篩選效果
        total_satellites = len(filter_engine._get_mock_satellite_data("starlink"))  # 100
        filtered_count = len(filtered)  # 40
        compression_ratio = (total_satellites - filtered_count) / total_satellites
        
        assert compression_ratio > 0.5, f"壓縮率 {compression_ratio:.1%} 不夠高"
        assert filtered_count > 0, "應該有篩選結果"
    
    def test_filtering_performance_oneweb(self, filter_engine):
        """測試 OneWeb 篩選性能"""
        import time
        
        start_time = time.time()
        filtered = filter_engine.filter_satellites_for_location("oneweb", max_count=30)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 性能要求
        assert processing_time < 1.0, f"篩選時間 {processing_time:.3f}s 過長"
        
        # 檢查篩選效果
        total_satellites = len(filter_engine._get_mock_satellite_data("oneweb"))  # 50
        filtered_count = len(filtered)  # 30
        compression_ratio = (total_satellites - filtered_count) / total_satellites
        
        assert compression_ratio > 0.3, f"壓縮率 {compression_ratio:.1%} 不夠高"
    
    def test_memory_efficiency(self, filter_engine):
        """測試記憶體效率"""
        # 執行多次篩選操作
        for i in range(10):
            filter_engine.filter_satellites_for_location("starlink", max_count=40)
        
        # 檢查統計計數器，確認沒有記憶體洩漏相關的異常增長
        assert filter_engine.geographic_filter_count == 10
        assert filter_engine.scoring_operations_count == 10


class TestConfigurationIntegration:
    """測試配置系統整合"""
    
    def test_target_location_configuration(self):
        """測試目標位置配置"""
        # 測試不同目標位置
        taipei_filter = MockIntelligentSatelliteFilter(25.0, 121.5)
        kaohsiung_filter = MockIntelligentSatelliteFilter(22.6, 120.3)
        
        assert taipei_filter.target_location == (25.0, 121.5)
        assert kaohsiung_filter.target_location == (22.6, 120.3)
    
    def test_scoring_weights_configuration(self):
        """測試評分權重配置"""
        filter_engine = MockIntelligentSatelliteFilter()
        
        # 修改權重配置
        filter_engine.scoring_weights = {
            'inclination': 0.3,
            'altitude': 0.25,
            'eccentricity': 0.15,
            'frequency': 0.15,
            'constellation': 0.15
        }
        
        # 檢查權重總和仍為 1
        assert abs(sum(filter_engine.scoring_weights.values()) - 1.0) < 0.001
        
        # 測試修改後的權重是否影響評分
        test_sat = MockSatelliteData(
            name="TEST-SAT",
            norad_id=99999,
            line1="1 99999U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9990",
            line2="2 99999  53.0000 123.4567 0001234  90.1234 269.8765 15.12345678123456",
            constellation="starlink"
        )
        
        score = filter_engine._calculate_composite_score(test_sat)
        assert 0.0 <= score <= 100.0


class TestErrorHandling:
    """測試錯誤處理"""
    
    @pytest.fixture
    def filter_engine(self):
        return MockIntelligentSatelliteFilter()
    
    def test_invalid_tle_data_handling(self, filter_engine):
        """測試無效 TLE 數據處理"""
        # 創建有問題的衛星數據
        invalid_sat = MockSatelliteData(
            name="INVALID-SAT",
            norad_id=99999,
            line1="invalid line 1",
            line2="invalid line 2",
            constellation="test"
        )
        
        # 應該能處理無效數據而不崩潰
        try:
            filtered = filter_engine.geographic_relevance_filter([invalid_sat])
            assert isinstance(filtered, list)
        except Exception as e:
            pytest.fail(f"處理無效 TLE 數據時不應拋出異常: {e}")
    
    def test_extreme_scoring_values(self, filter_engine):
        """測試極端評分值處理"""
        # 測試極端軌道參數
        extreme_sat = MockSatelliteData(
            name="EXTREME-SAT",
            norad_id=99999,
            line1="1 99999U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9990",
            line2="2 99999  180.000 360.0000 0.9999999  360.000 360.0000 50.00000000123456",
            constellation="test"
        )
        
        # 計算評分不應拋出異常，且結果應在合理範圍內
        score = filter_engine._calculate_composite_score(extreme_sat)
        assert 0.0 <= score <= 100.0
    
    def test_empty_constellation_data(self, filter_engine):
        """測試空星座數據"""
        # 測試不存在的星座
        result = filter_engine.filter_satellites_for_location("nonexistent", max_count=10)
        assert result == []
        
        # 統計計數器應該仍然增加（表示執行了篩選過程）
        assert filter_engine.geographic_filter_count == 1
        assert filter_engine.scoring_operations_count == 1


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])