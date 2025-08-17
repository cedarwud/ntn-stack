# 🛰️ F2: 衛星篩選引擎 (完整六階段篩選管線 v2)
"""
Satellite Filter Engine v2 - 從8,735顆篩選到563顆候選
實現@docs設計的完整六階段篩選管線，基於軌道位置數據的可見性感知智能篩選

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
class VisibilityAnalysis:
    """可見性分析結果"""
    satellite_id: str
    total_visible_time_minutes: float
    max_elevation_deg: float
    visible_passes_count: int
    avg_pass_duration_minutes: float
    best_elevation_time: Optional[datetime]
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

class SatelliteFilterEngineV2:
    """衛星篩選引擎v2 - 完整六階段篩選管線"""
    
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
            'final_candidates': 0,
            'starlink_candidates': 0,
            'oneweb_candidates': 0,
            'filter_stages': {}
        }
    
    async def apply_comprehensive_filter(self, 
                                       orbital_data: Dict[str, List], 
                                       satellite_orbital_positions: Dict) -> Dict[str, List[SatelliteScore]]:
        """應用完整F1→F2→F3→A1篩選流程 - 從8,735顆篩選到563顆候選
        
        Args:
            orbital_data: 衛星基本數據 (TLE數據)
            satellite_orbital_positions: 軌道位置數據 (SGP4計算結果)
        """
        self.logger.info("🔍 開始F1→F2→F3→A1衛星篩選流程...")
        
        # 統計輸入數據
        total_input = sum(len(sats) for sats in orbital_data.values())
        self.filter_statistics['input_satellites'] = total_input
        self.logger.info(f"📊 輸入衛星總數: {total_input} 顆")
        self.logger.info(f"📊 軌道位置數據: {len(satellite_orbital_positions)} 顆衛星")
        
        filtered_candidates = {}
        
        try:
            # 對每個星座應用F1→F2→F3→A1篩選管線
            for constellation in ['starlink', 'oneweb']:
                if constellation in orbital_data:
                    self.logger.info(f"\n🛰️ 開始{constellation.upper()}篩選 ({len(orbital_data[constellation])} 顆)")
                    
                    candidates = await self._apply_comprehensive_filter_pipeline(
                        orbital_data[constellation], 
                        satellite_orbital_positions,
                        constellation
                    )
                    
                    filtered_candidates[constellation] = candidates
                    self.filter_statistics[f'{constellation}_candidates'] = len(candidates)
                    
                    self.logger.info(f"✅ {constellation.upper()}篩選完成: {len(candidates)} 顆")
            
            # 統計最終結果
            total_candidates = sum(len(candidates) for candidates in filtered_candidates.values())
            self.filter_statistics['final_candidates'] = total_candidates
            
            self.logger.info(f"\n🎯 F1→F2→F3→A1篩選完成:")
            self.logger.info(f"   Starlink候選: {self.filter_statistics.get('starlink_candidates', 0)} 顆")
            self.logger.info(f"   OneWeb候選: {self.filter_statistics.get('oneweb_candidates', 0)} 顆")
            self.logger.info(f"   總候選數: {total_candidates} 顆")
            filter_ratio = (total_candidates/total_input)*100 if total_input > 0 else 0.0
            self.logger.info(f"   篩選比例: {filter_ratio:.1f}%")
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ F1→F2→F3→A1篩選失敗: {e}")
            raise

    async def apply_development_filter(self, 
                                     orbital_data: Dict[str, List], 
                                     satellite_orbital_positions: Dict) -> Dict[str, List[SatelliteScore]]:
        """🚀 開發模式：寬鬆篩選，使用真實軌道計算數據"""
        print("🔥🔥🔥 [CRITICAL] apply_development_filter CALLED! Using improved visibility calculation")
        self.logger.info("🚀 開始開發模式寬鬆篩選...")
        
        # 🔥 強制日誌：確認方法被正確調用
        self.logger.info("🔥 [DEBUG] apply_development_filter 被調用！改進的可見性計算方法正在運行")
        
        # 統計輸入數據
        total_input = sum(len(sats) for sats in orbital_data.values())
        self.filter_statistics['input_satellites'] = total_input
        self.logger.info(f"📊 輸入衛星總數: {total_input} 顆")
        
        # ✅ 新增：檢查軌道數據可用性
        available_orbital_data = len(satellite_orbital_positions)
        self.logger.info(f"📊 可用軌道數據: {available_orbital_data} 顆衛星")
        
        # 🎯 修復：添加篩選閾值配置
        min_score_threshold = self.config.get('filtering_params', {}).get('min_score_threshold', 50.0)
        max_candidates_per_constellation = self.config.get('filtering_params', {}).get('max_candidates_per_constellation', 100)
        min_elevation_threshold = self.config.get('filtering_params', {}).get('min_elevation_threshold', 5.0)
        min_visible_time_threshold = self.config.get('filtering_params', {}).get('min_visible_time_threshold', 10.0)
        
        self.logger.info(f"🎯 篩選閾值: 最低評分{min_score_threshold}, 最低仰角{min_elevation_threshold}°, 最少可見時間{min_visible_time_threshold}分鐘")
        self.logger.info(f"🎯 每星座最大候選數: {max_candidates_per_constellation}")
        
        filtered_candidates = {}
        total_visibility_time_all = 0.0
        max_elevation_all = -90.0
        successful_calculations = 0
        total_filtered_out = 0
        satellites_without_orbital_data = 0  # 新增：統計沒有軌道數據的衛星
        
        try:
            # 對每個星座應用寬鬆篩選
            for constellation in ['starlink', 'oneweb']:
                if constellation in orbital_data and orbital_data[constellation]:
                    satellites = orbital_data[constellation]
                    self.logger.info(f"🛰️ 處理{constellation.upper()} ({len(satellites)} 顆)")
                    
                    # 寬鬆的開發模式篩選
                    candidates = []
                    constellation_visibility_time = 0.0
                    constellation_max_elevation = -90.0
                    constellation_filtered_out = 0
                    
                    for satellite in satellites:
                        satellite_id = satellite.satellite_id
                        
                        # 🎯 關鍵修復：只處理有真實軌道數據的衛星
                        if satellite_id in satellite_orbital_positions:
                            orbital_positions = satellite_orbital_positions[satellite_id]
                            self.logger.debug(f"📡 {satellite_id}: 使用{len(orbital_positions)}個真實軌道位置")
                            print(f"🔥🔥🔥 [VISIBILITY] Calculating for {satellite_id}, {len(orbital_positions)} positions")
                            
                            # 使用真實軌道計算可見性分析
                            visibility_analysis = await self._calculate_visibility_analysis(
                                satellite, orbital_positions, constellation
                            )
                            
                            print(f"🔥🔥🔥 [RESULT] {satellite_id}: {visibility_analysis.total_visible_time_minutes:.1f} min, max {visibility_analysis.max_elevation_deg:.1f}°")
                            
                            # 🔥 強制日誌：記錄每個衛星的可見性結果
                            self.logger.debug(f"🔥 [DEBUG] {satellite_id} 可見性結果: {visibility_analysis.total_visible_time_minutes:.1f}分鐘, 最高{visibility_analysis.max_elevation_deg:.1f}°")
                            
                            # 統計總體可見性
                            constellation_visibility_time += visibility_analysis.total_visible_time_minutes
                            constellation_max_elevation = max(constellation_max_elevation, visibility_analysis.max_elevation_deg)
                            successful_calculations += 1
                            
                            # 基於真實可見性數據動態評分
                            visibility_score = min(100.0, visibility_analysis.total_visible_time_minutes * 2)  # 可見時間轉評分
                            elevation_score = min(100.0, (visibility_analysis.max_elevation_deg + 90) * 0.5)  # 仰角轉評分
                            signal_score = min(100.0, (visibility_analysis.signal_strength_estimate_dbm + 150) * 2)  # 信號轉評分
                            
                            # 開發模式給予寬鬆評分（最低60分）
                            total_score = max(60.0, (visibility_score + elevation_score + signal_score) / 3)
                            
                            self.logger.debug(f"   🎯 {satellite_id}: 可見{visibility_analysis.total_visible_time_minutes:.1f}分鐘, 最高仰角{visibility_analysis.max_elevation_deg:.1f}°, 評分{total_score:.1f}")
                            
                            # 🎯 關鍵修復：應用篩選閾值
                            passes_filters = True
                            filter_reasons = []
                            
                            # 1. 評分篩選
                            if total_score < min_score_threshold:
                                passes_filters = False
                                filter_reasons.append(f"評分{total_score:.1f} < {min_score_threshold}")
                            
                            # 2. 仰角篩選
                            if visibility_analysis.max_elevation_deg < min_elevation_threshold:
                                passes_filters = False
                                filter_reasons.append(f"仰角{visibility_analysis.max_elevation_deg:.1f}° < {min_elevation_threshold}°")
                            
                            # 3. 可見時間篩選
                            if visibility_analysis.total_visible_time_minutes < min_visible_time_threshold:
                                passes_filters = False
                                filter_reasons.append(f"可見時間{visibility_analysis.total_visible_time_minutes:.1f}分鐘 < {min_visible_time_threshold}分鐘")
                            
                            # 🎯 只有通過篩選的衛星才會被添加
                            if passes_filters:
                                # 創建評分候選（使用計算出的評分）
                                candidate = SatelliteScore(
                                    satellite_id=satellite.satellite_id,
                                    constellation=constellation,
                                    total_score=total_score,
                                    geographic_relevance_score=total_score * 0.8,  # 基於總分調整
                                    orbital_characteristics_score=total_score * 0.9,
                                    signal_quality_score=total_score * 0.85,
                                    temporal_distribution_score=total_score * 0.95,
                                    visibility_compliance_score=total_score,
                                    visibility_analysis=visibility_analysis,
                                    scoring_rationale={"mode": "🚀 開發模式：基於真實軌道數據評分"},
                                    is_selected=True
                                )
                                candidates.append(candidate)
                                self.logger.debug(f"✅ {satellite_id}: 通過篩選，評分{total_score:.1f}")
                            else:
                                constellation_filtered_out += 1
                                total_filtered_out += 1
                                self.logger.debug(f"❌ {satellite_id}: 被篩選掉 - {', '.join(filter_reasons)}")
                        
                        else:
                            # 🚨 關鍵修復：沒有軌道數據的衛星直接拒絕，不給假數據
                            satellites_without_orbital_data += 1
                            constellation_filtered_out += 1
                            total_filtered_out += 1
                            self.logger.debug(f"🚫 {satellite_id}: 沒有軌道數據，直接拒絕")
                    
                    # 4. 🎯 應用每星座最大候選數限制
                    if len(candidates) > max_candidates_per_constellation:
                        # 按評分排序，保留最高分的候選
                        candidates.sort(key=lambda c: c.total_score, reverse=True)
                        removed_count = len(candidates) - max_candidates_per_constellation
                        candidates = candidates[:max_candidates_per_constellation]
                        constellation_filtered_out += removed_count
                        total_filtered_out += removed_count
                        self.logger.info(f"🔄 {constellation.upper()}: 按評分限制到{max_candidates_per_constellation}顆，移除{removed_count}顆低分衛星")
                    
                    filtered_candidates[constellation] = candidates
                    self.filter_statistics[f'{constellation}_candidates'] = len(candidates)
                    self.filter_statistics[f'{constellation}_filtered_out'] = constellation_filtered_out
                    
                    # 記錄星座統計
                    total_visibility_time_all += constellation_visibility_time
                    max_elevation_all = max(max_elevation_all, constellation_max_elevation)
                    
                    self.logger.info(f"✅ {constellation.upper()}開發篩選: {len(candidates)} 顆候選 (篩選掉{constellation_filtered_out}顆)")
                    self.logger.info(f"🔥 [DEBUG] {constellation.upper()} 總可見時間: {constellation_visibility_time:.1f}分鐘, 最高仰角: {constellation_max_elevation:.1f}°")
            
            # 統計最終結果
            total_candidates = sum(len(candidates) for candidates in filtered_candidates.values())
            self.filter_statistics['final_candidates'] = total_candidates
            self.filter_statistics['total_filtered_out'] = total_filtered_out
            
            # 🔥 強制日誌：最終統計結果
            self.logger.info(f"🔥 [DEBUG] 開發模式篩選最終統計:")
            self.logger.info(f"🔥 [DEBUG]   輸入衛星總數: {total_input} 顆")
            self.logger.info(f"🔥 [DEBUG]   沒有軌道數據: {satellites_without_orbital_data} 顆")
            self.logger.info(f"🔥 [DEBUG]   篩選掉衛星: {total_filtered_out} 顆")
            self.logger.info(f"🔥 [DEBUG]   最終候選數: {total_candidates} 顆")
            self.logger.info(f"🔥 [DEBUG]   篩選比例: {(total_filtered_out/total_input)*100:.1f}%")
            self.logger.info(f"🔥 [DEBUG]   成功計算可見性: {successful_calculations} 顆")
            self.logger.info(f"🔥 [DEBUG]   全系統總可見時間: {total_visibility_time_all:.1f} 分鐘")
            self.logger.info(f"🔥 [DEBUG]   全系統最高仰角: {max_elevation_all:.1f}°")
            
            # ✅ 計算真實可見性統計
            total_visible_time = 0.0
            max_elevation_found = -90.0
            candidates_with_orbital_data = 0
            
            for candidates in filtered_candidates.values():
                for candidate in candidates:
                    if candidate.visibility_analysis:
                        total_visible_time += candidate.visibility_analysis.total_visible_time_minutes
                        max_elevation_found = max(max_elevation_found, candidate.visibility_analysis.max_elevation_deg)
                        if candidate.satellite_id in satellite_orbital_positions:
                            candidates_with_orbital_data += 1
            
            self.logger.info(f"🎯 開發模式篩選完成:")
            self.logger.info(f"   Starlink候選: {self.filter_statistics.get('starlink_candidates', 0)} 顆")
            self.logger.info(f"   OneWeb候選: {self.filter_statistics.get('oneweb_candidates', 0)} 顆")
            self.logger.info(f"   總候選數: {total_candidates} 顆")
            self.logger.info(f"   有軌道數據: {candidates_with_orbital_data} 顆")
            self.logger.info(f"   總可見時間: {total_visible_time:.1f} 分鐘")
            self.logger.info(f"   最高仰角: {max_elevation_found:.1f}°")
            
            # 🔥 強制驗證：確認可見性結果被正確保存
            if total_visible_time > 0:
                self.logger.info(f"✅ [SUCCESS] 改進的可見性計算成功！發現 {total_visible_time:.1f} 分鐘總可見時間")
            else:
                self.logger.error(f"❌ [ERROR] 可見性計算失敗！總可見時間為 0")
            
            # 🎯 驗證篩選功能正常工作
            if total_filtered_out > 0:
                self.logger.info(f"✅ [SUCCESS] 篩選機制工作正常！成功篩選掉 {total_filtered_out} 顆衛星")
                self.logger.info(f"  其中 {satellites_without_orbital_data} 顆因缺少軌道數據被拒絕")
            else:
                self.logger.warning(f"⚠️ [WARNING] 沒有衛星被篩選掉，檢查閾值設置")
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ 開發模式篩選失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _apply_comprehensive_filter_pipeline(self, 
                                    satellites: List, 
                                    orbital_positions: Dict, 
                                    constellation: str) -> List[SatelliteScore]:
        """實現完整的F1→F2→F3→A1篩選管線"""
        
        params = self.constellation_params[constellation]
        current_satellites = satellites.copy()
        
        # F1階段: 基礎地理篩選 (8,735 → ~2,500)
        self.logger.info(f"📍 F1階段: 基礎地理篩選 ({len(current_satellites)} 顆)")
        f1_filtered = await self._f1_geographic_filter(current_satellites, constellation)
        self.logger.info(f"   篩選後: {len(f1_filtered)} 顆")
        self.filter_statistics[f'f1_{constellation}'] = len(f1_filtered)
        
        # F2階段: 可見性時間篩選 (~2,500 → ~1,200) - 需要軌道位置數據
        self.logger.info(f"⏰ F2階段: 可見性時間篩選 ({len(f1_filtered)} 顆)")
        f2_filtered = await self._f2_visibility_time_filter(
            f1_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(f2_filtered)} 顆")
        self.filter_statistics[f'f2_{constellation}'] = len(f2_filtered)
        
        # F3階段: 仰角品質篩選 (~1,200 → ~800) - 需要軌道位置數據
        self.logger.info(f"📐 F3階段: 仰角品質篩選 ({len(f2_filtered)} 顆)")
        f3_filtered = await self._f3_elevation_quality_filter(
            f2_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(f3_filtered)} 顆")
        self.filter_statistics[f'f3_{constellation}'] = len(f3_filtered)
        
        # A1階段: 服務連續性篩選 (~800 → ~650) - 需要軌道位置數據
        self.logger.info(f"🔄 A1階段: 服務連續性篩選 ({len(f3_filtered)} 顆)")
        a1_filtered = await self._a1_service_continuity_filter(
            f3_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(a1_filtered)} 顆")
        self.filter_statistics[f'a1_{constellation}'] = len(a1_filtered)
        
        # 階段五: 信號品質預評估 (~650 → ~580) - 保持現有功能
        self.logger.info(f"📶 階段五: 信號品質預評估 ({len(a1_filtered)} 顆)")
        stage5_filtered = await self._stage5_signal_quality_assessment(
            a1_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(stage5_filtered)} 顆")
        self.filter_statistics[f'stage5_{constellation}'] = len(stage5_filtered)
        
        # 階段六: 負載平衡最佳化 (~580 → 563)
        self.logger.info(f"⚖️ 階段六: 負載平衡最佳化 ({len(stage5_filtered)} 顆)")
        final_candidates = await self._stage6_load_balancing_optimization(
            stage5_filtered, constellation
        )
        self.logger.info(f"   最終候選: {len(final_candidates)} 顆")
        self.filter_statistics[f'stage6_{constellation}'] = len(final_candidates)
        
        return final_candidates
    
    async def _f1_geographic_filter(self, satellites: List, constellation: str) -> List:
        """F1階段: 基礎地理篩選 - 針對NTPU觀測點優化"""
        relevant_satellites = []
        
        for satellite in satellites:
            # 1. 軌道傾角檢查 - 必須大於觀測點緯度
            if satellite.inclination_deg <= self.observer_lat:
                continue  # 跳過不能覆蓋NTPU的衛星
            
            # 2. 升交點經度相關性評分 (修正: LEO衛星RAAN會變化，不應過度依賴)
            longitude_diff = abs(satellite.raan_deg - self.observer_lon)
            if longitude_diff > 180:
                longitude_diff = 360 - longitude_diff
            
            # 🔧 修正: 經度評分更寬鬆，因為LEO衛星會經過所有經度
            longitude_relevance = max(40, 100 - longitude_diff * 0.5)  # 最低40分，更寬鬆的斜率
            
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
    
    async def _f2_visibility_time_filter(self, 
                                            satellites: List, 
                                            orbital_positions: Dict, 
                                            constellation: str) -> List:
        """F2階段: 可見性時間篩選 - 保留可見時間 > 15分鐘的衛星"""
        params = self.constellation_params[constellation]
        min_visible_time = params['min_visible_time_min']
        
        filtered_satellites = []
        
        for satellite in satellites:
            if satellite.satellite_id not in orbital_positions:
                continue  # 跳過沒有軌道數據的衛星
            
            # 計算總可見時間
            visibility_analysis = await self._calculate_visibility_analysis(
                satellite, orbital_positions[satellite.satellite_id], constellation
            )
            
            # 篩選條件: 總可見時間 >= 最低要求
            if visibility_analysis.total_visible_time_minutes >= min_visible_time:
                # 將可見性分析附加到衛星對象
                satellite.visibility_analysis = visibility_analysis
                filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    async def _f3_elevation_quality_filter(self, 
                                              satellites: List, 
                                              orbital_positions: Dict, 
                                              constellation: str) -> List:
        """F3階段: 仰角品質篩選 - 保留最高仰角符合要求的衛星"""
        params = self.constellation_params[constellation]
        min_elevation = params['min_elevation_deg']
        
        filtered_satellites = []
        
        for satellite in satellites:
            # 使用F2階段計算的可見性分析
            if hasattr(satellite, 'visibility_analysis'):
                visibility = satellite.visibility_analysis
                
                # 篩選條件: 最高仰角 >= 門檻
                if visibility.max_elevation_deg >= min_elevation:
                    filtered_satellites.append(satellite)
            else:
                # 如果沒有可見性分析，重新計算
                visibility_analysis = await self._calculate_visibility_analysis(
                    satellite, orbital_positions[satellite.satellite_id], constellation
                )
                
                if visibility_analysis.max_elevation_deg >= min_elevation:
                    satellite.visibility_analysis = visibility_analysis
                    filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    async def _a1_service_continuity_filter(self, 
                                               satellites: List, 
                                               orbital_positions: Dict, 
                                               constellation: str) -> List:
        """A1階段: 服務連續性篩選 - 至少3個獨立可見窗口"""
        params = self.constellation_params[constellation]
        min_passes = params['min_visible_passes']
        
        filtered_satellites = []
        
        for satellite in satellites:
            if hasattr(satellite, 'visibility_analysis'):
                visibility = satellite.visibility_analysis
                
                # 篩選條件: 可見次數 >= 最少要求
                if visibility.visible_passes_count >= min_passes:
                    filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    async def _stage5_signal_quality_assessment(self, 
                                               satellites: List, 
                                               orbital_positions: Dict, 
                                               constellation: str) -> List:
        """階段五: 信號品質預評估 - RSRP ≥ -110 dBm"""
        params = self.constellation_params[constellation]
        rsrp_threshold = params['rsrp_threshold_dbm']
        
        filtered_satellites = []
        
        for satellite in satellites:
            if hasattr(satellite, 'visibility_analysis'):
                visibility = satellite.visibility_analysis
                
                # 篩選條件: 信號強度 >= 門檻
                if visibility.signal_strength_estimate_dbm >= rsrp_threshold:
                    filtered_satellites.append(satellite)
        
        return filtered_satellites
    
    async def _stage6_load_balancing_optimization(self, 
                                                 satellites: List, 
                                                 constellation: str) -> List[SatelliteScore]:
        """階段六: 負載平衡最佳化 - 選擇最終候選數量"""
        params = self.constellation_params[constellation]
        target_count = params['target_candidate_count']
        
        # 對衛星進行評分排序
        scored_satellites = []
        
        for satellite in satellites:
            score = await self._calculate_final_score(satellite, constellation)
            scored_satellites.append(score)
        
        # 按總分排序並選取目標數量
        scored_satellites.sort(key=lambda x: x.total_score, reverse=True)
        selected_candidates = scored_satellites[:target_count]
        
        # 標記選中狀態
        for candidate in selected_candidates:
            candidate.is_selected = True
        
        return selected_candidates
    
    async def _calculate_visibility_analysis(self, 
                                           satellite, 
                                           orbital_positions: List, 
                                           constellation: str) -> VisibilityAnalysis:
        """計算衛星的詳細可見性分析 - 使用原本6階段系統的proven方法"""
        import math
        
        sat_id = satellite.get('satellite_id', 'unknown') if isinstance(satellite, dict) else 'unknown'
        print(f"🔥🔥🔥 [CALC] Starting calculation for {sat_id}")
        if orbital_positions:
            print(f"🔥🔥🔥 [CALC] First position sample: {orbital_positions[0]}")
        else:
            print("🔥🔥🔥 [CALC] NO POSITIONS!")
        
        params = self.constellation_params[constellation]
        min_elevation = params['min_elevation_deg']
        
        total_visible_time = 0.0
        max_elevation = -90.0
        visible_passes = 0
        pass_durations = []
        best_elevation_time = None
        signal_strengths = []
        
        current_pass_start = None
        current_pass_duration = 0.0
        
        # 🔧 使用原本6階段系統的proven elevation calculation
        def calculate_elevation_from_eci(eci_position):
            """使用原本系統的proven方法計算仰角"""
            x, y, z = eci_position
            
            # 轉換為弧度
            lat_rad = math.radians(self.observer_lat)
            lon_rad = math.radians(self.observer_lon)
            
            # 地球半徑 (km)
            earth_radius = 6371.0
            
            # 觀測點位置
            observer_x = earth_radius * math.cos(lat_rad) * math.cos(lon_rad)
            observer_y = earth_radius * math.cos(lat_rad) * math.sin(lon_rad)
            observer_z = earth_radius * math.sin(lat_rad)
            
            # 相對位置
            dx = x - observer_x
            dy = y - observer_y
            dz = z - observer_z
            
            # 簡化仰角計算
            ground_range = math.sqrt(dx*dx + dy*dy)
            elevation_rad = math.atan2(dz, ground_range)
            
            return math.degrees(elevation_rad)
        
        # 🔧 新增：根據地理位置計算ECI座標
        def geodetic_to_eci(lat_deg, lon_deg, alt_km):
            """將地理座標轉換為ECI座標 - 簡化版本"""
            lat_rad = math.radians(lat_deg)
            lon_rad = math.radians(lon_deg)
            earth_radius = 6371.0
            
            # 簡化的ECI轉換（忽略地球自轉和時間差）
            x = (earth_radius + alt_km) * math.cos(lat_rad) * math.cos(lon_rad)
            y = (earth_radius + alt_km) * math.cos(lat_rad) * math.sin(lon_rad)
            z = (earth_radius + alt_km) * math.sin(lat_rad)
            
            return (x, y, z)
        
        for position in orbital_positions:
            # 支援字典格式和SatellitePosition物件格式的軌道位置數據
            if isinstance(position, dict):
                lat_deg = position['latitude_deg']
                lon_deg = position['longitude_deg']
                alt_km = position['altitude_km']
                timestamp = position['timestamp']
            else:
                # 處理SatellitePosition物件
                lat_deg = float(position.latitude_deg)
                lon_deg = float(position.longitude_deg)
                alt_km = float(position.altitude_km)
                timestamp = position.timestamp
            
            # 🎯 關鍵修復：使用原本系統的proven方法重新計算仰角
            eci_position = geodetic_to_eci(lat_deg, lon_deg, alt_km)
            elevation = calculate_elevation_from_eci(eci_position)
            
            # 計算距離（使用球面距離公式）
            observer_lat_rad = math.radians(self.observer_lat)
            observer_lon_rad = math.radians(self.observer_lon)
            sat_lat_rad = math.radians(lat_deg)
            sat_lon_rad = math.radians(lon_deg)
            
            # Haversine distance formula
            dlat = sat_lat_rad - observer_lat_rad
            dlon = sat_lon_rad - observer_lon_rad
            a = math.sin(dlat/2)**2 + math.cos(observer_lat_rad) * math.cos(sat_lat_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            ground_distance = 6371.0 * c
            distance = math.sqrt(ground_distance**2 + alt_km**2)
            
            # 🔍 Debug: 記錄仰角計算結果
            if len(signal_strengths) < 3:  # 只記錄前3個位置以避免過多log
                original_elev = position.get('elevation_deg', 'N/A') if isinstance(position, dict) else getattr(position, 'elevation_deg', 'N/A')
                print(f"🔥🔥🔥 [ELEV] Position {len(signal_strengths)+1}: Recalculated {elevation:.2f}° (Original: {original_elev}°)")
            
            # 檢查是否可見
            is_visible = elevation >= min_elevation
            
            if is_visible:
                # 記錄最高仰角
                if elevation > max_elevation:
                    max_elevation = elevation
                    best_elevation_time = timestamp
                
                # 累計可見時間 (假設30秒間隔)
                total_visible_time += 0.5  # 30秒 = 0.5分鐘
                
                # 計算信號強度估算
                rsrp_estimate = await self._estimate_signal_strength(elevation, distance, constellation)
                signal_strengths.append(rsrp_estimate)
                
                # 追蹤可見窗口
                if current_pass_start is None:
                    current_pass_start = timestamp
                    current_pass_duration = 0.5
                else:
                    current_pass_duration += 0.5
            else:
                # 可見窗口結束
                if current_pass_start is not None:
                    visible_passes += 1
                    pass_durations.append(current_pass_duration)
                    current_pass_start = None
                    current_pass_duration = 0.0
        
        # 處理最後一個可見窗口
        if current_pass_start is not None:
            visible_passes += 1
            pass_durations.append(current_pass_duration)
        
        avg_pass_duration = sum(pass_durations) / len(pass_durations) if pass_durations else 0
        avg_signal_strength = sum(signal_strengths) / len(signal_strengths) if signal_strengths else -150
        
        # 🔍 Debug: 記錄可見性分析結果
        self.logger.info(f"   🎯 {satellite.satellite_id}: 可見{total_visible_time:.1f}分鐘, 最高仰角{max_elevation:.1f}°, {visible_passes}次通過")
        
        return VisibilityAnalysis(
            satellite_id=satellite.satellite_id,
            total_visible_time_minutes=total_visible_time,
            max_elevation_deg=max_elevation,
            visible_passes_count=visible_passes,
            avg_pass_duration_minutes=avg_pass_duration,
            best_elevation_time=best_elevation_time,
            signal_strength_estimate_dbm=avg_signal_strength
        )
    
    async def _estimate_signal_strength(self, elevation_deg: float, distance_km: float, constellation: str) -> float:
        """基於仰角和距離估算信號強度 (RSRP)"""
        
        # 基本自由空間路徑損耗計算 (簡化版)
        frequency_ghz = 12.0  # Ku頻段
        tx_power_dbm = 43.0   # 發射功率
        antenna_gain_dbi = 35.0  # 天線增益
        
        # 自由空間路徑損耗
        fspl_db = 32.44 + 20 * math.log10(frequency_ghz) + 20 * math.log10(distance_km)
        
        # 仰角損失修正
        elevation_loss_db = max(0, (90 - elevation_deg) * 0.1) if elevation_deg > 0 else 50
        
        # 大氣衰減 (簡化)
        atmospheric_loss_db = 2.0
        
        # 計算接收信號強度
        rsrp_dbm = tx_power_dbm + antenna_gain_dbi - fspl_db - elevation_loss_db - atmospheric_loss_db
        
        return rsrp_dbm
    
    async def _calculate_final_score(self, satellite, constellation: str) -> SatelliteScore:
        """計算衛星的最終綜合評分"""
        
        visibility = satellite.visibility_analysis
        
        # 1. 可見性合規評分 (40%)
        visibility_score = min(100, (visibility.total_visible_time_minutes / 30.0) * 100)
        
        # 2. 仰角品質評分 (25%)
        elevation_score = min(100, visibility.max_elevation_deg * 2)
        
        # 3. 信號品質評分 (20%)
        signal_score = min(100, max(0, (visibility.signal_strength_estimate_dbm + 120) * 2))
        
        # 4. 服務連續性評分 (15%)
        continuity_score = min(100, visibility.visible_passes_count * 20)
        
        # 計算總分
        total_score = (
            visibility_score * 0.40 +
            elevation_score * 0.25 +
            signal_score * 0.20 +
            continuity_score * 0.15
        )
        
        return SatelliteScore(
            satellite_id=satellite.satellite_id,
            constellation=constellation,
            total_score=total_score,
            geographic_relevance_score=70.0,  # 簡化
            orbital_characteristics_score=elevation_score,
            signal_quality_score=signal_score,
            temporal_distribution_score=continuity_score,
            visibility_compliance_score=visibility_score,
            visibility_analysis=visibility,
            scoring_rationale={
                'visibility_analysis': f"可見時間{visibility.total_visible_time_minutes:.1f}分鐘，最高仰角{visibility.max_elevation_deg:.1f}°",
                'signal_analysis': f"預估RSRP {visibility.signal_strength_estimate_dbm:.1f} dBm",
                'continuity_analysis': f"{visibility.visible_passes_count}次可見窗口，平均持續{visibility.avg_pass_duration_minutes:.1f}分鐘"
            },
            is_selected=False
        )
    
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
                'filter_method': 'six_stage_pipeline_v2',
                'candidates': {}
            }
            
            # 匯出候選衛星詳細信息
            for constellation, candidates in filtered_candidates.items():
                export_data['candidates'][constellation] = []
                
                for candidate in candidates:
                    candidate_data = {
                        'satellite_id': candidate.satellite_id,
                        'total_score': round(candidate.total_score, 2),
                        'visibility_compliance_score': round(candidate.visibility_compliance_score, 2),
                        'orbital_characteristics_score': round(candidate.orbital_characteristics_score, 2),
                        'signal_quality_score': round(candidate.signal_quality_score, 2),
                        'temporal_distribution_score': round(candidate.temporal_distribution_score, 2),
                        'scoring_rationale': candidate.scoring_rationale,
                        'is_selected': candidate.is_selected
                    }
                    
                    # 添加可見性分析詳情
                    if candidate.visibility_analysis:
                        visibility = candidate.visibility_analysis
                        candidate_data['visibility_analysis'] = {
                            'total_visible_time_minutes': round(visibility.total_visible_time_minutes, 2),
                            'max_elevation_deg': round(visibility.max_elevation_deg, 2),
                            'visible_passes_count': visibility.visible_passes_count,
                            'avg_pass_duration_minutes': round(visibility.avg_pass_duration_minutes, 2),
                            'signal_strength_estimate_dbm': round(visibility.signal_strength_estimate_dbm, 2)
                        }
                    
                    export_data['candidates'][constellation].append(candidate_data)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 六階段篩選結果已匯出至: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 篩選結果匯出失敗: {e}")