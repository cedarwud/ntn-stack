#!/usr/bin/env python3
"""
備份池管理器 - BackupPoolManager
負責備份衛星池的建立、評估和分類功能

從 BackupSatelliteManager 拆分出來的專業模組
專注於備份池的生命週期管理
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

try:
    from ...shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore
except ImportError:
    from shared.core_modules import OrbitalCalculationsCore, VisibilityCalculationsCore, SignalCalculationsCore

logger = logging.getLogger(__name__)

class BackupPoolManager:
    """
    備份池管理器

    職責：
    - 備份衛星池建立與配置
    - 智能備份評估與選擇
    - 備份衛星分類與角色分配
    - 備份適用性評估與評分
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化備份池管理器

        Args:
            config: 配置參數，可以是直接配置或包含'observer'鍵的嵌套配置
        """
        self.logger = logger

        # 處理配置格式
        if config and 'observer' in config:
            actual_observer_config = config['observer']
        else:
            actual_observer_config = config

        # 初始化共享核心模組
        self.orbital_calc = OrbitalCalculationsCore(actual_observer_config)
        self.visibility_calc = VisibilityCalculationsCore(actual_observer_config)
        self.signal_calc = SignalCalculationsCore()

        # 備份池管理配置
        self.pool_config = {
            'default_pool_size': 6,
            'minimum_pool_size': 3,
            'maximum_pool_size': 12,
            'backup_ratio': 0.25,
            'evaluation_criteria': {
                'signal_quality_weight': 0.4,
                'coverage_contribution_weight': 0.3,
                'orbital_stability_weight': 0.2,
                'diversity_weight': 0.1
            }
        }

        # 評估統計
        self.evaluation_stats = {
            'pools_created': 0,
            'satellites_evaluated': 0,
            'average_pool_quality': 0.0
        }

        self.logger.info("✅ BackupPoolManager 初始化完成")

    def establish_backup_satellite_pool(self, satellites: List[Dict],
                                      primary_selection: List[Dict] = None) -> Dict:
        """
        建立備份衛星池

        Args:
            satellites: 候選衛星列表
            primary_selection: 主要選擇的衛星 (用於避免重複)

        Returns:
            備份池建立結果
        """
        try:
            self.logger.info(f"🏗️ 建立備份衛星池 (候選: {len(satellites)}顆)")

            # 排除主要選擇的衛星
            available_satellites = satellites
            if primary_selection:
                primary_ids = {sat.get('satellite_id') for sat in primary_selection}
                available_satellites = [
                    sat for sat in satellites
                    if sat.get('satellite_id') not in primary_ids
                ]

            if not available_satellites:
                return {'error': 'No satellites available for backup pool'}

            # 計算備份池大小
            target_pool_size = min(
                self.pool_config['default_pool_size'],
                len(available_satellites)
            )

            # 執行智慧備份評估選擇最佳備份候選
            backup_evaluation = self.implement_intelligent_backup_evaluation(available_satellites)

            if 'error' in backup_evaluation:
                return backup_evaluation

            # 選擇前N個最佳候選作為備份池
            evaluated_candidates = backup_evaluation.get('evaluated_candidates', [])
            selected_backups = evaluated_candidates[:target_pool_size]

            # 建立備份池結構
            backup_pool_structure = {
                'pool_id': f"backup_pool_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'established_timestamp': datetime.now(timezone.utc).isoformat(),
                'pool_configuration': {
                    'target_size': target_pool_size,
                    'actual_size': len(selected_backups),
                    'selection_method': 'intelligent_evaluation'
                },
                'backup_satellites': selected_backups,
                'pool_categories': self._categorize_backup_satellites(selected_backups),
                'pool_quality_metrics': {
                    'average_signal_quality': backup_evaluation.get('average_signal_quality', 0),
                    'coverage_redundancy': backup_evaluation.get('coverage_redundancy', 0),
                    'orbital_diversity': backup_evaluation.get('orbital_diversity', 0)
                }
            }

            # 更新統計
            self.evaluation_stats['pools_created'] += 1

            self.logger.info(f"✅ 備份池建立成功: {len(selected_backups)}顆備份衛星")
            return backup_pool_structure

        except Exception as e:
            self.logger.error(f"❌ 備份衛星池建立失敗: {e}")
            return {'error': str(e)}

    def implement_intelligent_backup_evaluation(self, candidates: List[Dict]) -> Dict:
        """
        實施智能備份評估

        Args:
            candidates: 備份候選衛星列表

        Returns:
            評估結果
        """
        try:
            self.logger.info(f"🧠 開始智能備份評估 (候選: {len(candidates)}顆)")

            evaluated_candidates = []
            total_signal_quality = 0
            total_coverage_score = 0

            for candidate in candidates:
                # 計算備份適用性評分
                suitability_score = self._calculate_backup_suitability_score(candidate)

                # 評估信號品質
                signal_quality = self._assess_candidate_signal_quality(candidate)

                # 評估覆蓋貢獻
                coverage_contribution = self._assess_backup_coverage_contribution(candidate)

                # 評估軌道穩定性
                orbital_stability = self._assess_backup_orbital_stability(candidate)

                # 綜合評分
                overall_score = (
                    suitability_score * 0.4 +
                    signal_quality * 0.3 +
                    coverage_contribution * 0.2 +
                    orbital_stability * 0.1
                )

                candidate_evaluation = {
                    **candidate,
                    'backup_evaluation': {
                        'suitability_score': suitability_score,
                        'signal_quality': signal_quality,
                        'coverage_contribution': coverage_contribution,
                        'orbital_stability': orbital_stability,
                        'overall_score': overall_score,
                        'backup_grade': self._grade_backup_suitability(overall_score),
                        'recommended_role': self._recommend_backup_role(overall_score)
                    }
                }

                evaluated_candidates.append(candidate_evaluation)
                total_signal_quality += signal_quality
                total_coverage_score += coverage_contribution

            # 按總評分排序
            evaluated_candidates.sort(
                key=lambda x: x['backup_evaluation']['overall_score'],
                reverse=True
            )

            # 計算軌道多樣性
            orbital_diversity = self._calculate_candidates_orbital_diversity(evaluated_candidates)

            evaluation_result = {
                'evaluated_candidates': evaluated_candidates,
                'evaluation_summary': {
                    'total_candidates': len(candidates),
                    'average_signal_quality': total_signal_quality / len(candidates) if candidates else 0,
                    'coverage_redundancy': total_coverage_score / len(candidates) if candidates else 0,
                    'orbital_diversity': orbital_diversity,
                    'top_candidates_count': min(10, len(evaluated_candidates))
                }
            }

            # 更新統計
            self.evaluation_stats['satellites_evaluated'] += len(candidates)

            self.logger.info(f"✅ 智能備份評估完成，平均評分: {evaluation_result['evaluation_summary']['average_signal_quality']:.2f}")

            return evaluation_result

        except Exception as e:
            self.logger.error(f"❌ 智能備份評估失敗: {e}")
            return {'error': str(e)}

    def _calculate_backup_suitability_score(self, candidate: Dict) -> float:
        """計算備份適用性評分"""
        try:
            base_score = 0.5

            # 信號強度加權
            if 'signal_data' in candidate:
                rsrp = candidate['signal_data'].get('rsrp', -100)
                if rsrp > -90:
                    base_score += 0.3
                elif rsrp > -100:
                    base_score += 0.2

            # 仰角加權
            if 'position' in candidate:
                elevation = candidate['position'].get('elevation', 0)
                if elevation > 30:
                    base_score += 0.2
                elif elevation > 15:
                    base_score += 0.1

            return min(1.0, base_score)

        except Exception as e:
            self.logger.error(f"備份適用性評分計算錯誤: {e}")
            return 0.5

    def _assess_candidate_signal_quality(self, candidate: Dict) -> float:
        """評估候選衛星信號品質"""
        try:
            if 'signal_data' not in candidate:
                return 0.5

            signal_data = candidate['signal_data']
            rsrp = signal_data.get('rsrp', -100)
            sinr = signal_data.get('sinr', 0)

            # RSRP 評分 (dBm)
            rsrp_score = max(0, min(1, (rsrp + 120) / 30))

            # SINR 評分 (dB)
            sinr_score = max(0, min(1, (sinr + 5) / 25))

            return (rsrp_score + sinr_score) / 2

        except Exception as e:
            self.logger.error(f"信號品質評估錯誤: {e}")
            return 0.5

    def _assess_backup_coverage_contribution(self, candidate: Dict) -> float:
        """評估備份覆蓋貢獻"""
        try:
            base_contribution = 0.6

            if 'position' in candidate:
                elevation = candidate['position'].get('elevation', 0)
                azimuth = candidate['position'].get('azimuth', 0)

                # 高仰角貢獻更大
                elevation_factor = min(1.0, elevation / 45.0)
                base_contribution += elevation_factor * 0.3

            return min(1.0, base_contribution)

        except Exception:
            return 0.6

    def _assess_backup_orbital_stability(self, candidate: Dict) -> float:
        """評估備份軌道穩定性"""
        return 0.8  # 簡化實現

    def _grade_backup_suitability(self, score: float) -> str:
        """評定備份適用性等級"""
        if score >= 0.8:
            return "EXCELLENT"
        elif score >= 0.6:
            return "GOOD"
        elif score >= 0.4:
            return "FAIR"
        else:
            return "POOR"

    def _recommend_backup_role(self, score: float) -> str:
        """推薦備份角色"""
        if score >= 0.8:
            return "primary_backup"
        elif score >= 0.6:
            return "secondary_backup"
        else:
            return "emergency_backup"

    def _categorize_backup_satellites(self, backup_satellites: List[Dict]) -> Dict:
        """分類備份衛星"""
        categories = {
            'primary_backups': [],
            'secondary_backups': [],
            'emergency_backups': []
        }

        for satellite in backup_satellites:
            evaluation = satellite.get('backup_evaluation', {})
            role = evaluation.get('recommended_role', 'emergency_backup')

            if role == 'primary_backup':
                categories['primary_backups'].append(satellite)
            elif role == 'secondary_backup':
                categories['secondary_backups'].append(satellite)
            else:
                categories['emergency_backups'].append(satellite)

        return categories

    def _calculate_candidates_orbital_diversity(self, candidates: List[Dict]) -> float:
        """計算候選衛星軌道多樣性"""
        if not candidates:
            return 0.0

        # 簡化實現：基於位置分散度
        positions = []
        for candidate in candidates:
            if 'position' in candidate:
                pos = candidate['position']
                positions.append((pos.get('elevation', 0), pos.get('azimuth', 0)))

        if len(positions) < 2:
            return 0.5

        # 計算位置分散度
        diversity_score = min(1.0, len(set(positions)) / len(positions))
        return diversity_score

    def get_pool_statistics(self) -> Dict[str, Any]:
        """獲取備份池統計信息"""
        return {
            'module_name': 'BackupPoolManager',
            'pools_created': self.evaluation_stats['pools_created'],
            'satellites_evaluated': self.evaluation_stats['satellites_evaluated'],
            'average_pool_quality': self.evaluation_stats['average_pool_quality'],
            'pool_config': self.pool_config
        }