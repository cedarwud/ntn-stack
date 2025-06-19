"""
Fine-Grained Synchronized Algorithm Implementation
實作 IEEE INFOCOM 2024 論文中的核心同步演算法
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import math
import logging
from dataclasses import dataclass

from ..models.simple_handover_models import (
    HandoverPredictionRecord,
    BinarySearchIteration,
)
from ...satellite.services.orbit_service import OrbitService
from .constrained_satellite_access_service import ConstrainedSatelliteAccessService
from .weather_integrated_prediction_service import WeatherIntegratedPredictionService
from .prediction_accuracy_optimizer import PredictionAccuracyOptimizer

logger = logging.getLogger(__name__)


@dataclass
class SatelliteCandidate:
    """衛星候選者資料結構"""

    satellite_id: str
    name: str
    elevation: float
    azimuth: float
    distance: float
    signal_strength: float
    score: float


@dataclass
class TwoPointPredictionResult:
    """二點預測結果"""

    current_satellite: str  # AT
    predicted_satellite: str  # AT+Δt
    current_time: float
    future_time: float
    handover_needed: bool
    confidence: float


class FineGrainedSyncService:
    """
    Fine-Grained Synchronized Algorithm 核心服務
    實現二點預測機制和 Binary Search Refinement
    """

    def __init__(self, delta_t: int = 10):
        self.delta_t = delta_t  # 預測時間間隔（秒）
        self.orbit_service = OrbitService()
        self.constrained_access_service = ConstrainedSatelliteAccessService()
        self.weather_prediction_service = WeatherIntegratedPredictionService()
        self.accuracy_optimizer = PredictionAccuracyOptimizer()  # 準確率優化器
        self.prediction_cache: Dict[str, HandoverPredictionRecord] = {}
        self.min_elevation_threshold = 10.0  # 最低仰角門檻（度）
        self.precision_threshold = 0.1  # Binary search 精度門檻（秒）
        self.max_iterations = 15  # 最大迭代次數
        self.weather_integration_enabled = True  # 啟用天氣整合
        self.accuracy_optimization_enabled = True  # 啟用準確率優化

    async def two_point_prediction(
        self, ue_id: str, ue_position: Tuple[float, float, float]
    ) -> TwoPointPredictionResult:
        """
        實作二點預測方法
        返回: 當前和預測時段的最佳接入衛星
        """
        try:
            current_time = time.time()

            # 使用優化器推薦的 delta_t
            if self.accuracy_optimization_enabled:
                optimized_delta_t = self.accuracy_optimizer.get_recommended_delta_t()
                if optimized_delta_t != self.delta_t:
                    logger.info(
                        f"使用優化 delta_t: {self.delta_t} -> {optimized_delta_t}"
                    )
                    self.delta_t = optimized_delta_t

            future_time = current_time + self.delta_t

            logger.info(
                f"執行二點預測 - UE: {ue_id}, T: {current_time}, T+Δt: {future_time}"
            )

            # 計算當前時間的最佳衛星 (AT)
            current_satellite = await self.calculate_best_satellite(
                ue_position, current_time
            )

            # 計算未來時間的最佳衛星 (AT+Δt)
            future_satellite = await self.calculate_best_satellite(
                ue_position, future_time
            )

            # 判斷是否需要換手
            handover_needed = (
                current_satellite.satellite_id != future_satellite.satellite_id
            )

            # 計算預測信賴水準
            confidence = self.calculate_prediction_confidence(
                current_satellite, future_satellite
            )

            result = TwoPointPredictionResult(
                current_satellite=current_satellite.satellite_id,
                predicted_satellite=future_satellite.satellite_id,
                current_time=current_time,
                future_time=future_time,
                handover_needed=handover_needed,
                confidence=confidence,
            )

            logger.info(
                f"二點預測完成 - 當前衛星: {current_satellite.satellite_id}, "
                f"預測衛星: {future_satellite.satellite_id}, 需要換手: {handover_needed}"
            )

            return result

        except Exception as e:
            logger.error(f"二點預測失敗: {e}")
            raise

    def _generate_mock_visible_satellites(
        self, ue_position: Tuple[float, float, float], timestamp: float
    ) -> List[Any]:
        """
        生成模擬的可見衛星數據 (用於開發階段)
        在生產環境中應替換為真實的軌道計算
        """
        import random
        import math

        # 基於時間和位置生成偽隨機但一致的衛星
        random.seed(
            int(timestamp) + int(ue_position[0] * 1000) + int(ue_position[1] * 1000)
        )

        satellites = []
        satellite_names = [
            "ONEWEB-0012",
            "ONEWEB-0010",
            "ONEWEB-0008",
            "ONEWEB-0007",
            "ONEWEB-0006",
            "ONEWEB-0001",
            "ONEWEB-0002",
            "ONEWEB-0003",
            "ONEWEB-0004",
            "ONEWEB-0005",
        ]

        # 生成 5-8 顆可見衛星
        num_satellites = random.randint(5, 8)
        selected_satellites = random.sample(
            satellite_names, min(num_satellites, len(satellite_names))
        )

        for i, sat_name in enumerate(selected_satellites):
            # 模擬衛星的類型
            class MockSatellite:
                def __init__(
                    self,
                    name: str,
                    norad_id: str,
                    elevation: float,
                    azimuth: float,
                    distance: float,
                ):
                    self.name = name
                    self.norad_id = norad_id
                    self.elevation_deg = elevation
                    self.azimuth_deg = azimuth
                    self.distance_km = distance
                    self.velocity_km_s = random.uniform(6.8, 7.8)  # LEO 衛星典型速度

            # 生成合理的衛星位置參數
            elevation = random.uniform(self.min_elevation_threshold, 85.0)
            azimuth = random.uniform(0, 360)
            distance = random.uniform(500, 1200)  # LEO 距離範圍

            mock_sat = MockSatellite(
                name=sat_name,
                norad_id=f"{40000 + i + int(timestamp % 1000)}",
                elevation=elevation,
                azimuth=azimuth,
                distance=distance,
            )

            satellites.append(mock_sat)

        # 按仰角排序（仰角越高，信號質量通常越好）
        satellites.sort(key=lambda s: s.elevation_deg, reverse=True)

        logger.info(f"生成了 {len(satellites)} 顆模擬可見衛星 (timestamp: {timestamp})")
        return satellites

    async def _fallback_satellite_selection(
        self, visible_satellites: List[Any], ue_position: Tuple[float, float, float]
    ) -> SatelliteCandidate:
        """
        回退衛星選擇策略
        當約束式選擇失敗時使用的簡單選擇方法
        """
        try:
            candidates = []

            for sat in visible_satellites:
                # 計算簡單評分
                score = await self.calculate_satellite_score(
                    sat, ue_position, time.time()
                )

                candidate = SatelliteCandidate(
                    satellite_id=sat.norad_id,
                    name=sat.name,
                    elevation=sat.elevation_deg,
                    azimuth=sat.azimuth_deg,
                    distance=sat.distance_km,
                    signal_strength=await self.estimate_signal_strength(
                        sat, ue_position
                    ),
                    score=score,
                )
                candidates.append(candidate)

            # 選擇評分最高的衛星
            best_satellite = max(candidates, key=lambda x: x.score)

            logger.info(
                f"回退策略選擇最佳衛星: {best_satellite.name} (評分: {best_satellite.score:.2f})"
            )

            return best_satellite

        except Exception as e:
            logger.error(f"回退策略失敗: {e}")
            # 最後的保險策略：選擇第一個可用衛星
            if visible_satellites:
                sat = visible_satellites[0]
                return SatelliteCandidate(
                    satellite_id=sat.norad_id,
                    name=sat.name,
                    elevation=sat.elevation_deg,
                    azimuth=sat.azimuth_deg,
                    distance=sat.distance_km,
                    signal_strength=-70.0,  # 假設值
                    score=0.5,  # 低評分
                )
            else:
                raise ValueError("沒有可用的衛星")

    async def calculate_best_satellite(
        self, ue_position: Tuple[float, float, float], timestamp: float
    ) -> SatelliteCandidate:
        """
        計算指定時間點的最佳衛星
        使用多因子評分機制選擇最佳衛星
        """
        try:
            # 獲取可見衛星數據
            visible_satellites = self._generate_mock_visible_satellites(
                ue_position, timestamp
            )

            if not visible_satellites:
                raise ValueError(f"在時間 {timestamp} 沒有可見衛星")

            # 轉換為約束服務需要的格式
            satellite_data = []
            for sat in visible_satellites:
                satellite_data.append(
                    {
                        "norad_id": sat.norad_id,
                        "name": sat.name,
                        "elevation_deg": sat.elevation_deg,
                        "azimuth_deg": sat.azimuth_deg,
                        "distance_km": sat.distance_km,
                        "velocity_km_s": sat.velocity_km_s,
                    }
                )

            # 使用約束式衛星接入策略選擇最佳衛星
            selected_candidate = (
                await self.constrained_access_service.select_optimal_satellite(
                    ue_id=f"temp_ue_{int(timestamp)}",  # 臨時 UE ID
                    ue_position=ue_position,
                    available_satellites=satellite_data,
                    timestamp=timestamp,
                    consider_future=True,
                )
            )

            # 如果啟用天氣整合，進一步優化選擇
            if self.weather_integration_enabled and selected_candidate:
                enhanced_candidate = await self._enhance_with_weather_prediction(
                    selected_candidate, satellite_data, ue_position
                )
                if enhanced_candidate:
                    selected_candidate = enhanced_candidate

            if not selected_candidate:
                # 如果約束式選擇失敗，回退到簡單選擇
                logger.warning("約束式選擇失敗，使用回退策略")
                return await self._fallback_satellite_selection(
                    visible_satellites, ue_position
                )

            # 轉換為 SatelliteCandidate 格式
            best_satellite = SatelliteCandidate(
                satellite_id=selected_candidate.satellite_id,
                name=selected_candidate.satellite_name,
                elevation=selected_candidate.elevation_deg,
                azimuth=selected_candidate.azimuth_deg,
                distance=selected_candidate.distance_km,
                signal_strength=selected_candidate.signal_strength_dbm,
                score=selected_candidate.overall_score,
            )

            logger.debug(
                f"約束式選擇最佳衛星: {best_satellite.name} (評分: {best_satellite.score:.2f})"
            )

            return best_satellite

        except Exception as e:
            logger.error(f"最佳衛星計算失敗: {e}")
            # 嘗試使用回退策略
            try:
                visible_satellites = self._generate_mock_visible_satellites(
                    ue_position, timestamp
                )
                return await self._fallback_satellite_selection(
                    visible_satellites, ue_position
                )
            except:
                raise e

    async def _enhance_with_weather_prediction(
        self,
        selected_candidate,
        all_satellite_data: List[Dict],
        ue_position: Tuple[float, float, float],
    ):
        """
        使用天氣預測增強衛星選擇
        如果天氣條件會嚴重影響當前選擇，重新評估
        """
        try:
            # 準備天氣評估用的候選者數據
            weather_candidates = []
            for sat_data in all_satellite_data:
                weather_candidates.append(
                    {
                        "satellite_id": sat_data.get("norad_id"),
                        "base_score": 0.8,  # 基礎評分
                        "elevation_deg": sat_data.get("elevation_deg", 30.0),
                        "signal_strength_dbm": -80.0,  # 假設基礎信號強度
                    }
                )

            # 執行天氣整合預測
            weather_prediction = (
                await self.weather_prediction_service.predict_with_weather_integration(
                    ue_id=f"weather_enhanced_{int(time.time())}",
                    ue_position=ue_position,
                    satellite_candidates=weather_candidates,
                    future_time_horizon_sec=self.delta_t * 3,  # 預測3個時間間隔
                )
            )

            if weather_prediction.get("success"):
                weather_selected = weather_prediction["selected_satellite"]
                weather_confidence = weather_prediction["prediction_confidence"]

                # 如果天氣預測的信心度很高且與當前選擇不同，考慮換手
                if (
                    weather_confidence > 0.8
                    and weather_selected["satellite_id"]
                    != selected_candidate.satellite_id
                ):

                    logger.info(
                        f"天氣預測建議換手衛星: {selected_candidate.satellite_id} -> {weather_selected['satellite_id']}"
                    )

                    # 尋找對應的約束式候選者
                    for sat_data in all_satellite_data:
                        if sat_data.get("norad_id") == weather_selected["satellite_id"]:
                            # 重新執行約束式選擇，但優先考慮天氣推薦的衛星
                            weather_enhanced = await self.constrained_access_service.select_optimal_satellite(
                                ue_id=f"weather_pref_{int(time.time())}",
                                ue_position=ue_position,
                                available_satellites=[sat_data],  # 只考慮天氣推薦的衛星
                                timestamp=time.time(),
                                consider_future=True,
                            )

                            if (
                                weather_enhanced
                                and weather_enhanced.overall_score
                                >= selected_candidate.overall_score * 0.9
                            ):
                                logger.info(
                                    f"採用天氣增強建議: {weather_enhanced.satellite_name}"
                                )
                                return weather_enhanced
                            break

                logger.debug(
                    f"天氣預測確認當前選擇 {selected_candidate.satellite_id} (信心度: {weather_confidence:.3f})"
                )

            return selected_candidate

        except Exception as e:
            logger.error(f"天氣預測增強失敗: {e}")
            return selected_candidate

    async def calculate_satellite_score(
        self, satellite, ue_position: Tuple[float, float, float], timestamp: float
    ) -> float:
        """
        計算衛星的綜合評分
        考慮仰角、信號強度、負載等因子
        """
        try:
            # 基礎評分：仰角（越高越好）
            elevation_score = min(satellite.elevation_deg / 90.0, 1.0) * 40

            # 距離評分（越近越好）
            distance_score = max(0, (2000 - satellite.distance_km) / 2000) * 30

            # 信號強度評分
            signal_strength = await self.estimate_signal_strength(
                satellite, ue_position
            )
            signal_score = max(0, (signal_strength + 60) / 40) * 20  # -60dBm 為基準

            # 負載評分（模擬衛星負載）
            load_factor = (
                1.0 - (hash(satellite.norad_id + str(int(timestamp))) % 100) / 100
            )
            load_score = load_factor * 10

            total_score = elevation_score + distance_score + signal_score + load_score

            return total_score

        except Exception as e:
            logger.error(f"衛星評分計算失敗: {e}")
            return 0.0

    async def estimate_signal_strength(
        self, satellite, ue_position: Tuple[float, float, float]
    ) -> float:
        """
        估算信號強度
        基於自由空間路徑損耗模型
        """
        try:
            # 基本參數
            frequency_ghz = 20.0  # 20 GHz
            tx_power_dbm = 40.0  # 40 dBm 發射功率

            # 自由空間路徑損耗計算
            distance_km = satellite.distance_km
            fspl_db = (
                32.45 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz)
            )

            # 接收信號強度
            rx_power_dbm = tx_power_dbm - fspl_db

            # 加入隨機衰落
            fading_db = (hash(str(satellite.norad_id)) % 20) - 10  # ±10dB 隨機衰落

            return rx_power_dbm + fading_db

        except Exception as e:
            logger.error(f"信號強度估算失敗: {e}")
            return -100.0

    def calculate_prediction_confidence(
        self, current_sat: SatelliteCandidate, future_sat: SatelliteCandidate
    ) -> float:
        """
        計算預測信賴水準
        基於衛星軌道穩定性和環境因子
        """
        try:
            # 基礎信賴水準
            base_confidence = 0.85

            # 仰角穩定性加成
            if current_sat.elevation > 30 and future_sat.elevation > 30:
                base_confidence += 0.1

            # 信號強度穩定性
            signal_diff = abs(current_sat.signal_strength - future_sat.signal_strength)
            if signal_diff < 5.0:  # 5dB 以內視為穩定
                base_confidence += 0.05

            # 距離變化穩定性
            distance_diff = abs(current_sat.distance - future_sat.distance)
            if distance_diff < 100:  # 100km 以內視為穩定
                base_confidence += 0.03

            return min(base_confidence, 0.99)

        except Exception as e:
            logger.error(f"信賴水準計算失敗: {e}")
            return 0.5

    async def binary_search_refinement(
        self,
        ue_id: str,
        ue_position: Tuple[float, float, float],
        t_start: float,
        t_end: float,
    ) -> Tuple[float, List[BinarySearchIteration]]:
        """
        使用 Binary Search Refinement 精確計算換手觸發時間 Tp
        將預測誤差迭代減半至低於 RAN 層換手程序時間
        """
        try:
            logger.info(
                f"開始 Binary Search Refinement - UE: {ue_id}, 時間區間: [{t_start}, {t_end}]"
            )

            iterations = []
            iteration_count = 0

            # 獲取起始時間的基準衛星
            start_satellite = await self.calculate_best_satellite(ue_position, t_start)
            start_satellite_id = start_satellite.satellite_id

            while (
                t_end - t_start
            ) > self.precision_threshold and iteration_count < self.max_iterations:
                iteration_count += 1
                t_mid = (t_start + t_end) / 2

                # 計算中點時間的最佳衛星
                mid_satellite = await self.calculate_best_satellite(ue_position, t_mid)
                mid_satellite_id = mid_satellite.satellite_id

                # 記錄迭代過程
                iteration = BinarySearchIteration(
                    iteration=iteration_count,
                    start_time=t_start,
                    end_time=t_end,
                    mid_time=t_mid,
                    satellite=mid_satellite_id,
                    precision=(t_end - t_start),
                    completed=False,
                )
                iterations.append(iteration)

                logger.debug(
                    f"迭代 {iteration_count}: t_mid={t_mid:.3f}, "
                    f"衛星={mid_satellite_id}, 精度={(t_end - t_start):.3f}s"
                )

                # 判斷換手點位置
                if mid_satellite_id != start_satellite_id:
                    # 換手點在前半段
                    t_end = t_mid
                else:
                    # 換手點在後半段
                    t_start = t_mid

                # 避免過度計算
                await asyncio.sleep(0.01)

            # 標記最後一個迭代為完成
            if iterations:
                iterations[-1].completed = True

            # 最終換手時間
            handover_time = (t_start + t_end) / 2

            logger.info(
                f"Binary Search 完成 - 換手時間: {handover_time:.3f}s, "
                f"迭代次數: {iteration_count}, 最終精度: {(t_end - t_start):.3f}s"
            )

            return handover_time, iterations

        except Exception as e:
            logger.error(f"Binary Search Refinement 失敗: {e}")
            raise

    async def update_prediction_record(
        self, ue_id: str, ue_position: Tuple[float, float, float]
    ):
        """
        更新 UE 的預測記錄
        """
        try:
            # 執行二點預測
            prediction_result = await self.two_point_prediction(ue_id, ue_position)

            handover_time = None
            if prediction_result.handover_needed:
                # 如果需要換手，使用 Binary Search 精確計算時間
                handover_time, _ = await self.binary_search_refinement(
                    ue_id,
                    ue_position,
                    prediction_result.current_time,
                    prediction_result.future_time,
                )

            # 更新預測記錄
            record = HandoverPredictionRecord(
                ue_id=ue_id,
                current_satellite=prediction_result.current_satellite,
                predicted_satellite=prediction_result.predicted_satellite,
                handover_time=handover_time,
                prediction_confidence=prediction_result.confidence,
                last_updated=datetime.now(),
            )

            self.prediction_cache[ue_id] = record

            logger.info(f"UE {ue_id} 預測記錄已更新")

            return record

        except Exception as e:
            logger.error(f"預測記錄更新失敗: {e}")
            raise

    def get_prediction_record(self, ue_id: str) -> Optional[HandoverPredictionRecord]:
        """獲取 UE 的預測記錄"""
        return self.prediction_cache.get(ue_id)

    async def start_continuous_prediction(
        self, ue_id: str, ue_position: Tuple[float, float, float]
    ):
        """
        啟動持續預測模式
        每 delta_t 時間更新一次預測
        """
        logger.info(f"啟動 UE {ue_id} 的持續預測模式，間隔 {self.delta_t} 秒")

        while True:
            try:
                await self.update_prediction_record(ue_id, ue_position)
                await asyncio.sleep(self.delta_t)

            except Exception as e:
                logger.error(f"持續預測過程中發生錯誤: {e}")
                await asyncio.sleep(5)  # 錯誤時短暫等待後重試

    def enable_weather_integration(self, enabled: bool):
        """啟用/禁用天氣整合"""
        self.weather_integration_enabled = enabled
        logger.info(f"天氣整合已{'啟用' if enabled else '禁用'}")

    def get_enhanced_prediction_statistics(self) -> Dict:
        """獲取增強的預測統計信息"""
        base_stats = {
            "prediction_cache_size": len(self.prediction_cache),
            "delta_t_seconds": self.delta_t,
            "weather_integration_enabled": self.weather_integration_enabled,
            "min_elevation_threshold": self.min_elevation_threshold,
            "binary_search_precision": self.precision_threshold,
        }

        # 添加天氣預測統計
        if self.weather_integration_enabled:
            weather_stats = (
                self.weather_prediction_service.get_weather_prediction_statistics()
            )
            base_stats.update(
                {
                    "weather_predictions": weather_stats.get("total_predictions", 0),
                    "weather_average_confidence": weather_stats.get(
                        "average_confidence", 0.0
                    ),
                    "weather_cache_size": weather_stats.get("cache_size", 0),
                }
            )

        # 添加準確率優化統計
        if self.accuracy_optimization_enabled:
            accuracy_metrics = self.accuracy_optimizer.get_current_metrics()
            base_stats.update(
                {
                    "accuracy_current": accuracy_metrics.current_accuracy,
                    "accuracy_rolling": accuracy_metrics.rolling_accuracy,
                    "accuracy_trend": accuracy_metrics.accuracy_trend,
                    "accuracy_target_achieved": accuracy_metrics.target_achievement,
                    "predictions_evaluated": accuracy_metrics.predictions_evaluated,
                }
            )

        return base_stats

    async def record_prediction_accuracy(
        self,
        ue_id: str,
        predicted_satellite: str,
        actual_satellite: str,
        prediction_timestamp: float,
        context: Optional[Dict] = None,
    ):
        """
        記錄預測準確率到優化器
        """
        if self.accuracy_optimization_enabled:
            await self.accuracy_optimizer.record_prediction_result(
                ue_id=ue_id,
                predicted_satellite=predicted_satellite,
                actual_satellite=actual_satellite,
                prediction_timestamp=prediction_timestamp,
                delta_t_used=self.delta_t,
                context=context or {},
            )

    def enable_accuracy_optimization(self, enabled: bool):
        """啟用/禁用準確率優化"""
        self.accuracy_optimization_enabled = enabled
        logger.info(f"準確率優化已{'啟用' if enabled else '禁用'}")

    def get_accuracy_metrics(self):
        """獲取準確率指標"""
        if self.accuracy_optimization_enabled:
            return self.accuracy_optimizer.get_current_metrics()
        return None

    def get_accuracy_recommendations(self) -> List[str]:
        """獲取準確率優化建議"""
        if self.accuracy_optimization_enabled:
            return self.accuracy_optimizer.get_optimization_recommendations()
        return ["準確率優化未啟用"]
