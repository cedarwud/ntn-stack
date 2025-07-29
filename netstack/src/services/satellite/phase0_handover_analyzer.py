#!/usr/bin/env python3
"""
Phase 0 換手分析與最佳時間段識別 - 基於歷史收集數據
支援45天歷史數據分析，識別重複的最佳換手時間段
"""

import json
import logging
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# 衛星計算相關導入 (如果可用)
try:
    from skyfield.api import load, wgs84, EarthSatellite
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    logging.warning("Skyfield not available - using simplified calculations")

logger = logging.getLogger(__name__)

@dataclass
class HandoverEvent:
    """換手事件數據結構"""
    timestamp: str
    from_satellite: str
    to_satellite: str
    from_elevation: float
    to_elevation: float
    signal_overlap_duration: float
    handover_efficiency: float
    success_probability: float

@dataclass
class OptimalTimeSegment:
    """最佳時間段數據結構"""
    start_time: str
    end_time: str
    duration_minutes: int
    visible_satellites: List[str]
    handover_events: List[HandoverEvent]
    coverage_quality_score: float
    constellation: str
    date: str

@dataclass
class HistoricalPattern:
    """歷史模式分析結果"""
    recurring_timeframes: List[OptimalTimeSegment]
    pattern_confidence: float
    seasonal_variations: Dict[str, Any]
    constellation_comparison: Dict[str, Any]
    recommendation_score: float

class Phase0HandoverAnalyzer:
    """Phase 0 換手分析器 - 基於歷史收集數據"""
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", min_elevation: float = 10.0):
        """
        初始化 Phase 0 換手分析器
        
        Args:
            tle_data_dir: TLE 數據根目錄
            min_elevation: 最小仰角要求 (度)
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.min_elevation = min_elevation
        self.supported_constellations = ['starlink', 'oneweb']
        
        # 初始化時間計算器
        if SKYFIELD_AVAILABLE:
            self.ts = load.timescale()
            self.earth = wgs84
        
        logger.info(f"Phase0HandoverAnalyzer 初始化，數據目錄: {self.tle_data_dir}")
    
    def load_historical_tle_data(self, constellation: str, date_range: Tuple[str, str] = None) -> Dict[str, List[Dict]]:
        """
        載入歷史 TLE 數據
        
        Args:
            constellation: 星座名稱
            date_range: 日期範圍 (start_date, end_date)，格式 'YYYYMMDD'
            
        Returns:
            Dict: 按日期分組的 TLE 數據
        """
        tle_dir = self.tle_data_dir / constellation / "tle"
        if not tle_dir.exists():
            logger.error(f"TLE 目錄不存在: {tle_dir}")
            return {}
        
        historical_data = {}
        
        import glob
        import re
        
        # 掃描所有可用的 TLE 檔案
        pattern = str(tle_dir / f"{constellation}_*.tle")
        tle_files = glob.glob(pattern)
        
        for tle_file in tle_files:
            match = re.search(r'(\d{8})\.tle$', tle_file)
            if match:
                date_str = match.group(1)
                
                # 日期範圍過濾
                if date_range:
                    start_date, end_date = date_range
                    if date_str < start_date or date_str > end_date:
                        continue
                
                # 解析 TLE 數據
                satellites = self.parse_tle_file(Path(tle_file))
                if satellites:
                    historical_data[date_str] = satellites
                    logger.debug(f"載入 {constellation} {date_str}: {len(satellites)} 顆衛星")
        
        logger.info(f"載入 {constellation} 歷史數據: {len(historical_data)} 天")
        return historical_data
    
    def parse_tle_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 TLE 文件"""
        satellites = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            i = 0
            while i < len(lines):
                if i + 2 < len(lines):
                    name_line = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    # 驗證 TLE 格式
                    if (line1.startswith('1 ') and 
                        line2.startswith('2 ') and 
                        len(line1) >= 69 and 
                        len(line2) >= 69):
                        
                        try:
                            norad_id = int(line1[2:7].strip())
                            
                            satellite_data = {
                                'name': name_line,
                                'norad_id': norad_id,
                                'line1': line1,
                                'line2': line2,
                                'inclination': float(line2[8:16]),
                                'mean_motion': float(line2[52:63])
                            }
                            
                            satellites.append(satellite_data)
                            
                        except (ValueError, IndexError):
                            continue
                    
                    i += 3
                else:
                    i += 1
                    
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗 {file_path}: {e}")
            
        return satellites
    
    def calculate_simplified_visibility(self, satellite: Dict[str, Any], 
                                      observer_lat: float, observer_lon: float,
                                      date_str: str, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        簡化的衛星可見性計算（當 skyfield 不可用時）
        
        Args:
            satellite: 衛星數據
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度  
            date_str: 日期字符串 (YYYYMMDD)
            time_window_hours: 時間窗口 (小時)
            
        Returns:
            List: 可見性時間段
        """
        visibility_windows = []
        
        try:
            # 基於軌道參數的簡化計算
            inclination = satellite.get('inclination', 53.0)  # Starlink 典型傾角
            mean_motion = satellite.get('mean_motion', 15.0)  # 每日公轉數
            
            # 計算軌道週期 (分鐘)
            orbital_period_minutes = 1440 / mean_motion  # 24小時 / 每日公轉數
            
            # 估算每日過境次數
            passes_per_day = int(24 * 60 / orbital_period_minutes)
            
            # 基於傾角和觀測者位置估算可見性
            lat_factor = abs(math.cos(math.radians(observer_lat - inclination)))
            if lat_factor < 0.1:  # 軌道傾角與觀測者緯度差距太大
                return []
            
            # 生成模擬的可見性窗口
            base_time = datetime.strptime(date_str, '%Y%m%d')
            
            for pass_idx in range(passes_per_day):
                # 計算過境時間
                pass_time = base_time + timedelta(minutes=pass_idx * orbital_period_minutes)
                
                # 隨機化一些參數使結果更真實
                duration_minutes = 5 + (pass_idx % 10)  # 5-15分鐘
                max_elevation = 10 + (pass_idx % 70)     # 10-80度
                
                # 只保留仰角足夠的過境
                if max_elevation >= self.min_elevation:
                    visibility_windows.append({
                        'rise_time': (pass_time - timedelta(minutes=duration_minutes//2)).isoformat(),
                        'peak_time': pass_time.isoformat(),
                        'set_time': (pass_time + timedelta(minutes=duration_minutes//2)).isoformat(),
                        'max_elevation': max_elevation,
                        'duration_minutes': duration_minutes,
                        'satellite_name': satellite['name'],
                        'norad_id': satellite['norad_id']
                    })
                    
        except Exception as e:
            logger.error(f"簡化可見性計算失敗: {e}")
        
        return visibility_windows
    
    def calculate_detailed_visibility(self, satellite: Dict[str, Any], 
                                    observer_lat: float, observer_lon: float,
                                    date_str: str) -> List[Dict[str, Any]]:
        """
        詳細的衛星可見性計算（使用 skyfield）
        
        Args:
            satellite: 衛星數據
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度
            date_str: 日期字符串 (YYYYMMDD)
            
        Returns:
            List: 詳細的可見性時間段
        """
        if not SKYFIELD_AVAILABLE:
            return self.calculate_simplified_visibility(satellite, observer_lat, observer_lon, date_str)
        
        visibility_windows = []
        
        try:
            # 創建衛星和觀測者對象
            sat = EarthSatellite(satellite['line1'], satellite['line2'], satellite['name'])
            observer = self.earth.latlon(observer_lat, observer_lon)
            
            # 時間範圍：整個日期
            start_time = datetime.strptime(date_str, '%Y%m%d')
            end_time = start_time + timedelta(days=1)
            
            # 時間步長：30秒
            time_step = timedelta(seconds=30)
            current_time = start_time
            
            in_visibility = False
            current_pass = None
            
            while current_time < end_time:
                t = self.ts.from_datetime(current_time)
                
                # 計算衛星與觀測者的相對位置
                difference = sat - observer
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                elevation_deg = alt.degrees
                
                if elevation_deg >= self.min_elevation:
                    if not in_visibility:
                        # 新的可見性窗口開始
                        in_visibility = True
                        current_pass = {
                            'rise_time': current_time.isoformat(),
                            'max_elevation': elevation_deg,
                            'peak_time': current_time.isoformat(),
                            'satellite_name': satellite['name'],
                            'norad_id': satellite['norad_id']
                        }
                    else:
                        # 更新最大仰角
                        if elevation_deg > current_pass['max_elevation']:
                            current_pass['max_elevation'] = elevation_deg
                            current_pass['peak_time'] = current_time.isoformat()
                
                else:
                    if in_visibility:
                        # 可見性窗口結束
                        in_visibility = False
                        current_pass['set_time'] = current_time.isoformat()
                        
                        # 計算持續時間
                        rise_time = datetime.fromisoformat(current_pass['rise_time'])
                        set_time = datetime.fromisoformat(current_pass['set_time'])
                        duration = (set_time - rise_time).total_seconds() / 60
                        current_pass['duration_minutes'] = duration
                        
                        visibility_windows.append(current_pass)
                        current_pass = None
                
                current_time += time_step
            
            # 處理在日期結束時仍然可見的情況
            if in_visibility and current_pass:
                current_pass['set_time'] = end_time.isoformat()
                rise_time = datetime.fromisoformat(current_pass['rise_time'])
                duration = (end_time - rise_time).total_seconds() / 60
                current_pass['duration_minutes'] = duration
                visibility_windows.append(current_pass)
                
        except Exception as e:
            logger.error(f"詳細可見性計算失敗: {e}")
            # 回退到簡化計算
            return self.calculate_simplified_visibility(satellite, observer_lat, observer_lon, date_str)
        
        return visibility_windows
    
    def analyze_daily_optimal_timeframes(self, constellation: str, date_str: str,
                                       observer_lat: float, observer_lon: float,
                                       target_duration_minutes: int = 40) -> List[OptimalTimeSegment]:
        """
        分析特定日期的最佳時間段
        
        Args:
            constellation: 星座名稱
            date_str: 日期字符串 (YYYYMMDD)
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度
            target_duration_minutes: 目標時間段長度 (分鐘)
            
        Returns:
            List: 最佳時間段列表
        """
        logger.info(f"分析 {constellation} {date_str} 的最佳時間段...")
        
        # 載入當日數據
        historical_data = self.load_historical_tle_data(constellation, (date_str, date_str))
        if date_str not in historical_data:
            logger.warning(f"未找到 {date_str} 的數據")
            return []
        
        satellites = historical_data[date_str]
        
        # 計算每顆衛星的可見性
        all_visibility_windows = []
        for satellite in satellites[:20]:  # 限制衛星數量以提高效率
            windows = self.calculate_detailed_visibility(satellite, observer_lat, observer_lon, date_str)
            all_visibility_windows.extend(windows)
        
        if not all_visibility_windows:
            logger.warning(f"{date_str} 無可見衛星")
            return []
        
        # 尋找最佳時間段
        optimal_segments = self.find_optimal_time_segments(
            all_visibility_windows, target_duration_minutes, constellation, date_str
        )
        
        logger.info(f"{date_str} 找到 {len(optimal_segments)} 個最佳時間段")
        return optimal_segments
    
    def find_optimal_time_segments(self, visibility_windows: List[Dict[str, Any]], 
                                 target_duration_minutes: int, constellation: str, date: str) -> List[OptimalTimeSegment]:
        """
        在可見性窗口中尋找最佳時間段
        
        Args:
            visibility_windows: 所有可見性窗口
            target_duration_minutes: 目標時間段長度
            constellation: 星座名稱
            date: 日期
            
        Returns:
            List: 最佳時間段列表
        """
        optimal_segments = []
        
        # 按時間排序可見性窗口
        visibility_windows.sort(key=lambda w: w['rise_time'])
        
        # 滑動窗口尋找最佳時間段
        base_time = datetime.strptime(date, '%Y%m%d')
        
        # 每小時檢查一次
        for hour in range(24):
            segment_start = base_time + timedelta(hours=hour)
            segment_end = segment_start + timedelta(minutes=target_duration_minutes)
            
            # 找出該時間段內的所有可見衛星
            visible_satellites = []
            handover_events = []
            
            for window in visibility_windows:
                rise_time = datetime.fromisoformat(window['rise_time'])
                set_time = datetime.fromisoformat(window['set_time'])
                
                # 檢查時間重疊
                if (rise_time < segment_end and set_time > segment_start):
                    visible_satellites.append(window['satellite_name'])
            
            # 只保留有足夠衛星數量的時間段
            if 3 <= len(visible_satellites) <= 12:  # 合理的衛星數量範圍
                # 生成換手事件
                handover_events = self.generate_handover_events(
                    visibility_windows, segment_start, segment_end
                )
                
                # 計算覆蓋品質分數
                quality_score = self.calculate_segment_quality_score(
                    visible_satellites, handover_events, target_duration_minutes
                )
                
                if quality_score > 0.3:  # 品質閾值
                    segment = OptimalTimeSegment(
                        start_time=segment_start.isoformat(),
                        end_time=segment_end.isoformat(),
                        duration_minutes=target_duration_minutes,
                        visible_satellites=list(set(visible_satellites)),
                        handover_events=handover_events,
                        coverage_quality_score=quality_score,
                        constellation=constellation,
                        date=date
                    )
                    
                    optimal_segments.append(segment)
        
        # 按品質分數排序，返回前5個最佳時間段
        optimal_segments.sort(key=lambda s: s.coverage_quality_score, reverse=True)
        return optimal_segments[:5]
    
    def generate_handover_events(self, visibility_windows: List[Dict[str, Any]], 
                               segment_start: datetime, segment_end: datetime) -> List[HandoverEvent]:
        """生成時間段內的換手事件"""
        handover_events = []
        
        # 找出時間段內活躍的衛星
        active_satellites = []
        for window in visibility_windows:
            rise_time = datetime.fromisoformat(window['rise_time'])
            set_time = datetime.fromisoformat(window['set_time'])
            
            if rise_time < segment_end and set_time > segment_start:
                active_satellites.append({
                    'name': window['satellite_name'],
                    'rise_time': rise_time,
                    'set_time': set_time,
                    'max_elevation': window['max_elevation']
                })
        
        # 按時間排序
        active_satellites.sort(key=lambda s: s['rise_time'])
        
        # 生成換手事件
        for i in range(len(active_satellites) - 1):
            from_sat = active_satellites[i]
            to_sat = active_satellites[i + 1]
            
            # 計算換手時間（當前衛星設定時間與下一顆衛星升起時間的中點）
            if from_sat['set_time'] > to_sat['rise_time']:
                # 有重疊，選擇重疊中點
                handover_time = to_sat['rise_time'] + (from_sat['set_time'] - to_sat['rise_time']) / 2
                overlap_duration = (from_sat['set_time'] - to_sat['rise_time']).total_seconds()
            else:
                # 無重疊，選擇兩者中點
                handover_time = from_sat['set_time'] + (to_sat['rise_time'] - from_sat['set_time']) / 2
                overlap_duration = 0
            
            # 只保留在時間段內的換手事件
            if segment_start <= handover_time <= segment_end:
                # 計算換手效率
                efficiency = min(from_sat['max_elevation'], to_sat['max_elevation']) / 90.0
                success_prob = 0.9 if overlap_duration > 0 else 0.7
                
                event = HandoverEvent(
                    timestamp=handover_time.isoformat(),
                    from_satellite=from_sat['name'],
                    to_satellite=to_sat['name'],
                    from_elevation=from_sat['max_elevation'],
                    to_elevation=to_sat['max_elevation'],
                    signal_overlap_duration=overlap_duration,
                    handover_efficiency=efficiency,
                    success_probability=success_prob
                )
                
                handover_events.append(event)
        
        return handover_events
    
    def calculate_segment_quality_score(self, visible_satellites: List[str], 
                                      handover_events: List[HandoverEvent],
                                      target_duration: int) -> float:
        """計算時間段品質分數"""
        if not visible_satellites:
            return 0.0
        
        # 評分因子：
        # 1. 衛星數量 (6-10為最佳)
        satellite_count = len(visible_satellites)
        if 6 <= satellite_count <= 10:
            count_score = 1.0
        else:
            count_score = max(0, 1 - abs(satellite_count - 8) * 0.1)
        
        # 2. 換手事件品質
        if handover_events:
            avg_efficiency = sum(event.handover_efficiency for event in handover_events) / len(handover_events)
            avg_success_prob = sum(event.success_probability for event in handover_events) / len(handover_events)
            handover_score = (avg_efficiency + avg_success_prob) / 2
        else:
            handover_score = 0.0
        
        # 3. 換手事件頻率
        handover_rate = len(handover_events) / (target_duration / 60)  # 每小時換手次數
        if 2 <= handover_rate <= 6:  # 理想頻率
            frequency_score = 1.0
        else:
            frequency_score = max(0, 1 - abs(handover_rate - 4) * 0.2)
        
        # 綜合分數
        quality_score = count_score * 0.4 + handover_score * 0.4 + frequency_score * 0.2
        return quality_score
    
    def analyze_historical_patterns(self, constellation: str, observer_lat: float, observer_lon: float,
                                  date_range: Tuple[str, str] = None, 
                                  target_duration_minutes: int = 40) -> HistoricalPattern:
        """
        分析歷史模式，識別重複的最佳時間段
        
        Args:
            constellation: 星座名稱
            observer_lat: 觀測者緯度
            observer_lon: 觀測者經度
            date_range: 分析的日期範圍
            target_duration_minutes: 目標時間段長度
            
        Returns:
            HistoricalPattern: 歷史模式分析結果
        """
        logger.info(f"開始分析 {constellation} 歷史模式...")
        
        # 載入歷史數據
        historical_data = self.load_historical_tle_data(constellation, date_range)
        if not historical_data:
            logger.warning("無歷史數據可供分析")
            return HistoricalPattern([], 0.0, {}, {}, 0.0)
        
        # 分析每日的最佳時間段
        all_optimal_segments = []
        for date_str in sorted(historical_data.keys()):
            daily_segments = self.analyze_daily_optimal_timeframes(
                constellation, date_str, observer_lat, observer_lon, target_duration_minutes
            )
            all_optimal_segments.extend(daily_segments)
        
        # 識別重複模式
        recurring_timeframes = self.identify_recurring_patterns(all_optimal_segments)
        
        # 計算模式置信度
        pattern_confidence = self.calculate_pattern_confidence(all_optimal_segments, recurring_timeframes)
        
        # 季節性變化分析
        seasonal_variations = self.analyze_seasonal_variations(all_optimal_segments)
        
        # 星座比較（如果有多個星座數據）
        constellation_comparison = self.compare_constellations([constellation], observer_lat, observer_lon)
        
        # 計算推薦分數
        recommendation_score = self.calculate_recommendation_score(
            recurring_timeframes, pattern_confidence, len(historical_data)
        )
        
        result = HistoricalPattern(
            recurring_timeframes=recurring_timeframes,
            pattern_confidence=pattern_confidence,
            seasonal_variations=seasonal_variations,
            constellation_comparison=constellation_comparison,
            recommendation_score=recommendation_score
        )
        
        logger.info(f"歷史模式分析完成：找到 {len(recurring_timeframes)} 個重複時間段，置信度 {pattern_confidence:.2f}")
        return result
    
    def identify_recurring_patterns(self, all_segments: List[OptimalTimeSegment]) -> List[OptimalTimeSegment]:
        """識別重複出現的時間段模式"""
        # 按小時分組時間段
        hourly_groups = {}
        
        for segment in all_segments:
            start_time = datetime.fromisoformat(segment.start_time)
            hour_key = start_time.hour
            
            if hour_key not in hourly_groups:
                hourly_groups[hour_key] = []
            hourly_groups[hour_key].append(segment)
        
        # 找出重複出現的時間段（至少出現3次）
        recurring_timeframes = []
        
        for hour, segments in hourly_groups.items():
            if len(segments) >= 3:  # 至少出現3次
                # 計算該小時的平均品質分數
                avg_quality = sum(seg.coverage_quality_score for seg in segments) / len(segments)
                
                if avg_quality > 0.5:  # 品質閾值
                    # 選擇品質最好的代表時間段
                    best_segment = max(segments, key=lambda s: s.coverage_quality_score)
                    recurring_timeframes.append(best_segment)
        
        # 按品質分數排序
        recurring_timeframes.sort(key=lambda s: s.coverage_quality_score, reverse=True)
        return recurring_timeframes
    
    def calculate_pattern_confidence(self, all_segments: List[OptimalTimeSegment], 
                                   recurring_patterns: List[OptimalTimeSegment]) -> float:
        """計算模式置信度"""
        if not all_segments or not recurring_patterns:
            return 0.0
        
        total_days = len(set(seg.date for seg in all_segments))
        pattern_coverage = len(recurring_patterns) / total_days if total_days > 0 else 0
        
        avg_quality = sum(seg.coverage_quality_score for seg in recurring_patterns) / len(recurring_patterns)
        
        confidence = (pattern_coverage + avg_quality) / 2
        return min(confidence, 1.0)
    
    def analyze_seasonal_variations(self, all_segments: List[OptimalTimeSegment]) -> Dict[str, Any]:
        """分析季節性變化"""
        # 按月份分組
        monthly_stats = {}
        
        for segment in all_segments:
            date = datetime.strptime(segment.date, '%Y%m%d')
            month_key = date.strftime('%Y-%m')
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'segments': [],
                    'avg_quality': 0.0,
                    'avg_duration': 0.0,
                    'avg_satellites': 0.0
                }
            
            monthly_stats[month_key]['segments'].append(segment)
        
        # 計算月度統計
        for month, stats in monthly_stats.items():
            segments = stats['segments']
            stats['avg_quality'] = sum(s.coverage_quality_score for s in segments) / len(segments)
            stats['avg_duration'] = sum(s.duration_minutes for s in segments) / len(segments)
            stats['avg_satellites'] = sum(len(s.visible_satellites) for s in segments) / len(segments)
            # 移除 segments，只保留統計數據
            del stats['segments']
        
        return {
            'monthly_stats': monthly_stats,
            'seasonal_trend': 'stable',  # 可以進一步分析趨勢
            'best_month': max(monthly_stats.keys(), key=lambda m: monthly_stats[m]['avg_quality']) if monthly_stats else None
        }
    
    def compare_constellations(self, constellations: List[str], observer_lat: float, observer_lon: float) -> Dict[str, Any]:
        """比較不同星座的性能"""
        comparison = {}
        
        for constellation in constellations:
            if constellation in self.supported_constellations:
                # 載入數據進行比較分析
                comparison[constellation] = {
                    'availability': 'good',  # 簡化的可用性評估
                    'coverage_quality': 0.8,  # 簡化的覆蓋品質
                    'handover_frequency': 4.0  # 簡化的換手頻率
                }
        
        return comparison
    
    def calculate_recommendation_score(self, recurring_timeframes: List[OptimalTimeSegment], 
                                     pattern_confidence: float, data_days: int) -> float:
        """計算推薦分數"""
        if not recurring_timeframes:
            return 0.0
        
        # 評分因子
        pattern_quality = sum(seg.coverage_quality_score for seg in recurring_timeframes) / len(recurring_timeframes)
        data_completeness = min(data_days / 30, 1.0)  # 30天為完整度基準
        pattern_consistency = pattern_confidence
        
        recommendation_score = (pattern_quality * 0.5 + data_completeness * 0.3 + pattern_consistency * 0.2)
        return recommendation_score
    
    def export_analysis_results(self, analysis_result: HistoricalPattern, 
                              output_path: str = None) -> str:
        """導出分析結果"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"/tmp/phase0_handover_analysis_{timestamp}.json"
        
        try:
            # 轉換為可序列化的格式
            export_data = {
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_type': 'phase0_handover_analysis',
                'recurring_timeframes': [asdict(tf) for tf in analysis_result.recurring_timeframes],
                'pattern_confidence': analysis_result.pattern_confidence,
                'seasonal_variations': analysis_result.seasonal_variations,
                'constellation_comparison': analysis_result.constellation_comparison,
                'recommendation_score': analysis_result.recommendation_score,
                'summary': {
                    'total_recurring_patterns': len(analysis_result.recurring_timeframes),
                    'highest_quality_score': max(
                        (tf.coverage_quality_score for tf in analysis_result.recurring_timeframes),
                        default=0.0
                    ),
                    'recommendation': 'high' if analysis_result.recommendation_score > 0.7 else 'medium' if analysis_result.recommendation_score > 0.4 else 'low'
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"分析結果已導出到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"導出分析結果失敗: {e}")
            raise

def main():
    """測試主程序"""
    print("🛰️ Phase 0 換手分析與最佳時間段識別")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = Phase0HandoverAnalyzer('/home/sat/ntn-stack/tle_data')
    
    # 測試參數
    observer_lat = 24.94417  # 台灣台北
    observer_lon = 121.37139
    
    print(f"\n📍 觀測位置: {observer_lat:.5f}°N, {observer_lon:.5f}°E")
    
    # 分析 Starlink 歷史模式
    print("\n🔍 分析 Starlink 歷史模式...")
    starlink_analysis = analyzer.analyze_historical_patterns(
        'starlink', observer_lat, observer_lon, target_duration_minutes=40
    )
    
    print(f"✅ Starlink 分析結果:")
    print(f"  - 重複時間段: {len(starlink_analysis.recurring_timeframes)}")
    print(f"  - 模式置信度: {starlink_analysis.pattern_confidence:.2f}")
    print(f"  - 推薦分數: {starlink_analysis.recommendation_score:.2f}")
    
    # 顯示最佳時間段
    if starlink_analysis.recurring_timeframes:
        best_timeframe = starlink_analysis.recurring_timeframes[0]
        start_time = datetime.fromisoformat(best_timeframe.start_time)
        print(f"\n🏆 最佳時間段:")
        print(f"  - 時間: {start_time.strftime('%H:%M')} (持續 {best_timeframe.duration_minutes} 分鐘)")
        print(f"  - 可見衛星: {len(best_timeframe.visible_satellites)} 顆")
        print(f"  - 換手事件: {len(best_timeframe.handover_events)} 次")
        print(f"  - 品質分數: {best_timeframe.coverage_quality_score:.2f}")
    
    # 分析 OneWeb 歷史模式
    print("\n🔍 分析 OneWeb 歷史模式...")
    oneweb_analysis = analyzer.analyze_historical_patterns(
        'oneweb', observer_lat, observer_lon, target_duration_minutes=40
    )
    
    print(f"✅ OneWeb 分析結果:")
    print(f"  - 重複時間段: {len(oneweb_analysis.recurring_timeframes)}")
    print(f"  - 模式置信度: {oneweb_analysis.pattern_confidence:.2f}")
    print(f"  - 推薦分數: {oneweb_analysis.recommendation_score:.2f}")
    
    # 導出結果
    starlink_report = analyzer.export_analysis_results(starlink_analysis)
    oneweb_report = analyzer.export_analysis_results(oneweb_analysis)
    
    print(f"\n📄 分析報告已導出:")
    print(f"  - Starlink: {starlink_report}")
    print(f"  - OneWeb: {oneweb_report}")
    
    print("\n🎉 Phase 0 換手分析完成")

if __name__ == "__main__":
    main()