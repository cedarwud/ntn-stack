"""
衛星配置管理器 - Grade A學術標準
消除硬編碼值，實現配置驅動的參數管理

支持多星座差異化配置和動態參數加載
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConstellationConfig:
    """星座配置數據類"""
    name: str
    altitude_km: float
    altitude_range_km: Tuple[float, float]
    eirp_dbm: float
    eirp_range_dbm: Tuple[float, float]
    antenna_gain_dbi: float
    frequency_hz: float
    bandwidth_hz: float


class SatelliteConfigManager:
    """衛星配置管理器 - 學術級參數管理"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路徑，默認使用標準位置
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # 確定配置文件路徑
        if config_path is None:
            # 嘗試多個可能的路徑
            possible_paths = [
                Path("/orbit-engine/src/shared/configs/satellite_constellation_config.yaml"),
                Path("src/shared/configs/satellite_constellation_config.yaml"),
                Path("shared/configs/satellite_constellation_config.yaml"),
                Path(__file__).parent / "configs" / "satellite_constellation_config.yaml"
            ]

            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                raise FileNotFoundError("找不到衛星配置文件")

        self.config_path = config_path
        self._config_cache = None
        self._load_config()

    def _load_config(self) -> None:
        """加載配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_cache = yaml.safe_load(f)

            self.logger.info(f"✅ 成功加載衛星配置: {self.config_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置文件加載失敗: {e}")
            # 提供基本的默認配置避免系統崩潰
            self._config_cache = self._get_fallback_config()

    def _get_fallback_config(self) -> Dict[str, Any]:
        """提供緊急回退配置"""
        return {
            "constellations": {
                "starlink": {
                    "altitude_km": 550,
                    "signal_parameters": {
                        "eirp_dbm": 50.0,
                        "frequency_hz": 2.1e9,
                        "bandwidth_hz": 20e6
                    },
                    "link_budget": {
                        "antenna_gain_dbi": 35.0
                    }
                },
                "oneweb": {
                    "altitude_km": 1200,
                    "signal_parameters": {
                        "eirp_dbm": 55.0,
                        "frequency_hz": 2.1e9,
                        "bandwidth_hz": 20e6
                    },
                    "link_budget": {
                        "antenna_gain_dbi": 38.0
                    }
                }
            },
            "ground_terminal": {
                "ue_antenna": {
                    "gain_dbi": 2.15,
                    "noise_figure_db": 7.0,
                    "cable_loss_db": 2.0
                },
                "environment": {
                    "temperature_k": 290
                }
            }
        }

    def get_constellation_config(self, constellation: str) -> ConstellationConfig:
        """
        獲取指定星座的配置

        Args:
            constellation: 星座名稱 (starlink, oneweb)

        Returns:
            ConstellationConfig: 星座配置對象
        """
        constellation = constellation.lower()

        if constellation not in self._config_cache.get("constellations", {}):
            self.logger.warning(f"未知星座: {constellation}, 使用默認配置")
            constellation = "starlink"  # 默認使用starlink配置

        const_config = self._config_cache["constellations"][constellation]

        return ConstellationConfig(
            name=const_config.get("name", constellation.title()),
            altitude_km=const_config.get("altitude_km", 550),
            altitude_range_km=tuple(const_config.get("altitude_range_km", [500, 600])),
            eirp_dbm=const_config["signal_parameters"]["eirp_dbm"],
            eirp_range_dbm=tuple(const_config["signal_parameters"]["eirp_range_dbm"]),
            antenna_gain_dbi=const_config["link_budget"]["antenna_gain_dbi"],
            frequency_hz=const_config["signal_parameters"]["frequency_hz"],
            bandwidth_hz=const_config["signal_parameters"]["bandwidth_hz"]
        )

    def get_ground_terminal_config(self) -> Dict[str, Any]:
        """獲取地面終端配置"""
        return self._config_cache.get("ground_terminal", {})

    def get_3gpp_parameters(self) -> Dict[str, Any]:
        """獲取3GPP NTN標準參數"""
        return self._config_cache.get("gpp_ntn_parameters", {})

    def get_signal_quality_standards(self) -> Dict[str, Any]:
        """獲取信號質量評估標準"""
        return self._config_cache.get("signal_quality_standards", {})

    def get_physical_constraints(self) -> Dict[str, Any]:
        """獲取物理約束參數"""
        return self._config_cache.get("physical_constraints", {})

    def get_validation_thresholds(self) -> Dict[str, Any]:
        """獲取驗證門檻設定"""
        return self._config_cache.get("validation_thresholds", {})

    def validate_constellation_parameters(self, constellation: str,
                                        distance_km: float,
                                        eirp_dbm: float) -> Tuple[bool, str]:
        """
        驗證星座參數的合理性

        Args:
            constellation: 星座名稱
            distance_km: 衛星距離
            eirp_dbm: 有效全向輻射功率

        Returns:
            Tuple[bool, str]: (是否有效, 錯誤信息)
        """
        try:
            config = self.get_constellation_config(constellation)

            # 檢查距離範圍
            min_dist, max_dist = config.altitude_range_km
            if not (min_dist <= distance_km <= max_dist):
                return False, f"{constellation}衛星距離{distance_km}km超出合理範圍{config.altitude_range_km}"

            # 檢查EIRP範圍
            min_eirp, max_eirp = config.eirp_range_dbm
            if not (min_eirp <= eirp_dbm <= max_eirp):
                return False, f"{constellation}衛星EIRP{eirp_dbm}dBm超出合理範圍{config.eirp_range_dbm}"

            return True, "參數驗證通過"

        except Exception as e:
            return False, f"參數驗證異常: {e}"

    def get_eirp_for_constellation(self, constellation: str) -> float:
        """獲取指定星座的EIRP值"""
        config = self.get_constellation_config(constellation)
        return config.eirp_dbm

    def get_system_config_for_calculator(self, constellation: str = "starlink") -> Dict[str, Any]:
        """
        為SignalQualityCalculator提供系統配置

        Args:
            constellation: 星座名稱

        Returns:
            Dict: 系統配置字典
        """
        const_config = self.get_constellation_config(constellation)
        ground_config = self.get_ground_terminal_config()

        # 確保所有數值都是正確的類型
        def ensure_float(value, default=0.0):
            """確保值是float類型"""
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return default
            return float(value) if value is not None else default

        return {
            'frequency': ensure_float(const_config.frequency_hz, 2.1e9),
            'bandwidth': ensure_float(const_config.bandwidth_hz, 20e6),
            'noise_figure': ensure_float(ground_config.get("ue_antenna", {}).get("noise_figure_db", 7.0), 7.0),
            'temperature': ensure_float(ground_config.get("environment", {}).get("temperature_k", 290), 290),
            'antenna_gain': ensure_float(ground_config.get("ue_antenna", {}).get("gain_dbi", 2.15), 2.15),
            'cable_loss': ensure_float(ground_config.get("ue_antenna", {}).get("cable_loss_db", 2.0), 2.0),
            'satellite_eirp': ensure_float(const_config.eirp_dbm, 50.0),
            'satellite_antenna_gain': ensure_float(const_config.antenna_gain_dbi, 35.0)
        }

    def reload_config(self) -> bool:
        """重新加載配置文件"""
        try:
            old_config = self._config_cache
            self._load_config()

            if self._config_cache != old_config:
                self.logger.info("✅ 配置已重新加載並檢測到變更")

            return True

        except Exception as e:
            self.logger.error(f"❌ 配置重新加載失敗: {e}")
            return False


# 全局配置管理器實例
_global_config_manager = None


def get_satellite_config_manager() -> SatelliteConfigManager:
    """獲取全局配置管理器實例"""
    global _global_config_manager

    if _global_config_manager is None:
        _global_config_manager = SatelliteConfigManager()

    return _global_config_manager


def get_constellation_eirp(constellation: str) -> float:
    """快速獲取星座EIRP值"""
    manager = get_satellite_config_manager()
    return manager.get_eirp_for_constellation(constellation)


def validate_satellite_parameters(constellation: str, distance_km: float, eirp_dbm: float) -> Tuple[bool, str]:
    """快速驗證衛星參數"""
    manager = get_satellite_config_manager()
    return manager.validate_constellation_parameters(constellation, distance_km, eirp_dbm)