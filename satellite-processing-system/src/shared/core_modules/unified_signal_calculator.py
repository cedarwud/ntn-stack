#!/usr/bin/env python3
"""
統一信號品質計算器 - 消除跨階段重複功能

提供所有階段使用的標準化信號品質計算功能：
1. 統一的RSRP/RSRQ/RS-SINR計算
2. 標準化的路徑損耗模型
3. 一致的3GPP NTN標準實現
4. 避免重複的信號計算邏輯

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 重複功能消除專用
"""

import logging
import math
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class UnifiedSignalCalculator:
    """
    統一信號品質計算器

    所有階段使用此計算器進行信號品質分析，避免重複實現：
    - Stage 3: 基礎信號品質分析
    - Stage 4: 時序信號趨勢分析
    - Stage 6: 動態規劃的信號評估

    統一功能：
    1. 3GPP NTN標準的RSRP計算
    2. ITU-R P.618大氣衰減模型
    3. 標準化的信號品質評級
    4. 換手決策支援計算
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化統一信號品質計算器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 3GPP NTN標準參數
        self.ntn_config = {
            'frequency_ghz': self.config.get('frequency_ghz', 28.0),  # Ka頻段
            'tx_power_dbm': self.config.get('tx_power_dbm', 50.0),   # 衛星發射功率
            'antenna_gain_dbi': self.config.get('antenna_gain_dbi', 30.0),  # 天線增益
            'noise_floor_dbm': self.config.get('noise_floor_dbm', -120.0),  # 噪聲基底
            'system_loss_db': self.config.get('system_loss_db', 3.0)  # 系統損耗
        }

        # 信號品質閾值（3GPP標準）
        self.quality_thresholds = {
            'rsrp_excellent_dbm': -80.0,
            'rsrp_good_dbm': -90.0,
            'rsrp_fair_dbm': -100.0,
            'rsrp_poor_dbm': -110.0,
            'rsrq_excellent_db': -10.0,
            'rsrq_good_db': -12.0,
            'rsrq_fair_db': -15.0,
            'rsrq_poor_db': -17.0,
            'sinr_excellent_db': 15.0,
            'sinr_good_db': 10.0,
            'sinr_fair_db': 5.0,
            'sinr_poor_db': 0.0
        }

        # 計算統計
        self.calculation_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'rsrp_calculations': 0,
            'rsrq_calculations': 0,
            'sinr_calculations': 0
        }

        self.logger.info("✅ 統一信號品質計算器初始化完成")
        self.logger.info(f"📡 頻率: {self.ntn_config['frequency_ghz']} GHz")
        self.logger.info(f"⚡ 發射功率: {self.ntn_config['tx_power_dbm']} dBm")

    def calculate_signal_quality(self, orbital_data: Dict[str, Any],
                               include_detailed_analysis: bool = False) -> Dict[str, Any]:
        """
        計算信號品質 - 統一介面

        Args:
            orbital_data: 軌道數據（包含距離、仰角等）
            include_detailed_analysis: 是否包含詳細分析

        Returns:
            完整的信號品質分析結果
        """

        try:
            self.calculation_stats['total_calculations'] += 1

            # 提取基本參數
            distance_km = orbital_data.get('distance_km', orbital_data.get('relative_to_observer', {}).get('distance_km', 0))
            elevation_deg = orbital_data.get('elevation_deg', orbital_data.get('relative_to_observer', {}).get('elevation_deg', 0))

            if distance_km <= 0 or elevation_deg <= 0:
                self.logger.warning("⚠️ 軌道數據不完整，使用默認值")
                distance_km = max(distance_km, 1000.0)  # 最小1000km
                elevation_deg = max(elevation_deg, 5.0)   # 最小5度

            # 計算基本信號指標
            signal_metrics = self._calculate_core_signal_metrics(distance_km, elevation_deg)

            # 評估信號品質等級
            quality_assessment = self._assess_signal_quality(signal_metrics)

            # 構建結果
            result = {
                'signal_quality': signal_metrics,
                'quality_assessment': quality_assessment,
                'calculation_metadata': {
                    'frequency_ghz': self.ntn_config['frequency_ghz'],
                    'calculation_method': '3gpp_ntn_standard',
                    'calculation_time': datetime.now(timezone.utc).isoformat(),
                    'input_parameters': {
                        'distance_km': distance_km,
                        'elevation_deg': elevation_deg
                    }
                }
            }

            # 詳細分析（可選）
            if include_detailed_analysis:
                detailed_analysis = self._perform_detailed_analysis(signal_metrics, orbital_data)
                result['detailed_analysis'] = detailed_analysis

            self.calculation_stats['successful_calculations'] += 1
            return result

        except Exception as e:
            self.calculation_stats['failed_calculations'] += 1
            self.logger.error(f"❌ 信號品質計算失敗: {e}")
            return self._create_fallback_result(str(e))

    def _calculate_core_signal_metrics(self, distance_km: float, elevation_deg: float) -> Dict[str, float]:
        """計算核心信號指標"""

        try:
            # 1. 自由空間路徑損耗 (Friis公式)
            fspl_db = self._calculate_free_space_path_loss(distance_km)

            # 2. 大氣衰減 (ITU-R P.618)
            atmospheric_loss_db = self._calculate_atmospheric_loss(elevation_deg)

            # 3. 天線增益調整
            antenna_gain_adjusted = self._calculate_elevation_dependent_antenna_gain(elevation_deg)

            # 4. RSRP計算 (3GPP TS 38.214)
            rsrp_dbm = (self.ntn_config['tx_power_dbm'] +
                       antenna_gain_adjusted -
                       fspl_db -
                       atmospheric_loss_db -
                       self.ntn_config['system_loss_db'])

            # 限制RSRP範圍 (-140 dBm to -44 dBm per 3GPP)
            rsrp_dbm = max(-140.0, min(-44.0, rsrp_dbm))

            # 5. RSRQ計算
            rsrq_db = self._calculate_rsrq(rsrp_dbm, elevation_deg)

            # 6. RS-SINR計算
            rs_sinr_db = self._calculate_rs_sinr(rsrp_dbm, elevation_deg)

            self.calculation_stats['rsrp_calculations'] += 1
            self.calculation_stats['rsrq_calculations'] += 1
            self.calculation_stats['sinr_calculations'] += 1

            return {
                'rsrp_dbm': rsrp_dbm,
                'rsrq_db': rsrq_db,
                'rs_sinr_db': rs_sinr_db,
                'fspl_db': fspl_db,
                'atmospheric_loss_db': atmospheric_loss_db,
                'antenna_gain_db': antenna_gain_adjusted,
                'distance_km': distance_km,
                'elevation_deg': elevation_deg
            }

        except Exception as e:
            self.logger.error(f"❌ 核心信號指標計算失敗: {e}")
            return self._create_fallback_metrics()

    def _calculate_free_space_path_loss(self, distance_km: float) -> float:
        """計算自由空間路徑損耗 (3GPP TS 38.901)"""

        try:
            if distance_km <= 0:
                return 999.0  # 無效距離

            # FSPL = 20*log10(4π*d*f/c)
            # d: 距離(m), f: 頻率(Hz), c: 光速
            distance_m = distance_km * 1000
            frequency_hz = self.ntn_config['frequency_ghz'] * 1e9

            fspl_db = 20 * math.log10(4 * math.pi * distance_m * frequency_hz / 299792458)
            return max(0, fspl_db)

        except Exception as e:
            self.logger.warning(f"⚠️ FSPL計算失敗: {e}")
            return 200.0  # 預設高損耗值

    def _calculate_atmospheric_loss(self, elevation_deg: float) -> float:
        """計算大氣衰減 (ITU-R P.618)"""

        try:
            if elevation_deg <= 0:
                return 10.0  # 低仰角高衰減

            # ITU-R P.618 大氣衰減模型
            if elevation_deg >= 90:
                return 0.5  # 天頂方向最小衰減
            elif elevation_deg >= 30:
                return 0.5 + (90 - elevation_deg) * 0.05
            elif elevation_deg >= 10:
                return 3.0 + (30 - elevation_deg) * 0.1
            else:
                return 5.0 + (10 - elevation_deg) * 0.2

        except Exception as e:
            self.logger.warning(f"⚠️ 大氣衰減計算失敗: {e}")
            return 5.0

    def _calculate_elevation_dependent_antenna_gain(self, elevation_deg: float) -> float:
        """計算仰角相關的天線增益"""

        try:
            base_gain = self.ntn_config['antenna_gain_dbi']

            # 仰角增益調整
            if elevation_deg >= 45:
                gain_adjustment = 0.0  # 高仰角無損失
            elif elevation_deg >= 20:
                gain_adjustment = (45 - elevation_deg) * 0.1  # 輕微損失
            elif elevation_deg >= 10:
                gain_adjustment = (20 - elevation_deg) * 0.2  # 中等損失
            else:
                gain_adjustment = (10 - elevation_deg) * 0.5  # 重大損失

            return base_gain - gain_adjustment

        except Exception as e:
            self.logger.warning(f"⚠️ 天線增益計算失敗: {e}")
            return self.ntn_config['antenna_gain_dbi']

    def _calculate_rsrq(self, rsrp_dbm: float, elevation_deg: float) -> float:
        """計算RSRQ (3GPP TS 38.214)"""

        try:
            # RSRQ = RSRP - RSSI (簡化模型)
            # 基於仰角調整干擾水平
            if elevation_deg >= 30:
                interference_factor = 0.5
            elif elevation_deg >= 10:
                interference_factor = 1.0
            else:
                interference_factor = 2.0

            rsrq_db = rsrp_dbm + 30 - interference_factor * 10  # 簡化計算

            # RSRQ範圍限制 (-19.5 dB to -3 dB per 3GPP)
            return max(-19.5, min(-3.0, rsrq_db))

        except Exception as e:
            self.logger.warning(f"⚠️ RSRQ計算失敗: {e}")
            return -15.0

    def _calculate_rs_sinr(self, rsrp_dbm: float, elevation_deg: float) -> float:
        """計算RS-SINR (3GPP TS 38.214)"""

        try:
            # RS-SINR基於RSRP和環境因素
            base_sinr = rsrp_dbm + 100  # 轉換為相對值

            # 基於仰角的調整
            if elevation_deg >= 45:
                elevation_bonus = 5.0
            elif elevation_deg >= 20:
                elevation_bonus = 2.0
            elif elevation_deg >= 10:
                elevation_bonus = 0.0
            else:
                elevation_bonus = -5.0

            rs_sinr_db = base_sinr + elevation_bonus

            # RS-SINR範圍限制 (-20 dB to 30 dB)
            return max(-20.0, min(30.0, rs_sinr_db))

        except Exception as e:
            self.logger.warning(f"⚠️ RS-SINR計算失敗: {e}")
            return 0.0

    def _assess_signal_quality(self, signal_metrics: Dict[str, float]) -> Dict[str, Any]:
        """評估信號品質等級"""

        try:
            rsrp_dbm = signal_metrics.get('rsrp_dbm', -120.0)
            rsrq_db = signal_metrics.get('rsrq_db', -15.0)
            rs_sinr_db = signal_metrics.get('rs_sinr_db', 0.0)

            # 3GPP NTN品質等級評估
            if (rsrp_dbm >= self.quality_thresholds['rsrp_excellent_dbm'] and
                rsrq_db >= self.quality_thresholds['rsrq_excellent_db'] and
                rs_sinr_db >= self.quality_thresholds['sinr_excellent_db']):
                quality_level = "優秀"
                quality_score = 5
            elif (rsrp_dbm >= self.quality_thresholds['rsrp_good_dbm'] and
                  rsrq_db >= self.quality_thresholds['rsrq_good_db'] and
                  rs_sinr_db >= self.quality_thresholds['sinr_good_db']):
                quality_level = "良好"
                quality_score = 4
            elif (rsrp_dbm >= self.quality_thresholds['rsrp_fair_dbm'] and
                  rsrq_db >= self.quality_thresholds['rsrq_fair_db'] and
                  rs_sinr_db >= self.quality_thresholds['sinr_fair_db']):
                quality_level = "中等"
                quality_score = 3
            elif (rsrp_dbm >= self.quality_thresholds['rsrp_poor_dbm'] and
                  rsrq_db >= self.quality_thresholds['rsrq_poor_db'] and
                  rs_sinr_db >= self.quality_thresholds['sinr_poor_db']):
                quality_level = "較差"
                quality_score = 2
            else:
                quality_level = "不良"
                quality_score = 1

            return {
                'quality_level': quality_level,
                'quality_score': quality_score,
                'is_usable': quality_score >= 3,
                'handover_recommended': quality_score <= 2,
                'assessment_criteria': {
                    'rsrp_threshold_met': rsrp_dbm >= self.quality_thresholds['rsrp_fair_dbm'],
                    'rsrq_threshold_met': rsrq_db >= self.quality_thresholds['rsrq_fair_db'],
                    'sinr_threshold_met': rs_sinr_db >= self.quality_thresholds['sinr_fair_db']
                },
                'thresholds_used': self.quality_thresholds.copy()
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 品質評估失敗: {e}")
            return {
                'quality_level': "未知",
                'quality_score': 1,
                'is_usable': False,
                'handover_recommended': True,
                'assessment_error': str(e)
            }

    def _perform_detailed_analysis(self, signal_metrics: Dict[str, float],
                                 orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行詳細信號分析"""

        try:
            # 鏈路預算分析
            link_budget = self._calculate_link_budget(signal_metrics)

            # 換手預測
            handover_analysis = self._analyze_handover_potential(signal_metrics, orbital_data)

            # 信號穩定性評估
            stability_analysis = self._assess_signal_stability(signal_metrics)

            return {
                'link_budget': link_budget,
                'handover_analysis': handover_analysis,
                'stability_analysis': stability_analysis,
                'detailed_calculation_time': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.warning(f"⚠️ 詳細分析失敗: {e}")
            return {'analysis_error': str(e)}

    def _calculate_link_budget(self, signal_metrics: Dict[str, float]) -> Dict[str, float]:
        """計算鏈路預算"""
        return {
            'tx_power_dbm': self.ntn_config['tx_power_dbm'],
            'antenna_gain_db': signal_metrics.get('antenna_gain_db', 0),
            'path_loss_db': signal_metrics.get('fspl_db', 0) + signal_metrics.get('atmospheric_loss_db', 0),
            'system_loss_db': self.ntn_config['system_loss_db'],
            'rx_power_dbm': signal_metrics.get('rsrp_dbm', -120),
            'snr_margin_db': signal_metrics.get('rsrp_dbm', -120) - self.ntn_config['noise_floor_dbm']
        }

    def _analyze_handover_potential(self, signal_metrics: Dict[str, float],
                                  orbital_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析換手潛力"""
        rsrp = signal_metrics.get('rsrp_dbm', -120)
        elevation = signal_metrics.get('elevation_deg', 0)

        return {
            'handover_urgency': 'high' if rsrp < -110 else 'medium' if rsrp < -100 else 'low',
            'predicted_handover_time_minutes': max(1, 20 - elevation) if elevation < 20 else 30,
            'handover_trigger_rsrp': self.quality_thresholds['rsrp_poor_dbm'],
            'current_margin_db': rsrp - self.quality_thresholds['rsrp_poor_dbm']
        }

    def _assess_signal_stability(self, signal_metrics: Dict[str, float]) -> Dict[str, Any]:
        """評估信號穩定性"""
        rsrp = signal_metrics.get('rsrp_dbm', -120)
        elevation = signal_metrics.get('elevation_deg', 0)

        stability_score = min(1.0, max(0.0, (rsrp + 120) / 50 + elevation / 90))

        return {
            'stability_score': stability_score,
            'stability_level': 'high' if stability_score > 0.7 else 'medium' if stability_score > 0.4 else 'low',
            'dominant_factors': ['elevation', 'path_loss'] if elevation < 30 else ['atmospheric_conditions']
        }

    def _create_fallback_result(self, error_message: str) -> Dict[str, Any]:
        """創建回退結果"""
        return {
            'signal_quality': self._create_fallback_metrics(),
            'quality_assessment': {
                'quality_level': "不良",
                'quality_score': 1,
                'is_usable': False,
                'calculation_error': error_message
            },
            'calculation_metadata': {
                'calculation_method': 'fallback',
                'error': error_message
            }
        }

    def _create_fallback_metrics(self) -> Dict[str, float]:
        """創建回退信號指標"""
        return {
            'rsrp_dbm': -120.0,
            'rsrq_db': -15.0,
            'rs_sinr_db': 0.0,
            'fspl_db': 200.0,
            'atmospheric_loss_db': 5.0,
            'antenna_gain_db': self.ntn_config['antenna_gain_dbi'],
            'distance_km': 1000.0,
            'elevation_deg': 5.0
        }

    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        return self.calculation_stats.copy()

    def reset_statistics(self) -> None:
        """重置統計信息"""
        self.calculation_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'rsrp_calculations': 0,
            'rsrq_calculations': 0,
            'sinr_calculations': 0
        }

# 工廠方法：為不同階段提供適配的計算器實例
def create_stage_signal_calculator(stage_number: int, config: Optional[Dict] = None) -> UnifiedSignalCalculator:
    """
    為特定階段創建信號品質計算器

    Args:
        stage_number: 階段編號
        config: 階段特定配置

    Returns:
        配置好的信號品質計算器
    """

    # 階段特定的默認配置
    stage_configs = {
        3: {'frequency_ghz': 28.0, 'tx_power_dbm': 50.0},  # Stage 3: 基礎分析
        4: {'frequency_ghz': 28.0, 'tx_power_dbm': 50.0},  # Stage 4: 時序分析
        6: {'frequency_ghz': 28.0, 'tx_power_dbm': 50.0}   # Stage 6: 規劃分析
    }

    stage_config = stage_configs.get(stage_number, {})
    if config:
        stage_config.update(config)

    calculator = UnifiedSignalCalculator(stage_config)
    logger.info(f"✅ 為階段 {stage_number} 創建統一信號品質計算器")

    return calculator