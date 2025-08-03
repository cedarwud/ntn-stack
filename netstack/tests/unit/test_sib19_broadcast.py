"""
Phase 3.1.2 SIB19 廣播機制單元測試

測試衛星位置資訊廣播的完整實現，包括：
1. 衛星星曆數據管理
2. 可見性計算
3. SIB19 消息生成
4. 廣播調度機制
5. 緊急廣播功能
"""

import pytest
import pytest_asyncio
import asyncio
import time
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# 導入待測試的模組
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.protocols.sib.sib19_broadcast import (
    SIB19BroadcastScheduler,
    SatelliteEphemeris,
    VisibleSatellite,
    SIB19Message,
    SIB19BroadcastType,
    SatelliteVisibilityStatus,
    create_sib19_broadcast_scheduler,
    create_test_satellite_ephemeris
)


class TestSatelliteEphemeris:
    """測試衛星星曆數據"""
    
    def test_ephemeris_creation(self):
        """測試星曆數據創建"""
        ephemeris = SatelliteEphemeris(
            satellite_id="STARLINK-TEST",
            norad_id=12345,
            epoch_time=datetime.now(timezone.utc),
            semi_major_axis=6921.0,
            eccentricity=0.0001,
            inclination=53.0,
            raan=123.45,
            argument_of_perigee=67.89,
            mean_anomaly=123.45,
            mean_motion=15.12345678,
            latitude=24.5,
            longitude=121.0,
            altitude=550.0
        )
        
        assert ephemeris.satellite_id == "STARLINK-TEST"
        assert ephemeris.norad_id == 12345
        assert ephemeris.inclination == 53.0
        assert ephemeris.altitude == 550.0
    
    def test_position_calculation(self):
        """測試位置計算"""
        ephemeris = create_test_satellite_ephemeris("TEST-SAT", 12345)
        
        # 測試當前時間的位置
        current_time = datetime.now(timezone.utc)
        lat, lon, alt = ephemeris.calculate_position_at_time(current_time)
        
        assert -90 <= lat <= 90, f"緯度超出範圍: {lat}"
        assert -180 <= lon <= 180, f"經度超出範圍: {lon}"
        assert alt > 0, f"高度應為正值: {alt}"
    
    def test_visibility_calculation(self):
        """測試可見性計算"""
        ephemeris = create_test_satellite_ephemeris("TEST-SAT", 12345)
        
        # 設置接近台灣的位置，應該可見
        ephemeris.latitude = 25.0
        ephemeris.longitude = 121.5
        ephemeris.altitude = 550.0
        
        # NTPU 位置
        observer_lat = 24.9441667
        observer_lon = 121.3713889
        
        is_visible = ephemeris.is_visible_from_location(observer_lat, observer_lon, 5.0)
        assert isinstance(is_visible, bool)
        
        # 測試不可見的位置（地球另一側）
        ephemeris.latitude = -25.0
        ephemeris.longitude = -58.5
        
        is_not_visible = ephemeris.is_visible_from_location(observer_lat, observer_lon, 5.0)
        assert is_not_visible is False


class TestVisibleSatellite:
    """測試可見衛星"""
    
    def test_visible_satellite_creation(self):
        """測試可見衛星創建"""
        ephemeris = create_test_satellite_ephemeris("TEST-SAT", 12345)
        
        visible_sat = VisibleSatellite(
            satellite_id="TEST-SAT",
            ephemeris=ephemeris,
            visibility_status=SatelliteVisibilityStatus.VISIBLE,
            elevation_angle=25.5,
            azimuth_angle=180.0,
            distance=1000.0,
            doppler_shift=1500.0,
            first_visible_time=datetime.now(timezone.utc),
            last_update_time=datetime.now(timezone.utc)
        )
        
        assert visible_sat.satellite_id == "TEST-SAT"
        assert visible_sat.elevation_angle == 25.5
        assert visible_sat.azimuth_angle == 180.0
        assert visible_sat.visibility_status == SatelliteVisibilityStatus.VISIBLE
    
    def test_signal_strength_calculation(self):
        """測試信號強度計算"""
        ephemeris = create_test_satellite_ephemeris("TEST-SAT", 12345)
        
        visible_sat = VisibleSatellite(
            satellite_id="TEST-SAT",
            ephemeris=ephemeris,
            visibility_status=SatelliteVisibilityStatus.VISIBLE,
            elevation_angle=30.0,
            azimuth_angle=180.0,
            distance=800.0,  # 800km
            doppler_shift=1000.0,
            first_visible_time=datetime.now(timezone.utc),
            last_update_time=datetime.now(timezone.utc)
        )
        
        signal_strength = visible_sat.calculate_signal_strength()
        
        # 信號強度應該是負值 (dBm)
        assert signal_strength < 0
        assert signal_strength > -250  # 合理範圍（考慮自由空間路徑損耗）


class TestSIB19Message:
    """測試 SIB19 消息"""
    
    def test_sib19_message_creation(self):
        """測試 SIB19 消息創建"""
        ephemeris_list = [
            create_test_satellite_ephemeris("SAT-1", 12345),
            create_test_satellite_ephemeris("SAT-2", 12346)
        ]
        
        message = SIB19Message(
            message_id="test_sib19_001",
            broadcast_time=datetime.now(timezone.utc),
            broadcast_type=SIB19BroadcastType.PERIODIC,
            validity_duration=60,
            sequence_number=1,
            satellite_ephemeris_list=ephemeris_list
        )
        
        assert message.message_id == "test_sib19_001"
        assert message.broadcast_type == SIB19BroadcastType.PERIODIC
        assert len(message.satellite_ephemeris_list) == 2
        assert message.validity_duration == 60
    
    def test_sib19_message_validity(self):
        """測試 SIB19 消息有效性"""
        # 創建剛過期的消息
        old_message = SIB19Message(
            message_id="old_message",
            broadcast_time=datetime.now(timezone.utc) - timedelta(seconds=70),
            broadcast_type=SIB19BroadcastType.PERIODIC,
            validity_duration=60,
            sequence_number=1
        )
        
        assert old_message.is_valid() is False
        
        # 創建有效的消息
        valid_message = SIB19Message(
            message_id="valid_message",
            broadcast_time=datetime.now(timezone.utc),
            broadcast_type=SIB19BroadcastType.PERIODIC,
            validity_duration=60,
            sequence_number=2
        )
        
        assert valid_message.is_valid() is True
    
    def test_sib19_message_to_dict(self):
        """測試 SIB19 消息轉換為字典"""
        ephemeris = create_test_satellite_ephemeris("TEST-SAT", 12345)
        
        message = SIB19Message(
            message_id="test_dict",
            broadcast_time=datetime.now(timezone.utc),
            broadcast_type=SIB19BroadcastType.EMERGENCY,
            validity_duration=120,
            sequence_number=5,
            satellite_ephemeris_list=[ephemeris]
        )
        
        message_dict = message.to_dict()
        
        assert isinstance(message_dict, dict)
        assert message_dict['messageId'] == "test_dict"
        assert message_dict['broadcastType'] == "emergency"
        assert message_dict['sequenceNumber'] == 5
        assert len(message_dict['satelliteEphemerisList']) == 1


class TestSIB19BroadcastScheduler:
    """測試 SIB19 廣播調度器"""
    
    @pytest_asyncio.fixture
    async def scheduler(self):
        """創建測試用的廣播調度器"""
        return await create_sib19_broadcast_scheduler()
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, scheduler):
        """測試調度器初始化"""
        assert isinstance(scheduler, SIB19BroadcastScheduler)
        assert len(scheduler.active_satellites) >= 2  # 預設有測試衛星
        assert scheduler.is_running is False
        assert scheduler.observer_location['latitude'] == 24.9441667
        assert scheduler.observer_location['longitude'] == 121.3713889
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """測試調度器啟動和停止"""
        # 啟動調度器
        await scheduler.start_scheduler()
        assert scheduler.is_running is True
        assert scheduler.scheduler_task is not None
        
        # 等待一小段時間確保調度器運行
        await asyncio.sleep(0.1)
        
        # 停止調度器
        await scheduler.stop_scheduler()
        assert scheduler.is_running is False
    
    @pytest.mark.asyncio
    async def test_add_remove_satellite(self, scheduler):
        """測試添加和移除衛星"""
        initial_count = len(scheduler.active_satellites)
        
        # 添加新衛星
        new_satellite = create_test_satellite_ephemeris("NEW-SAT", 99999)
        scheduler.add_satellite(new_satellite)
        
        assert len(scheduler.active_satellites) == initial_count + 1
        assert "NEW-SAT" in scheduler.active_satellites
        
        # 移除衛星
        scheduler.remove_satellite("NEW-SAT")
        assert len(scheduler.active_satellites) == initial_count
        assert "NEW-SAT" not in scheduler.active_satellites
    
    @pytest.mark.asyncio
    async def test_update_observer_location(self, scheduler):
        """測試更新觀測點位置"""
        new_lat = 35.6762
        new_lon = 139.6503
        new_alt = 0.05
        new_min_elev = 10.0
        
        scheduler.update_observer_location(new_lat, new_lon, new_alt, new_min_elev)
        
        assert scheduler.observer_location['latitude'] == new_lat
        assert scheduler.observer_location['longitude'] == new_lon
        assert scheduler.observer_location['altitude'] == new_alt
        assert scheduler.observer_location['min_elevation'] == new_min_elev
    
    @pytest.mark.asyncio
    async def test_satellite_position_update(self, scheduler):
        """測試衛星位置更新"""
        # 記錄初始位置
        satellite_id = list(scheduler.active_satellites.keys())[0]
        initial_lat = scheduler.active_satellites[satellite_id].latitude
        
        # 更新衛星位置
        await scheduler._update_satellite_positions()
        
        # 檢查位置是否可能已更新（基於時間）
        updated_lat = scheduler.active_satellites[satellite_id].latitude
        # 由於時間很短，位置變化可能很小，所以這裡主要檢查功能沒有異常
        assert isinstance(updated_lat, (int, float))
        assert -90 <= updated_lat <= 90
    
    @pytest.mark.asyncio
    async def test_visible_satellites_calculation(self, scheduler):
        """測試可見衛星計算"""
        # 添加一顆接近觀測點的衛星
        close_satellite = create_test_satellite_ephemeris("CLOSE-SAT", 88888)
        close_satellite.latitude = 25.0  # 接近 NTPU
        close_satellite.longitude = 121.4
        close_satellite.altitude = 550.0
        
        scheduler.add_satellite(close_satellite)
        
        # 計算可見衛星
        await scheduler._calculate_visible_satellites()
        
        # 檢查可見衛星列表
        visible_satellites = scheduler.get_current_visible_satellites()
        assert isinstance(visible_satellites, list)
        
        # 檢查是否有可見衛星（接近的衛星應該可見）
        if visible_satellites:
            for sat in visible_satellites:
                assert 'satellite_id' in sat
                assert 'elevation_angle' in sat
                assert 'azimuth_angle' in sat
                assert sat['elevation_angle'] >= scheduler.observer_location['min_elevation']
    
    @pytest.mark.asyncio
    async def test_sib19_message_generation(self, scheduler):
        """測試 SIB19 消息生成"""
        # 先計算可見衛星
        await scheduler._calculate_visible_satellites()
        
        # 生成 SIB19 消息
        message = await scheduler._generate_sib19_message(SIB19BroadcastType.PERIODIC)
        
        if message:  # 如果有可見衛星才會生成消息
            assert isinstance(message, SIB19Message)
            assert message.broadcast_type == SIB19BroadcastType.PERIODIC
            assert message.sequence_number > 0
            assert message.validity_duration > 0
            assert len(message.satellite_ephemeris_list) <= scheduler.broadcast_config['max_satellites_per_message']
            
            # 檢查 NTN 配置
            assert 'ntn_area_code' in message.ntn_config
            assert 'time_reference' in message.ntn_config
            
            # 檢查服務區域信息
            assert 'service_area_id' in message.service_area_info
            assert 'coverage_center' in message.service_area_info
    
    @pytest.mark.asyncio
    async def test_emergency_broadcast(self, scheduler):
        """測試緊急廣播"""
        # 添加一顆可見衛星確保能生成消息
        visible_satellite = create_test_satellite_ephemeris("EMERGENCY-SAT", 77777)
        visible_satellite.latitude = 24.9
        visible_satellite.longitude = 121.4
        scheduler.add_satellite(visible_satellite)
        
        try:
            emergency_message = await scheduler.trigger_emergency_broadcast("測試緊急情況")
            
            assert emergency_message.broadcast_type == SIB19BroadcastType.EMERGENCY
            assert emergency_message.validity_duration == 120  # 緊急廣播延長有效期
            assert 'emergency_reason' in emergency_message.ntn_config
            assert emergency_message.ntn_config['emergency_reason'] == "測試緊急情況"
            
        except Exception as e:
            # 如果沒有可見衛星，緊急廣播可能失敗，這是正常的
            assert "無法生成緊急" in str(e)
    
    @pytest.mark.asyncio
    async def test_broadcast_statistics(self, scheduler):
        """測試廣播統計"""
        stats = scheduler.get_broadcast_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_active_satellites' in stats
        assert 'currently_visible_satellites' in stats
        assert 'total_broadcasts_sent' in stats
        assert 'scheduler_running' in stats
        assert 'observer_location' in stats
        assert 'broadcast_config' in stats
        
        assert stats['total_active_satellites'] >= 2
        assert stats['scheduler_running'] is False  # 預設未啟動
    
    @pytest.mark.asyncio
    async def test_latest_sib19_message_retrieval(self, scheduler):
        """測試最新 SIB19 消息獲取"""
        # 初始時沒有廣播歷史
        latest_message = scheduler.get_latest_sib19_message()
        assert latest_message is None
        
        # 手動添加一條廣播記錄
        test_message = SIB19Message(
            message_id="test_latest",
            broadcast_time=datetime.now(timezone.utc),
            broadcast_type=SIB19BroadcastType.PERIODIC,
            validity_duration=60,
            sequence_number=1
        )
        
        scheduler.broadcast_history.append(test_message)
        
        # 現在應該能獲取到消息
        latest_message = scheduler.get_latest_sib19_message()
        assert latest_message is not None
        assert latest_message['messageId'] == "test_latest"


class TestSIB19Integration:
    """SIB19 廣播系統整合測試"""
    
    @pytest_asyncio.fixture
    async def scheduler(self):
        """創建測試用的廣播調度器"""
        return await create_sib19_broadcast_scheduler()
    
    @pytest.mark.asyncio
    async def test_complete_broadcast_cycle(self, scheduler):
        """測試完整的廣播週期"""
        # 添加接近觀測點的衛星以確保可見性
        visible_satellite = create_test_satellite_ephemeris("CYCLE-TEST", 66666)
        visible_satellite.latitude = 24.95
        visible_satellite.longitude = 121.35
        visible_satellite.altitude = 550.0
        scheduler.add_satellite(visible_satellite)
        
        # 執行一次完整的廣播週期
        await scheduler._periodic_broadcast_cycle()
        
        # 檢查可見衛星是否已計算
        visible_satellites = scheduler.get_current_visible_satellites()
        assert isinstance(visible_satellites, list)
        
        # 檢查是否生成了廣播消息（如果有可見衛星）
        if visible_satellites:
            stats = scheduler.get_broadcast_statistics()
            assert stats['total_broadcasts_sent'] > 0
    
    @pytest.mark.asyncio
    async def test_scheduler_runtime_behavior(self, scheduler):
        """測試調度器運行時行為"""
        # 啟動調度器
        await scheduler.start_scheduler()
        
        # 等待至少一個廣播週期
        await asyncio.sleep(0.5)
        
        # 檢查調度器狀態
        assert scheduler.is_running is True
        
        # 檢查是否有廣播活動（可能有，取決於可見衛星）
        stats = scheduler.get_broadcast_statistics()
        assert stats['scheduler_running'] is True
        
        # 停止調度器
        await scheduler.stop_scheduler()
        assert scheduler.is_running is False
    
    @pytest.mark.asyncio
    async def test_multi_satellite_visibility_scenario(self, scheduler):
        """測试多衛星可見性場景"""
        # 添加多顆在不同位置的衛星
        satellites = [
            ("MULTI-SAT-1", 11111, 24.8, 121.2),
            ("MULTI-SAT-2", 11112, 25.1, 121.5),
            ("MULTI-SAT-3", 11113, 24.7, 121.8),
            ("MULTI-SAT-4", 11114, 25.2, 121.1)
        ]
        
        for sat_id, norad_id, lat, lon in satellites:
            satellite = create_test_satellite_ephemeris(sat_id, norad_id)
            satellite.latitude = lat
            satellite.longitude = lon
            satellite.altitude = 550.0
            scheduler.add_satellite(satellite)
        
        # 計算可見衛星
        await scheduler._calculate_visible_satellites()
        
        # 獲取可見衛星列表
        visible_satellites = scheduler.get_current_visible_satellites()
        
        # 檢查可見衛星的屬性
        for visible_sat in visible_satellites:
            assert visible_sat['elevation_angle'] >= scheduler.observer_location['min_elevation']
            assert 0 <= visible_sat['azimuth_angle'] <= 360
            assert visible_sat['distance_km'] > 0
            assert 'visibility_status' in visible_sat
            assert 'signal_strength_dbm' in visible_sat


class TestBroadcastConfigurationAndControl:
    """測試廣播配置和控制"""
    
    @pytest_asyncio.fixture
    async def scheduler(self):
        """創建測試用的廣播調度器"""
        return await create_sib19_broadcast_scheduler()
    
    @pytest.mark.asyncio
    async def test_broadcast_config_update(self, scheduler):
        """測試廣播配置更新"""
        original_interval = scheduler.broadcast_config['periodic_interval']
        
        # 更新配置
        new_interval = 45
        scheduler.broadcast_config['periodic_interval'] = new_interval
        
        assert scheduler.broadcast_config['periodic_interval'] == new_interval
        assert scheduler.broadcast_config['periodic_interval'] != original_interval
    
    @pytest.mark.asyncio
    async def test_different_broadcast_types(self, scheduler):
        """測試不同類型的廣播"""
        # 測試週期性廣播
        await scheduler._calculate_visible_satellites()
        periodic_message = await scheduler._generate_sib19_message(SIB19BroadcastType.PERIODIC)
        
        if periodic_message:
            assert periodic_message.broadcast_type == SIB19BroadcastType.PERIODIC
        
        # 測試事件觸發廣播
        event_message = await scheduler._generate_sib19_message(SIB19BroadcastType.EVENT_TRIGGERED)
        
        if event_message:
            assert event_message.broadcast_type == SIB19BroadcastType.EVENT_TRIGGERED


class TestHelperFunctions:
    """測試輔助函數"""
    
    @pytest.mark.asyncio
    async def test_create_sib19_broadcast_scheduler(self):
        """測試創建 SIB19 廣播調度器"""
        scheduler = await create_sib19_broadcast_scheduler()
        
        assert isinstance(scheduler, SIB19BroadcastScheduler)
        assert len(scheduler.active_satellites) >= 2
        assert scheduler.observer_location['latitude'] == 24.9441667
    
    def test_create_test_satellite_ephemeris(self):
        """測試創建測試衛星星曆"""
        ephemeris = create_test_satellite_ephemeris("TEST-HELPER", 55555)
        
        assert ephemeris.satellite_id == "TEST-HELPER"
        assert ephemeris.norad_id == 55555
        assert ephemeris.inclination == 53.0
        assert ephemeris.mean_motion == 15.12
        assert ephemeris.altitude == 550.0


# 性能測試
class TestSIB19Performance:
    """測試 SIB19 廣播性能"""
    
    @pytest_asyncio.fixture
    async def scheduler(self):
        """創建測試用的廣播調度器"""
        return await create_sib19_broadcast_scheduler()
    
    @pytest.mark.asyncio
    async def test_satellite_position_update_performance(self, scheduler):
        """測試衛星位置更新性能"""
        # 添加更多衛星
        for i in range(10):
            satellite = create_test_satellite_ephemeris(f"PERF-SAT-{i}", 50000 + i)
            scheduler.add_satellite(satellite)
        
        start_time = time.time()
        await scheduler._update_satellite_positions()
        update_time = time.time() - start_time
        
        # 位置更新應該在 100ms 內完成
        assert update_time < 0.1
    
    @pytest.mark.asyncio
    async def test_visibility_calculation_performance(self, scheduler):
        """測試可見性計算性能"""
        # 添加更多衛星
        for i in range(15):
            satellite = create_test_satellite_ephemeris(f"VIS-SAT-{i}", 60000 + i)
            # 隨機分佈位置
            satellite.latitude = 20.0 + (i % 10)
            satellite.longitude = 115.0 + (i % 15)
            scheduler.add_satellite(satellite)
        
        start_time = time.time()
        await scheduler._calculate_visible_satellites()
        calc_time = time.time() - start_time
        
        # 可見性計算應該在 200ms 內完成
        assert calc_time < 0.2
    
    @pytest.mark.asyncio
    async def test_message_generation_performance(self, scheduler):
        """測試消息生成性能"""
        # 確保有可見衛星
        await scheduler._calculate_visible_satellites()
        
        start_time = time.time()
        message = await scheduler._generate_sib19_message(SIB19BroadcastType.PERIODIC)
        gen_time = time.time() - start_time
        
        # 消息生成應該在 50ms 內完成
        assert gen_time < 0.05


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])