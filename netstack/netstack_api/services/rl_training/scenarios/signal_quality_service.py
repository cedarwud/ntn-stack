"""
Phase 2.2 統一信號品質預測模型服務

整合 Phase 2.1 的信號品質預測功能，添加先進的預測算法、場景適應性和多維度分析
支援 RSRP、RSRQ、SINR 的精確預測和趨勢分析
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json

from ...simworld_tle_bridge_service import SimWorldTLEBridgeService
from ..environments.leo_satellite_environment import (
    LEOSatelliteEnvironment,
    SatelliteState,
)

logger = logging.getLogger(__name__)


class SignalModel(Enum):
    """信號模型類型"""

    BASIC = "basic"
    PHYSICAL = "physical"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


class EnvironmentScenario(Enum):
    """環境場景類型"""

    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    MARITIME = "maritime"
    AVIATION = "aviation"


@dataclass
class SignalQualityPrediction:
    """信號品質預測結果"""

    satellite_id: str
    timestamp: datetime

    # 主要信號指標
    rsrp_dbm: float
    rsrq_db: float
    sinr_db: float

    # 置信度和變異性
    prediction_confidence: float
    rsrp_std: float
    rsrq_std: float
    sinr_std: float

    # 趨勢分析
    rsrp_trend: str  # "improving", "degrading", "stable"
    quality_trend_rate: float  # dB/s

    # 預測視窗
    prediction_horizon_s: float
    next_update_time: datetime

    # 詳細分析
    path_loss_db: float
    atmospheric_attenuation_db: float
    shadow_fading_db: float
    interference_level: float

    # 場景因子
    scenario_type: str
    mobility_factor: float
    weather_impact: float


@dataclass
class SignalQualityMetrics:
    """信號品質指標集合"""

    current: SignalQualityPrediction
    predicted_5s: SignalQualityPrediction
    predicted_30s: SignalQualityPrediction
    predicted_60s: SignalQualityPrediction

    # 歷史分析
    improvement_potential: float
    degradation_risk: float
    stability_score: float


class EnhancedSignalQualityService:
    """
    增強信號品質預測服務

    整合多種預測模型，提供精確的信號品質預測和分析
    """

    def __init__(
        self,
        tle_bridge_service: SimWorldTLEBridgeService,
        leo_environment: LEOSatelliteEnvironment,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化信號品質服務

        Args:
            tle_bridge_service: SimWorld TLE 橋接服務
            leo_environment: LEO 衛星環境
            config: 配置參數
        """
        self.tle_bridge = tle_bridge_service
        self.leo_env = leo_environment
        self.config = config or {}

        # 預測配置
        self.signal_model = SignalModel(self.config.get("signal_model", "physical"))
        self.prediction_horizons = self.config.get(
            "prediction_horizons", [5, 30, 60]
        )  # 秒
        self.update_interval_s = self.config.get("update_interval_s", 1.0)

        # 物理模型參數
        self.frequency_hz = self.config.get("frequency_hz", 20e9)  # 20 GHz
        self.satellite_eirp_dbw = self.config.get("satellite_eirp_dbw", 55.0)
        self.bandwidth_hz = self.config.get("bandwidth_hz", 20e6)  # 20 MHz

        # 場景配置
        self.scenario_configs = {
            EnvironmentScenario.URBAN: {
                "building_loss_db": 5.0,
                "multipath_factor": 1.5,
                "interference_level": 0.3,
                "mobility_factor": 1.0,
            },
            EnvironmentScenario.SUBURBAN: {
                "building_loss_db": 2.0,
                "multipath_factor": 1.2,
                "interference_level": 0.2,
                "mobility_factor": 1.2,
            },
            EnvironmentScenario.RURAL: {
                "building_loss_db": 0.5,
                "multipath_factor": 1.0,
                "interference_level": 0.1,
                "mobility_factor": 1.5,
            },
            EnvironmentScenario.MARITIME: {
                "building_loss_db": 0.0,
                "multipath_factor": 0.8,
                "interference_level": 0.05,
                "mobility_factor": 2.0,
            },
            EnvironmentScenario.AVIATION: {
                "building_loss_db": 0.0,
                "multipath_factor": 0.5,
                "interference_level": 0.02,
                "mobility_factor": 3.0,
            },
        }

        # 預測歷史和緩存
        self.prediction_cache: Dict[str, SignalQualityMetrics] = {}
        self.prediction_history: Dict[str, List[SignalQualityPrediction]] = {}

        # 性能統計
        self.predictions_made = 0
        self.prediction_accuracy = 0.0
        self.cache_hit_rate = 0.0

        logger.info("增強信號品質預測服務初始化完成")

    async def predict_signal_quality(
        self,
        satellite: SatelliteState,
        ue_position: Dict[str, float],
        scenario: EnvironmentScenario = EnvironmentScenario.URBAN,
        time_horizons: Optional[List[int]] = None,
    ) -> SignalQualityMetrics:
        """
        預測信號品質指標

        Args:
            satellite: 衛星狀態
            ue_position: 用戶設備位置
            scenario: 環境場景
            time_horizons: 預測時間範圍（秒）

        Returns:
            SignalQualityMetrics: 完整的信號品質預測
        """
        satellite_id = str(satellite.id)
        current_time = datetime.now()

        # 檢查緩存
        if self._is_cache_valid(satellite_id, current_time):
            self.cache_hit_rate = (self.cache_hit_rate * self.predictions_made + 1) / (
                self.predictions_made + 1
            )
            return self.prediction_cache[satellite_id]

        try:
            # 當前信號品質
            current_prediction = await self._predict_single_timepoint(
                satellite, ue_position, scenario, current_time, 0
            )

            # 未來時間點預測
            future_predictions = {}
            horizons = time_horizons or self.prediction_horizons

            for horizon in horizons:
                future_prediction = await self._predict_single_timepoint(
                    satellite, ue_position, scenario, current_time, horizon
                )
                future_predictions[f"predicted_{horizon}s"] = future_prediction

            # 構建完整指標
            metrics = SignalQualityMetrics(
                current=current_prediction,
                predicted_5s=future_predictions.get("predicted_5s", current_prediction),
                predicted_30s=future_predictions.get(
                    "predicted_30s", current_prediction
                ),
                predicted_60s=future_predictions.get(
                    "predicted_60s", current_prediction
                ),
                improvement_potential=self._calculate_improvement_potential(
                    current_prediction, list(future_predictions.values())
                ),
                degradation_risk=self._calculate_degradation_risk(
                    current_prediction, list(future_predictions.values())
                ),
                stability_score=self._calculate_stability_score(satellite_id),
            )

            # 更新緩存和歷史
            self.prediction_cache[satellite_id] = metrics
            self._update_prediction_history(satellite_id, current_prediction)

            self.predictions_made += 1

            logger.debug(
                f"信號品質預測完成 - 衛星: {satellite_id}, RSRP: {current_prediction.rsrp_dbm:.1f}dBm"
            )

            return metrics

        except Exception as e:
            logger.error(f"信號品質預測失敗: {e}")
            # 返回基礎預測
            return await self._get_fallback_prediction(satellite, ue_position)

    async def _predict_single_timepoint(
        self,
        satellite: SatelliteState,
        ue_position: Dict[str, float],
        scenario: EnvironmentScenario,
        base_time: datetime,
        time_offset_s: float,
    ) -> SignalQualityPrediction:
        """預測單個時間點的信號品質"""

        prediction_time = base_time + timedelta(seconds=time_offset_s)
        satellite_id = str(satellite.id)

        # 獲取衛星位置（當前或預測）
        if time_offset_s == 0:
            satellite_position = satellite.position
        else:
            # 使用軌道預測獲取未來位置
            satellite_position = await self._predict_satellite_position(
                satellite, prediction_time
            )

        # 計算距離和仰角
        distance_km = satellite_position.get("range", 1000)
        elevation_deg = satellite_position.get("elevation", 30)
        azimuth_deg = satellite_position.get("azimuth", 0)

        # 物理信號傳播計算
        signal_components = self._calculate_signal_components(
            distance_km, elevation_deg, scenario, ue_position
        )

        # 主要信號指標
        rsrp = self._calculate_rsrp(signal_components)
        rsrq = self._calculate_rsrq(signal_components, scenario)
        sinr = self._calculate_sinr(signal_components, scenario)

        # 添加時間相關的變化
        if time_offset_s > 0:
            rsrp, rsrq, sinr = self._apply_temporal_effects(
                rsrp, rsrq, sinr, satellite, time_offset_s
            )

        # 預測置信度
        confidence = self._calculate_prediction_confidence(satellite_id, time_offset_s)

        # 趨勢分析
        trend, trend_rate = self._analyze_signal_trend(satellite_id, rsrp)

        # 構建預測結果
        prediction = SignalQualityPrediction(
            satellite_id=satellite_id,
            timestamp=prediction_time,
            rsrp_dbm=rsrp,
            rsrq_db=rsrq,
            sinr_db=sinr,
            prediction_confidence=confidence,
            rsrp_std=self._calculate_prediction_uncertainty(confidence, "rsrp"),
            rsrq_std=self._calculate_prediction_uncertainty(confidence, "rsrq"),
            sinr_std=self._calculate_prediction_uncertainty(confidence, "sinr"),
            rsrp_trend=trend,
            quality_trend_rate=trend_rate,
            prediction_horizon_s=time_offset_s,
            next_update_time=prediction_time
            + timedelta(seconds=self.update_interval_s),
            path_loss_db=signal_components["path_loss"],
            atmospheric_attenuation_db=signal_components["atmospheric_loss"],
            shadow_fading_db=signal_components["shadow_fading"],
            interference_level=signal_components["interference"],
            scenario_type=scenario.value,
            mobility_factor=self.scenario_configs[scenario]["mobility_factor"],
            weather_impact=0.0,  # 簡化實現
        )

        return prediction

    def _calculate_signal_components(
        self,
        distance_km: float,
        elevation_deg: float,
        scenario: EnvironmentScenario,
        ue_position: Dict[str, float],
    ) -> Dict[str, float]:
        """計算信號傳播組件"""

        # 自由空間路徑損耗
        path_loss = (
            20 * np.log10(distance_km * 1000)
            + 20 * np.log10(self.frequency_hz)
            + 20 * np.log10(4 * np.pi / 3e8)
        )

        # 大氣衰減（基於仰角）
        elevation_rad = np.radians(elevation_deg)
        atmospheric_loss = 0.5 / np.sin(elevation_rad) if elevation_deg > 5 else 10.0

        # 場景特定損耗
        scenario_config = self.scenario_configs[scenario]
        building_loss = scenario_config["building_loss_db"]

        # 陰影衰落（對數正態分布）
        shadow_fading = np.random.lognormal(0, 0.5)

        # 多徑衰落
        multipath_factor = scenario_config["multipath_factor"]
        multipath_loss = np.random.exponential(2.0) * multipath_factor

        # 干擾水平
        interference_level = scenario_config["interference_level"]

        return {
            "path_loss": path_loss,
            "atmospheric_loss": atmospheric_loss,
            "building_loss": building_loss,
            "shadow_fading": shadow_fading,
            "multipath_loss": multipath_loss,
            "interference": interference_level,
        }

    def _calculate_rsrp(self, signal_components: Dict[str, float]) -> float:
        """計算 RSRP (參考信號接收功率)"""

        rsrp = (
            self.satellite_eirp_dbw
            - signal_components["path_loss"]
            - signal_components["atmospheric_loss"]
            - signal_components["building_loss"]
            - signal_components["shadow_fading"]
            - signal_components["multipath_loss"]
        )

        return float(rsrp)

    def _calculate_rsrq(
        self, signal_components: Dict[str, float], scenario: EnvironmentScenario
    ) -> float:
        """計算 RSRQ (參考信號接收品質)"""

        # RSRQ = RSRP / (RSSI)，其中 RSSI 包含干擾
        rsrp = self._calculate_rsrp(signal_components)
        interference_power = 10 * np.log10(signal_components["interference"] + 0.01)

        rsrq = rsrp - interference_power - 5.0  # 基準偏移

        return float(rsrq)

    def _calculate_sinr(
        self, signal_components: Dict[str, float], scenario: EnvironmentScenario
    ) -> float:
        """計算 SINR (信號干擾雜訊比)"""

        # 信號功率
        signal_power = self._calculate_rsrp(signal_components)

        # 雜訊功率
        thermal_noise = -174 + 10 * np.log10(self.bandwidth_hz)

        # 干擾功率
        interference_power = thermal_noise + 10 * np.log10(
            signal_components["interference"] + 0.1
        )

        # SINR 計算
        total_noise_interference = 10 * np.log10(
            10 ** (thermal_noise / 10) + 10 ** (interference_power / 10)
        )

        sinr = signal_power - total_noise_interference

        return float(sinr)

    async def _predict_satellite_position(
        self, satellite: SatelliteState, future_time: datetime
    ) -> Dict[str, float]:
        """預測衛星未來位置"""

        try:
            # 使用 TLE 橋接服務進行軌道預測
            satellite_id = str(satellite.id)

            # 簡化的位置預測（基於當前速度和方向）
            current_position = satellite.position
            time_diff_s = (future_time - datetime.now()).total_seconds()

            # 基於軌道運動的簡單預測
            # 在實際實現中，這裡會使用完整的軌道動力學
            current_elevation = current_position.get("elevation", 30)
            current_azimuth = current_position.get("azimuth", 0)
            current_range = current_position.get("range", 1000)

            # 簡化的角速度估算（LEO 衛星約為 1 度/分鐘）
            angular_velocity_deg_per_s = 1.0 / 60.0

            # 預測位置
            predicted_azimuth = (
                current_azimuth + angular_velocity_deg_per_s * time_diff_s
            )
            predicted_elevation = current_elevation  # 簡化假設仰角緩慢變化
            predicted_range = current_range  # 簡化假設距離相對穩定

            return {
                "elevation": predicted_elevation,
                "azimuth": predicted_azimuth % 360,
                "range": predicted_range,
                "latitude": current_position.get("latitude", 0),
                "longitude": current_position.get("longitude", 0),
                "altitude": current_position.get("altitude", 550),
            }

        except Exception as e:
            logger.warning(f"預測衛星位置失敗: {e}")
            return satellite.position

    def _apply_temporal_effects(
        self,
        rsrp: float,
        rsrq: float,
        sinr: float,
        satellite: SatelliteState,
        time_offset_s: float,
    ) -> Tuple[float, float, float]:
        """應用時間相關效應"""

        # 基於歷史趨勢的時間演化
        satellite_id = str(satellite.id)

        if satellite_id in self.prediction_history:
            history = self.prediction_history[satellite_id][-5:]  # 最近5個預測

            if len(history) >= 2:
                # 計算歷史趨勢
                recent_rsrp = [h.rsrp_dbm for h in history]
                rsrp_trend = (recent_rsrp[-1] - recent_rsrp[0]) / len(recent_rsrp)

                # 應用趨勢到未來預測
                rsrp_future = rsrp + rsrp_trend * time_offset_s
                rsrq_future = rsrq + rsrp_trend * 0.5 * time_offset_s  # RSRQ 變化較小
                sinr_future = (
                    sinr + rsrp_trend * 0.7 * time_offset_s
                )  # SINR 與 RSRP 相關

                return rsrp_future, rsrq_future, sinr_future

        # 添加隨機時間變化
        time_noise_factor = min(time_offset_s / 60.0, 1.0)  # 1分鐘內的變化
        rsrp += np.random.normal(0, 1.0 * time_noise_factor)
        rsrq += np.random.normal(0, 0.5 * time_noise_factor)
        sinr += np.random.normal(0, 0.8 * time_noise_factor)

        return rsrp, rsrq, sinr

    def _calculate_prediction_confidence(
        self, satellite_id: str, time_offset_s: float
    ) -> float:
        """計算預測置信度"""

        # 基礎置信度隨時間衰減
        base_confidence = 0.95
        time_decay = min(time_offset_s / 300.0, 0.5)  # 5分鐘內最多衰減50%

        confidence = base_confidence * (1.0 - time_decay)

        # 基於歷史數據調整置信度
        if satellite_id in self.prediction_history:
            history_length = len(self.prediction_history[satellite_id])
            history_bonus = min(history_length / 10.0, 0.1)  # 最多10%提升
            confidence += history_bonus

        return np.clip(confidence, 0.1, 1.0)

    def _analyze_signal_trend(
        self, satellite_id: str, current_rsrp: float
    ) -> Tuple[str, float]:
        """分析信號趨勢"""

        if satellite_id not in self.prediction_history:
            return "stable", 0.0

        history = self.prediction_history[satellite_id][-5:]
        if len(history) < 2:
            return "stable", 0.0

        # 計算 RSRP 變化率
        rsrp_values = [h.rsrp_dbm for h in history] + [current_rsrp]
        time_diffs = [
            (h.timestamp - history[0].timestamp).total_seconds() for h in history[1:]
        ] + [0]

        if len(rsrp_values) >= 3:
            # 線性回歸計算趨勢
            x = np.array(range(len(rsrp_values)))
            y = np.array(rsrp_values)

            # 簡單線性擬合
            slope = np.polyfit(x, y, 1)[0]

            if slope > 0.5:
                return "improving", slope
            elif slope < -0.5:
                return "degrading", slope
            else:
                return "stable", slope

        return "stable", 0.0

    def _calculate_prediction_uncertainty(
        self, confidence: float, signal_type: str
    ) -> float:
        """計算預測不確定性"""

        # 基於置信度的不確定性映射
        uncertainty_ranges = {
            "rsrp": (0.5, 5.0),  # dB
            "rsrq": (0.2, 3.0),  # dB
            "sinr": (0.3, 4.0),  # dB
        }

        min_std, max_std = uncertainty_ranges.get(signal_type, (0.5, 3.0))

        # 置信度越低，不確定性越高
        std = max_std - (confidence * (max_std - min_std))

        return float(std)

    def _calculate_improvement_potential(
        self,
        current: SignalQualityPrediction,
        future_predictions: List[SignalQualityPrediction],
    ) -> float:
        """計算信號改善潛力"""

        if not future_predictions:
            return 0.0

        max_future_rsrp = max(p.rsrp_dbm for p in future_predictions)
        improvement = max_future_rsrp - current.rsrp_dbm

        # 正規化到 0-100 範圍
        improvement_potential = np.clip(improvement * 10, 0, 100)

        return float(improvement_potential)

    def _calculate_degradation_risk(
        self,
        current: SignalQualityPrediction,
        future_predictions: List[SignalQualityPrediction],
    ) -> float:
        """計算信號劣化風險"""

        if not future_predictions:
            return 50.0

        min_future_rsrp = min(p.rsrp_dbm for p in future_predictions)
        degradation = current.rsrp_dbm - min_future_rsrp

        # 風險評估
        if degradation > 5.0:
            risk = 90.0
        elif degradation > 2.0:
            risk = 70.0
        elif degradation > 0.0:
            risk = 50.0
        else:
            risk = 20.0

        return float(risk)

    def _calculate_stability_score(self, satellite_id: str) -> float:
        """計算穩定性評分"""

        if satellite_id not in self.prediction_history:
            return 50.0

        history = self.prediction_history[satellite_id][-10:]
        if len(history) < 3:
            return 60.0

        # 計算信號指標的變異性
        rsrp_values = [h.rsrp_dbm for h in history]
        rsrp_std = np.std(rsrp_values)

        # 穩定性評分（標準差越小越穩定）
        stability = max(0.0, 100.0 - rsrp_std * 10)

        return float(stability)

    def _is_cache_valid(self, satellite_id: str, current_time: datetime) -> bool:
        """檢查緩存是否有效"""

        if satellite_id not in self.prediction_cache:
            return False

        cached_metrics = self.prediction_cache[satellite_id]
        time_diff = (current_time - cached_metrics.current.timestamp).total_seconds()

        return time_diff < self.update_interval_s

    def _update_prediction_history(
        self, satellite_id: str, prediction: SignalQualityPrediction
    ):
        """更新預測歷史"""

        if satellite_id not in self.prediction_history:
            self.prediction_history[satellite_id] = []

        self.prediction_history[satellite_id].append(prediction)

        # 保持歷史記錄在合理範圍內
        if len(self.prediction_history[satellite_id]) > 50:
            self.prediction_history[satellite_id] = self.prediction_history[
                satellite_id
            ][-25:]

    async def _get_fallback_prediction(
        self, satellite: SatelliteState, ue_position: Dict[str, float]
    ) -> SignalQualityMetrics:
        """獲取備用預測"""

        # 使用 LEO 環境的基礎預測方法
        try:
            basic_signal = await self.leo_env._predict_signal_quality(
                satellite.position
            )

            current_prediction = SignalQualityPrediction(
                satellite_id=str(satellite.id),
                timestamp=datetime.now(),
                rsrp_dbm=basic_signal["rsrp"],
                rsrq_db=basic_signal["rsrq"],
                sinr_db=basic_signal["sinr"],
                prediction_confidence=0.7,
                rsrp_std=2.0,
                rsrq_std=1.0,
                sinr_std=1.5,
                rsrp_trend="stable",
                quality_trend_rate=0.0,
                prediction_horizon_s=0.0,
                next_update_time=datetime.now()
                + timedelta(seconds=self.update_interval_s),
                path_loss_db=120.0,
                atmospheric_attenuation_db=2.0,
                shadow_fading_db=1.0,
                interference_level=0.2,
                scenario_type="urban",
                mobility_factor=1.0,
                weather_impact=0.0,
            )

            return SignalQualityMetrics(
                current=current_prediction,
                predicted_5s=current_prediction,
                predicted_30s=current_prediction,
                predicted_60s=current_prediction,
                improvement_potential=20.0,
                degradation_risk=30.0,
                stability_score=50.0,
            )

        except Exception as e:
            logger.error(f"備用預測也失敗: {e}")
            raise

    def get_service_statistics(self) -> Dict[str, Any]:
        """獲取服務統計信息"""

        return {
            "predictions_made": self.predictions_made,
            "prediction_accuracy": self.prediction_accuracy,
            "cache_hit_rate": self.cache_hit_rate,
            "active_satellites": len(self.prediction_cache),
            "history_length": sum(len(h) for h in self.prediction_history.values()),
            "signal_model": self.signal_model.value,
            "supported_scenarios": [s.value for s in EnvironmentScenario],
            "prediction_horizons": self.prediction_horizons,
            "update_interval_s": self.update_interval_s,
        }

    async def cleanup_old_data(self, max_age_hours: int = 2):
        """清理舊的預測數據"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # 清理預測歷史
        for satellite_id in list(self.prediction_history.keys()):
            initial_count = len(self.prediction_history[satellite_id])
            self.prediction_history[satellite_id] = [
                p
                for p in self.prediction_history[satellite_id]
                if p.timestamp > cutoff_time
            ]

            # 如果沒有近期數據，移除整個記錄
            if not self.prediction_history[satellite_id]:
                del self.prediction_history[satellite_id]

        # 清理過期緩存
        for satellite_id in list(self.prediction_cache.keys()):
            metrics = self.prediction_cache[satellite_id]
            if metrics.current.timestamp < cutoff_time:
                del self.prediction_cache[satellite_id]

        logger.info(f"清理了過期的預測數據（超過 {max_age_hours} 小時）")
