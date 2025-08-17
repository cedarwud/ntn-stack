"""
🛰️ 階段六：動態衛星池規劃器
==============================

目標：為立體圖生成時空分散的動態衛星池，實現整個軌道週期的平衡覆蓋
輸入：階段五的混合存儲數據
輸出：動態衛星池規劃結果
處理對象：從563顆候選中篩選動態覆蓋衛星池
處理時間：約 3-5 分鐘
"""

import asyncio
import json
import time
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# 核心配置
@dataclass
class DynamicCoverageTarget:
    """動態覆蓋目標配置"""
    min_elevation_deg: float
    target_visible_range: Tuple[int, int]  # (min, max) 同時可見衛星數
    target_handover_range: Tuple[int, int]  # (min, max) handover候選數
    orbit_period_minutes: int
    estimated_pool_size: int

@dataclass
class VisibilityWindow:
    """可見時間窗口"""
    start_minute: int
    end_minute: int
    duration: int
    peak_elevation: float
    peak_minute: int

@dataclass
class SatelliteCandidate:
    """衛星候選資訊"""
    satellite_id: str
    constellation: str
    norad_id: int
    windows: List[VisibilityWindow]
    total_visible_time: int
    coverage_ratio: float
    distribution_score: float
    selection_rationale: Dict[str, float]

class Stage6DynamicPoolPlanner:
    """動態衛星池規劃器 - 確保整個軌道週期的平衡覆蓋"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processing_start_time = time.time()
        
        # NTPU觀測座標
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        self.time_resolution = 30  # 秒
        
        # 動態覆蓋目標
        self.coverage_targets = {
            'starlink': DynamicCoverageTarget(
                min_elevation_deg=5.0,
                target_visible_range=(10, 15),
                target_handover_range=(6, 8),
                orbit_period_minutes=96,
                estimated_pool_size=45
            ),
            'oneweb': DynamicCoverageTarget(
                min_elevation_deg=10.0,
                target_visible_range=(3, 6),
                target_handover_range=(2, 3),
                orbit_period_minutes=109,
                estimated_pool_size=20
            )
        }
    
    async def plan_dynamic_pools(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """主要規劃邏輯：規劃動態衛星池"""
        
        self.logger.info("🛰️ 開始動態衛星池規劃...")
        
        results = {
            "metadata": {
                "generation_time": datetime.now(timezone.utc).isoformat(),
                "stage": "stage6_dynamic_pool_planning",
                "observer_location": {
                    "latitude": self.observer_lat,
                    "longitude": self.observer_lon,
                    "location_name": "NTPU"
                },
                "planning_algorithm_version": "v1.0.0"
            },
            "starlink": {},
            "oneweb": {},
            "integration_notes": {
                "frontend_integration": "立體圖使用selected_satellites進行動畫渲染",
                "handover_simulation": "使用coverage_timeline進行換手場景模擬",
                "performance_expectations": "維持目標可見數量的95%+時間覆蓋"
            }
        }
        
        try:
            # 1. 載入處理過的衛星數據
            processed_satellites = await self._load_processed_satellite_data()
            
            # 2. 分析每顆衛星的可見時間窗口
            self.logger.info("🔍 分析可見時間窗口...")
            visibility_analysis = await self._analyze_visibility_windows(processed_satellites)
            
            # 3. 為Starlink規劃時空分散池
            self.logger.info("⭐ 規劃Starlink動態衛星池...")
            starlink_pool = await self._plan_time_distributed_pool(
                visibility_analysis['starlink'],
                self.coverage_targets['starlink']
            )
            
            # 4. 為OneWeb規劃時空分散池
            self.logger.info("🌐 規劃OneWeb動態衛星池...")
            oneweb_pool = await self._plan_time_distributed_pool(
                visibility_analysis['oneweb'], 
                self.coverage_targets['oneweb']
            )
            
            # 5. 動態覆蓋驗證
            self.logger.info("✅ 驗證動態覆蓋品質...")
            coverage_quality = await self._verify_dynamic_coverage(starlink_pool, oneweb_pool)
            
            # 6. 組裝結果
            results["starlink"] = self._format_constellation_results(
                starlink_pool, coverage_quality['starlink'], 'starlink'
            )
            results["oneweb"] = self._format_constellation_results(
                oneweb_pool, coverage_quality['oneweb'], 'oneweb'
            )
            
            # 7. 保存結果到Volume
            await self._save_pool_results(results)
            
            self.logger.info("🎯 動態衛星池規劃完成")
            
        except Exception as e:
            self.logger.error(f"❌ 動態池規劃失敗: {e}")
            results["error"] = str(e)
            raise
        
        return results
    
    async def _load_processed_satellite_data(self) -> Dict[str, Any]:
        """載入階段三處理完成的衛星數據（554顆候選衛星）"""
        
        # 從階段三的輸出文件載入真實數據
        base_path = Path("/app/data") if Path("/app/data").exists() else Path("/tmp/satellite_data")
        stage3_file = base_path / "stage3_signal_event_analysis_output.json"
        
        self.logger.info(f"📥 載入階段三數據: {stage3_file}")
        
        if not stage3_file.exists():
            raise FileNotFoundError(f"階段三輸出檔案不存在: {stage3_file}")
        
        try:
            with open(stage3_file, 'r', encoding='utf-8') as f:
                stage3_data = json.load(f)
            
            # 提取星座數據
            constellations = stage3_data.get('constellations', {})
            processed_data = {"starlink": [], "oneweb": []}
            
            for const_name, const_data in constellations.items():
                satellites = const_data.get('satellites', [])
                if const_name == 'starlink':
                    processed_data["starlink"] = satellites
                    self.logger.info(f"  載入 Starlink: {len(satellites)} 顆衛星")
                elif const_name == 'oneweb':
                    processed_data["oneweb"] = satellites
                    self.logger.info(f"  載入 OneWeb: {len(satellites)} 顆衛星")
            
            total_satellites = len(processed_data["starlink"]) + len(processed_data["oneweb"])
            self.logger.info(f"✅ 階段三數據載入完成: 總計 {total_satellites} 顆候選衛星")
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"載入階段三數據失敗: {e}")
            raise
    
    def _format_constellation_results(self, pool: List[SatelliteCandidate], 
                                    coverage: Dict[str, Any], 
                                    constellation: str) -> Dict[str, Any]:
        """格式化星座規劃結果"""
        
        target = self.coverage_targets[constellation]
        
        return {
            "estimated_pool_size": target.estimated_pool_size,
            "actual_pool_size": len(pool),
            "orbit_period_minutes": target.orbit_period_minutes,
            "target_visible_range": list(target.target_visible_range),
            "target_handover_range": list(target.target_handover_range),
            "min_elevation_deg": target.min_elevation_deg,
            "coverage_statistics": {
                "target_met_ratio": coverage.get('target_met_ratio', 0.0),
                "avg_visible_satellites": coverage.get('avg_visible', 0.0),
                "coverage_gaps_count": len(coverage.get('coverage_gaps', []))
            },
            "selected_satellites": [
                {
                    "satellite_id": candidate.satellite_id,
                    "constellation": candidate.constellation,
                    "norad_id": candidate.norad_id,
                    "selection_score": candidate.distribution_score,
                    "total_visible_time_minutes": candidate.total_visible_time,
                    "coverage_ratio": candidate.coverage_ratio,
                    "visibility_windows": [
                        {
                            "start_minute": w.start_minute,
                            "end_minute": w.end_minute,
                            "duration": w.duration,
                            "peak_elevation": w.peak_elevation
                        } for w in candidate.windows
                    ],
                    "selection_rationale": candidate.selection_rationale
                } for candidate in pool
            ]
        }
    
    async def _analyze_visibility_windows(self, processed_satellites: Dict[str, Any]) -> Dict[str, List[SatelliteCandidate]]:
        """分析每顆衛星在完整軌道週期內的可見窗口"""
        
        visibility_analysis = {"starlink": [], "oneweb": []}
        
        for constellation in ["starlink", "oneweb"]:
            satellites = processed_satellites.get(constellation, [])
            target = self.coverage_targets[constellation]
            
            self.logger.info(f"🔍 分析 {constellation} 可見窗口: {len(satellites)} 顆衛星")
            
            for satellite in satellites:
                windows = await self._calculate_satellite_windows(satellite, target)
                
                if windows:  # 只處理有可見窗口的衛星
                    candidate = SatelliteCandidate(
                        satellite_id=satellite.get('satellite_id', ''),
                        constellation=constellation,
                        norad_id=satellite.get('norad_id', 0),
                        windows=windows,
                        total_visible_time=sum(w.duration for w in windows),
                        coverage_ratio=sum(w.duration for w in windows) / target.orbit_period_minutes,
                        distribution_score=0.0,  # 後續計算
                        selection_rationale={}
                    )
                    
                    visibility_analysis[constellation].append(candidate)
        
        self.logger.info(f"📊 可見窗口分析完成: Starlink {len(visibility_analysis['starlink'])}顆, OneWeb {len(visibility_analysis['oneweb'])}顆")
        
        return visibility_analysis
    
    async def _calculate_satellite_windows(self, satellite: Dict[str, Any], 
                                         target: DynamicCoverageTarget) -> List[VisibilityWindow]:
        """計算單顆衛星的可見時間窗口"""
        
        windows = []
        
        # 從衛星的時間序列數據中提取可見窗口
        time_series = satellite.get('timeseries', [])
        if not time_series:
            # 如果沒有timeseries，嘗試使用positions數據
            positions = satellite.get('positions', [])
            if positions:
                time_series = positions
            else:
                return windows
        
        in_view = False
        window_start = None
        window_elevations = []
        
        for i, point in enumerate(time_series):
            elevation = point.get('elevation_deg', -999)
            
            # 計算時間偏移（分鐘）
            if 'time_offset_seconds' in point:
                minute = point['time_offset_seconds'] / 60.0
            else:
                minute = i * 0.5  # 假設30秒間隔
            
            if elevation >= target.min_elevation_deg and not in_view:
                # 衛星進入可見範圍
                in_view = True
                window_start = minute
                window_elevations = [elevation]
                
            elif elevation >= target.min_elevation_deg and in_view:
                # 衛星仍在可見範圍內
                window_elevations.append(elevation)
                
            elif elevation < target.min_elevation_deg and in_view:
                # 衛星離開可見範圍
                in_view = False
                
                if window_elevations:
                    peak_elevation = max(window_elevations)
                    peak_idx = window_elevations.index(peak_elevation)
                    
                    window = VisibilityWindow(
                        start_minute=int(window_start),
                        end_minute=int(minute),
                        duration=int(minute - window_start),
                        peak_elevation=peak_elevation,
                        peak_minute=int(window_start + peak_idx * 0.5)
                    )
                    
                    # 過濾太短的窗口（至少2分鐘）
                    if window.duration >= 2:
                        windows.append(window)
        
        return windows
    
    async def _plan_time_distributed_pool(self, candidates: List[SatelliteCandidate], 
                                         target: DynamicCoverageTarget) -> List[SatelliteCandidate]:
        """核心時空分散演算法 - 確保衛星不會同時出現/消失"""
        
        if not candidates:
            return []
        
        self.logger.info(f"🎯 時空分散選擇: {len(candidates)}顆候選 → {target.estimated_pool_size}顆目標")
        
        # 1. 創建時間槽網格（每分鐘一個槽）
        time_slots = [[] for _ in range(target.orbit_period_minutes)]
        selected_pool = []
        
        # 2. 計算並排序候選衛星的分散性評分
        scored_candidates = await self._score_satellites_for_distribution(candidates, target)
        
        # 3. 貪心選擇算法
        for candidate in scored_candidates:
            # 檢查時空衝突
            conflicts = self._check_temporal_conflicts(candidate, time_slots, target.target_visible_range[1])
            
            if not conflicts:
                # 無衝突，加入衛星池
                self._add_to_time_slots(candidate, time_slots)
                selected_pool.append(candidate)
                
                self.logger.debug(f"✅ 選中衛星: {candidate.satellite_id} (評分: {candidate.distribution_score:.3f})")
                
                # 檢查是否達到足夠覆蓋
                if self._check_coverage_adequate(time_slots, target):
                    self.logger.info(f"🎯 達到覆蓋目標，選擇了 {len(selected_pool)} 顆衛星")
                    break
            else:
                self.logger.debug(f"⚠️ 跳過衛星 {candidate.satellite_id}: 時空衝突")
        
        self.logger.info(f"🔄 時空分散選擇完成: {len(selected_pool)} 顆衛星")
        
        return selected_pool
    
    async def _score_satellites_for_distribution(self, candidates: List[SatelliteCandidate], 
                                               target: DynamicCoverageTarget) -> List[SatelliteCandidate]:
        """多維度評分確保最佳分散性"""
        
        for candidate in candidates:
            score = 0.0
            rationale = {}
            
            # 1. 可見時間品質 (30%)
            visibility_score = min(1.0, candidate.total_visible_time / 30)
            score += visibility_score * 0.3
            rationale['visibility_score'] = visibility_score
            
            # 2. 時間分散性 (40%) - 關鍵指標
            dispersion_score = self._calculate_temporal_dispersion(candidate.windows)
            score += dispersion_score * 0.4
            rationale['dispersion_score'] = dispersion_score
            
            # 3. 信號品質估算 (20%)
            signal_score = self._estimate_signal_quality(candidate)
            score += signal_score * 0.2
            rationale['signal_score'] = signal_score
            
            # 4. 軌道多樣性 (10%)
            orbit_diversity = self._calculate_orbit_diversity_score(candidate)
            score += orbit_diversity * 0.1
            rationale['orbit_diversity'] = orbit_diversity
            
            candidate.distribution_score = score
            candidate.selection_rationale = rationale
        
        # 按分散性評分降序排序
        return sorted(candidates, key=lambda x: x.distribution_score, reverse=True)
    
    def _calculate_temporal_dispersion(self, windows: List[VisibilityWindow]) -> float:
        """計算時間分散性評分"""
        
        if not windows:
            return 0.0
        
        # 計算窗口間間隔的方差，間隔越均勻分散性越高
        if len(windows) < 2:
            return 0.5  # 單個窗口給予中等分數
        
        # 窗口開始時間
        start_times = [w.start_minute for w in windows]
        start_times.sort()
        
        # 計算間隔
        intervals = []
        for i in range(1, len(start_times)):
            intervals.append(start_times[i] - start_times[i-1])
        
        # 添加循環間隔（最後到第一個）
        if len(start_times) > 1:
            cycle_interval = (start_times[0] + 96) - start_times[-1]  # 假設96分鐘週期
            intervals.append(cycle_interval)
        
        # 計算均勻性：方差越小，分散性越好
        if intervals:
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            # 標準化到0-1範圍，方差越小分數越高
            dispersion_score = max(0.0, 1.0 - (variance / (mean_interval ** 2)))
        else:
            dispersion_score = 0.0
        
        return dispersion_score
    
    def _estimate_signal_quality(self, candidate: SatelliteCandidate) -> float:
        """估算信號品質評分"""
        
        if not candidate.windows:
            return 0.0
        
        # 基於峰值仰角估算信號品質
        peak_elevations = [w.peak_elevation for w in candidate.windows]
        avg_peak_elevation = sum(peak_elevations) / len(peak_elevations)
        
        # 仰角越高，信號品質越好
        # 5度=0.0, 90度=1.0
        signal_score = min(1.0, max(0.0, (avg_peak_elevation - 5.0) / 85.0))
        
        return signal_score
    
    def _calculate_orbit_diversity_score(self, candidate: SatelliteCandidate) -> float:
        """計算軌道多樣性評分"""
        
        # 基於NORAD ID的簡單多樣性估算
        # 實際實現中可以考慮軌道傾角、RAAN等參數
        diversity_factor = (candidate.norad_id % 100) / 100.0
        return diversity_factor
    
    def _check_temporal_conflicts(self, candidate: SatelliteCandidate, 
                                time_slots: List[List[str]], 
                                max_concurrent: int) -> bool:
        """檢查時空衝突"""
        
        # 檢查候選衛星的可見窗口是否會導致超過最大並發數
        for window in candidate.windows:
            for minute in range(window.start_minute, window.end_minute + 1):
                if minute < len(time_slots):
                    if len(time_slots[minute]) >= max_concurrent:
                        return True  # 有衝突
        
        return False  # 無衝突
    
    def _add_to_time_slots(self, candidate: SatelliteCandidate, 
                         time_slots: List[List[str]]) -> None:
        """將衛星添加到時間槽"""
        
        for window in candidate.windows:
            for minute in range(window.start_minute, window.end_minute + 1):
                if minute < len(time_slots):
                    time_slots[minute].append(candidate.satellite_id)
    
    def _check_coverage_adequate(self, time_slots: List[List[str]], 
                               target: DynamicCoverageTarget) -> bool:
        """檢查覆蓋是否足夠"""
        
        # 計算滿足最小可見數量要求的時間比例
        min_visible = target.target_visible_range[0]
        adequate_slots = sum(1 for slot in time_slots if len(slot) >= min_visible)
        coverage_ratio = adequate_slots / len(time_slots)
        
        # 要求95%的時間滿足最小可見數量
        return coverage_ratio >= 0.95
    
    async def _verify_dynamic_coverage(self, starlink_pool: List[SatelliteCandidate], 
                                     oneweb_pool: List[SatelliteCandidate]) -> Dict[str, Dict[str, Any]]:
        """驗證整個軌道週期的動態覆蓋品質"""
        
        self.logger.info("✅ 開始動態覆蓋驗證...")
        
        verification_results = {}
        
        # Starlink 覆蓋驗證
        if starlink_pool:
            starlink_timeline = await self._simulate_coverage_timeline(
                starlink_pool, 
                self.coverage_targets['starlink']
            )
            
            verification_results['starlink'] = {
                'pool_size': len(starlink_pool),
                'coverage_timeline': starlink_timeline,
                'target_met_ratio': sum(1 for t in starlink_timeline if t['meets_target']) / max(len(starlink_timeline), 1),
                'avg_visible': sum(t['visible_count'] for t in starlink_timeline) / max(len(starlink_timeline), 1),
                'coverage_gaps': [t for t in starlink_timeline if not t['meets_target']]
            }
        else:
            verification_results['starlink'] = {
                'pool_size': 0,
                'coverage_timeline': [],
                'target_met_ratio': 0.0,
                'avg_visible': 0.0,
                'coverage_gaps': []
            }
        
        # OneWeb 覆蓋驗證  
        if oneweb_pool:
            oneweb_timeline = await self._simulate_coverage_timeline(
                oneweb_pool, 
                self.coverage_targets['oneweb']
            )
            
            verification_results['oneweb'] = {
                'pool_size': len(oneweb_pool),
                'coverage_timeline': oneweb_timeline,
                'target_met_ratio': sum(1 for t in oneweb_timeline if t['meets_target']) / max(len(oneweb_timeline), 1),
                'avg_visible': sum(t['visible_count'] for t in oneweb_timeline) / max(len(oneweb_timeline), 1),
                'coverage_gaps': [t for t in oneweb_timeline if not t['meets_target']]
            }
        else:
            verification_results['oneweb'] = {
                'pool_size': 0,
                'coverage_timeline': [],
                'target_met_ratio': 0.0,
                'avg_visible': 0.0,
                'coverage_gaps': []
            }
        
        # 記錄驗證結果
        self.logger.info(f"📊 Starlink覆蓋驗證: {verification_results['starlink']['target_met_ratio']:.1%} 時間達標")
        self.logger.info(f"📊 OneWeb覆蓋驗證: {verification_results['oneweb']['target_met_ratio']:.1%} 時間達標")
        
        return verification_results
    
    async def _simulate_coverage_timeline(self, pool: List[SatelliteCandidate], 
                                        target: DynamicCoverageTarget) -> List[Dict[str, Any]]:
        """模擬整個軌道週期的覆蓋時間軸"""
        
        timeline = []
        
        # 創建時間槽網格
        time_slots = [[] for _ in range(target.orbit_period_minutes)]
        
        # 填入所有選中衛星的可見窗口
        for candidate in pool:
            for window in candidate.windows:
                for minute in range(window.start_minute, window.end_minute + 1):
                    if minute < len(time_slots):
                        time_slots[minute].append({
                            'satellite_id': candidate.satellite_id,
                            'elevation': self._interpolate_elevation(window, minute)
                        })
        
        # 分析每分鐘的覆蓋狀況
        for minute, satellites in enumerate(time_slots):
            visible_count = len(satellites)
            min_target, max_target = target.target_visible_range
            
            meets_target = min_target <= visible_count <= max_target
            
            timeline_point = {
                'minute': minute,
                'visible_count': visible_count,
                'meets_target': meets_target,
                'satellites': satellites,
                'coverage_quality': self._assess_coverage_quality(satellites, target)
            }
            
            timeline.append(timeline_point)
        
        return timeline
    
    def _interpolate_elevation(self, window: VisibilityWindow, minute: int) -> float:
        """線性插值計算指定分鐘的仰角"""
        
        if minute < window.start_minute or minute > window.end_minute:
            return 0.0
        
        if minute == window.peak_minute:
            return window.peak_elevation
        
        # 簡化的線性插值
        # 實際實現可以使用更精確的軌道計算
        if minute <= window.peak_minute:
            # 上升階段
            progress = (minute - window.start_minute) / max(1, window.peak_minute - window.start_minute)
            return window.peak_elevation * progress
        else:
            # 下降階段
            progress = (window.end_minute - minute) / max(1, window.end_minute - window.peak_minute)
            return window.peak_elevation * progress
    
    def _assess_coverage_quality(self, satellites: List[Dict[str, Any]], 
                               target: DynamicCoverageTarget) -> str:
        """評估覆蓋品質等級"""
        
        count = len(satellites)
        min_target, max_target = target.target_visible_range
        
        if count < min_target:
            return "insufficient"
        elif count <= max_target:
            return "optimal"
        else:
            return "oversaturated"
    
    async def _save_pool_results(self, results: Dict[str, Any]) -> None:
        """保存動態池規劃結果到Volume"""
        
        # 適應開發/生產環境路徑
        base_path = Path("/app/data") if Path("/app/data").exists() else Path("/tmp/satellite_data")
        output_dir = base_path / "dynamic_satellite_pools"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "pools.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 動態池結果已保存: {output_file}")


# 便利函數
def create_stage6_planner(config: Optional[Dict[str, Any]] = None) -> Stage6DynamicPoolPlanner:
    """創建階段六動態池規劃器"""
    default_config = {
        "observer_location": {
            "latitude": 24.9441667,
            "longitude": 121.3713889,
            "name": "NTPU"
        },
        "analysis_settings": {
            "time_resolution_seconds": 30,
            "orbit_analysis_cycles": 2,
            "min_pool_coverage_ratio": 0.95
        }
    }
    
    if config:
        default_config.update(config)
    
    return Stage6DynamicPoolPlanner(default_config)


# CLI 測試入口
async def main():
    """測試用主程式"""
    import logging
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    planner = create_stage6_planner()
    
    try:
        # 模擬數據測試
        mock_data = {"starlink": [], "oneweb": []}
        results = await planner.plan_dynamic_pools(mock_data)
        
        print("🎯 動態池規劃測試完成")
        print(f"Starlink池大小: {results['starlink']['actual_pool_size']}")
        print(f"OneWeb池大小: {results['oneweb']['actual_pool_size']}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")


if __name__ == "__main__":
    asyncio.run(main())