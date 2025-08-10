#!/usr/bin/env python3
"""
Phase 2.5 智能衛星選擇器 - 重構版
從衛星池中智能選擇最佳配置

版本: v2.0.0
建立日期: 2025-08-10
重構目標: 移除重複配置，加強智能選擇
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from unified_satellite_config import (
    UnifiedSatelliteConfig,
    ConstellationConfig,
    SelectionStrategy,
    get_unified_config
)

logger = logging.getLogger(__name__)

# Numpy 替代方案 (保持與原版兼容)
try:
    import numpy as np
except ImportError:
    class NumpyMock:
        def std(self, data): 
            if not data or len(data) <= 1: return 0.0
            mean_val = sum(data) / len(data)
            variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
            return variance ** 0.5
        def mean(self, data): return sum(data) / len(data) if data else 0.0
        def min(self, data): return min(data) if data else 0.0
        def max(self, data): return max(data) if data else 0.0
        def linalg(self): 
            class LinAlg:
                def norm(self, vec): return sum(x**2 for x in vec)**0.5
            return LinAlg()
        def random(self):
            class Random:
                def normal(self, mean, std): 
                    # 確定性替代：使用基於平均值的小變化
                    return mean + std * 0.1  # 固定偏移，避免隨機性
            return Random()
    np = NumpyMock()
    np.linalg = np.linalg()  
    np.random = np.random()

@dataclass
class SatelliteMetrics:
    """衛星評估指標 - Phase 2.5 增強版"""
    satellite_id: str
    satellite_name: str
    constellation: str
    norad_id: int
    
    # 可見性指標
    visibility_score: float
    elevation_potential: float      # 仰角潛力
    coverage_duration: float        # 覆蓋持續時間
    
    # 軌道品質指標
    orbital_stability: float        # 軌道穩定性
    handover_suitability: float     # 換手適用性
    phase_diversity: float          # 相位多樣性
    
    # 3GPP NTN 事件潛力
    event_potential: Dict[str, float] = None  # A4, A5, D2 事件潛力
    
    def __post_init__(self):
        if self.event_potential is None:
            self.event_potential = {"A4": 0.0, "A5": 0.0, "D2": 0.0}
    
    def get_overall_score(self) -> float:
        """計算綜合評分"""
        weights = {
            "visibility": 0.25,
            "elevation": 0.20,
            "coverage": 0.15,
            "stability": 0.15,
            "handover": 0.15,
            "diversity": 0.10
        }
        
        score = (
            self.visibility_score * weights["visibility"] +
            self.elevation_potential * weights["elevation"] +
            self.coverage_duration * weights["coverage"] +
            self.orbital_stability * weights["stability"] +
            self.handover_suitability * weights["handover"] +
            self.phase_diversity * weights["diversity"]
        )
        
        return max(0.0, min(100.0, score))  # 限制在 0-100 範圍

@dataclass
class SelectionResult:
    """選擇結果"""
    selected_satellites: List[Dict[str, Any]]
    metrics: List[SatelliteMetrics]
    selection_summary: Dict[str, Any]
    
    def get_constellation_count(self, constellation: str) -> int:
        """獲取指定星座的選中衛星數量"""
        return len([s for s in self.selected_satellites 
                   if s.get('constellation', '').lower() == constellation.lower()])

class IntelligentSatelliteSelector:
    """運行階段：從衛星池中智能選擇最終配置
    
    Phase 2.5 重構改進：
    1. 移除內建 SatelliteSelectionConfig (使用統一配置)
    2. 加強智能選擇算法
    3. 支援多種選擇策略
    4. 集中所有智能篩選邏輯
    """
    
    def __init__(self, config: Optional[UnifiedSatelliteConfig] = None):
        """
        初始化智能選擇器
        
        Args:
            config: 統一配置實例，None 時使用默認配置
        """
        self.config = config or get_unified_config()
        
        # 驗證配置
        validation_result = self.config.validate()
        if not validation_result.is_valid:
            raise ValueError(f"配置驗證失敗: {validation_result.errors}")
        
        # 3GPP NTN 事件觸發條件 - 基於真實標準
        self.event_thresholds = {
            'A4': {'rsrp': -95, 'hysteresis': 3},       # dBm, dB
            'A5': {'thresh1': -100, 'thresh2': -95},    # dBm  
            'D2': {'low_elev': 10, 'high_elev': 30}     # 度
        }
        
        logger.info(f"🚀 Phase 2.5 智能衛星選擇器啟動")
        logger.info(f"📡 配置版本: {self.config.version}")
        logger.info(f"🎯 選擇目標:")
        
        for name, constellation in self.config.constellations.items():
            logger.info(f"  {name}: {constellation.target_satellites} 顆 "
                       f"(從 {constellation.total_satellites} 顆池中選擇)")
    
    def select_optimal_satellites(self, satellite_pools: Dict[str, List[Dict[str, Any]]]) -> SelectionResult:
        """從衛星池中選擇最佳配置
        
        Args:
            satellite_pools: 各星座的衛星池 {constellation_name: [satellite_data]}
            
        Returns:
            SelectionResult: 選擇結果包含衛星、指標和統計
        """
        logger.info("🎯 開始智能衛星選擇...")
        
        selected_satellites = []
        all_metrics = []
        selection_summary = {
            "total_pools": len(satellite_pools),
            "total_pool_satellites": sum(len(pool) for pool in satellite_pools.values()),
            "total_selected": 0,
            "constellations": {}
        }
        
        # 逐一處理每個星座
        for constellation_name, satellite_pool in satellite_pools.items():
            constellation_config = self.config.get_constellation_config(constellation_name)
            
            if not constellation_config:
                logger.warning(f"未找到 {constellation_name} 配置，跳過")
                continue
            
            if not satellite_pool:
                logger.warning(f"{constellation_name} 衛星池為空，跳過")
                continue
            
            logger.info(f"處理 {constellation_name}: 從 {len(satellite_pool)} 顆中選擇 {constellation_config.target_satellites} 顆")
            
            # 智能選擇該星座的衛星
            constellation_result = self._intelligent_selection(
                satellite_pool,
                constellation_config.target_satellites,
                constellation_config.selection_strategy,
                constellation_name
            )
            
            if constellation_result:
                selected_satellites.extend(constellation_result["satellites"])
                all_metrics.extend(constellation_result["metrics"])
                
                selection_summary["constellations"][constellation_name] = {
                    "pool_size": len(satellite_pool),
                    "target_count": constellation_config.target_satellites,
                    "selected_count": len(constellation_result["satellites"]),
                    "selection_rate": len(constellation_result["satellites"]) / len(satellite_pool) * 100,
                    "avg_score": constellation_result["avg_score"],
                    "strategy": constellation_config.selection_strategy.value
                }
                
                logger.info(f"  ✅ {constellation_name}: 選擇 {len(constellation_result['satellites'])} 顆 "
                           f"(平均分數: {constellation_result['avg_score']:.1f})")
        
        selection_summary["total_selected"] = len(selected_satellites)
        
        # 創建結果
        result = SelectionResult(
            selected_satellites=selected_satellites,
            metrics=all_metrics,
            selection_summary=selection_summary
        )
        
        # 輸出統計
        logger.info(f"🎉 智能選擇完成:")
        logger.info(f"  總計選擇: {len(selected_satellites)} 顆衛星")
        for constellation, stats in selection_summary["constellations"].items():
            logger.info(f"  {constellation}: {stats['selected_count']} 顆 "
                       f"({stats['selection_rate']:.1f}% 選擇率)")
        
        return result
    
    def _intelligent_selection(self, satellite_pool: List[Dict[str, Any]], target_count: int, 
                              strategy: SelectionStrategy, constellation: str) -> Optional[Dict[str, Any]]:
        """智能選擇算法 - 集中所有智能篩選邏輯
        
        Args:
            satellite_pool: 衛星池
            target_count: 目標數量
            strategy: 選擇策略
            constellation: 星座名稱
            
        Returns:
            選擇結果字典或 None
        """
        if len(satellite_pool) <= target_count:
            # 衛星池不足，直接返回全部
            metrics = [self._evaluate_satellite(sat, constellation) for sat in satellite_pool]
            avg_score = np.mean([m.get_overall_score() for m in metrics]) if metrics else 0.0
            
            return {
                "satellites": satellite_pool[:],
                "metrics": metrics,
                "avg_score": avg_score
            }
        
        # 評估所有衛星
        logger.debug(f"  評估 {len(satellite_pool)} 顆衛星...")
        evaluated_satellites = []
        
        for satellite in satellite_pool:
            metrics = self._evaluate_satellite(satellite, constellation)
            evaluated_satellites.append((satellite, metrics))
        
        # 根據策略選擇
        if strategy == SelectionStrategy.DYNAMIC_OPTIMAL:
            selected = self._dynamic_optimal_selection(evaluated_satellites, target_count)
        elif strategy == SelectionStrategy.COVERAGE_OPTIMAL:
            selected = self._coverage_optimal_selection(evaluated_satellites, target_count)
        elif strategy == SelectionStrategy.DIVERSITY_BALANCED:
            selected = self._diversity_balanced_selection(evaluated_satellites, target_count)
        elif strategy == SelectionStrategy.HANDOVER_FOCUSED:
            selected = self._handover_focused_selection(evaluated_satellites, target_count)
        else:
            logger.warning(f"未知選擇策略 {strategy}，使用動態最優")
            selected = self._dynamic_optimal_selection(evaluated_satellites, target_count)
        
        if selected:
            satellites = [item[0] for item in selected]
            metrics = [item[1] for item in selected]
            avg_score = np.mean([m.get_overall_score() for m in metrics])
            
            return {
                "satellites": satellites,
                "metrics": metrics,
                "avg_score": avg_score
            }
        
        return None
    
    def _evaluate_satellite(self, satellite: Dict[str, Any], constellation: str) -> SatelliteMetrics:
        """評估單顆衛星的各項指標"""
        try:
            # 基本信息
            satellite_id = satellite.get('norad_id', 'unknown')
            satellite_name = satellite.get('name', 'unknown')
            norad_id = int(satellite.get('norad_id', 0))
            
            # 提取軌道參數
            line1 = satellite.get('line1', '')
            line2 = satellite.get('line2', '')
            orbital_params = self._extract_orbital_parameters(line1, line2)
            
            # 計算各項指標
            visibility_score = self._calculate_visibility_score(orbital_params, constellation)
            elevation_potential = self._calculate_elevation_potential(orbital_params, constellation)
            coverage_duration = self._calculate_coverage_duration(orbital_params, constellation)
            orbital_stability = self._calculate_orbital_stability(orbital_params)
            handover_suitability = self._calculate_handover_suitability(orbital_params, constellation)
            phase_diversity = self._calculate_phase_diversity(orbital_params, constellation)
            
            # 計算事件潛力
            event_potential = self._calculate_event_potential(orbital_params, constellation)
            
            metrics = SatelliteMetrics(
                satellite_id=str(satellite_id),
                satellite_name=satellite_name,
                constellation=constellation,
                norad_id=norad_id,
                visibility_score=visibility_score,
                elevation_potential=elevation_potential,
                coverage_duration=coverage_duration,
                orbital_stability=orbital_stability,
                handover_suitability=handover_suitability,
                phase_diversity=phase_diversity,
                event_potential=event_potential
            )
            
            return metrics
            
        except Exception as e:
            logger.debug(f"評估衛星失敗 {satellite.get('name', 'unknown')}: {e}")
            # 返回最低分數的指標
            return SatelliteMetrics(
                satellite_id=str(satellite.get('norad_id', 'error')),
                satellite_name=satellite.get('name', 'error'),
                constellation=constellation,
                norad_id=int(satellite.get('norad_id', 0)),
                visibility_score=0.0,
                elevation_potential=0.0,
                coverage_duration=0.0,
                orbital_stability=0.0,
                handover_suitability=0.0,
                phase_diversity=0.0
            )
    
    def _extract_orbital_parameters(self, line1: str, line2: str) -> Dict[str, float]:
        """從 TLE 數據提取軌道參數"""
        params = {}
        
        try:
            if len(line2) >= 69:
                params['inclination'] = float(line2[8:16].strip())      # 軌道傾角
                params['raan'] = float(line2[17:25].strip())            # 升交點赤經
                params['eccentricity'] = float(f"0.{line2[26:33].strip()}")  # 偏心率
                params['arg_perigee'] = float(line2[34:42].strip())     # 近地點幅角
                params['mean_anomaly'] = float(line2[43:51].strip())    # 平近點角
                params['mean_motion'] = float(line2[52:63].strip())     # 平均運動
            
            if len(line1) >= 69:
                # 提取 epoch (紀元時間)
                epoch_str = line1[18:32].strip()
                if epoch_str:
                    params['epoch'] = float(epoch_str)
        
        except (ValueError, IndexError):
            # 設置默認值
            params = {
                'inclination': 0.0,
                'raan': 0.0,
                'eccentricity': 0.0,
                'arg_perigee': 0.0,
                'mean_anomaly': 0.0,
                'mean_motion': 15.0,
                'epoch': 0.0
            }
        
        return params
    
    def _calculate_visibility_score(self, orbital_params: Dict[str, float], constellation: str) -> float:
        """計算可見性分數"""
        inclination = orbital_params.get('inclination', 0.0)
        mean_motion = orbital_params.get('mean_motion', 15.0)
        
        # 觀測點緯度覆蓋檢查
        observer_lat = abs(self.config.observer.latitude)
        
        if inclination < observer_lat:
            return 0.0  # 無法覆蓋觀測點
        
        # 基於軌道傾角的可見性評分
        coverage_score = min(100.0, (inclination - observer_lat) / (90.0 - observer_lat) * 100)
        
        # 基於軌道高度的可見性調整
        if constellation.lower() == 'starlink':
            # Starlink 較低軌道，更頻繁通過
            if 14.5 <= mean_motion <= 16.0:  # 550-600km 高度範圍
                altitude_bonus = 20.0
            else:
                altitude_bonus = 0.0
        elif constellation.lower() == 'oneweb':
            # OneWeb 較高軌道，覆蓋更穩定
            if 12.5 <= mean_motion <= 14.5:  # 1200km 高度範圍  
                altitude_bonus = 15.0
            else:
                altitude_bonus = 0.0
        else:
            altitude_bonus = 0.0
        
        return min(100.0, coverage_score + altitude_bonus)
    
    def _calculate_elevation_potential(self, orbital_params: Dict[str, float], constellation: str) -> float:
        """計算仰角潛力"""
        inclination = orbital_params.get('inclination', 0.0)
        mean_motion = orbital_params.get('mean_motion', 15.0)
        
        # 基於軌道傾角和高度的仰角潛力估算
        observer_lat = abs(self.config.observer.latitude)
        
        if inclination <= observer_lat:
            return 0.0
        
        # 高傾角軌道具有更高的仰角潛力
        inclination_factor = min(1.0, inclination / 90.0)
        
        # 低軌道衛星能達到更高仰角
        altitude_factor = max(0.0, (16.0 - mean_motion) / 4.0)  # 高頻運動 = 低高度
        
        elevation_score = (inclination_factor * 70 + altitude_factor * 30)
        
        return min(100.0, max(0.0, elevation_score))
    
    def _calculate_coverage_duration(self, orbital_params: Dict[str, float], constellation: str) -> float:
        """計算覆蓋持續時間潛力"""
        mean_motion = orbital_params.get('mean_motion', 15.0)
        inclination = orbital_params.get('inclination', 0.0)
        
        # 軌道週期 (分鐘)
        orbital_period = 24 * 60 / mean_motion
        
        # 基於軌道週期的覆蓋時間評分
        if constellation.lower() == 'starlink':
            # Starlink 96分鐘週期，覆蓋時間約 8-12 分鐘
            optimal_period = 96.0
            period_score = max(0, 100 - abs(orbital_period - optimal_period) * 2)
        elif constellation.lower() == 'oneweb':
            # OneWeb 109分鐘週期，覆蓋時間約 10-15 分鐘
            optimal_period = 109.0
            period_score = max(0, 100 - abs(orbital_period - optimal_period) * 2)
        else:
            period_score = 50.0  # 默認分數
        
        # 軌道傾角對覆蓋持續時間的影響
        inclination_bonus = min(20.0, inclination / 90.0 * 20)
        
        return min(100.0, period_score + inclination_bonus)
    
    def _calculate_orbital_stability(self, orbital_params: Dict[str, float]) -> float:
        """計算軌道穩定性"""
        eccentricity = orbital_params.get('eccentricity', 0.0)
        mean_motion = orbital_params.get('mean_motion', 15.0)
        
        # 低偏心率表示穩定的圓軌道
        eccentricity_score = max(0, 100 - eccentricity * 1000)  # 偏心率通常 < 0.01
        
        # 合理的平均運動範圍 (LEO 衛星)
        if 12.0 <= mean_motion <= 16.5:
            motion_score = 100.0
        else:
            motion_score = max(0, 100 - abs(mean_motion - 14.0) * 10)
        
        stability_score = (eccentricity_score * 0.6 + motion_score * 0.4)
        
        return min(100.0, max(0.0, stability_score))
    
    def _calculate_handover_suitability(self, orbital_params: Dict[str, float], constellation: str) -> float:
        """計算換手適用性"""
        inclination = orbital_params.get('inclination', 0.0)
        mean_motion = orbital_params.get('mean_motion', 15.0)
        raan = orbital_params.get('raan', 0.0)
        
        constellation_config = self.config.get_constellation_config(constellation)
        if not constellation_config:
            return 50.0
        
        min_elevation = constellation_config.min_elevation
        
        # 基於最小仰角門檻的適用性
        if min_elevation <= 10.0:
            elevation_suitability = 100.0
        else:
            elevation_suitability = max(0, 100 - (min_elevation - 10.0) * 5)
        
        # 軌道分布多樣性 (RAAN 分散)
        raan_diversity = abs(math.sin(math.radians(raan))) * 30 + 70  # 70-100 分數範圍
        
        handover_score = (elevation_suitability * 0.7 + raan_diversity * 0.3)
        
        return min(100.0, max(0.0, handover_score))
    
    def _calculate_phase_diversity(self, orbital_params: Dict[str, float], constellation: str) -> float:
        """計算相位多樣性"""
        mean_anomaly = orbital_params.get('mean_anomaly', 0.0)
        arg_perigee = orbital_params.get('arg_perigee', 0.0)
        
        # 平近點角的分散性 (避免衛星同步出現)
        ma_diversity = abs(math.sin(math.radians(mean_anomaly))) * 50 + 50
        
        # 近地點幅角的分散性
        ap_diversity = abs(math.cos(math.radians(arg_perigee))) * 30 + 70
        
        diversity_score = (ma_diversity * 0.6 + ap_diversity * 0.4)
        
        return min(100.0, max(0.0, diversity_score))
    
    def _calculate_event_potential(self, orbital_params: Dict[str, float], constellation: str) -> Dict[str, float]:
        """計算 3GPP NTN 事件潛力"""
        inclination = orbital_params.get('inclination', 0.0)
        mean_motion = orbital_params.get('mean_motion', 15.0)
        
        # A4 事件潛力 (RSRP based)
        a4_potential = min(100.0, inclination / 90.0 * 80 + 20)
        
        # A5 事件潛力 (threshold based)  
        a5_potential = min(100.0, (16.0 - mean_motion) / 4.0 * 60 + 40)
        
        # D2 事件潛力 (elevation based)
        d2_potential = min(100.0, inclination / 90.0 * 90 + 10)
        
        return {
            "A4": max(0.0, a4_potential),
            "A5": max(0.0, a5_potential),
            "D2": max(0.0, d2_potential)
        }
    
    def _dynamic_optimal_selection(self, evaluated_satellites: List[Tuple], target_count: int) -> List[Tuple]:
        """動態最優選擇策略 (適用於 Starlink)"""
        logger.debug("  使用動態最優選擇策略")
        
        # 按綜合分數排序
        sorted_satellites = sorted(evaluated_satellites, 
                                 key=lambda x: x[1].get_overall_score(), 
                                 reverse=True)
        
        # 選擇前 N 個高分衛星，但保持軌道平面多樣性
        selected = []
        used_raan_ranges = set()
        
        for satellite, metrics in sorted_satellites:
            if len(selected) >= target_count:
                break
            
            # 檢查軌道平面多樣性
            try:
                line2 = satellite.get('line2', '')
                if len(line2) >= 25:
                    raan = float(line2[17:25].strip())
                    raan_range = int(raan // 30) * 30  # 30度分組
                    
                    # 如果這個軌道平面組已經有太多衛星，跳過
                    if raan_range in used_raan_ranges and len([r for r in used_raan_ranges if r == raan_range]) >= 3:
                        continue
                    
                    used_raan_ranges.add(raan_range)
            except (ValueError, IndexError):
                pass
            
            selected.append((satellite, metrics))
        
        # 如果還需要更多衛星，從剩餘中選擇最高分的
        if len(selected) < target_count:
            remaining = [item for item in sorted_satellites if item not in selected]
            needed = target_count - len(selected)
            selected.extend(remaining[:needed])
        
        logger.debug(f"    動態最優選擇: {len(selected)} 顆衛星")
        return selected
    
    def _coverage_optimal_selection(self, evaluated_satellites: List[Tuple], target_count: int) -> List[Tuple]:
        """覆蓋最優選擇策略 (適用於 OneWeb)"""
        logger.debug("  使用覆蓋最優選擇策略")
        
        # 優先選擇覆蓋時間和可見性分數高的衛星
        def coverage_score_func(item):
            satellite, metrics = item
            return (metrics.coverage_duration * 0.4 + 
                   metrics.visibility_score * 0.4 +
                   metrics.elevation_potential * 0.2)
        
        sorted_satellites = sorted(evaluated_satellites, key=coverage_score_func, reverse=True)
        selected = sorted_satellites[:target_count]
        
        logger.debug(f"    覆蓋最優選擇: {len(selected)} 顆衛星")
        return selected
    
    def _diversity_balanced_selection(self, evaluated_satellites: List[Tuple], target_count: int) -> List[Tuple]:
        """多樣性平衡選擇策略"""
        logger.debug("  使用多樣性平衡選擇策略")
        
        # 平衡各項指標的選擇
        def balanced_score_func(item):
            satellite, metrics = item
            return (metrics.get_overall_score() * 0.6 + metrics.phase_diversity * 0.4)
        
        sorted_satellites = sorted(evaluated_satellites, key=balanced_score_func, reverse=True)
        selected = sorted_satellites[:target_count]
        
        logger.debug(f"    多樣性平衡選擇: {len(selected)} 顆衛星")
        return selected
    
    def _handover_focused_selection(self, evaluated_satellites: List[Tuple], target_count: int) -> List[Tuple]:
        """換手專注選擇策略"""
        logger.debug("  使用換手專注選擇策略")
        
        # 優先選擇換手適用性高的衛星
        def handover_score_func(item):
            satellite, metrics = item
            return (metrics.handover_suitability * 0.5 + 
                   metrics.elevation_potential * 0.3 +
                   sum(metrics.event_potential.values()) / 3 * 0.2)
        
        sorted_satellites = sorted(evaluated_satellites, key=handover_score_func, reverse=True)
        selected = sorted_satellites[:target_count]
        
        logger.debug(f"    換手專注選擇: {len(selected)} 顆衛星")
        return selected


def create_intelligent_satellite_selector(config: Optional[UnifiedSatelliteConfig] = None) -> IntelligentSatelliteSelector:
    """創建智能衛星選擇器的便利函數"""
    return IntelligentSatelliteSelector(config)


if __name__ == "__main__":
    """智能選擇器測試腳本"""
    import json
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Phase 2.5 智能衛星選擇器測試")
    print("=" * 60)
    
    # 創建智能選擇器
    selector = create_intelligent_satellite_selector()
    
    # 模擬衛星池數據
    mock_pools = {
        "starlink": [
            {
                "name": f"STARLINK-{1000+i}",
                "norad_id": 50000 + i,
                "constellation": "starlink",
                "line1": f"1 {50000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                "line2": f"2 {50000+i:05d}  {53 + i%10}.{i%10:04d} {i*6%360:03d}.0000 000{i%9+1:d}000  {i*10%360:03d}.0000 {i*15%360:03d}.0000 15.{50+i%50:02d}000000    1{i%10}",
                "tle_date": "20250810"
            }
            for i in range(555)  # 模擬 555 顆 Starlink 衛星池
        ],
        "oneweb": [
            {
                "name": f"ONEWEB-{100+i:04d}",
                "norad_id": 60000 + i,
                "constellation": "oneweb", 
                "line1": f"1 {60000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                "line2": f"2 {60000+i:05d}  87.{4000+i%1000:04d} {i*6%360:03d}.0000 000{i%9+1:d}000  {i*10%360:03d}.0000 {i*15%360:03d}.0000 13.{20+i%30:02d}000000    1{i%10}",
                "tle_date": "20250810"
            }
            for i in range(134)  # 模擬 134 顆 OneWeb 衛星池
        ]
    }
    
    print(f"模擬衛星池:")
    for constellation, pool in mock_pools.items():
        print(f"  {constellation}: {len(pool)} 顆衛星")
    
    # 執行智能選擇
    print(f"\n執行智能選擇...")
    result = selector.select_optimal_satellites(mock_pools)
    
    # 輸出結果
    print(f"\n選擇結果:")
    print(f"  總計選擇: {len(result.selected_satellites)} 顆衛星")
    
    for constellation, stats in result.selection_summary["constellations"].items():
        print(f"\n  {constellation.upper()}:")
        print(f"    選擇數量: {stats['selected_count']} / {stats['target_count']} 顆")
        print(f"    選擇率: {stats['selection_rate']:.1f}%")
        print(f"    平均分數: {stats['avg_score']:.1f}")
        print(f"    選擇策略: {stats['strategy']}")
    
    # 顯示前5顆衛星的詳細指標
    print(f"\n前5顆衛星詳細指標:")
    for i, metrics in enumerate(result.metrics[:5]):
        print(f"  {i+1}. {metrics.satellite_name}")
        print(f"     星座: {metrics.constellation}")
        print(f"     綜合評分: {metrics.get_overall_score():.1f}")
        print(f"     可見性: {metrics.visibility_score:.1f}")
        print(f"     換手適用性: {metrics.handover_suitability:.1f}")
        print(f"     事件潛力: A4={metrics.event_potential['A4']:.1f}")
    
    print(f"\n" + "=" * 60)
    print("智能選擇器測試完成")
    print("=" * 60)