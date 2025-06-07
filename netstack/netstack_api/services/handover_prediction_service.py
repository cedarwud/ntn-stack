"""
衛星換手預測服務 (Handover Prediction Service)

實現智能衛星換手預測算法，維護UE-衛星映射表，
結合軌道預測和信號品質評估提供精確的換手時間計算。
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math

import structlog
import numpy as np
from skyfield.api import load, EarthSatellite
from skyfield.positionlib import Geocentric
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class HandoverReason(Enum):
    """換手原因"""
    SIGNAL_DEGRADATION = "signal_degradation"      # 信號品質下降
    SATELLITE_ELEVATION = "satellite_elevation"    # 衛星仰角過低
    ORBITAL_TRANSITION = "orbital_transition"      # 軌道轉換
    LOAD_BALANCING = "load_balancing"              # 負載平衡
    MAINTENANCE = "maintenance"                     # 維護需求
    EMERGENCY = "emergency"                        # 緊急情況


class HandoverTrigger(Enum):
    """換手觸發類型"""
    PROACTIVE = "proactive"        # 主動預測
    REACTIVE = "reactive"          # 被動響應
    FORCED = "forced"              # 強制切換
    SCHEDULED = "scheduled"        # 計劃切換


class PredictionConfidence(Enum):
    """預測信心度"""
    HIGH = "high"          # 高信心度 (>0.8)
    MEDIUM = "medium"      # 中等信心度 (0.5-0.8)
    LOW = "low"            # 低信心度 (<0.5)


@dataclass
class SatelliteOrbitData:
    """衛星軌道數據"""
    satellite_id: str
    tle_line1: str
    tle_line2: str
    last_update: datetime
    orbit_period_minutes: float = 0.0
    inclination_deg: float = 0.0
    apogee_km: float = 0.0
    perigee_km: float = 0.0


@dataclass
class UESatelliteMapping:
    """UE-衛星映射"""
    ue_id: str
    current_satellite_id: str
    signal_quality: float = 0.0          # RSRP (dBm)
    elevation_angle: float = 0.0         # 仰角 (度)
    azimuth_angle: float = 0.0           # 方位角 (度)
    distance_km: float = 0.0             # 距離 (km)
    doppler_shift_hz: float = 0.0        # 都卜勒頻移 (Hz)
    connection_start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    predicted_handover_time: Optional[datetime] = None


@dataclass
class HandoverPrediction:
    """換手預測"""
    prediction_id: str
    ue_id: str
    current_satellite_id: str
    target_satellite_id: str
    predicted_handover_time: datetime
    confidence_level: PredictionConfidence
    confidence_score: float
    handover_reason: HandoverReason
    trigger_type: HandoverTrigger
    signal_quality_trend: List[float] = field(default_factory=list)
    elevation_trend: List[float] = field(default_factory=list)
    prediction_factors: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class HandoverCandidate:
    """換手候選衛星"""
    satellite_id: str
    predicted_signal_quality: float
    predicted_elevation: float
    predicted_distance_km: float
    availability_score: float      # 可用性分數 (0-1)
    load_factor: float             # 負載因子 (0-1)
    handover_cost: float           # 換手成本
    selection_priority: int        # 選擇優先級
    coverage_duration_minutes: float  # 覆蓋持續時間


class HandoverPredictionRequest(BaseModel):
    """換手預測請求"""
    ue_id: str
    prediction_horizon_minutes: int = 30
    include_signal_trend: bool = True
    confidence_threshold: float = 0.6


class HandoverAnalysisRequest(BaseModel):
    """換手分析請求"""
    ue_ids: List[str] = []
    time_window_hours: int = 24
    include_statistics: bool = True


class HandoverPredictionService:
    """衛星換手預測服務"""

    def __init__(self, event_bus_service=None, satellite_service=None):
        self.logger = structlog.get_logger(__name__)
        self.event_bus_service = event_bus_service
        self.satellite_service = satellite_service
        
        # UE-衛星映射表
        self.ue_satellite_mappings: Dict[str, UESatelliteMapping] = {}
        
        # 衛星軌道數據
        self.satellite_orbits: Dict[str, SatelliteOrbitData] = {}
        
        # 換手預測記錄
        self.handover_predictions: Dict[str, HandoverPrediction] = {}
        
        # 預測算法參數
        self.signal_threshold_dbm = -85.0      # 信號品質閾值
        self.elevation_threshold_deg = 10.0    # 最小仰角閾值
        self.prediction_interval = 60.0        # 預測間隔 (秒)
        self.history_window_minutes = 60       # 歷史數據窗口
        
        # 軌道預測
        self.ts = load.timescale()
        self.earth_satellites: Dict[str, EarthSatellite] = {}
        
        # 信號品質歷史
        self.signal_history: Dict[str, List[Tuple[datetime, float]]] = {}
        
        # 預測任務
        self.prediction_task: Optional[asyncio.Task] = None
        
    async def start_prediction_service(self):
        """啟動預測服務"""
        if self.prediction_task is None:
            self.prediction_task = asyncio.create_task(self._prediction_loop())
            await self._load_satellite_orbit_data()
            self.logger.info("衛星換手預測服務已啟動")
    
    async def stop_prediction_service(self):
        """停止預測服務"""
        if self.prediction_task:
            self.prediction_task.cancel()
            try:
                await self.prediction_task
            except asyncio.CancelledError:
                pass
            self.prediction_task = None
            self.logger.info("衛星換手預測服務已停止")
    
    async def _prediction_loop(self):
        """預測循環"""
        while True:
            try:
                # 更新UE-衛星映射
                await self._update_ue_satellite_mappings()
                
                # 執行換手預測
                await self._perform_handover_predictions()
                
                # 清理過期預測
                await self._cleanup_expired_predictions()
                
                await asyncio.sleep(self.prediction_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"預測循環異常: {e}")
                await asyncio.sleep(10.0)
    
    async def _load_satellite_orbit_data(self):
        """載入衛星軌道數據"""
        # 模擬OneWeb衛星軌道數據
        mock_satellites = [
            {
                "satellite_id": "oneweb_001",
                "tle_line1": "1 47926U 21022A   23001.00000000  .00000000  00000-0  00000-0 0  9990",
                "tle_line2": "2 47926  87.4000 000.0000 0000000  90.0000 270.0000 13.34000000000000",
                "orbit_period_minutes": 109.5,
                "inclination_deg": 87.4,
                "apogee_km": 1200.0,
                "perigee_km": 1200.0
            },
            {
                "satellite_id": "oneweb_002", 
                "tle_line1": "1 47927U 21022B   23001.00000000  .00000000  00000-0  00000-0 0  9991",
                "tle_line2": "2 47927  87.4000 030.0000 0000000  90.0000 270.0000 13.34000000000000",
                "orbit_period_minutes": 109.5,
                "inclination_deg": 87.4,
                "apogee_km": 1200.0,
                "perigee_km": 1200.0
            },
            {
                "satellite_id": "oneweb_003",
                "tle_line1": "1 47928U 21022C   23001.00000000  .00000000  00000-0  00000-0 0  9992", 
                "tle_line2": "2 47928  87.4000 060.0000 0000000  90.0000 270.0000 13.34000000000000",
                "orbit_period_minutes": 109.5,
                "inclination_deg": 87.4,
                "apogee_km": 1200.0,
                "perigee_km": 1200.0
            }
        ]
        
        for sat_data in mock_satellites:
            orbit_data = SatelliteOrbitData(
                satellite_id=sat_data["satellite_id"],
                tle_line1=sat_data["tle_line1"],
                tle_line2=sat_data["tle_line2"],
                last_update=datetime.now(),
                orbit_period_minutes=sat_data["orbit_period_minutes"],
                inclination_deg=sat_data["inclination_deg"],
                apogee_km=sat_data["apogee_km"],
                perigee_km=sat_data["perigee_km"]
            )
            
            self.satellite_orbits[sat_data["satellite_id"]] = orbit_data
            
            # 創建Skyfield衛星對象
            try:
                satellite = EarthSatellite(
                    sat_data["tle_line1"],
                    sat_data["tle_line2"],
                    sat_data["satellite_id"],
                    self.ts
                )
                self.earth_satellites[sat_data["satellite_id"]] = satellite
            except Exception as e:
                self.logger.warning(f"無法創建衛星 {sat_data['satellite_id']} 的軌道對象: {e}")
        
        self.logger.info(f"已載入 {len(self.satellite_orbits)} 顆衛星的軌道數據")
    
    async def _update_ue_satellite_mappings(self):
        """更新UE-衛星映射"""
        # 模擬獲取當前UE連接狀態
        mock_ue_connections = [
            {
                "ue_id": "ue_001",
                "current_satellite_id": "oneweb_001",
                "latitude": 25.0,
                "longitude": 121.0,
                "altitude": 100.0
            },
            {
                "ue_id": "ue_002", 
                "current_satellite_id": "oneweb_002",
                "latitude": 25.1,
                "longitude": 121.1,
                "altitude": 150.0
            },
            {
                "ue_id": "ue_003",
                "current_satellite_id": "oneweb_001",
                "latitude": 24.9,
                "longitude": 120.9,
                "altitude": 80.0
            }
        ]
        
        for ue_data in mock_ue_connections:
            ue_id = ue_data["ue_id"]
            satellite_id = ue_data["current_satellite_id"]
            
            # 計算衛星與UE的幾何關係
            geometry = await self._calculate_satellite_geometry(
                satellite_id,
                ue_data["latitude"],
                ue_data["longitude"], 
                ue_data["altitude"]
            )
            
            if geometry:
                # 更新或創建映射
                if ue_id in self.ue_satellite_mappings:
                    mapping = self.ue_satellite_mappings[ue_id]
                    mapping.current_satellite_id = satellite_id
                    mapping.last_update = datetime.now()
                else:
                    mapping = UESatelliteMapping(
                        ue_id=ue_id,
                        current_satellite_id=satellite_id
                    )
                    self.ue_satellite_mappings[ue_id] = mapping
                
                # 更新幾何參數
                mapping.elevation_angle = geometry["elevation"]
                mapping.azimuth_angle = geometry["azimuth"]
                mapping.distance_km = geometry["distance"]
                mapping.doppler_shift_hz = geometry["doppler_shift"]
                
                # 計算信號品質
                mapping.signal_quality = self._estimate_signal_quality(geometry)
                
                # 記錄信號品質歷史
                await self._record_signal_history(ue_id, mapping.signal_quality)
    
    async def _calculate_satellite_geometry(
        self, 
        satellite_id: str, 
        lat: float, 
        lon: float, 
        alt: float
    ) -> Optional[Dict]:
        """計算衛星幾何關係"""
        if satellite_id not in self.earth_satellites:
            return None
            
        try:
            satellite = self.earth_satellites[satellite_id]
            now = self.ts.now()
            
            # 計算衛星位置
            geocentric = satellite.at(now)
            lat_rad, lon_rad = math.radians(lat), math.radians(lon)
            
            # 地面站位置
            from skyfield.api import wgs84
            ground_station = wgs84.latlon(lat, lon, elevation_m=alt)
            
            # 計算相對位置
            difference = satellite - ground_station
            topocentric = difference.at(now)
            
            # 獲取仰角、方位角
            alt_deg, az_deg, distance_km = topocentric.altaz()
            
            # 計算都卜勒頻移 (簡化模型)
            velocity_vector = geocentric.velocity.km_per_s
            velocity_magnitude = np.linalg.norm(velocity_vector)
            doppler_shift = velocity_magnitude * 1e6 / 299792458 * 2.1e9  # 假設2.1GHz載波
            
            return {
                "elevation": float(alt_deg.degrees),
                "azimuth": float(az_deg.degrees), 
                "distance": float(distance_km.km),
                "doppler_shift": doppler_shift
            }
            
        except Exception as e:
            self.logger.warning(f"計算衛星 {satellite_id} 幾何關係失敗: {e}")
            return None
    
    def _estimate_signal_quality(self, geometry: Dict) -> float:
        """估算信號品質"""
        elevation = geometry["elevation"]
        distance = geometry["distance"]
        
        # 簡化的信號強度模型
        # 基於自由空間路徑損耗和仰角修正
        
        # 自由空間路徑損耗 (dB)
        frequency_ghz = 2.1
        path_loss_db = 20 * math.log10(distance) + 20 * math.log10(frequency_ghz) + 92.45
        
        # 仰角修正因子
        elevation_factor = max(0.1, math.sin(math.radians(max(5, elevation))))
        elevation_correction_db = 10 * math.log10(elevation_factor)
        
        # 假設衛星EIRP為50dBW，接收天線增益為0dBi
        eirp_dbw = 50.0
        antenna_gain_dbi = 0.0
        
        # 接收功率 (dBm)
        received_power_dbm = eirp_dbw + 30 + antenna_gain_dbi - path_loss_db + elevation_correction_db
        
        return received_power_dbm
    
    async def _record_signal_history(self, ue_id: str, signal_quality: float):
        """記錄信號品質歷史"""
        if ue_id not in self.signal_history:
            self.signal_history[ue_id] = []
        
        self.signal_history[ue_id].append((datetime.now(), signal_quality))
        
        # 清理超過窗口的歷史數據
        cutoff_time = datetime.now() - timedelta(minutes=self.history_window_minutes)
        self.signal_history[ue_id] = [
            (timestamp, quality) for timestamp, quality in self.signal_history[ue_id]
            if timestamp > cutoff_time
        ]
    
    async def _perform_handover_predictions(self):
        """執行換手預測"""
        for ue_id, mapping in self.ue_satellite_mappings.items():
            try:
                # 分析當前連接狀態
                prediction = await self._analyze_handover_need(ue_id, mapping)
                
                if prediction:
                    # 找到候選衛星
                    candidates = await self._find_handover_candidates(ue_id, mapping)
                    
                    if candidates:
                        # 選擇最佳候選
                        best_candidate = self._select_best_candidate(candidates)
                        
                        # 更新預測
                        prediction.target_satellite_id = best_candidate.satellite_id
                        prediction.prediction_factors["candidates"] = len(candidates)
                        prediction.prediction_factors["best_candidate_score"] = best_candidate.availability_score
                        
                        # 保存預測
                        self.handover_predictions[prediction.prediction_id] = prediction
                        
                        # 發送預測事件
                        await self._publish_handover_prediction_event(prediction)
                        
                        self.logger.info(
                            f"生成換手預測: {ue_id} -> {prediction.target_satellite_id}",
                            prediction_time=prediction.predicted_handover_time.isoformat(),
                            confidence=prediction.confidence_score
                        )
                        
            except Exception as e:
                self.logger.error(f"為UE {ue_id} 執行換手預測失敗: {e}")
    
    async def _analyze_handover_need(
        self, 
        ue_id: str, 
        mapping: UESatelliteMapping
    ) -> Optional[HandoverPrediction]:
        """分析是否需要換手"""
        
        # 檢查信號品質趨勢
        signal_trend = await self._analyze_signal_trend(ue_id)
        
        # 檢查仰角趨勢
        elevation_trend = await self._analyze_elevation_trend(ue_id, mapping.current_satellite_id)
        
        # 判斷換手觸發條件
        handover_reasons = []
        confidence_factors = []
        
        # 信號品質檢查
        if mapping.signal_quality < self.signal_threshold_dbm:
            handover_reasons.append(HandoverReason.SIGNAL_DEGRADATION)
            confidence_factors.append(0.8)
        
        # 仰角檢查
        if mapping.elevation_angle < self.elevation_threshold_deg:
            handover_reasons.append(HandoverReason.SATELLITE_ELEVATION)
            confidence_factors.append(0.9)
        
        # 信號品質趨勢檢查
        if signal_trend and signal_trend["slope"] < -0.5:  # 信號快速下降
            handover_reasons.append(HandoverReason.SIGNAL_DEGRADATION)
            confidence_factors.append(0.7)
        
        # 軌道轉換檢查
        if await self._check_orbital_transition(mapping.current_satellite_id):
            handover_reasons.append(HandoverReason.ORBITAL_TRANSITION)
            confidence_factors.append(0.6)
        
        if not handover_reasons:
            return None
        
        # 預測換手時間
        predicted_time = await self._predict_handover_time(ue_id, mapping, handover_reasons)
        
        # 計算信心度
        confidence_score = np.mean(confidence_factors) if confidence_factors else 0.5
        confidence_level = self._determine_confidence_level(confidence_score)
        
        # 創建預測
        prediction = HandoverPrediction(
            prediction_id=f"pred_{uuid.uuid4().hex[:8]}",
            ue_id=ue_id,
            current_satellite_id=mapping.current_satellite_id,
            target_satellite_id="",  # 稍後確定
            predicted_handover_time=predicted_time,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            handover_reason=handover_reasons[0],  # 主要原因
            trigger_type=HandoverTrigger.PROACTIVE,
            signal_quality_trend=signal_trend.get("values", []) if signal_trend else [],
            elevation_trend=elevation_trend.get("values", []) if elevation_trend else [],
            prediction_factors={
                "reasons": [r.value for r in handover_reasons],
                "signal_quality": mapping.signal_quality,
                "elevation_angle": mapping.elevation_angle,
                "trend_slope": signal_trend.get("slope", 0) if signal_trend else 0
            }
        )
        
        return prediction
    
    async def _analyze_signal_trend(self, ue_id: str) -> Optional[Dict]:
        """分析信號品質趨勢"""
        if ue_id not in self.signal_history or len(self.signal_history[ue_id]) < 3:
            return None
        
        history = self.signal_history[ue_id]
        recent_history = history[-10:]  # 最近10個數據點
        
        # 計算時間序列
        times = [(t - recent_history[0][0]).total_seconds() for t, _ in recent_history]
        values = [quality for _, quality in recent_history]
        
        # 線性回歸計算趨勢
        if len(times) > 1:
            slope = np.polyfit(times, values, 1)[0]
            
            return {
                "slope": slope,
                "values": values,
                "time_span_minutes": (times[-1] - times[0]) / 60
            }
        
        return None
    
    async def _analyze_elevation_trend(self, ue_id: str, satellite_id: str) -> Optional[Dict]:
        """分析仰角趨勢"""
        # 預測未來30分鐘的仰角變化
        future_elevations = []
        
        if ue_id in self.ue_satellite_mappings:
            mapping = self.ue_satellite_mappings[ue_id]
            
            # 模擬未來仰角計算
            for minutes_ahead in range(0, 31, 5):
                future_time = datetime.now() + timedelta(minutes=minutes_ahead)
                # 簡化的仰角預測 (實際應基於軌道計算)
                predicted_elevation = mapping.elevation_angle - (minutes_ahead * 0.2)
                future_elevations.append(max(0, predicted_elevation))
        
        if future_elevations:
            times = list(range(0, len(future_elevations) * 5, 5))
            slope = np.polyfit(times, future_elevations, 1)[0] if len(times) > 1 else 0
            
            return {
                "slope": slope,
                "values": future_elevations,
                "min_elevation": min(future_elevations)
            }
        
        return None
    
    async def _check_orbital_transition(self, satellite_id: str) -> bool:
        """檢查軌道轉換"""
        # 檢查衛星是否接近軌道轉換點
        if satellite_id in self.satellite_orbits:
            orbit_data = self.satellite_orbits[satellite_id]
            # 簡化檢查：基於軌道週期判斷
            current_time = datetime.now()
            time_since_update = (current_time - orbit_data.last_update).total_seconds()
            orbit_period_seconds = orbit_data.orbit_period_minutes * 60
            
            # 檢查是否接近軌道週期的特定點
            position_in_orbit = (time_since_update % orbit_period_seconds) / orbit_period_seconds
            
            # 如果接近軌道的1/4或3/4點，可能需要換手
            return 0.2 < position_in_orbit < 0.3 or 0.7 < position_in_orbit < 0.8
        
        return False
    
    async def _predict_handover_time(
        self, 
        ue_id: str, 
        mapping: UESatelliteMapping, 
        reasons: List[HandoverReason]
    ) -> datetime:
        """預測換手時間"""
        base_time = datetime.now()
        
        # 根據不同原因調整預測時間
        if HandoverReason.SIGNAL_DEGRADATION in reasons:
            # 基於信號品質下降速度
            signal_trend = await self._analyze_signal_trend(ue_id)
            if signal_trend and signal_trend["slope"] < 0:
                # 估算信號降到閾值的時間
                current_signal = mapping.signal_quality
                threshold = self.signal_threshold_dbm
                if current_signal > threshold:
                    time_to_threshold = (current_signal - threshold) / abs(signal_trend["slope"])
                    return base_time + timedelta(seconds=time_to_threshold * 60)
        
        if HandoverReason.SATELLITE_ELEVATION in reasons:
            # 基於仰角下降速度
            elevation_trend = await self._analyze_elevation_trend(ue_id, mapping.current_satellite_id)
            if elevation_trend and elevation_trend["slope"] < 0:
                current_elevation = mapping.elevation_angle
                threshold = self.elevation_threshold_deg
                if current_elevation > threshold:
                    time_to_threshold = (current_elevation - threshold) / abs(elevation_trend["slope"])
                    return base_time + timedelta(minutes=time_to_threshold)
        
        # 默認預測時間：10-20分鐘
        import random
        return base_time + timedelta(minutes=random.uniform(10, 20))
    
    def _determine_confidence_level(self, confidence_score: float) -> PredictionConfidence:
        """確定信心度等級"""
        if confidence_score >= 0.8:
            return PredictionConfidence.HIGH
        elif confidence_score >= 0.5:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW
    
    async def _find_handover_candidates(
        self, 
        ue_id: str, 
        current_mapping: UESatelliteMapping
    ) -> List[HandoverCandidate]:
        """尋找換手候選衛星"""
        candidates = []
        
        if ue_id not in self.ue_satellite_mappings:
            return candidates
        
        mapping = self.ue_satellite_mappings[ue_id]
        
        # 獲取UE位置（模擬）
        ue_lat, ue_lon, ue_alt = 25.0, 121.0, 100.0  # 實際應從mapping獲取
        
        for satellite_id, orbit_data in self.satellite_orbits.items():
            if satellite_id == current_mapping.current_satellite_id:
                continue  # 跳過當前衛星
            
            # 計算候選衛星的幾何關係
            geometry = await self._calculate_satellite_geometry(
                satellite_id, ue_lat, ue_lon, ue_alt
            )
            
            if not geometry:
                continue
            
            # 檢查基本條件
            if geometry["elevation"] < self.elevation_threshold_deg:
                continue
            
            # 估算信號品質
            predicted_signal = self._estimate_signal_quality(geometry)
            
            if predicted_signal < self.signal_threshold_dbm:
                continue
            
            # 計算可用性分數
            availability_score = self._calculate_availability_score(geometry, predicted_signal)
            
            # 估算負載因子（模擬）
            load_factor = 0.3 + (hash(satellite_id) % 40) / 100.0  # 0.3-0.7
            
            # 計算換手成本
            handover_cost = self._calculate_handover_cost(
                current_mapping, satellite_id, geometry
            )
            
            # 估算覆蓋持續時間
            coverage_duration = await self._estimate_coverage_duration(
                satellite_id, ue_lat, ue_lon, ue_alt
            )
            
            candidate = HandoverCandidate(
                satellite_id=satellite_id,
                predicted_signal_quality=predicted_signal,
                predicted_elevation=geometry["elevation"],
                predicted_distance_km=geometry["distance"],
                availability_score=availability_score,
                load_factor=load_factor,
                handover_cost=handover_cost,
                selection_priority=0,  # 稍後計算
                coverage_duration_minutes=coverage_duration
            )
            
            candidates.append(candidate)
        
        # 計算選擇優先級並排序
        candidates = self._rank_handover_candidates(candidates)
        
        return candidates
    
    def _calculate_availability_score(self, geometry: Dict, signal_quality: float) -> float:
        """計算可用性分數"""
        # 基於仰角、信號品質和距離的綜合評分
        elevation_score = min(1.0, geometry["elevation"] / 90.0)
        signal_score = min(1.0, (signal_quality - self.signal_threshold_dbm) / 20.0)
        distance_score = max(0.0, 1.0 - (geometry["distance"] - 1000) / 1000.0)
        
        availability_score = (
            elevation_score * 0.4 +
            signal_score * 0.4 +
            distance_score * 0.2
        )
        
        return max(0.0, min(1.0, availability_score))
    
    def _calculate_handover_cost(
        self, 
        current_mapping: UESatelliteMapping, 
        target_satellite_id: str, 
        target_geometry: Dict
    ) -> float:
        """計算換手成本"""
        # 基於頻率差異、信號強度差異和幾何差異
        
        # 都卜勒頻移差異成本
        doppler_diff = abs(target_geometry["doppler_shift"] - current_mapping.doppler_shift_hz)
        doppler_cost = min(1.0, doppler_diff / 10000.0)  # 正規化到0-1
        
        # 仰角變化成本
        elevation_diff = abs(target_geometry["elevation"] - current_mapping.elevation_angle)
        elevation_cost = elevation_diff / 180.0  # 正規化到0-1
        
        # 距離變化成本
        distance_diff = abs(target_geometry["distance"] - current_mapping.distance_km)
        distance_cost = min(1.0, distance_diff / 1000.0)  # 正規化到0-1
        
        # 總成本
        total_cost = (
            doppler_cost * 0.4 +
            elevation_cost * 0.3 +
            distance_cost * 0.3
        )
        
        return total_cost
    
    async def _estimate_coverage_duration(
        self, 
        satellite_id: str, 
        ue_lat: float, 
        ue_lon: float, 
        ue_alt: float
    ) -> float:
        """估算覆蓋持續時間（分鐘）"""
        if satellite_id not in self.satellite_orbits:
            return 0.0
        
        orbit_data = self.satellite_orbits[satellite_id]
        
        # 簡化的覆蓋時間估算
        # 基於軌道週期和仰角變化速度
        orbit_period_minutes = orbit_data.orbit_period_minutes
        
        # 假設衛星在可見範圍內的時間約為軌道週期的1/6到1/4
        coverage_fraction = 0.15 + (orbit_data.inclination_deg / 90.0) * 0.1
        estimated_duration = orbit_period_minutes * coverage_fraction
        
        return estimated_duration
    
    def _rank_handover_candidates(self, candidates: List[HandoverCandidate]) -> List[HandoverCandidate]:
        """對候選衛星進行排序"""
        
        # 計算綜合評分
        for i, candidate in enumerate(candidates):
            # 綜合評分：可用性、負載、成本、覆蓋時間
            score = (
                candidate.availability_score * 0.3 +
                (1.0 - candidate.load_factor) * 0.2 +  # 負載越低越好
                (1.0 - candidate.handover_cost) * 0.2 +  # 成本越低越好
                min(1.0, candidate.coverage_duration_minutes / 60.0) * 0.3  # 覆蓋時間越長越好
            )
            
            candidate.selection_priority = i + 1
            candidates[i] = candidate
        
        # 按綜合評分排序
        candidates.sort(key=lambda c: (
            c.availability_score * 0.3 +
            (1.0 - c.load_factor) * 0.2 +
            (1.0 - c.handover_cost) * 0.2 +
            min(1.0, c.coverage_duration_minutes / 60.0) * 0.3
        ), reverse=True)
        
        # 更新優先級
        for i, candidate in enumerate(candidates):
            candidate.selection_priority = i + 1
        
        return candidates
    
    def _select_best_candidate(self, candidates: List[HandoverCandidate]) -> HandoverCandidate:
        """選擇最佳候選衛星"""
        if not candidates:
            raise ValueError("沒有可用的候選衛星")
        
        # 返回排序後的第一個（最佳）候選
        return candidates[0]
    
    async def _publish_handover_prediction_event(self, prediction: HandoverPrediction):
        """發佈換手預測事件"""
        if self.event_bus_service:
            event_data = {
                "event_type": "handover.prediction.created",
                "prediction_id": prediction.prediction_id,
                "ue_id": prediction.ue_id,
                "current_satellite": prediction.current_satellite_id,
                "target_satellite": prediction.target_satellite_id,
                "predicted_time": prediction.predicted_handover_time.isoformat(),
                "confidence": prediction.confidence_score,
                "reason": prediction.handover_reason.value
            }
            
            try:
                await self.event_bus_service.publish_event(
                    "handover.prediction",
                    event_data,
                    priority="HIGH"
                )
            except Exception as e:
                self.logger.error(f"發佈換手預測事件失敗: {e}")
    
    async def _cleanup_expired_predictions(self):
        """清理過期預測"""
        current_time = datetime.now()
        expired_predictions = []
        
        for prediction_id, prediction in self.handover_predictions.items():
            # 清理已過期或已完成的預測
            if (prediction.predicted_handover_time < current_time or 
                not prediction.is_active):
                expired_predictions.append(prediction_id)
        
        for prediction_id in expired_predictions:
            del self.handover_predictions[prediction_id]
        
        if expired_predictions:
            self.logger.debug(f"清理了 {len(expired_predictions)} 個過期預測")
    
    async def get_handover_prediction(self, ue_id: str) -> Optional[HandoverPrediction]:
        """獲取UE的換手預測"""
        for prediction in self.handover_predictions.values():
            if prediction.ue_id == ue_id and prediction.is_active:
                return prediction
        return None
    
    async def get_all_predictions(self) -> List[HandoverPrediction]:
        """獲取所有活躍預測"""
        return [p for p in self.handover_predictions.values() if p.is_active]
    
    async def get_prediction_statistics(self) -> Dict:
        """獲取預測統計"""
        active_predictions = [p for p in self.handover_predictions.values() if p.is_active]
        
        if not active_predictions:
            return {
                "total_predictions": 0,
                "active_predictions": 0,
                "confidence_distribution": {},
                "reason_distribution": {},
                "average_confidence": 0.0
            }
        
        # 信心度分佈
        confidence_dist = {}
        for pred in active_predictions:
            level = pred.confidence_level.value
            confidence_dist[level] = confidence_dist.get(level, 0) + 1
        
        # 原因分佈
        reason_dist = {}
        for pred in active_predictions:
            reason = pred.handover_reason.value
            reason_dist[reason] = reason_dist.get(reason, 0) + 1
        
        return {
            "total_predictions": len(self.handover_predictions),
            "active_predictions": len(active_predictions),
            "confidence_distribution": confidence_dist,
            "reason_distribution": reason_dist,
            "average_confidence": np.mean([p.confidence_score for p in active_predictions]),
            "ue_mappings": len(self.ue_satellite_mappings),
            "satellite_orbits": len(self.satellite_orbits)
        }