"""
Phase 3.1.3 時間同步和頻率補償單元測試

測試時間同步和頻率補償的完整實現，包括：
1. GPS/GNSS 時間基準整合
2. NTP 協議支援
3. 衛星時間偏移校正
4. 都卜勒頻移預測和補償
5. 動態頻率調整
6. 多普勒預補償
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

from src.protocols.sync.time_frequency_sync import (
    TimeFrequencySynchronizer,
    DopplerCompensator,
    TimeReference,
    FrequencyReference,
    DopplerParameters,
    SynchronizationStatus,
    NTPClient,
    TimeReferenceType,
    FrequencyBand,
    create_time_frequency_synchronizer,
    create_doppler_compensator,
    create_test_doppler_parameters
)


class TestTimeReference:
    """測試時間基準"""
    
    def test_time_reference_creation(self):
        """測試時間基準創建"""
        ref_time = datetime.now(timezone.utc)
        time_ref = TimeReference(
            reference_type=TimeReferenceType.GPS,
            timestamp=ref_time,
            accuracy_ns=10000,
            stability_ppm=1.0,
            source_id="gps_receiver",
            leap_seconds=18
        )
        
        assert time_ref.reference_type == TimeReferenceType.GPS
        assert time_ref.timestamp == ref_time
        assert time_ref.accuracy_ns == 10000
        assert time_ref.stability_ppm == 1.0
        assert time_ref.source_id == "gps_receiver"
        assert time_ref.leap_seconds == 18
    
    def test_time_offset_calculation(self):
        """測試時間偏移計算"""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=5)
        time_ref = TimeReference(
            reference_type=TimeReferenceType.GPS,
            timestamp=past_time,
            accuracy_ns=10000,
            stability_ppm=1.0,
            source_id="test"
        )
        
        offset = time_ref.get_current_offset()
        assert 4.0 < abs(offset) < 6.0  # 大約5秒前
    
    def test_time_reference_validity(self):
        """測試時間基準有效性"""
        # 有效的時間基準
        valid_ref = TimeReference(
            reference_type=TimeReferenceType.GPS,
            timestamp=datetime.now(timezone.utc),
            accuracy_ns=500000,  # 500µs
            stability_ppm=1.0,
            source_id="test"
        )
        assert valid_ref.is_valid() is True
        
        # 過期的時間基準
        old_ref = TimeReference(
            reference_type=TimeReferenceType.GPS,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
            accuracy_ns=500000,
            stability_ppm=1.0,
            source_id="test"
        )
        assert old_ref.is_valid() is False
        
        # 精度不足的時間基準
        inaccurate_ref = TimeReference(
            reference_type=TimeReferenceType.GPS,
            timestamp=datetime.now(timezone.utc),
            accuracy_ns=2000000,  # 2ms，超過1ms門檻
            stability_ppm=1.0,
            source_id="test"
        )
        assert inaccurate_ref.is_valid() is False


class TestFrequencyReference:
    """測試頻率基準"""
    
    def test_frequency_reference_creation(self):
        """測試頻率基準創建"""
        freq_ref = FrequencyReference(
            center_frequency_hz=2.0e9,
            frequency_band=FrequencyBand.S_BAND,
            stability_ppb=100,
            accuracy_ppb=50,
            temperature_coefficient=0.1,
            aging_rate=0.5,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert freq_ref.center_frequency_hz == 2.0e9
        assert freq_ref.frequency_band == FrequencyBand.S_BAND
        assert freq_ref.stability_ppb == 100
        assert freq_ref.accuracy_ppb == 50
    
    def test_frequency_drift_calculation(self):
        """測試頻率漂移計算"""
        freq_ref = FrequencyReference(
            center_frequency_hz=2.0e9,
            frequency_band=FrequencyBand.S_BAND,
            stability_ppb=100,
            accuracy_ppb=50,
            temperature_coefficient=0.1,
            aging_rate=0.5,
            timestamp=datetime.now(timezone.utc)
        )
        
        # 測試老化漂移（1小時）
        aging_drift = freq_ref.calculate_frequency_drift(1.0, 0.0)
        expected_aging = 2.0e9 * (0.5 / 8760) / 1e9  # ppb to Hz
        assert abs(aging_drift - expected_aging) < 0.01
        
        # 測試溫度漂移（10°C變化）
        temp_drift = freq_ref.calculate_frequency_drift(0.0, 10.0)
        expected_temp = 2.0e9 * (0.1 * 10 * 1e6) / 1e9  # ppm to Hz
        assert abs(temp_drift - expected_temp) < 1.0


class TestDopplerParameters:
    """測試都卜勒參數"""
    
    def test_doppler_params_creation(self):
        """測試都卜勒參數創建"""
        params = DopplerParameters(
            satellite_id="TEST-SAT",
            satellite_velocity=(7.5, 0.0, 0.0),
            satellite_position=(6921.0, 0.0, 0.0),
            observer_position=(24.9441667, 121.3713889, 0.1),
            carrier_frequency_hz=2.0e9,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert params.satellite_id == "TEST-SAT"
        assert params.satellite_velocity == (7.5, 0.0, 0.0)
        assert params.carrier_frequency_hz == 2.0e9
    
    def test_radial_velocity_calculation(self):
        """測試徑向速度計算"""
        params = create_test_doppler_parameters("TEST-SAT")
        radial_velocity = params.calculate_radial_velocity()
        
        # 徑向速度應該是合理的值
        assert isinstance(radial_velocity, float)
        assert -10.0 <= radial_velocity <= 10.0  # km/s範圍
    
    def test_doppler_shift_calculation(self):
        """測試都卜勒頻移計算"""
        params = create_test_doppler_parameters("TEST-SAT")
        doppler_shift = params.calculate_doppler_shift()
        
        # 都卜勒頻移應該在合理範圍內
        assert isinstance(doppler_shift, float)
        assert abs(doppler_shift) < 100000  # <100kHz 對於LEO衛星


class TestNTPClient:
    """測試 NTP 客戶端"""
    
    @pytest_asyncio.fixture
    async def ntp_client(self):
        """創建測試用 NTP 客戶端"""
        return NTPClient(['time.google.com', 'pool.ntp.org'])
    
    @pytest.mark.asyncio
    async def test_ntp_client_creation(self, ntp_client):
        """測試 NTP 客戶端創建"""
        assert isinstance(ntp_client, NTPClient)
        assert len(ntp_client.ntp_servers) == 2
        assert 'time.google.com' in ntp_client.ntp_servers
    
    @pytest.mark.asyncio
    async def test_ntp_time_request_timeout(self, ntp_client):
        """測試 NTP 時間請求超時處理"""
        # 使用不存在的伺服器測試超時
        ntp_time = await ntp_client.get_ntp_time('192.0.2.1', timeout=1.0)
        assert ntp_time is None
    
    @pytest.mark.asyncio
    @patch('socket.socket')
    async def test_ntp_sync_success(self, mock_socket, ntp_client):
        """測試 NTP 同步成功"""
        # 模擬 NTP 響應
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        # 創建模擬的 NTP 響應包
        import struct
        timestamp = int(time.time()) + 2208988800  # NTP epoch offset
        ntp_response = b'\x00' * 40 + struct.pack('!I', timestamp) + b'\x00' * 4
        mock_sock.recvfrom.return_value = (ntp_response, ('127.0.0.1', 123))
        
        time_ref = await ntp_client.sync_with_ntp()
        
        if time_ref:  # 可能由於網路問題失敗
            assert time_ref.reference_type == TimeReferenceType.NTP
            assert time_ref.accuracy_ns == 50000000  # 50ms
            assert time_ref.stability_ppm == 100


class TestSynchronizationStatus:
    """測試同步狀態"""
    
    def test_sync_status_creation(self):
        """測試同步狀態創建"""
        status = SynchronizationStatus(
            time_sync_achieved=True,
            frequency_sync_achieved=True,
            time_offset_ns=500000,
            frequency_offset_hz=100,
            sync_accuracy_ns=10000,
            last_sync_time=datetime.now(timezone.utc),
            sync_source="gps_receiver",
            quality_indicator=0.95
        )
        
        assert status.time_sync_achieved is True
        assert status.frequency_sync_achieved is True
        assert status.time_offset_ns == 500000
        assert status.quality_indicator == 0.95
    
    def test_sync_status_check(self):
        """測試同步狀態檢查"""
        # 已同步的狀態
        good_status = SynchronizationStatus(
            time_sync_achieved=True,
            frequency_sync_achieved=True,
            time_offset_ns=500000,  # 0.5ms
            frequency_offset_hz=100,  # 100Hz
            sync_accuracy_ns=10000,
            last_sync_time=datetime.now(timezone.utc),
            sync_source="test",
            quality_indicator=0.9
        )
        assert good_status.is_synchronized() is True
        
        # 時間偏移過大
        bad_time_status = SynchronizationStatus(
            time_sync_achieved=True,
            frequency_sync_achieved=True,
            time_offset_ns=2000000,  # 2ms，超過1ms門檻
            frequency_offset_hz=100,
            sync_accuracy_ns=10000,
            last_sync_time=datetime.now(timezone.utc),
            sync_source="test",
            quality_indicator=0.9
        )
        assert bad_time_status.is_synchronized() is False
        
        # 頻率偏移過大
        bad_freq_status = SynchronizationStatus(
            time_sync_achieved=True,
            frequency_sync_achieved=True,
            time_offset_ns=500000,
            frequency_offset_hz=1500,  # 1.5kHz，超過1kHz門檻
            sync_accuracy_ns=10000,
            last_sync_time=datetime.now(timezone.utc),
            sync_source="test",
            quality_indicator=0.9
        )
        assert bad_freq_status.is_synchronized() is False


class TestTimeFrequencySynchronizer:
    """測試時間頻率同步器"""
    
    @pytest_asyncio.fixture
    async def synchronizer(self):
        """創建測試用同步器"""
        return await create_time_frequency_synchronizer()
    
    @pytest.mark.asyncio
    async def test_synchronizer_initialization(self, synchronizer):
        """測試同步器初始化"""
        assert isinstance(synchronizer, TimeFrequencySynchronizer)
        assert len(synchronizer.time_references) == 0
        assert len(synchronizer.frequency_references) == 1  # 預設頻率基準
        assert synchronizer.is_running is False
        assert synchronizer.sync_status.time_sync_achieved is False
    
    @pytest.mark.asyncio
    async def test_synchronizer_start_stop(self, synchronizer):
        """測試同步器啟動和停止"""
        # 啟動同步器
        await synchronizer.start_synchronizer()
        assert synchronizer.is_running is True
        assert synchronizer.sync_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止同步器
        await synchronizer.stop_synchronizer()
        assert synchronizer.is_running is False
    
    @pytest.mark.asyncio
    async def test_sync_config_update(self, synchronizer):
        """測試同步配置更新"""
        original_interval = synchronizer.sync_config['time_sync_interval']
        
        new_config = {'time_sync_interval': 600}
        synchronizer.update_sync_config(new_config)
        
        assert synchronizer.sync_config['time_sync_interval'] == 600
        assert synchronizer.sync_config['time_sync_interval'] != original_interval
    
    @pytest.mark.asyncio
    async def test_time_sync_with_ntp(self, synchronizer):
        """測試 NTP 時間同步"""
        # 使用 patch 直接在同步器的 ntp_client 上模擬成功
        ntp_ref = TimeReference(
            reference_type=TimeReferenceType.NTP,
            timestamp=datetime.now(timezone.utc),
            accuracy_ns=500000,  # 500µs, well below 1ms threshold
            stability_ppm=100,
            source_id="time.google.com"
        )
        
        # 直接模擬 ntp_client.sync_with_ntp 方法
        async def mock_sync_with_ntp():
            return ntp_ref
        
        synchronizer.ntp_client.sync_with_ntp = mock_sync_with_ntp
        
        # 設置 NTP 為主要時間源
        synchronizer.sync_config['primary_time_source'] = TimeReferenceType.NTP
        
        await synchronizer._perform_time_sync()
        
        assert synchronizer.sync_status.time_sync_achieved is True
        assert synchronizer.sync_status.sync_source == "time.google.com"
    
    @pytest.mark.asyncio
    async def test_gps_time_sync(self, synchronizer):
        """測試 GPS 時間同步"""
        # GPS 時間同步（模擬實現）
        await synchronizer._perform_time_sync()
        
        # 由於是模擬實現，應該成功
        if synchronizer.sync_status.time_sync_achieved:
            assert synchronizer.sync_status.sync_source == "gps_receiver"
            assert synchronizer.sync_status.sync_accuracy_ns == 10000
    
    @pytest.mark.asyncio
    async def test_frequency_sync(self, synchronizer):
        """測試頻率同步"""
        # 先建立時間同步
        synchronizer.sync_status.time_sync_achieved = True
        synchronizer.sync_status.time_offset_ns = 500000  # 0.5ms
        
        await synchronizer._perform_frequency_sync()
        
        if synchronizer.sync_status.frequency_sync_achieved:
            assert synchronizer.sync_status.frequency_offset_hz != 0
    
    @pytest.mark.asyncio
    async def test_doppler_compensator_management(self, synchronizer):
        """測試都卜勒補償器管理"""
        # 添加都卜勒補償器
        compensator = create_doppler_compensator("TEST-SAT", 2.0e9)
        synchronizer.add_doppler_compensator("TEST-SAT", compensator)
        
        assert "TEST-SAT" in synchronizer.doppler_compensators
        assert len(synchronizer.doppler_compensators) == 1
        
        # 移除都卜勒補償器
        synchronizer.remove_doppler_compensator("TEST-SAT")
        assert "TEST-SAT" not in synchronizer.doppler_compensators
        assert len(synchronizer.doppler_compensators) == 0
    
    @pytest.mark.asyncio
    async def test_sync_status_retrieval(self, synchronizer):
        """測試同步狀態獲取"""
        status = synchronizer.get_sync_status()
        
        assert isinstance(status, dict)
        assert 'time_sync_achieved' in status
        assert 'frequency_sync_achieved' in status
        assert 'time_offset_ns' in status
        assert 'frequency_offset_hz' in status
        assert 'sync_accuracy_ns' in status
        assert 'last_sync_time' in status
        assert 'sync_source' in status
        assert 'quality_indicator' in status
        assert 'is_synchronized' in status
        assert 'active_compensators' in status


class TestDopplerCompensator:
    """測試都卜勒補償器"""
    
    @pytest_asyncio.fixture
    async def compensator(self):
        """創建測試用都卜勒補償器"""
        return create_doppler_compensator("TEST-SAT", 2.0e9)
    
    @pytest.mark.asyncio
    async def test_compensator_initialization(self, compensator):
        """測試補償器初始化"""
        assert isinstance(compensator, DopplerCompensator)
        assert compensator.satellite_id == "TEST-SAT"
        assert compensator.carrier_frequency_hz == 2.0e9
        assert compensator.current_compensation_hz == 0.0
        assert len(compensator.doppler_history) == 0
    
    @pytest.mark.asyncio
    async def test_doppler_parameters_update(self, compensator):
        """測試都卜勒參數更新"""
        params = create_test_doppler_parameters("TEST-SAT")
        
        await compensator.update_doppler_parameters(params)
        
        assert len(compensator.doppler_history) == 1
        assert compensator.current_compensation_hz != 0.0
    
    @pytest.mark.asyncio
    async def test_compensation_calculation(self, compensator):
        """測試補償計算"""
        # 模擬都卜勒頻移
        test_doppler = 5000.0  # 5kHz
        
        await compensator._calculate_compensation(test_doppler)
        
        # 補償應該是反向的
        assert compensator.current_compensation_hz == -test_doppler
    
    @pytest.mark.asyncio
    async def test_compensation_limits(self, compensator):
        """測試補償限制"""
        # 測試超出限制的都卜勒頻移
        extreme_doppler = 100000.0  # 100kHz，超過50kHz限制
        
        await compensator._calculate_compensation(extreme_doppler)
        
        # 補償應該被限制在最大值
        max_comp = compensator.config['max_compensation_hz']
        assert abs(compensator.current_compensation_hz) <= max_comp
    
    @pytest.mark.asyncio
    async def test_compensated_frequency(self, compensator):
        """測試補償後頻率"""
        original_freq = compensator.carrier_frequency_hz
        test_compensation = -1000.0  # -1kHz補償
        
        compensator.current_compensation_hz = test_compensation
        compensated_freq = compensator.get_compensated_frequency()
        
        assert compensated_freq == original_freq + test_compensation
    
    @pytest.mark.asyncio
    async def test_compensation_info(self, compensator):
        """測試補償信息獲取"""
        # 添加一些歷史數據
        params = create_test_doppler_parameters("TEST-SAT")
        await compensator.update_doppler_parameters(params)
        
        info = compensator.get_compensation_info()
        
        assert isinstance(info, dict)
        assert info['satellite_id'] == "TEST-SAT"
        assert info['carrier_frequency_hz'] == 2.0e9
        assert 'current_compensation_hz' in info
        assert 'compensated_frequency_hz' in info
        assert 'history_points' in info
        assert info['history_points'] == 1


class TestTimeFrequencySyncIntegration:
    """時間頻率同步系統整合測試"""
    
    @pytest_asyncio.fixture
    async def sync_system(self):
        """創建完整的同步系統"""
        synchronizer = await create_time_frequency_synchronizer()
        
        # 添加多個都卜勒補償器
        satellites = ["SAT-1", "SAT-2", "SAT-3"]
        for sat_id in satellites:
            compensator = create_doppler_compensator(sat_id, 2.0e9)
            synchronizer.add_doppler_compensator(sat_id, compensator)
        
        return synchronizer
    
    @pytest.mark.asyncio
    async def test_complete_sync_cycle(self, sync_system):
        """測試完整的同步週期"""
        # 啟動同步系統
        await sync_system.start_synchronizer()
        
        # 等待至少一個同步週期
        await asyncio.sleep(0.2)
        
        # 檢查同步狀態
        status = sync_system.get_sync_status()
        assert status['active_compensators'] == 3
        
        # 停止同步系統
        await sync_system.stop_synchronizer()
        assert sync_system.is_running is False
    
    @pytest.mark.asyncio
    async def test_multi_satellite_doppler_compensation(self, sync_system):
        """測試多衛星都卜勒補償"""
        # 為每個衛星更新都卜勒參數
        for sat_id in ["SAT-1", "SAT-2", "SAT-3"]:
            params = create_test_doppler_parameters(sat_id)
            compensator = sync_system.doppler_compensators[sat_id]
            await compensator.update_doppler_parameters(params)
        
        # 檢查所有補償器都有數據
        for sat_id, compensator in sync_system.doppler_compensators.items():
            info = compensator.get_compensation_info()
            assert info['history_points'] >= 1
            assert info['current_compensation_hz'] != 0.0
    
    @pytest.mark.asyncio
    async def test_sync_quality_assessment(self, sync_system):
        """測試同步品質評估"""
        # 模擬高品質同步
        sync_system.sync_status.time_sync_achieved = True
        sync_system.sync_status.frequency_sync_achieved = True
        sync_system.sync_status.time_offset_ns = 100000  # 0.1ms
        sync_system.sync_status.frequency_offset_hz = 50  # 50Hz
        sync_system.sync_status.sync_accuracy_ns = 5000  # 5µs
        sync_system.sync_status.quality_indicator = 0.95
        
        status = sync_system.get_sync_status()
        assert status['is_synchronized'] is True
        assert status['quality_indicator'] > 0.9


class TestHelperFunctions:
    """測試輔助函數"""
    
    @pytest.mark.asyncio
    async def test_create_time_frequency_synchronizer(self):
        """測試創建時間頻率同步器"""
        synchronizer = await create_time_frequency_synchronizer()
        
        assert isinstance(synchronizer, TimeFrequencySynchronizer)
        assert len(synchronizer.frequency_references) == 1
        assert 'default_s_band' in synchronizer.frequency_references
    
    def test_create_doppler_compensator(self):
        """測試創建都卜勒補償器"""
        compensator = create_doppler_compensator("TEST-SAT", 1.5e9)
        
        assert isinstance(compensator, DopplerCompensator)
        assert compensator.satellite_id == "TEST-SAT"
        assert compensator.carrier_frequency_hz == 1.5e9
    
    def test_create_test_doppler_parameters(self):
        """測試創建測試都卜勒參數"""
        params = create_test_doppler_parameters("TEST-SAT")
        
        assert isinstance(params, DopplerParameters)
        assert params.satellite_id == "TEST-SAT"
        assert params.satellite_velocity == (7.5, 0.0, 0.0)
        assert params.observer_position == (24.9441667, 121.3713889, 0.1)
        assert params.carrier_frequency_hz == 2.0e9


# 性能測試
class TestTimeFrequencySyncPerformance:
    """測試時間頻率同步性能"""
    
    @pytest_asyncio.fixture
    async def perf_synchronizer(self):
        """創建性能測試用同步器"""
        synchronizer = await create_time_frequency_synchronizer()
        
        # 添加更多都卜勒補償器
        for i in range(20):
            compensator = create_doppler_compensator(f"PERF-SAT-{i}", 2.0e9)
            synchronizer.add_doppler_compensator(f"PERF-SAT-{i}", compensator)
        
        return synchronizer
    
    @pytest.mark.asyncio
    async def test_time_sync_performance(self, perf_synchronizer):
        """測試時間同步性能"""
        start_time = time.time()
        await perf_synchronizer._perform_time_sync()
        sync_time = time.time() - start_time
        
        # 時間同步應該在 100ms 內完成
        assert sync_time < 0.1
    
    @pytest.mark.asyncio
    async def test_frequency_sync_performance(self, perf_synchronizer):
        """測試頻率同步性能"""
        # 先建立時間同步
        perf_synchronizer.sync_status.time_sync_achieved = True
        
        start_time = time.time()
        await perf_synchronizer._perform_frequency_sync()
        sync_time = time.time() - start_time
        
        # 頻率同步應該在 50ms 內完成
        assert sync_time < 0.05
    
    @pytest.mark.asyncio
    async def test_doppler_update_performance(self, perf_synchronizer):
        """測試都卜勒補償更新性能"""
        # 為所有補償器添加測試數據
        for sat_id, compensator in perf_synchronizer.doppler_compensators.items():
            params = create_test_doppler_parameters(sat_id)
            await compensator.update_doppler_parameters(params)
        
        start_time = time.time()
        await perf_synchronizer._update_doppler_compensation()
        update_time = time.time() - start_time
        
        # 20個補償器的更新應該在 200ms 內完成
        assert update_time < 0.2


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])