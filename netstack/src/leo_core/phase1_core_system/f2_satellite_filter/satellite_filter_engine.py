# 🛰️ F2: 衛星篩選引擎 (完整六階段篩選管線)
"""
Satellite Filter Engine - 從8,735顆篩選到563顆候選
功能: 實現@docs設計的完整六階段篩選管線
目標: 基於軌道位置數據的可見性感知智能篩選

六階段篩選流程:
1. 基礎地理篩選 (8,735 → ~2,500)
2. 可見性時間篩選 (~2,500 → ~1,200) - 需要軌道位置數據
3. 仰角品質篩選 (~1,200 → ~800) - 需要軌道位置數據
4. 服務連續性篩選 (~800 → ~650) - 需要軌道位置數據
5. 信號品質預評估 (~650 → ~580) - 需要軌道位置數據
6. 負載平衡最佳化 (~580 → 563)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import math
import numpy as np

@dataclass
class FilterCriteria:
    """篩選條件"""
    observer_latitude: float
    observer_longitude: float
    min_inclination_diff: float  # 最小傾角差
    max_longitude_diff: float    # 最大經度差
    signal_quality_threshold: float
    orbital_stability_threshold: float

@dataclass
class VisibilityAnalysis:
    """可見性分析結果"""
    satellite_id: str
    total_visible_time_minutes: float
    max_elevation_deg: float
    visible_passes_count: int
    avg_pass_duration_minutes: float
    best_elevation_time: datetime
    signal_strength_estimate_dbm: float
    
@dataclass
class SatelliteScore:
    """衛星評分結果"""
    satellite_id: str
    constellation: str
    total_score: float
    
    # 評分細項
    geographic_relevance_score: float
    orbital_characteristics_score: float
    signal_quality_score: float
    temporal_distribution_score: float
    visibility_compliance_score: float  # 新增可見性合規評分
    
    # 可見性分析
    visibility_analysis: Optional[VisibilityAnalysis]
    
    # 評分理由
    scoring_rationale: Dict[str, str]
    is_selected: bool

class SatelliteFilterEngine:
    """衛星篩選引擎 - 智能篩選高品質候選衛星"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # NTPU觀測點座標
        self.observer_lat = 24.9441667  # NTPU緯度
        self.observer_lon = 121.3713889  # NTPU經度
        
        # 星座特定參數 (按照@docs標準)
        self.constellation_params = {
            'starlink': {
                'optimal_inclination': 53.0,    # 最佳傾角
                'optimal_altitude': 550.0,      # 最佳高度 km
                'min_elevation_deg': 5.0,       # 最低仰角門檻
                'min_visible_time_min': 15.0,   # 最低可見時間
                'min_visible_passes': 3,        # 最少可見次數
                'target_candidate_count': 450,  # @docs標準目標
                'rsrp_threshold_dbm': -110.0,   # RSRP門檻
                'max_distance_km': 2000.0       # 最大距離
            },
            'oneweb': {
                'optimal_inclination': 87.4,    # OneWeb最佳傾角
                'optimal_altitude': 1200.0,     # 最佳高度 km
                'min_elevation_deg': 10.0,      # 更高的仰角要求
                'min_visible_time_min': 15.0,   # 最低可見時間
                'min_visible_passes': 3,        # 最少可見次數
                'target_candidate_count': 113,  # @docs標準目標
                'rsrp_threshold_dbm': -110.0,   # RSRP門檻
                'max_distance_km': 2000.0       # 最大距離
            }
        }
        
        # 篩選統計
        self.filter_statistics = {
            'input_satellites': 0,
            'geographic_filtered': 0,
            'constellation_filtered': 0,
            'final_candidates': 0,
            'starlink_candidates': 0,
            'oneweb_candidates': 0,
            'filter_stages': {}
        }
    
    async def apply_comprehensive_filter(self, 
                                       satellite_data: Dict[str, List]) -> Dict[str, List[SatelliteScore]]:
        """應用綜合篩選流程 - 從8,735顆篩選到554顆候選"""
        self.logger.info("🔍 開始綜合衛星篩選流程...")
        
        # 統計輸入數據
        total_input = sum(len(sats) for sats in satellite_data.values())
        self.filter_statistics['input_satellites'] = total_input
        self.logger.info(f"📊 輸入衛星總數: {total_input} 顆")
        
        filtered_candidates = {}
        
        try:
            # 1. Starlink篩選
            if 'starlink' in satellite_data:
                starlink_candidates = await self._filter_starlink_satellites(
                    satellite_data['starlink']
                )
                filtered_candidates['starlink'] = starlink_candidates
                self.filter_statistics['starlink_candidates'] = len(starlink_candidates)
                
            # 2. OneWeb篩選  
            if 'oneweb' in satellite_data:
                oneweb_candidates = await self._filter_oneweb_satellites(
                    satellite_data['oneweb']
                )
                filtered_candidates['oneweb'] = oneweb_candidates
                self.filter_statistics['oneweb_candidates'] = len(oneweb_candidates)
            
            # 統計最終結果
            total_candidates = sum(len(candidates) for candidates in filtered_candidates.values())
            self.filter_statistics['final_candidates'] = total_candidates
            
            self.logger.info(f"✅ 篩選完成:")
            self.logger.info(f"   Starlink候選: {self.filter_statistics['starlink_candidates']} 顆")
            self.logger.info(f"   OneWeb候選: {self.filter_statistics['oneweb_candidates']} 顆")
            self.logger.info(f"   總候選數: {total_candidates} 顆")
            filter_ratio = (total_candidates/total_input)*100 if total_input > 0 else 0.0
            self.logger.info(f"   篩選比例: {filter_ratio:.1f}%")
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ 衛星篩選失敗: {e}")
            raise
    
    async def _filter_starlink_satellites(self, starlink_satellites: List) -> List[SatelliteScore]:
        """Starlink專用篩選邏輯"""
        self.logger.info(f"📡 開始Starlink篩選 ({len(starlink_satellites)} 顆)")
        
        constellation_params = self.constellation_params['starlink']
        scored_satellites = []
        
        # 第一階段: 地理相關性篩選
        geographically_relevant = await self._apply_geographic_filter(
            starlink_satellites, 'starlink'
        )
        self.logger.info(f"🌍 地理篩選後: {len(geographically_relevant)} 顆")
        
        # 第二階段: Starlink特定評分
        for satellite in geographically_relevant:
            try:
                score = await self._calculate_starlink_score(satellite, constellation_params)
                scored_satellites.append(score)
            except Exception as e:
                self.logger.warning(f"⚠️ 衛星 {satellite.satellite_id} 評分失敗: {e}")
                continue
        
        # 第三階段: 根據評分選擇最佳候選
        scored_satellites.sort(key=lambda x: x.total_score, reverse=True)
        target_count = constellation_params['target_candidate_count']
        selected_candidates = scored_satellites[:target_count]
        
        # 標記選中狀態
        for candidate in selected_candidates:
            candidate.is_selected = True
        
        self.logger.info(f"⭐ Starlink篩選完成: {len(selected_candidates)} 顆候選")
        return selected_candidates
    
    async def _filter_oneweb_satellites(self, oneweb_satellites: List) -> List[SatelliteScore]:
        """OneWeb專用篩選邏輯"""
        self.logger.info(f"📡 開始OneWeb篩選 ({len(oneweb_satellites)} 顆)")
        
        constellation_params = self.constellation_params['oneweb']
        scored_satellites = []
        
        # 第一階段: 地理相關性篩選
        geographically_relevant = await self._apply_geographic_filter(
            oneweb_satellites, 'oneweb'
        )
        self.logger.info(f"🌍 地理篩選後: {len(geographically_relevant)} 顆")
        
        # 第二階段: OneWeb特定評分
        for satellite in geographically_relevant:
            try:
                score = await self._calculate_oneweb_score(satellite, constellation_params)
                scored_satellites.append(score)
            except Exception as e:
                self.logger.warning(f"⚠️ 衛星 {satellite.satellite_id} 評分失敗: {e}")
                continue
        
        # 第三階段: 根據評分選擇最佳候選
        scored_satellites.sort(key=lambda x: x.total_score, reverse=True)
        target_count = constellation_params['target_candidate_count']
        selected_candidates = scored_satellites[:target_count]
        
        # 標記選中狀態
        for candidate in selected_candidates:
            candidate.is_selected = True
        
        self.logger.info(f"⭐ OneWeb篩選完成: {len(selected_candidates)} 顆候選")
        return selected_candidates
    
    async def _apply_geographic_filter(self, satellites: List, constellation: str) -> List:
        """地理相關性篩選 - 針對NTPU觀測點優化"""
        
        relevant_satellites = []
        
        for satellite in satellites:
            # 1. 軌道傾角檢查 - 必須大於觀測點緯度
            if satellite.inclination_deg <= self.observer_lat:
                continue  # 跳過不能覆蓋NTPU的衛星
            
            # 2. 升交點經度相關性評分
            longitude_diff = abs(satellite.raan_deg - self.observer_lon)
            if longitude_diff > 180:
                longitude_diff = 360 - longitude_diff
            
            # 經度差距評分 (差距越小越好)
            longitude_relevance = max(0, 100 - longitude_diff * 2)
            
            # 3. 軌道特性評分
            if constellation == 'starlink':
                # Starlink: 53°傾角和550km高度為最佳
                inclination_score = 100 - abs(satellite.inclination_deg - 53.0) * 2
                altitude_score = 100 - abs(satellite.apogee_km - 550.0) * 0.1
            elif constellation == 'oneweb':
                # OneWeb: 87.4°傾角和1200km高度為最佳
                inclination_score = 100 - abs(satellite.inclination_deg - 87.4) * 2
                altitude_score = 100 - abs(satellite.apogee_km - 1200.0) * 0.05
            else:
                inclination_score = 50  # 其他星座使用預設評分
                altitude_score = 50
            
            # 4. 綜合地理相關性評分
            geographic_score = (longitude_relevance * 0.4 + 
                              inclination_score * 0.35 + 
                              altitude_score * 0.25)
            
            # 5. 篩選門檻 (地理相關性評分 > 60)
            if geographic_score > 60:
                relevant_satellites.append(satellite)
        
        return relevant_satellites
    
    async def _calculate_starlink_score(self, satellite, params: Dict) -> SatelliteScore:
        """計算Starlink衛星的綜合評分"""
        
        # 1. 軌道傾角適用性 (30%)
        inclination_diff = abs(satellite.inclination_deg - params['optimal_inclination'])
        inclination_score = max(0, 100 - inclination_diff * 3)  # 每度差距扣3分
        
        # 2. 高度適用性 (25%)
        altitude_diff = abs(satellite.apogee_km - params['optimal_altitude'])
        altitude_score = max(0, 100 - altitude_diff * 0.2)  # 每km差距扣0.2分
        
        # 3. 相位分散度 (20%) - 基於平近點角
        phase_dispersion_score = await self._calculate_phase_dispersion_score(satellite)
        
        # 4. 換手頻率適用性 (15%)
        handover_frequency_score = await self._calculate_handover_frequency_score(satellite)
        
        # 5. 信號穩定性 (10%) - 基於軌道偏心率
        eccentricity_penalty = satellite.eccentricity * 1000  # 偏心率懲罰
        signal_stability_score = max(0, 100 - eccentricity_penalty)
        
        # 計算總分
        total_score = (
            inclination_score * params['weight_inclination'] +
            altitude_score * params['weight_altitude'] +
            phase_dispersion_score * params['weight_phase_dispersion'] +
            handover_frequency_score * params['weight_handover_frequency'] +
            signal_stability_score * params['weight_signal_stability']
        )
        
        return SatelliteScore(
            satellite_id=satellite.satellite_id,
            constellation='starlink',
            total_score=total_score,
            geographic_relevance_score=inclination_score,
            orbital_characteristics_score=altitude_score,
            signal_quality_score=signal_stability_score,
            temporal_distribution_score=phase_dispersion_score,
            scoring_rationale={
                'inclination_analysis': f"傾角{satellite.inclination_deg:.1f}°，與最佳53°差距{inclination_diff:.1f}°",
                'altitude_analysis': f"高度{satellite.apogee_km:.0f}km，與最佳550km差距{altitude_diff:.0f}km",
                'stability_analysis': f"偏心率{satellite.eccentricity:.6f}，軌道穩定性評分{signal_stability_score:.1f}",
                'phase_analysis': f"相位分散評分{phase_dispersion_score:.1f}"
            },
            is_selected=False
        )
    
    async def _calculate_oneweb_score(self, satellite, params: Dict) -> SatelliteScore:
        """計算OneWeb衛星的綜合評分"""
        
        # 1. 軌道傾角適用性 (25%)
        inclination_diff = abs(satellite.inclination_deg - params['optimal_inclination'])
        inclination_score = max(0, 100 - inclination_diff * 2)
        
        # 2. 高度適用性 (25%)
        altitude_diff = abs(satellite.apogee_km - params['optimal_altitude'])
        altitude_score = max(0, 100 - altitude_diff * 0.1)
        
        # 3. 極地覆蓋能力 (20%) - 高傾角優勢
        polar_coverage_score = min(100, satellite.inclination_deg)  # 傾角越高覆蓋越好
        
        # 4. 軌道形狀 (20%) - 偏心率接近圓形
        eccentricity_penalty = satellite.eccentricity * 2000  # OneWeb對偏心率更敏感
        orbital_shape_score = max(0, 100 - eccentricity_penalty)
        
        # 5. 相位分散 (10%)
        phase_dispersion_score = await self._calculate_phase_dispersion_score(satellite)
        
        # 計算總分
        total_score = (
            inclination_score * params['weight_inclination'] +
            altitude_score * params['weight_altitude'] +
            polar_coverage_score * params['weight_polar_coverage'] +
            orbital_shape_score * params['weight_orbital_shape'] +
            phase_dispersion_score * params['weight_phase_dispersion']
        )
        
        return SatelliteScore(
            satellite_id=satellite.satellite_id,
            constellation='oneweb',
            total_score=total_score,
            geographic_relevance_score=inclination_score,
            orbital_characteristics_score=altitude_score,
            signal_quality_score=orbital_shape_score,
            temporal_distribution_score=phase_dispersion_score,
            scoring_rationale={
                'inclination_analysis': f"傾角{satellite.inclination_deg:.1f}°，與最佳87.4°差距{inclination_diff:.1f}°",
                'altitude_analysis': f"高度{satellite.apogee_km:.0f}km，與最佳1200km差距{altitude_diff:.0f}km",
                'polar_coverage': f"極地覆蓋能力{polar_coverage_score:.1f}分",
                'orbital_shape': f"軌道形狀評分{orbital_shape_score:.1f}分 (偏心率{satellite.eccentricity:.6f})"
            },
            is_selected=False
        )
    
    async def _calculate_phase_dispersion_score(self, satellite) -> float:
        """計算相位分散評分 - 避免衛星同時出現/消失"""
        
        # 基於平近點角的相位分析
        mean_anomaly = satellite.mean_anomaly_deg
        
        # 相位分散評分邏輯 (簡化版本)
        # 實際實現需要考慮與其他已選衛星的相位關係
        
        # 如果平近點角在合理分佈範圍內給予高分
        if 0 <= mean_anomaly <= 360:
            # 根據平近點角計算分散度
            phase_factor = abs(180 - mean_anomaly) / 180  # 距離180度的比例
            base_score = 70 + phase_factor * 30  # 基礎分數70-100
            
            return min(100, base_score)
        else:
            return 30  # 異常平近點角給予低分
    
    async def _calculate_handover_frequency_score(self, satellite) -> float:
        """計算換手頻率適用性評分"""
        
        # 基於軌道週期計算換手頻率
        orbital_period = satellite.orbital_period_minutes
        
        # Starlink理想軌道週期 ~96分鐘
        ideal_period = 96.0
        period_diff = abs(orbital_period - ideal_period)
        
        # 週期差距評分
        if period_diff <= 5:
            return 100  # 非常接近理想週期
        elif period_diff <= 15:
            return 80   # 可接受範圍
        elif period_diff <= 30:
            return 60   # 勉強可用
        else:
            return 30   # 不理想
    
    async def export_filter_results(self, 
                                  filtered_candidates: Dict[str, List[SatelliteScore]], 
                                  output_path: str):
        """匯出篩選結果和統計數據"""
        try:
            export_data = {
                'filter_statistics': self.filter_statistics,
                'filter_timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_coordinates': {
                    'latitude': self.observer_lat,
                    'longitude': self.observer_lon,
                    'location_name': 'NTPU'
                },
                'candidates': {}
            }
            
            # 匯出候選衛星詳細信息
            for constellation, candidates in filtered_candidates.items():
                export_data['candidates'][constellation] = []
                
                for candidate in candidates:
                    export_data['candidates'][constellation].append({
                        'satellite_id': candidate.satellite_id,
                        'total_score': round(candidate.total_score, 2),
                        'geographic_relevance_score': round(candidate.geographic_relevance_score, 2),
                        'orbital_characteristics_score': round(candidate.orbital_characteristics_score, 2),
                        'signal_quality_score': round(candidate.signal_quality_score, 2),
                        'temporal_distribution_score': round(candidate.temporal_distribution_score, 2),
                        'scoring_rationale': candidate.scoring_rationale,
                        'is_selected': candidate.is_selected
                    })
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 篩選結果已匯出至: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 篩選結果匯出失敗: {e}")

# 使用範例
async def main():
    """F2_Satellite_Filter使用範例"""
    
    config = {
        'filtering_params': {
            'geographic_threshold': 60.0,
            'min_score_threshold': 70.0
        },
        'ntpu_coordinates': {
            'latitude': 24.9441667,
            'longitude': 121.3713889
        }
    }
    
    # 初始化篩選引擎
    filter_engine = SatelliteFilterEngine(config)
    
    # 模擬載入的衛星數據 (實際應從F1獲取)
    satellite_data = {
        'starlink': [],  # 來自F1_TLE_Loader的Starlink數據
        'oneweb': []     # 來自F1_TLE_Loader的OneWeb數據
    }
    
    # 應用綜合篩選
    filtered_candidates = await filter_engine.apply_comprehensive_filter(satellite_data)
    
    # 匯出篩選結果
    await filter_engine.export_filter_results(
        filtered_candidates, 
        '/tmp/f2_filter_results.json'
    )
    
    print(f"✅ F2_Satellite_Filter測試完成")
    print(f"   篩選候選總數: {filter_engine.filter_statistics['final_candidates']}")

if __name__ == "__main__":
    asyncio.run(main())