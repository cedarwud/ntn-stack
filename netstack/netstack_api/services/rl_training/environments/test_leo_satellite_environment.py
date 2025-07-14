"""
Phase 2.1 LEO 衛星環境測試

測試 LEOSatelliteEnvironment 的核心功能，包括：
- 軌道動力學計算
- 事件檢測
- 候選衛星評分
- 動態負載平衡
- 信號品質預測
"""

import asyncio
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from .leo_satellite_environment import (
    LEOSatelliteEnvironment,
    SatelliteState,
    OrbitEvent,
    CandidateScore,
    DynamicLoadBalancer,
)


class TestLEOSatelliteEnvironment:
    """LEO 衛星環境測試類"""

    @pytest.fixture
    def environment_config(self):
        """環境配置"""
        return {
            "simworld_url": "http://localhost:8888",
            "max_satellites": 6,
            "scenario": "urban",
            "min_elevation": 10.0,
            "fallback_enabled": True,
            "orbit_update_interval": 5.0,
            "handover_prediction_horizon": 60.0,
            "signal_degradation_threshold": -85.0,
            "scoring_weights": {
                "signal_quality": 0.4,
                "load_factor": 0.25,
                "elevation_angle": 0.2,
                "distance": 0.15,
            },
        }

    @pytest.fixture
    def sample_satellites(self):
        """示例衛星數據"""
        return [
            SatelliteState(
                id=44713,
                name="STARLINK-1007",
                position={
                    "latitude": 25.0,
                    "longitude": 121.0,
                    "altitude": 550.0,
                    "elevation": 45.0,
                    "azimuth": 180.0,
                    "range": 800.0,
                },
                signal_quality={"rsrp": -80.0, "rsrq": -8.0, "sinr": 15.0},
                load_factor=0.3,
                timestamp=datetime.now().isoformat(),
            ),
            SatelliteState(
                id=44714,
                name="STARLINK-1008",
                position={
                    "latitude": 24.0,
                    "longitude": 120.0,
                    "altitude": 560.0,
                    "elevation": 30.0,
                    "azimuth": 90.0,
                    "range": 1200.0,
                },
                signal_quality={"rsrp": -85.0, "rsrq": -10.0, "sinr": 12.0},
                load_factor=0.5,
                timestamp=datetime.now().isoformat(),
            ),
        ]

    def test_environment_initialization(self, environment_config):
        """測試環境初始化"""
        env = LEOSatelliteEnvironment(environment_config)

        assert env.simworld_url == "http://localhost:8888"
        assert env.max_satellites == 6
        assert env.scenario == "urban"
        assert env.min_elevation == 10.0
        assert env.fallback_enabled is True
        assert env.orbit_update_interval == 5.0
        assert env.handover_prediction_horizon == 60.0
        assert env.signal_degradation_threshold == -85.0

        # 檢查評分權重
        assert env.scoring_weights["signal_quality"] == 0.4
        assert env.scoring_weights["load_factor"] == 0.25
        assert env.scoring_weights["elevation_angle"] == 0.2
        assert env.scoring_weights["distance"] == 0.15

        # 檢查動態負載平衡器
        assert isinstance(env.load_balancer, DynamicLoadBalancer)
        assert env.load_balancer.capacity_threshold == 0.8

        # 檢查動作和狀態空間
        assert env.action_space.n == 6
        assert env.observation_space.shape == (36,)  # 6 衛星 * 6 特徵

    def test_fallback_satellite_data(self, environment_config):
        """測試 fallback 衛星數據生成"""
        env = LEOSatelliteEnvironment(environment_config)

        fallback_satellites = env._get_fallback_satellite_data()

        assert len(fallback_satellites) == 6
        assert all(isinstance(sat, SatelliteState) for sat in fallback_satellites)

        # 檢查衛星 ID 唯一性
        satellite_ids = [sat.id for sat in fallback_satellites]
        assert len(set(satellite_ids)) == len(satellite_ids)

        # 檢查數據合理性
        for sat in fallback_satellites:
            assert sat.position["elevation"] > 0
            assert -150 <= sat.signal_quality["rsrp"] <= -50
            assert 0 <= sat.load_factor <= 1

    @pytest.mark.asyncio
    async def test_predict_signal_quality(self, environment_config):
        """測試信號品質預測"""
        env = LEOSatelliteEnvironment(environment_config)

        position = {"elevation": 45.0, "range": 800.0}

        signal_quality = await env._predict_signal_quality(position)

        # 檢查返回的信號品質指標
        assert "rsrp" in signal_quality
        assert "rsrq" in signal_quality
        assert "sinr" in signal_quality

        # 檢查數據合理性
        assert -150 <= signal_quality["rsrp"] <= -50
        assert -30 <= signal_quality["rsrq"] <= 10
        assert -10 <= signal_quality["sinr"] <= 30

    @pytest.mark.asyncio
    async def test_calculate_dynamic_load(self, environment_config):
        """測試動態負載計算"""
        env = LEOSatelliteEnvironment(environment_config)

        satellite_id = 44713
        load_factor = await env._calculate_dynamic_load(satellite_id)

        # 檢查負載因子範圍
        assert 0.0 <= load_factor <= 1.0

        # 測試一致性 (相同衛星 ID 應該產生相似的負載)
        load_factor2 = await env._calculate_dynamic_load(satellite_id)
        assert abs(load_factor - load_factor2) < 0.3  # 考慮隨機因子

    @pytest.mark.asyncio
    async def test_detect_orbit_events(self, environment_config, sample_satellites):
        """測試軌道事件檢測"""
        env = LEOSatelliteEnvironment(environment_config)

        # 添加歷史記錄
        for sat in sample_satellites:
            env._update_satellite_history(sat)

        # 修改衛星狀態以觸發事件
        modified_satellites = sample_satellites.copy()
        modified_satellites[0].position["elevation"] = 50.0  # 5度變化
        modified_satellites[0].signal_quality["rsrp"] = -90.0  # 信號劣化

        await env._detect_orbit_events(modified_satellites)

        # 檢查事件是否被檢測到
        assert len(env.orbit_events) > 0

        # 檢查事件類型
        event_types = [event.event_type for event in env.orbit_events]
        assert "elevation_change" in event_types or "signal_degradation" in event_types

    def test_evaluate_candidate_satellites(self, environment_config, sample_satellites):
        """測試候選衛星評分"""
        env = LEOSatelliteEnvironment(environment_config)

        scored_candidates = env.evaluate_candidate_satellites(sample_satellites)

        assert len(scored_candidates) == 2
        assert all(isinstance(score, CandidateScore) for score in scored_candidates)

        # 檢查評分是否按降序排列
        for i in range(len(scored_candidates) - 1):
            assert (
                scored_candidates[i].overall_score
                >= scored_candidates[i + 1].overall_score
            )

        # 檢查評分範圍
        for score in scored_candidates:
            assert 0 <= score.overall_score <= 100
            assert 0 <= score.signal_score <= 100
            assert 0 <= score.load_score <= 100
            assert 0 <= score.elevation_score <= 100
            assert 0 <= score.distance_score <= 100

    def test_calculate_handover_metrics(self, environment_config, sample_satellites):
        """測試換手指標計算"""
        env = LEOSatelliteEnvironment(environment_config)

        satellite = sample_satellites[0]
        metrics = env._calculate_handover_metrics(satellite)

        # 檢查指標值
        assert metrics.rsrp == satellite.signal_quality["rsrp"]
        assert metrics.rsrq == satellite.signal_quality["rsrq"]
        assert metrics.sinr == satellite.signal_quality["sinr"]
        assert metrics.load_factor == satellite.load_factor
        assert 0 <= metrics.handover_probability <= 1

    def test_get_observation(self, environment_config, sample_satellites):
        """測試觀測值生成"""
        env = LEOSatelliteEnvironment(environment_config)
        env.current_satellites = sample_satellites

        observation = env._get_observation()

        # 檢查觀測值形狀
        assert observation.shape == (36,)  # 6 衛星 * 6 特徵

        # 檢查觀測值範圍
        assert observation.dtype == np.float32

        # 檢查非零值 (前兩個衛星應該有數據)
        first_satellite_features = observation[:6]
        assert not np.allclose(first_satellite_features, 0)

    def test_calculate_reward(self, environment_config, sample_satellites):
        """測試獎勵函數計算"""
        env = LEOSatelliteEnvironment(environment_config)
        env.current_satellites = sample_satellites

        # 測試有效動作
        reward = env._calculate_reward(0, None)
        assert -1.0 <= reward <= 1.0

        # 測試無效動作
        invalid_reward = env._calculate_reward(10, None)
        assert invalid_reward == -10.0

        # 測試換手懲罰
        handover_reward = env._calculate_reward(0, sample_satellites[1].id)
        assert handover_reward <= reward  # 換手應該有懲罰

    @pytest.mark.asyncio
    async def test_reset_environment(self, environment_config):
        """測試環境重置"""
        env = LEOSatelliteEnvironment(environment_config)

        # Mock SimWorld API 調用
        with patch.object(env, "get_satellite_data") as mock_get_data:
            mock_get_data.return_value = env._get_fallback_satellite_data()

            observation, info = await env.reset()

            # 檢查重置後的狀態
            assert observation.shape == (36,)
            assert "serving_satellite_id" in info
            assert "available_satellites" in info
            assert "episode_steps" in info

            # 檢查統計重置
            assert env.episode_steps == 0
            assert env.total_handovers == 0
            assert env.successful_handovers == 0
            assert env.total_reward == 0.0

    @pytest.mark.asyncio
    async def test_step_environment(self, environment_config, sample_satellites):
        """測試環境步驟執行"""
        env = LEOSatelliteEnvironment(environment_config)
        env.current_satellites = sample_satellites

        # Mock SimWorld API 調用
        with patch.object(env, "get_satellite_data") as mock_get_data:
            mock_get_data.return_value = sample_satellites

            observation, reward, terminated, truncated, info = await env.step(0)

            # 檢查返回值
            assert observation.shape == (36,)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)

            # 檢查統計更新
            assert env.episode_steps == 1
            assert "serving_satellite_id" in info
            assert "selected_action" in info
            assert "reward" in info

    def test_get_stats(self, environment_config, sample_satellites):
        """測試統計信息獲取"""
        env = LEOSatelliteEnvironment(environment_config)
        env.current_satellites = sample_satellites

        stats = env.get_stats()

        # 檢查統計信息
        assert stats["environment_type"] == "LEOSatelliteEnvironment"
        assert stats["scenario"] == "urban"
        assert stats["max_satellites"] == 6
        assert stats["current_satellites"] == 2
        assert stats["fallback_enabled"] is True
        assert stats["simworld_url"] == "http://localhost:8888"


class TestDynamicLoadBalancer:
    """動態負載平衡器測試類"""

    @pytest.fixture
    def load_balancer(self):
        """負載平衡器實例"""
        return DynamicLoadBalancer(capacity_threshold=0.8, balance_weight=0.3)

    @pytest.fixture
    def sample_satellites_for_balancing(self):
        """用於負載平衡測試的衛星數據"""
        return [
            SatelliteState(
                id=1,
                name="SAT1",
                position={"elevation": 45.0, "range": 800.0},
                signal_quality={"rsrp": -80.0, "rsrq": -8.0, "sinr": 15.0},
                load_factor=0.9,  # 高負載
                timestamp=datetime.now().isoformat(),
            ),
            SatelliteState(
                id=2,
                name="SAT2",
                position={"elevation": 30.0, "range": 1200.0},
                signal_quality={"rsrp": -85.0, "rsrq": -10.0, "sinr": 12.0},
                load_factor=0.2,  # 低負載
                timestamp=datetime.now().isoformat(),
            ),
            SatelliteState(
                id=3,
                name="SAT3",
                position={"elevation": 60.0, "range": 600.0},
                signal_quality={"rsrp": -75.0, "rsrq": -6.0, "sinr": 18.0},
                load_factor=0.5,  # 中等負載
                timestamp=datetime.now().isoformat(),
            ),
        ]

    def test_load_balancer_initialization(self, load_balancer):
        """測試負載平衡器初始化"""
        assert load_balancer.capacity_threshold == 0.8
        assert load_balancer.balance_weight == 0.3
        assert isinstance(load_balancer.load_history, dict)

    def test_balance_load(self, load_balancer, sample_satellites_for_balancing):
        """測試負載平衡"""
        balanced_satellites = load_balancer.balance_load(
            sample_satellites_for_balancing
        )

        # 檢查返回的衛星數量
        assert len(balanced_satellites) == 3

        # 檢查高負載衛星的負載因子被調整
        high_load_sat = next(sat for sat in balanced_satellites if sat.id == 1)
        assert high_load_sat.load_factor >= 0.9  # 應該被調整（增加）

        # 檢查低負載衛星的負載因子被調整
        low_load_sat = next(sat for sat in balanced_satellites if sat.id == 2)
        assert low_load_sat.load_factor <= 0.2  # 應該被調整（減少）

    def test_predict_load_trend(self, load_balancer):
        """測試負載趨勢預測"""
        satellite_id = 1

        # 添加負載歷史
        load_balancer.load_history[satellite_id] = [0.3, 0.4, 0.5, 0.6, 0.7]

        trend = load_balancer.predict_load_trend(satellite_id)

        # 檢查趨勢預測
        assert -1.0 <= trend <= 1.0
        assert trend > 0  # 應該是上升趨勢

    def test_empty_satellites_list(self, load_balancer):
        """測試空衛星列表"""
        balanced_satellites = load_balancer.balance_load([])
        assert len(balanced_satellites) == 0

    def test_load_history_update(self, load_balancer, sample_satellites_for_balancing):
        """測試負載歷史更新"""
        initial_history_count = len(load_balancer.load_history)

        load_balancer.balance_load(sample_satellites_for_balancing)

        # 檢查歷史記錄是否更新
        assert len(load_balancer.load_history) == initial_history_count + 3

        # 檢查每個衛星的歷史記錄
        for satellite in sample_satellites_for_balancing:
            assert satellite.id in load_balancer.load_history
            assert len(load_balancer.load_history[satellite.id]) == 1


# 運行測試的輔助函數
def run_phase_2_1_tests():
    """運行 Phase 2.1 測試"""
    print("🚀 開始運行 Phase 2.1 LEO 衛星環境測試...")

    # 測試環境配置
    config = {
        "simworld_url": "http://localhost:8888",
        "max_satellites": 6,
        "scenario": "urban",
        "min_elevation": 10.0,
        "fallback_enabled": True,
    }

    try:
        # 基本功能測試
        env = LEOSatelliteEnvironment(config)
        print("✅ 環境初始化測試通過")

        # Fallback 數據測試
        fallback_data = env._get_fallback_satellite_data()
        assert len(fallback_data) == 6
        print("✅ Fallback 數據生成測試通過")

        # 評分系統測試
        scored_candidates = env.evaluate_candidate_satellites(fallback_data)
        assert len(scored_candidates) == 6
        print("✅ 候選衛星評分測試通過")

        # 動態負載平衡測試
        balanced_satellites = env.load_balancer.balance_load(fallback_data)
        assert len(balanced_satellites) == 6
        print("✅ 動態負載平衡測試通過")

        print("🎉 Phase 2.1 所有測試通過！")
        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


if __name__ == "__main__":
    # 運行簡化測試
    success = run_phase_2_1_tests()

    if success:
        print("\n🎯 Phase 2.1 測試總結:")
        print("✅ LEO 衛星環境核心架構：正常運行")
        print("✅ 候選衛星評分系統：正常運行")
        print("✅ 動態負載平衡：正常運行")
        print("✅ Fallback 機制：正常運行")
        print("\n🚀 Phase 2.1 已準備好進入 Phase 2.2！")
    else:
        print("\n❌ 測試失敗，請檢查實現")
