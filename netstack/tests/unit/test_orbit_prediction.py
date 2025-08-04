"""
Phase 3.2.2.1 軌道預測優化算法單元測試

測試軌道預測優化算法的完整實現，包括：
1. TLE 數據管理和解析
2. SGP4/SDP4 軌道傳播算法
3. 攝動力計算和修正
4. 坐標轉換和可見性計算
5. 預測品質評估和緩存機制
"""

import pytest
import pytest_asyncio
import asyncio
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

# 導入待測試的模組
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.algorithms.prediction.orbit_prediction import (
    OrbitPredictionEngine,
    TLEData,
    SatelliteState,
    PredictionRequest,
    PredictionResult,
    OrbitModelType,
    PredictionAccuracy,
    PerturbationType,
    create_orbit_prediction_engine,
    create_test_prediction_request,
    create_sample_tle_data
)


class TestTLEData:
    """測試 TLE 數據類"""
    
    def test_tle_creation_with_parsing(self):
        """測試 TLE 數據創建和解析"""
        tle = TLEData(
            satellite_id="TEST-001",
            satellite_name="Test Satellite",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        assert tle.satellite_id == "TEST-001"
        assert tle.satellite_name == "Test Satellite"
        assert tle.inclination_deg == 51.6461
        assert tle.raan_deg == 290.5094
        assert tle.eccentricity == 0.0000597
        assert tle.arg_perigee_deg == 91.8164
        assert tle.mean_anomaly_deg == 268.3516
        assert tle.mean_motion_revs_per_day == 15.48919103
    
    def test_tle_parsing_with_invalid_data(self):
        """測試無效 TLE 數據的解析"""
        tle = TLEData(
            satellite_id="INVALID-001",
            satellite_name="Invalid Satellite",
            line1="invalid line 1",
            line2="invalid line 2",
            epoch=datetime.now(timezone.utc)
        )
        
        # 解析失敗時應該保持默認值
        assert tle.inclination_deg == 0.0
        assert tle.mean_motion_revs_per_day == 0.0
    
    def test_tle_epoch_calculation(self):
        """測試 TLE epoch 時間計算"""
        # 測試 2021年第1天
        tle = TLEData(
            satellite_id="EPOCH-TEST",
            satellite_name="Epoch Test",
            line1="1 25544U 98067A   21001.50000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        # epoch 應該是 2021-01-01 12:00:00 UTC
        expected_epoch = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert abs((tle.epoch - expected_epoch).total_seconds()) < 60  # 允許1分鐘誤差


class TestSatelliteState:
    """測試衛星狀態類"""
    
    def test_satellite_state_creation(self):
        """測試衛星狀態創建"""
        state = SatelliteState(
            satellite_id="TEST-SAT-001",
            timestamp=datetime.now(timezone.utc),
            position_x=6500.0,
            position_y=1000.0,
            position_z=2000.0,
            velocity_x=0.5,
            velocity_y=7.5,
            velocity_z=0.1,
            altitude_km=400.0,
            latitude_deg=25.0,
            longitude_deg=121.0
        )
        
        assert state.satellite_id == "TEST-SAT-001"
        assert state.position_x == 6500.0
        assert state.altitude_km == 400.0
        assert state.latitude_deg == 25.0
    
    def test_position_velocity_vectors(self):
        """測試位置和速度向量計算"""
        state = SatelliteState(
            satellite_id="VECTOR-TEST",
            timestamp=datetime.now(timezone.utc),
            position_x=6500.0,
            position_y=1000.0,
            position_z=2000.0,
            velocity_x=0.5,
            velocity_y=7.5,
            velocity_z=0.1
        )
        
        pos_vector = state.get_position_vector()
        vel_vector = state.get_velocity_vector()
        
        np.testing.assert_array_equal(pos_vector, [6500.0, 1000.0, 2000.0])
        np.testing.assert_array_equal(vel_vector, [0.5, 7.5, 0.1])
    
    def test_orbital_speed_calculation(self):
        """測試軌道速度計算"""
        state = SatelliteState(
            satellite_id="SPEED-TEST",
            timestamp=datetime.now(timezone.utc),
            velocity_x=3.0,
            velocity_y=4.0,
            velocity_z=0.0
        )
        
        orbital_speed = state.calculate_orbital_speed()
        assert abs(orbital_speed - 5.0) < 1e-6  # 3-4-5 直角三角形
    
    def test_distance_calculation(self):
        """測試衛星間距離計算"""
        state1 = SatelliteState(
            satellite_id="SAT-1",
            timestamp=datetime.now(timezone.utc),
            position_x=0.0,
            position_y=0.0,
            position_z=0.0
        )
        
        state2 = SatelliteState(
            satellite_id="SAT-2", 
            timestamp=datetime.now(timezone.utc),
            position_x=3.0,
            position_y=4.0,
            position_z=0.0
        )
        
        distance = state1.calculate_distance_to(state2)
        assert abs(distance - 5.0) < 1e-6


class TestPredictionRequest:
    """測試預測請求類"""
    
    def test_prediction_request_creation(self):
        """測試預測請求創建"""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=6)
        
        request = PredictionRequest(
            request_id="TEST-REQ-001",
            satellite_ids=["SAT-1", "SAT-2"],
            start_time=start_time,
            end_time=end_time,
            time_step_seconds=60,
            accuracy_level=PredictionAccuracy.HIGH,
            observer_latitude_deg=25.0,
            observer_longitude_deg=121.0,
            include_perturbations=[PerturbationType.ATMOSPHERIC_DRAG]
        )
        
        assert request.request_id == "TEST-REQ-001"
        assert len(request.satellite_ids) == 2
        assert request.accuracy_level == PredictionAccuracy.HIGH
        assert request.observer_latitude_deg == 25.0
        assert PerturbationType.ATMOSPHERIC_DRAG in request.include_perturbations


class TestPredictionResult:
    """測試預測結果類"""
    
    def test_prediction_result_creation(self):
        """測試預測結果創建"""
        states = [
            SatelliteState("TEST-SAT", datetime.now(timezone.utc), altitude_km=400),
            SatelliteState("TEST-SAT", datetime.now(timezone.utc) + timedelta(minutes=5), altitude_km=410)
        ]
        
        result = PredictionResult(
            request_id="TEST-REQ",
            satellite_id="TEST-SAT",
            prediction_states=states,
            average_confidence=0.95,
            max_error_km=0.5,
            orbital_period_minutes=93.0
        )
        
        assert result.request_id == "TEST-REQ"
        assert len(result.prediction_states) == 2
        assert result.average_confidence == 0.95
        assert result.orbital_period_minutes == 93.0
    
    def test_get_state_at_time(self):
        """測試獲取指定時間的狀態"""
        base_time = datetime.now(timezone.utc)
        states = [
            SatelliteState("TEST-SAT", base_time, altitude_km=400),
            SatelliteState("TEST-SAT", base_time + timedelta(minutes=5), altitude_km=410),
            SatelliteState("TEST-SAT", base_time + timedelta(minutes=10), altitude_km=420)
        ]
        
        result = PredictionResult(
            request_id="TIME-TEST",
            satellite_id="TEST-SAT",
            prediction_states=states
        )
        
        # 測試精確時間匹配
        target_time = base_time + timedelta(minutes=5)
        state = result.get_state_at_time(target_time)
        assert state is not None
        assert state.altitude_km == 410
        
        # 測試最接近時間匹配
        target_time = base_time + timedelta(minutes=7)
        state = result.get_state_at_time(target_time)
        assert state is not None
        assert state.altitude_km in [410, 420]  # 應該是最接近的一個
    
    def test_get_states_in_timerange(self):
        """測試獲取時間範圍內的狀態"""
        base_time = datetime.now(timezone.utc)
        states = [
            SatelliteState("TEST-SAT", base_time, altitude_km=400),
            SatelliteState("TEST-SAT", base_time + timedelta(minutes=5), altitude_km=410),
            SatelliteState("TEST-SAT", base_time + timedelta(minutes=10), altitude_km=420),
            SatelliteState("TEST-SAT", base_time + timedelta(minutes=15), altitude_km=430)
        ]
        
        result = PredictionResult(
            request_id="RANGE-TEST",
            satellite_id="TEST-SAT",
            prediction_states=states
        )
        
        # 測試部分時間範圍
        start_time = base_time + timedelta(minutes=3)
        end_time = base_time + timedelta(minutes=12)
        
        range_states = result.get_states_in_timerange(start_time, end_time)
        assert len(range_states) == 2  # 5分鐘和10分鐘的狀態
        assert range_states[0].altitude_km == 410
        assert range_states[1].altitude_km == 420


class TestOrbitPredictionEngine:
    """測試軌道預測引擎"""
    
    @pytest_asyncio.fixture
    async def prediction_engine(self):
        """創建測試用預測引擎"""
        engine = create_orbit_prediction_engine("test_engine")
        return engine
    
    @pytest_asyncio.fixture
    async def running_engine(self):
        """創建運行中的預測引擎"""
        engine = create_orbit_prediction_engine("running_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, prediction_engine):
        """測試引擎初始化"""
        assert isinstance(prediction_engine, OrbitPredictionEngine)
        assert prediction_engine.engine_id.startswith("test_engine")
        assert prediction_engine.is_running is False
        assert len(prediction_engine.tle_database) == 0
        assert len(prediction_engine.prediction_cache) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self, prediction_engine):
        """測試引擎啟動和停止"""
        # 啟動引擎
        await prediction_engine.start_engine()
        assert prediction_engine.is_running is True
        assert prediction_engine.cache_cleanup_task is not None
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 停止引擎
        await prediction_engine.stop_engine()
        assert prediction_engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_tle_data_management(self, running_engine):
        """測試 TLE 數據管理"""
        # 更新 TLE 數據
        success = await running_engine.update_tle_data(
            satellite_id="TEST-SAT-001",
            tle_line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            tle_line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            satellite_name="Test Satellite 1"
        )
        
        assert success is True
        assert "TEST-SAT-001" in running_engine.tle_database
        assert running_engine.stats['tle_updates'] == 1
        
        # 獲取 TLE 數據
        tle_data = running_engine.get_tle_data("TEST-SAT-001")
        assert tle_data is not None
        assert tle_data.satellite_name == "Test Satellite 1"
        assert tle_data.inclination_deg == 51.6461
        
        # 檢查 TLE 年齡
        age_hours = running_engine.get_tle_age_hours("TEST-SAT-001")
        assert age_hours is not None
        assert age_hours < 1.0  # 應該是剛剛更新的
    
    @pytest.mark.asyncio
    async def test_batch_tle_update(self, running_engine):
        """測試批量 TLE 數據更新"""
        sample_data = create_sample_tle_data()
        
        success_count = await running_engine.batch_update_tle_data(sample_data)
        
        assert success_count == 2
        assert len(running_engine.tle_database) == 2
        assert "TEST-SAT-001" in running_engine.tle_database
        assert "TEST-SAT-002" in running_engine.tle_database
    
    @pytest.mark.asyncio
    async def test_sgp4_propagation(self, running_engine):
        """測試 SGP4 軌道傳播算法"""
        # 添加測試 TLE 數據
        tle_data = TLEData(
            satellite_id="SGP4-TEST",
            satellite_name="SGP4 Test Satellite",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        # 測試 SGP4 傳播計算
        position, velocity = running_engine._sgp4_propagate(tle_data, 0.0)  # epoch 時刻
        
        # 檢查結果合理性 
        pos_magnitude = np.linalg.norm(position)
        vel_magnitude = np.linalg.norm(velocity)
        
        # 地球半徑約 6371km，低軌道衛星距離應該在 6500-7000km 範圍
        assert 6500 < pos_magnitude < 8000
        # 軌道速度應該在 7-8 km/s 範圍
        assert 6 < vel_magnitude < 9
    
    @pytest.mark.asyncio
    async def test_kepler_equation_solver(self, running_engine):
        """測試開普勒方程求解"""
        # 測試各種偏心率和平近點角
        test_cases = [
            (0.0, 0.0),      # 圓軌道，M=0
            (0.1, math.pi),  # 小偏心率，M=π
            (0.5, math.pi/2), # 中等偏心率，M=π/2
            (0.8, 0.1)       # 大偏心率，小M
        ]
        
        for e, M in test_cases:
            E = running_engine._solve_kepler_equation(M, e)
            
            # 驗證開普勒方程：M = E - e*sin(E)
            calculated_M = E - e * math.sin(E)
            assert abs(calculated_M - M) < 1e-6
    
    @pytest.mark.asyncio
    async def test_coordinate_conversion(self, running_engine):
        """測試坐標轉換"""
        # 測試 ECI 到大地坐標轉換
        position = np.array([6500.0, 1000.0, 2000.0])  # km
        timestamp = datetime.now(timezone.utc)
        
        lat, lon, alt = running_engine._eci_to_geodetic(position, timestamp)
        
        # 檢查結果合理性
        assert -90 <= lat <= 90     # 緯度範圍
        assert -180 <= lon <= 180   # 經度範圍
        assert alt > 0              # 高度應該為正
    
    @pytest.mark.asyncio
    async def test_visibility_calculation(self, running_engine):
        """測試可見性計算"""
        # 高空衛星位置
        sat_position = np.array([6800.0, 0.0, 3000.0])  # km
        
        # NTPU 觀測點
        obs_lat = 24.9441667
        obs_lon = 121.3713889
        obs_alt = 0.05
        timestamp = datetime.now(timezone.utc)
        
        elevation, azimuth, distance = running_engine._calculate_visibility(
            sat_position, obs_lat, obs_lon, obs_alt, timestamp
        )
        
        # 檢查結果合理性
        assert -90 <= elevation <= 90   # 仰角範圍
        assert 0 <= azimuth <= 360      # 方位角範圍
        assert distance > 0             # 距離應該為正
    
    @pytest.mark.asyncio 
    async def test_atmospheric_drag_perturbation(self, running_engine):
        """測試大氣阻力攝動計算"""
        # 低軌道位置和速度
        position = np.array([6600.0, 0.0, 0.0])  # 約200km高度
        velocity = np.array([0.0, 7.5, 0.0])     # 典型軌道速度
        timestamp = datetime.now(timezone.utc)
        
        pos_correction, vel_correction = running_engine._calculate_atmospheric_drag(
            position, velocity, timestamp
        )
        
        # 在這個高度範圍，大氣阻力效應應該很小但存在
        # 檢查返回的修正向量不是 NaN 或無窮大
        assert np.all(np.isfinite(pos_correction))
        assert np.all(np.isfinite(vel_correction))
        
        # 對於200km高度，阻力修正應該很小
        assert np.linalg.norm(pos_correction) < 1.0  # 位置修正 < 1km
        assert np.linalg.norm(vel_correction) < 0.1  # 速度修正 < 0.1km/s
    
    @pytest.mark.asyncio
    async def test_j2_perturbation(self, running_engine):
        """測試 J2 攝動計算"""
        position = np.array([7000.0, 0.0, 1000.0])  # 典型軌道位置
        velocity = np.array([0.0, 7.0, 1.0])        # 典型軌道速度
        timestamp = datetime.now(timezone.utc)
        
        pos_correction, vel_correction = running_engine._calculate_earth_oblateness(
            position, velocity, timestamp
        )
        
        # J2 攝動應該產生修正
        assert np.linalg.norm(pos_correction) > 0
        assert np.linalg.norm(vel_correction) > 0
    
    @pytest.mark.asyncio
    async def test_prediction_quality_evaluation(self, running_engine):
        """測試預測品質評估"""
        # 創建測試狀態
        states = [
            SatelliteState("TEST", datetime.now(timezone.utc), 
                         prediction_confidence=0.9, prediction_error_km=0.1),
            SatelliteState("TEST", datetime.now(timezone.utc), 
                         prediction_confidence=0.8, prediction_error_km=0.2),
            SatelliteState("TEST", datetime.now(timezone.utc), 
                         prediction_confidence=0.95, prediction_error_km=0.05)
        ]
        
        avg_confidence, max_error, rmse_error = running_engine._evaluate_prediction_quality(
            states, PredictionAccuracy.HIGH
        )
        
        # 檢查計算結果
        assert 0.8 < avg_confidence < 1.0
        assert max_error == 0.2  # 最大誤差
        assert rmse_error > 0     # RMSE 應該大於0
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, running_engine):
        """測試置信度計算"""
        tle_data = TLEData(
            satellite_id="CONF-TEST",
            satellite_name="Confidence Test",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        # 測試不同時間範圍的置信度
        confidence_1h = running_engine._calculate_prediction_confidence(
            tle_data, 60.0, PredictionAccuracy.HIGH  # 1小時
        )
        confidence_24h = running_engine._calculate_prediction_confidence(
            tle_data, 24*60.0, PredictionAccuracy.HIGH  # 24小時
        )
        
        # 置信度應該在合理範圍內，並且長時間預測的置信度不高於短期預測
        assert 0 < confidence_1h <= 1.0
        assert 0 < confidence_24h <= 1.0
        assert confidence_24h <= confidence_1h
    
    @pytest.mark.asyncio
    async def test_orbit_prediction_full_workflow(self, running_engine):
        """測試完整軌道預測工作流程"""
        # 添加 TLE 數據
        sample_data = create_sample_tle_data()
        await running_engine.batch_update_tle_data(sample_data)
        
        # 創建預測請求
        request = create_test_prediction_request(
            satellite_ids=["TEST-SAT-001"],
            hours_ahead=2,
            time_step_minutes=10
        )
        
        # 執行預測
        results = await running_engine.predict_satellite_orbit(request)
        
        # 檢查結果
        assert len(results) == 1
        result = results[0]
        
        assert result.satellite_id == "TEST-SAT-001"
        assert len(result.prediction_states) > 0  # 應該有預測狀態
        assert result.computation_time_ms > 0     # 應該有計算時間
        assert result.orbital_period_minutes > 0  # 軌道週期應該為正
        
        # 檢查統計更新
        assert running_engine.stats['predictions_completed'] >= 1
    
    @pytest.mark.asyncio
    async def test_prediction_caching(self, running_engine):
        """測試預測結果緩存"""
        # 添加 TLE 數據
        sample_data = create_sample_tle_data()
        await running_engine.batch_update_tle_data(sample_data)
        
        # 創建相同的預測請求
        request = create_test_prediction_request(satellite_ids=["TEST-SAT-001"])
        
        # 第一次預測
        results1 = await running_engine.predict_satellite_orbit(request)
        cache_misses_1 = running_engine.stats['cache_misses']
        
        # 第二次相同的預測（應該命中緩存）
        results2 = await running_engine.predict_satellite_orbit(request)
        cache_hits = running_engine.stats['cache_hits']
        cache_misses_2 = running_engine.stats['cache_misses']
        
        # 檢查緩存效果
        assert len(results1) == len(results2)
        assert cache_hits > 0  # 應該有緩存命中
        assert cache_misses_2 == cache_misses_1  # 緩存遺失不應該增加
    
    @pytest.mark.asyncio
    async def test_model_selection(self, running_engine):
        """測試軌道模型選擇"""
        # 低軌道衛星 (高平均運動)
        leo_tle = TLEData(
            satellite_id="LEO-TEST",
            satellite_name="LEO Test",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        # 地球同步軌道衛星 (低平均運動)
        geo_tle = TLEData(
            satellite_id="GEO-TEST", 
            satellite_name="GEO Test",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  0.0000 290.5094 0000597  91.8164 268.3516 1.00270000262509",  # 每天1圈
            epoch=datetime.now(timezone.utc)
        )
        
        leo_model = running_engine._select_prediction_model(leo_tle, PredictionAccuracy.HIGH)
        geo_model = running_engine._select_prediction_model(geo_tle, PredictionAccuracy.HIGH)
        
        assert leo_model == OrbitModelType.SGP4
        assert geo_model == OrbitModelType.SDP4
    
    @pytest.mark.asyncio
    async def test_time_series_generation(self, running_engine):
        """測試時間序列生成"""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        step_seconds = 300  # 5分鐘
        
        time_points = running_engine._generate_time_series(start_time, end_time, step_seconds)
        
        # 應該有13個時間點 (0, 5, 10, ..., 60分鐘)
        assert len(time_points) == 13
        assert time_points[0] == start_time
        assert time_points[-1] == end_time
        
        # 檢查時間間隔
        for i in range(1, len(time_points)):
            interval = (time_points[i] - time_points[i-1]).total_seconds()
            assert interval == step_seconds
    
    @pytest.mark.asyncio
    async def test_orbital_period_calculation(self, running_engine):
        """測試軌道週期計算"""
        # ISS 類似軌道參數
        tle_data = TLEData(
            satellite_id="PERIOD-TEST",
            satellite_name="Period Test",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        period_minutes = running_engine._calculate_orbital_period(tle_data)
        
        # ISS 軌道週期約 93 分鐘
        assert 90 < period_minutes < 96
    
    @pytest.mark.asyncio
    async def test_error_estimation(self, running_engine):
        """測試預測誤差估算"""
        tle_data = TLEData(
            satellite_id="ERROR-TEST",
            satellite_name="Error Test",
            line1="1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            line2="2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509",
            epoch=datetime.now(timezone.utc)
        )
        
        # 測試不同精度級別的誤差估算
        error_low = running_engine._estimate_prediction_error(
            tle_data, 60.0, PredictionAccuracy.LOW
        )
        error_high = running_engine._estimate_prediction_error(
            tle_data, 60.0, PredictionAccuracy.HIGH
        )
        
        # 高精度模式的誤差應該更小
        assert error_high < error_low
        assert error_low > 0.5  # 低精度誤差應該 > 0.5km
        assert error_high < 0.1  # 高精度誤差應該 < 0.1km
    
    @pytest.mark.asyncio
    async def test_cache_management(self, running_engine):
        """測試緩存管理"""
        # 測試緩存鍵生成
        request = create_test_prediction_request()
        cache_key = running_engine._generate_cache_key("TEST-SAT", request)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
        assert "TEST-SAT" in cache_key
        
        # 測試緩存存取
        test_result = PredictionResult(
            request_id="CACHE-TEST",
            satellite_id="TEST-SAT",
            prediction_states=[]
        )
        
        # 存入緩存
        running_engine._cache_result(cache_key, test_result)
        assert len(running_engine.prediction_cache) == 1
        
        # 從緩存獲取
        cached_result = running_engine._get_cached_result(cache_key)
        assert cached_result is not None
        assert cached_result.request_id == "CACHE-TEST"
    
    @pytest.mark.asyncio
    async def test_engine_status(self, running_engine):
        """測試引擎狀態獲取"""
        # 添加一些數據
        await running_engine.batch_update_tle_data(create_sample_tle_data())
        
        status = running_engine.get_engine_status()
        
        assert isinstance(status, dict)
        assert status['engine_id'] == running_engine.engine_id
        assert status['is_running'] is True
        assert status['tle_count'] == 2
        assert 'statistics' in status
        assert 'configuration' in status
    
    @pytest.mark.asyncio
    async def test_config_update(self, running_engine):
        """測試配置更新"""
        original_cache_size = running_engine.prediction_config['cache_size']
        
        new_config = {
            'cache_size': 2000,
            'max_prediction_horizon_days': 14
        }
        
        running_engine.update_config(new_config)
        
        assert running_engine.prediction_config['cache_size'] == 2000
        assert running_engine.prediction_config['max_prediction_horizon_days'] == 14
        assert running_engine.prediction_config['cache_size'] != original_cache_size


class TestPerformanceMetrics:
    """測試性能指標"""
    
    @pytest_asyncio.fixture
    async def perf_engine(self):
        """創建性能測試引擎"""
        engine = create_orbit_prediction_engine("perf_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_prediction_performance(self, perf_engine):
        """測試預測性能"""
        # 添加測試數據
        sample_data = create_sample_tle_data()
        await perf_engine.batch_update_tle_data(sample_data)
        
        # 創建性能測試請求
        request = create_test_prediction_request(
            satellite_ids=["TEST-SAT-001", "TEST-SAT-002"],
            hours_ahead=1,
            time_step_minutes=5
        )
        
        # 執行預測並測量時間
        import time
        start_time = time.time()
        
        results = await perf_engine.predict_satellite_orbit(request)
        
        execution_time = time.time() - start_time
        
        # 檢查性能要求
        assert len(results) == 2  # 兩顆衛星
        assert execution_time < 5.0  # 應該在5秒內完成
        
        # 檢查每個結果的計算時間
        for result in results:
            assert result.computation_time_ms > 0
            assert result.computation_time_ms < 2000  # 每顆衛星 < 2秒
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, perf_engine):
        """測試緩存性能"""
        # 添加測試數據
        sample_data = create_sample_tle_data()
        await perf_engine.batch_update_tle_data(sample_data)
        
        request = create_test_prediction_request(satellite_ids=["TEST-SAT-001"])
        
        # 第一次預測（無緩存）
        import time
        start_time = time.time()
        results1 = await perf_engine.predict_satellite_orbit(request)
        first_time = time.time() - start_time
        
        # 第二次預測（有緩存）
        start_time = time.time()
        results2 = await perf_engine.predict_satellite_orbit(request)
        second_time = time.time() - start_time
        
        # 緩存應該顯著提升性能
        assert len(results1) == len(results2)
        assert second_time < first_time / 2  # 緩存應該至少快一倍
        assert perf_engine.stats['cache_hits'] > 0


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_orbit_prediction_engine(self):
        """測試創建軌道預測引擎"""
        engine = create_orbit_prediction_engine("helper_test")
        
        assert isinstance(engine, OrbitPredictionEngine)
        assert engine.engine_id.startswith("helper_test")
        assert engine.is_running is False
    
    def test_create_test_prediction_request(self):
        """測試創建測試預測請求"""
        request = create_test_prediction_request(
            satellite_ids=["SAT-1", "SAT-2"],
            hours_ahead=12,
            time_step_minutes=10
        )
        
        assert isinstance(request, PredictionRequest)
        assert len(request.satellite_ids) == 2
        assert request.satellite_ids == ["SAT-1", "SAT-2"]
        assert request.time_step_seconds == 600  # 10 minutes
        assert request.accuracy_level == PredictionAccuracy.MEDIUM
        
        # 檢查時間範圍
        time_diff = (request.end_time - request.start_time).total_seconds()
        assert abs(time_diff - 12 * 3600) < 60  # 12小時，允許1分鐘誤差
        
        # 檢查觀測者位置（NTPU）
        assert request.observer_latitude_deg == 24.9441667
        assert request.observer_longitude_deg == 121.3713889
        
        # 檢查攝動力設定
        assert PerturbationType.ATMOSPHERIC_DRAG in request.include_perturbations
        assert PerturbationType.EARTH_OBLATENESS in request.include_perturbations
    
    def test_create_sample_tle_data(self):
        """測試創建示例 TLE 數據"""
        sample_data = create_sample_tle_data()
        
        assert isinstance(sample_data, list)
        assert len(sample_data) == 2
        
        # 檢查第一個衛星數據
        sat1 = sample_data[0]
        assert sat1['satellite_id'] == 'TEST-SAT-001'
        assert sat1['satellite_name'] == 'Test Satellite 1'
        assert sat1['line1'].startswith('1 25544U')
        assert sat1['line2'].startswith('2 25544')
        
        # 檢查第二個衛星數據
        sat2 = sample_data[1]
        assert sat2['satellite_id'] == 'TEST-SAT-002'
        assert sat2['satellite_name'] == 'Test Satellite 2'
        assert sat2['line1'].startswith('1 43013U')
        assert sat2['line2'].startswith('2 43013')


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])