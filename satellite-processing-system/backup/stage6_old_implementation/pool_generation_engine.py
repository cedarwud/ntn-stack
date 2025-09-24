#!/usr/bin/env python3
"""
Pool Generation Engine - 衛星池生成引擎

專責衛星候選池的生成和管理：
- 基於策略生成候選池
- RL驅動的衛星池選擇
- 星座分佈分析
- 候選衛星提取和處理

從 DynamicPoolOptimizerEngine 中拆分出來，專注於池生成功能
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class SatelliteCandidate:
    """衛星候選者數據結構"""
    satellite_id: str
    constellation: str
    rsrp: float
    elevation: float
    distance: float
    coverage_score: float
    handover_potential: float
    rl_score: float = 0.0

class PoolGenerationEngine:
    """
    衛星池生成引擎

    專責各種策略的衛星候選池生成
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化生成引擎"""
        self.logger = logging.getLogger(f"{__name__}.PoolGenerationEngine")
        self.config = config or {}

        self.logger.info("✅ Pool Generation Engine 初始化完成")

    def generate_candidate_pools(self, satellite_candidates: List[SatelliteCandidate],
                               target_count: int, strategies: List[str]) -> List[Dict[str, Any]]:
        """
        生成多個候選衛星池

        Args:
            satellite_candidates: 衛星候選者列表
            target_count: 目標衛星數量
            strategies: 生成策略列表

        Returns:
            候選池配置列表
        """
        try:
            pools = []

            for strategy in strategies:
                self.logger.info(f"🔄 使用策略生成候選池: {strategy}")

                pool_config = self._generate_pool_by_strategy(
                    satellite_candidates, target_count, strategy
                )

                if pool_config:
                    pools.append(pool_config)
                    self.logger.info(f"✅ 策略 {strategy} 生成候選池成功")
                else:
                    self.logger.warning(f"⚠️ 策略 {strategy} 生成候選池失敗")

            self.logger.info(f"✅ 總共生成 {len(pools)} 個候選池")
            return pools

        except Exception as e:
            self.logger.error(f"❌ 候選池生成失敗: {e}")
            return []

    def _generate_pool_by_strategy(self, candidates: List[SatelliteCandidate],
                                 target_count: int, strategy: str) -> Optional[Dict[str, Any]]:
        """根據策略生成候選池"""
        try:
            if strategy == "rl_driven":
                return self._generate_rl_driven_pool(candidates, target_count)
            elif strategy == "gap_filling":
                return self._generate_gap_filling_pool(candidates, target_count)
            elif strategy == "balanced":
                return self._generate_balanced_pool(candidates, target_count)
            elif strategy == "high_quality":
                return self._generate_high_quality_pool(candidates, target_count)
            else:
                return self._generate_fallback_pool(candidates, target_count)

        except Exception as e:
            self.logger.error(f"❌ 策略 {strategy} 執行失敗: {e}")
            return None

    def _generate_rl_driven_pool(self, candidates: List[SatelliteCandidate],
                               target_count: int) -> Dict[str, Any]:
        """生成RL驅動的衛星池"""
        try:
            # 計算每個候選者的RL分數
            for candidate in candidates:
                candidate.rl_score = self._calculate_rl_score(candidate)

            # 按RL分數排序並選擇頂部候選者
            sorted_candidates = sorted(candidates, key=lambda x: x.rl_score, reverse=True)
            selected = sorted_candidates[:target_count]

            return {
                "strategy": "rl_driven",
                "satellites": selected,
                "total_count": len(selected),
                "avg_rl_score": np.mean([s.rl_score for s in selected]),
                "configuration_score": self._calculate_pool_score(selected)
            }

        except Exception as e:
            self.logger.error(f"❌ RL驅動池生成失敗: {e}")
            return {}

    def _generate_gap_filling_pool(self, candidates: List[SatelliteCandidate],
                                 target_count: int) -> Dict[str, Any]:
        """生成填補覆蓋空隙的衛星池"""
        try:
            # 選擇覆蓋分數高且位置分散的衛星
            gap_filling_satellites = self._select_gap_filling_satellites(
                candidates, target_count
            )

            return {
                "strategy": "gap_filling",
                "satellites": gap_filling_satellites,
                "total_count": len(gap_filling_satellites),
                "avg_coverage_score": np.mean([s.coverage_score for s in gap_filling_satellites]),
                "configuration_score": self._calculate_pool_score(gap_filling_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 填補空隙池生成失敗: {e}")
            return {}

    def _generate_balanced_pool(self, candidates: List[SatelliteCandidate],
                              target_count: int) -> Dict[str, Any]:
        """生成平衡的衛星池"""
        try:
            balanced_satellites = self._select_balanced_satellites(candidates, target_count)

            return {
                "strategy": "balanced",
                "satellites": balanced_satellites,
                "total_count": len(balanced_satellites),
                "constellation_balance": self._calculate_constellation_balance(balanced_satellites),
                "configuration_score": self._calculate_pool_score(balanced_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 平衡池生成失敗: {e}")
            return {}

    def _generate_high_quality_pool(self, candidates: List[SatelliteCandidate],
                                  target_count: int) -> Dict[str, Any]:
        """生成高品質衛星池"""
        try:
            # 按RSRP排序選擇最佳信號品質的衛星
            high_quality_satellites = sorted(
                candidates, key=lambda x: x.rsrp, reverse=True
            )[:target_count]

            return {
                "strategy": "high_quality",
                "satellites": high_quality_satellites,
                "total_count": len(high_quality_satellites),
                "avg_rsrp": np.mean([s.rsrp for s in high_quality_satellites]),
                "configuration_score": self._calculate_pool_score(high_quality_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 高品質池生成失敗: {e}")
            return {}

    def _generate_fallback_pool(self, candidates: List[SatelliteCandidate],
                              target_count: int) -> Dict[str, Any]:
        """生成回退衛星池（綜合評分最高的候選者）"""
        try:
            # 計算綜合評分
            for candidate in candidates:
                candidate.overall_score = (
                    candidate.coverage_score * 0.4 +
                    candidate.rsrp / 100.0 * 0.3 +
                    candidate.handover_potential * 0.2 +
                    (100.0 - candidate.elevation) / 100.0 * 0.1
                )

            # 選擇綜合評分最高的候選者
            fallback_satellites = sorted(
                candidates, key=lambda x: x.overall_score, reverse=True
            )[:target_count]

            return {
                "strategy": "fallback",
                "satellites": fallback_satellites,
                "total_count": len(fallback_satellites),
                "avg_overall_score": np.mean([s.overall_score for s in fallback_satellites]),
                "configuration_score": self._calculate_pool_score(fallback_satellites)
            }

        except Exception as e:
            self.logger.error(f"❌ 回退池生成失敗: {e}")
            return {}

    def _select_gap_filling_satellites(self, candidates: List[SatelliteCandidate],
                                     target_count: int) -> List[SatelliteCandidate]:
        """選擇填補覆蓋空隙的衛星"""
        # 基於覆蓋分數和位置分散性選擇
        selected = []
        remaining = candidates.copy()

        while len(selected) < target_count and remaining:
            # 選擇覆蓋分數最高的衛星
            best_candidate = max(remaining, key=lambda x: x.coverage_score)
            selected.append(best_candidate)
            remaining.remove(best_candidate)

            # 移除與已選衛星過於接近的候選者（簡化版本）
            remaining = [c for c in remaining if abs(c.elevation - best_candidate.elevation) > 5.0]

        return selected

    def _select_balanced_satellites(self, candidates: List[SatelliteCandidate],
                                  target_count: int) -> List[SatelliteCandidate]:
        """選擇平衡的衛星組合"""
        try:
            # 分離不同星座的候選者
            starlink_candidates = [c for c in candidates if 'starlink' in c.constellation.lower()]
            oneweb_candidates = [c for c in candidates if 'oneweb' in c.constellation.lower()]

            # 計算平衡的分配比例
            total_starlink = len(starlink_candidates)
            total_oneweb = len(oneweb_candidates)
            total_candidates = total_starlink + total_oneweb

            if total_candidates == 0:
                return []

            # 按比例分配
            starlink_target = int(target_count * total_starlink / total_candidates)
            oneweb_target = target_count - starlink_target

            # 選擇每個星座的最佳候選者
            selected_starlink = sorted(starlink_candidates, key=lambda x: x.rsrp, reverse=True)[:starlink_target]
            selected_oneweb = sorted(oneweb_candidates, key=lambda x: x.rsrp, reverse=True)[:oneweb_target]

            return selected_starlink + selected_oneweb

        except Exception as e:
            self.logger.error(f"❌ 平衡衛星選擇失敗: {e}")
            return candidates[:target_count]

    def _calculate_rl_score(self, candidate: SatelliteCandidate) -> float:
        """計算候選者的RL分數"""
        try:
            # 基於多個因子計算RL分數
            signal_factor = max(0, (candidate.rsrp + 100) / 50)  # 標準化RSRP
            elevation_factor = candidate.elevation / 90.0  # 標準化仰角
            coverage_factor = candidate.coverage_score
            handover_factor = 1.0 - candidate.handover_potential  # 換手頻率越低越好

            rl_score = (
                signal_factor * 0.35 +
                elevation_factor * 0.25 +
                coverage_factor * 0.25 +
                handover_factor * 0.15
            )

            return max(0.0, min(1.0, rl_score))

        except Exception as e:
            self.logger.warning(f"⚠️ RL分數計算失敗: {e}")
            return 0.0

    def _calculate_pool_score(self, satellites: List[SatelliteCandidate]) -> float:
        """計算衛星池的整體分數"""
        if not satellites:
            return 0.0

        try:
            # 綜合評估池的品質
            avg_rsrp = np.mean([s.rsrp for s in satellites])
            avg_coverage = np.mean([s.coverage_score for s in satellites])
            avg_elevation = np.mean([s.elevation for s in satellites])

            # 標準化並加權
            rsrp_score = max(0, (avg_rsrp + 100) / 50)
            coverage_score = avg_coverage
            elevation_score = avg_elevation / 90.0

            pool_score = (
                rsrp_score * 0.4 +
                coverage_score * 0.4 +
                elevation_score * 0.2
            )

            return max(0.0, min(1.0, pool_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 池分數計算失敗: {e}")
            return 0.0

    def _calculate_constellation_balance(self, satellites: List[SatelliteCandidate]) -> Dict[str, Any]:
        """計算星座平衡度"""
        try:
            starlink_count = sum(1 for s in satellites if 'starlink' in s.constellation.lower())
            oneweb_count = sum(1 for s in satellites if 'oneweb' in s.constellation.lower())
            total_count = len(satellites)

            if total_count == 0:
                return {"starlink_ratio": 0, "oneweb_ratio": 0, "balance_score": 0}

            starlink_ratio = starlink_count / total_count
            oneweb_ratio = oneweb_count / total_count

            # 平衡分數：越接近50:50越好
            balance_score = 1.0 - abs(starlink_ratio - 0.5) * 2

            return {
                "starlink_count": starlink_count,
                "oneweb_count": oneweb_count,
                "starlink_ratio": starlink_ratio,
                "oneweb_ratio": oneweb_ratio,
                "balance_score": balance_score
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 星座平衡度計算失敗: {e}")
            return {"balance_score": 0}

    def extract_satellite_candidates(self, stage5_data: Dict[str, Any]) -> List[SatelliteCandidate]:
        """從Stage 5數據中提取衛星候選者"""
        try:
            candidates = []

            satellites_data = stage5_data.get('integrated_satellites', {})

            for sat_id, sat_data in satellites_data.items():
                candidate = self._create_satellite_candidate(sat_id, sat_data)
                if candidate:
                    candidates.append(candidate)

            self.logger.info(f"✅ 成功提取 {len(candidates)} 個衛星候選者")
            return candidates

        except Exception as e:
            self.logger.error(f"❌ 衛星候選者提取失敗: {e}")
            return []

    def _create_satellite_candidate(self, sat_id: str, sat_data: Dict[str, Any]) -> Optional[SatelliteCandidate]:
        """創建衛星候選者對象"""
        try:
            # 提取基本信息
            constellation = sat_data.get('constellation', 'unknown')

            # 獲取信號品質數據
            signal_quality = sat_data.get('signal_quality', {})
            rsrp = signal_quality.get('rsrp', -120.0)

            # 獲取軌道數據
            orbital_data = sat_data.get('orbital_data', {})
            elevation = orbital_data.get('elevation', 0.0)
            distance = orbital_data.get('distance', 0.0)

            # 計算覆蓋分數和換手潛力
            coverage_score = self._calculate_coverage_score(sat_data)
            handover_potential = self._calculate_handover_potential(sat_data)

            return SatelliteCandidate(
                satellite_id=sat_id,
                constellation=constellation,
                rsrp=rsrp,
                elevation=elevation,
                distance=distance,
                coverage_score=coverage_score,
                handover_potential=handover_potential
            )

        except Exception as e:
            self.logger.warning(f"⚠️ 候選者創建失敗 {sat_id}: {e}")
            return None

    def _calculate_coverage_score(self, sat_data: Dict[str, Any]) -> float:
        """計算覆蓋分數"""
        try:
            # 基於多個因素計算覆蓋分數
            signal_quality = sat_data.get('signal_quality', {})
            orbital_data = sat_data.get('orbital_data', {})

            rsrp = signal_quality.get('rsrp', -120.0)
            elevation = orbital_data.get('elevation', 0.0)

            # 標準化並組合
            rsrp_score = max(0, (rsrp + 120) / 50)
            elevation_score = elevation / 90.0

            coverage_score = (rsrp_score * 0.6 + elevation_score * 0.4)
            return max(0.0, min(1.0, coverage_score))

        except Exception as e:
            self.logger.warning(f"⚠️ 覆蓋分數計算失敗: {e}")
            return 0.0

    def _calculate_handover_potential(self, sat_data: Dict[str, Any]) -> float:
        """計算換手潛力（換手頻率的預測）"""
        try:
            orbital_data = sat_data.get('orbital_data', {})
            elevation = orbital_data.get('elevation', 0.0)

            # 仰角越低，換手頻率越高
            handover_potential = max(0, (90.0 - elevation) / 90.0)
            return handover_potential

        except Exception as e:
            self.logger.warning(f"⚠️ 換手潛力計算失敗: {e}")
            return 0.5