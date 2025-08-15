# 🛰️ F3: A4/A5/D2 事件處理器
"""
A4/A5/D2 Event Processor - 完整3GPP NTN換手事件分析
功能: 精確RSRP計算、事件檢測、優先級決策
符合: 3GPP TS 38.331標準和LEO衛星特性
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import math
import numpy as np

class EventType(Enum):
    """3GPP事件類型"""
    A4 = "A4"  # 鄰近衛星信號優於門檻
    A5 = "A5"  # 服務衛星劣化且鄰近衛星良好
    D2 = "D2"  # LEO衛星距離優化換手

class EventPriority(Enum):
    """事件優先級"""
    HIGH = "HIGH"      # A5事件 - 緊急換手
    MEDIUM = "MEDIUM"  # A4事件 - 標準換手
    LOW = "LOW"        # D2事件 - 優化換手

@dataclass
class SatelliteSignalData:
    """衛星信號數據"""
    satellite_id: str
    constellation: str
    timestamp: datetime
    
    # 位置信息
    latitude: float
    longitude: float
    altitude_km: float
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    
    # 信號特性
    rsrp_dbm: float
    rsrq_db: float
    sinr_db: float
    path_loss_db: float
    
    # 多普勒和延遲
    doppler_shift_hz: float
    propagation_delay_ms: float

@dataclass
class HandoverEvent:
    """換手事件"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    timestamp: datetime
    
    # 涉及衛星
    serving_satellite: SatelliteSignalData
    neighbor_satellite: SatelliteSignalData
    
    # 事件觸發條件
    trigger_conditions: Dict[str, float]
    event_description: str
    
    # 決策信息
    handover_recommended: bool
    confidence_score: float

class A4A5D2EventProcessor:
    """A4/A5/D2事件處理器 - 3GPP NTN標準實現"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 3GPP事件門檻值
        self.event_thresholds = {
            'a4_neighbor_threshold_dbm': -100.0,    # A4: 鄰居衛星RSRP門檻
            'a5_serving_threshold_dbm': -110.0,     # A5: 服務衛星劣化門檻
            'a5_neighbor_threshold_dbm': -100.0,    # A5: 鄰居衛星良好門檻
            'd2_serving_distance_km': 5000.0,       # D2: 服務衛星距離門檻
            'd2_neighbor_distance_km': 3000.0,      # D2: 候選衛星距離門檻
            'hysteresis_db': 3.0,                   # 滯後裕量
            'time_to_trigger_ms': 640               # 觸發時間
        }
        
        # Ku頻段12GHz參數
        self.signal_params = {
            'frequency_ghz': 12.0,                  # Ku頻段中心頻率
            'tx_power_dbm': 43.0,                   # 衛星發射功率
            'antenna_gain_dbi': 35.0,               # 衛星天線增益
            'receiver_gain_dbi': 30.0,              # 地面天線增益
            'system_noise_db': 5.0,                 # 系統噪聲係數
            'fade_margin_db': 10.0,                 # 衰落裕量
            'atmospheric_loss_db': 2.0              # 大氣損耗
        }
        
        # 事件統計
        self.event_statistics = {
            'total_events': 0,
            'a4_events': 0,
            'a5_events': 0,
            'd2_events': 0,
            'handover_recommendations': 0,
            'average_confidence': 0.0
        }
    
    async def process_handover_events(self, 
                                    serving_satellite_timeline: List[SatelliteSignalData],
                                    neighbor_satellites_timeline: List[List[SatelliteSignalData]],
                                    time_range_minutes: int = 200) -> List[HandoverEvent]:
        """處理完整時間軸的換手事件檢測"""
        self.logger.info(f"🔍 開始A4/A5/D2事件檢測 ({time_range_minutes}分鐘時間軸)")
        
        all_handover_events = []
        
        # 確保時間軸長度一致 (200個時間點，30秒間隔)
        timeline_length = len(serving_satellite_timeline)
        if timeline_length != (time_range_minutes * 2):  # 200個時間點
            self.logger.warning(f"⚠️ 時間軸長度不匹配: 期望{time_range_minutes * 2}，實際{timeline_length}")
        
        # 逐時間點檢測事件
        for time_index in range(timeline_length):
            try:
                serving_data = serving_satellite_timeline[time_index]
                neighbor_data_list = [neighbors[time_index] for neighbors in neighbor_satellites_timeline if time_index < len(neighbors)]
                
                # 檢測所有類型的事件
                events_at_time = await self._detect_events_at_timepoint(
                    serving_data, neighbor_data_list
                )
                
                all_handover_events.extend(events_at_time)
                
                # 每50個時間點記錄進度
                if time_index % 50 == 0:
                    self.logger.info(f"🔄 已處理 {time_index}/{timeline_length} 個時間點")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 時間點 {time_index} 事件檢測失敗: {e}")
                continue
        
        # 統計結果
        self._update_event_statistics(all_handover_events)
        
        self.logger.info(f"✅ 事件檢測完成:")
        self.logger.info(f"   總事件數: {self.event_statistics['total_events']}")
        self.logger.info(f"   A4事件: {self.event_statistics['a4_events']}")
        self.logger.info(f"   A5事件: {self.event_statistics['a5_events']}")
        self.logger.info(f"   D2事件: {self.event_statistics['d2_events']}")
        self.logger.info(f"   換手建議: {self.event_statistics['handover_recommendations']}")
        
        return all_handover_events
    
    async def _detect_events_at_timepoint(self, 
                                        serving_satellite: SatelliteSignalData,
                                        neighbor_satellites: List[SatelliteSignalData]) -> List[HandoverEvent]:
        """檢測單個時間點的所有換手事件"""
        
        events = []
        
        for neighbor in neighbor_satellites:
            try:
                # 跳過同一顆衛星
                if neighbor.satellite_id == serving_satellite.satellite_id:
                    continue
                
                # 跳過跨星座換手 (只允許星座內換手)
                if neighbor.constellation != serving_satellite.constellation:
                    continue
                
                # 檢測A4事件
                a4_event = await self._detect_a4_event(serving_satellite, neighbor)
                if a4_event:
                    events.append(a4_event)
                
                # 檢測A5事件
                a5_event = await self._detect_a5_event(serving_satellite, neighbor)
                if a5_event:
                    events.append(a5_event)
                
                # 檢測D2事件
                d2_event = await self._detect_d2_event(serving_satellite, neighbor)
                if d2_event:
                    events.append(d2_event)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 鄰居衛星 {neighbor.satellite_id} 事件檢測失敗: {e}")
                continue
        
        return events
    
    async def _detect_a4_event(self, 
                             serving: SatelliteSignalData, 
                             neighbor: SatelliteSignalData) -> Optional[HandoverEvent]:
        """檢測A4事件: 鄰近衛星信號優於門檻"""
        
        # 3GPP標準: Mn + Ofn + Ocn – Hys > Thresh2
        # 簡化實現: neighbor_rsrp > -100 dBm
        
        neighbor_rsrp = neighbor.rsrp_dbm
        threshold = self.event_thresholds['a4_neighbor_threshold_dbm']
        hysteresis = self.event_thresholds['hysteresis_db']
        
        # A4觸發條件
        a4_condition = neighbor_rsrp > (threshold + hysteresis)
        
        if a4_condition:
            # 計算信心分數
            confidence = self._calculate_confidence_score(
                neighbor_rsrp, threshold, 'a4'
            )
            
            event = HandoverEvent(
                event_id=f"A4_{serving.satellite_id}_{neighbor.satellite_id}_{serving.timestamp.strftime('%H%M%S')}",
                event_type=EventType.A4,
                priority=EventPriority.MEDIUM,
                timestamp=serving.timestamp,
                serving_satellite=serving,
                neighbor_satellite=neighbor,
                trigger_conditions={
                    'neighbor_rsrp_dbm': neighbor_rsrp,
                    'threshold_dbm': threshold,
                    'hysteresis_db': hysteresis,
                    'margin_db': neighbor_rsrp - threshold
                },
                event_description=f"A4事件: 鄰居衛星{neighbor.satellite_id}信號{neighbor_rsrp:.1f}dBm優於門檻{threshold}dBm",
                handover_recommended=confidence > 0.7,
                confidence_score=confidence
            )
            
            return event
        
        return None
    
    async def _detect_a5_event(self, 
                             serving: SatelliteSignalData, 
                             neighbor: SatelliteSignalData) -> Optional[HandoverEvent]:
        """檢測A5事件: 服務衛星劣化且鄰近衛星良好"""
        
        # 3GPP標準雙重條件:
        # 條件1: Mp + Hys < Thresh1 (服務衛星劣化)
        # 條件2: Mn + Ofn + Ocn – Hys > Thresh2 (鄰居衛星良好)
        
        serving_rsrp = serving.rsrp_dbm
        neighbor_rsrp = neighbor.rsrp_dbm
        serving_threshold = self.event_thresholds['a5_serving_threshold_dbm']
        neighbor_threshold = self.event_thresholds['a5_neighbor_threshold_dbm']
        hysteresis = self.event_thresholds['hysteresis_db']
        
        # A5觸發條件
        condition1 = serving_rsrp < (serving_threshold - hysteresis)  # 服務衛星劣化
        condition2 = neighbor_rsrp > (neighbor_threshold + hysteresis)  # 鄰居衛星良好
        
        a5_condition = condition1 and condition2
        
        if a5_condition:
            # 計算信心分數 (A5事件使用更嚴格的評估)
            confidence = self._calculate_confidence_score(
                neighbor_rsrp - serving_rsrp, 10.0, 'a5'
            )
            
            event = HandoverEvent(
                event_id=f"A5_{serving.satellite_id}_{neighbor.satellite_id}_{serving.timestamp.strftime('%H%M%S')}",
                event_type=EventType.A5,
                priority=EventPriority.HIGH,  # A5是最高優先級
                timestamp=serving.timestamp,
                serving_satellite=serving,
                neighbor_satellite=neighbor,
                trigger_conditions={
                    'serving_rsrp_dbm': serving_rsrp,
                    'neighbor_rsrp_dbm': neighbor_rsrp,
                    'serving_threshold_dbm': serving_threshold,
                    'neighbor_threshold_dbm': neighbor_threshold,
                    'hysteresis_db': hysteresis,
                    'rsrp_difference_db': neighbor_rsrp - serving_rsrp
                },
                event_description=f"A5事件: 服務衛星{serving.satellite_id}劣化({serving_rsrp:.1f}dBm)且鄰居{neighbor.satellite_id}良好({neighbor_rsrp:.1f}dBm)",
                handover_recommended=True,  # A5事件通常建議立即換手
                confidence_score=confidence
            )
            
            return event
        
        return None
    
    async def _detect_d2_event(self, 
                             serving: SatelliteSignalData, 
                             neighbor: SatelliteSignalData) -> Optional[HandoverEvent]:
        """檢測D2事件: LEO衛星距離優化換手"""
        
        # LEO特定距離優化換手
        # 觸發條件: 服務衛星距離 > 5000km 且 候選衛星 < 3000km
        
        serving_distance = serving.distance_km
        neighbor_distance = neighbor.distance_km
        serving_threshold = self.event_thresholds['d2_serving_distance_km']
        neighbor_threshold = self.event_thresholds['d2_neighbor_distance_km']
        
        # D2觸發條件
        condition1 = serving_distance > serving_threshold
        condition2 = neighbor_distance < neighbor_threshold
        
        d2_condition = condition1 and condition2
        
        if d2_condition:
            # 計算距離優勢
            distance_advantage = serving_distance - neighbor_distance
            confidence = min(1.0, distance_advantage / 3000.0)  # 3000km作為滿分基準
            
            event = HandoverEvent(
                event_id=f"D2_{serving.satellite_id}_{neighbor.satellite_id}_{serving.timestamp.strftime('%H%M%S')}",
                event_type=EventType.D2,
                priority=EventPriority.LOW,  # D2是優化級別
                timestamp=serving.timestamp,
                serving_satellite=serving,
                neighbor_satellite=neighbor,
                trigger_conditions={
                    'serving_distance_km': serving_distance,
                    'neighbor_distance_km': neighbor_distance,
                    'serving_threshold_km': serving_threshold,
                    'neighbor_threshold_km': neighbor_threshold,
                    'distance_advantage_km': distance_advantage
                },
                event_description=f"D2事件: 服務衛星{serving.satellite_id}距離{serving_distance:.0f}km過遠，鄰居{neighbor.satellite_id}距離{neighbor_distance:.0f}km更近",
                handover_recommended=confidence > 0.5,
                confidence_score=confidence
            )
            
            return event
        
        return None
    
    async def calculate_precise_rsrp(self, satellite_data: SatelliteSignalData) -> float:
        """精確RSRP計算 - Ku頻段12GHz"""
        
        try:
            # 1. 自由空間路徑損耗 (Free Space Path Loss)
            distance_km = satellite_data.distance_km
            frequency_ghz = self.signal_params['frequency_ghz']
            
            # FSPL = 20*log10(d) + 20*log10(f) + 32.45
            fspl_db = (20 * math.log10(distance_km) + 
                      20 * math.log10(frequency_ghz) + 
                      32.45)
            
            # 2. 仰角增益 (Elevation Gain)
            elevation_deg = satellite_data.elevation_deg
            elevation_gain_db = min(elevation_deg / 90.0, 1.0) * 15.0  # 最大15dB增益
            
            # 3. 發射功率和天線增益
            tx_power_dbm = self.signal_params['tx_power_dbm']
            antenna_gain_dbi = self.signal_params['antenna_gain_dbi']
            receiver_gain_dbi = self.signal_params['receiver_gain_dbi']
            
            # 4. 額外損耗
            atmospheric_loss_db = self.signal_params['atmospheric_loss_db']
            system_noise_db = self.signal_params['system_noise_db']
            
            # 5. RSRP計算
            rsrp_dbm = (tx_power_dbm + 
                       antenna_gain_dbi + 
                       receiver_gain_dbi + 
                       elevation_gain_db - 
                       fspl_db - 
                       atmospheric_loss_db - 
                       system_noise_db)
            
            return rsrp_dbm
            
        except Exception as e:
            self.logger.warning(f"⚠️ RSRP計算失敗: {e}")
            return -120.0  # 預設低RSRP值
    
    def _calculate_confidence_score(self, signal_value: float, threshold: float, event_type: str) -> float:
        """計算事件信心分數"""
        
        if event_type == 'a4':
            # A4: 信號越強於門檻，信心越高
            margin = signal_value - threshold
            confidence = min(1.0, max(0.0, margin / 20.0))  # 20dB為滿分
            
        elif event_type == 'a5':
            # A5: RSRP差距越大，信心越高
            confidence = min(1.0, max(0.0, signal_value / 30.0))  # 30dB差距為滿分
            
        elif event_type == 'd2':
            # D2: 距離優勢越大，信心越高
            confidence = signal_value  # 直接使用傳入的計算值
            
        else:
            confidence = 0.5  # 預設中等信心
        
        return confidence
    
    def _update_event_statistics(self, events: List[HandoverEvent]):
        """更新事件統計"""
        
        self.event_statistics['total_events'] = len(events)
        self.event_statistics['a4_events'] = sum(1 for e in events if e.event_type == EventType.A4)
        self.event_statistics['a5_events'] = sum(1 for e in events if e.event_type == EventType.A5)
        self.event_statistics['d2_events'] = sum(1 for e in events if e.event_type == EventType.D2)
        self.event_statistics['handover_recommendations'] = sum(1 for e in events if e.handover_recommended)
        
        if events:
            self.event_statistics['average_confidence'] = sum(e.confidence_score for e in events) / len(events)
        else:
            self.event_statistics['average_confidence'] = 0.0
    
    async def export_event_analysis(self, events: List[HandoverEvent], output_path: str):
        """匯出事件分析結果"""
        try:
            export_data = {
                'analysis_metadata': {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'event_count': len(events),
                    'thresholds': self.event_thresholds,
                    'signal_parameters': self.signal_params
                },
                'statistics': self.event_statistics,
                'events': []
            }
            
            # 匯出事件詳細信息
            for event in events:
                export_data['events'].append({
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'priority': event.priority.value,
                    'timestamp': event.timestamp.isoformat(),
                    'serving_satellite_id': event.serving_satellite.satellite_id,
                    'neighbor_satellite_id': event.neighbor_satellite.satellite_id,
                    'trigger_conditions': event.trigger_conditions,
                    'event_description': event.event_description,
                    'handover_recommended': event.handover_recommended,
                    'confidence_score': round(event.confidence_score, 3)
                })
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 事件分析結果已匯出至: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 事件分析匯出失敗: {e}")

# 使用範例
async def main():
    """F3_A4A5D2事件處理器使用範例"""
    
    config = {
        'event_thresholds': {
            'a4_neighbor_threshold_dbm': -100.0,
            'a5_serving_threshold_dbm': -110.0,
            'd2_serving_distance_km': 5000.0
        },
        'signal_params': {
            'frequency_ghz': 12.0,
            'tx_power_dbm': 43.0
        }
    }
    
    # 初始化事件處理器
    event_processor = A4A5D2EventProcessor(config)
    
    # 模擬信號數據 (實際應來自F1和F2的數據)
    serving_timeline = []  # 服務衛星時間軸
    neighbor_timelines = []  # 鄰居衛星時間軸列表
    
    # 處理換手事件
    handover_events = await event_processor.process_handover_events(
        serving_timeline, neighbor_timelines, time_range_minutes=200
    )
    
    # 匯出分析結果
    await event_processor.export_event_analysis(
        handover_events, '/tmp/f3_event_analysis.json'
    )
    
    print(f"✅ F3_A4A5D2事件處理器測試完成")
    print(f"   檢測事件總數: {len(handover_events)}")

if __name__ == "__main__":
    asyncio.run(main())