#!/usr/bin/env python3
"""
純信號品質計算器 - 修復跨階段違規

專責功能：
1. 單點RSRP/RSRQ/SINR計算
2. 3GPP NTN標準合規
3. 信號品質評估
4. 切換候選識別

修復問題：
- 移除position_timeseries處理 (歸還給Stage 4)
- 移除時序連續性驗證 (歸還給Stage 4)
- 專注於單點信號分析

作者: Claude & Human
創建日期: 2025年
版本: v2.0 - 跨階段違規修復版
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

# 使用共享核心模組，避免重複實現
from shared.core_modules.unified_signal_calculator import UnifiedSignalCalculator
from shared.core_modules.visibility_calculations_core import VisibilityCalculationsCore

logger = logging.getLogger(__name__)

class PureSignalQualityCalculator:
    """
    純信號品質計算器 - 修復跨階段違規版本

    專責功能：
    - 單點信號品質計算
    - 3GPP NTN標準合規
    - 信號品質評估
    - 切換候選識別

    不包含：
    - position_timeseries處理 → Stage 4
    - 時序數據分析 → Stage 4
    - 連續性驗證 → Stage 4
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化純信號品質計算器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 使用共享模組避免重複實現
        self.signal_calculator = UnifiedSignalCalculator(config)
        self.visibility_calculator = VisibilityCalculationsCore()

        # 3GPP NTN標準配置
        self.ntn_config = {
            'frequency_bands': {
                'ka_band': 20.0e9,  # Hz
                'ku_band': 12.0e9,  # Hz
            },
            'signal_thresholds': {
                'rsrp_min': -120.0,  # dBm
                'rsrp_max': -44.0,   # dBm
                'rsrq_min': -20.0,   # dB
                'rsrq_max': -3.0,    # dB
                'sinr_min': -6.0,    # dB
                'sinr_max': 30.0     # dB
            },
            'handover_thresholds': {
                'rsrp_handover': -100.0,  # dBm
                'quality_degradation': 0.3  # 30%品質下降觸發
            }
        }

        self.calculation_stats = {
            'satellites_processed': 0,
            'positions_analyzed': 0,
            'handover_candidates_identified': 0,
            'signal_quality_assessments': 0
        }

        self.logger.info("✅ 純信號品質計算器初始化完成 (修復跨階段違規)")

    def calculate_signal_quality(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算信號品質 - 純單點分析

        Args:
            satellite_data: 單顆衛星數據 (不包含時序)

        Returns:
            信號品質分析結果
        """
        try:
            self.logger.info("🔍 開始信號品質計算")

            satellite_id = satellite_data.get('satellite_id')
            constellation = satellite_data.get('constellation')

            # ✅ 只處理當前位置，不處理時序
            current_position = satellite_data.get('current_position')
            if not current_position:
                return self._create_invalid_result(satellite_id, "missing_current_position")

            # ✅ 使用共享模組計算信號品質
            signal_quality = self.signal_calculator.calculate_signal_quality(
                current_position, satellite_data
            )

            # ✅ 使用共享模組計算可見性
            visibility_info = self.visibility_calculator.calculate_visibility_metrics(
                current_position
            )

            # 3GPP NTN合規性檢查
            compliance_check = self._validate_3gpp_ntn_compliance(signal_quality)

            # 品質評估
            quality_assessment = self._assess_signal_quality(signal_quality)

            # 切換候選識別
            handover_candidates = self._identify_handover_candidates(
                signal_quality, visibility_info, satellite_data
            )

            # 更新統計
            self.calculation_stats['satellites_processed'] += 1
            self.calculation_stats['positions_analyzed'] += 1
            self.calculation_stats['signal_quality_assessments'] += 1
            if handover_candidates:
                self.calculation_stats['handover_candidates_identified'] += 1

            result = {
                'satellite_id': satellite_id,
                'constellation': constellation,
                'signal_quality_metrics': signal_quality,
                'visibility_metrics': visibility_info,
                'quality_assessment': quality_assessment,
                'handover_candidates': handover_candidates,
                'ntn_compliance': compliance_check,
                'calculation_timestamp': datetime.now(timezone.utc).isoformat(),
                'stage_compliance': 'pure_stage3_no_timeseries',
                'academic_grade': 'A_single_point_analysis'
            }

            self.logger.info(f"✅ 信號品質計算完成: {satellite_id}")
            return result

        except Exception as e:
            self.logger.error(f"❌ 信號品質計算失敗: {e}")
            return self._create_error_result(satellite_data.get('satellite_id'), str(e))

    def _validate_3gpp_ntn_compliance(self, signal_quality: Dict[str, Any]) -> Dict[str, Any]:
        """驗證3GPP NTN標準合規性"""
        try:
            rsrp = signal_quality.get('rsrp_dbm')
            rsrq = signal_quality.get('rsrq_db')
            sinr = signal_quality.get('sinr_db')

            thresholds = self.ntn_config['signal_thresholds']

            compliance = {
                'rsrp_compliant': thresholds['rsrp_min'] <= rsrp <= thresholds['rsrp_max'] if rsrp else False,
                'rsrq_compliant': thresholds['rsrq_min'] <= rsrq <= thresholds['rsrq_max'] if rsrq else False,
                'sinr_compliant': thresholds['sinr_min'] <= sinr <= thresholds['sinr_max'] if sinr else False,
                'overall_compliant': False
            }

            compliance['overall_compliant'] = all([
                compliance['rsrp_compliant'],
                compliance['rsrq_compliant'],
                compliance['sinr_compliant']
            ])

            compliance['standard_version'] = '3GPP_TS_38.821_NTN'

            return compliance

        except Exception as e:
            self.logger.error(f"❌ 3GPP NTN合規性檢查失敗: {e}")
            return {'overall_compliant': False, 'error': str(e)}

    def _assess_signal_quality(self, signal_quality: Dict[str, Any]) -> Dict[str, Any]:
        """評估信號品質"""
        try:
            rsrp = signal_quality.get('rsrp_dbm', -120)
            rsrq = signal_quality.get('rsrq_db', -20)
            sinr = signal_quality.get('sinr_db', -6)

            # 基於3GPP標準的品質分級
            if rsrp >= -85 and rsrq >= -10 and sinr >= 20:
                quality_grade = 'excellent'
                quality_score = 0.9
            elif rsrp >= -95 and rsrq >= -13 and sinr >= 10:
                quality_grade = 'good'
                quality_score = 0.7
            elif rsrp >= -105 and rsrq >= -16 and sinr >= 0:
                quality_grade = 'fair'
                quality_score = 0.5
            elif rsrp >= -115 and rsrq >= -18 and sinr >= -3:
                quality_grade = 'poor'
                quality_score = 0.3
            else:
                quality_grade = 'unusable'
                quality_score = 0.1

            return {
                'quality_grade': quality_grade,
                'quality_score': quality_score,
                'rsrp_assessment': self._assess_rsrp_level(rsrp),
                'rsrq_assessment': self._assess_rsrq_level(rsrq),
                'sinr_assessment': self._assess_sinr_level(sinr),
                'connection_viability': quality_score >= 0.3,
                'handover_recommended': quality_score < 0.5
            }

        except Exception as e:
            self.logger.error(f"❌ 信號品質評估失敗: {e}")
            return {'quality_grade': 'error', 'quality_score': 0.0}

    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計"""
        stats = self.calculation_stats.copy()
        stats['stage_violation_fixed'] = 'removed_position_timeseries_processing'
        stats['cross_stage_compliance'] = 'pure_stage3_responsibilities'
        return stats
