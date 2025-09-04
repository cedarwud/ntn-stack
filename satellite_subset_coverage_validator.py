#!/usr/bin/env python3
"""
衛星子集覆蓋率驗證器
====================

目標：驗證時空錯置理論，測試不同規模的衛星子集是否能達到10-15/3-6的持續覆蓋目標
方法：從階段六數據中選擇不同規模的衛星子集，計算實際可見性時間序列
"""

import json
import numpy as np
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import sys

# 設置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CoverageStats:
    """覆蓋率統計"""
    min_visible: int
    max_visible: int
    avg_visible: float
    coverage_rate: float  # 滿足最低要求的時間百分比
    gaps: List[Tuple[datetime, datetime]]  # 覆蓋不足的時間段

class SatelliteSubsetValidator:
    """衛星子集覆蓋率驗證器"""
    
    def __init__(self, data_dir: str = "/tmp/satellite_data"):
        self.data_dir = Path(data_dir)
        self.observer_lat = 24.9441667  # NTPU座標
        self.observer_lon = 121.3713889
        self.observer_alt = 100  # 海拔高度（米）
        
        # 目標可見性要求
        self.starlink_target = (10, 15)  # 最小-最大可見衛星數
        self.oneweb_target = (3, 6)
        
        # 載入衛星數據
        self.satellites_data = {}
        self.load_satellite_data()
        
    def load_satellite_data(self):
        """載入衛星軌道和信號數據"""
        logger.info("🔍 載入衛星數據...")
        
        # 嘗試從多個可能的位置載入數據
        possible_files = [
            self.data_dir / "stage3_signal_event_analysis_output.json",  # 使用階段三數據
            Path("/app/data/signal_event_analysis_output.json"),
            Path("/app/data/tle_orbital_calculation_output.json"),
            Path("/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json")
        ]
        
        tle_data = None
        for file_path in possible_files:
            if file_path.exists():
                logger.info(f"📥 載入TLE數據: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    tle_data = json.load(f)
                break
                
        if not tle_data:
            raise FileNotFoundError("找不到TLE軌道計算數據")
            
        # 處理數據格式
        if 'satellites' in tle_data:
            # 新格式：扁平化衛星陣列
            satellites = tle_data['satellites']
        elif 'constellations' in tle_data:
            # 舊格式：按星座分組
            satellites = []
            for constellation_data in tle_data['constellations'].values():
                if isinstance(constellation_data, dict) and 'satellites' in constellation_data:
                    satellites.extend(constellation_data['satellites'])
                elif isinstance(constellation_data, dict) and 'orbit_data' in constellation_data:
                    orbit_data = constellation_data['orbit_data']
                    if 'satellites' in orbit_data:
                        satellites.extend(orbit_data['satellites'])
        else:
            raise ValueError("無法識別的數據格式")
            
        # 按星座分組
        for sat in satellites:
            constellation = sat.get('constellation', 'unknown')
            if constellation not in self.satellites_data:
                self.satellites_data[constellation] = []
            self.satellites_data[constellation].append(sat)
            
        logger.info(f"✅ 載入完成:")
        for constellation, sats in self.satellites_data.items():
            logger.info(f"  {constellation}: {len(sats)} 顆衛星")
            
    def calculate_visibility_timeseries(self, satellites: List[Dict], 
                                      duration_hours: int = 24, 
                                      time_step_minutes: int = 1) -> np.ndarray:
        """計算衛星子集的可見性時間序列"""
        
        time_points = int(duration_hours * 60 / time_step_minutes)
        visibility_count = np.zeros(time_points)
        
        start_time = datetime.now(timezone.utc)
        
        for i, sat in enumerate(satellites):
            if i % 50 == 0:
                logger.info(f"  處理衛星 {i+1}/{len(satellites)}")
                
            # 獲取衛星軌道數據
            orbital_data = sat.get('orbital_data', {})
            positions = orbital_data.get('positions', [])
            
            if not positions:
                continue
                
            # 為每個時間點計算可見性
            for t_idx in range(time_points):
                current_time = start_time + timedelta(minutes=t_idx * time_step_minutes)
                
                # 找到最接近的位置數據點
                if self._is_satellite_visible(positions, current_time):
                    visibility_count[t_idx] += 1
                    
        return visibility_count
        
    def _is_satellite_visible(self, positions: List[Dict], target_time: datetime) -> bool:
        """判斷衛星在指定時間是否可見"""
        
        if not positions:
            return False
            
        # 找到最接近的時間點
        target_timestamp = target_time.timestamp()
        closest_pos = None
        min_time_diff = float('inf')
        
        for pos in positions:
            pos_time = datetime.fromisoformat(pos['timestamp'].replace('Z', '+00:00')).timestamp()
            time_diff = abs(pos_time - target_timestamp)
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_pos = pos
                
        if not closest_pos or min_time_diff > 3600:  # 1小時內的數據才有效
            return False
            
        # 計算仰角
        elevation = closest_pos.get('elevation_deg', 0)
        return elevation >= 10.0  # 10度仰角門檻
        
    def test_subset_coverage(self, subset_sizes: Dict[str, int]) -> CoverageStats:
        """測試指定規模子集的覆蓋率"""
        
        logger.info(f"📊 測試子集覆蓋率:")
        for constellation, size in subset_sizes.items():
            logger.info(f"  {constellation}: {size} 顆衛星")
            
        # 選擇衛星子集（選擇前N顆最優衛星）
        selected_satellites = {}
        total_satellites = []
        
        for constellation, target_size in subset_sizes.items():
            if constellation in self.satellites_data:
                available = self.satellites_data[constellation]
                
                # 簡單選擇：取前N顆衛星
                # TODO: 可以加入更智能的選擇策略（信號品質、軌道分布等）
                selected = available[:target_size]
                selected_satellites[constellation] = selected
                total_satellites.extend(selected)
                
                logger.info(f"  已選擇 {constellation}: {len(selected)}/{len(available)} 顆")
        
        # 計算可見性時間序列
        logger.info("🔄 計算可見性時間序列...")
        starlink_visibility = np.zeros(24*60) if 'starlink' not in selected_satellites else \
                             self.calculate_visibility_timeseries(selected_satellites.get('starlink', []))
        oneweb_visibility = np.zeros(24*60) if 'oneweb' not in selected_satellites else \
                           self.calculate_visibility_timeseries(selected_satellites.get('oneweb', []))
        
        # 分析覆蓋率
        return self._analyze_coverage(starlink_visibility, oneweb_visibility)
        
    def _analyze_coverage(self, starlink_vis: np.ndarray, oneweb_vis: np.ndarray) -> Dict[str, CoverageStats]:
        """分析覆蓋率統計"""
        
        results = {}
        
        # 分析Starlink覆蓋率
        starlink_stats = CoverageStats(
            min_visible=int(np.min(starlink_vis)),
            max_visible=int(np.max(starlink_vis)),
            avg_visible=float(np.mean(starlink_vis)),
            coverage_rate=float(np.sum(starlink_vis >= self.starlink_target[0]) / len(starlink_vis)),
            gaps=[]
        )
        
        # 分析OneWeb覆蓋率
        oneweb_stats = CoverageStats(
            min_visible=int(np.min(oneweb_vis)),
            max_visible=int(np.max(oneweb_vis)),
            avg_visible=float(np.mean(oneweb_vis)),
            coverage_rate=float(np.sum(oneweb_vis >= self.oneweb_target[0]) / len(oneweb_vis)),
            gaps=[]
        )
        
        results['starlink'] = starlink_stats
        results['oneweb'] = oneweb_stats
        
        return results
        
    def run_progressive_validation(self):
        """執行漸進式驗證：從小子集開始，逐步增加規模"""
        
        logger.info("🚀 開始漸進式子集覆蓋率驗證")
        
        # 測試不同規模的子集
        test_cases = [
            {'starlink': 20, 'oneweb': 10},    # 非常小的子集
            {'starlink': 50, 'oneweb': 20},    # 小子集  
            {'starlink': 100, 'oneweb': 40},   # 中等子集
            {'starlink': 200, 'oneweb': 80},   # 大子集
            {'starlink': 400, 'oneweb': 120},  # 很大子集
            {'starlink': 850, 'oneweb': 150}   # 完整目標子集
        ]
        
        results = []
        
        for i, subset_sizes in enumerate(test_cases):
            logger.info(f"\n📋 測試案例 {i+1}/{len(test_cases)}")
            
            try:
                coverage_stats = self.test_subset_coverage(subset_sizes)
                
                result = {
                    'subset_sizes': subset_sizes,
                    'starlink_stats': coverage_stats['starlink'],
                    'oneweb_stats': coverage_stats['oneweb']
                }
                
                results.append(result)
                
                # 輸出結果
                self._print_coverage_result(subset_sizes, coverage_stats)
                
                # 檢查是否達到目標
                starlink_ok = (coverage_stats['starlink'].coverage_rate >= 0.95 and 
                             coverage_stats['starlink'].avg_visible >= self.starlink_target[0])
                oneweb_ok = (coverage_stats['oneweb'].coverage_rate >= 0.95 and 
                           coverage_stats['oneweb'].avg_visible >= self.oneweb_target[0])
                
                if starlink_ok and oneweb_ok:
                    logger.info(f"🎯 找到滿足要求的最小子集！")
                    break
                    
            except Exception as e:
                logger.error(f"❌ 測試案例失敗: {e}")
                continue
                
        return results
        
    def _print_coverage_result(self, subset_sizes: Dict[str, int], 
                             coverage_stats: Dict[str, CoverageStats]):
        """打印覆蓋率結果"""
        
        print(f"\n📊 子集規模: Starlink {subset_sizes.get('starlink', 0)}, OneWeb {subset_sizes.get('oneweb', 0)}")
        
        for constellation, stats in coverage_stats.items():
            target_min = self.starlink_target[0] if constellation == 'starlink' else self.oneweb_target[0]
            target_max = self.starlink_target[1] if constellation == 'starlink' else self.oneweb_target[1]
            
            status = "✅" if stats.coverage_rate >= 0.95 and stats.avg_visible >= target_min else "❌"
            
            print(f"  {constellation.upper()} {status}:")
            print(f"    可見範圍: {stats.min_visible}-{stats.max_visible} 顆 (目標: {target_min}-{target_max})")
            print(f"    平均可見: {stats.avg_visible:.1f} 顆")
            print(f"    覆蓋率: {stats.coverage_rate*100:.1f}% (目標: ≥95%)")

if __name__ == "__main__":
    validator = SatelliteSubsetValidator()
    results = validator.run_progressive_validation()
    
    print("\n🏆 驗證完成！")
    print("基於實際數據的驗證結果將幫助優化衛星子集選擇策略。")