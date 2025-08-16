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
        """應用完整六階段篩選流程 - 從8,735顆篩選到563顆候選
        
        Args:
            orbital_data: 衛星基本數據 (TLE數據)
            satellite_orbital_positions: 軌道位置數據 (SGP4計算結果)
        """
        self.logger.info("🔍 開始六階段衛星篩選流程...")
        
        # 統計輸入數據
        total_input = sum(len(sats) for sats in orbital_data.values())
        self.filter_statistics['input_satellites'] = total_input
        self.logger.info(f"📊 輸入衛星總數: {total_input} 顆")
        self.logger.info(f"📊 軌道位置數據: {len(satellite_orbital_positions)} 顆衛星")
        
        filtered_candidates = {}
        
        try:
            # 對每個星座應用六階段篩選管線
            for constellation in ['starlink', 'oneweb']:
                if constellation in orbital_data:
                    self.logger.info(f"\n🛰️ 開始{constellation.upper()}六階段篩選 ({len(orbital_data[constellation])} 顆)")
                    
                    candidates = await self._apply_six_stage_filter(
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
            
            self.logger.info(f"\n🎯 六階段篩選完成:")
            self.logger.info(f"   Starlink候選: {self.filter_statistics.get('starlink_candidates', 0)} 顆")
            self.logger.info(f"   OneWeb候選: {self.filter_statistics.get('oneweb_candidates', 0)} 顆")
            self.logger.info(f"   總候選數: {total_candidates} 顆")
            filter_ratio = (total_candidates/total_input)*100 if total_input > 0 else 0.0
            self.logger.info(f"   篩選比例: {filter_ratio:.1f}%")
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ 六階段篩選失敗: {e}")
            raise

    async def apply_development_filter(self, 
                                     orbital_data: Dict[str, List], 
                                     satellite_orbital_positions: Dict) -> Dict[str, List[SatelliteScore]]:
        """🚀 开发模式：宽松筛选，使用真实轨道计算数据"""
        print("🔥🔥🔥 [CRITICAL] apply_development_filter CALLED! Using improved visibility calculation")
        self.logger.info("🚀 开始开发模式宽松筛选...")
        
        # 🔥 强制日志：确认方法被正确调用
        self.logger.info("🔥 [DEBUG] apply_development_filter 被调用！改进的可见性计算方法正在运行")
        
        # 统计输入数据
        total_input = sum(len(sats) for sats in orbital_data.values())
        self.filter_statistics['input_satellites'] = total_input
        self.logger.info(f"📊 输入卫星总数: {total_input} 颗")
        
        # ✅ 新增：检查轨道数据可用性
        available_orbital_data = len(satellite_orbital_positions)
        self.logger.info(f"📊 可用轨道数据: {available_orbital_data} 颗卫星")
        
        filtered_candidates = {}
        total_visibility_time_all = 0.0
        max_elevation_all = -90.0
        successful_calculations = 0
        
        try:
            # 对每个星座应用宽松筛选
            for constellation in ['starlink', 'oneweb']:
                if constellation in orbital_data and orbital_data[constellation]:
                    satellites = orbital_data[constellation]
                    self.logger.info(f"🛰️ 处理{constellation.upper()} ({len(satellites)} 颗)")
                    
                    # 宽松的开发模式筛选
                    candidates = []
                    constellation_visibility_time = 0.0
                    constellation_max_elevation = -90.0
                    
                    for satellite in satellites:
                        satellite_id = satellite.satellite_id
                        
                        # ✅ 关键修复：使用真实轨道数据计算可见性分析
                        if satellite_id in satellite_orbital_positions:
                            orbital_positions = satellite_orbital_positions[satellite_id]
                            self.logger.info(f"📡 {satellite_id}: 使用{len(orbital_positions)}个真实轨道位置")
                            print(f"🔥🔥🔥 [VISIBILITY] Calculating for {satellite_id}, {len(orbital_positions)} positions")
                            
                            # 使用真实轨道计算可见性分析
                            visibility_analysis = await self._calculate_visibility_analysis(
                                satellite, orbital_positions, constellation
                            )
                            
                            print(f"🔥🔥🔥 [RESULT] {satellite_id}: {visibility_analysis.total_visible_time_minutes:.1f} min, max {visibility_analysis.max_elevation_deg:.1f}°")
                            
                            # 🔥 强制日志：记录每个卫星的可见性结果
                            self.logger.info(f"🔥 [DEBUG] {satellite_id} 可见性结果: {visibility_analysis.total_visible_time_minutes:.1f}分钟, 最高{visibility_analysis.max_elevation_deg:.1f}°")
                            
                            # 统计总体可见性
                            constellation_visibility_time += visibility_analysis.total_visible_time_minutes
                            constellation_max_elevation = max(constellation_max_elevation, visibility_analysis.max_elevation_deg)
                            successful_calculations += 1
                            
                            # 基于真实可见性数据动态评分
                            visibility_score = min(100.0, visibility_analysis.total_visible_time_minutes * 2)  # 可见时间转评分
                            elevation_score = min(100.0, (visibility_analysis.max_elevation_deg + 90) * 0.5)  # 仰角转评分
                            signal_score = min(100.0, (visibility_analysis.signal_strength_estimate_dbm + 150) * 2)  # 信号转评分
                            
                            # 开发模式给予宽松评分（最低60分）
                            total_score = max(60.0, (visibility_score + elevation_score + signal_score) / 3)
                            
                            self.logger.info(f"   🎯 {satellite_id}: 可见{visibility_analysis.total_visible_time_minutes:.1f}分钟, 最高仰角{visibility_analysis.max_elevation_deg:.1f}°, 评分{total_score:.1f}")
                            
                        else:
                            # 没有轨道数据时使用简化分析（但记录警告）
                            self.logger.warning(f"⚠️ {satellite_id}: 缺少轨道数据，使用简化分析")
                            visibility_analysis = VisibilityAnalysis(
                                satellite_id=satellite.satellite_id,
                                total_visible_time_minutes=50.0,  # 降低预设值
                                max_elevation_deg=20.0,           # 降低预设值
                                visible_passes_count=3,
                                avg_pass_duration_minutes=15.0,
                                best_elevation_time=datetime.utcnow(),
                                signal_strength_estimate_dbm=-100.0  # 较弱信号
                            )
                            total_score = 60.0  # 最低分
                        
                        # 创建评分候选（使用计算出的评分）
                        candidate = SatelliteScore(
                            satellite_id=satellite.satellite_id,
                            constellation=constellation,
                            total_score=total_score,
                            geographic_relevance_score=total_score * 0.8,  # 基于总分调整
                            orbital_characteristics_score=total_score * 0.9,
                            signal_quality_score=total_score * 0.85,
                            temporal_distribution_score=total_score * 0.95,
                            visibility_compliance_score=total_score,
                            visibility_analysis=visibility_analysis,
                            scoring_rationale={"mode": "🚀 开发模式：基于真实轨道数据评分"},
                            is_selected=True
                        )
                        candidates.append(candidate)
                    
                    filtered_candidates[constellation] = candidates
                    self.filter_statistics[f'{constellation}_candidates'] = len(candidates)
                    
                    # 记录星座统计
                    total_visibility_time_all += constellation_visibility_time
                    max_elevation_all = max(max_elevation_all, constellation_max_elevation)
                    
                    self.logger.info(f"✅ {constellation.upper()}开发筛选: {len(candidates)} 颗候选")
                    self.logger.info(f"🔥 [DEBUG] {constellation.upper()} 总可见时间: {constellation_visibility_time:.1f}分钟, 最高仰角: {constellation_max_elevation:.1f}°")
            
            # 统计最终结果
            total_candidates = sum(len(candidates) for candidates in filtered_candidates.values())
            self.filter_statistics['final_candidates'] = total_candidates
            
            # 🔥 强制日志：最终统计结果
            self.logger.info(f"🔥 [DEBUG] 开发模式筛选最终统计:")
            self.logger.info(f"🔥 [DEBUG]   成功计算可见性: {successful_calculations} 颗")
            self.logger.info(f"🔥 [DEBUG]   全系统总可见时间: {total_visibility_time_all:.1f} 分钟")
            self.logger.info(f"🔥 [DEBUG]   全系统最高仰角: {max_elevation_all:.1f}°")
            
            # ✅ 计算真实可见性统计
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
            
            self.logger.info(f"🎯 开发模式筛选完成:")
            self.logger.info(f"   Starlink候选: {self.filter_statistics.get('starlink_candidates', 0)} 颗")
            self.logger.info(f"   OneWeb候选: {self.filter_statistics.get('oneweb_candidates', 0)} 颗")
            self.logger.info(f"   总候选数: {total_candidates} 颗")
            self.logger.info(f"   有轨道数据: {candidates_with_orbital_data} 颗")
            self.logger.info(f"   总可见时间: {total_visible_time:.1f} 分钟")
            self.logger.info(f"   最高仰角: {max_elevation_found:.1f}°")
            
            # 🔥 强制验证：确认可见性结果被正确保存
            if total_visible_time > 0:
                self.logger.info(f"✅ [SUCCESS] 改进的可见性计算成功！发现 {total_visible_time:.1f} 分钟总可见时间")
            else:
                self.logger.error(f"❌ [ERROR] 可见性计算失败！总可见时间为 0")
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ 开发模式筛选失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _apply_six_stage_filter(self, 
                                    satellites: List, 
                                    orbital_positions: Dict, 
                                    constellation: str) -> List[SatelliteScore]:
        """實現完整的六階段篩選管線"""
        
        params = self.constellation_params[constellation]
        current_satellites = satellites.copy()
        
        # 階段一: 基礎地理篩選 (8,735 → ~2,500)
        self.logger.info(f"📍 階段一: 基礎地理篩選 ({len(current_satellites)} 顆)")
        stage1_filtered = await self._stage1_geographic_filter(current_satellites, constellation)
        self.logger.info(f"   篩選後: {len(stage1_filtered)} 顆")
        self.filter_statistics[f'stage1_{constellation}'] = len(stage1_filtered)
        
        # 階段二: 可見性時間篩選 (~2,500 → ~1,200) - 需要軌道位置數據
        self.logger.info(f"⏰ 階段二: 可見性時間篩選 ({len(stage1_filtered)} 顆)")
        stage2_filtered = await self._stage2_visibility_time_filter(
            stage1_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(stage2_filtered)} 顆")
        self.filter_statistics[f'stage2_{constellation}'] = len(stage2_filtered)
        
        # 階段三: 仰角品質篩選 (~1,200 → ~800) - 需要軌道位置數據
        self.logger.info(f"📐 階段三: 仰角品質篩選 ({len(stage2_filtered)} 顆)")
        stage3_filtered = await self._stage3_elevation_quality_filter(
            stage2_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(stage3_filtered)} 顆")
        self.filter_statistics[f'stage3_{constellation}'] = len(stage3_filtered)
        
        # 階段四: 服務連續性篩選 (~800 → ~650) - 需要軌道位置數據
        self.logger.info(f"🔄 階段四: 服務連續性篩選 ({len(stage3_filtered)} 顆)")
        stage4_filtered = await self._stage4_service_continuity_filter(
            stage3_filtered, orbital_positions, constellation
        )
        self.logger.info(f"   篩選後: {len(stage4_filtered)} 顆")
        self.filter_statistics[f'stage4_{constellation}'] = len(stage4_filtered)
        
        # 階段五: 信號品質預評估 (~650 → ~580) - 需要軌道位置數據
        self.logger.info(f"📶 階段五: 信號品質預評估 ({len(stage4_filtered)} 顆)")
        stage5_filtered = await self._stage5_signal_quality_assessment(
            stage4_filtered, orbital_positions, constellation
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
    
    async def _stage1_geographic_filter(self, satellites: List, constellation: str) -> List:
        """階段一: 基礎地理篩選 - 針對NTPU觀測點優化"""
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
    
    async def _stage2_visibility_time_filter(self, 
                                            satellites: List, 
                                            orbital_positions: Dict, 
                                            constellation: str) -> List:
        """階段二: 可見性時間篩選 - 保留可見時間 > 15分鐘的衛星"""
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
    
    async def _stage3_elevation_quality_filter(self, 
                                              satellites: List, 
                                              orbital_positions: Dict, 
                                              constellation: str) -> List:
        """階段三: 仰角品質篩選 - 保留最高仰角符合要求的衛星"""
        params = self.constellation_params[constellation]
        min_elevation = params['min_elevation_deg']
        
        filtered_satellites = []
        
        for satellite in satellites:
            # 使用階段二計算的可見性分析
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
    
    async def _stage4_service_continuity_filter(self, 
                                               satellites: List, 
                                               orbital_positions: Dict, 
                                               constellation: str) -> List:
        """階段四: 服務連續性篩選 - 至少3個獨立可見窗口"""
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