#\!/usr/bin/env python3
"""
D2/A4/A5 換手事件檢測器
基於 3GPP 38.331 標準的衛星換手事件檢測邏輯
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import time
logger = logging.getLogger(__name__)

class HandoverEventDetector:
    """
    3GPP NTN 換手事件檢測器
    
    實現 D2/A4/A5 事件檢測：
    - D2: 服務衛星即將不可見 (elevation ≤ critical_threshold + margin)
    - A4: 鄰近衛星測量值超過門檻 (elevation ≥ execution_threshold)  
    - A5: 服務變差且鄰近變好 (serving < execution & neighbor > pre_handover)
    """
    
    def __init__(self, scene_id: str = "ntpu"):
        """
        初始化事件檢測器
        
        Args:
            scene_id: 場景ID，用於載入對應的門檻參數
        """
        self.scene_id = scene_id
        self.load_scene_thresholds()
        
        # RSRP 門檻 (基於 ITU-R 建議)
        self.rsrp_good_threshold = -110  # dBm
        self.rsrp_poor_threshold = -120  # dBm
        
        # D2 事件預警時間餘量
        self.d2_warning_margin = 2.0  # 度
        
        # 🆕 多普勒補償系統
        try:
            from doppler_compensation_system import DopplerCompensationSystem
            self.doppler_system = DopplerCompensationSystem()
            self.doppler_enabled = True
            logger.info("多普勒補償系統已啟用")
        except ImportError as e:
            logger.warning(f"多普勒補償系統載入失敗: {e}")
            self.doppler_system = None
            self.doppler_enabled = False
        
        # 🆕 動態鏈路預算計算器
        try:
            from dynamic_link_budget_calculator import DynamicLinkBudgetCalculator
            self.link_budget_calculator = DynamicLinkBudgetCalculator()
            self.link_budget_enabled = True
            logger.info("動態鏈路預算計算器已啟用")
        except ImportError as e:
            logger.warning(f"動態鏈路預算計算器載入失敗: {e}")
            self.link_budget_calculator = None
            self.link_budget_enabled = False
        
        # 🆕 SMTC 測量優化系統
        try:
            from smtc_measurement_optimizer import SMTCOptimizer
            self.smtc_optimizer = SMTCOptimizer()
            self.smtc_enabled = True
            logger.info("SMTC 測量優化系統已啟用")
        except ImportError as e:
            logger.warning(f"SMTC 測量優化系統載入失敗: {e}")
            self.smtc_optimizer = None
            self.smtc_enabled = False
        
        # 預設 UE 位置 (NTPU)
        self.default_ue_position = (24.9442, 121.3711, 0.05)  # (lat, lon, alt_km)
        
        logger.info(f"HandoverEventDetector 初始化 - 場景: {scene_id}")
        logger.info(f"  門檻設定: 預備={self.pre_handover_threshold}°, 執行={self.execution_threshold}°, 臨界={self.critical_threshold}°")
        logger.info(f"  多普勒補償: {'啟用' if self.doppler_enabled else '停用'}")
        logger.info(f"  鏈路預算計算: {'啟用' if self.link_budget_enabled else '停用'}")
        logger.info(f"  SMTC 測量優化: {'啟用' if self.smtc_enabled else '停用'}")
    
    def load_scene_thresholds(self):
        """從 scenes.csv 載入場景門檻參數"""
        try:
            scenes_file = Path("/app/data/scenes.csv")
            if not scenes_file.exists():
                raise FileNotFoundError(f"場景配置檔案不存在: {scenes_file}")
            
            import csv
            with open(scenes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['scene_id'] == self.scene_id:
                        self.pre_handover_threshold = float(row['pre_handover_threshold'])
                        self.execution_threshold = float(row['execution_threshold'])
                        self.critical_threshold = float(row['critical_threshold'])
                        self.environment_factor = float(row['environment_factor'])
                        return
            
            raise ValueError(f"找不到場景 {self.scene_id} 的配置")
            
        except Exception as e:
            logger.warning(f"載入場景配置失敗: {e}，使用預設值")
            # NTPU 預設值
            self.pre_handover_threshold = 15.0
            self.execution_threshold = 10.0  
            self.critical_threshold = 5.0
            self.environment_factor = 1.1
    
    def process_orbit_data(self, orbit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理軌道資料，生成換手事件
        
        Args:
            orbit_data: 來自 phase0_precomputed_orbits.json 的軌道資料
            
        Returns:
            Dict: 包含 D2/A4/A5 事件的資料結構
        """
        logger.info("🔍 開始事件檢測處理")
        
        events = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "scene_id": self.scene_id,
                "detection_config": {
                    "pre_handover_threshold": self.pre_handover_threshold,
                    "execution_threshold": self.execution_threshold,
                    "critical_threshold": self.critical_threshold,
                    "d2_warning_margin": self.d2_warning_margin,
                    "rsrp_good_threshold": self.rsrp_good_threshold
                }
            },
            "events": {
                "d2_events": [],
                "a4_events": [],
                "a5_events": []
            },
            "statistics": {
                "total_d2_events": 0,
                "total_a4_events": 0,
                "total_a5_events": 0,
                "analysis_duration_minutes": 0,
                "processed_satellites": 0
            }
        }
        
        # 處理每個星座
        total_processed = 0
        for constellation_name, constellation_data in orbit_data.get("constellations", {}).items():
            satellites = constellation_data.get("orbit_data", {}).get("satellites", {})
            logger.info(f"處理 {constellation_name}: {len(satellites)} 顆衛星")
            
            constellation_events = self._detect_constellation_events(satellites, constellation_name)
            
            # 調試資訊：星座事件統計
            logger.info(f"  {constellation_name} 事件統計: D2={len(constellation_events['d2_events'])}, A4={len(constellation_events['a4_events'])}, A5={len(constellation_events['a5_events'])}")
            
            # 合併事件
            events["events"]["d2_events"].extend(constellation_events["d2_events"])
            events["events"]["a4_events"].extend(constellation_events["a4_events"])
            events["events"]["a5_events"].extend(constellation_events["a5_events"])
            
            total_processed += len(satellites)
        
        # 更新統計
        events["statistics"].update({
            "total_d2_events": len(events["events"]["d2_events"]),
            "total_a4_events": len(events["events"]["a4_events"]),
            "total_a5_events": len(events["events"]["a5_events"]),
            "processed_satellites": total_processed,
            "analysis_duration_minutes": orbit_data.get("metadata", {}).get("duration_minutes", 120)
        })
        
        logger.info(f"✅ 事件檢測完成: D2={events['statistics']['total_d2_events']}, A4={events['statistics']['total_a4_events']}, A5={events['statistics']['total_a5_events']}")
        
        return events

    
    def _detect_constellation_events(self, satellites: Dict[str, Any], constellation_name: str) -> Dict[str, List]:
        """
        檢測單個星座的換手事件 - 3GPP TS 38.331 合規版本
        
        Args:
            satellites: 衛星資料字典
            constellation_name: 星座名稱
            
        Returns:
            Dict: 包含三種事件的字典
        """
        constellation_events = {
            "d2_events": [],
            "a4_events": [],
            "a5_events": []
        }
        
        # 建立時間軸資料結構
        timeline_data = self._build_timeline(satellites, constellation_name)
        
        # 調試資訊：時間軸統計
        total_timeline_points = len(timeline_data)
        total_visible_instances = sum(len(sats) for sats in timeline_data.values())
        logger.info(f"    時間軸: {total_timeline_points} 個時間點, {total_visible_instances} 個可見實例")
        
        # 按時間順序檢測事件
        processed_timestamps = 0
        for timestamp, visible_satellites in timeline_data.items():
            if not visible_satellites:
                continue
                
            # 選擇服務衛星 (假定為仰角最高的衛星)
            serving_satellite = max(visible_satellites, key=lambda sat: sat['elevation_deg'])
            neighbors = [sat for sat in visible_satellites if sat['satellite_id'] != serving_satellite['satellite_id']]
            
            processed_timestamps += 1
            
            # 每100個時間點輸出一次調試資訊
            if processed_timestamps % 100 == 0 or processed_timestamps <= 5:
                logger.info(f"    時間點 {processed_timestamps}: {len(visible_satellites)} 顆可見衛星, 服務衛星仰角={serving_satellite['elevation_deg']:.1f}°")
            
            # ✅ D2 事件檢測：基於地理距離 (3GPP TS 38.331)
            d2_triggered, d2_candidate = self._should_trigger_d2(
                self.default_ue_position, serving_satellite, neighbors
            )
            
            if d2_triggered:
                d2_event = self._create_d2_event(timestamp, serving_satellite, neighbors, d2_candidate)
                if d2_event:
                    constellation_events["d2_events"].append(d2_event)
                    logger.info(f"    ✓ D2 事件: 基於地理距離檢測 - 服務衛星 {serving_satellite['satellite_id']}")
            
            # ✅ A4 事件檢測：基於 RSRP 信號強度 (3GPP TS 38.331)
            a4_candidates = 0
            for neighbor in neighbors:
                if self._should_trigger_a4(neighbor):
                    a4_candidates += 1
                    a4_event = self._create_a4_event(timestamp, neighbor, serving_satellite)
                    if a4_event:
                        constellation_events["a4_events"].append(a4_event)
                        if processed_timestamps <= 5:  # 只在前幾個時間點顯示詳細資訊
                            logger.info(f"    ✓ A4 事件: 基於 RSRP 檢測 - 候選衛星 {neighbor['satellite_id']}")
            
            if processed_timestamps <= 5 and a4_candidates > 0:
                logger.info(f"    A4 候選數: {a4_candidates} 顆衛星符合條件")
            
            # ✅ A5 事件檢測：雙重 RSRP 條件 (3GPP TS 38.331)
            a5_candidates = 0
            for neighbor in neighbors:
                if self._should_trigger_a5(serving_satellite, neighbor):
                    a5_candidates += 1
                    a5_event = self._create_a5_event(timestamp, serving_satellite, neighbor)
                    if a5_event:
                        constellation_events["a5_events"].append(a5_event)
                        if processed_timestamps <= 5:
                            logger.info(f"    ✓ A5 事件: 雙重 RSRP 條件 - 服務 {serving_satellite['satellite_id']} → 候選 {neighbor['satellite_id']}")
            
            if processed_timestamps <= 5 and a5_candidates > 0:
                logger.info(f"    A5 候選數: {a5_candidates} 顆衛星符合條件")
        
        return constellation_events
    
    def _should_trigger_d2(self, ue_position: tuple, serving_satellite: Dict, candidate_satellites: List[Dict]) -> tuple:
        """
        實現 3GPP TS 38.331 D2 事件條件
        Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2
        
        Args:
            ue_position: UE位置 (lat, lon, alt_km)
            serving_satellite: 服務衛星資料
            candidate_satellites: 候選衛星列表
            
        Returns:
            tuple: (is_triggered: bool, selected_candidate: Dict or None)
        """
        if not candidate_satellites:
            return False, None
            
        serving_distance = self._calculate_distance(ue_position, serving_satellite)
        
        # D2 距離門檻 (km) - 基於 LEO 衛星典型參數
        distance_threshold1 = 1500.0  # 與服務衛星距離門檻
        distance_threshold2 = 1200.0  # 與候選衛星距離門檻
        hysteresis = 50.0  # 滯後 (km)
        
        for candidate in candidate_satellites:
            candidate_distance = self._calculate_distance(ue_position, candidate)
            
            # D2-1: 與服務衛星距離超過門檻
            condition1 = serving_distance - hysteresis > distance_threshold1
            
            # D2-2: 與候選衛星距離低於門檻  
            condition2 = candidate_distance + hysteresis < distance_threshold2
            
            if condition1 and condition2:
                logger.debug(f"D2 觸發: 服務距離 {serving_distance:.1f}km > {distance_threshold1}km, "
                           f"候選距離 {candidate_distance:.1f}km < {distance_threshold2}km")
                return True, candidate
        
        return False, None
    
    def _calculate_distance(self, ue_position: tuple, satellite_position: Dict) -> float:
        """
        計算 UE 與衛星的 3D 距離 (km)
        基於 Haversine 公式 + 高度差
        
        Args:
            ue_position: UE位置 (lat, lon, alt_km)  
            satellite_position: 衛星位置資料
            
        Returns:
            float: 3D距離 (km)
        """
        import math
        
        # 地球半徑 (km)
        earth_radius = 6371.0
        
        # UE 位置
        lat1, lon1, alt1 = ue_position
        
        # 衛星位置 - 從 range_km 和 elevation/azimuth 計算
        range_km = satellite_position.get('range_km', 800.0)
        elevation_deg = satellite_position.get('elevation_deg', 45.0)
        azimuth_deg = satellite_position.get('azimuth_deg', 0.0)
        
        # 如果有直接的距離資料，使用它
        if range_km and range_km > 0:
            return range_km
        
        # 否則使用仰角和方位角計算（簡化模型）
        elevation_rad = math.radians(elevation_deg)
        if elevation_deg > 5.0:
            # 基於仰角的距離估算 (LEO 衛星高度約 550km)
            satellite_altitude = 550.0  # km
            distance = satellite_altitude / math.sin(elevation_rad)
            return distance
        else:
            # 低仰角時使用保守估計
            return 2000.0
    
    def _should_trigger_a4(self, candidate_satellite: Dict) -> bool:
        """
        實現 3GPP TS 38.331 A4 事件條件
        Mn + Ofn + Ocn - Hys > Thresh
        
        Args:
            candidate_satellite: 候選衛星資料
            
        Returns:
            bool: 是否觸發 A4 事件
        """
        # 計算 RSRP (基於 ITU-R P.618-14)
        rsrp = self._calculate_rsrp(candidate_satellite)
        
        # 應用偏移量
        measurement_offset = candidate_satellite.get('offset_mo', 0)
        cell_offset = candidate_satellite.get('cell_individual_offset', 0)
        hysteresis = 3.0  # dB
        a4_threshold = -110.0  # dBm
        
        # A4 判斷條件
        adjusted_rsrp = rsrp + measurement_offset + cell_offset - hysteresis
        
        is_triggered = adjusted_rsrp > a4_threshold
        
        if is_triggered:
            logger.debug(f"A4 觸發: RSRP {rsrp:.1f} dBm (調整後 {adjusted_rsrp:.1f}) > {a4_threshold} dBm")
        
        return is_triggered
    
    def _should_trigger_a5(self, serving_satellite: Dict, candidate_satellite: Dict) -> bool:
        """
        實現 3GPP TS 38.331 A5 事件條件
        A5-1: Mp + Hys < Thresh1 (服務衛星變差)
        A5-2: Mn + Ofn + Ocn - Hys > Thresh2 (候選衛星變好)
        
        Args:
            serving_satellite: 服務衛星資料
            candidate_satellite: 候選衛星資料
            
        Returns:
            bool: 是否觸發 A5 事件
        """
        # 計算服務衛星和候選衛星的 RSRP
        serving_rsrp = self._calculate_rsrp(serving_satellite)
        candidate_rsrp = self._calculate_rsrp(candidate_satellite)
        
        hysteresis = 3.0  # dB
        a5_threshold1 = -115.0  # dBm (服務衛星變差門檻)
        a5_threshold2 = -105.0  # dBm (候選衛星變好門檻)
        
        # A5-1 條件檢查：服務衛星信號變差
        condition1 = serving_rsrp + hysteresis < a5_threshold1
        
        # A5-2 條件檢查：候選衛星信號變好
        candidate_offset = (candidate_satellite.get('offset_mo', 0) + 
                           candidate_satellite.get('cell_individual_offset', 0))
        condition2 = candidate_rsrp + candidate_offset - hysteresis > a5_threshold2
        
        is_triggered = condition1 and condition2
        
        if is_triggered:
            logger.debug(f"A5 觸發: 服務RSRP {serving_rsrp:.1f} < {a5_threshold1} dBm, "
                        f"候選RSRP {candidate_rsrp:.1f} > {a5_threshold2} dBm")
        
        return is_triggered
    
    def _calculate_rsrp(self, satellite: Dict) -> float:
        """
        計算 LEO 衛星 RSRP 值 (dBm)
        基於 ITU-R P.618-14 標準
        
        Args:
            satellite: 衛星資料
            
        Returns:
            float: RSRP 值 (dBm)
        """
        import math
        import random
        
        # 基本參數
        distance_km = satellite.get('range_km', 800.0)
        frequency_ghz = 28.0  # Ka 頻段
        elevation_deg = satellite.get('elevation_deg', 45.0)
        
        # 自由空間路徑損耗 (dB)
        fspl = 32.45 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz)
        
        # 大氣衰減 (基於仰角)
        elevation_rad = math.radians(elevation_deg)
        if elevation_deg > 5.0:
            atmospheric_loss = 0.5 / math.sin(elevation_rad)  # 簡化模型
        else:
            atmospheric_loss = 10.0  # 低仰角大氣損耗嚴重
        
        # 天線增益與功率
        tx_power_dbm = 43.0  # 衛星發射功率
        rx_antenna_gain = 25.0  # 用戶設備天線增益
        
        # RSRP 計算
        rsrp = tx_power_dbm - fspl - atmospheric_loss + rx_antenna_gain
        
        # 添加快衰落和陰影衰落  
        fast_fading = random.gauss(0, 2.0)  # 標準差 2dB
        shadow_fading = random.gauss(0, 4.0)  # 標準差 4dB
        
        return rsrp + fast_fading + shadow_fading
    
    def _calculate_distance_urgency(self, distance_km: float) -> str:
        """
        基於距離計算換手緊急程度
        
        Args:
            distance_km: 與服務衛星距離
            
        Returns:
            str: 緊急程度 (low/medium/high/critical)
        """
        if distance_km > 2000:
            return "critical"
        elif distance_km > 1800:
            return "high" 
        elif distance_km > 1500:
            return "medium"
        else:
            return "low"
    
    def _build_timeline(self, satellites: Dict[str, Any], constellation_name: str) -> Dict[str, List]:
        """
        建立時間軸資料結構，使用時間窗口聚合實現多衛星同時可見
        
        修正版：實現時間窗口機制，聚合相近時間點的衛星
        
        Args:
            satellites: 衛星資料字典
            constellation_name: 星座名稱
            
        Returns:
            Dict: 時間戳對應的可見衛星列表
        """
        logger.info(f"🔍 建立 {constellation_name} 星座時間軸，處理 {len(satellites)} 顆衛星")
        
        # 第一階段：收集所有衛星的位置數據，按時間戳分組
        raw_timeline = {}
        satellite_count = 0
        position_count = 0
        
        for satellite_id, satellite_data in satellites.items():
            # 跳過不可見的衛星
            if satellite_data.get('satellite_info', {}).get('status') == 'not_visible':
                continue
                
            satellite_count += 1
            positions = satellite_data.get('positions', [])
            
            for position in positions:
                timestamp = position['time']
                position_count += 1
                
                if timestamp not in raw_timeline:
                    raw_timeline[timestamp] = []
                
                # 添加衛星位置資訊
                satellite_position = {
                    'satellite_id': satellite_id,
                    'constellation': constellation_name,
                    'elevation_deg': position['elevation_deg'],
                    'azimuth_deg': position['azimuth_deg'],
                    'range_km': position['range_km'],
                    'time_offset_seconds': position['time_offset_seconds']
                }
                
                raw_timeline[timestamp].append(satellite_position)
        
        # 第二階段：實現時間窗口聚合機制
        # 設定時間窗口大小 (秒)
        time_window_seconds = 60  # 1分鐘窗口
        aggregated_timeline = {}
        
        # 將所有時間戳按順序排列
        sorted_timestamps = sorted(raw_timeline.keys())
        
        logger.info(f"📊 原始資料: {satellite_count} 顆可見衛星, {position_count} 個位置點, {len(sorted_timestamps)} 個時間戳")
        
        # 處理時間窗口聚合
        processed_timestamps = set()
        
        for base_timestamp in sorted_timestamps:
            if base_timestamp in processed_timestamps:
                continue
                
            # 解析基準時間
            from datetime import datetime
            try:
                base_time = datetime.fromisoformat(base_timestamp.replace('Z', '+00:00'))
            except:
                continue
            
            # 找出時間窗口內的所有衛星
            window_satellites = []
            window_timestamps = []
            
            for check_timestamp in sorted_timestamps:
                if check_timestamp in processed_timestamps:
                    continue
                    
                try:
                    check_time = datetime.fromisoformat(check_timestamp.replace('Z', '+00:00'))
                    time_diff = abs((check_time - base_time).total_seconds())
                    
                    # 如果在時間窗口內，加入聚合
                    if time_diff <= time_window_seconds:
                        window_satellites.extend(raw_timeline[check_timestamp])
                        window_timestamps.append(check_timestamp)
                        processed_timestamps.add(check_timestamp)
                        
                except Exception as e:
                    logger.warning(f"時間解析錯誤 {check_timestamp}: {e}")
                    continue
            
            # 如果窗口內有衛星，創建聚合時間點
            if window_satellites:
                # 使用窗口的代表時間戳（第一個）
                representative_timestamp = base_timestamp
                
                # 去重衛星（同一顆衛星可能在窗口內有多個位置）
                unique_satellites = {}
                for sat in window_satellites:
                    sat_id = sat['satellite_id']
                    if sat_id not in unique_satellites:
                        unique_satellites[sat_id] = sat
                    else:
                        # 如果有重複，選擇仰角較高的
                        if sat['elevation_deg'] > unique_satellites[sat_id]['elevation_deg']:
                            unique_satellites[sat_id] = sat
                
                aggregated_timeline[representative_timestamp] = list(unique_satellites.values())
        
        # 第三階段：品質檢查和統計
        total_aggregated_timestamps = len(aggregated_timeline)
        multi_satellite_timestamps = sum(1 for sats in aggregated_timeline.values() if len(sats) > 1)
        max_simultaneous_satellites = max(len(sats) for sats in aggregated_timeline.values()) if aggregated_timeline else 0
        
        logger.info(f"🎯 時間軸聚合完成:")
        logger.info(f"  - 聚合後時間點: {total_aggregated_timestamps}")
        logger.info(f"  - 多衛星時間點: {multi_satellite_timestamps} ({multi_satellite_timestamps/total_aggregated_timestamps*100:.1f}%)")
        logger.info(f"  - 最大同時可見: {max_simultaneous_satellites} 顆衛星")
        
        # 詳細檢查前幾個時間點
        if aggregated_timeline:
            sample_timestamps = list(aggregated_timeline.keys())[:5]
            for i, ts in enumerate(sample_timestamps, 1):
                satellites_at_time = aggregated_timeline[ts]
                elevation_list = [f'{s["elevation_deg"]:.1f}°' for s in satellites_at_time]
                logger.info(f"  樣本 {i}: {len(satellites_at_time)} 顆衛星 (仰角: {elevation_list})")
        
        return aggregated_timeline
    
    def _create_d2_event(self, timestamp: str, serving_satellite: Dict, neighbors: List[Dict], 
                    recommended_candidate: Dict = None) -> Optional[Dict]:
        """
        創建 D2 事件：基於 3GPP TS 38.331 地理距離標準
        
        Args:
            timestamp: 事件時間戳
            serving_satellite: 服務衛星資訊
            neighbors: 鄰近衛星列表
            recommended_candidate: 推薦的候選衛星
            
        Returns:
            Optional[Dict]: D2 事件資料，如果不符合條件則返回 None
        """
        # 計算與服務衛星的距離
        serving_distance = self._calculate_distance(self.default_ue_position, serving_satellite)
        
        # 計算到失去訊號的時間
        time_to_los = self._estimate_time_to_los(serving_satellite)
        
        # 選擇最佳換手目標 (優先使用推薦候選，否則選仰角最高)
        best_target = recommended_candidate
        if not best_target and neighbors:
            best_target = max(neighbors, key=lambda sat: sat['elevation_deg'])
        
        # 計算最佳目標的距離
        target_distance = None
        if best_target:
            target_distance = self._calculate_distance(self.default_ue_position, best_target)
        
        return {
            "timestamp": timestamp,
            "event_type": "D2",
            "detection_method": "3gpp_distance_based",
            "serving_satellite": {
                "id": serving_satellite['satellite_id'],
                "constellation": serving_satellite['constellation'],
                "elevation": round(serving_satellite['elevation_deg'], 2),
                "azimuth": round(serving_satellite['azimuth_deg'], 1),
                "range_km": round(serving_satellite['range_km'], 1),
                "distance_to_ue_km": round(serving_distance, 1)
            },
            "recommended_target": {
                "id": best_target['satellite_id'] if best_target else None,
                "elevation": round(best_target['elevation_deg'], 2) if best_target else None,
                "distance_to_ue_km": round(target_distance, 1) if target_distance else None,
                "handover_gain_km": round(serving_distance - target_distance, 1) if target_distance else None
            } if best_target else None,
            "time_to_los_seconds": time_to_los,
            "distance_threshold_km": 1500.0,
            "triggered_by_distance": True,
            "severity": "critical" if serving_distance > 1800 else "warning",
            "handover_urgency": self._calculate_distance_urgency(serving_distance),
            "3gpp_compliant": True
        }
    
    def _create_a4_event(self, timestamp: str, candidate_satellite: Dict, serving_satellite: Dict) -> Optional[Dict]:
        """
        創建 A4 事件：鄰近衛星測量值超過門檻 (多普勒增強)
        
        Args:
            timestamp: 事件時間戳
            candidate_satellite: 候選衛星資訊
            serving_satellite: 當前服務衛星資訊
            
        Returns:
            Optional[Dict]: A4 事件資料
        """
        # 🆕 多普勒增強 RSRP 計算
        timestamp_float = time.time()  # 轉換為浮點數時間戳
        
        candidate_rsrp = self._estimate_rsrp(
            candidate_satellite['elevation_deg'], 
            candidate_satellite, 
            timestamp_float,
            use_doppler_compensation=True
        )
        
        serving_rsrp = self._estimate_rsrp(
            serving_satellite['elevation_deg'],
            serving_satellite,
            timestamp_float,
            use_doppler_compensation=True
        )
        
        # 調整後的 RSRP 門檻（更寬鬆以考慮多普勒補償效果）
        adjusted_rsrp_threshold = -120  # dBm
        if candidate_rsrp <= adjusted_rsrp_threshold:
            return None
        
        # 計算品質優勢
        quality_advantage = candidate_rsrp - serving_rsrp
        
        return {
            "timestamp": timestamp,
            "event_type": "A4",
            "candidate_satellite": {
                "id": candidate_satellite['satellite_id'],
                "constellation": candidate_satellite['constellation'],
                "elevation": round(candidate_satellite['elevation_deg'], 2),
                "azimuth": round(candidate_satellite['azimuth_deg'], 1),
                "range_km": round(candidate_satellite['range_km'], 1),
                "estimated_rsrp_dbm": round(candidate_rsrp, 1),
                "doppler_enhanced": self.doppler_enabled
            },
            "serving_satellite": {
                "id": serving_satellite['satellite_id'],
                "elevation": round(serving_satellite['elevation_deg'], 2),
                "estimated_rsrp_dbm": round(serving_rsrp, 1)
            },
            "quality_advantage_db": round(quality_advantage, 1),
            "handover_opportunity": quality_advantage > 3.0  # 需要明顯優勢才推薦切換
        }
    
    def _create_a5_event(self, timestamp: str, serving_satellite: Dict, candidate_satellite: Dict) -> Optional[Dict]:
        """
        創建 A5 事件：服務變差且鄰近變好 (多普勒增強)
        
        Args:
            timestamp: 事件時間戳
            serving_satellite: 服務衛星資訊
            candidate_satellite: 候選衛星資訊
            
        Returns:
            Optional[Dict]: A5 事件資料
        """
        # 🆕 多普勒增強 RSRP 計算
        timestamp_float = time.time()
        
        serving_rsrp = self._estimate_rsrp(
            serving_satellite['elevation_deg'],
            serving_satellite,
            timestamp_float,
            use_doppler_compensation=True
        )
        
        candidate_rsrp = self._estimate_rsrp(
            candidate_satellite['elevation_deg'],
            candidate_satellite,
            timestamp_float,
            use_doppler_compensation=True
        )
        
        # 計算換手增益
        handover_gain = candidate_rsrp - serving_rsrp
        
        # 多普勒補償後的A5條件更嚴格，確保真正的信號品質優勢
        min_gain_threshold = 5.0 if self.doppler_enabled else 3.0  # 多普勒增強需更高門檻
        if handover_gain < min_gain_threshold:
            return None
        
        # 計算緊急程度
        urgency = self._calculate_a5_urgency(serving_satellite, handover_gain)
        
        return {
            "timestamp": timestamp,
            "event_type": "A5",
            "serving_satellite": {
                "id": serving_satellite['satellite_id'],
                "constellation": serving_satellite['constellation'],
                "elevation": round(serving_satellite['elevation_deg'], 2),
                "estimated_rsrp_dbm": round(serving_rsrp, 1),
                "doppler_enhanced": self.doppler_enabled
            },
            "candidate_satellite": {
                "id": candidate_satellite['satellite_id'],
                "constellation": candidate_satellite['constellation'],
                "elevation": round(candidate_satellite['elevation_deg'], 2),
                "estimated_rsrp_dbm": round(candidate_rsrp, 1),
                "doppler_enhanced": self.doppler_enabled
            },
            "handover_gain_db": round(handover_gain, 1),
            "urgency": urgency,
            "recommended_action": "execute_handover" if urgency == "critical" else "prepare_handover",
            "doppler_compensation_active": self.doppler_enabled
        }
    
    def _calculate_a5_urgency(self, serving_satellite: Dict, handover_gain: float) -> str:
        """
        計算 A5 事件的緊急程度
        """
        elevation = serving_satellite['elevation_deg']
        
        if elevation < 5.0 and handover_gain > 10.0:
            return "critical"
        elif elevation < 8.0 and handover_gain > 7.0:
            return "high"
        elif handover_gain > 5.0:
            return "normal"
        else:
            return "low"
    
    def _estimate_time_to_los(self, satellite: Dict) -> int:
        """
        估算衛星失去訊號的時間 (秒)
        
        Args:
            satellite: 衛星資訊
            
        Returns:
            int: 預估的失去訊號時間 (秒)
        """
        elevation = satellite['elevation_deg']
        
        # 簡化模型：基於仰角線性估算
        # LEO 衛星通常以 ~1°/分鐘的速度變化仰角
        degrees_to_critical = elevation - self.critical_threshold
        
        if degrees_to_critical <= 0:
            return 0
        
        # 估算：1° ≈ 60 秒 (簡化模型)
        return int(degrees_to_critical * 60)
    
    def _estimate_rsrp(self, elevation_deg: float, satellite_data: dict = None, 
                       timestamp: float = None, use_enhanced_calculation: bool = True,
                       use_doppler_compensation: bool = False) -> float:
        """
        根據仰角估算 RSRP (dBm)，支援多種計算方法
        
        Args:
            elevation_deg: 仰角 (度)
            satellite_data: 衛星數據字典 (可選)
            timestamp: 時間戳 (可選)
            use_enhanced_calculation: 是否使用增強計算 (鏈路預算+多普勒)
            use_doppler_compensation: 是否啟用多普勒補償 (向後兼容參數)
            
        Returns:
            float: 估算的 RSRP 值 (dBm)
        """
        # 向後兼容：如果指定了多普勒補償，啟用增強計算
        if use_doppler_compensation:
            use_enhanced_calculation = True
        
        # 如果不使用增強計算或缺少衛星數據，使用基礎計算
        if not use_enhanced_calculation or not satellite_data:
            return self._calculate_base_rsrp(elevation_deg)
        
        # 使用綜合 RSRP 計算
        try:
            # 確保衛星數據包含必要信息
            if 'elevation_deg' not in satellite_data:
                satellite_data['elevation_deg'] = elevation_deg
            
            comprehensive_result = self._calculate_comprehensive_rsrp(
                satellite_data, timestamp)
            
            return comprehensive_result['final_rsrp_dbm']
            
        except Exception as e:
            logger.warning(f"增強 RSRP 計算失敗，使用基礎方法: {e}")
            return self._calculate_base_rsrp(elevation_deg)
    
    def _calculate_base_rsrp(self, elevation_deg: float) -> float:
        """
        計算基礎 RSRP (無多普勒補償)
        """
        # 簡化的 RSRP 模型：仰角越高，信號越強
        # 基於自由空間路徑損耗模型
        base_rsrp = -100  # 基準 RSRP
        elevation_bonus = (elevation_deg - 10) * 0.5  # 每度增加 0.5dB
        
        # 加入環境因子
        environment_penalty = (self.environment_factor - 1.0) * 10
        
        return base_rsrp + elevation_bonus - environment_penalty
    
    def _calculate_doppler_enhanced_rsrp(self, base_rsrp: float, 
                                       satellite_data: dict, timestamp: float) -> float:
        """
        計算多普勒增強的 RSRP
        """
        try:
            # 準備衛星數據結構
            from .doppler_compensation_system import SatelliteData
            
            sat_data = SatelliteData(
                satellite_id=satellite_data.get('satellite_id', 'unknown'),
                position=(
                    satellite_data.get('lat', 25.0),
                    satellite_data.get('lon', 122.0),
                    satellite_data.get('altitude_km', 550)
                ),
                carrier_freq_hz=28e9,  # Ka 頻段
                rsrp_dbm=base_rsrp,
                elevation_deg=satellite_data.get('elevation_deg'),
                range_km=satellite_data.get('range_km')
            )
            
            # 執行多普勒校正 RSRP 計算
            result = self.doppler_system.calculate_doppler_corrected_rsrp(
                sat_data, self.default_ue_position, timestamp, base_rsrp)
            
            corrected_rsrp = result['corrected_rsrp_dbm']
            
            # 記錄多普勒補償效果
            if result['doppler_info']:
                doppler_info = result['doppler_info']
                logger.debug(f"多普勒補償效果: {base_rsrp:.1f} → {corrected_rsrp:.1f} dBm "
                           f"(補償: {doppler_info.total_offset_hz:.0f} Hz, "
                           f"精度: {doppler_info.compensation_accuracy:.2f})")
            
            return corrected_rsrp
            
        except Exception as e:
            logger.error(f"多普勒增強 RSRP 計算失敗: {e}")
            return base_rsrp

    def _calculate_comprehensive_rsrp(self, satellite_data: dict, 
                                     timestamp: float = None,
                                     weather_data=None,
                                     environment_type: str = 'standard') -> Dict[str, Any]:
        """
        綜合 RSRP 計算：整合動態鏈路預算 + 多普勒補償
        
        Args:
            satellite_data: 衛星數據
            timestamp: 時間戳
            weather_data: 天氣數據 (可選)
            environment_type: 環境類型
            
        Returns:
            Dict: 詳細的 RSRP 計算結果
        """
        timestamp = timestamp or time.time()
        
        try:
            # 方法1: 動態鏈路預算計算 (如果可用)
            if self.link_budget_enabled:
                # 準備鏈路預算計算所需數據
                link_budget_data = {
                    'range_km': satellite_data.get('range_km', 800.0),
                    'elevation_deg': satellite_data.get('elevation_deg', 45.0),
                    'frequency_ghz': 28.0,  # Ka 頻段
                    'satellite_id': satellite_data.get('satellite_id', 'unknown'),
                    'azimuth_deg': satellite_data.get('azimuth_deg', 0.0)
                }
                
                # 執行增強 RSRP 計算
                rsrp_result = self.link_budget_calculator.calculate_enhanced_rsrp(
                    link_budget_data, 
                    self.default_ue_position, 
                    timestamp,
                    weather_data,
                    environment_type
                )
                
                base_rsrp = rsrp_result['rsrp_dbm']
                calculation_method = 'link_budget_enhanced'
                
                logger.debug(f"鏈路預算 RSRP: {base_rsrp:.1f} dBm")
                
            else:
                # 備用方法: 基礎 RSRP 計算
                base_rsrp = self._calculate_base_rsrp(satellite_data.get('elevation_deg', 45.0))
                rsrp_result = {
                    'rsrp_dbm': base_rsrp,
                    'base_rsrp_dbm': base_rsrp,
                    'calculation_method': 'basic'
                }
                calculation_method = 'basic'
            
            # 方法2: 多普勒補償增強 (如果可用)
            if self.doppler_enabled:
                doppler_enhanced_rsrp = self._calculate_doppler_enhanced_rsrp(
                    base_rsrp, satellite_data, timestamp)
                
                # 計算多普勒改善
                doppler_improvement = doppler_enhanced_rsrp - base_rsrp
                final_rsrp = doppler_enhanced_rsrp
                calculation_method += '_doppler_enhanced'
                
                logger.debug(f"多普勒增強 RSRP: {base_rsrp:.1f} → {final_rsrp:.1f} dBm "
                           f"(改善: {doppler_improvement:.1f} dB)")
            else:
                final_rsrp = base_rsrp
                doppler_improvement = 0.0
            
            # 綜合結果
            comprehensive_result = {
                'final_rsrp_dbm': final_rsrp,
                'base_rsrp_dbm': base_rsrp,
                'doppler_improvement_db': doppler_improvement,
                'calculation_method': calculation_method,
                'timestamp': timestamp,
                'satellite_id': satellite_data.get('satellite_id', 'unknown'),
                'elevation_deg': satellite_data.get('elevation_deg', 45.0),
                'link_budget_details': rsrp_result if self.link_budget_enabled else None,
                'doppler_enabled': self.doppler_enabled,
                'link_budget_enabled': self.link_budget_enabled
            }
            
            logger.debug(f"綜合 RSRP: {final_rsrp:.1f} dBm (方法: {calculation_method})")
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"綜合 RSRP 計算失敗: {e}")
            # 備用計算
            fallback_rsrp = self._calculate_base_rsrp(satellite_data.get('elevation_deg', 45.0))
            return {
                'final_rsrp_dbm': fallback_rsrp,
                'base_rsrp_dbm': fallback_rsrp,
                'doppler_improvement_db': 0.0,
                'calculation_method': 'fallback',
                'timestamp': timestamp,
                'satellite_id': satellite_data.get('satellite_id', 'unknown'),
                'elevation_deg': satellite_data.get('elevation_deg', 45.0),
                'link_budget_details': None,
                'doppler_enabled': False,
                'link_budget_enabled': False
            }

    def optimize_smtc_configuration(self, 
                                  satellite_data: Dict[str, Dict],
                                  measurement_requirements: Optional[Dict[str, Any]] = None,
                                  power_budget: float = 5000.0) -> Dict[str, Any]:
        """
        優化 SMTC 測量配置
        
        Args:
            satellite_data: 衛星數據字典 {sat_id: sat_info}
            measurement_requirements: 測量需求配置
            power_budget: 功耗預算 (mW)
            
        Returns:
            Dict: SMTC 配置結果
        """
        try:
            if not self.smtc_enabled:
                logger.warning("SMTC 優化系統未啟用")
                return self._get_default_smtc_result()
            
            # 預設測量需求
            if measurement_requirements is None:
                measurement_requirements = {
                    'high_accuracy_mode': True,
                    'power_efficiency_mode': False,
                    'priority_satellites': list(satellite_data.keys())[:3]  # 前3顆衛星
                }
            
            # 獲取當前時間戳
            timestamp = time.time()
            
            # 執行 SMTC 配置優化
            smtc_config = self.smtc_optimizer.optimize_smtc_configuration(
                satellite_data,
                self.default_ue_position,
                measurement_requirements,
                power_budget,
                timestamp
            )
            
            # 生成配置建議
            configuration_advice = self._generate_smtc_advice(smtc_config)
            
            result = {
                'smtc_config': {
                    'config_id': smtc_config.config_id,
                    'periodicity_ms': smtc_config.periodicity_ms,
                    'offset_ms': smtc_config.offset_ms,
                    'duration_ms': smtc_config.duration_ms,
                    'total_power_consumption': smtc_config.total_power_consumption,
                    'efficiency_score': smtc_config.efficiency_score
                },
                'measurement_windows': [
                    {
                        'window_id': window.window_id,
                        'start_time': window.start_time,
                        'duration_ms': window.duration_ms,
                        'measurement_types': [mt.value for mt in window.measurement_types],
                        'target_satellites': window.target_satellites,
                        'priority': window.priority.value,
                        'power_budget': window.power_budget,
                        'expected_measurements': window.expected_measurements
                    }
                    for window in smtc_config.measurement_slots
                ],
                'adaptive_parameters': smtc_config.adaptive_parameters,
                'configuration_advice': configuration_advice,
                'optimization_timestamp': timestamp,
                'optimization_method': 'intelligent_smtc_optimizer'
            }
            
            logger.info(f"SMTC 配置優化完成: 週期={smtc_config.periodicity_ms}ms, "
                       f"窗口數={len(smtc_config.measurement_slots)}, "
                       f"效率={smtc_config.efficiency_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"SMTC 配置優化失敗: {e}")
            return self._get_default_smtc_result()
    
    def _generate_smtc_advice(self, smtc_config) -> List[str]:
        """生成 SMTC 配置建議"""
        advice = []
        
        # 基於效率評分的建議
        if smtc_config.efficiency_score > 0.8:
            advice.append("配置效率優秀，建議保持當前設定")
        elif smtc_config.efficiency_score > 0.6:
            advice.append("配置效率良好，可考慮微調測量類型")
        elif smtc_config.efficiency_score > 0.4:
            advice.append("配置效率中等，建議降低測量複雜度或增加功耗預算")
        else:
            advice.append("配置效率偏低，建議重新評估測量需求")
        
        # 基於功耗的建議
        if smtc_config.total_power_consumption > 3000:
            advice.append("功耗偏高，建議啟用功耗效率模式")
        elif smtc_config.total_power_consumption < 1000:
            advice.append("功耗富餘，可考慮增加測量精度")
        
        # 基於測量窗口數量的建議
        window_count = len(smtc_config.measurement_slots)
        if window_count > 5:
            advice.append("測量窗口較多，注意避免測量衝突")
        elif window_count < 2:
            advice.append("測量窗口較少，可能影響換手決策準確性")
        
        # 基於自適應參數的建議
        if smtc_config.adaptive_parameters:
            if 'recommended_updates' in smtc_config.adaptive_parameters:
                advice.extend(smtc_config.adaptive_parameters['recommended_updates'])
        
        return advice
    
    def _get_default_smtc_result(self) -> Dict[str, Any]:
        """獲取預設 SMTC 配置結果"""
        return {
            'smtc_config': {
                'config_id': f'default_{int(time.time())}',
                'periodicity_ms': 160,
                'offset_ms': 0,
                'duration_ms': 80,
                'total_power_consumption': 500.0,
                'efficiency_score': 0.5
            },
            'measurement_windows': [],
            'adaptive_parameters': {},
            'configuration_advice': ['使用預設配置，建議啟用 SMTC 優化系統'],
            'optimization_timestamp': time.time(),
            'optimization_method': 'default_fallback'
        }
    
    def _calculate_handover_urgency(self, elevation_deg: float) -> str:
        """
        計算換手緊急程度
        
        Args:
            elevation_deg: 當前仰角
            
        Returns:
            str: 緊急程度 (low/medium/high/critical)
        """
        if elevation_deg <= self.critical_threshold:
            return "critical"
        elif elevation_deg <= self.critical_threshold + 1:
            return "high"
        elif elevation_deg <= self.critical_threshold + 2:
            return "medium"
        else:
            return "low"


class RuleBasedHandoverEngine:
    """
    規則式換手決策引擎
    
    整合 D2/A4/A5 事件檢測與 LayeredElevationEngine，
    提供統一的規則式換手決策介面
    """
    
    def __init__(self, scene_id: str = "ntpu"):
        """
        初始化規則式換手引擎
        
        Args:
            scene_id: 場景ID，用於載入對應的門檻參數
        """
        self.scene_id = scene_id
        self.current_serving = None
        self.event_queue = []
        self.handover_in_progress = False
        self.handover_history = []
        
        # 初始化子系統
        self.event_detector = HandoverEventDetector(scene_id)
        
        # 載入分層門檻引擎和座標軌道引擎
        try:
            from .layered_elevation_threshold import create_layered_engine
            from .unified_elevation_config import get_elevation_config
            from .coordinate_specific_orbit_engine import (
                CoordinateSpecificOrbitEngine, 
                get_observer_coordinates
            )
            
            # 獲取標準化門檻配置
            elevation_config = get_elevation_config(
                use_case="satellite_handover", 
                environment="urban"
            )
            
            self.elevation_engine = create_layered_engine(environment="urban")
            
            # 初始化座標軌道引擎
            self.orbit_engine = CoordinateSpecificOrbitEngine()
            observer_coords = get_observer_coordinates(scene_id)
            self.observer_location = observer_coords
            
            logger.info(f"✅ 整合引擎初始化成功 - 觀測點: {observer_coords}")
            
        except ImportError as e:
            logger.warning(f"LayeredElevationEngine 或相關組件不可用: {e}")
            self.elevation_engine = None
            self.orbit_engine = None
            self.observer_location = None
        
        # 決策參數
        self.handover_cooldown = 30.0  # 換手冷卻時間（秒）
        self.min_signal_improvement = 3.0  # 最小信號改善（dB）
        self.emergency_threshold = 5.0  # 緊急換手門檻（度）
        
        logger.info(f"RuleBasedHandoverEngine 初始化完成 - 場景: {scene_id}")
    
    def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        處理換手事件並生成決策
        
        Args:
            event: 換手事件資料
            
        Returns:
            Optional[Dict]: 換手決策，如果不需要動作則返回 None
        """
        event_type = event.get('type', '').upper()
        
        if event_type == 'D2':
            return self._process_d2_event(event)
        elif event_type == 'A4':
            return self._process_a4_event(event)
        elif event_type == 'A5':
            return self._process_a5_event(event)
        else:
            logger.warning(f"未知事件類型: {event_type}")
            return None
    
    def _process_d2_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """處理 D2 事件：服務衛星即將不可見"""
        serving_info = event.get('serving_satellite', {})
        recommended_target = event.get('recommended_target', {})
        time_to_los = event.get('time_to_los_seconds', 0)
        
        # D2 事件優先級最高，立即執行換手
        if time_to_los < 30 and recommended_target:
            self.handover_in_progress = True
            
            decision = {
                'action': 'EXECUTE_HANDOVER',
                'decision_type': 'd2_emergency',
                'source_satellite': serving_info.get('id'),
                'target_satellite': recommended_target.get('id'),
                'urgency': 'critical',
                'expected_interruption_ms': 50,
                'reason': f'服務衛星 {serving_info.get("id")} 將在 {time_to_los}s 內失去訊號',
                'confidence': 0.95,
                'timestamp': datetime.now().isoformat()
            }
            
            self._record_handover_decision(decision)
            return decision
            
        return None
    
    def _process_a4_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """處理 A4 事件：鄰近衛星測量值超過門檻"""
        if self.handover_in_progress:
            return None
            
        candidate_info = event.get('candidate_satellite', {})
        serving_info = event.get('serving_satellite', {})
        quality_advantage = event.get('quality_advantage_db', 0)
        
        # 檢查信號改善是否足夠
        if quality_advantage >= self.min_signal_improvement:
            # 檢查冷卻時間
            if self._is_handover_allowed(candidate_info.get('id')):
                decision = {
                    'action': 'EXECUTE_HANDOVER',
                    'decision_type': 'a4_opportunity',
                    'source_satellite': serving_info.get('id'),
                    'target_satellite': candidate_info.get('id'),
                    'urgency': 'medium',
                    'expected_interruption_ms': 80,
                    'reason': f'鄰近衛星 {candidate_info.get("id")} 信號品質優於服務衛星 {quality_advantage:.1f}dB',
                    'confidence': 0.8,
                    'timestamp': datetime.now().isoformat()
                }
                
                self._record_handover_decision(decision)
                return decision
        
        return None
    
    def _process_a5_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """處理 A5 事件：服務變差且鄰近變好"""
        serving_info = event.get('serving_satellite', {})
        candidate_info = event.get('candidate_satellite', {})
        handover_gain = event.get('handover_gain_db', 0)
        urgency = event.get('urgency', 'normal')
        
        # 根據緊急程度決定是否執行換手
        if urgency == 'high' or handover_gain >= self.min_signal_improvement:
            if self._is_handover_allowed(candidate_info.get('id')):
                decision = {
                    'action': 'EXECUTE_HANDOVER',
                    'decision_type': 'a5_quality_driven',
                    'source_satellite': serving_info.get('id'),
                    'target_satellite': candidate_info.get('id'),
                    'urgency': urgency,
                    'expected_interruption_ms': 100,
                    'reason': f'服務品質下降，換手至 {candidate_info.get("id")} 可獲得 {handover_gain:.1f}dB 改善',
                    'confidence': 0.7,
                    'timestamp': datetime.now().isoformat()
                }
                
                self._record_handover_decision(decision)
                return decision
        
        return None
    
    def _is_handover_allowed(self, target_satellite_id: str) -> bool:
        """檢查是否允許換手到指定衛星"""
        if not self.handover_history:
            return True
            
        # 檢查最近是否有換手到同一衛星
        recent_handovers = [
            h for h in self.handover_history[-10:]
            if h.get('target_satellite') == target_satellite_id
        ]
        
        if recent_handovers:
            last_handover_time = datetime.fromisoformat(recent_handovers[-1]['timestamp'])
            time_since_last = (datetime.now() - last_handover_time).total_seconds()
            
            if time_since_last < self.handover_cooldown:
                logger.info(f"換手冷卻中，距離上次換手至 {target_satellite_id} 僅 {time_since_last:.1f}s")
                return False
        
        return True
    
    def _record_handover_decision(self, decision: Dict[str, Any]) -> None:
        """記錄換手決策"""
        self.handover_history.append(decision)
        
        # 保持歷史記錄在合理範圍內
        if len(self.handover_history) > 100:
            self.handover_history = self.handover_history[-100:]
        
        # 更新當前服務衛星
        if decision['action'] == 'EXECUTE_HANDOVER':
            self.current_serving = decision['target_satellite']
            logger.info(f"執行換手決策: {decision['source_satellite']} -> {decision['target_satellite']}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """獲取當前換手引擎狀態"""
        return {
            'scene_id': self.scene_id,
            'current_serving_satellite': self.current_serving,
            'handover_in_progress': self.handover_in_progress,
            'pending_events': len(self.event_queue),
            'recent_handovers': len([
                h for h in self.handover_history
                if (datetime.now() - datetime.fromisoformat(h['timestamp'])).total_seconds() < 300
            ]),
            'total_handovers': len(self.handover_history),
            'engine_health': 'operational'
        }
    
    def reset_handover_progress(self) -> None:
        """重置換手進行狀態（由外部系統在換手完成後調用）"""
        self.handover_in_progress = False
        logger.info("換手進行狀態已重置")
    
    def analyze_satellite_visibility(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析衛星可見性狀態，整合分層門檻引擎和座標軌道引擎
        
        Args:
            satellite_data: 衛星位置和狀態數據
            
        Returns:
            Dict: 完整的可見性分析結果
        """
        satellite_id = satellite_data.get('satellite_id', 'unknown')
        
        if self.elevation_engine and self.orbit_engine:
            # 使用完整的整合引擎分析
            try:
                # 1. 分層門檻分析
                phase_analysis = self.elevation_engine.analyze_satellite_phase(satellite_data)
                
                # 2. 座標軌道引擎增強分析
                enhanced_analysis = self._enhance_with_orbit_engine(
                    satellite_data, phase_analysis
                )
                
                # 3. 整合 ITU-R P.618 標準合規性
                compliance_analysis = self._assess_itu_compliance(
                    satellite_data.get('elevation', 0.0)
                )
                
                # 4. 合併所有分析結果
                return {
                    **phase_analysis,
                    **enhanced_analysis,
                    **compliance_analysis,
                    'analysis_method': 'integrated_engine',
                    'observer_location': self.observer_location
                }
                
            except Exception as e:
                logger.warning(f"整合引擎分析失敗，回退到簡化分析: {e}")
                return self._simplified_visibility_analysis(satellite_data)
        else:
            # 簡化分析
            return self._simplified_visibility_analysis(satellite_data)
    
    def _enhance_with_orbit_engine(self, satellite_data: Dict[str, Any], 
                                  base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """使用座標軌道引擎增強分析"""
        enhancements = {}
        
        try:
            elevation = satellite_data.get('elevation', 0.0)
            azimuth = satellite_data.get('azimuth', 0.0)
            range_km = satellite_data.get('range_km', 0.0)
            
            # 計算更精確的軌道預測
            if self.orbit_engine and hasattr(self.orbit_engine, 'predict_visibility_window'):
                visibility_prediction = self.orbit_engine.predict_visibility_window(
                    satellite_data, self.observer_location
                )
                enhancements['visibility_prediction'] = visibility_prediction
            
            # 計算都卜勒頻移預估
            doppler_shift = self._estimate_doppler_shift(satellite_data)
            if doppler_shift is not None:
                enhancements['doppler_shift_hz'] = doppler_shift
            
            # 路徑損耗計算
            path_loss = self._calculate_path_loss(elevation, range_km)
            enhancements['path_loss_db'] = path_loss
            
            # 大氣衰減風險（結合環境因子）
            atmospheric_risk = self._assess_atmospheric_conditions(elevation)
            enhancements['atmospheric_conditions'] = atmospheric_risk
            
        except Exception as e:
            logger.debug(f"軌道引擎增強分析失敗: {e}")
        
        return enhancements
    
    def _assess_itu_compliance(self, elevation: float) -> Dict[str, Any]:
        """評估 ITU-R P.618 標準合規性"""
        return {
            'itu_compliance': {
                'meets_10_degree_standard': elevation >= 10.0,
                'elevation_margin_deg': max(0, elevation - 10.0),
                'compliance_level': self._get_compliance_level(elevation),
                'standard_reference': 'ITU-R P.618'
            }
        }
    
    def _get_compliance_level(self, elevation: float) -> str:
        """獲取合規等級"""
        if elevation >= 15.0:
            return 'excellent'
        elif elevation >= 10.0:
            return 'compliant'
        elif elevation >= 5.0:
            return 'marginal'
        else:
            return 'non_compliant'
    
    def _simplified_visibility_analysis(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """簡化的可見性分析"""
        elevation = satellite_data.get('elevation', 0.0)
        satellite_id = satellite_data.get('satellite_id', 'unknown')
        
        if elevation >= 15.0:
            phase = "monitoring"
            urgency = "low"
        elif elevation >= 10.0:
            phase = "pre_handover"
            urgency = "medium"
        elif elevation >= 5.0:
            phase = "execution"
            urgency = "high"
        else:
            phase = "critical"
            urgency = "critical"
        
        return {
            'satellite_id': satellite_id,
            'current_elevation': elevation,
            'handover_phase': phase,
            'urgency_level': urgency,
            'action_required': f'{phase}_recommended',
            'analysis_method': 'simplified',
            'itu_compliance': {
                'meets_10_degree_standard': elevation >= 10.0,
                'compliance_level': self._get_compliance_level(elevation)
            }
        }
    
    def _estimate_doppler_shift(self, satellite_data: Dict[str, Any]) -> Optional[float]:
        """估算都卜勒頻移 (Hz)"""
        try:
            # 簡化的都卜勒頻移計算
            # 實際實現需要衛星速度向量和觀測者相對位置
            elevation = satellite_data.get('elevation', 0.0)
            range_rate = satellite_data.get('range_rate_km_s', None)
            
            if range_rate is not None:
                # L頻段載波頻率約 1.5 GHz
                carrier_freq_hz = 1.5e9
                c = 299792458  # 光速 m/s
                
                doppler_hz = -(range_rate * 1000 * carrier_freq_hz) / c
                return doppler_hz
            
            return None
            
        except Exception:
            return None
    
    def _calculate_path_loss(self, elevation: float, range_km: float) -> float:
        """計算自由空間路徑損耗 (dB)"""
        try:
            if range_km <= 0:
                return 0.0
            
            # 自由空間路徑損耗公式
            # L = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
            # 假設 L頻段 1.5 GHz
            freq_mhz = 1500
            
            path_loss_db = (
                20 * math.log10(range_km * 1000) + 
                20 * math.log10(freq_mhz) - 
                147.55  # 常數項
            )
            
            return max(0.0, path_loss_db)
            
        except Exception:
            return 0.0
    
    def _assess_atmospheric_conditions(self, elevation: float) -> Dict[str, Any]:
        """評估大氣條件影響"""
        # 基於仰角的大氣衰減風險評估
        if elevation >= 30:
            risk_level = "minimal"
            attenuation_factor = 1.0
        elif elevation >= 15:
            risk_level = "low"
            attenuation_factor = 1.1
        elif elevation >= 10:
            risk_level = "moderate"
            attenuation_factor = 1.2
        elif elevation >= 5:
            risk_level = "high"
            attenuation_factor = 1.4
        else:
            risk_level = "severe"
            attenuation_factor = 2.0
        
        return {
            'risk_level': risk_level,
            'attenuation_factor': attenuation_factor,
            'scintillation_risk': 'high' if elevation < 10 else 'low',
            'multipath_risk': 'high' if elevation < 15 else 'moderate'
        }


class HandoverDataAccess:
    """
    換手數據存取層
    
    整合 Phase 0 預計算軌道數據，提供高性能的衛星可見性查詢
    """
    
    def __init__(self, data_dir: str = "/app/data"):
        """
        初始化數據存取層
        
        Args:
            data_dir: 數據目錄路徑
        """
        self.data_dir = Path(data_dir)
        self.orbit_data = None
        self.event_data = None
        self.visibility_cache = {}
        self.cache_ttl = 300  # 5分鐘緩存過期
        
        # 載入預計算數據
        self._load_precomputed_data()
        
        logger.info(f"HandoverDataAccess 初始化完成 - 數據目錄: {data_dir}")
    
    def _load_precomputed_data(self) -> None:
        """載入預計算數據"""
        try:
            # 載入軌道數據
            orbit_file = self.data_dir / "phase0_precomputed_orbits.json"
            if orbit_file.exists():
                with open(orbit_file, 'r', encoding='utf-8') as f:
                    self.orbit_data = json.load(f)
                logger.info(f"✅ 軌道數據載入成功: {len(self.orbit_data.get('constellations', {}))} 個星座")
            else:
                logger.warning(f"⚠️ 軌道數據檔案不存在: {orbit_file}")
                self.orbit_data = {"constellations": {}}
            
            # 載入事件數據（如果存在）
            event_file = self.data_dir / "events" / "ntpu_handover_events.json"
            if event_file.exists():
                with open(event_file, 'r', encoding='utf-8') as f:
                    self.event_data = json.load(f)
                logger.info("✅ 換手事件數據載入成功")
            else:
                logger.info("ℹ️ 換手事件數據不存在，將即時生成")
                self.event_data = None
                
        except Exception as e:
            logger.error(f"❌ 預計算數據載入失敗: {e}")
            self.orbit_data = {"constellations": {}}
            self.event_data = None
    
    def get_visible_satellites(self, timestamp: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        獲取特定時刻的可見衛星
        
        Args:
            timestamp: ISO 格式時間戳
            use_cache: 是否使用緩存
            
        Returns:
            List[Dict]: 可見衛星列表，按仰角降序排列
        """
        cache_key = f"visible_{timestamp}"
        
        # 檢查緩存
        if use_cache and cache_key in self.visibility_cache:
            cache_entry = self.visibility_cache[cache_key]
            if (datetime.now() - cache_entry['timestamp']).total_seconds() < self.cache_ttl:
                return cache_entry['data']
        
        visible_satellites = []
        
        if not self.orbit_data:
            return visible_satellites
        
        try:
            target_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            for constellation_name, constellation_data in self.orbit_data.get("constellations", {}).items():
                orbit_data = constellation_data.get("orbit_data", {})
                satellites = orbit_data.get("satellites", {})
                
                for satellite_id, satellite_data in satellites.items():
                    # 檢查衛星狀態
                    sat_info = satellite_data.get('satellite_info', {})
                    if sat_info.get('status') == 'not_visible':
                        continue
                    
                    # 查找最接近的時間點
                    position = self._find_position_at_time(
                        satellite_data.get('positions', []), 
                        target_time
                    )
                    
                    if position and position.get('elevation_deg', 0) > 0:
                        visible_satellites.append({
                            'satellite_id': satellite_id,
                            'constellation': constellation_name,
                            'name': sat_info.get('name', satellite_id),
                            'elevation_deg': position['elevation_deg'],
                            'azimuth_deg': position['azimuth_deg'],
                            'range_km': position.get('range_km', 0),
                            'time_offset_seconds': position.get('time_offset_seconds', 0),
                            'is_visible': True
                        })
            
            # 按仰角降序排列
            visible_satellites.sort(key=lambda x: x['elevation_deg'], reverse=True)
            
            # 緩存結果
            if use_cache:
                self.visibility_cache[cache_key] = {
                    'data': visible_satellites,
                    'timestamp': datetime.now()
                }
                
                # 清理過期緩存
                self._cleanup_cache()
            
            return visible_satellites
            
        except Exception as e:
            logger.error(f"❌ 獲取可見衛星失敗: {e}")
            return []
    
    def _find_position_at_time(self, positions: List[Dict], target_time: datetime) -> Optional[Dict]:
        """
        在位置列表中查找最接近目標時間的位置
        
        Args:
            positions: 位置數據列表
            target_time: 目標時間
            
        Returns:
            Optional[Dict]: 最接近的位置數據
        """
        if not positions:
            return None
        
        best_position = None
        min_time_diff = float('inf')
        
        for position in positions:
            try:
                pos_time = datetime.fromisoformat(position['time'].replace('Z', '+00:00'))
                time_diff = abs((target_time - pos_time).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_position = position
                    
            except (KeyError, ValueError) as e:
                continue
        
        return best_position
    
    def get_constellation_status(self) -> Dict[str, Any]:
        """獲取星座狀態統計"""
        if not self.orbit_data:
            return {"total_constellations": 0, "total_satellites": 0}
        
        stats = {
            "total_constellations": 0,
            "total_satellites": 0,
            "constellations": {}
        }
        
        for constellation_name, constellation_data in self.orbit_data.get("constellations", {}).items():
            orbit_data = constellation_data.get("orbit_data", {})
            satellites = orbit_data.get("satellites", {})
            
            visible_count = sum(
                1 for sat_data in satellites.values()
                if sat_data.get('satellite_info', {}).get('status') != 'not_visible'
            )
            
            stats["constellations"][constellation_name] = {
                "total_satellites": len(satellites),
                "visible_satellites": visible_count,
                "coverage_percentage": (visible_count / len(satellites) * 100) if satellites else 0
            }
            
            stats["total_satellites"] += len(satellites)
        
        stats["total_constellations"] = len(stats["constellations"])
        return stats
    
    def get_handover_events(self, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        """
        獲取換手事件數據
        
        Args:
            start_time: 開始時間（ISO格式）
            end_time: 結束時間（ISO格式）
            
        Returns:
            Dict: 換手事件數據
        """
        if self.event_data:
            events = self.event_data.get("events", {})
            
            # 如果指定了時間範圍，需要過濾事件
            if start_time or end_time:
                filtered_events = self._filter_events_by_time(events, start_time, end_time)
                return {
                    "metadata": self.event_data.get("metadata", {}),
                    "events": filtered_events,
                    "statistics": self._calculate_event_statistics(filtered_events)
                }
            
            return self.event_data
        else:
            # 即時生成事件（如果需要）
            logger.info("即時生成換手事件數據...")
            return self._generate_events_from_orbits(start_time, end_time)
    
    def _filter_events_by_time(self, events: Dict, start_time: str = None, end_time: str = None) -> Dict:
        """根據時間範圍過濾事件"""
        filtered = {"d2_events": [], "a4_events": [], "a5_events": []}
        
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if start_time else None
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else None
            
            for event_type, event_list in events.items():
                for event in event_list:
                    event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    
                    if start_dt and event_time < start_dt:
                        continue
                    if end_dt and event_time > end_dt:
                        continue
                    
                    filtered[event_type].append(event)
            
        except Exception as e:
            logger.error(f"事件時間過濾失敗: {e}")
            return events
        
        return filtered
    
    def _calculate_event_statistics(self, events: Dict) -> Dict:
        """計算事件統計"""
        return {
            "total_d2_events": len(events.get("d2_events", [])),
            "total_a4_events": len(events.get("a4_events", [])),
            "total_a5_events": len(events.get("a5_events", [])),
            "total_events": sum(len(event_list) for event_list in events.values())
        }
    
    def _generate_events_from_orbits(self, start_time: str = None, end_time: str = None) -> Dict:
        """從軌道數據即時生成事件"""
        logger.info("即時事件生成功能尚未實現，返回空事件集")
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "method": "real_time_generation",
                "time_range": {"start": start_time, "end": end_time}
            },
            "events": {"d2_events": [], "a4_events": [], "a5_events": []},
            "statistics": {"total_d2_events": 0, "total_a4_events": 0, "total_a5_events": 0}
        }
    
    def _cleanup_cache(self) -> None:
        """清理過期緩存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self.visibility_cache.items()
            if (current_time - entry['timestamp']).total_seconds() > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.visibility_cache[key]
        
        if expired_keys:
            logger.debug(f"清理 {len(expired_keys)} 個過期緩存項")
    
    def get_data_health(self) -> Dict[str, Any]:
        """獲取數據健康狀態"""
        return {
            "orbit_data_available": self.orbit_data is not None,
            "event_data_available": self.event_data is not None,
            "cache_entries": len(self.visibility_cache),
            "data_directory": str(self.data_dir),
            "last_update": datetime.now().isoformat()
        }

class HandoverMetrics:
    """
    換手性能監控系統
    
    記錄和分析換手決策的 KPI，支援即時監控和歷史分析
    """
    
    def __init__(self):
        """初始化監控系統"""
        self.metrics = {
            'total_handovers': 0,
            'successful_handovers': 0,
            'failed_handovers': 0,
            'avg_interruption_time_ms': 0.0,
            'service_availability_percent': 100.0,
            'decision_latency_ms': 0.0
        }
        
        # 詳細統計
        self.handover_by_type = {
            'd2_emergency': {'count': 0, 'success_rate': 0.0, 'avg_interruption': 0.0},
            'a4_opportunity': {'count': 0, 'success_rate': 0.0, 'avg_interruption': 0.0},
            'a5_quality_driven': {'count': 0, 'success_rate': 0.0, 'avg_interruption': 0.0}
        }
        
        # 歷史記錄
        self.handover_history = []
        self.decision_times = []
        self.interruption_times = []
        
        # 時間窗口統計
        self.hourly_stats = {}
        
        logger.info("HandoverMetrics 監控系統初始化完成")
    
    def record_handover_decision(self, decision: Dict[str, Any], decision_time_ms: float = 0.0) -> None:
        """
        記錄換手決策
        
        Args:
            decision: 換手決策數據
            decision_time_ms: 決策耗時（毫秒）
        """
        decision_type = decision.get('decision_type', 'unknown')
        timestamp = decision.get('timestamp', datetime.now().isoformat())
        
        # 記錄決策時間
        if decision_time_ms > 0:
            self.decision_times.append(decision_time_ms)
            self._update_decision_latency()
        
        # 更新類型統計
        if decision_type in self.handover_by_type:
            self.handover_by_type[decision_type]['count'] += 1
        
        # 記錄到歷史
        self.handover_history.append({
            'timestamp': timestamp,
            'decision': decision,
            'decision_time_ms': decision_time_ms,
            'status': 'initiated'
        })
        
        # 更新時間統計
        self._update_hourly_stats(timestamp, 'decision')
        
        logger.debug(f"記錄換手決策: {decision_type} - 耗時 {decision_time_ms:.2f}ms")
    
    def record_handover_result(self, decision_id: str, result: Dict[str, Any]) -> None:
        """
        記錄換手執行結果
        
        Args:
            decision_id: 決策ID（通常是時間戳）
            result: 執行結果
        """
        success = result.get('success', False)
        interruption_ms = result.get('interruption_ms', 0)
        error_reason = result.get('error_reason', '')
        
        # 更新總體指標
        self.metrics['total_handovers'] += 1
        
        if success:
            self.metrics['successful_handovers'] += 1
            self.interruption_times.append(interruption_ms)
            self._update_avg_interruption()
        else:
            self.metrics['failed_handovers'] += 1
        
        # 更新服務可用性
        self._update_service_availability()
        
        # 查找對應的決策記錄並更新
        for record in reversed(self.handover_history):
            if record['timestamp'] == decision_id:
                record['status'] = 'completed'
                record['result'] = result
                decision_type = record['decision'].get('decision_type', 'unknown')
                
                # 更新類型統計
                if decision_type in self.handover_by_type:
                    type_stats = self.handover_by_type[decision_type]
                    old_count = type_stats['count']
                    old_success = int(type_stats['success_rate'] * old_count / 100) if old_count > 0 else 0
                    
                    if success:
                        old_success += 1
                    
                    type_stats['success_rate'] = (old_success / old_count * 100) if old_count > 0 else 0
                    
                    if success and interruption_ms > 0:
                        old_avg = type_stats['avg_interruption']
                        old_total = old_avg * (old_success - 1) if old_success > 1 else 0
                        type_stats['avg_interruption'] = (old_total + interruption_ms) / old_success
                
                break
        
        # 更新時間統計
        self._update_hourly_stats(decision_id, 'result', success)
        
        logger.info(f"記錄換手結果: {'成功' if success else '失敗'} - 中斷時間 {interruption_ms}ms")
    
    def _update_avg_interruption(self) -> None:
        """更新平均中斷時間"""
        if self.interruption_times:
            self.metrics['avg_interruption_time_ms'] = sum(self.interruption_times) / len(self.interruption_times)
    
    def _update_decision_latency(self) -> None:
        """更新決策延遲"""
        if self.decision_times:
            # 保持最近1000個決策時間
            if len(self.decision_times) > 1000:
                self.decision_times = self.decision_times[-1000:]
            
            self.metrics['decision_latency_ms'] = sum(self.decision_times) / len(self.decision_times)
    
    def _update_service_availability(self) -> None:
        """更新服務可用性"""
        if self.metrics['total_handovers'] > 0:
            success_rate = self.metrics['successful_handovers'] / self.metrics['total_handovers']
            # 基於成功率估算服務可用性
            self.metrics['service_availability_percent'] = min(99.999, success_rate * 100)
    
    def _update_hourly_stats(self, timestamp: str, event_type: str, success: bool = None) -> None:
        """更新時間統計"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            
            if hour_key not in self.hourly_stats:
                self.hourly_stats[hour_key] = {
                    'decisions': 0,
                    'completions': 0,
                    'successes': 0,
                    'failures': 0
                }
            
            stats = self.hourly_stats[hour_key]
            
            if event_type == 'decision':
                stats['decisions'] += 1
            elif event_type == 'result':
                stats['completions'] += 1
                if success:
                    stats['successes'] += 1
                else:
                    stats['failures'] += 1
            
        except Exception as e:
            logger.warning(f"時間統計更新失敗: {e}")
    
    def get_kpis(self) -> Dict[str, Any]:
        """獲取關鍵績效指標"""
        success_rate = 0.0
        if self.metrics['total_handovers'] > 0:
            success_rate = self.metrics['successful_handovers'] / self.metrics['total_handovers'] * 100
        
        return {
            # 主要 KPI
            'handover_success_rate_percent': round(success_rate, 2),
            'avg_interruption_time_ms': round(self.metrics['avg_interruption_time_ms'], 2),
            'service_availability_percent': round(self.metrics['service_availability_percent'], 3),
            'avg_decision_latency_ms': round(self.metrics['decision_latency_ms'], 2),
            
            # 統計摘要
            'total_handovers_24h': self.metrics['total_handovers'],
            'successful_handovers': self.metrics['successful_handovers'],
            'failed_handovers': self.metrics['failed_handovers'],
            
            # 按類型統計
            'handover_by_type': self.handover_by_type.copy(),
            
            # 性能指標
            'performance_grade': self._calculate_performance_grade(),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_detailed_statistics(self) -> Dict[str, Any]:
        """獲取詳細統計數據"""
        recent_decisions = [
            record for record in self.handover_history[-100:]
            if (datetime.now() - datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))).total_seconds() < 3600
        ]
        
        return {
            'kpis': self.get_kpis(),
            'recent_activity': {
                'last_hour_decisions': len(recent_decisions),
                'recent_decision_types': self._analyze_recent_decision_types(recent_decisions),
                'decision_frequency': len(recent_decisions) / 60.0 if recent_decisions else 0.0  # 每分鐘決策數
            },
            'historical_trends': {
                'hourly_stats': dict(list(self.hourly_stats.items())[-24:]),  # 最近24小時
                'decision_latency_trend': self.decision_times[-100:] if len(self.decision_times) >= 100 else self.decision_times,
                'interruption_trend': self.interruption_times[-100:] if len(self.interruption_times) >= 100 else self.interruption_times
            },
            'system_health': {
                'total_records': len(self.handover_history),
                'memory_usage_mb': self._estimate_memory_usage(),
                'oldest_record': self.handover_history[0]['timestamp'] if self.handover_history else None
            }
        }
    
    def _calculate_performance_grade(self) -> str:
        """計算性能等級"""
        success_rate = 0.0
        if self.metrics['total_handovers'] > 0:
            success_rate = self.metrics['successful_handovers'] / self.metrics['total_handovers'] * 100
        
        avg_latency = self.metrics['decision_latency_ms']
        avg_interruption = self.metrics['avg_interruption_time_ms']
        
        # 評分標準
        if success_rate >= 99 and avg_latency <= 10 and avg_interruption <= 50:
            return 'A+'
        elif success_rate >= 95 and avg_latency <= 20 and avg_interruption <= 100:
            return 'A'
        elif success_rate >= 90 and avg_latency <= 50 and avg_interruption <= 200:
            return 'B'
        elif success_rate >= 80:
            return 'C'
        else:
            return 'D'
    
    def _analyze_recent_decision_types(self, recent_decisions: List[Dict]) -> Dict[str, int]:
        """分析最近決策類型分布"""
        type_counts = {}
        for record in recent_decisions:
            decision_type = record['decision'].get('decision_type', 'unknown')
            type_counts[decision_type] = type_counts.get(decision_type, 0) + 1
        
        return type_counts
    
    def _estimate_memory_usage(self) -> float:
        """估算內存使用量（MB）"""
        import sys
        
        total_size = 0
        total_size += sys.getsizeof(self.handover_history)
        total_size += sys.getsizeof(self.decision_times)
        total_size += sys.getsizeof(self.interruption_times)
        total_size += sys.getsizeof(self.hourly_stats)
        
        return total_size / (1024 * 1024)  # 轉換為 MB
    
    def cleanup_old_records(self, max_records: int = 10000) -> int:
        """
        清理舊記錄
        
        Args:
            max_records: 保留的最大記錄數
            
        Returns:
            int: 清理的記錄數
        """
        cleaned_count = 0
        
        # 清理換手歷史
        if len(self.handover_history) > max_records:
            old_count = len(self.handover_history)
            self.handover_history = self.handover_history[-max_records:]
            cleaned_count += old_count - len(self.handover_history)
        
        # 清理決策時間記錄
        if len(self.decision_times) > max_records:
            old_count = len(self.decision_times)
            self.decision_times = self.decision_times[-max_records:]
            cleaned_count += old_count - len(self.decision_times)
        
        # 清理中斷時間記錄
        if len(self.interruption_times) > max_records:
            old_count = len(self.interruption_times)
            self.interruption_times = self.interruption_times[-max_records:]
            cleaned_count += old_count - len(self.interruption_times)
        
        # 清理過舊的時間統計（保留最近7天）
        current_time = datetime.now()
        old_hour_keys = [
            key for key in self.hourly_stats.keys()
            if (current_time - datetime.strptime(key, '%Y-%m-%d %H:%S')).days > 7
        ]
        
        for key in old_hour_keys:
            del self.hourly_stats[key]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"清理 {cleaned_count} 個舊記錄")
        
        return cleaned_count
    
    def reset_metrics(self) -> None:
        """重置所有指標（謹慎使用）"""
        self.__init__()
        logger.warning("HandoverMetrics 已重置所有指標")

class HandoverDecisionInterface:
    """
    統一換手決策介面
    
    支援規則式和 RL 決策方法的統一介面，為未來 RL 整合預留擴展點
    """
    
    def __init__(self, scene_id: str = "ntpu", default_method: str = "rule"):
        """
        初始化決策介面
        
        Args:
            scene_id: 場景ID
            default_method: 預設決策方法 ("rule" 或 "rl")
        """
        self.scene_id = scene_id
        self.default_method = default_method
        self.supported_methods = ["rule"]  # 未來會加入 "rl"
        
        # 初始化規則式引擎
        self.rule_engine = RuleBasedHandoverEngine(scene_id)
        
        # RL 引擎預留（Phase 5 實現）
        self.rl_engine = None
        
        # 決策統計
        self.decision_counts = {
            "rule": 0,
            "rl": 0,
            "hybrid": 0
        }
        
        logger.info(f"HandoverDecisionInterface 初始化 - 場景: {scene_id}, 預設方法: {default_method}")
    
    def make_decision(self, state: Dict[str, Any], method: str = None) -> Optional[Dict[str, Any]]:
        """
        生成換手決策
        
        Args:
            state: 系統狀態或事件資料
            method: 指定決策方法 ("rule", "rl", "hybrid")，None 使用預設
            
        Returns:
            Optional[Dict]: 換手決策，沒有決策則返回 None
        """
        if method is None:
            method = self.default_method
        
        if method not in self.supported_methods:
            logger.warning(f"不支援的決策方法: {method}，回退到規則式")
            method = "rule"
        
        try:
            decision = None
            
            if method == "rule":
                decision = self._rule_based_decision(state)
            elif method == "rl":
                decision = self._rl_based_decision(state)
            elif method == "hybrid":
                decision = self._hybrid_decision(state)
            
            # 統計決策方法使用次數
            if decision:
                self.decision_counts[method] += 1
                decision["decision_method"] = method
                decision["interface_version"] = "v1.0"
            
            return decision
            
        except Exception as e:
            logger.error(f"決策生成失敗 ({method}): {e}")
            # 容錯：回退到規則式決策
            if method != "rule":
                logger.info("回退到規則式決策")
                return self._rule_based_decision(state)
            return None
    
    def _rule_based_decision(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """規則式決策實現"""
        return self.rule_engine.process_event(state)
    
    def _rl_based_decision(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        RL 決策實現（預留給 Phase 5）
        
        Args:
            state: 系統狀態
            
        Returns:
            Optional[Dict]: RL 決策結果
        """
        if self.rl_engine is None:
            raise NotImplementedError(
                "RL 決策引擎尚未實現，將在 Phase 5 中加入"
            )
        
        # Phase 5 實現：
        # 1. 狀態預處理和特徵提取
        # 2. RL 模型推論
        # 3. 動作轉換為換手決策
        # 4. 不確定性和信心度評估
        
        return self.rl_engine.predict(state)
    
    def _hybrid_decision(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        混合決策：結合規則式和 RL 方法
        
        Args:
            state: 系統狀態
            
        Returns:
            Optional[Dict]: 混合決策結果
        """
        # 先獲取規則式決策
        rule_decision = self._rule_based_decision(state)
        
        # 如果 RL 不可用，返回規則式結果
        if self.rl_engine is None:
            if rule_decision:
                rule_decision["decision_method"] = "hybrid_rule_only"
                rule_decision["hybrid_note"] = "RL 引擎不可用，使用純規則式決策"
            return rule_decision
        
        # Phase 5 實現混合邏輯：
        # 1. 獲取 RL 決策
        # 2. 比較兩種決策的信心度
        # 3. 根據系統狀態選擇最佳決策
        # 4. 可能結合兩種方法的優勢
        
        try:
            rl_decision = self._rl_based_decision(state)
            
            # 決策仲裁邏輯（預留實現）
            final_decision = self._arbitrate_decisions(rule_decision, rl_decision, state)
            
            if final_decision:
                final_decision["decision_method"] = "hybrid"
                final_decision["rule_confidence"] = rule_decision.get("confidence", 0.0) if rule_decision else 0.0
                final_decision["rl_confidence"] = rl_decision.get("confidence", 0.0) if rl_decision else 0.0
            
            return final_decision
            
        except NotImplementedError:
            # RL 不可用時的回退
            if rule_decision:
                rule_decision["decision_method"] = "hybrid_rule_fallback"
            return rule_decision
    
    def _arbitrate_decisions(self, rule_decision: Optional[Dict], rl_decision: Optional[Dict], 
                           state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        決策仲裁：在規則式和 RL 決策之間選擇
        
        Args:
            rule_decision: 規則式決策
            rl_decision: RL 決策
            state: 系統狀態
            
        Returns:
            Optional[Dict]: 最終決策
        """
        # Phase 5 實現複雜的仲裁邏輯：
        # 1. 緊急情況優先使用規則式（快速、可靠）
        # 2. 複雜場景優先使用 RL（學習能力強）
        # 3. 信心度比較
        # 4. 歷史績效考量
        
        # 暫時簡化實現：優先規則式決策
        if rule_decision and rule_decision.get("urgency") == "critical":
            return rule_decision
        
        # 比較信心度
        rule_confidence = rule_decision.get("confidence", 0.0) if rule_decision else 0.0
        rl_confidence = rl_decision.get("confidence", 0.0) if rl_decision else 0.0
        
        if rule_confidence > rl_confidence:
            return rule_decision
        else:
            return rl_decision
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """獲取決策統計資訊"""
        total_decisions = sum(self.decision_counts.values())
        
        return {
            "total_decisions": total_decisions,
            "method_distribution": self.decision_counts.copy(),
            "method_percentages": {
                method: (count / total_decisions * 100) if total_decisions > 0 else 0.0
                for method, count in self.decision_counts.items()
            },
            "supported_methods": self.supported_methods.copy(),
            "default_method": self.default_method,
            "rl_available": self.rl_engine is not None
        }
    
    def set_rl_engine(self, rl_engine):
        """
        設置 RL 引擎（Phase 5 使用）
        
        Args:
            rl_engine: RL 決策引擎實例
        """
        self.rl_engine = rl_engine
        if "rl" not in self.supported_methods:
            self.supported_methods.append("rl")
            self.supported_methods.append("hybrid")
        
        logger.info("RL 引擎已設置，支援方法已更新")
    
    def switch_default_method(self, method: str) -> bool:
        """
        切換預設決策方法
        
        Args:
            method: 新的預設方法
            
        Returns:
            bool: 切換是否成功
        """
        if method in self.supported_methods:
            old_method = self.default_method
            self.default_method = method
            logger.info(f"預設決策方法已從 {old_method} 切換到 {method}")
            return True
        else:
            logger.warning(f"無法切換到不支援的方法: {method}")
            return False
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取各引擎狀態"""
        status = {
            "rule_engine": {
                "available": True,
                "status": self.rule_engine.get_current_status()
            },
            "rl_engine": {
                "available": self.rl_engine is not None,
                "status": "not_implemented" if self.rl_engine is None else "operational"
            }
        }
        
        return status
    
    def reset_statistics(self) -> None:
        """重置決策統計"""
        self.decision_counts = {method: 0 for method in self.decision_counts.keys()}
        logger.info("決策統計已重置")


# 工廠函數：創建預配置的決策介面
def create_handover_decision_interface(scene_id: str = "ntpu", 
                                     method: str = "rule") -> HandoverDecisionInterface:
    """
    創建換手決策介面的工廠函數
    
    Args:
        scene_id: 場景ID
        method: 決策方法
        
    Returns:
        HandoverDecisionInterface: 配置好的決策介面
    """
    interface = HandoverDecisionInterface(scene_id, method)
    
    # 未來可以在這裡加入更多配置邏輯
    # 例如：根據場景載入特定的 RL 模型
    
    return interface

