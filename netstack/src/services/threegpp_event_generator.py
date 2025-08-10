#!/usr/bin/env python3
"""
Phase 3: 3GPP NTN 標準事件生成器
生成符合 3GPP TS 38.331 的測量事件，支援學術研究
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MeasurementEventType(Enum):
    """3GPP 測量事件類型"""
    A1 = "A1"  # 服務衛星信號強度高於閾值
    A2 = "A2"  # 服務衛星信號強度低於閾值  
    A3 = "A3"  # 相鄰衛星信號強度比服務衛星強
    A4 = "A4"  # 相鄰衛星信號強度高於閾值
    A5 = "A5"  # 服務衛星信號低於閾值1且相鄰衛星高於閾值2
    A6 = "A6"  # 相鄰衛星信號強度比服務衛星強且高於偏移量
    D2 = "D2"  # 基於距離的換手觸發  # 相鄰衛星信號強度比服務衛星強且高於偏移量

class ThreeGPPEventGenerator:
    """3GPP NTN 標準事件生成器"""
    
    def __init__(self):
        # 3GPP TS 38.331 標準閾值配置
        self.measurement_config = {
            'rsrp_thresholds': {
                'threshold1': -110,  # dBm - A5服務衛星門檻
                'threshold2': -100,  # dBm - A4/A5鄰居衛星門檻
                'threshold3': -90,   # dBm - A1高品質門檻
            },
            'rsrq_thresholds': {
                'threshold1': -15,   # dB
                'threshold2': -10,   # dB
                'threshold3': -5,    # dB
            },
            'hysteresis': 2.0,       # dB
            'time_to_trigger': 160,  # ms
            'offset_a3': 3.0,        # dB
            'offset_a6': 2.0,        # dB
        }
        
        # NTN 特定參數
        self.ntn_config = {
            'doppler_compensation': True,
            'beam_switching_enabled': True,
            'elevation_threshold': 10.0,  # 度
            'max_handover_frequency': 5,  # 每分鐘最大換手次數
        }
        
        # D2 距離換手配置
        self.distance_config = {
            'serving_distance_threshold': 5000.0,    # km - 服務衛星最大距離
            'neighbor_distance_threshold': 3000.0,   # km - 鄰居衛星最大距離
            'distance_hysteresis': 200.0,            # km - 距離滯後參數
            'enable_distance_handover': True,        # 啟用距離換手
            'distance_weight': 0.3,                  # 距離權重(相對於RSRP)
        }
    
    def generate_measurement_events(self, handover_data: Dict) -> List[Dict]:
        """生成符合 3GPP TS 38.331 的測量事件"""
        logger.info("🔬 生成 3GPP NTN 標準測量事件")
        
        events = []
        
        # 提取衛星軌跡數據
        trajectories = handover_data.get('trajectories', {})
        observer_location = handover_data.get('observer_location', {})
        
        for sat_id, trajectory in trajectories.items():
            sat_events = self.generate_satellite_events(sat_id, trajectory, trajectories)
            events.extend(sat_events)
        
        # 按時間排序
        events.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"✅ 生成 {len(events)} 個 3GPP 測量事件")
        return events
    
    def generate_satellite_events(self, serving_sat_id: str, serving_trajectory: List[Dict], 
                                 all_trajectories: Dict[str, List[Dict]]) -> List[Dict]:
        """為單顆衛星生成測量事件"""
        events = []
        
        for i, point in enumerate(serving_trajectory):
            timestamp = point.get('timestamp', i * 60)  # 假設每分鐘一個測量點
            
            # 計算 RSRP 和 RSRQ
            rsrp = self.calculate_rsrp(point)
            rsrq = self.calculate_rsrq(point)
            
            # 獲取服務衛星距離
            serving_distance = point.get('distance_km', point.get('range_km', 1000.0))
            
            # 生成各類測量事件
            events.extend(self.check_a1_event(serving_sat_id, timestamp, rsrp, point))
            events.extend(self.check_a2_event(serving_sat_id, timestamp, rsrp, point))
            
            # 檢查相鄰衛星事件
            neighbor_measurements = self.get_neighbor_measurements(
                timestamp, all_trajectories, serving_sat_id
            )
            
            for neighbor_id, neighbor_rsrp, neighbor_point in neighbor_measurements:
                # 獲取鄰居衛星距離
                neighbor_distance = neighbor_point.get('distance_km', neighbor_point.get('range_km', 1000.0))
                
                # RSRP基礎的換手事件
                events.extend(self.check_a3_event(
                    serving_sat_id, neighbor_id, timestamp, rsrp, neighbor_rsrp, point, neighbor_point
                ))
                events.extend(self.check_a4_event(
                    neighbor_id, timestamp, neighbor_rsrp, neighbor_point
                ))
                events.extend(self.check_a5_event(
                    serving_sat_id, neighbor_id, timestamp, rsrp, neighbor_rsrp, point, neighbor_point
                ))
                events.extend(self.check_a6_event(
                    serving_sat_id, neighbor_id, timestamp, rsrp, neighbor_rsrp, point, neighbor_point
                ))
                
                # 🎯 D2距離基礎的換手事件 - 新增！
                events.extend(self.check_d2_event(
                    serving_sat_id, neighbor_id, timestamp, serving_distance, neighbor_distance, point, neighbor_point
                ))
        
        return events
    
    def calculate_rsrp(self, point: Dict) -> float:
        """計算 RSRP (Reference Signal Received Power)"""
        # 基於信號強度和距離的 RSRP 計算
        signal_strength = point.get('signal_strength', 0.5)
        elevation = point.get('elevation', 30.0)
        range_km = point.get('range_km', 1000.0)
        
        # 自由空間路徑損耗 (Ku 頻段 12 GHz)
        fspl_db = 20 * np.log10(range_km) + 20 * np.log10(12.0) + 32.45
        
        # 仰角增益
        elevation_gain = min(elevation / 90.0, 1.0) * 15  # 最大 15dB
        
        # 假設發射功率 43dBm (20W)
        tx_power = 43.0
        
        # RSRP 計算
        rsrp = tx_power - fspl_db + elevation_gain
        
        # 添加陰影衰落 (對數正態分佈)
        shadow_fading = np.random.normal(0, 4)  # 4dB 標準差
        rsrp += shadow_fading
        
        return rsrp
    
    def calculate_rsrq(self, point: Dict) -> float:
        """計算 RSRQ (Reference Signal Received Quality)"""
        rsrp = self.calculate_rsrp(point)
        
        # 簡化的 RSRQ 計算 (通常 RSRQ = RSRP - RSSI)
        # 假設干擾水平
        interference_level = -105.0  # dBm
        thermal_noise = -174.0 + 10 * np.log10(15e3)  # 15kHz 頻寬的熱雜訊
        
        total_interference = 10 * np.log10(
            10**(interference_level/10) + 10**(thermal_noise/10)
        )
        
        rsrq = rsrp - total_interference
        return rsrq
    
    def get_neighbor_measurements(self, timestamp: float, all_trajectories: Dict[str, List[Dict]], 
                                 serving_sat_id: str) -> List[Tuple[str, float, Dict]]:
        """獲取相鄰衛星測量值"""
        neighbors = []
        
        for sat_id, trajectory in all_trajectories.items():
            if sat_id == serving_sat_id:
                continue
            
            # 找到對應時間點的測量
            point = self.find_measurement_at_time(trajectory, timestamp)
            if point and point.get('is_visible', False):
                rsrp = self.calculate_rsrp(point)
                neighbors.append((sat_id, rsrp, point))
        
        # 按 RSRP 排序，返回前 3 個最強的相鄰衛星
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors[:3]
    
    def find_measurement_at_time(self, trajectory: List[Dict], target_time: float) -> Optional[Dict]:
        """在軌跡中找到指定時間的測量點"""
        for point in trajectory:
            if abs(point.get('timestamp', 0) - target_time) < 30:  # 30秒容差
                return point
        return None
    
    def check_a1_event(self, sat_id: str, timestamp: float, rsrp: float, point: Dict) -> List[Dict]:
        """檢查 A1 事件：服務衛星信號強度高於閾值"""
        events = []
        threshold = self.measurement_config['rsrp_thresholds']['threshold3']
        
        if rsrp > threshold + self.measurement_config['hysteresis']:
            event = self.create_measurement_event(
                MeasurementEventType.A1,
                sat_id,
                timestamp,
                {
                    'serving_rsrp': rsrp,
                    'threshold': threshold,
                    'margin': rsrp - threshold,
                    'elevation': point.get('elevation', 0),
                    'azimuth': point.get('azimuth', 0)
                }
            )
            events.append(event)
        
        return events
    
    def check_a2_event(self, sat_id: str, timestamp: float, rsrp: float, point: Dict) -> List[Dict]:
        """檢查 A2 事件：服務衛星信號強度低於閾值"""
        events = []
        threshold = self.measurement_config['rsrp_thresholds']['threshold1']
        
        if rsrp < threshold - self.measurement_config['hysteresis']:
            event = self.create_measurement_event(
                MeasurementEventType.A2,
                sat_id,
                timestamp,
                {
                    'serving_rsrp': rsrp,
                    'threshold': threshold,
                    'margin': threshold - rsrp,
                    'elevation': point.get('elevation', 0),
                    'handover_required': True
                }
            )
            events.append(event)
        
        return events
    
    def check_a3_event(self, serving_sat_id: str, neighbor_sat_id: str, timestamp: float,
                      serving_rsrp: float, neighbor_rsrp: float, 
                      serving_point: Dict, neighbor_point: Dict) -> List[Dict]:
        """檢查 A3 事件：相鄰衛星信號強度比服務衛星強"""
        events = []
        offset = self.measurement_config['offset_a3']
        hysteresis = self.measurement_config['hysteresis']
        
        if neighbor_rsrp > serving_rsrp + offset + hysteresis:
            event = self.create_measurement_event(
                MeasurementEventType.A3,
                serving_sat_id,
                timestamp,
                {
                    'serving_rsrp': serving_rsrp,
                    'neighbor_rsrp': neighbor_rsrp,
                    'neighbor_sat_id': neighbor_sat_id,
                    'offset': offset,
                    'margin': neighbor_rsrp - serving_rsrp - offset,
                    'serving_elevation': serving_point.get('elevation', 0),
                    'neighbor_elevation': neighbor_point.get('elevation', 0),
                    'handover_candidate': neighbor_sat_id
                }
            )
            events.append(event)
        
        return events
    
    def check_a4_event(self, neighbor_sat_id: str, timestamp: float, 
                      neighbor_rsrp: float, neighbor_point: Dict) -> List[Dict]:
        """檢查 A4 事件：相鄰衛星信號強度高於閾值"""
        events = []
        threshold = self.measurement_config['rsrp_thresholds']['threshold2']
        
        if neighbor_rsrp > threshold + self.measurement_config['hysteresis']:
            event = self.create_measurement_event(
                MeasurementEventType.A4,
                neighbor_sat_id,
                timestamp,
                {
                    'neighbor_rsrp': neighbor_rsrp,
                    'threshold': threshold,
                    'margin': neighbor_rsrp - threshold,
                    'elevation': neighbor_point.get('elevation', 0),
                    'handover_candidate': neighbor_sat_id
                }
            )
            events.append(event)
        
        return events
    
    def check_a5_event(self, serving_sat_id: str, neighbor_sat_id: str, timestamp: float,
                      serving_rsrp: float, neighbor_rsrp: float,
                      serving_point: Dict, neighbor_point: Dict) -> List[Dict]:
        """檢查 A5 事件：服務衛星信號低於閾值1且相鄰衛星高於閾值2"""
        events = []
        threshold1 = self.measurement_config['rsrp_thresholds']['threshold1']
        threshold2 = self.measurement_config['rsrp_thresholds']['threshold2']
        hysteresis = self.measurement_config['hysteresis']
        
        if (serving_rsrp < threshold1 - hysteresis and 
            neighbor_rsrp > threshold2 + hysteresis):
            
            event = self.create_measurement_event(
                MeasurementEventType.A5,
                serving_sat_id,
                timestamp,
                {
                    'serving_rsrp': serving_rsrp,
                    'neighbor_rsrp': neighbor_rsrp,
                    'neighbor_sat_id': neighbor_sat_id,
                    'threshold1': threshold1,
                    'threshold2': threshold2,
                    'serving_margin': threshold1 - serving_rsrp,
                    'neighbor_margin': neighbor_rsrp - threshold2,
                    'handover_required': True,
                    'handover_candidate': neighbor_sat_id
                }
            )
            events.append(event)
        
        return events
    
    def check_a6_event(self, serving_sat_id: str, neighbor_sat_id: str, timestamp: float,
                      serving_rsrp: float, neighbor_rsrp: float,
                      serving_point: Dict, neighbor_point: Dict) -> List[Dict]:
        """檢查 A6 事件：相鄰衛星信號強度比服務衛星強且高於偏移量"""
        events = []
        offset = self.measurement_config['offset_a6']
        hysteresis = self.measurement_config['hysteresis']
        
        if neighbor_rsrp > serving_rsrp + offset + hysteresis:
            event = self.create_measurement_event(
                MeasurementEventType.A6,
                serving_sat_id,
                timestamp,
                {
                    'serving_rsrp': serving_rsrp,
                    'neighbor_rsrp': neighbor_rsrp,
                    'neighbor_sat_id': neighbor_sat_id,
                    'offset': offset,
                    'margin': neighbor_rsrp - serving_rsrp - offset,
                    'handover_candidate': neighbor_sat_id
                }
            )
            events.append(event)
        
        return events

    
    def check_d2_event(self, serving_sat_id: str, neighbor_sat_id: str, timestamp: float,
                       serving_distance: float, neighbor_distance: float,
                       serving_point: Dict, neighbor_point: Dict) -> List[Dict]:
        """檢查 D2 事件：基於距離的換手觸發
        
        觸發條件：
        - 服務衛星距離 > 距離門檻1 (太遠)
        - 鄰居衛星距離 < 距離門檻2 (較近)
        """
        events = []
        
        if not self.distance_config.get('enable_distance_handover', True):
            return events
            
        serving_threshold = self.distance_config['serving_distance_threshold']
        neighbor_threshold = self.distance_config['neighbor_distance_threshold'] 
        hysteresis = self.distance_config['distance_hysteresis']
        
        # D2 觸發條件 - 符合您提到的標準
        condition1 = serving_distance > (serving_threshold + hysteresis)  # 服務衛星太遠
        condition2 = neighbor_distance < (neighbor_threshold - hysteresis)  # 鄰居衛星較近
        
        if condition1 and condition2:
            # 計算距離優勢 (鄰居衛星的距離優勢)
            distance_advantage = serving_distance - neighbor_distance
            
            event = self.create_measurement_event(
                MeasurementEventType.D2,
                serving_sat_id,
                timestamp,
                {
                    'serving_distance_km': serving_distance,
                    'neighbor_distance_km': neighbor_distance,
                    'neighbor_sat_id': neighbor_sat_id,
                    'serving_threshold_km': serving_threshold,
                    'neighbor_threshold_km': neighbor_threshold,
                    'distance_advantage_km': distance_advantage,
                    'serving_elevation': serving_point.get('elevation', 0),
                    'neighbor_elevation': neighbor_point.get('elevation', 0),
                    'handover_required': True,
                    'handover_candidate': neighbor_sat_id,
                    'handover_reason': 'distance_optimization',
                    'expected_improvement_km': distance_advantage
                }
            )
            events.append(event)
            
            logger.info(
                f"🎯 D2事件觸發: {serving_sat_id}→{neighbor_sat_id}, "
                f"距離改善: {distance_advantage:.1f}km "
                f"({serving_distance:.1f}km → {neighbor_distance:.1f}km)"
            )
        
        return events
    
    def create_measurement_event(self, event_type: MeasurementEventType, 
                               sat_id: str, timestamp: float, 
                               measurements: Dict) -> Dict:
        """創建標準化的測量事件"""
        return {
            'event_id': f"{event_type.value}_{sat_id}_{int(timestamp)}",
            'event_type': event_type.value,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat(),
            'serving_satellite_id': sat_id,
            'measurements': measurements,
            'ntn_specific': {
                'doppler_shift': self.calculate_doppler_shift(measurements),
                'beam_id': self.get_beam_id(measurements),
                'elevation_angle': measurements.get('elevation', 0),
                'azimuth_angle': measurements.get('azimuth', 0)
            },
            'standard_compliance': {
                '3gpp_ts': '38.331',
                'version': 'Rel-17',
                'ntn_support': True
            }
        }
    
    def calculate_doppler_shift(self, measurements: Dict) -> float:
        """計算都卜勒頻移 (簡化模型)"""
        # 基於仰角的簡化都卜勒計算
        elevation = measurements.get('elevation', 30.0)
        satellite_velocity = 7.5  # km/s (LEO 衛星典型速度)
        frequency = 12e9  # Hz (Ku 頻段)
        c = 3e8  # 光速 m/s
        
        # 徑向速度分量
        radial_velocity = satellite_velocity * 1000 * np.cos(np.radians(elevation))
        
        # 都卜勒頻移
        doppler_shift = (radial_velocity / c) * frequency
        
        return doppler_shift
    
    def get_beam_id(self, measurements: Dict) -> str:
        """獲取波束 ID (簡化模型)"""
        elevation = measurements.get('elevation', 30.0)
        azimuth = measurements.get('azimuth', 0.0)
        
        # 基於角度的簡化波束分配
        beam_elevation = int(elevation // 15)  # 每 15 度一個仰角波束
        beam_azimuth = int(azimuth // 30)      # 每 30 度一個方位波束
        
        return f"BEAM_{beam_elevation:02d}_{beam_azimuth:02d}"
    
    def generate_academic_report(self, events: List[Dict], output_path: str = "3gpp_analysis_report.json") -> Dict:
        """生成學術研究品質的分析報告"""
        logger.info("📊 生成學術研究分析報告")
        
        # 統計分析
        event_stats = {}
        for event_type in MeasurementEventType:
            event_stats[event_type.value] = len([e for e in events if e['event_type'] == event_type.value])
        
        # 換手分析
        handover_events = [e for e in events if e['measurements'].get('handover_required', False)]
        handover_candidates = [e for e in events if 'handover_candidate' in e['measurements']]
        
        report = {
            'analysis_metadata': {
                'generation_date': datetime.now().isoformat(),
                'total_events': len(events),
                'analysis_duration_hours': (events[-1]['timestamp'] - events[0]['timestamp']) / 3600 if events else 0,
                'standard_compliance': '3GPP TS 38.331 Rel-17'
            },
            'event_statistics': event_stats,
            'handover_analysis': {
                'total_handover_triggers': len(handover_events),
                'total_handover_candidates': len(handover_candidates),
                'handover_rate_per_hour': len(handover_events) / max(1, (events[-1]['timestamp'] - events[0]['timestamp']) / 3600) if events else 0
            },
            'signal_quality_analysis': self.analyze_signal_quality(events),
            'ntn_specific_analysis': self.analyze_ntn_characteristics(events),
            'academic_insights': self.generate_academic_insights(events)
        }
        
        # 保存報告
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 學術分析報告已保存: {output_path}")
        return report
    
    def analyze_signal_quality(self, events: List[Dict]) -> Dict:
        """分析信號品質"""
        rsrp_values = []
        for event in events:
            if 'serving_rsrp' in event['measurements']:
                rsrp_values.append(event['measurements']['serving_rsrp'])
        
        if rsrp_values:
            return {
                'mean_rsrp': np.mean(rsrp_values),
                'std_rsrp': np.std(rsrp_values),
                'min_rsrp': np.min(rsrp_values),
                'max_rsrp': np.max(rsrp_values),
                'rsrp_percentiles': {
                    '10th': np.percentile(rsrp_values, 10),
                    '50th': np.percentile(rsrp_values, 50),
                    '90th': np.percentile(rsrp_values, 90)
                }
            }
        return {}
    
    def analyze_ntn_characteristics(self, events: List[Dict]) -> Dict:
        """分析 NTN 特性"""
        doppler_shifts = []
        elevations = []
        
        for event in events:
            ntn_data = event.get('ntn_specific', {})
            doppler_shifts.append(ntn_data.get('doppler_shift', 0))
            elevations.append(ntn_data.get('elevation_angle', 0))
        
        return {
            'doppler_analysis': {
                'mean_doppler_hz': np.mean(doppler_shifts),
                'max_doppler_hz': np.max(doppler_shifts),
                'doppler_variation_hz': np.std(doppler_shifts)
            },
            'elevation_analysis': {
                'mean_elevation_deg': np.mean(elevations),
                'min_elevation_deg': np.min(elevations),
                'elevation_distribution': {
                    'low_elevation_events': len([e for e in elevations if e < 20]),
                    'medium_elevation_events': len([e for e in elevations if 20 <= e < 60]),
                    'high_elevation_events': len([e for e in elevations if e >= 60])
                }
            }
        }
    
    def generate_academic_insights(self, events: List[Dict]) -> List[str]:
        """生成學術洞察"""
        insights = []
        
        # A3 事件分析
        a3_events = [e for e in events if e['event_type'] == 'A3']
        if a3_events:
            insights.append(f"A3 事件 (相鄰衛星信號更強) 發生 {len(a3_events)} 次，表明頻繁的換手機會")
        
        # 信號品質分析
        low_signal_events = [e for e in events if e['event_type'] == 'A2']
        if low_signal_events:
            insights.append(f"A2 事件 (服務信號低於閾值) 發生 {len(low_signal_events)} 次，需要優化覆蓋")
        
        # NTN 特性洞察
        high_elevation_events = [e for e in events if e.get('ntn_specific', {}).get('elevation_angle', 0) > 60]
        if high_elevation_events:
            insights.append(f"高仰角事件 ({len(high_elevation_events)} 次) 提供更穩定的連接品質")
        
        return insights
