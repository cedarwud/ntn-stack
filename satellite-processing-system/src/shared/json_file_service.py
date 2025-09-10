#!/usr/bin/env python3
"""
統一 JSON 檔案服務 - 消除重複的檔案 I/O 程式碼
Unified JSON File Service - Eliminates duplicate file I/O code

提供標準化的 JSON 檔案讀寫功能，具備完整錯誤處理和日誌記錄
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class JSONFileService:
    """統一的 JSON 檔案處理服務"""
    
    @staticmethod
    def load_stage_data(file_path: str, stage_name: str = "") -> Dict[str, Any]:
        """
        統一的 JSON 載入方法
        
        Args:
            file_path: 要載入的檔案路徑
            stage_name: 階段名稱 (用於日誌記錄)
            
        Returns:
            載入的 JSON 數據，失敗時返回空字典
        """
        file_path = Path(file_path)
        stage_prefix = f"[{stage_name}] " if stage_name else ""
        
        logger.info(f"{stage_prefix}📥 載入 JSON 檔案: {file_path}")
        
        # 檢查檔案是否存在
        if not file_path.exists():
            logger.error(f"{stage_prefix}❌ 檔案不存在: {file_path}")
            return {}
        
        try:
            # 統一的載入方式
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 計算並記錄檔案大小
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"{stage_prefix}✅ JSON 載入成功: {file_path}")
            logger.info(f"{stage_prefix}   檔案大小: {file_size_mb:.1f} MB")
            
            # 記錄基本統計資訊
            if isinstance(data, dict):
                logger.info(f"{stage_prefix}   頂層鍵: {', '.join(list(data.keys())[:5])}")
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"{stage_prefix}❌ JSON 解析錯誤 ({file_path}): {e}")
            return {}
            
        except Exception as e:
            logger.error(f"{stage_prefix}❌ 載入檔案失敗 ({file_path}): {e}")
            return {}
    
    @staticmethod
    def save_stage_data(data: Dict[str, Any], output_path: str, stage_name: str = "") -> bool:
        """
        統一的 JSON 儲存方法
        
        Args:
            data: 要儲存的數據
            output_path: 輸出檔案路徑
            stage_name: 階段名稱 (用於日誌記錄)
            
        Returns:
            成功返回 True，失敗返回 False
        """
        output_path = Path(output_path)
        stage_prefix = f"[{stage_name}] " if stage_name else ""
        
        # 創建父目錄 (如果不存在)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 備份舊檔案 (如果存在)
        if output_path.exists():
            old_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"{stage_prefix}🗑️ 清理舊檔案: {output_path} ({old_size:.1f} MB)")
            output_path.unlink()
        
        try:
            # 統一的儲存方式
            logger.info(f"{stage_prefix}💾 儲存 JSON 檔案: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 記錄新檔案資訊
            new_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"{stage_prefix}✅ JSON 儲存成功: {output_path}")
            logger.info(f"{stage_prefix}   檔案大小: {new_size:.1f} MB")
            
            # 記錄基本統計資訊
            if isinstance(data, dict):
                if 'metadata' in data:
                    logger.info(f"{stage_prefix}   包含 metadata 區塊")
                if 'satellites' in data:
                    satellite_count = len(data['satellites']) if isinstance(data['satellites'], list) else 0
                    logger.info(f"{stage_prefix}   包含衛星數: {satellite_count}")
                if 'constellations' in data:
                    constellation_names = list(data['constellations'].keys())
                    logger.info(f"{stage_prefix}   包含星座: {', '.join(constellation_names)}")
            
            return True
            
        except Exception as e:
            logger.error(f"{stage_prefix}❌ 儲存檔案失敗 ({output_path}): {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        標準的檔案大小計算
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            檔案大小 (MB)，不存在時返回 0.0
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return 0.0
        
        return file_path.stat().st_size / (1024 * 1024)
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
        """
        驗證 JSON 數據結構
        
        Args:
            data: 要驗證的數據
            required_keys: 必須包含的鍵列表
            
        Returns:
            驗證成功返回 True，失敗返回 False
        """
        if not isinstance(data, dict):
            logger.error("❌ 數據不是字典格式")
            return False
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            logger.error(f"❌ 缺少必要的鍵: {', '.join(missing_keys)}")
            return False
        
        return True
    
    @staticmethod
    def merge_stage_outputs(stage_data_list: list, merge_strategy: str = "update") -> Dict[str, Any]:
        """
        合併多個階段的輸出數據
        
        Args:
            stage_data_list: 階段數據列表
            merge_strategy: 合併策略 ("update", "extend", "replace")
            
        Returns:
            合併後的數據
        """
        merged_data = {}
        
        for stage_data in stage_data_list:
            if not isinstance(stage_data, dict):
                continue
            
            if merge_strategy == "update":
                # 更新合併 (覆蓋同名鍵)
                merged_data.update(stage_data)
                
            elif merge_strategy == "extend":
                # 擴展合併 (對列表進行擴展)
                for key, value in stage_data.items():
                    if key in merged_data and isinstance(merged_data[key], list) and isinstance(value, list):
                        merged_data[key].extend(value)
                    else:
                        merged_data[key] = value
                        
            elif merge_strategy == "replace":
                # 替換合併 (完全替換)
                merged_data = stage_data
        
        return merged_data
    
    @staticmethod
    def create_error_response(error_message: str, stage_name: str = "") -> Dict[str, Any]:
        """
        創建標準化的錯誤響應
        
        Args:
            error_message: 錯誤訊息
            stage_name: 階段名稱
            
        Returns:
            錯誤響應字典
        """
        from datetime import datetime, timezone
        
        return {
            "success": False,
            "error": error_message,
            "stage": stage_name if stage_name else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {}
        }
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], stage_name: str = "") -> Dict[str, Any]:
        """
        創建標準化的成功響應
        
        Args:
            data: 數據內容
            stage_name: 階段名稱
            
        Returns:
            成功響應字典
        """
        from datetime import datetime, timezone
        
        return {
            "success": True,
            "stage": stage_name if stage_name else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

# 單例模式
_json_service_instance: Optional[JSONFileService] = None

def get_json_file_service() -> JSONFileService:
    """
    獲取統一的 JSON 檔案服務實例
    
    Returns:
        JSONFileService 實例
    """
    global _json_service_instance
    
    if _json_service_instance is None:
        _json_service_instance = JSONFileService()
        logger.info("✅ 統一 JSON 檔案服務初始化完成")
    
    return _json_service_instance

# 提供便捷的導入方式
__all__ = ['JSONFileService', 'get_json_file_service']