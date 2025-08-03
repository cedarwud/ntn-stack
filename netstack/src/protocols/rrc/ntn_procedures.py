"""
Phase 3.1.1: 3GPP NTN-specific RRC Procedures Implementation

實現符合 3GPP TS 38.331 Release 17/18 的 NTN 特定 RRC 程序，包括：
1. NTN-specific RRC Connection Establishment
2. NTN-specific RRC Reconfiguration  
3. NTN-specific RRC Connection Release
4. Timing Advance handling for satellite communication
5. Doppler compensation mechanisms

符合標準：
- 3GPP TS 38.331: NTN Radio Resource Control (RRC) protocol specification
- 3GPP TS 38.300: NR and NG-RAN Overall Description
- 3GPP TS 38.101-5: NR User Equipment radio transmission and reception Part 5: NTN
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class RRCState(Enum):
    """RRC 連接狀態"""
    RRC_IDLE = "RRC_IDLE"
    RRC_INACTIVE = "RRC_INACTIVE" 
    RRC_CONNECTED = "RRC_CONNECTED"


class RRCMessageType(Enum):
    """RRC 消息類型"""
    # Connection Management
    RRC_SETUP_REQUEST = "RrcSetupRequest"
    RRC_SETUP = "RrcSetup"
    RRC_SETUP_COMPLETE = "RrcSetupComplete"
    
    # Reconfiguration
    RRC_RECONFIGURATION = "RrcReconfiguration"
    RRC_RECONFIGURATION_COMPLETE = "RrcReconfigurationComplete"
    
    # Connection Release
    RRC_RELEASE = "RrcRelease"
    
    # Measurement
    MEASUREMENT_REPORT = "MeasurementReport"
    
    # NTN Specific
    NTN_TIMING_ADVANCE_COMMAND = "NtnTimingAdvanceCommand"
    NTN_DOPPLER_COMPENSATION = "NtnDopplerCompensation"


class NTNTimingAdvanceType(Enum):
    """NTN 時間提前量類型"""
    COMMON_TA = "commonTA"          # 公共時間提前量
    DEDICATED_TA = "dedicatedTA"    # 專用時間提前量
    REFERENCE_TA = "referenceTA"    # 參考時間提前量


@dataclass
class NTNTimingAdvance:
    """NTN 時間提前量配置"""
    ta_type: NTNTimingAdvanceType
    ta_value: float  # 微秒
    ta_validity_time: int  # 有效時間 (秒)
    satellite_id: str
    reference_time: datetime
    doppler_pre_compensation: float = 0.0  # Hz
    
    def is_valid(self) -> bool:
        """檢查時間提前量是否有效"""
        age = (datetime.now(timezone.utc) - self.reference_time).total_seconds()
        return age < self.ta_validity_time


@dataclass 
class DopplerCompensation:
    """都卜勒補償配置"""
    frequency_offset_hz: float
    compensation_factor: float
    update_period_ms: int
    satellite_id: str
    ephemeris_time: datetime
    
    def calculate_compensation(self, current_time: datetime) -> float:
        """計算當前時間的都卜勒補償值"""
        time_diff = (current_time - self.ephemeris_time).total_seconds()
        # 簡化的都卜勒計算 (實際應使用軌道動力學)
        compensation = self.frequency_offset_hz * (1 + time_diff * self.compensation_factor / 3600)
        return compensation


@dataclass
class RRCMessage:
    """RRC 消息基類"""
    message_type: RRCMessageType
    message_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cell_identity: Optional[str] = None
    ue_identity: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NTNConnectionContext:
    """NTN 連接上下文"""
    ue_identity: str
    serving_satellite_id: str
    current_state: RRCState
    connection_established_time: datetime
    last_activity_time: datetime
    timing_advance: Optional[NTNTimingAdvance] = None
    doppler_compensation: Optional[DopplerCompensation] = None
    measurement_config: Dict[str, Any] = field(default_factory=dict)
    neighbor_satellites: List[str] = field(default_factory=list)
    
    def update_activity(self):
        """更新活動時間"""
        self.last_activity_time = datetime.now(timezone.utc)
    
    def is_timing_advance_valid(self) -> bool:
        """檢查時間提前量是否有效"""
        return self.timing_advance is not None and self.timing_advance.is_valid()


class NTNRRCProcessor:
    """NTN RRC 程序處理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, NTNConnectionContext] = {}
        self.satellite_info: Dict[str, Dict] = {}
        self.measurement_config: Dict[str, Any] = {
            'measurement_period_ms': 1000,
            'rsrp_threshold_dbm': -110,
            'sinr_threshold_db': 3,
            'a4_threshold_dbm': -105,  # Event A4 threshold
            'd1_distance_threshold_km': 100,  # Event D1 threshold
            'd2_distance_threshold_km': 150   # Event D2 threshold
        }
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def process_rrc_setup_request(self, request: RRCMessage) -> RRCMessage:
        """
        處理 RRC Setup Request (3GPP TS 38.331 Section 5.3.3)
        包含 NTN 特定的時間提前量計算和都卜勒補償
        """
        self.logger.info(f"🔗 處理 RRC Setup Request: {request.message_id}")
        
        ue_identity = request.payload.get('ue_identity')
        if not ue_identity:
            return self._create_rrc_setup_reject(request, "Missing UE identity")
        
        # 選擇服務衛星
        serving_satellite = await self._select_serving_satellite(request)
        if not serving_satellite:
            return self._create_rrc_setup_reject(request, "No suitable satellite available")
        
        # 計算 NTN 時間提前量
        timing_advance = await self._calculate_ntn_timing_advance(
            ue_identity, serving_satellite, request.payload
        )
        
        # 計算都卜勒補償
        doppler_compensation = await self._calculate_doppler_compensation(
            serving_satellite, request.payload
        )
        
        # 創建連接上下文
        connection_context = NTNConnectionContext(
            ue_identity=ue_identity,
            serving_satellite_id=serving_satellite,
            current_state=RRCState.RRC_CONNECTED,
            connection_established_time=datetime.now(timezone.utc),
            last_activity_time=datetime.now(timezone.utc),
            timing_advance=timing_advance,
            doppler_compensation=doppler_compensation
        )
        
        self.active_connections[ue_identity] = connection_context
        
        # 創建 RRC Setup 響應
        setup_response = RRCMessage(
            message_type=RRCMessageType.RRC_SETUP,
            message_id=f"setup_resp_{int(time.time() * 1000)}",
            cell_identity=serving_satellite,
            ue_identity=ue_identity,
            payload={
                'serving_satellite_id': serving_satellite,
                'timing_advance': {
                    'ta_type': timing_advance.ta_type.value,
                    'ta_value_us': timing_advance.ta_value,
                    'validity_time_s': timing_advance.ta_validity_time
                },
                'doppler_compensation': {
                    'frequency_offset_hz': doppler_compensation.frequency_offset_hz,
                    'compensation_factor': doppler_compensation.compensation_factor,
                    'update_period_ms': doppler_compensation.update_period_ms
                },
                'measurement_config': self.measurement_config.copy(),
                'sib19_config': await self._get_sib19_config(serving_satellite)
            }
        )
        
        self.logger.info(f"✅ RRC Setup 完成 - UE: {ue_identity}, 衛星: {serving_satellite}")
        return setup_response
    
    async def process_rrc_reconfiguration(self, reconfig_request: Dict[str, Any]) -> RRCMessage:
        """
        處理 RRC Reconfiguration (3GPP TS 38.331 Section 5.3.5)
        用於衛星切換和測量配置更新
        """
        ue_identity = reconfig_request.get('ue_identity')
        if not ue_identity or ue_identity not in self.active_connections:
            return self._create_error_response("Invalid UE identity")
        
        context = self.active_connections[ue_identity]
        self.logger.info(f"🔄 處理 RRC Reconfiguration - UE: {ue_identity}")
        
        # 處理衛星切換
        if 'target_satellite_id' in reconfig_request:
            await self._process_satellite_handover(context, reconfig_request)
        
        # 更新測量配置
        if 'measurement_config' in reconfig_request:
            context.measurement_config.update(reconfig_request['measurement_config'])
        
        # 更新鄰近衛星列表
        if 'neighbor_satellites' in reconfig_request:
            context.neighbor_satellites = reconfig_request['neighbor_satellites']
        
        context.update_activity()
        
        # 創建 Reconfiguration 響應
        reconfig_response = RRCMessage(
            message_type=RRCMessageType.RRC_RECONFIGURATION,
            message_id=f"reconfig_{int(time.time() * 1000)}",
            ue_identity=ue_identity,
            payload={
                'serving_satellite_id': context.serving_satellite_id,
                'reconfiguration_complete': True,
                'updated_measurement_config': context.measurement_config,
                'neighbor_satellites': context.neighbor_satellites,
                'timing_advance_updated': context.is_timing_advance_valid()
            }
        )
        
        self.logger.info(f"✅ RRC Reconfiguration 完成 - UE: {ue_identity}")
        return reconfig_response
    
    async def process_rrc_release(self, release_request: Dict[str, Any]) -> RRCMessage:
        """
        處理 RRC Release (3GPP TS 38.331 Section 5.3.8)
        釋放 RRC 連接並清理資源
        """
        ue_identity = release_request.get('ue_identity')
        if not ue_identity:
            return self._create_error_response("Missing UE identity")
        
        self.logger.info(f"🔚 處理 RRC Release - UE: {ue_identity}")
        
        # 清理連接上下文
        if ue_identity in self.active_connections:
            context = self.active_connections[ue_identity]
            
            # 記錄連接統計
            connection_duration = (
                datetime.now(timezone.utc) - context.connection_established_time
            ).total_seconds()
            
            self.logger.info(
                f"📊 連接統計 - UE: {ue_identity}, "
                f"衛星: {context.serving_satellite_id}, "
                f"持續時間: {connection_duration:.1f}秒"
            )
            
            del self.active_connections[ue_identity]
        
        # 創建 Release 響應
        release_response = RRCMessage(
            message_type=RRCMessageType.RRC_RELEASE,
            message_id=f"release_{int(time.time() * 1000)}",
            ue_identity=ue_identity,
            payload={
                'release_cause': release_request.get('cause', 'normal'),
                'connection_released': True
            }
        )
        
        self.logger.info(f"✅ RRC Release 完成 - UE: {ue_identity}")
        return release_response
    
    async def process_measurement_report(self, measurement_data: Dict[str, Any]) -> Optional[RRCMessage]:
        """
        處理測量報告 (3GPP TS 38.331 Section 5.5.2)
        分析測量結果並觸發必要的 RRC 程序
        """
        ue_identity = measurement_data.get('ue_identity')
        if not ue_identity or ue_identity not in self.active_connections:
            return None
        
        context = self.active_connections[ue_identity]
        measurements = measurement_data.get('measurements', [])
        
        self.logger.debug(f"📊 處理測量報告 - UE: {ue_identity}, 測量數: {len(measurements)}")
        
        # 分析測量結果
        handover_decision = await self._analyze_measurements_for_handover(
            context, measurements
        )
        
        if handover_decision:
            # 觸發衛星切換
            return await self._initiate_satellite_handover(context, handover_decision)
        
        # 更新測量歷史
        context.update_activity()
        return None
    
    async def update_timing_advance(self, ue_identity: str) -> Optional[RRCMessage]:
        """
        更新時間提前量 (NTN-specific procedure)
        """
        if ue_identity not in self.active_connections:
            return None
        
        context = self.active_connections[ue_identity]
        
        # 檢查是否需要更新時間提前量
        if context.is_timing_advance_valid():
            return None
        
        self.logger.info(f"⏰ 更新時間提前量 - UE: {ue_identity}")
        
        # 計算新的時間提前量
        new_timing_advance = await self._calculate_ntn_timing_advance(
            ue_identity, context.serving_satellite_id, {}
        )
        
        context.timing_advance = new_timing_advance
        context.update_activity()
        
        # 創建時間提前量命令
        ta_command = RRCMessage(
            message_type=RRCMessageType.NTN_TIMING_ADVANCE_COMMAND,
            message_id=f"ta_cmd_{int(time.time() * 1000)}",
            ue_identity=ue_identity,
            payload={
                'timing_advance': {
                    'ta_type': new_timing_advance.ta_type.value,
                    'ta_value_us': new_timing_advance.ta_value,
                    'validity_time_s': new_timing_advance.ta_validity_time
                }
            }
        )
        
        self.logger.info(f"✅ 時間提前量更新完成 - UE: {ue_identity}")
        return ta_command
    
    # === 私有輔助方法 ===
    
    async def _select_serving_satellite(self, request: RRCMessage) -> Optional[str]:
        """選擇服務衛星"""
        # 簡化實現：選擇信號最強的衛星
        # 實際應考慮負載平衡、覆蓋範圍等因素
        available_satellites = list(self.satellite_info.keys())
        if not available_satellites:
            return None
        return available_satellites[0]  # 暫時選擇第一個可用衛星
    
    async def _calculate_ntn_timing_advance(
        self, ue_identity: str, satellite_id: str, payload: Dict
    ) -> NTNTimingAdvance:
        """計算 NTN 時間提前量"""
        # 實際實現應考慮：
        # 1. 衛星位置和 UE 位置
        # 2. 信號傳播延遲
        # 3. 衛星運動速度
        # 4. 地球自轉效應
        
        # 簡化計算（實際應使用 SGP4 和精確的幾何計算）
        base_delay_us = 250000  # 250ms base delay for LEO satellite
        dynamic_offset = hash(satellite_id + ue_identity) % 1000  # 模擬動態偏移
        
        return NTNTimingAdvance(
            ta_type=NTNTimingAdvanceType.DEDICATED_TA,
            ta_value=base_delay_us + dynamic_offset,
            ta_validity_time=30,  # 30秒有效期
            satellite_id=satellite_id,
            reference_time=datetime.now(timezone.utc)
        )
    
    async def _calculate_doppler_compensation(
        self, satellite_id: str, payload: Dict
    ) -> DopplerCompensation:
        """計算都卜勒補償"""
        # 簡化的都卜勒計算
        # 實際應基於衛星軌道參數和 UE 位置
        base_frequency_offset = 1500.0  # Hz
        compensation_factor = 0.001  # 每小時的變化率
        
        return DopplerCompensation(
            frequency_offset_hz=base_frequency_offset,
            compensation_factor=compensation_factor,
            update_period_ms=5000,  # 5秒更新週期
            satellite_id=satellite_id,
            ephemeris_time=datetime.now(timezone.utc)
        )
    
    async def _get_sib19_config(self, satellite_id: str) -> Dict[str, Any]:
        """獲取 SIB19 配置"""
        return {
            'satellite_ephemeris': {
                satellite_id: {
                    'norad_id': 12345,
                    'inclination': 53.0,
                    'raan': 123.45,
                    'mean_motion': 15.12345678
                }
            },
            'epoch_time': datetime.now(timezone.utc).isoformat(),
            'ntn_neigh_cell_config': [],
            'distance_threshold_km': 1000.0
        }
    
    async def _process_satellite_handover(
        self, context: NTNConnectionContext, reconfig_request: Dict
    ) -> None:
        """處理衛星切換"""
        target_satellite = reconfig_request['target_satellite_id']
        old_satellite = context.serving_satellite_id
        
        self.logger.info(
            f"🛰️ 執行衛星切換 - UE: {context.ue_identity}, "
            f"{old_satellite} → {target_satellite}"
        )
        
        # 更新服務衛星
        context.serving_satellite_id = target_satellite
        
        # 重新計算時間提前量和都卜勒補償
        context.timing_advance = await self._calculate_ntn_timing_advance(
            context.ue_identity, target_satellite, {}
        )
        
        context.doppler_compensation = await self._calculate_doppler_compensation(
            target_satellite, {}
        )
    
    async def _analyze_measurements_for_handover(
        self, context: NTNConnectionContext, measurements: List[Dict]
    ) -> Optional[Dict]:
        """分析測量結果以決定是否需要切換"""
        # 簡化的切換決策邏輯
        # 實際應實現完整的 3GPP 測量事件 (A4, D1, D2 等)
        
        current_rsrp = -999
        best_neighbor_rsrp = -999
        best_neighbor_id = None
        
        for measurement in measurements:
            if measurement.get('satellite_id') == context.serving_satellite_id:
                current_rsrp = measurement.get('rsrp_dbm', -999)
            elif measurement.get('rsrp_dbm', -999) > best_neighbor_rsrp:
                best_neighbor_rsrp = measurement.get('rsrp_dbm', -999)
                best_neighbor_id = measurement.get('satellite_id')
        
        # 切換條件：鄰近衛星 RSRP 比當前衛星高 3dB 以上
        if (best_neighbor_id and 
            best_neighbor_rsrp > current_rsrp + 3 and
            best_neighbor_rsrp > self.measurement_config['a4_threshold_dbm']):
            
            return {
                'target_satellite_id': best_neighbor_id,
                'handover_reason': 'signal_quality',
                'source_rsrp': current_rsrp,
                'target_rsrp': best_neighbor_rsrp
            }
        
        return None
    
    async def _initiate_satellite_handover(
        self, context: NTNConnectionContext, handover_decision: Dict
    ) -> RRCMessage:
        """發起衛星切換"""
        target_satellite = handover_decision['target_satellite_id']
        
        self.logger.info(
            f"🚀 發起衛星切換 - UE: {context.ue_identity}, "
            f"目標衛星: {target_satellite}"
        )
        
        # 創建切換命令 (RRC Reconfiguration with mobility control info)
        handover_command = RRCMessage(
            message_type=RRCMessageType.RRC_RECONFIGURATION,
            message_id=f"ho_cmd_{int(time.time() * 1000)}",
            ue_identity=context.ue_identity,
            payload={
                'mobility_control_info': {
                    'target_satellite_id': target_satellite,
                    'handover_type': 'satellite_handover',
                    'handover_reason': handover_decision['handover_reason']
                },
                'target_satellite_config': await self._get_sib19_config(target_satellite)
            }
        )
        
        return handover_command
    
    def _create_rrc_setup_reject(self, request: RRCMessage, reason: str) -> RRCMessage:
        """創建 RRC Setup Reject 消息"""
        return RRCMessage(
            message_type=RRCMessageType.RRC_SETUP,
            message_id=f"setup_reject_{int(time.time() * 1000)}",
            payload={
                'setup_result': 'rejected',
                'rejection_reason': reason
            }
        )
    
    def _create_error_response(self, error_message: str) -> RRCMessage:
        """創建錯誤響應"""
        return RRCMessage(
            message_type=RRCMessageType.RRC_RELEASE,
            message_id=f"error_{int(time.time() * 1000)}",
            payload={
                'error': True,
                'error_message': error_message
            }
        )
    
    # === 狀態查詢方法 ===
    
    def get_active_connections(self) -> Dict[str, Dict]:
        """獲取所有活動連接狀態"""
        connections = {}
        for ue_identity, context in self.active_connections.items():
            connections[ue_identity] = {
                'serving_satellite_id': context.serving_satellite_id,
                'current_state': context.current_state.value,
                'connection_duration': (
                    datetime.now(timezone.utc) - context.connection_established_time
                ).total_seconds(),
                'timing_advance_valid': context.is_timing_advance_valid(),
                'neighbor_satellites_count': len(context.neighbor_satellites)
            }
        return connections
    
    def get_connection_statistics(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        total_connections = len(self.active_connections)
        satellites_in_use = set(
            ctx.serving_satellite_id for ctx in self.active_connections.values()
        )
        
        return {
            'total_active_connections': total_connections,
            'unique_satellites_in_use': len(satellites_in_use),
            'satellites_in_use': list(satellites_in_use),
            'average_connection_age': self._calculate_average_connection_age()
        }
    
    def _calculate_average_connection_age(self) -> float:
        """計算平均連接年齡"""
        if not self.active_connections:
            return 0.0
        
        total_age = sum(
            (datetime.now(timezone.utc) - ctx.connection_established_time).total_seconds()
            for ctx in self.active_connections.values()
        )
        
        return total_age / len(self.active_connections)


# === 便利函數 ===

async def create_ntn_rrc_processor() -> NTNRRCProcessor:
    """創建 NTN RRC 處理器實例"""
    processor = NTNRRCProcessor()
    
    # 初始化衛星信息 (實際應從數據庫或 API 獲取)
    processor.satellite_info = {
        'STARLINK-1007': {'norad_id': 44713, 'name': 'STARLINK-1007'},
        'STARLINK-1008': {'norad_id': 44714, 'name': 'STARLINK-1008'},
        'ONEWEB-0001': {'norad_id': 44235, 'name': 'ONEWEB-0001'}
    }
    
    logger.info("✅ NTN RRC 處理器初始化完成")
    return processor


# === 測試輔助函數 ===

def create_test_rrc_setup_request(ue_identity: str) -> RRCMessage:
    """創建測試用的 RRC Setup Request"""
    return RRCMessage(
        message_type=RRCMessageType.RRC_SETUP_REQUEST,
        message_id=f"test_setup_{int(time.time() * 1000)}",
        payload={
            'ue_identity': ue_identity,
            'establishment_cause': 'mo_data',
            'selected_plmn_identity': '46692'
        }
    )


def create_test_measurement_report(ue_identity: str, measurements: List[Dict]) -> Dict[str, Any]:
    """創建測試用的測量報告"""
    return {
        'ue_identity': ue_identity,
        'measurement_id': f"meas_{int(time.time() * 1000)}",
        'measurements': measurements,
        'report_timestamp': datetime.now(timezone.utc).isoformat()
    }