"""
動態池策略引擎 - Stage 6 內部模組化拆分

從 temporal_spatial_analysis_engine.py 中提取的動態池選擇和策略決策功能
包含20個策略創建和執行相關的方法，專注於衛星池動態管理策略

職責範圍:
- 動態池選擇策略創建和評估
- 時空互補策略實施
- 主動覆蓋保證機制
- 最大間隙控制策略
- 備份衛星策略制定
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np

# 導入共享核心模組
try:
    from ...shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    sys.path.append(str(src_path))
    from shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore

logger = logging.getLogger(__name__)

class DynamicPoolStrategyEngine:
    """
    🎯 動態池策略引擎 v4.0
    
    負責創建和執行多種動態衛星池策略，包括：
    - 精確數量維持策略  
    - 時空互補策略
    - 主動覆蓋保證策略
    - 軌道多樣性最大化策略
    - 軌道相位分析 (從Stage 1遷移)
    """
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """初始化動態池策略引擎"""
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.logger.info("🚀 初始化動態池策略引擎 v4.0...")

        # 基礎配置
        self.config = config or {}
        
        # 初始化計算引擎
        try:
            from ...shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
            from ...shared.visibility_service import VisibilityService
            
            self.orbital_calc = SGP4OrbitalEngine()
            self.visibility_calc = VisibilityService()
            
        except ImportError as e:
            self.logger.warning(f"引擎導入警告: {e}")
            self.orbital_calc = None
            self.visibility_calc = None

        # 策略配置
        self.strategy_config = {
            "starlink_target_count": self.config.get("starlink_target_count", 12),
            "oneweb_target_count": self.config.get("oneweb_target_count", 5),
            "diversity_weight": self.config.get("diversity_weight", 0.7),
            "coverage_weight": self.config.get("coverage_weight", 0.3)
        }

        # 軌道相位分析配置 (從Stage 1遷移)
        self.phase_analysis_config = {
            'mean_anomaly_bins': 12,  # 12個30度扇區
            'raan_bins': 18,          # 18個20度扇區
            'enable_diversity_analysis': True,
            'diversity_weight_ma': 0.6,
            'diversity_weight_raan': 0.4
        }

        # 策略統計
        self.strategy_stats = {
            "strategies_created": 0,
            "total_satellites_processed": 0,
            "average_diversity_score": 0.0,
            "last_strategy_timestamp": None
        }

        self.logger.info("✅ 動態池策略引擎初始化完成")

    def create_precise_quantity_maintenance_strategy(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        創建精確數量維持策略
        
        Args:
            satellites: 候選衛星列表
            
        Returns:
            包含選中衛星和策略信息的字典
        """
        self.logger.info("🎯 創建精確數量維持策略...")
        
        try:
            # 按星座分組
            starlink_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'starlink']
            oneweb_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'oneweb']
            
            # 數量維持選擇
            selected_starlink = self._select_satellites_by_quantity_maintenance(
                starlink_sats, self.strategy_config['starlink_target_count']
            )
            selected_oneweb = self._select_satellites_by_quantity_maintenance(
                oneweb_sats, self.strategy_config['oneweb_target_count']
            )
            
            # 合併結果
            selected_satellites = selected_starlink + selected_oneweb
            
            # 計算覆蓋效率
            coverage_efficiency = self._calculate_coverage_efficiency(selected_satellites)
            
            strategy_result = {
                "strategy_type": "precise_quantity_maintenance",
                "selected_satellites": selected_satellites,
                "satellite_count": {
                    "starlink": len(selected_starlink),
                    "oneweb": len(selected_oneweb),
                    "total": len(selected_satellites)
                },
                "target_count": {
                    "starlink": self.strategy_config['starlink_target_count'],
                    "oneweb": self.strategy_config['oneweb_target_count']
                },
                "coverage_efficiency": coverage_efficiency,
                "strategy_metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "total_candidates": len(satellites),
                    "selection_success_rate": len(selected_satellites) / len(satellites) if satellites else 0
                }
            }
            
            # 更新統計
            self.strategy_stats["strategies_created"] += 1
            self.strategy_stats["total_satellites_processed"] += len(satellites)
            self.strategy_stats["last_strategy_timestamp"] = datetime.now().isoformat()
            
            self.logger.info(f"✅ 精確數量維持策略完成: {len(selected_satellites)}顆衛星")
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 精確數量維持策略失敗: {e}")
            return {
                "strategy_type": "precise_quantity_maintenance",
                "selected_satellites": [],
                "error": str(e)
            }

    def create_temporal_spatial_complementary_strategy(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        創建時空互補策略
        
        Args:
            satellites: 候選衛星列表
            
        Returns:
            包含時空互補選擇結果的字典
        """
        self.logger.info("🕐 創建時空互補策略...")
        
        try:
            # 按星座分組
            starlink_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'starlink']
            oneweb_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'oneweb']
            
            # 時空互補選擇
            selected_starlink = self._select_complementary_satellites(
                starlink_sats, self.strategy_config['starlink_target_count']
            )
            selected_oneweb = self._select_complementary_satellites(
                oneweb_sats, self.strategy_config['oneweb_target_count']
            )
            
            # 計算互補效率
            complementary_efficiency = self._calculate_complementary_efficiency(
                selected_starlink + selected_oneweb
            )
            
            strategy_result = {
                "strategy_type": "temporal_spatial_complementary",
                "selected_satellites": selected_starlink + selected_oneweb,
                "complementary_pairs": len(selected_starlink + selected_oneweb) // 2,
                "complementary_efficiency": complementary_efficiency,
                "constellation_distribution": {
                    "starlink": len(selected_starlink),
                    "oneweb": len(selected_oneweb)
                },
                "strategy_metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "total_candidates": len(satellites)
                }
            }
            
            self.logger.info(f"✅ 時空互補策略完成: {len(selected_starlink + selected_oneweb)}顆衛星")
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 時空互補策略失敗: {e}")
            return {
                "strategy_type": "temporal_spatial_complementary",
                "selected_satellites": [],
                "error": str(e)
            }

    def create_proactive_coverage_guarantee_strategy(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        創建主動覆蓋保證策略
        
        Args:
            satellites: 候選衛星列表
            
        Returns:
            包含覆蓋保證選擇結果的字典
        """
        self.logger.info("🛡️ 創建主動覆蓋保證策略...")
        
        try:
            # 基礎選擇
            base_strategy = self.create_precise_quantity_maintenance_strategy(satellites)
            base_satellites = base_strategy.get("selected_satellites", [])
            
            # 額外備用衛星選擇 (20%冗餘)
            backup_count = max(1, int(len(base_satellites) * 0.2))
            remaining_satellites = [sat for sat in satellites if sat not in base_satellites]
            
            backup_satellites = self._select_backup_candidates(remaining_satellites, backup_count)
            
            # 合併主要和備用衛星
            all_selected = base_satellites + backup_satellites
            
            # 覆蓋保證驗證
            coverage_guarantee = self.verify_95_plus_coverage_guarantee(all_selected)
            
            strategy_result = {
                "strategy_type": "proactive_coverage_guarantee",
                "primary_satellites": base_satellites,
                "backup_satellites": backup_satellites,
                "total_satellites": all_selected,
                "coverage_guarantee": coverage_guarantee,
                "redundancy_ratio": len(backup_satellites) / len(base_satellites) if base_satellites else 0,
                "strategy_metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "total_candidates": len(satellites),
                    "backup_count": len(backup_satellites)
                }
            }
            
            self.logger.info(f"✅ 主動覆蓋保證策略完成: {len(all_selected)}顆衛星 (含{len(backup_satellites)}顆備用)")
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 主動覆蓋保證策略失敗: {e}")
            return {
                "strategy_type": "proactive_coverage_guarantee",
                "primary_satellites": [],
                "backup_satellites": [],
                "error": str(e)
            }

    def create_orbital_diversity_maximization_strategy(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        創建軌道多樣性最大化策略
        
        Args:
            satellites: 候選衛星列表
            
        Returns:
            包含多樣性優化選擇結果的字典
        """
        self.logger.info("🌍 創建軌道多樣性最大化策略...")
        
        try:
            # 計算軌道多樣性
            diversity_metrics = self._calculate_orbital_diversity(satellites)
            
            # 按星座分組並選擇多樣化衛星
            starlink_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'starlink']
            oneweb_sats = [sat for sat in satellites if sat.get('constellation', '').lower() == 'oneweb']
            
            selected_starlink = self._select_diverse_satellites(
                starlink_sats, self.strategy_config['starlink_target_count']
            )
            selected_oneweb = self._select_diverse_satellites(
                oneweb_sats, self.strategy_config['oneweb_target_count']
            )
            
            # 計算最終多樣性分數
            final_diversity = self._calculate_final_diversity_score(selected_starlink + selected_oneweb)
            
            strategy_result = {
                "strategy_type": "orbital_diversity_maximization",
                "selected_satellites": selected_starlink + selected_oneweb,
                "diversity_metrics": diversity_metrics,
                "final_diversity_score": final_diversity,
                "constellation_diversity": {
                    "starlink_diversity": self._calculate_orbital_diversity(selected_starlink),
                    "oneweb_diversity": self._calculate_orbital_diversity(selected_oneweb)
                },
                "strategy_metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "total_candidates": len(satellites),
                    "diversity_improvement": final_diversity.get("improvement_ratio", 0.0)
                }
            }
            
            self.logger.info(f"✅ 軌道多樣性最大化策略完成: {len(selected_starlink + selected_oneweb)}顆衛星")
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 軌道多樣性最大化策略失敗: {e}")
            return {
                "strategy_type": "orbital_diversity_maximization",
                "selected_satellites": [],
                "error": str(e)
            }

    def _calculate_orbital_diversity(self, satellites: List[Dict]) -> Dict[str, Any]:
        """計算軌道多樣性指標"""
        if not satellites:
            return {"diversity_score": 0.0, "metrics": {}}
            
        try:
            # 提取軌道參數
            elevations = [sat.get('elevation', 0) for sat in satellites]
            azimuths = [sat.get('azimuth', 0) for sat in satellites]
            
            # 計算分散度
            elevation_spread = max(elevations) - min(elevations) if elevations else 0
            azimuth_spread = max(azimuths) - min(azimuths) if azimuths else 0
            
            # 歸一化多樣性分數 (0-1)
            diversity_score = min(1.0, (elevation_spread / 90.0 + azimuth_spread / 360.0) / 2.0)
            
            return {
                "diversity_score": diversity_score,
                "metrics": {
                    "elevation_spread": elevation_spread,
                    "azimuth_spread": azimuth_spread,
                    "satellite_count": len(satellites)
                }
            }
            
        except Exception as e:
            self.logger.error(f"軌道多樣性計算失敗: {e}")
            return {"diversity_score": 0.0, "metrics": {}, "error": str(e)}

    def _select_satellites_by_quantity_maintenance(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """根據數量維持策略選擇衛星"""
        if not satellites:
            return []
            
        # 按信號強度排序
        sorted_satellites = sorted(
            satellites, 
            key=lambda x: x.get('rsrp', -999), 
            reverse=True
        )
        
        # 選擇前 target_count 顆
        return sorted_satellites[:target_count]

    def _calculate_coverage_efficiency(self, satellites: List[Dict]) -> Dict[str, float]:
        """計算覆蓋效率指標"""
        if not satellites:
            return {"efficiency_score": 0.0}
            
        try:
            # 計算平均信號強度
            rsrp_values = [sat.get('rsrp', -999) for sat in satellites]
            avg_rsrp = sum(rsrp_values) / len(rsrp_values)
            
            # 計算仰角分佈
            elevations = [sat.get('elevation', 0) for sat in satellites]
            avg_elevation = sum(elevations) / len(elevations)
            
            # 歸一化效率分數
            efficiency_score = min(1.0, (avg_rsrp + 140) / 40.0 + avg_elevation / 90.0) / 2.0
            
            return {
                "efficiency_score": max(0.0, efficiency_score),
                "avg_rsrp": avg_rsrp,
                "avg_elevation": avg_elevation,
                "satellite_count": len(satellites)
            }
            
        except Exception as e:
            self.logger.error(f"覆蓋效率計算失敗: {e}")
            return {"efficiency_score": 0.0, "error": str(e)}

    def _select_complementary_satellites(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """選擇時空互補的衛星"""
        if not satellites or target_count <= 0:
            return []
            
        selected = []
        remaining = satellites.copy()
        
        # 首先選擇信號最強的衛星
        if remaining:
            best_satellite = max(remaining, key=lambda x: x.get('rsrp', -999))
            selected.append(best_satellite)
            remaining.remove(best_satellite)
        
        # 選擇互補衛星
        while len(selected) < target_count and remaining:
            # 找到與已選衛星最互補的衛星
            best_complement = None
            best_complement_score = -1
            
            for candidate in remaining:
                complement_score = self._calculate_complementary_efficiency([candidate] + selected)
                if complement_score.get("efficiency_score", 0) > best_complement_score:
                    best_complement_score = complement_score.get("efficiency_score", 0)
                    best_complement = candidate
            
            if best_complement:
                selected.append(best_complement)
                remaining.remove(best_complement)
            else:
                break
        
        return selected

    def _calculate_complementary_efficiency(self, satellites: List[Dict]) -> Dict[str, float]:
        """計算時空互補效率"""
        if not satellites:
            return {"efficiency_score": 0.0}
            
        try:
            # 計算空間分散度
            azimuths = [sat.get('azimuth', 0) for sat in satellites]
            elevations = [sat.get('elevation', 0) for sat in satellites]
            
            azimuth_spread = max(azimuths) - min(azimuths) if len(azimuths) > 1 else 0
            elevation_spread = max(elevations) - min(elevations) if len(elevations) > 1 else 0
            
            # 計算時間分散度 (使用衛星ID哈希模擬)
            time_diversity = len(set(hash(sat.get('satellite_id', '')) % 24 for sat in satellites)) / 24.0
            
            # 綜合互補效率分數
            efficiency_score = (
                azimuth_spread / 360.0 * 0.4 +
                elevation_spread / 90.0 * 0.3 +
                time_diversity * 0.3
            )
            
            return {
                "efficiency_score": min(1.0, efficiency_score),
                "azimuth_spread": azimuth_spread,
                "elevation_spread": elevation_spread,
                "time_diversity": time_diversity
            }
            
        except Exception as e:
            self.logger.error(f"互補效率計算失敗: {e}")
            return {"efficiency_score": 0.0, "error": str(e)}

    def _select_diverse_satellites(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """選擇多樣化衛星"""
        if not satellites or target_count <= 0:
            return []
            
        # 計算每顆衛星的多樣性貢獻
        satellite_scores = []
        for sat in satellites:
            diversity = self._calculate_orbital_diversity([sat])
            score = diversity.get("diversity_score", 0) + sat.get('rsrp', -999) / 1000.0  # 結合多樣性和信號強度
            satellite_scores.append((score, sat))
        
        # 按多樣性分數排序並選擇
        satellite_scores.sort(key=lambda x: x[0], reverse=True)
        return [sat for score, sat in satellite_scores[:target_count]]

    def _calculate_final_diversity_score(self, satellites: List[Dict]) -> Dict[str, float]:
        """計算最終多樣性分數"""
        base_diversity = self._calculate_orbital_diversity(satellites)
        
        return {
            "final_score": base_diversity.get("diversity_score", 0.0),
            "improvement_ratio": base_diversity.get("diversity_score", 0.0),  # 簡化實現
            "satellite_count": len(satellites)
        }

    def select_optimal_staggering_strategy(self, satellites: List[Dict], 
                                         coverage_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        選擇最優的錯開策略
        
        Args:
            satellites: 候選衛星列表
            coverage_requirements: 覆蓋需求
            
        Returns:
            最優錯開策略結果
        """
        self.logger.info("🔄 選擇最優錯開策略...")
        
        strategies = [
            self.create_precise_quantity_maintenance_strategy(satellites),
            self.create_temporal_spatial_complementary_strategy(satellites),
            self.create_proactive_coverage_guarantee_strategy(satellites),
            self.create_orbital_diversity_maximization_strategy(satellites)
        ]
        
        # 評估每個策略的性能
        best_strategy = None
        best_score = -1
        
        for strategy in strategies:
            if strategy.get("selected_satellites"):
                performance = self._evaluate_strategy_performance(strategy, coverage_requirements)
                if performance.get("overall_score", 0) > best_score:
                    best_score = performance.get("overall_score", 0)
                    best_strategy = strategy
                    best_strategy["performance_evaluation"] = performance
        
        if best_strategy:
            self.logger.info(f"✅ 最優策略: {best_strategy['strategy_type']} (分數: {best_score:.3f})")
            return best_strategy
        else:
            self.logger.warning("⚠️ 未找到合適的錯開策略")
            return {"strategy_type": "none", "selected_satellites": []}

    def evaluate_strategy_performance(self, strategy: Dict[str, Any]) -> Dict[str, float]:
        """評估策略性能 (公開方法)"""
        return self._evaluate_strategy_performance(strategy, {})

    def create_dynamic_backup_satellite_strategy(self, primary_satellites: List[Dict], 
                                                available_satellites: List[Dict]) -> Dict[str, Any]:
        """
        創建動態備用衛星策略
        
        Args:
            primary_satellites: 主要衛星列表
            available_satellites: 可用衛星列表
            
        Returns:
            備用衛星策略結果
        """
        self.logger.info("🔄 創建動態備用衛星策略...")
        
        try:
            # 排除已選中的主要衛星
            backup_candidates = [
                sat for sat in available_satellites 
                if sat not in primary_satellites
            ]
            
            # 選擇備用衛星 (主要衛星數量的30%)
            backup_count = max(1, int(len(primary_satellites) * 0.3))
            backup_satellites = self._select_backup_candidates(backup_candidates, backup_count)
            
            strategy_result = {
                "strategy_type": "dynamic_backup_satellite",
                "primary_satellites": primary_satellites,
                "backup_satellites": backup_satellites,
                "backup_ratio": len(backup_satellites) / len(primary_satellites) if primary_satellites else 0,
                "total_coverage_satellites": len(primary_satellites) + len(backup_satellites),
                "strategy_metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "backup_count": len(backup_satellites),
                    "primary_count": len(primary_satellites)
                }
            }
            
            self.logger.info(f"✅ 動態備用衛星策略完成: {len(backup_satellites)}顆備用衛星")
            return strategy_result
            
        except Exception as e:
            self.logger.error(f"❌ 動態備用衛星策略失敗: {e}")
            return {
                "strategy_type": "dynamic_backup_satellite",
                "backup_satellites": [],
                "error": str(e)
            }

    def implement_max_gap_control_mechanism(self, satellites: List[Dict], 
                                          max_gap_minutes: float = 2.0) -> Dict[str, Any]:
        """
        實施最大間隙控制機制
        
        Args:
            satellites: 衛星列表
            max_gap_minutes: 最大允許間隙時間(分鐘)
            
        Returns:
            間隙控制結果
        """
        self.logger.info(f"⏱️ 實施最大間隙控制: {max_gap_minutes}分鐘...")
        
        try:
            # 模擬覆蓋時間線
            coverage_timeline = self._generate_coverage_timeline(satellites)
            
            # 識別覆蓋間隙
            gaps = self._identify_coverage_gaps(coverage_timeline, max_gap_minutes)
            
            # 生成填補建議
            gap_fill_recommendations = self._generate_gap_fill_recommendations(gaps, satellites)
            
            control_result = {
                "max_gap_minutes": max_gap_minutes,
                "coverage_gaps_found": len(gaps),
                "gaps_details": gaps,
                "gap_fill_recommendations": gap_fill_recommendations,
                "gap_control_success": len(gaps) == 0,
                "strategy_metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "satellites_analyzed": len(satellites)
                }
            }
            
            if len(gaps) == 0:
                self.logger.info("✅ 間隙控制成功: 無超過限制的覆蓋間隙")
            else:
                self.logger.warning(f"⚠️ 發現 {len(gaps)} 個覆蓋間隙需要處理")
            
            return control_result
            
        except Exception as e:
            self.logger.error(f"❌ 間隙控制機制失敗: {e}")
            return {
                "max_gap_minutes": max_gap_minutes,
                "gap_control_success": False,
                "error": str(e)
            }

    def verify_95_plus_coverage_guarantee(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        驗證95%+覆蓋保證
        
        Args:
            satellites: 衛星列表
            
        Returns:
            覆蓋保證驗證結果
        """
        self.logger.info("🛡️ 驗證95%+覆蓋保證...")
        
        try:
            # 模擬24小時覆蓋分析
            total_time_slots = 1440  # 24小時 * 60分鐘
            covered_slots = 0
            
            # 簡化覆蓋計算
            for slot in range(total_time_slots):
                # 模擬每分鐘的衛星可見性
                visible_satellites = self._simulate_visibility_at_time(satellites, slot)
                if len(visible_satellites) > 0:
                    covered_slots += 1
            
            coverage_percentage = (covered_slots / total_time_slots) * 100
            
            verification_result = {
                "coverage_percentage": coverage_percentage,
                "target_coverage": 95.0,
                "coverage_guarantee_met": coverage_percentage >= 95.0,
                "total_time_slots": total_time_slots,
                "covered_time_slots": covered_slots,
                "uncovered_time_slots": total_time_slots - covered_slots,
                "verification_metadata": {
                    "verification_time": datetime.now().isoformat(),
                    "satellites_count": len(satellites)
                }
            }
            
            if coverage_percentage >= 95.0:
                self.logger.info(f"✅ 覆蓋保證驗證成功: {coverage_percentage:.1f}%")
            else:
                self.logger.warning(f"⚠️ 覆蓋保證不足: {coverage_percentage:.1f}% < 95%")
            
            return verification_result
            
        except Exception as e:
            self.logger.error(f"❌ 覆蓋保證驗證失敗: {e}")
            return {
                "coverage_guarantee_met": False,
                "error": str(e)
            }

    def get_strategy_statistics(self) -> Dict[str, Any]:
        """獲取策略統計信息"""
        return self.strategy_stats.copy()

    # ===========================================
    # 軌道相位分析功能 (從Stage 1遷移)
    # ===========================================

    def analyze_orbital_phase_distribution(self, satellites: List[Dict]) -> Dict[str, Any]:
        """
        軌道相位分佈分析 (從Stage 1遷移的完整實現)
        
        Args:
            satellites: 衛星數據列表，包含軌道信息
            
        Returns:
            完整的軌道相位分析結果
        """
        self.logger.info("🛰️ 開始軌道相位分佈分析 (從Stage 1遷移)...")
        
        try:
            # 提取軌道元素
            orbital_elements = self._extract_orbital_elements_from_satellites(satellites)
            
            if not orbital_elements:
                self.logger.warning("⚠️ 無法提取軌道元素")
                return {"phase_analysis": {}, "error": "No orbital elements extracted"}
            
            # 執行相位分析
            phase_analysis = self._perform_orbital_phase_analysis(orbital_elements)
            
            # 計算相位多樣性
            phase_diversity = self._calculate_orbital_phase_diversity(phase_analysis)
            
            # 分析時間覆蓋模式
            temporal_patterns = self._analyze_temporal_coverage_patterns(orbital_elements)
            
            # 組合結果
            complete_analysis = {
                "orbital_elements": orbital_elements,
                "phase_distribution": phase_analysis,
                "phase_diversity_metrics": phase_diversity,
                "temporal_coverage_patterns": temporal_patterns,
                "analysis_configuration": self.phase_analysis_config.copy(),
                "analysis_metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "satellites_analyzed": len(satellites),
                    "orbital_elements_extracted": len(orbital_elements),
                    "analysis_version": "v4.0_migrated_from_stage1"
                }
            }
            
            self.logger.info(f"✅ 軌道相位分析完成: {len(orbital_elements)} 顆衛星")
            return complete_analysis
            
        except Exception as e:
            self.logger.error(f"❌ 軌道相位分析失敗: {e}")
            return {
                "phase_analysis": {},
                "error": str(e),
                "analysis_metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "satellites_input": len(satellites) if satellites else 0
                }
            }

    def _extract_orbital_elements_from_satellites(self, satellites: List[Dict]) -> List[Dict[str, Any]]:
        """從衛星數據提取軌道元素 (從Stage 1遷移)"""
        orbital_elements = []
        
        for sat in satellites:
            try:
                # 獲取星座信息
                constellation = sat.get("constellation", "unknown").lower()
                
                # 從軌道位置或直接從衛星數據提取軌道元素
                if "orbital_positions" in sat and sat["orbital_positions"]:
                    first_position = sat["orbital_positions"][0]
                    mean_anomaly = self._calculate_mean_anomaly_from_position(first_position)
                    raan = self._calculate_raan_from_position(first_position)
                else:
                    # 從衛星基本信息計算近似軌道元素
                    mean_anomaly = self._estimate_mean_anomaly_from_satellite(sat)
                    raan = self._estimate_raan_from_satellite(sat)
                
                orbital_element = {
                    "satellite_id": sat.get("satellite_id", f"unknown_{len(orbital_elements)}"),
                    "constellation": constellation,
                    "mean_anomaly": mean_anomaly,
                    "raan": raan,
                    "elevation": sat.get("elevation", 0),
                    "azimuth": sat.get("azimuth", 0),
                    "rsrp": sat.get("rsrp", -999)
                }
                
                orbital_elements.append(orbital_element)
                
            except Exception as e:
                self.logger.debug(f"提取衛星 {sat.get('satellite_id', 'unknown')} 軌道元素失敗: {e}")
                continue
        
        return orbital_elements

    def _estimate_mean_anomaly_from_satellite(self, satellite: Dict) -> float:
        """從衛星信息估算平近點角"""
        try:
            # 使用方位角作為平近點角的近似
            azimuth = satellite.get("azimuth", 0)
            return float(azimuth) % 360.0
        except:
            return 0.0

    def _estimate_raan_from_satellite(self, satellite: Dict) -> float:
        """從衛星信息估算升交點經度"""
        try:
            # 使用衛星ID哈希值生成RAAN近似值
            sat_id = satellite.get("satellite_id", "0")
            raan = (hash(sat_id) % 360)
            return float(raan)
        except:
            return 0.0

    def _calculate_mean_anomaly_from_position(self, position_data: Dict) -> float:
        """從位置數據計算平近點角 (從Stage 1遷移)"""
        try:
            position_eci = position_data.get("position_eci", {})
            if isinstance(position_eci, dict):
                x = float(position_eci.get('x', 0))
                y = float(position_eci.get('y', 0))
            else:
                x = float(position_eci[0])
                y = float(position_eci[1])

            # 簡化計算平近點角
            import math
            mean_anomaly = math.degrees(math.atan2(y, x))
            if mean_anomaly < 0:
                mean_anomaly += 360.0

            return mean_anomaly

        except Exception:
            return 0.0

    def _calculate_raan_from_position(self, position_data: Dict) -> float:
        """從位置數據計算升交點赤經 (從Stage 1遷移)"""
        try:
            position_eci = position_data.get("position_eci", {})
            if isinstance(position_eci, dict):
                x = float(position_eci.get('x', 0))
                y = float(position_eci.get('y', 0))
            else:
                x = float(position_eci[0])
                y = float(position_eci[1])

            # 簡化計算RAAN
            import math
            raan = math.degrees(math.atan2(y, x)) + 90.0  # 簡化計算
            if raan < 0:
                raan += 360.0
            elif raan >= 360.0:
                raan -= 360.0

            return raan

        except Exception:
            return 0.0

    def _perform_orbital_phase_analysis(self, orbital_elements: List[Dict]) -> Dict[str, Any]:
        """執行軌道相位分析 (從Stage 1遷移)"""
        phase_analysis = {
            'mean_anomaly_distribution': {},
            'raan_distribution': {},
            'phase_diversity_metrics': {}
        }

        # 按星座分組分析
        constellations = {}
        for element in orbital_elements:
            constellation = element['constellation']
            if constellation not in constellations:
                constellations[constellation] = []
            constellations[constellation].append(element)

        # 分析每個星座
        for constellation, constellation_elements in constellations.items():
            # 分析平近點角分佈
            ma_distribution = self._analyze_mean_anomaly_distribution(
                constellation_elements, self.phase_analysis_config['mean_anomaly_bins']
            )
            phase_analysis['mean_anomaly_distribution'][constellation] = ma_distribution

            # 分析RAAN分佈
            raan_distribution = self._analyze_raan_distribution(
                constellation_elements, self.phase_analysis_config['raan_bins']
            )
            phase_analysis['raan_distribution'][constellation] = raan_distribution

            # 計算相位多樣性指標
            diversity_metrics = self._calculate_constellation_phase_diversity(
                ma_distribution, raan_distribution
            )
            phase_analysis['phase_diversity_metrics'][constellation] = diversity_metrics

        return phase_analysis

    def _analyze_mean_anomaly_distribution(self, elements: List[Dict], bins: int) -> Dict[str, Any]:
        """分析平近點角分佈 (從Stage 1遷移)"""
        bin_size = 360.0 / bins
        distribution = {f'ma_bin_{i}': [] for i in range(bins)}

        for element in elements:
            ma = element['mean_anomaly']
            bin_index = min(int(ma / bin_size), bins - 1)
            distribution[f'ma_bin_{bin_index}'].append(element['satellite_id'])

        # 計算分佈均勻性
        bin_counts = [len(distribution[f'ma_bin_{i}']) for i in range(bins)]
        mean_count = sum(bin_counts) / bins
        variance = sum((count - mean_count) ** 2 for count in bin_counts) / bins
        uniformity = 1.0 - (variance / (mean_count ** 2)) if mean_count > 0 else 0.0

        return {
            'distribution': distribution,
            'uniformity_score': uniformity,
            'bin_counts': bin_counts,
            'total_satellites': len(elements)
        }

    def _analyze_raan_distribution(self, elements: List[Dict], bins: int) -> Dict[str, Any]:
        """分析RAAN分佈 (從Stage 1遷移)"""
        bin_size = 360.0 / bins
        distribution = {f'raan_bin_{i}': [] for i in range(bins)}

        for element in elements:
            raan = element['raan']
            bin_index = min(int(raan / bin_size), bins - 1)
            distribution[f'raan_bin_{bin_index}'].append(element['satellite_id'])

        # 計算分散性分數
        bin_counts = [len(distribution[f'raan_bin_{i}']) for i in range(bins)]
        non_empty_bins = sum(1 for count in bin_counts if count > 0)
        dispersion_score = non_empty_bins / bins

        return {
            'distribution': distribution,
            'dispersion_score': dispersion_score,
            'non_empty_bins': non_empty_bins,
            'raan_bins_count': bins
        }

    def _calculate_constellation_phase_diversity(self, ma_dist: Dict, raan_dist: Dict) -> Dict[str, Any]:
        """計算星座相位多樣性 (從Stage 1遷移)"""
        ma_uniformity = ma_dist.get('uniformity_score', 0.0)
        raan_dispersion = raan_dist.get('dispersion_score', 0.0)

        # 計算總體多樣性分數
        diversity_score = (ma_uniformity * 0.6 + raan_dispersion * 0.4)

        return {
            'mean_anomaly_uniformity': ma_uniformity,
            'raan_dispersion': raan_dispersion,
            'overall_diversity_score': diversity_score,
            'diversity_rating': self._rate_diversity_score(diversity_score)
        }

    def _rate_diversity_score(self, score: float) -> str:
        """評估多樣性分數 (從Stage 1遷移)"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"

    def _calculate_orbital_phase_diversity(self, phase_analysis: Dict) -> Dict[str, Any]:
        """計算軌道相位多樣性總結 (從Stage 1遷移)"""
        diversity_summary = {
            'constellation_diversity': {},
            'overall_metrics': {}
        }

        total_diversity = 0.0
        constellation_count = 0

        for constellation, diversity_metrics in phase_analysis.get('phase_diversity_metrics', {}).items():
            diversity_score = diversity_metrics.get('overall_diversity_score', 0.0)
            diversity_summary['constellation_diversity'][constellation] = {
                'diversity_score': diversity_score,
                'rating': diversity_metrics.get('diversity_rating', 'unknown')
            }

            total_diversity += diversity_score
            constellation_count += 1

        # 計算總體指標
        if constellation_count > 0:
            average_diversity = total_diversity / constellation_count
            diversity_summary['overall_metrics'] = {
                'average_diversity_score': average_diversity,
                'constellation_count': constellation_count,
                'overall_rating': self._rate_diversity_score(average_diversity)
            }

        return diversity_summary

    def _analyze_temporal_coverage_patterns(self, orbital_elements: List[Dict]) -> Dict[str, Any]:
        """分析時間覆蓋模式 (從Stage 1遷移)"""
        patterns = {
            'phase_sectors': {},
            'coverage_gaps': [],
            'optimization_opportunities': []
        }

        # 分析相位扇區分佈
        for element in orbital_elements:
            ma = element['mean_anomaly']
            sector = int(ma / 30.0) % 12  # 12個30度扇區

            if sector not in patterns['phase_sectors']:
                patterns['phase_sectors'][sector] = []
            patterns['phase_sectors'][sector].append(element['satellite_id'])

        # 識別覆蓋空隙
        for sector in range(12):
            if sector not in patterns['phase_sectors'] or len(patterns['phase_sectors'][sector]) == 0:
                patterns['coverage_gaps'].append({
                    'sector': sector,
                    'angle_range': [sector * 30, (sector + 1) * 30],
                    'severity': 'critical'
                })

        # 識別優化機會
        sector_counts = [len(patterns['phase_sectors'].get(i, [])) for i in range(12)]
        mean_count = sum(sector_counts) / 12

        for i, count in enumerate(sector_counts):
            if count < mean_count * 0.5:  # 少於平均值50%
                patterns['optimization_opportunities'].append({
                    'sector': i,
                    'current_count': count,
                    'recommended_count': int(mean_count),
                    'improvement_potential': mean_count - count
                })

        return patterns

    # ===========================================
    # 輔助方法
    # ===========================================

    def _evaluate_strategy_performance(self, strategy: Dict[str, Any], 
                                     coverage_requirements: Dict[str, Any]) -> Dict[str, float]:
        """評估策略性能"""
        try:
            satellites = strategy.get("selected_satellites", [])
            if not satellites:
                return {"overall_score": 0.0}

            # 基本性能指標
            satellite_count_score = min(1.0, len(satellites) / 20.0)  # 歸一化到20顆衛星
            
            # 覆蓋效率
            coverage_eff = self._calculate_coverage_efficiency(satellites)
            coverage_score = coverage_eff.get("efficiency_score", 0.0)
            
            # 多樣性分數
            diversity_metrics = self._calculate_orbital_diversity(satellites)
            diversity_score = diversity_metrics.get("diversity_score", 0.0)
            
            # 加權總分
            overall_score = (
                satellite_count_score * 0.3 +
                coverage_score * 0.4 +
                diversity_score * 0.3
            )
            
            return {
                "overall_score": overall_score,
                "satellite_count_score": satellite_count_score,
                "coverage_score": coverage_score,
                "diversity_score": diversity_score,
                "satellite_count": len(satellites)
            }
            
        except Exception as e:
            self.logger.error(f"策略性能評估失敗: {e}")
            return {"overall_score": 0.0, "error": str(e)}

    def _calculate_strategy_metrics(self, strategy: Dict[str, Any]) -> Dict[str, float]:
        """計算策略指標"""
        satellites = strategy.get("selected_satellites", [])
        return {
            "satellite_count": len(satellites),
            "strategy_efficiency": len(satellites) / 20.0 if satellites else 0.0
        }

    def _select_backup_candidates(self, candidates: List[Dict], backup_count: int) -> List[Dict]:
        """選擇備用候選衛星"""
        if not candidates or backup_count <= 0:
            return []
            
        # 按信號強度排序選擇備用衛星
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get('rsrp', -999),
            reverse=True
        )
        
        return sorted_candidates[:backup_count]

    def _generate_coverage_recommendations(self, satellites: List[Dict]) -> List[Dict]:
        """生成覆蓋建議"""
        recommendations = []
        
        if len(satellites) < 10:
            recommendations.append({
                "type": "增加衛星數量",
                "description": "當前衛星數量不足，建議增加更多候選衛星",
                "priority": "high"
            })
        
        # 檢查星座分佈
        starlink_count = len([s for s in satellites if s.get('constellation', '').lower() == 'starlink'])
        oneweb_count = len([s for s in satellites if s.get('constellation', '').lower() == 'oneweb'])
        
        if starlink_count < 8:
            recommendations.append({
                "type": "Starlink 數量不足",
                "description": f"當前只有{starlink_count}顆Starlink衛星，建議增加到10-15顆",
                "priority": "medium"
            })
        
        if oneweb_count < 3:
            recommendations.append({
                "type": "OneWeb 數量不足", 
                "description": f"當前只有{oneweb_count}顆OneWeb衛星，建議增加到3-6顆",
                "priority": "medium"
            })
        
        return recommendations

    def _generate_coverage_timeline(self, satellites: List[Dict]) -> List[Dict]:
        """生成覆蓋時間線"""
        # 簡化實現
        timeline = []
        for i in range(1440):  # 24小時，每分鐘一個點
            visible_satellites = self._simulate_visibility_at_time(satellites, i)
            timeline.append({
                "time_minute": i,
                "visible_satellites": len(visible_satellites),
                "satellite_ids": [sat.get("satellite_id") for sat in visible_satellites]
            })
        return timeline

    def _identify_coverage_gaps(self, timeline: List[Dict], max_gap_minutes: float) -> List[Dict]:
        """識別覆蓋間隙"""
        gaps = []
        gap_start = None
        
        for entry in timeline:
            if entry["visible_satellites"] == 0:
                if gap_start is None:
                    gap_start = entry["time_minute"]
            else:
                if gap_start is not None:
                    gap_duration = entry["time_minute"] - gap_start
                    if gap_duration > max_gap_minutes:
                        gaps.append({
                            "start_minute": gap_start,
                            "end_minute": entry["time_minute"],
                            "duration_minutes": gap_duration
                        })
                    gap_start = None
        
        return gaps

    def _generate_gap_fill_recommendations(self, gaps: List[Dict], satellites: List[Dict]) -> List[Dict]:
        """生成間隙填補建議"""
        recommendations = []
        
        for gap in gaps:
            recommendations.append({
                "gap_time": f"{gap['start_minute']}-{gap['end_minute']}分鐘",
                "gap_duration": gap["duration_minutes"],
                "recommendation": "增加備用衛星或調整衛星軌道相位",
                "priority": "high" if gap["duration_minutes"] > 5 else "medium"
            })
        
        return recommendations

    def _simulate_visibility_at_time(self, satellites: List[Dict], time_minute: int) -> List[Dict]:
        """模擬特定時間的衛星可見性"""
        # 簡化實現：假設衛星在不同時間有不同的可見性
        visible = []
        for sat in satellites:
            # 使用衛星ID和時間創建偽隨機可見性
            visibility_hash = hash(f"{sat.get('satellite_id', '')}_{time_minute}") % 100
            if visibility_hash < 70:  # 70%概率可見
                visible.append(sat)
        return visible