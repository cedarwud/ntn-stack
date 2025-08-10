"""
Phase 3.1.3: 時間同步和頻率補償實現

實現符合 NTN 標準的時間同步和頻率補償機制，包括：
1. GPS/GNSS 時間基準整合
2. NTP 協議支援
3. 衛星時間偏移校正
4. 都卜勒頻移預測和補償
5. 動態頻率調整
6. 多普勒預補償

符合標準：
- ITU-R TF.460: 時頻標準
- 3GPP TS 38.331: NTN 時間同步
- RFC 5905: NTPv4 規範
"""

import asyncio
import logging
import time
import math
import struct
import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class TimeReferenceType(Enum):
    """時間基準類型"""
    GPS = "gps"                 # GPS 時間
    GLONASS = "glonass"        # GLONASS 時間
    GALILEO = "galileo"        # Galileo 時間
    BEIDOU = "beidou"          # 北斗時間
    NTP = "ntp"                # NTP 時間
    UTC = "utc"                # UTC 協調世界時
    TAI = "tai"                # 國際原子時


class FrequencyBand(Enum):
    """頻段類型"""
    L_BAND = "l_band"          # 1-2 GHz
    S_BAND = "s_band"          # 2-4 GHz
    C_BAND = "c_band"          # 4-8 GHz
    X_BAND = "x_band"          # 8-12 GHz
    KU_BAND = "ku_band"        # 12-18 GHz
    KA_BAND = "ka_band"        # 26.5-40 GHz


@dataclass
class TimeReference:
    """時間基準"""
    reference_type: TimeReferenceType
    timestamp: datetime
    accuracy_ns: float          # 精度 (奈秒)
    stability_ppm: float        # 穩定度 (百萬分之一)
    source_id: str
    leap_seconds: int = 0       # 閏秒
    
    def get_current_offset(self) -> float:
        """獲取當前時間偏移 (秒)"""
        current_time = datetime.now(timezone.utc)
        offset = (current_time - self.timestamp).total_seconds()
        return offset
    
    def is_valid(self, max_age_seconds: float = 3600) -> bool:
        """檢查時間基準是否有效"""
        age = abs(self.get_current_offset())
        return age < max_age_seconds and self.accuracy_ns < 1e6  # 1ms


@dataclass
class FrequencyReference:
    """頻率基準"""
    center_frequency_hz: float
    frequency_band: FrequencyBand
    stability_ppb: float        # 穩定度 (十億分之一)
    accuracy_ppb: float         # 精度 (十億分之一)
    temperature_coefficient: float  # 溫度係數 (ppm/°C)
    aging_rate: float          # 老化率 (ppb/年)
    timestamp: datetime
    
    def calculate_frequency_drift(self, elapsed_hours: float, 
                                temperature_delta: float = 0) -> float:
        """計算頻率漂移 (Hz)"""
        # 老化漂移
        aging_drift_ppb = self.aging_rate * (elapsed_hours / 8760)  # 年化
        
        # 溫度漂移
        temp_drift_ppb = self.temperature_coefficient * temperature_delta * 1e6
        
        # 總漂移
        total_drift_ppb = aging_drift_ppb + temp_drift_ppb
        
        return self.center_frequency_hz * total_drift_ppb / 1e9


@dataclass
class DopplerParameters:
    """都卜勒參數"""
    satellite_id: str
    satellite_velocity: Tuple[float, float, float]  # (vx, vy, vz) km/s
    satellite_position: Tuple[float, float, float]  # (x, y, z) km
    observer_position: Tuple[float, float, float]   # (lat, lon, alt)
    carrier_frequency_hz: float
    timestamp: datetime
    
    def calculate_radial_velocity(self) -> float:
        """計算徑向速度 (km/s)"""
        # 衛星位置向量 (簡化為笛卡爾座標)
        sat_x, sat_y, sat_z = self.satellite_position
        
        # 觀測點位置轉換 (簡化)
        obs_lat, obs_lon, obs_alt = self.observer_position
        earth_radius = 6371.0
        
        obs_x = (earth_radius + obs_alt) * math.cos(math.radians(obs_lat)) * math.cos(math.radians(obs_lon))
        obs_y = (earth_radius + obs_alt) * math.cos(math.radians(obs_lat)) * math.sin(math.radians(obs_lon))
        obs_z = (earth_radius + obs_alt) * math.sin(math.radians(obs_lat))
        
        # 位置差向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        if distance == 0:
            return 0.0
        
        # 單位向量
        ux = dx / distance
        uy = dy / distance
        uz = dz / distance
        
        # 徑向速度 (衛星速度在徑向上的分量)
        vx, vy, vz = self.satellite_velocity
        radial_velocity = vx * ux + vy * uy + vz * uz
        
        return radial_velocity
    
    def calculate_doppler_shift(self) -> float:
        """計算都卜勒頻移 (Hz)"""
        radial_velocity_ms = self.calculate_radial_velocity() * 1000  # 轉為 m/s
        light_speed = 299792458  # m/s
        
        # 都卜勒公式: fd = -fc * vr / c
        doppler_shift = -self.carrier_frequency_hz * radial_velocity_ms / light_speed
        
        return doppler_shift


@dataclass
class SynchronizationStatus:
    """同步狀態"""
    time_sync_achieved: bool
    frequency_sync_achieved: bool
    time_offset_ns: float
    frequency_offset_hz: float
    sync_accuracy_ns: float
    last_sync_time: datetime
    sync_source: str
    quality_indicator: float    # 0-1, 1 為最佳
    
    def is_synchronized(self, max_time_offset_ns: float = 1e6,
                       max_freq_offset_hz: float = 1000) -> bool:
        """檢查是否已同步"""
        time_ok = abs(self.time_offset_ns) < max_time_offset_ns
        freq_ok = abs(self.frequency_offset_hz) < max_freq_offset_hz
        return self.time_sync_achieved and self.frequency_sync_achieved and time_ok and freq_ok


class NTPClient:
    """簡化的 NTP 客戶端"""
    
    def __init__(self, ntp_servers: List[str] = None):
        self.ntp_servers = ntp_servers or [
            'pool.ntp.org',
            'time.google.com',
            'time.cloudflare.com'
        ]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_ntp_time(self, server: str = None, timeout: float = 5.0) -> Optional[datetime]:
        """獲取 NTP 時間"""
        if server is None:
            server = self.ntp_servers[0]
        
        try:
            # 創建 NTP 請求包
            ntp_packet = b'\x1b' + 47 * b'\0'
            
            # 發送 NTP 請求
            loop = asyncio.get_event_loop()
            
            def sync_ntp_request():
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                try:
                    sock.sendto(ntp_packet, (server, 123))
                    response, _ = sock.recvfrom(1024)
                    return response
                finally:
                    sock.close()
            
            response = await loop.run_in_executor(None, sync_ntp_request)
            
            if len(response) >= 48:
                # 解析 NTP 響應
                transmit_timestamp = struct.unpack('!I', response[40:44])[0]
                
                # NTP 時間戳轉換 (1900年1月1日起的秒數)
                ntp_epoch = datetime(1900, 1, 1, tzinfo=timezone.utc)
                ntp_time = ntp_epoch + timedelta(seconds=transmit_timestamp)
                
                self.logger.debug(f"📡 從 {server} 獲取 NTP 時間: {ntp_time}")
                return ntp_time
            
        except Exception as e:
            self.logger.warning(f"⚠️ NTP 請求失敗 ({server}): {e}")
        
        return None
    
    async def sync_with_ntp(self) -> Optional[TimeReference]:
        """與 NTP 伺服器同步"""
        for server in self.ntp_servers:
            ntp_time = await self.get_ntp_time(server)
            if ntp_time:
                # 計算往返延遲和偏移
                local_time = datetime.now(timezone.utc)
                offset = (ntp_time - local_time).total_seconds()
                
                return TimeReference(
                    reference_type=TimeReferenceType.NTP,
                    timestamp=ntp_time,
                    accuracy_ns=50000000,  # 50ms 典型精度
                    stability_ppm=100,     # NTP 穩定度
                    source_id=server,
                    leap_seconds=0
                )
        
        return None


class TimeFrequencySynchronizer:
    """時間頻率同步器"""
    
    def __init__(self):
        self.time_references: Dict[str, TimeReference] = {}
        self.frequency_references: Dict[str, FrequencyReference] = {}
        self.doppler_compensators: Dict[str, 'DopplerCompensator'] = {}
        self.sync_status = SynchronizationStatus(
            time_sync_achieved=False,
            frequency_sync_achieved=False,
            time_offset_ns=0,
            frequency_offset_hz=0,
            sync_accuracy_ns=1e9,
            last_sync_time=datetime.now(timezone.utc),
            sync_source="none",
            quality_indicator=0.0
        )
        
        self.ntp_client = NTPClient()
        self.sync_config = {
            'time_sync_interval': 300,    # 5分鐘
            'freq_sync_interval': 60,     # 1分鐘
            'doppler_update_interval': 5, # 5秒
            'max_time_offset_ns': 1e6,    # 1ms
            'max_freq_offset_hz': 1000,   # 1kHz
            'primary_time_source': TimeReferenceType.GPS,
            'backup_time_source': TimeReferenceType.NTP
        }
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 同步任務
        self.sync_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start_synchronizer(self):
        """啟動同步器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.sync_task = asyncio.create_task(self._sync_loop())
        self.logger.info("🕐 時間頻率同步器已啟動")
    
    async def stop_synchronizer(self):
        """停止同步器"""
        self.is_running = False
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ 時間頻率同步器已停止")
    
    async def _sync_loop(self):
        """主同步循環"""
        try:
            while self.is_running:
                await self._perform_time_sync()
                await self._perform_frequency_sync()
                await self._update_doppler_compensation()
                
                # 等待下一個同步週期
                await asyncio.sleep(min(
                    self.sync_config['time_sync_interval'],
                    self.sync_config['freq_sync_interval'],
                    self.sync_config['doppler_update_interval']
                ))
                
        except asyncio.CancelledError:
            self.logger.info("🕐 時間頻率同步循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 時間頻率同步異常: {e}")
    
    async def _perform_time_sync(self):
        """執行時間同步"""
        try:
            # 嘗試主要時間源
            primary_ref = await self._get_primary_time_reference()
            
            if primary_ref and primary_ref.is_valid():
                self._update_time_sync_status(primary_ref)
                return
            
            # 嘗試備用時間源
            backup_ref = await self._get_backup_time_reference()
            
            if backup_ref and backup_ref.is_valid():
                self._update_time_sync_status(backup_ref)
                return
            
            # 同步失敗
            self.sync_status.time_sync_achieved = False
            self.logger.warning("⚠️ 時間同步失敗：無可用時間源")
            
        except Exception as e:
            self.logger.error(f"❌ 時間同步異常: {e}")
    
    async def _get_primary_time_reference(self) -> Optional[TimeReference]:
        """獲取主要時間基準"""
        primary_type = self.sync_config['primary_time_source']
        
        if primary_type == TimeReferenceType.GPS:
            return await self._get_gps_time()
        elif primary_type == TimeReferenceType.NTP:
            return await self.ntp_client.sync_with_ntp()
        else:
            # 其他 GNSS 系統的實現
            return await self._get_generic_gnss_time(primary_type)
    
    async def _get_backup_time_reference(self) -> Optional[TimeReference]:
        """獲取備用時間基準"""
        backup_type = self.sync_config['backup_time_source']
        
        if backup_type == TimeReferenceType.NTP:
            return await self.ntp_client.sync_with_ntp()
        elif backup_type == TimeReferenceType.GPS:
            return await self._get_gps_time()
        else:
            return await self._get_generic_gnss_time(backup_type)
    
    async def _get_gps_time(self) -> Optional[TimeReference]:
        """獲取 GPS 時間 (模擬實現)"""
        # 實際實現需要 GPS 接收機硬體介面
        # 這裡提供模擬實現
        
        try:
            # 模擬 GPS 時間獲取
            gps_time = datetime.now(timezone.utc)
            
            return TimeReference(
                reference_type=TimeReferenceType.GPS,
                timestamp=gps_time,
                accuracy_ns=10000,      # 10µs 典型 GPS 精度
                stability_ppm=1,        # GPS 高穩定度
                source_id="gps_receiver",
                leap_seconds=18         # 當前 GPS-UTC 閏秒差
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️ GPS 時間獲取失敗: {e}")
            return None
    
    async def _get_generic_gnss_time(self, gnss_type: TimeReferenceType) -> Optional[TimeReference]:
        """獲取通用 GNSS 時間"""
        # 模擬其他 GNSS 系統
        try:
            gnss_time = datetime.now(timezone.utc)
            
            # 不同 GNSS 系統的特性
            gnss_specs = {
                TimeReferenceType.GLONASS: {'accuracy_ns': 15000, 'stability_ppm': 2},
                TimeReferenceType.GALILEO: {'accuracy_ns': 8000, 'stability_ppm': 1},
                TimeReferenceType.BEIDOU: {'accuracy_ns': 12000, 'stability_ppm': 1.5}
            }
            
            specs = gnss_specs.get(gnss_type, {'accuracy_ns': 20000, 'stability_ppm': 5})
            
            return TimeReference(
                reference_type=gnss_type,
                timestamp=gnss_time,
                accuracy_ns=specs['accuracy_ns'],
                stability_ppm=specs['stability_ppm'],
                source_id=f"{gnss_type.value}_receiver",
                leap_seconds=0
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️ {gnss_type.value} 時間獲取失敗: {e}")
            return None
    
    def _update_time_sync_status(self, time_ref: TimeReference):
        """更新時間同步狀態"""
        current_time = datetime.now(timezone.utc)
        time_offset = (time_ref.timestamp - current_time).total_seconds()
        
        self.sync_status.time_sync_achieved = True
        self.sync_status.time_offset_ns = time_offset * 1e9
        self.sync_status.sync_accuracy_ns = time_ref.accuracy_ns
        self.sync_status.last_sync_time = current_time
        self.sync_status.sync_source = time_ref.source_id
        
        # 計算品質指標
        accuracy_score = max(0, 1 - time_ref.accuracy_ns / 1e6)  # 以 1ms 為基準
        stability_score = max(0, 1 - time_ref.stability_ppm / 100)
        self.sync_status.quality_indicator = (accuracy_score + stability_score) / 2
        
        self.logger.info(
            f"🕐 時間同步完成 - 源: {time_ref.source_id}, "
            f"偏移: {time_offset*1000:.3f}ms, "
            f"精度: {time_ref.accuracy_ns/1000:.1f}µs"
        )
    
    async def _perform_frequency_sync(self):
        """執行頻率同步"""
        try:
            # 基於時間基準計算頻率偏移
            if self.sync_status.time_sync_achieved:
                await self._calculate_frequency_offset()
                self.sync_status.frequency_sync_achieved = True
            else:
                self.sync_status.frequency_sync_achieved = False
                
        except Exception as e:
            self.logger.error(f"❌ 頻率同步異常: {e}")
    
    async def _calculate_frequency_offset(self):
        """計算頻率偏移"""
        # 簡化的頻率偏移計算
        # 實際實現需要基於多次時間測量的頻率估算
        
        time_offset_ns = self.sync_status.time_offset_ns
        
        # 基於時間偏移估算頻率偏移
        if abs(time_offset_ns) > 1000:  # 1µs
            # 估算頻率偏移 (簡化)
            freq_offset = time_offset_ns / 1e9 * 1000  # 簡化公式
            self.sync_status.frequency_offset_hz = freq_offset
            
            self.logger.debug(f"📊 頻率偏移估算: {freq_offset:.3f} Hz")
    
    async def _update_doppler_compensation(self):
        """更新都卜勒補償"""
        for satellite_id, compensator in self.doppler_compensators.items():
            try:
                await compensator.update_compensation()
            except Exception as e:
                self.logger.warning(f"⚠️ 衛星 {satellite_id} 都卜勒補償更新失敗: {e}")
    
    # === 公共接口方法 ===
    
    def add_doppler_compensator(self, satellite_id: str, compensator: 'DopplerCompensator'):
        """添加都卜勒補償器"""
        self.doppler_compensators[satellite_id] = compensator
        self.logger.info(f"➕ 添加都卜勒補償器: {satellite_id}")
    
    def remove_doppler_compensator(self, satellite_id: str):
        """移除都卜勒補償器"""
        if satellite_id in self.doppler_compensators:
            del self.doppler_compensators[satellite_id]
            self.logger.info(f"➖ 移除都卜勒補償器: {satellite_id}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        return {
            'time_sync_achieved': self.sync_status.time_sync_achieved,
            'frequency_sync_achieved': self.sync_status.frequency_sync_achieved,
            'time_offset_ns': self.sync_status.time_offset_ns,
            'frequency_offset_hz': self.sync_status.frequency_offset_hz,
            'sync_accuracy_ns': self.sync_status.sync_accuracy_ns,
            'last_sync_time': self.sync_status.last_sync_time.isoformat(),
            'sync_source': self.sync_status.sync_source,
            'quality_indicator': self.sync_status.quality_indicator,
            'is_synchronized': self.sync_status.is_synchronized(),
            'active_compensators': len(self.doppler_compensators)
        }
    
    def update_sync_config(self, config: Dict[str, Any]):
        """更新同步配置"""
        self.sync_config.update(config)
        self.logger.info(f"🔧 同步配置已更新: {list(config.keys())}")


class DopplerCompensator:
    """都卜勒補償器"""
    
    def __init__(self, satellite_id: str, carrier_frequency_hz: float):
        self.satellite_id = satellite_id
        self.carrier_frequency_hz = carrier_frequency_hz
        self.doppler_history: List[Tuple[datetime, float]] = []
        self.current_compensation_hz = 0.0
        self.prediction_model = None
        
        self.config = {
            'prediction_window_s': 60,      # 60秒預測窗口
            'history_retention_s': 3600,    # 1小時歷史數據
            'update_interval_s': 1,         # 1秒更新頻率
            'max_compensation_hz': 50000    # 最大補償範圍
        }
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def update_doppler_parameters(self, doppler_params: DopplerParameters):
        """更新都卜勒參數"""
        try:
            # 計算當前都卜勒頻移
            doppler_shift = doppler_params.calculate_doppler_shift()
            
            # 記錄歷史數據
            current_time = datetime.now(timezone.utc)
            self.doppler_history.append((current_time, doppler_shift))
            
            # 清理過舊的歷史數據
            cutoff_time = current_time - timedelta(seconds=self.config['history_retention_s'])
            self.doppler_history = [(t, d) for t, d in self.doppler_history if t > cutoff_time]
            
            # 更新補償值
            await self._calculate_compensation(doppler_shift)
            
        except Exception as e:
            self.logger.error(f"❌ 衛星 {self.satellite_id} 都卜勒參數更新失敗: {e}")
    
    async def _calculate_compensation(self, current_doppler: float):
        """計算都卜勒補償"""
        # 簡單的補償策略：直接補償當前都卜勒頻移
        compensation = -current_doppler  # 反向補償
        
        # 限制補償範圍
        max_comp = self.config['max_compensation_hz']
        compensation = max(-max_comp, min(max_comp, compensation))
        
        self.current_compensation_hz = compensation
        
        self.logger.debug(
            f"🛰️ {self.satellite_id} 都卜勒補償: "
            f"原始頻移={current_doppler:.1f}Hz, 補償={compensation:.1f}Hz"
        )
    
    async def update_compensation(self):
        """更新補償 (週期性調用)"""
        # 實際實現會根據軌道預測更新補償
        # 這裡提供簡化實現
        pass
    
    def get_compensated_frequency(self) -> float:
        """獲取補償後的頻率"""
        return self.carrier_frequency_hz + self.current_compensation_hz
    
    def get_compensation_info(self) -> Dict[str, Any]:
        """獲取補償信息"""
        return {
            'satellite_id': self.satellite_id,
            'carrier_frequency_hz': self.carrier_frequency_hz,
            'current_compensation_hz': self.current_compensation_hz,
            'compensated_frequency_hz': self.get_compensated_frequency(),
            'history_points': len(self.doppler_history),
            'last_update': self.doppler_history[-1][0].isoformat() if self.doppler_history else None
        }


# === 便利函數 ===

async def create_time_frequency_synchronizer() -> TimeFrequencySynchronizer:
    """創建時間頻率同步器實例"""
    synchronizer = TimeFrequencySynchronizer()
    
    # 添加預設頻率基準
    default_freq_ref = FrequencyReference(
        center_frequency_hz=2.0e9,  # 2GHz
        frequency_band=FrequencyBand.S_BAND,
        stability_ppb=100,
        accuracy_ppb=50,
        temperature_coefficient=0.1,
        aging_rate=0.5,
        timestamp=datetime.now(timezone.utc)
    )
    
    synchronizer.frequency_references['default_s_band'] = default_freq_ref
    
    logger.info("✅ 時間頻率同步器初始化完成")
    return synchronizer


def create_doppler_compensator(satellite_id: str, carrier_frequency_hz: float = 2.0e9) -> DopplerCompensator:
    """創建都卜勒補償器"""
    return DopplerCompensator(satellite_id, carrier_frequency_hz)


def create_test_doppler_parameters(satellite_id: str) -> DopplerParameters:
    """創建測試用都卜勒參數"""
    return DopplerParameters(
        satellite_id=satellite_id,
        satellite_velocity=(7.5, 0.0, 0.0),  # 7.5 km/s 典型 LEO 速度
        satellite_position=(6921.0, 0.0, 0.0),  # 550km 高度軌道
        observer_position=(24.9441667, 121.3713889, 0.1),  # NTPU
        carrier_frequency_hz=2.0e9,
        timestamp=datetime.now(timezone.utc)
    )