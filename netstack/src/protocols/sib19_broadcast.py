"""
Phase 3.1.2: 衛星位置資訊廣播機制實現

實現符合 3GPP TS 38.331 的 SIB19 (SystemInformationBlockType19) 廣播機制，包括：
1. 衛星位置資訊 (Ephemeris data) 廣播
2. 動態廣播調度機制
3. 可見衛星列表維護
4. 服務區域覆蓋資訊管理
5. 緊急廣播機制

符合標準：
- 3GPP TS 38.331 Section 5.2.2: SIB19 for NTN
- 3GPP TS 38.300: NTN 系統架構
- ITU-R S.1001: 衛星軌道參數標準
"""

import asyncio
import logging
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from datetime import datetime, timezone, timedelta
import math

logger = logging.getLogger(__name__)


class SIB19BroadcastType(Enum):
    """SIB19 廣播類型"""
    PERIODIC = "periodic"           # 週期性廣播
    EVENT_TRIGGERED = "event_triggered"  # 事件觸發廣播
    EMERGENCY = "emergency"         # 緊急廣播


class SatelliteVisibilityStatus(Enum):
    """衛星可見性狀態"""
    VISIBLE = "visible"             # 可見
    RISING = "rising"               # 上升中
    SETTING = "setting"             # 下降中
    HIDDEN = "hidden"               # 不可見


@dataclass
class SatelliteEphemeris:
    """衛星星曆數據"""
    satellite_id: str
    norad_id: int
    epoch_time: datetime
    
    # Keplerian 軌道參數
    semi_major_axis: float          # 半長軸 (km)
    eccentricity: float            # 偏心率
    inclination: float             # 軌道傾角 (度)
    raan: float                    # 升交點赤經 (度)
    argument_of_perigee: float     # 近地點幅角 (度)
    mean_anomaly: float            # 平近點角 (度)
    mean_motion: float             # 平均運動 (revs/day)
    
    # 當前位置資訊
    latitude: float = field(default=0.0)   # 緯度 (度)
    longitude: float = field(default=0.0)  # 經度 (度)
    altitude: float = field(default=550.0) # 高度 (km)
    
    # 運動參數
    velocity_x: float = field(default=0.0)  # X 方向速度 (km/s)
    velocity_y: float = field(default=0.0)  # Y 方向速度 (km/s)
    velocity_z: float = field(default=0.0)  # Z 方向速度 (km/s)
    
    def calculate_position_at_time(self, target_time: datetime) -> Tuple[float, float, float]:
        """
        計算指定時間的衛星位置
        使用簡化的 Keplerian 軌道計算
        """
        # 計算時間差 (分鐘)
        time_diff = (target_time - self.epoch_time).total_seconds() / 60.0
        
        # 簡化的軌道計算 (實際應使用 SGP4)
        # 基於平均運動計算軌道位置
        orbital_period_minutes = 1440.0 / self.mean_motion  # 軌道週期 (分鐘)
        phase = (time_diff / orbital_period_minutes) * 2 * math.pi
        
        # 計算位置 (簡化的圓形軌道)
        lat = math.degrees(math.asin(math.sin(math.radians(self.inclination)) * 
                                   math.sin(phase + math.radians(self.raan))))
        
        lon = math.degrees(math.atan2(
            math.cos(math.radians(self.inclination)) * math.sin(phase),
            math.cos(phase)
        )) + self.longitude + (time_diff * 0.25)  # 地球自轉補償
        
        # 正規化經度
        lon = ((lon + 180) % 360) - 180
        
        return lat, lon, self.altitude
    
    def is_visible_from_location(self, observer_lat: float, observer_lon: float, 
                               min_elevation: float = 5.0) -> bool:
        """
        計算衛星是否從指定位置可見
        """
        # 計算衛星與觀測點的角距離
        lat_diff = math.radians(self.latitude - observer_lat)
        lon_diff = math.radians(self.longitude - observer_lon)
        
        # 使用球面餘弦定律計算角距離
        angular_distance = math.acos(
            math.sin(math.radians(observer_lat)) * math.sin(math.radians(self.latitude)) +
            math.cos(math.radians(observer_lat)) * math.cos(math.radians(self.latitude)) *
            math.cos(lon_diff)
        )
        
        # 計算仰角 (簡化計算)
        earth_radius = 6371.0  # km
        satellite_distance = math.sqrt(
            (earth_radius + self.altitude) ** 2 +
            earth_radius ** 2 -
            2 * earth_radius * (earth_radius + self.altitude) * math.cos(angular_distance)
        )
        
        elevation = math.asin(
            ((earth_radius + self.altitude) * math.sin(angular_distance)) / satellite_distance
        ) - angular_distance
        
        elevation_degrees = math.degrees(elevation)
        
        return elevation_degrees >= min_elevation


@dataclass
class VisibleSatellite:
    """可見衛星資訊"""
    satellite_id: str
    ephemeris: SatelliteEphemeris
    visibility_status: SatelliteVisibilityStatus
    elevation_angle: float          # 仰角 (度)
    azimuth_angle: float           # 方位角 (度)
    distance: float                # 距離 (km)
    doppler_shift: float           # 都卜勒頻移 (Hz)
    first_visible_time: datetime   # 首次可見時間
    last_update_time: datetime     # 最後更新時間
    
    def calculate_signal_strength(self, base_power_dbm: float = -70) -> float:
        """計算信號強度 (RSRP)"""
        # 自由空間路徑損耗計算
        frequency_ghz = 2.0  # 假設 2GHz 頻段
        fspl_db = 20 * math.log10(self.distance) + 20 * math.log10(frequency_ghz) + 92.45
        
        # 仰角修正
        elevation_correction = max(0, (self.elevation_angle - 5) * 0.1)
        
        return base_power_dbm - fspl_db + elevation_correction


@dataclass
class SIB19Message:
    """SIB19 廣播消息"""
    message_id: str
    broadcast_time: datetime
    broadcast_type: SIB19BroadcastType
    validity_duration: int          # 有效期 (秒)
    sequence_number: int
    
    # 衛星星曆資訊
    satellite_ephemeris_list: List[SatelliteEphemeris] = field(default_factory=list)
    
    # NTN 特定配置
    ntn_config: Dict[str, Any] = field(default_factory=dict)
    
    # 鄰近小區配置
    neighbor_cell_config: List[Dict[str, Any]] = field(default_factory=list)
    
    # 服務區域資訊
    service_area_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'messageId': self.message_id,
            'broadcastTime': self.broadcast_time.isoformat(),
            'broadcastType': self.broadcast_type.value,
            'validityDuration': self.validity_duration,
            'sequenceNumber': self.sequence_number,
            'satelliteEphemerisList': [asdict(eph) for eph in self.satellite_ephemeris_list],
            'ntnConfig': self.ntn_config,
            'neighborCellConfig': self.neighbor_cell_config,
            'serviceAreaInfo': self.service_area_info
        }
    
    def is_valid(self) -> bool:
        """檢查消息是否仍然有效"""
        age = (datetime.now(timezone.utc) - self.broadcast_time).total_seconds()
        return age < self.validity_duration


class SIB19BroadcastScheduler:
    """SIB19 廣播調度器"""
    
    def __init__(self):
        self.broadcast_config = {
            'periodic_interval': 30,        # 週期性廣播間隔 (秒)
            'validity_duration': 60,        # 消息有效期 (秒)
            'max_satellites_per_message': 8, # 每條消息最大衛星數
            'emergency_priority': True,     # 緊急廣播優先
            'adaptive_scheduling': True     # 自適應調度
        }
        
        self.active_satellites: Dict[str, SatelliteEphemeris] = {}
        self.visible_satellites: Dict[str, VisibleSatellite] = {}
        self.broadcast_history: List[SIB19Message] = []
        self.sequence_counter = 0
        
        # 觀測點配置 (預設為台北科技大學)
        self.observer_location = {
            'latitude': 24.9441667,
            'longitude': 121.3713889,
            'altitude': 0.1,  # km
            'min_elevation': 5.0  # 最小仰角
        }
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 廣播任務控制
        self.scheduler_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start_scheduler(self):
        """啟動廣播調度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("🎯 SIB19 廣播調度器已啟動")
    
    async def stop_scheduler(self):
        """停止廣播調度器"""
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ SIB19 廣播調度器已停止")
    
    async def _scheduler_loop(self):
        """主調度循環"""
        try:
            while self.is_running:
                await self._periodic_broadcast_cycle()
                
                # 等待下一個廣播週期
                await asyncio.sleep(self.broadcast_config['periodic_interval'])
                
        except asyncio.CancelledError:
            self.logger.info("📡 SIB19 廣播調度器循環已取消")
        except Exception as e:
            self.logger.error(f"❌ SIB19 廣播調度器異常: {e}")
    
    async def _periodic_broadcast_cycle(self):
        """週期性廣播循環"""
        try:
            # 1. 更新衛星位置
            await self._update_satellite_positions()
            
            # 2. 計算可見衛星
            await self._calculate_visible_satellites()
            
            # 3. 生成並廣播 SIB19 消息
            sib19_message = await self._generate_sib19_message(SIB19BroadcastType.PERIODIC)
            
            if sib19_message:
                await self._broadcast_sib19_message(sib19_message)
                
        except Exception as e:
            self.logger.error(f"❌ 週期性廣播循環異常: {e}")
    
    async def _update_satellite_positions(self):
        """更新所有衛星位置"""
        current_time = datetime.now(timezone.utc)
        
        for satellite_id, ephemeris in self.active_satellites.items():
            try:
                # 計算當前位置
                lat, lon, alt = ephemeris.calculate_position_at_time(current_time)
                
                # 更新位置
                ephemeris.latitude = lat
                ephemeris.longitude = lon
                ephemeris.altitude = alt
                
            except Exception as e:
                self.logger.warning(f"⚠️ 更新衛星 {satellite_id} 位置失敗: {e}")
    
    async def _calculate_visible_satellites(self):
        """計算當前可見衛星"""
        current_time = datetime.now(timezone.utc)
        observer_lat = self.observer_location['latitude']
        observer_lon = self.observer_location['longitude']
        min_elevation = self.observer_location['min_elevation']
        
        new_visible_satellites = {}
        
        for satellite_id, ephemeris in self.active_satellites.items():
            try:
                # 檢查可見性
                is_visible = ephemeris.is_visible_from_location(
                    observer_lat, observer_lon, min_elevation
                )
                
                if is_visible:
                    # 計算詳細可見性參數
                    visible_sat = self._calculate_satellite_visibility_params(
                        satellite_id, ephemeris, current_time
                    )
                    new_visible_satellites[satellite_id] = visible_sat
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 計算衛星 {satellite_id} 可見性失敗: {e}")
        
        # 更新可見衛星列表
        self.visible_satellites = new_visible_satellites
        
        self.logger.debug(
            f"🛰️ 當前可見衛星: {len(self.visible_satellites)} 顆 "
            f"({list(self.visible_satellites.keys())})"
        )
    
    def _calculate_satellite_visibility_params(
        self, satellite_id: str, ephemeris: SatelliteEphemeris, current_time: datetime
    ) -> VisibleSatellite:
        """計算衛星可見性參數"""
        observer_lat = self.observer_location['latitude']
        observer_lon = self.observer_location['longitude']
        
        # 計算角度和距離 (簡化計算)
        lat_diff = math.radians(ephemeris.latitude - observer_lat)
        lon_diff = math.radians(ephemeris.longitude - observer_lon)
        
        # 方位角計算
        azimuth = math.atan2(
            math.sin(lon_diff),
            math.cos(math.radians(observer_lat)) * math.tan(math.radians(ephemeris.latitude)) -
            math.sin(math.radians(observer_lat)) * math.cos(lon_diff)
        )
        azimuth_degrees = (math.degrees(azimuth) + 360) % 360
        
        # 仰角計算 (簡化)
        earth_radius = 6371.0
        angular_distance = math.acos(
            math.sin(math.radians(observer_lat)) * math.sin(math.radians(ephemeris.latitude)) +
            math.cos(math.radians(observer_lat)) * math.cos(math.radians(ephemeris.latitude)) *
            math.cos(lon_diff)
        )
        
        satellite_distance = math.sqrt(
            (earth_radius + ephemeris.altitude) ** 2 +
            earth_radius ** 2 -
            2 * earth_radius * (earth_radius + ephemeris.altitude) * math.cos(angular_distance)
        )
        
        elevation = math.asin(
            ((earth_radius + ephemeris.altitude) * math.sin(angular_distance)) / satellite_distance
        ) - angular_distance
        elevation_degrees = math.degrees(elevation)
        
        # 都卜勒頻移計算 (簡化)
        doppler_shift = self._calculate_doppler_shift(ephemeris, observer_lat, observer_lon)
        
        # 確定可見性狀態
        if satellite_id in self.visible_satellites:
            old_elevation = self.visible_satellites[satellite_id].elevation_angle
            if elevation_degrees > old_elevation:
                visibility_status = SatelliteVisibilityStatus.RISING
            elif elevation_degrees < old_elevation:
                visibility_status = SatelliteVisibilityStatus.SETTING
            else:
                visibility_status = SatelliteVisibilityStatus.VISIBLE
        else:
            visibility_status = SatelliteVisibilityStatus.RISING
        
        return VisibleSatellite(
            satellite_id=satellite_id,
            ephemeris=ephemeris,
            visibility_status=visibility_status,
            elevation_angle=elevation_degrees,
            azimuth_angle=azimuth_degrees,
            distance=satellite_distance,
            doppler_shift=doppler_shift,
            first_visible_time=current_time,
            last_update_time=current_time
        )
    
    def _calculate_doppler_shift(self, ephemeris: SatelliteEphemeris, 
                               observer_lat: float, observer_lon: float) -> float:
        """計算都卜勒頻移"""
        # 簡化的都卜勒計算
        # 實際實現應考慮完整的相對速度向量
        
        # 假設頻率
        carrier_frequency = 2.0e9  # 2 GHz
        light_speed = 3.0e8  # m/s
        
        # 簡化的相對徑向速度估算 (km/s)
        orbital_velocity = 7.5  # LEO 典型軌道速度
        
        # 基於仰角的徑向速度分量
        if ephemeris.latitude != observer_lat or ephemeris.longitude != observer_lon:
            lat_diff = ephemeris.latitude - observer_lat
            lon_diff = ephemeris.longitude - observer_lon
            
            # 簡化的徑向速度計算
            radial_velocity = orbital_velocity * 0.5 * (lat_diff + lon_diff) / 180.0
        else:
            radial_velocity = 0.0
        
        # 都卜勒頻移計算
        doppler_hz = -(radial_velocity * 1000) * carrier_frequency / light_speed
        
        return doppler_hz
    
    async def _generate_sib19_message(self, broadcast_type: SIB19BroadcastType) -> Optional[SIB19Message]:
        """生成 SIB19 廣播消息"""
        if not self.visible_satellites:
            self.logger.debug("📡 無可見衛星，跳過 SIB19 廣播")
            return None
        
        # 選擇要廣播的衛星 (限制數量)
        max_satellites = self.broadcast_config['max_satellites_per_message']
        selected_satellites = list(self.visible_satellites.values())[:max_satellites]
        
        # 生成序列號
        self.sequence_counter += 1
        
        # 創建 SIB19 消息
        sib19_message = SIB19Message(
            message_id=f"sib19_{int(time.time() * 1000)}_{self.sequence_counter}",
            broadcast_time=datetime.now(timezone.utc),
            broadcast_type=broadcast_type,
            validity_duration=self.broadcast_config['validity_duration'],
            sequence_number=self.sequence_counter,
            satellite_ephemeris_list=[sat.ephemeris for sat in selected_satellites],
            ntn_config=self._generate_ntn_config(),
            neighbor_cell_config=self._generate_neighbor_cell_config(selected_satellites),
            service_area_info=self._generate_service_area_info()
        )
        
        return sib19_message
    
    def _generate_ntn_config(self) -> Dict[str, Any]:
        """生成 NTN 配置信息"""
        return {
            'ntn_area_code': 'TW-NTPU-001',
            'time_reference': 'GPS',
            'ephemeris_update_period': 30,
            'max_tracked_satellites': 8,
            'feeder_link_frequency_band': 'Ka',
            'service_link_frequency_band': 'S',
            'satellite_access_stratum': 'transparent',
            'timing_advance_type': 'dedicated'
        }
    
    def _generate_neighbor_cell_config(self, visible_satellites: List[VisibleSatellite]) -> List[Dict[str, Any]]:
        """生成鄰近小區配置"""
        neighbor_configs = []
        
        for i, satellite in enumerate(visible_satellites):
            neighbor_config = {
                'neighbor_cell_id': i + 1,
                'satellite_id': satellite.satellite_id,
                'physical_cell_id': 100 + i,
                'carrier_frequency': 2000000,  # 2GHz in kHz
                'cell_selection_priority': max(1, int(satellite.elevation_angle / 10)),
                'q_rx_lev_min': -110,  # dBm
                'q_qual_min': -20,     # dB
                'threshold_high': satellite.elevation_angle > 15,
                'threshold_low': satellite.elevation_angle < 10
            }
            neighbor_configs.append(neighbor_config)
        
        return neighbor_configs
    
    def _generate_service_area_info(self) -> Dict[str, Any]:
        """生成服務區域信息"""
        return {
            'service_area_id': 'TW-NTPU-SERVICE-AREA',
            'coverage_center': {
                'latitude': self.observer_location['latitude'],
                'longitude': self.observer_location['longitude']
            },
            'coverage_radius_km': 50.0,
            'service_type': 'enhanced_mobile_broadband',
            'supported_services': ['voice', 'data', 'emergency'],
            'qos_parameters': {
                'max_latency_ms': 250,
                'min_throughput_mbps': 1.0,
                'reliability_percentage': 99.5
            }
        }
    
    async def _broadcast_sib19_message(self, message: SIB19Message):
        """廣播 SIB19 消息"""
        try:
            # 記錄廣播歷史
            self.broadcast_history.append(message)
            
            # 限制歷史記錄數量
            if len(self.broadcast_history) > 100:
                self.broadcast_history = self.broadcast_history[-50:]
            
            # 實際廣播實現 (這裡僅記錄日誌)
            self.logger.info(
                f"📡 廣播 SIB19 消息 - ID: {message.message_id}, "
                f"類型: {message.broadcast_type.value}, "
                f"衛星數: {len(message.satellite_ephemeris_list)}, "
                f"序列號: {message.sequence_number}"
            )
            
            # 調試信息
            satellite_names = [eph.satellite_id for eph in message.satellite_ephemeris_list]
            self.logger.debug(f"🛰️ 廣播衛星列表: {satellite_names}")
            
        except Exception as e:
            self.logger.error(f"❌ SIB19 消息廣播失敗: {e}")
    
    # === 公共接口方法 ===
    
    def add_satellite(self, ephemeris: SatelliteEphemeris):
        """添加衛星到活動列表"""
        self.active_satellites[ephemeris.satellite_id] = ephemeris
        self.logger.info(f"➕ 添加衛星: {ephemeris.satellite_id}")
    
    def remove_satellite(self, satellite_id: str):
        """從活動列表移除衛星"""
        if satellite_id in self.active_satellites:
            del self.active_satellites[satellite_id]
            self.logger.info(f"➖ 移除衛星: {satellite_id}")
        
        if satellite_id in self.visible_satellites:
            del self.visible_satellites[satellite_id]
    
    def update_observer_location(self, latitude: float, longitude: float, 
                               altitude: float = 0.1, min_elevation: float = 5.0):
        """更新觀測點位置"""
        self.observer_location.update({
            'latitude': latitude,
            'longitude': longitude, 
            'altitude': altitude,
            'min_elevation': min_elevation
        })
        
        self.logger.info(
            f"📍 更新觀測點位置: ({latitude:.4f}, {longitude:.4f}), "
            f"最小仰角: {min_elevation}°"
        )
    
    async def trigger_emergency_broadcast(self, reason: str) -> SIB19Message:
        """觸發緊急廣播"""
        self.logger.warning(f"🚨 觸發緊急 SIB19 廣播: {reason}")
        
        # 立即更新衛星信息
        await self._update_satellite_positions()
        await self._calculate_visible_satellites()
        
        # 生成緊急廣播消息
        emergency_message = await self._generate_sib19_message(SIB19BroadcastType.EMERGENCY)
        
        if emergency_message:
            # 緊急消息優先處理
            emergency_message.ntn_config['emergency_reason'] = reason
            emergency_message.validity_duration = 120  # 延長有效期
            
            await self._broadcast_sib19_message(emergency_message)
            return emergency_message
        else:
            raise Exception("無法生成緊急 SIB19 廣播消息")
    
    def get_current_visible_satellites(self) -> List[Dict[str, Any]]:
        """獲取當前可見衛星列表"""
        visible_list = []
        
        for satellite_id, visible_sat in self.visible_satellites.items():
            visible_info = {
                'satellite_id': satellite_id,
                'elevation_angle': visible_sat.elevation_angle,
                'azimuth_angle': visible_sat.azimuth_angle,
                'distance_km': visible_sat.distance,
                'doppler_shift_hz': visible_sat.doppler_shift,
                'visibility_status': visible_sat.visibility_status.value,
                'signal_strength_dbm': visible_sat.calculate_signal_strength(),
                'last_update': visible_sat.last_update_time.isoformat()
            }
            visible_list.append(visible_info)
        
        # 按仰角排序
        visible_list.sort(key=lambda x: x['elevation_angle'], reverse=True)
        return visible_list
    
    def get_latest_sib19_message(self) -> Optional[Dict[str, Any]]:
        """獲取最新的 SIB19 廣播消息"""
        if not self.broadcast_history:
            return None
        
        latest_message = self.broadcast_history[-1]
        if latest_message.is_valid():
            return latest_message.to_dict()
        else:
            return None
    
    def get_broadcast_statistics(self) -> Dict[str, Any]:
        """獲取廣播統計信息"""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        # 統計最近一小時的廣播
        recent_broadcasts = [
            msg for msg in self.broadcast_history
            if msg.broadcast_time > one_hour_ago
        ]
        
        broadcast_types = {}
        for msg in recent_broadcasts:
            broadcast_types[msg.broadcast_type.value] = broadcast_types.get(
                msg.broadcast_type.value, 0
            ) + 1
        
        return {
            'total_active_satellites': len(self.active_satellites),
            'currently_visible_satellites': len(self.visible_satellites),
            'total_broadcasts_sent': len(self.broadcast_history),
            'recent_broadcasts_1h': len(recent_broadcasts),
            'broadcast_types_1h': broadcast_types,
            'scheduler_running': self.is_running,
            'observer_location': self.observer_location.copy(),
            'broadcast_config': self.broadcast_config.copy()
        }


# === 便利函數 ===

async def create_sib19_broadcast_scheduler() -> SIB19BroadcastScheduler:
    """創建 SIB19 廣播調度器實例"""
    scheduler = SIB19BroadcastScheduler()
    
    # 添加測試衛星數據
    test_satellites = [
        SatelliteEphemeris(
            satellite_id="STARLINK-1007",
            norad_id=44713,
            epoch_time=datetime.now(timezone.utc),
            semi_major_axis=6921.0,
            eccentricity=0.0001,
            inclination=53.0,
            raan=123.45,
            argument_of_perigee=67.89,
            mean_anomaly=123.45,
            mean_motion=15.12345678,
            latitude=25.0,
            longitude=121.5,
            altitude=550.0
        ),
        SatelliteEphemeris(
            satellite_id="STARLINK-1008", 
            norad_id=44714,
            epoch_time=datetime.now(timezone.utc),
            semi_major_axis=6921.0,
            eccentricity=0.0001,
            inclination=53.0,
            raan=124.50,
            argument_of_perigee=68.90,
            mean_anomaly=234.56,
            mean_motion=15.11234567,
            latitude=24.5,
            longitude=121.0,
            altitude=555.0
        )
    ]
    
    for satellite in test_satellites:
        scheduler.add_satellite(satellite)
    
    logger.info("✅ SIB19 廣播調度器初始化完成")
    return scheduler


def create_test_satellite_ephemeris(satellite_id: str, norad_id: int) -> SatelliteEphemeris:
    """創建測試用的衛星星曆"""
    return SatelliteEphemeris(
        satellite_id=satellite_id,
        norad_id=norad_id,
        epoch_time=datetime.now(timezone.utc),
        semi_major_axis=6921.0,
        eccentricity=0.0001,
        inclination=53.0,
        raan=120.0 + (norad_id % 360),
        argument_of_perigee=70.0,
        mean_anomaly=100.0 + (norad_id % 360),
        mean_motion=15.12,
        latitude=24.0 + ((norad_id % 100) / 100.0),
        longitude=121.0 + ((norad_id % 200) / 200.0),
        altitude=550.0
    )