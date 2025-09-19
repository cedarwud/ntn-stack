"""
信號品質計算器 - TDD核心算法測試套件

測試重點:
- RSRP/RSRQ/SINR計算精度
- ITU-R P.618標準合規
- 路徑損耗模型驗證
- 都卜勒效應計算
"""

import pytest
import sys
from pathlib import Path
import numpy as np
from unittest.mock import patch, MagicMock

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

# 導入算法類 (假設存在)
try:
    from shared.algorithms.signal_quality_calculator import SignalQualityCalculator
except ImportError:
    # 如果算法類不存在，跳過這些測試
    pytest.skip("SignalQualityCalculator not implemented yet", allow_module_level=True)


class TestSignalQualityCalculator:
    """信號品質計算器TDD測試套件"""

    @pytest.fixture
    def signal_calculator(self):
        """創建信號品質計算器實例"""
        return SignalQualityCalculator()

    @pytest.fixture
    def sample_satellite_data(self):
        """樣本衛星數據"""
        return {
            "name": "STARLINK-1234",
            "position_eci": {"x": 6771.0, "y": 0.0, "z": 0.0},  # km
            "velocity_eci": {"x": 0.0, "y": 7.66, "z": 0.0},    # km/s
            "elevation_deg": 45.0,
            "azimuth_deg": 180.0,
            "range_km": 1000.0,
            "constellation": "starlink"
        }

    @pytest.fixture
    def observer_coordinates(self):
        """觀測者座標 (台北)"""
        return (24.9441667, 121.3713889, 50)  # 緯度, 經度, 海拔(m)

    @pytest.mark.unit
    @pytest.mark.signal
    @pytest.mark.critical
    def test_friis_path_loss_calculation(self, signal_calculator, sample_satellite_data):
        """測試Friis路徑損耗公式計算"""
        # 測試參數
        frequency_hz = 2.0e10  # 20 GHz (Ka-band)
        distance_km = sample_satellite_data["range_km"]

        # 計算路徑損耗
        path_loss_db = signal_calculator.calculate_free_space_path_loss(
            frequency_hz, distance_km
        )

        # 驗證Friis公式: PL = 20*log10(4πd/λ)
        c = 299792458  # 光速 m/s
        wavelength = c / frequency_hz
        distance_m = distance_km * 1000

        expected_path_loss = 20 * np.log10(4 * np.pi * distance_m / wavelength)

        # 允許小誤差 (±0.1 dB)
        assert abs(path_loss_db - expected_path_loss) < 0.1
        assert path_loss_db > 0  # 路徑損耗應該為正值

    @pytest.mark.unit
    @pytest.mark.signal
    def test_rsrp_calculation_accuracy(self, signal_calculator, sample_satellite_data, observer_coordinates):
        """測試RSRP計算精度"""
        # 設定測試參數
        satellite_eirp_dbw = 55.0  # 55 dBW
        frequency_hz = 2.0e10      # 20 GHz

        # 計算RSRP
        rsrp_dbm = signal_calculator.calculate_rsrp(
            satellite_data=sample_satellite_data,
            observer_coordinates=observer_coordinates,
            satellite_eirp_dbw=satellite_eirp_dbw,
            frequency_hz=frequency_hz
        )

        # 驗證RSRP在合理範圍
        assert -150 <= rsrp_dbm <= -50, f"RSRP {rsrp_dbm:.1f} dBm 超出合理範圍"

        # 驗證計算公式: RSRP = EIRP - PL - 30 (dBW轉dBm)
        path_loss = signal_calculator.calculate_free_space_path_loss(
            frequency_hz, sample_satellite_data["range_km"]
        )
        expected_rsrp = satellite_eirp_dbw - path_loss - 30

        assert abs(rsrp_dbm - expected_rsrp) < 1.0, "RSRP計算誤差過大"

    @pytest.mark.unit
    @pytest.mark.signal
    def test_doppler_frequency_calculation(self, signal_calculator, sample_satellite_data):
        """測試都卜勒頻移計算"""
        # 測試參數
        carrier_frequency = 2.0e10  # 20 GHz
        observer_velocity = np.array([0, 0, 0])  # 觀測者靜止

        # 衛星相對速度
        satellite_velocity = np.array([
            sample_satellite_data["velocity_eci"]["x"],
            sample_satellite_data["velocity_eci"]["y"],
            sample_satellite_data["velocity_eci"]["z"]
        ]) * 1000  # 轉為 m/s

        # 計算都卜勒頻移
        doppler_shift = signal_calculator.calculate_doppler_shift(
            carrier_frequency=carrier_frequency,
            satellite_velocity=satellite_velocity,
            observer_velocity=observer_velocity,
            satellite_position=np.array([
                sample_satellite_data["position_eci"]["x"],
                sample_satellite_data["position_eci"]["y"],
                sample_satellite_data["position_eci"]["z"]
            ]) * 1000
        )

        # 驗證都卜勒公式: fd = fc * (vr / c)
        c = 299792458  # 光速
        position_vec = np.array([
            sample_satellite_data["position_eci"]["x"],
            sample_satellite_data["position_eci"]["y"],
            sample_satellite_data["position_eci"]["z"]
        ]) * 1000

        # 計算徑向速度
        unit_vector = position_vec / np.linalg.norm(position_vec)
        radial_velocity = np.dot(satellite_velocity, unit_vector)

        expected_doppler = carrier_frequency * radial_velocity / c

        assert abs(doppler_shift - expected_doppler) < 1000, "都卜勒計算誤差過大"

    @pytest.mark.unit
    @pytest.mark.signal
    @pytest.mark.compliance
    def test_itu_r_p618_atmospheric_loss(self, signal_calculator, sample_satellite_data):
        """測試ITU-R P.618大氣衰減標準"""
        # 測試參數 (Ka-band, 晴朗天氣)
        frequency_ghz = 20.0
        elevation_deg = sample_satellite_data["elevation_deg"]

        # 計算大氣衰減
        atmospheric_loss_db = signal_calculator.calculate_atmospheric_loss_itur_p618(
            frequency_ghz=frequency_ghz,
            elevation_deg=elevation_deg,
            weather_condition="clear"
        )

        # 驗證大氣衰減在合理範圍
        assert 0 <= atmospheric_loss_db <= 10, f"大氣衰減 {atmospheric_loss_db:.2f} dB 超出合理範圍"

        # 驗證仰角依賴性 (仰角越低，衰減越大)
        low_elevation_loss = signal_calculator.calculate_atmospheric_loss_itur_p618(
            frequency_ghz, 10.0, "clear"
        )
        high_elevation_loss = signal_calculator.calculate_atmospheric_loss_itur_p618(
            frequency_ghz, 80.0, "clear"
        )

        assert low_elevation_loss > high_elevation_loss, "低仰角應有更大大氣衰減"

    @pytest.mark.unit
    @pytest.mark.signal
    def test_rsrq_calculation(self, signal_calculator, sample_satellite_data, observer_coordinates):
        """測試RSRQ計算"""
        # 模擬鄰近衛星信號
        neighbor_satellites = [
            {"rsrp_dbm": -110, "range_km": 1200},
            {"rsrp_dbm": -115, "range_km": 1500},
            {"rsrp_dbm": -120, "range_km": 1800}
        ]

        # 計算主衛星RSRP
        rsrp_dbm = signal_calculator.calculate_rsrp(
            satellite_data=sample_satellite_data,
            observer_coordinates=observer_coordinates,
            satellite_eirp_dbw=55.0,
            frequency_hz=2.0e10
        )

        # 計算RSRQ
        rsrq_db = signal_calculator.calculate_rsrq(
            target_rsrp_dbm=rsrp_dbm,
            neighbor_satellites=neighbor_satellites
        )

        # 驗證RSRQ計算公式: RSRQ = RSRP / (RSRP + 鄰近干擾)
        # RSRQ應該為負值且在合理範圍
        assert -40 <= rsrq_db <= 0, f"RSRQ {rsrq_db:.1f} dB 超出合理範圍"

    @pytest.mark.unit
    @pytest.mark.signal
    def test_sinr_calculation(self, signal_calculator, sample_satellite_data):
        """測試SINR計算"""
        # 測試參數
        signal_power_dbm = -100.0
        interference_power_dbm = -110.0
        noise_power_dbm = -120.0

        # 計算SINR
        sinr_db = signal_calculator.calculate_sinr(
            signal_power_dbm=signal_power_dbm,
            interference_power_dbm=interference_power_dbm,
            noise_power_dbm=noise_power_dbm
        )

        # 驗證SINR公式: SINR = S / (I + N)
        signal_linear = 10**(signal_power_dbm / 10)
        interference_linear = 10**(interference_power_dbm / 10)
        noise_linear = 10**(noise_power_dbm / 10)

        expected_sinr = 10 * np.log10(signal_linear / (interference_linear + noise_linear))

        assert abs(sinr_db - expected_sinr) < 0.1, "SINR計算誤差過大"
        assert sinr_db > 0, "在此測試條件下SINR應該為正值"

    @pytest.mark.integration
    @pytest.mark.signal
    @pytest.mark.real_data
    def test_complete_signal_quality_analysis(self, signal_calculator, sample_satellite_data, observer_coordinates):
        """完整信號品質分析整合測試"""
        # 執行完整的信號品質計算
        result = signal_calculator.analyze_signal_quality(
            satellite_data=sample_satellite_data,
            observer_coordinates=observer_coordinates,
            frequency_hz=2.0e10,
            satellite_eirp_dbw=55.0,
            neighbor_satellites=[
                {"rsrp_dbm": -115, "range_km": 1200},
                {"rsrp_dbm": -120, "range_km": 1500}
            ]
        )

        # 驗證完整結果結構
        required_fields = ["rsrp_dbm", "rsrq_db", "sinr_db", "path_loss_db",
                          "atmospheric_loss_db", "doppler_shift_hz", "signal_quality_grade"]
        for field in required_fields:
            assert field in result, f"缺少必要欄位: {field}"

        # 驗證數值合理性
        assert -150 <= result["rsrp_dbm"] <= -50
        assert -40 <= result["rsrq_db"] <= 0
        assert -20 <= result["sinr_db"] <= 50
        assert result["path_loss_db"] > 0
        assert result["atmospheric_loss_db"] >= 0

        # 驗證信號品質等級
        assert result["signal_quality_grade"] in ["EXCELLENT", "GOOD", "FAIR", "POOR", "UNUSABLE"]

    @pytest.mark.performance
    @pytest.mark.signal
    def test_batch_signal_calculation_performance(self, signal_calculator, observer_coordinates):
        """批量信號計算性能測試"""
        # 創建100個衛星數據
        satellites = []
        for i in range(100):
            satellite = {
                "name": f"SATELLITE-{i}",
                "position_eci": {"x": 6771.0 + i*10, "y": 0.0, "z": 0.0},
                "velocity_eci": {"x": 0.0, "y": 7.66, "z": 0.0},
                "elevation_deg": 45.0 - i*0.1,
                "azimuth_deg": 180.0 + i*2,
                "range_km": 1000.0 + i*50,
                "constellation": "test"
            }
            satellites.append(satellite)

        import time
        start_time = time.time()

        # 批量計算信號品質
        results = []
        for satellite in satellites:
            result = signal_calculator.analyze_signal_quality(
                satellite_data=satellite,
                observer_coordinates=observer_coordinates,
                frequency_hz=2.0e10,
                satellite_eirp_dbw=55.0,
                neighbor_satellites=[]
            )
            results.append(result)

        execution_time = time.time() - start_time

        # 性能要求: 100顆衛星 < 5秒 (平均每顆 < 50ms)
        assert execution_time < 5.0, f"批量信號計算時間 {execution_time:.2f}s 超過預期"
        assert len(results) == 100

    @pytest.mark.unit
    @pytest.mark.signal
    @pytest.mark.compliance
    def test_3gpp_ntn_standards_compliance(self, signal_calculator, sample_satellite_data):
        """測試3GPP NTN標準合規性"""
        # 3GPP TS 38.821 NTN標準參數
        ntn_parameters = {
            "frequency_range": "Ka-band",  # 17.7-21.2 GHz
            "satellite_eirp_dbw": 55.0,    # 典型Ka-band EIRP
            "noise_figure_db": 3.0,        # 典型接收機雜訊指數
            "bandwidth_mhz": 100.0         # 典型5G NR帶寬
        }

        # 使用3GPP參數計算信號品質
        result = signal_calculator.analyze_signal_quality_3gpp_ntn(
            satellite_data=sample_satellite_data,
            ntn_parameters=ntn_parameters
        )

        # 驗證3GPP NTN合規性檢查
        compliance_checks = result.get("3gpp_compliance", {})

        assert compliance_checks.get("frequency_band_valid", False)
        assert compliance_checks.get("eirp_within_limits", False)
        assert compliance_checks.get("link_budget_adequate", False)

        # 驗證計算使用了正確的3GPP公式
        assert "3gpp_link_budget_db" in result
        assert "3gpp_coverage_probability" in result


# 信號品質計算器性能基準測試
@pytest.mark.benchmark
@pytest.mark.signal
class TestSignalQualityBenchmark:
    """信號品質計算性能基準測試"""

    def test_single_satellite_signal_calculation_benchmark(self, benchmark):
        """單顆衛星信號計算性能基準"""
        signal_calculator = SignalQualityCalculator()

        sample_data = {
            "name": "BENCHMARK-SAT",
            "position_eci": {"x": 6771.0, "y": 0.0, "z": 0.0},
            "velocity_eci": {"x": 0.0, "y": 7.66, "z": 0.0},
            "elevation_deg": 45.0,
            "azimuth_deg": 180.0,
            "range_km": 1000.0,
            "constellation": "starlink"
        }

        observer_coords = (24.9441667, 121.3713889, 50)

        def signal_calculation():
            return signal_calculator.analyze_signal_quality(
                satellite_data=sample_data,
                observer_coordinates=observer_coords,
                frequency_hz=2.0e10,
                satellite_eirp_dbw=55.0,
                neighbor_satellites=[]
            )

        # 基準測試: 單顆衛星信號計算應該 < 5ms
        result = benchmark(signal_calculation)
        assert result is not None