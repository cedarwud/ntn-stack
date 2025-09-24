#!/usr/bin/env python3
"""
衛星候選生成器 - 從dynamic_pool_optimizer_engine.py拆分

專責功能：
1. 從Stage5數據提取衛星候選
2. 創建候選對象
3. RL驅動的候選選擇
4. 策略導向的候選生成

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 模組化重構專用
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SatelliteCandidate:
    """衛星候選對象"""
    satellite_id: str
    constellation: str
    coverage_score: float
    signal_quality_score: float
    stability_score: float
    resource_cost: float
    predicted_handovers: int
    coverage_windows: List[Dict[str, Any]]
    elevation: float
    azimuth: float
    signal_quality: float
    coverage_area: float
    handover_frequency: float
    rl_score: float
    balanced_score: float

class SatelliteCandidateGenerator:
    """
    衛星候選生成器

    專責從Stage5整合數據中提取和生成衛星候選
    不再直接處理原始時序數據，遵循架構設計原則
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化候選生成器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        self.generation_stats = {
            'total_processed': 0,
            'valid_candidates': 0,
            'starlink_candidates': 0,
            'oneweb_candidates': 0
        }

        self.logger.info("✅ 衛星候選生成器初始化完成")

    def generate_candidate_pools(self, satellites: List[Dict[str, Any]],
                                strategy: str = "rl_driven") -> List[Dict[str, Any]]:
        """
        生成候選衛星池

        Args:
            satellites: 衛星數據列表
            strategy: 生成策略

        Returns:
            候選衛星池列表
        """
        try:
            self.logger.info(f"🎯 生成候選衛星池 (策略: {strategy})")

            # 提取衛星候選
            satellite_candidates = self._extract_satellite_candidates(satellites)

            if not satellite_candidates:
                self.logger.warning("⚠️ 未找到有效的衛星候選")
                return []

            # 根據策略生成不同類型的池
            pools = []

            if strategy == "rl_driven":
                pools.extend(self._generate_rl_driven_pools(satellite_candidates))
            elif strategy == "balanced":
                pools.extend(self._generate_balanced_pools(satellite_candidates))
            elif strategy == "gap_filling":
                pools.extend(self._generate_gap_filling_pools(satellite_candidates))
            else:
                pools.extend(self._generate_fallback_pools(satellite_candidates))

            self.logger.info(f"✅ 生成 {len(pools)} 個候選池")
            return pools

        except Exception as e:
            self.logger.error(f"❌ 候選池生成失敗: {e}")
            return []

    def _extract_satellite_candidates(self, satellites: List[Dict[str, Any]]) -> List[SatelliteCandidate]:
        """
        從整合數據中提取衛星候選 - 已修復跨階段違規

        ✅ 架構修正：只接收已經由前階段處理完成的候選數據
        ❌ 原違規：直接處理 position_timeseries 原始數據
        """
        candidates = []

        try:
            for sat_data in satellites:
                # ✅ 只提取已經標準化的候選信息
                satellite_id = sat_data.get('satellite_id')
                constellation = sat_data.get('constellation')

                if not satellite_id or not constellation:
                    continue

                # ✅ 使用已經計算好的候選評估結果
                candidate_metadata = sat_data.get('candidate_evaluation', {})

                # ✅ 檢查是否為有效候選（應該已經過濾）
                is_valid_candidate = candidate_metadata.get('is_valid_candidate', False)
                if not is_valid_candidate:
                    continue

                # ✅ 直接使用提供的標準化數據，不再重複計算
                coverage_score = candidate_metadata.get('coverage_score', 0.0)
                signal_quality_score = candidate_metadata.get('signal_quality_score', 0.0)
                stability_score = candidate_metadata.get('stability_score', 0.0)
                resource_cost = candidate_metadata.get('resource_cost', 1.0)
                predicted_handovers = candidate_metadata.get('predicted_handovers', 1)

                # ✅ 使用提供的最佳位置數據
                best_position = candidate_metadata.get('best_position', {})
                coverage_windows = candidate_metadata.get('coverage_windows', [])

                # ✅ 提取位置和信號數據（已標準化）
                elevation = best_position.get('elevation_deg', 0.0)
                azimuth = best_position.get('azimuth_deg', 0.0)
                signal_quality = best_position.get('rsrp_dbm', -120.0)
                coverage_area = best_position.get('coverage_area_km2', 100.0)
                handover_frequency = best_position.get('handover_frequency', 1.0)

                # ✅ 使用計算的RL評分
                rl_score = candidate_metadata.get('rl_score', 0.0)
                balanced_score = candidate_metadata.get('balanced_score', 0.0)

                # ✅ 創建衛星候選對象（使用標準化數據）
                candidate = SatelliteCandidate(
                    satellite_id=str(satellite_id),
                    constellation=constellation,
                    coverage_score=coverage_score,
                    signal_quality_score=signal_quality_score,
                    stability_score=stability_score,
                    resource_cost=resource_cost,
                    predicted_handovers=predicted_handovers,
                    coverage_windows=coverage_windows,
                    elevation=elevation,
                    azimuth=azimuth,
                    signal_quality=signal_quality,
                    coverage_area=coverage_area,
                    handover_frequency=handover_frequency,
                    rl_score=rl_score,
                    balanced_score=balanced_score
                )

                candidates.append(candidate)

                # 統計
                self.generation_stats['valid_candidates'] += 1
                if constellation == 'starlink':
                    self.generation_stats['starlink_candidates'] += 1
                elif constellation == 'oneweb':
                    self.generation_stats['oneweb_candidates'] += 1

            # ✅ 按照已經計算的RL評分排序
            candidates.sort(key=lambda x: x.rl_score, reverse=True)

            self.logger.info(f"🛰️ 接收候選數據：{len(candidates)}個有效候選")
            if candidates:
                starlink_candidates = [c for c in candidates if c.constellation == 'starlink']
                oneweb_candidates = [c for c in candidates if c.constellation == 'oneweb']
                self.logger.info(f"   📡 Starlink候選: {len(starlink_candidates)}顆")
                self.logger.info(f"   📡 OneWeb候選: {len(oneweb_candidates)}顆")

                # 顯示前幾名候選的RL評分
                for i, candidate in enumerate(candidates[:5]):
                    score = candidate.rl_score
                    self.logger.info(f"   🏆 第{i+1}名: {candidate.constellation} RL評分={score:.3f}")

            return candidates

        except Exception as e:
            self.logger.error(f"❌ 候選數據提取失敗: {e}")
            self.logger.error("⚠️ 這可能是因為沒有提供標準化的候選評估數據")
            import traceback
            traceback.print_exc()
            return []

    def _generate_rl_driven_pools(self, candidates: List[SatelliteCandidate]) -> List[Dict[str, Any]]:
        """生成RL驅動的候選池"""
        pools = []

        # 按RL評分排序並選取前N名
        top_candidates = sorted(candidates, key=lambda x: x.rl_score, reverse=True)[:20]

        pool = {
            'pool_type': 'rl_driven',
            'candidates': [self._candidate_to_dict(c) for c in top_candidates],
            'total_candidates': len(top_candidates),
            'avg_rl_score': sum(c.rl_score for c in top_candidates) / len(top_candidates) if top_candidates else 0,
            'constellation_distribution': self._calculate_constellation_distribution(top_candidates)
        }

        pools.append(pool)
        return pools

    def _generate_balanced_pools(self, candidates: List[SatelliteCandidate]) -> List[Dict[str, Any]]:
        """生成平衡的候選池"""
        pools = []

        # 平衡選擇Starlink和OneWeb
        starlink_candidates = [c for c in candidates if c.constellation == 'starlink']
        oneweb_candidates = [c for c in candidates if c.constellation == 'oneweb']

        # 各選前10名
        selected_starlink = sorted(starlink_candidates, key=lambda x: x.balanced_score, reverse=True)[:10]
        selected_oneweb = sorted(oneweb_candidates, key=lambda x: x.balanced_score, reverse=True)[:10]

        balanced_candidates = selected_starlink + selected_oneweb

        pool = {
            'pool_type': 'balanced',
            'candidates': [self._candidate_to_dict(c) for c in balanced_candidates],
            'total_candidates': len(balanced_candidates),
            'starlink_count': len(selected_starlink),
            'oneweb_count': len(selected_oneweb),
            'constellation_distribution': self._calculate_constellation_distribution(balanced_candidates)
        }

        pools.append(pool)
        return pools

    def _generate_gap_filling_pools(self, candidates: List[SatelliteCandidate]) -> List[Dict[str, Any]]:
        """生成覆蓋間隙填補池"""
        pools = []

        # 選擇覆蓋評分高的候選
        gap_filling_candidates = sorted(candidates, key=lambda x: x.coverage_score, reverse=True)[:15]

        pool = {
            'pool_type': 'gap_filling',
            'candidates': [self._candidate_to_dict(c) for c in gap_filling_candidates],
            'total_candidates': len(gap_filling_candidates),
            'avg_coverage_score': sum(c.coverage_score for c in gap_filling_candidates) / len(gap_filling_candidates) if gap_filling_candidates else 0,
            'constellation_distribution': self._calculate_constellation_distribution(gap_filling_candidates)
        }

        pools.append(pool)
        return pools

    def _generate_fallback_pools(self, candidates: List[SatelliteCandidate]) -> List[Dict[str, Any]]:
        """生成回退候選池"""
        pools = []

        # 簡單選擇前15名
        fallback_candidates = candidates[:15]

        pool = {
            'pool_type': 'fallback',
            'candidates': [self._candidate_to_dict(c) for c in fallback_candidates],
            'total_candidates': len(fallback_candidates),
            'constellation_distribution': self._calculate_constellation_distribution(fallback_candidates)
        }

        pools.append(pool)
        return pools

    def _candidate_to_dict(self, candidate: SatelliteCandidate) -> Dict[str, Any]:
        """將候選對象轉換為字典"""
        return {
            'satellite_id': candidate.satellite_id,
            'constellation': candidate.constellation,
            'coverage_score': candidate.coverage_score,
            'signal_quality_score': candidate.signal_quality_score,
            'stability_score': candidate.stability_score,
            'resource_cost': candidate.resource_cost,
            'predicted_handovers': candidate.predicted_handovers,
            'elevation': candidate.elevation,
            'azimuth': candidate.azimuth,
            'signal_quality': candidate.signal_quality,
            'coverage_area': candidate.coverage_area,
            'handover_frequency': candidate.handover_frequency,
            'rl_score': candidate.rl_score,
            'balanced_score': candidate.balanced_score,
            'coverage_windows': candidate.coverage_windows
        }

    def _calculate_constellation_distribution(self, candidates: List[SatelliteCandidate]) -> Dict[str, int]:
        """計算星座分布"""
        distribution = {}
        for candidate in candidates:
            constellation = candidate.constellation
            distribution[constellation] = distribution.get(constellation, 0) + 1
        return distribution

    def get_generation_statistics(self) -> Dict[str, Any]:
        """獲取生成統計"""
        return self.generation_stats.copy()