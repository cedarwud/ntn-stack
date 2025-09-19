"""
信號品質計算器 - Stage 4模組化組件

職責：
1. 計算RSRP信號強度 (基於Friis公式)
2. 計算大氣衰減 (ITU-R P.618標準)
3. 評估信號品質等級
4. 生成信號強度時間序列
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SignalQualityCalculator:
    """
    純粹的信號品質計算器 - Stage 3專用
    
    移除了所有跨階段功能：
    - 移除 position_timeseries 處理（屬於Stage 4）
    - 移除批次處理功能（屬於Stage 4）
    - 專注於單點信號品質計算
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化信號品質計算器"""
        self.logger = logging.getLogger(f"{__name__}.SignalQualityCalculator")
        self.config = config or {}
        
        # 3GPP NTN標準參數
        self.frequency_ghz = self.config.get('frequency_ghz', 28.0)  # Ka頻段
        self.tx_power_dbm = self.config.get('tx_power_dbm', 50.0)   # 衛星發射功率
        self.antenna_gain_dbi = self.config.get('antenna_gain_dbi', 30.0)  # 天線增益
        
        self.logger.info("✅ 純粹信號品質計算器初始化完成")

    def calculate_signal_quality(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        計算單一衛星的信號品質
        
        Args:
            satellite_data: 衛星數據（不包含 position_timeseries）
            
        Returns:
            信號品質計算結果
        """
        try:
            # 提取軌道數據
            orbital_data = satellite_data.get('orbital_data', {})
            distance_km = orbital_data.get('distance_km', 0)
            elevation_deg = orbital_data.get('elevation_deg', 0)
            
            if distance_km <= 0 or elevation_deg <= 0:
                self.logger.warning("⚠️ 軌道數據不完整，無法計算信號品質")
                return self._create_default_quality_result()
            
            # 計算基本信號品質
            signal_quality = self._calculate_single_position_quality(orbital_data)
            
            # 評估信號品質等級
            quality_assessment = self._assess_signal_quality(signal_quality)
            
            return {
                'signal_quality': signal_quality,
                'quality_assessment': quality_assessment,
                'calculation_metadata': {
                    'frequency_ghz': self.frequency_ghz,
                    'calculation_method': 'single_position_3gpp_ntn'
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 信號品質計算失敗: {e}")
            return self._create_default_quality_result()

    def _calculate_single_position_quality(self, orbital_data: Dict[str, Any]) -> Dict[str, float]:
        """計算單一位置的信號品質"""
        try:
            distance_km = orbital_data.get('distance_km', 0)
            elevation_deg = orbital_data.get('elevation_deg', 0)
            
            # 計算自由空間路徑損耗 (Friis公式)
            fspl_db = self._calculate_free_space_path_loss(distance_km)
            
            # 計算大氣衰減 (ITU-R P.618)
            atmospheric_loss_db = self._calculate_atmospheric_loss(elevation_deg)
            
            # 計算接收信號強度
            rsrp_dbm = self._calculate_rsrp(fspl_db, atmospheric_loss_db)
            
            # 計算信號品質指標
            rsrq_db = self._calculate_rsrq(rsrp_dbm, elevation_deg)
            rs_sinr_db = self._calculate_rs_sinr(rsrp_dbm, elevation_deg)
            
            return {
                'rsrp_dbm': rsrp_dbm,
                'rsrq_db': rsrq_db,
                'rs_sinr_db': rs_sinr_db,
                'fspl_db': fspl_db,
                'atmospheric_loss_db': atmospheric_loss_db,
                'distance_km': distance_km,
                'elevation_deg': elevation_deg
            }
            
        except Exception as e:
            self.logger.error(f"❌ 單點信號品質計算失敗: {e}")
            return {}

    def _calculate_free_space_path_loss(self, distance_km: float) -> float:
        """計算自由空間路徑損耗 (3GPP TS 38.901)"""
        try:
            if distance_km <= 0:
                return 999.0  # 無效距離
                
            # FSPL = 20*log10(4π*d*f/c)
            # d: 距離(m), f: 頻率(Hz), c: 光速
            distance_m = distance_km * 1000
            frequency_hz = self.frequency_ghz * 1e9
            
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
                
            # 簡化的大氣衰減模型
            # 仰角越低，大氣路徑越長，衰減越大
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

    def _calculate_rsrp(self, fspl_db: float, atmospheric_loss_db: float) -> float:
        """計算RSRP (3GPP TS 38.214)"""
        try:
            # RSRP = Tx_Power + Tx_Gain - FSPL - Atmospheric_Loss
            rsrp_dbm = (self.tx_power_dbm + self.antenna_gain_dbi - 
                       fspl_db - atmospheric_loss_db)
            
            # RSRP範圍限制 (-140 dBm to -44 dBm per 3GPP)
            return max(-140.0, min(-44.0, rsrp_dbm))
            
        except Exception as e:
            self.logger.warning(f"⚠️ RSRP計算失敗: {e}")
            return -120.0

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

    def _assess_signal_quality(self, signal_quality: Dict[str, float]) -> Dict[str, Any]:
        """評估信號品質等級"""
        try:
            rsrp_dbm = signal_quality.get('rsrp_dbm', -120.0)
            rsrq_db = signal_quality.get('rsrq_db', -15.0)
            rs_sinr_db = signal_quality.get('rs_sinr_db', 0.0)
            
            # 3GPP NTN品質等級評估
            if rsrp_dbm >= -80 and rsrq_db >= -10 and rs_sinr_db >= 15:
                quality_level = "優秀"
                quality_score = 5
            elif rsrp_dbm >= -90 and rsrq_db >= -12 and rs_sinr_db >= 10:
                quality_level = "良好"
                quality_score = 4
            elif rsrp_dbm >= -100 and rsrq_db >= -15 and rs_sinr_db >= 5:
                quality_level = "中等"
                quality_score = 3
            elif rsrp_dbm >= -110 and rsrq_db >= -17 and rs_sinr_db >= 0:
                quality_level = "較差"
                quality_score = 2
            else:
                quality_level = "不良"
                quality_score = 1
            
            return {
                'quality_level': quality_level,
                'quality_score': quality_score,
                'is_usable': quality_score >= 3,
                'assessment_criteria': {
                    'rsrp_threshold': rsrp_dbm >= -100,
                    'rsrq_threshold': rsrq_db >= -15,
                    'sinr_threshold': rs_sinr_db >= 5
                }
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ 品質評估失敗: {e}")
            return {
                'quality_level': "未知",
                'quality_score': 1,
                'is_usable': False
            }

    def _create_default_quality_result(self) -> Dict[str, Any]:
        """創建預設的品質結果"""
        return {
            'signal_quality': {
                'rsrp_dbm': -120.0,
                'rsrq_db': -15.0,
                'rs_sinr_db': 0.0,
                'fspl_db': 200.0,
                'atmospheric_loss_db': 5.0
            },
            'quality_assessment': {
                'quality_level': "不良",
                'quality_score': 1,
                'is_usable': False
            },
            'calculation_metadata': {
                'frequency_ghz': self.frequency_ghz,
                'calculation_method': 'default_fallback'
            }
        }
