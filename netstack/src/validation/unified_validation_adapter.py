#!/usr/bin/env python3
"""
UnifiedValidationAdapter - 統一簡化驗證適配器
提供簡單、實用的驗證機制，替代複雜的驗證邏輯
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnifiedValidationAdapter:
    """
    統一驗證適配器
    提供簡化的驗證接口，專注於功能驗證而非架構合規
    """
    
    def __init__(self, stage_number: int, stage_name: str):
        """
        初始化統一驗證適配器
        
        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱
        """
        self.stage_number = stage_number
        self.stage_name = stage_name
        logger.info(f"🔧 初始化階段{stage_number}統一驗證適配器")
    
    def validate_basic_functionality(self, output_data: Dict[str, Any], 
                                   output_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        驗證基本功能
        專注於檢查處理是否成功產生預期輸出
        
        Args:
            output_data: 處理器輸出的數據
            output_file_path: 輸出文件路徑（可選）
            
        Returns:
            Dict: 簡化的驗證結果
        """
        validation_result = {
            "stage": self.stage_number,
            "stage_name": self.stage_name,
            "validation_type": "basic_functionality",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # 基本數據檢查
            if not output_data:
                validation_result.update({
                    "status": "failed",
                    "issue": "輸出數據為空",
                    "critical": True
                })
                return validation_result
            
            # 檢查是否有預期的數據結構
            validation_checks = []
            
            # 通用檢查：是否有metadata
            if "metadata" in output_data:
                validation_checks.append(("metadata_present", True))
            else:
                validation_checks.append(("metadata_present", False))
            
            # 通用檢查：是否有處理統計
            has_stats = any(key in output_data for key in 
                          ["processing_statistics", "statistics", "processing_stats", "stats"])
            validation_checks.append(("processing_stats_present", has_stats))
            
            # 階段特定檢查
            stage_specific_checks = self._get_stage_specific_checks(output_data)
            validation_checks.extend(stage_specific_checks)
            
            # 評估總體結果
            passed_checks = sum(1 for _, passed in validation_checks if passed)
            total_checks = len(validation_checks)
            success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            validation_result.update({
                "status": "passed" if success_rate >= 70 else "failed",
                "success_rate": f"{success_rate:.1f}%",
                "passed_checks": passed_checks,
                "total_checks": total_checks,
                "details": {
                    "checks": dict(validation_checks),
                    "critical": success_rate < 50
                }
            })
            
            # 文件存在性檢查
            if output_file_path:
                file_exists = Path(output_file_path).exists()
                validation_result["details"]["output_file_exists"] = file_exists
                if not file_exists:
                    validation_result["status"] = "failed"
                    validation_result["issue"] = f"輸出文件不存在: {output_file_path}"
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ 階段{self.stage_number}驗證失敗: {e}")
            validation_result.update({
                "status": "failed",
                "issue": f"驗證過程異常: {str(e)}",
                "critical": True
            })
            return validation_result
    
    def _get_stage_specific_checks(self, output_data: Dict[str, Any]) -> list:
        """獲取階段特定的檢查項目"""
        stage_checkers = {
            1: self._check_stage1_orbital_data,
            2: self._check_stage2_filtering_data,
            3: self._check_stage3_signal_data,
            4: self._check_stage4_timeseries_data,
            5: self._check_stage5_integration_data,
            6: self._check_stage6_pool_data
        }
        
        checker = stage_checkers.get(self.stage_number)
        if checker:
            return checker(output_data)
        else:
            return []
    
    def _check_stage1_orbital_data(self, data: Dict[str, Any]) -> list:
        """階段一：軌道計算數據檢查"""
        checks = []
        
        # 檢查是否有星座數據
        constellations = data.get("constellations", {})
        checks.append(("has_constellations", bool(constellations)))
        
        # 檢查衛星數量
        total_satellites = sum(len(const.get("satellites", [])) for const in constellations.values())
        checks.append(("has_satellites", total_satellites > 0))
        checks.append(("reasonable_satellite_count", 100 <= total_satellites <= 20000))
        
        return checks
    
    def _check_stage2_filtering_data(self, data: Dict[str, Any]) -> list:
        """階段二：智能篩選數據檢查"""
        checks = []
        
        # 檢查篩選結果
        constellations = data.get("constellations", {})
        checks.append(("filtering_results_present", bool(constellations)))
        
        # 檢查是否有篩選統計
        has_filter_stats = any("filter" in key.lower() for key in data.keys())
        checks.append(("filtering_statistics_present", has_filter_stats))
        
        return checks
    
    def _check_stage3_signal_data(self, data: Dict[str, Any]) -> list:
        """階段三：信號分析數據檢查"""
        checks = []
        
        # 檢查信號分析結果
        constellations = data.get("constellations", {})
        checks.append(("signal_analysis_results_present", bool(constellations)))
        
        # 檢查是否有3GPP事件數據
        has_threegpp = "threegpp_events" in data or any("3gpp" in key.lower() for key in data.keys())
        checks.append(("threegpp_events_present", has_threegpp))
        
        return checks
    
    def _check_stage4_timeseries_data(self, data: Dict[str, Any]) -> list:
        """階段四：時間序列數據檢查"""
        checks = []
        
        # 檢查是否有增強格式數據
        has_enhanced = "enhanced_format" in data
        checks.append(("enhanced_format_present", has_enhanced))
        
        # 檢查是否有動畫數據
        has_animation = "animation_data" in data or "builder_type" in data
        checks.append(("animation_data_present", has_animation))
        
        return checks
    
    def _check_stage5_integration_data(self, data: Dict[str, Any]) -> list:
        """階段五：數據整合檢查"""
        checks = []
        
        # 檢查整合數據
        has_integrated = "integrated_data" in data
        checks.append(("integrated_data_present", has_integrated))
        
        # 檢查分層數據
        has_layered = "layered_elevation_data" in data
        checks.append(("layered_data_present", has_layered))
        
        return checks
    
    def _check_stage6_pool_data(self, data: Dict[str, Any]) -> list:
        """階段六：動態池數據檢查"""
        checks = []
        
        # 檢查衛星池
        has_pools = "satellite_pools" in data or "dynamic_pools" in data
        checks.append(("satellite_pools_present", has_pools))
        
        # 檢查覆蓋分析
        has_coverage = "coverage_analysis" in data
        checks.append(("coverage_analysis_present", has_coverage))
        
        return checks
    
    def create_simple_report(self, validation_result: Dict[str, Any]) -> str:
        """創建簡單的驗證報告"""
        status = validation_result["status"]
        stage_name = validation_result["stage_name"]
        
        if status == "passed":
            return f"✅ {stage_name}: 驗證通過 ({validation_result.get(success_rate, N/A)})"
        else:
            issue = validation_result.get("issue", "未知問題")
            return f"❌ {stage_name}: 驗證失敗 - {issue}"


# 便利函數，用於替代複雜的驗證器
def create_simple_validator(stage_number: int, stage_name: str) -> UnifiedValidationAdapter:
    """
    創建簡單驗證器的便利函數
    
    Args:
        stage_number: 階段編號
        stage_name: 階段名稱
        
    Returns:
        UnifiedValidationAdapter: 統一驗證適配器實例
    """
    return UnifiedValidationAdapter(stage_number, stage_name)


def validate_stage_output_simple(stage_number: int, output_data: Dict[str, Any], 
                                output_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    簡單的階段輸出驗證函數
    
    Args:
        stage_number: 階段編號
        output_data: 輸出數據
        output_file_path: 輸出文件路徑
        
    Returns:
        Dict: 驗證結果
    """
    stage_names = {
        1: "軌道計算",
        2: "智能篩選", 
        3: "信號分析",
        4: "時間序列預處理",
        5: "數據整合",
        6: "動態池規劃"
    }
    
    validator = UnifiedValidationAdapter(stage_number, stage_names.get(stage_number, f"階段{stage_number}"))
    return validator.validate_basic_functionality(output_data, output_file_path)
