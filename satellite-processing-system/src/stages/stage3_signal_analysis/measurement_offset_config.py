"""
3GPP測量偏移配置系統 - Stage 4模組化組件

職責：
1. 管理3GPP NTN測量偏移參數
2. 提供Ofn（測量對象偏移）配置
3. 提供Ocn（小區個別偏移）配置
4. 支援動態偏移調整
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MeasurementOffsetConfig:
    """
    3GPP測量偏移配置系統
    
    基於3GPP TS 38.331標準實現：
    - Ofn: 測量對象特定偏移 (offsetMO in measObjectNR)
    - Ocn: 小區個別偏移 (cellIndividualOffset in measObjectNR/reportConfigNR)
    """
    
    def __init__(self):
        """初始化測量偏移配置系統"""
        self.logger = logging.getLogger(f"{__name__}.MeasurementOffsetConfig")
        
        # 3GPP標準偏移範圍 (-24 to 24 dB，步長0.5dB)
        self.offset_range_db = {"min": -24.0, "max": 24.0, "step": 0.5}
        
        # 測量對象偏移配置 (Ofn)
        # 按頻率或星座分組配置
        self.measurement_object_offsets = {
            # Starlink Ku頻段配置
            "starlink_12ghz": {
                "frequency_ghz": 12.0,
                "constellation": "starlink",
                "offset_db": 0.0,  # 預設無偏移
                "description": "Starlink Ku頻段下行鏈路測量對象偏移"
            },
            
            # OneWeb Ku頻段配置
            "oneweb_13ghz": {
                "frequency_ghz": 13.25,
                "constellation": "oneweb", 
                "offset_db": 0.0,  # 預設無偏移
                "description": "OneWeb Ku頻段下行鏈路測量對象偏移"
            }
        }
        
        # 小區個別偏移配置 (Ocn)
        # 按衛星ID分別配置
        self.cell_individual_offsets = {}
        
        # 配置統計
        self.config_statistics = {
            "measurement_objects_configured": len(self.measurement_object_offsets),
            "cells_configured": 0,
            "total_offset_adjustments": 0,
            "last_update_time": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info("✅ 3GPP測量偏移配置系統初始化完成")
        self.logger.info(f"   支援偏移範圍: {self.offset_range_db['min']} to {self.offset_range_db['max']} dB")
        self.logger.info(f"   測量對象數量: {len(self.measurement_object_offsets)}")
    
    def get_measurement_object_offset(self, constellation: str, frequency_ghz: float = None) -> float:
        """
        獲取測量對象特定偏移 (Ofn)
        
        Args:
            constellation: 星座名稱
            frequency_ghz: 頻率 (GHz)，可選
            
        Returns:
            Ofn偏移值 (dB)
        """
        # 根據星座和頻率查找配置
        for obj_key, config in self.measurement_object_offsets.items():
            if config["constellation"].lower() == constellation.lower():
                if frequency_ghz is None or abs(config["frequency_ghz"] - frequency_ghz) < 0.1:
                    self.logger.debug(f"找到測量對象偏移: {obj_key} = {config['offset_db']} dB")
                    return config["offset_db"]
        
        # 預設值
        self.logger.debug(f"未找到 {constellation} 的測量對象偏移，使用預設值 0.0 dB")
        return 0.0
    
    def get_cell_individual_offset(self, satellite_id: str, constellation: str = None) -> float:
        """
        獲取小區個別偏移 (Ocn)
        
        Args:
            satellite_id: 衛星ID
            constellation: 星座名稱，可選
            
        Returns:
            Ocn偏移值 (dB)
        """
        # 直接查找衛星ID
        if satellite_id in self.cell_individual_offsets:
            offset = self.cell_individual_offsets[satellite_id]["offset_db"]
            self.logger.debug(f"找到小區偏移: {satellite_id} = {offset} dB")
            return offset
        
        # 按星座查找預設值
        if constellation:
            constellation_key = f"{constellation.lower()}_default"
            if constellation_key in self.cell_individual_offsets:
                offset = self.cell_individual_offsets[constellation_key]["offset_db"]
                self.logger.debug(f"使用星座預設偏移: {constellation} = {offset} dB")
                return offset
        
        # 預設值
        self.logger.debug(f"未找到 {satellite_id} 的小區偏移，使用預設值 0.0 dB")
        return 0.0
    
    def set_measurement_object_offset(self, constellation: str, frequency_ghz: float, offset_db: float, 
                                    description: str = "") -> bool:
        """
        設定測量對象偏移 (Ofn)
        
        Args:
            constellation: 星座名稱
            frequency_ghz: 頻率 (GHz)
            offset_db: 偏移值 (dB)
            description: 描述
            
        Returns:
            設定是否成功
        """
        # 驗證偏移值範圍
        if not self._validate_offset_range(offset_db):
            return False
        
        # 生成配置鍵
        config_key = f"{constellation.lower()}_{frequency_ghz}ghz"
        
        # 設定配置
        self.measurement_object_offsets[config_key] = {
            "frequency_ghz": frequency_ghz,
            "constellation": constellation.lower(),
            "offset_db": offset_db,
            "description": description or f"{constellation} {frequency_ghz}GHz測量對象偏移",
            "created_time": datetime.now(timezone.utc).isoformat(),
            "3gpp_compliant": True
        }
        
        self.config_statistics["measurement_objects_configured"] = len(self.measurement_object_offsets)
        self.config_statistics["total_offset_adjustments"] += 1
        self.config_statistics["last_update_time"] = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"✅ 設定測量對象偏移: {config_key} = {offset_db} dB")
        return True
    
    def set_cell_individual_offset(self, satellite_id: str, offset_db: float, 
                                 constellation: str = None, description: str = "") -> bool:
        """
        設定小區個別偏移 (Ocn)
        
        Args:
            satellite_id: 衛星ID  
            offset_db: 偏移值 (dB)
            constellation: 星座名稱，可選
            description: 描述
            
        Returns:
            設定是否成功
        """
        # 驗證偏移值範圍
        if not self._validate_offset_range(offset_db):
            return False
        
        # 設定配置
        self.cell_individual_offsets[satellite_id] = {
            "satellite_id": satellite_id,
            "constellation": constellation.lower() if constellation else "unknown",
            "offset_db": offset_db,
            "description": description or f"衛星 {satellite_id} 小區個別偏移",
            "created_time": datetime.now(timezone.utc).isoformat(),
            "3gpp_compliant": True
        }
        
        self.config_statistics["cells_configured"] = len(self.cell_individual_offsets)
        self.config_statistics["total_offset_adjustments"] += 1
        self.config_statistics["last_update_time"] = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"✅ 設定小區偏移: {satellite_id} = {offset_db} dB")
        return True
    
    def set_constellation_default_offset(self, constellation: str, offset_db: float) -> bool:
        """
        設定星座預設小區偏移
        
        Args:
            constellation: 星座名稱
            offset_db: 偏移值 (dB)
            
        Returns:
            設定是否成功
        """
        if not self._validate_offset_range(offset_db):
            return False
        
        default_key = f"{constellation.lower()}_default"
        self.cell_individual_offsets[default_key] = {
            "satellite_id": default_key,
            "constellation": constellation.lower(),
            "offset_db": offset_db,
            "description": f"{constellation} 星座預設小區偏移",
            "created_time": datetime.now(timezone.utc).isoformat(),
            "is_default": True,
            "3gpp_compliant": True
        }
        
        self.logger.info(f"✅ 設定星座預設偏移: {constellation} = {offset_db} dB")
        return True
    
    def get_offset_configuration_for_satellite(self, satellite_id: str, constellation: str, 
                                             frequency_ghz: float) -> Dict[str, Any]:
        """
        獲取特定衛星的完整偏移配置
        
        Args:
            satellite_id: 衛星ID
            constellation: 星座名稱
            frequency_ghz: 頻率 (GHz)
            
        Returns:
            完整偏移配置字典
        """
        ofn_db = self.get_measurement_object_offset(constellation, frequency_ghz)
        ocn_db = self.get_cell_individual_offset(satellite_id, constellation)
        
        return {
            "satellite_id": satellite_id,
            "constellation": constellation,
            "frequency_ghz": frequency_ghz,
            "offset_configuration": {
                "ofn_db": ofn_db,  # 測量對象偏移
                "ocn_db": ocn_db,  # 小區個別偏移
                "total_offset_db": ofn_db + ocn_db,  # 總偏移
                "3gpp_formula_ready": True
            },
            "3gpp_compliance": {
                "ofn_source": "measObjectNR.offsetMO",
                "ocn_source": "measObjectNR.cellIndividualOffset or reportConfigNR.cellIndividualOffset",
                "standard": "3GPP TS 38.331",
                "offset_range_valid": self._validate_offset_range(ofn_db) and self._validate_offset_range(ocn_db)
            },
            "retrieved_time": datetime.now(timezone.utc).isoformat()
        }
    
    def _validate_offset_range(self, offset_db: float) -> bool:
        """
        驗證偏移值是否在3GPP標準範圍內
        
        Args:
            offset_db: 偏移值 (dB)
            
        Returns:
            是否有效
        """
        if not (self.offset_range_db["min"] <= offset_db <= self.offset_range_db["max"]):
            self.logger.error(f"偏移值 {offset_db} dB 超出3GPP標準範圍 [{self.offset_range_db['min']}, {self.offset_range_db['max']}]")
            return False
        
        # 檢查步長 (3GPP要求0.5dB步長)
        if abs(offset_db % self.offset_range_db["step"]) > 0.01:  # 浮點數容差
            self.logger.warning(f"偏移值 {offset_db} dB 不符合3GPP標準步長 {self.offset_range_db['step']} dB")
        
        return True
    
    def load_configuration_from_file(self, config_file_path: str) -> bool:
        """
        從配置文件載入偏移設定
        
        Args:
            config_file_path: 配置文件路徑
            
        Returns:
            載入是否成功
        """
        try:
            import json
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 載入測量對象偏移
            if "measurement_object_offsets" in config_data:
                self.measurement_object_offsets.update(config_data["measurement_object_offsets"])
            
            # 載入小區個別偏移
            if "cell_individual_offsets" in config_data:
                self.cell_individual_offsets.update(config_data["cell_individual_offsets"])
            
            self.logger.info(f"✅ 成功載入偏移配置: {config_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"載入偏移配置失敗: {e}")
            return False
    
    def save_configuration_to_file(self, config_file_path: str) -> bool:
        """
        儲存偏移設定到配置文件
        
        Args:
            config_file_path: 配置文件路徑
            
        Returns:
            儲存是否成功
        """
        try:
            import json
            config_data = {
                "measurement_object_offsets": self.measurement_object_offsets,
                "cell_individual_offsets": self.cell_individual_offsets,
                "config_statistics": self.config_statistics,
                "3gpp_compliance": {
                    "standard": "3GPP TS 38.331",
                    "offset_range_db": self.offset_range_db,
                    "saved_time": datetime.now(timezone.utc).isoformat()
                }
            }
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 成功儲存偏移配置: {config_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"儲存偏移配置失敗: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        獲取配置摘要
        
        Returns:
            配置摘要字典
        """
        return {
            "measurement_object_offsets": {
                "count": len(self.measurement_object_offsets),
                "configurations": list(self.measurement_object_offsets.keys())
            },
            "cell_individual_offsets": {
                "count": len(self.cell_individual_offsets),
                "configured_satellites": [k for k in self.cell_individual_offsets.keys() if not k.endswith("_default")]
            },
            "statistics": self.config_statistics,
            "3gpp_compliance": {
                "standard": "3GPP TS 38.331",
                "offset_range_db": self.offset_range_db,
                "all_offsets_valid": all(
                    self._validate_offset_range(config["offset_db"]) 
                    for config in list(self.measurement_object_offsets.values()) + list(self.cell_individual_offsets.values())
                )
            }
        }