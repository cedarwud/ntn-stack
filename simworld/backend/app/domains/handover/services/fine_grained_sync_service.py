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

from ..models.handover_models import HandoverPredictionRecord, BinarySearchIteration
from ...satellite.services.orbit_service import OrbitService

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
        self.prediction_cache: Dict[str, HandoverPredictionRecord] = {}
        self.min_elevation_threshold = 10.0  # 最低仰角門檻（度）
        self.precision_threshold = 0.1  # Binary search 精度門檻（秒）
        self.max_iterations = 15  # 最大迭代次數
        
    async def two_point_prediction(self, ue_id: str, ue_position: Tuple[float, float, float]) -> TwoPointPredictionResult:
        """
        實作二點預測方法
        返回: 當前和預測時段的最佳接入衛星
        """
        try:
            current_time = time.time()
            future_time = current_time + self.delta_t
            
            logger.info(f"執行二點預測 - UE: {ue_id}, T: {current_time}, T+Δt: {future_time}")
            
            # 計算當前時間的最佳衛星 (AT)
            current_satellite = await self.calculate_best_satellite(ue_position, current_time)
            
            # 計算未來時間的最佳衛星 (AT+Δt)
            future_satellite = await self.calculate_best_satellite(ue_position, future_time)
            
            # 判斷是否需要換手
            handover_needed = (current_satellite.satellite_id != future_satellite.satellite_id)
            
            # 計算預測置信度
            confidence = self.calculate_prediction_confidence(current_satellite, future_satellite)
            
            result = TwoPointPredictionResult(
                current_satellite=current_satellite.satellite_id,
                predicted_satellite=future_satellite.satellite_id,
                current_time=current_time,
                future_time=future_time,
                handover_needed=handover_needed,
                confidence=confidence
            )
            
            logger.info(f"二點預測完成 - 當前衛星: {current_satellite.satellite_id}, "
                       f"預測衛星: {future_satellite.satellite_id}, 需要換手: {handover_needed}")
            
            return result
            
        except Exception as e:
            logger.error(f"二點預測失敗: {e}")
            raise
    
    def _generate_mock_visible_satellites(self, ue_position: Tuple[float, float, float], timestamp: float) -> List[Any]:
        """
        生成模擬的可見衛星數據 (用於開發階段)
        在生產環境中應替換為真實的軌道計算
        """
        import random
        import math
        
        # 基於時間和位置生成偽隨機但一致的衛星
        random.seed(int(timestamp) + int(ue_position[0] * 1000) + int(ue_position[1] * 1000))
        
        satellites = []
        satellite_names = [
            "STARLINK-1007", "STARLINK-1008", "STARLINK-1009", "STARLINK-1010",
            "ONEWEB-0001", "ONEWEB-0002", "ONEWEB-0003",
            "IRIDIUM-150", "IRIDIUM-151", "GLOBALSTAR-M001"
        ]
        
        # 生成 5-8 顆可見衛星
        num_satellites = random.randint(5, 8)
        selected_satellites = random.sample(satellite_names, min(num_satellites, len(satellite_names)))
        
        for i, sat_name in enumerate(selected_satellites):
            # 模擬衛星的類型
            class MockSatellite:
                def __init__(self, name: str, norad_id: str, elevation: float, azimuth: float, distance: float):
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
                distance=distance
            )
            
            satellites.append(mock_sat)
        
        # 按仰角排序（仰角越高，信號質量通常越好）
        satellites.sort(key=lambda s: s.elevation_deg, reverse=True)
        
        logger.info(f"生成了 {len(satellites)} 顆模擬可見衛星 (timestamp: {timestamp})")
        return satellites
    
    async def calculate_best_satellite(self, ue_position: Tuple[float, float, float], timestamp: float) -> SatelliteCandidate:
        """
        計算指定時間點的最佳衛星
        使用多因子評分機制選擇最佳衛星
        """
        try:
            # 暫時使用模擬的可見衛星數據，直到實現完整的軌道服務
            visible_satellites = self._generate_mock_visible_satellites(ue_position, timestamp)
            
            if not visible_satellites:
                raise ValueError(f"在時間 {timestamp} 沒有可見衛星")
            
            candidates = []
            
            for sat in visible_satellites:
                # 計算衛星評分
                score = await self.calculate_satellite_score(sat, ue_position, timestamp)
                
                candidate = SatelliteCandidate(
                    satellite_id=sat.norad_id,
                    name=sat.name,
                    elevation=sat.elevation_deg,
                    azimuth=sat.azimuth_deg,
                    distance=sat.distance_km,
                    signal_strength=await self.estimate_signal_strength(sat, ue_position),
                    score=score
                )
                candidates.append(candidate)
            
            # 選擇評分最高的衛星
            best_satellite = max(candidates, key=lambda x: x.score)
            
            logger.debug(f"最佳衛星選擇: {best_satellite.name} (評分: {best_satellite.score:.2f})")
            
            return best_satellite
            
        except Exception as e:
            logger.error(f"最佳衛星計算失敗: {e}")
            raise
    
    async def calculate_satellite_score(self, satellite, ue_position: Tuple[float, float, float], timestamp: float) -> float:
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
            signal_strength = await self.estimate_signal_strength(satellite, ue_position)
            signal_score = max(0, (signal_strength + 60) / 40) * 20  # -60dBm 為基準
            
            # 負載評分（模擬衛星負載）
            load_factor = 1.0 - (hash(satellite.norad_id + str(int(timestamp))) % 100) / 100
            load_score = load_factor * 10
            
            total_score = elevation_score + distance_score + signal_score + load_score
            
            return total_score
            
        except Exception as e:
            logger.error(f"衛星評分計算失敗: {e}")
            return 0.0
    
    async def estimate_signal_strength(self, satellite, ue_position: Tuple[float, float, float]) -> float:
        """
        估算信號強度
        基於自由空間路徑損耗模型
        """
        try:
            # 基本參數
            frequency_ghz = 20.0  # 20 GHz
            tx_power_dbm = 40.0   # 40 dBm 發射功率
            
            # 自由空間路徑損耗計算
            distance_km = satellite.distance_km
            fspl_db = 32.45 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz)
            
            # 接收信號強度
            rx_power_dbm = tx_power_dbm - fspl_db
            
            # 加入隨機衰落
            fading_db = (hash(str(satellite.norad_id)) % 20) - 10  # ±10dB 隨機衰落
            
            return rx_power_dbm + fading_db
            
        except Exception as e:
            logger.error(f"信號強度估算失敗: {e}")
            return -100.0
    
    def calculate_prediction_confidence(self, current_sat: SatelliteCandidate, future_sat: SatelliteCandidate) -> float:
        """
        計算預測置信度
        基於衛星軌道穩定性和環境因子
        """
        try:
            # 基礎置信度
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
            logger.error(f"置信度計算失敗: {e}")
            return 0.5
    
    async def binary_search_refinement(
        self, 
        ue_id: str, 
        ue_position: Tuple[float, float, float],
        t_start: float, 
        t_end: float
    ) -> Tuple[float, List[BinarySearchIteration]]:
        """
        使用 Binary Search Refinement 精確計算換手觸發時間 Tp
        將預測誤差迭代減半至低於 RAN 層切換程序時間
        """
        try:
            logger.info(f"開始 Binary Search Refinement - UE: {ue_id}, 時間區間: [{t_start}, {t_end}]")
            
            iterations = []
            iteration_count = 0
            
            # 獲取起始時間的基準衛星
            start_satellite = await self.calculate_best_satellite(ue_position, t_start)
            start_satellite_id = start_satellite.satellite_id
            
            while (t_end - t_start) > self.precision_threshold and iteration_count < self.max_iterations:
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
                    completed=False
                )
                iterations.append(iteration)
                
                logger.debug(f"迭代 {iteration_count}: t_mid={t_mid:.3f}, "
                           f"衛星={mid_satellite_id}, 精度={(t_end - t_start):.3f}s")
                
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
            
            logger.info(f"Binary Search 完成 - 換手時間: {handover_time:.3f}s, "
                       f"迭代次數: {iteration_count}, 最終精度: {(t_end - t_start):.3f}s")
            
            return handover_time, iterations
            
        except Exception as e:
            logger.error(f"Binary Search Refinement 失敗: {e}")
            raise
    
    async def update_prediction_record(self, ue_id: str, ue_position: Tuple[float, float, float]):
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
                    ue_id, ue_position, 
                    prediction_result.current_time, 
                    prediction_result.future_time
                )
            
            # 更新預測記錄
            record = HandoverPredictionRecord(
                ue_id=ue_id,
                current_satellite=prediction_result.current_satellite,
                predicted_satellite=prediction_result.predicted_satellite,
                handover_time=handover_time,
                prediction_confidence=prediction_result.confidence,
                last_updated=datetime.now()
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
    
    async def start_continuous_prediction(self, ue_id: str, ue_position: Tuple[float, float, float]):
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