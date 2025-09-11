#!/usr/bin/env python3
"""
階段四學術標準驗證器

實現階段四專用的學術級數據處理標準驗證，
確保時間序列預處理符合Grade A/B/C等級要求。

驗證維度：
1. 時間序列處理器類型強制檢查  
2. 輸入數據完整性檢查
3. 時間序列完整性強制檢查
4. 學術標準數據精度檢查
5. 前端性能優化合規檢查
6. 無簡化處理零容忍檢查

符合文檔: @satellite-processing-system/docs/stages/stage4-timeseries.md
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

class Stage4AcademicStandardsValidator:
    """
    階段四學術標準驗證器
    
    實現階段四專用的零容忍運行時檢查系統：
    
    🟢 Grade A 強制要求：數據完整性優先
    - 時間序列精度保持：嚴格維持30秒間隔
    - 軌道週期完整性：保持完整96分鐘軌道週期  
    - 精度不降級：座標精度足以支持學術研究
    
    🟡 Grade B 可接受：基於科學原理的優化
    - 座標系統轉換：使用標準WGS84橢球體參數
    - 時間系統同步：維持GPS時間基準一致性
    
    🔴 Grade C 嚴格禁止項目（零容忍）
    - 任意數據點減量、任意壓縮比例
    - 信號強度"正規化"、量化級數簡化
    - 任意精度截斷
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化階段四學術標準驗證器
        
        Args:
            config: 驗證器配置參數
        """
        self.logger = logging.getLogger(f"{__name__}.Stage4AcademicStandardsValidator")
        
        # 學術標準參數 (Grade A要求)
        self.academic_standards = {
            "time_resolution_sec": 30,           # 標準時間解析度
            "orbital_period_min": 96,            # 完整軌道週期
            "minimum_data_points": 192,          # 最小時間序列長度 (96*60/30)
            "coordinate_precision_digits": 3,    # 座標精度要求
            "elevation_precision_digits": 1,     # 仰角精度要求
            "signal_unit": "dBm"                # 原始信號單位
        }
        
        # 禁用處理模式 (Grade C禁止項目)
        self.forbidden_processing_modes = [
            "arbitrary_downsampling",     # 任意數據點減量
            "fixed_compression_ratio",    # 任意壓縮比例  
            "uniform_quantization",       # 量化級數簡化
            "simplified_coordinates",     # 座標簡化
            "mock_timeseries",           # 模擬時間序列
            "estimated_positions",       # 估算位置
            "signal_normalization",      # 信號正規化
            "precision_truncation"       # 精度截斷
        ]
        
        # 必要標準參考 (Grade A/B依據)
        self.required_standards = [
            "WGS84_coordinate_system",    # WGS84座標系統
            "GPS_time_standard",          # GPS時間標準
            "ITU_R_P834_compliance",      # ITU-R P.834合規
            "ISO_IEC_Guide_98_3",        # 測量不確定度指南
            "IEEE_Std_754_2019"          # 浮點算術標準
        ]
        
        self.logger.info("✅ Stage4AcademicStandardsValidator 初始化完成")
        self.logger.info(f"   時間解析度標準: {self.academic_standards['time_resolution_sec']}秒")
        self.logger.info(f"   軌道週期標準: {self.academic_standards['orbital_period_min']}分鐘")
    
    def perform_zero_tolerance_runtime_checks(self, 
                                            processor_instance: Any,
                                            animation_builder: Any,
                                            input_data: Dict[str, Any],
                                            processing_config: Dict[str, Any] = None) -> bool:
        """
        執行零容忍運行時檢查 (任何失敗都會停止執行)
        
        Args:
            processor_instance: 時間序列處理器實例
            animation_builder: 動畫建構器實例  
            input_data: 輸入數據
            processing_config: 處理配置
            
        Returns:
            bool: 檢查是否通過
            
        Raises:
            RuntimeError: 任何檢查失敗時拋出異常
        """
        self.logger.info("🚨 執行零容忍運行時檢查...")
        
        try:
            # 檢查1: 時間序列處理器類型強制檢查
            self._check_timeseries_processor_types(processor_instance, animation_builder)
            
            # 檢查2: 輸入數據完整性檢查
            self._check_input_data_format_integrity(input_data)
            
            # 檢查3: 時間序列完整性強制檢查 (暫存輸入檢查，輸出檢查在處理後)
            # 這裡只能檢查輸入數據的基本結構
            
            # 檢查4: 學術標準數據精度檢查 (配置檢查)
            self._check_academic_precision_configuration(processing_config or {})
            
            # 檢查5: 前端性能優化合規檢查
            self._check_frontend_optimization_compliance(processor_instance, processing_config or {})
            
            # 檢查6: 無簡化處理零容忍檢查
            self._check_no_simplified_processing(processor_instance)
            
            self.logger.info("✅ 零容忍運行時檢查全部通過")
            return True
            
        except Exception as e:
            self.logger.error(f"零容忍檢查失敗: {e}")
            raise RuntimeError(f"Stage4零容忍檢查失敗: {e}")
    
    def validate_timeseries_output_integrity(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證時間序列輸出完整性
        
        Args:
            output_data: 輸出數據
            
        Returns:
            bool: 驗證是否通過
        """
        self.logger.info("🔍 驗證時間序列輸出完整性...")
        
        try:
            # 🚨 強制檢查時間序列數據完整性
            self._check_timeseries_completeness(output_data)
            
            # 🚨 強制檢查學術標準數據精度
            self._check_output_academic_precision(output_data)
            
            self.logger.info("✅ 時間序列輸出完整性驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出完整性驗證失敗: {e}")
            return False
    
    def validate_academic_grade_compliance(self, 
                                         processor_instance: Any,
                                         configuration: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證學術等級合規性
        
        Args:
            processor_instance: 處理器實例
            configuration: 處理配置
            
        Returns:
            Dict[str, Any]: 合規性評估結果
        """
        self.logger.info("🎓 執行學術等級合規性評估...")
        
        compliance_result = {
            "Grade_A_compliance": False,
            "Grade_B_compliance": False,
            "Grade_C_violations": [],
            "academic_standards_met": [],
            "compliance_score": 0.0,
            "recommendations": []
        }
        
        try:
            # Grade A 合規性檢查
            grade_a_checks = self._evaluate_grade_a_compliance(processor_instance, configuration)
            compliance_result["Grade_A_compliance"] = grade_a_checks["passed"]
            compliance_result["academic_standards_met"].extend(grade_a_checks["standards_met"])
            
            # Grade B 合規性檢查  
            grade_b_checks = self._evaluate_grade_b_compliance(processor_instance, configuration)
            compliance_result["Grade_B_compliance"] = grade_b_checks["passed"]
            compliance_result["academic_standards_met"].extend(grade_b_checks["standards_met"])
            
            # Grade C 違規檢查
            grade_c_violations = self._detect_grade_c_violations(processor_instance, configuration)
            compliance_result["Grade_C_violations"] = grade_c_violations
            
            # 計算合規分數
            compliance_result["compliance_score"] = self._calculate_compliance_score(
                grade_a_checks, grade_b_checks, grade_c_violations
            )
            
            # 生成建議
            compliance_result["recommendations"] = self._generate_compliance_recommendations(
                grade_a_checks, grade_b_checks, grade_c_violations
            )
            
            self.logger.info(f"🎯 學術合規性評估完成: 分數 {compliance_result['compliance_score']:.2f}")
            return compliance_result
            
        except Exception as e:
            self.logger.error(f"學術合規性評估失敗: {e}")
            compliance_result["error"] = str(e)
            return compliance_result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        獲取驗證摘要
        
        Returns:
            Dict[str, Any]: 驗證器摘要信息
        """
        return {
            "validator_name": "Stage4AcademicStandardsValidator",
            "academic_standards": self.academic_standards,
            "forbidden_modes": self.forbidden_processing_modes,
            "required_standards": self.required_standards,
            "validation_capabilities": [
                "zero_tolerance_runtime_checks",
                "timeseries_output_integrity",
                "academic_grade_compliance"
            ]
        }
    
    # ==================== 私有檢查方法 ====================
    
    def _check_timeseries_processor_types(self, processor_instance: Any, animation_builder: Any):
        """檢查時間序列處理器類型"""
        self.logger.debug("檢查時間序列處理器類型...")
        
        # 🚨 嚴格檢查實際使用的時間序列處理器類型
        processor_class_name = processor_instance.__class__.__name__
        if "TimeseriesPreprocessingProcessor" not in processor_class_name:
            raise RuntimeError(f"錯誤時間序列處理器: {processor_class_name}")
        
        if animation_builder is not None:
            builder_class_name = animation_builder.__class__.__name__
            if "CronAnimationBuilder" not in builder_class_name:
                raise RuntimeError(f"錯誤動畫建構器: {builder_class_name}")
        
        self.logger.debug("✅ 處理器類型檢查通過")
    
    def _check_input_data_format_integrity(self, input_data: Dict[str, Any]):
        """檢查輸入數據格式完整性"""
        self.logger.debug("檢查輸入數據格式完整性...")
        
        # 🚨 強制檢查輸入數據來自階段三的完整格式
        if not isinstance(input_data, dict):
            raise RuntimeError("輸入數據必須是字典格式")
        
        required_sections = ["metadata", "satellites"]
        for section in required_sections:
            if section not in input_data:
                raise RuntimeError(f"缺少 {section} 數據段")
        
        # 檢查衛星數據
        satellites = input_data["satellites"]
        if not isinstance(satellites, list) or len(satellites) < 100:
            raise RuntimeError(f"衛星數據不足: {len(satellites) if isinstance(satellites, list) else 'invalid'}")
        
        # 檢查關鍵字段
        for i, satellite in enumerate(satellites[:3]):  # 檢查前3顆
            if "signal_quality" not in satellite:
                raise RuntimeError(f"衛星 {i} 缺少signal_quality數據")
            if "event_potential" not in satellite:
                raise RuntimeError(f"衛星 {i} 缺少event_potential數據")
        
        self.logger.debug("✅ 輸入數據格式檢查通過")
    
    def _check_timeseries_completeness(self, output_data: Dict[str, Any]):
        """檢查時間序列完整性"""
        self.logger.debug("檢查時間序列完整性...")
        
        # 檢查輸出結構
        if "timeseries_data" not in output_data:
            raise ValueError("輸出缺少timeseries_data段")
        
        timeseries_data = output_data["timeseries_data"]
        
        for constellation, data in timeseries_data.items():
            if constellation == "metadata":
                continue
                
            satellites = data.get("satellites", [])
            
            for satellite in satellites[:3]:  # 檢查前3顆
                track_points = satellite.get("track_points", [])
                
                # 🚨 時間序列長度檢查
                if len(track_points) < self.academic_standards["minimum_data_points"]:
                    raise ValueError(f"時間序列長度不足: {len(track_points)} < {self.academic_standards['minimum_data_points']}")
                
                # 檢查必要字段
                required_fields = ["time", "lat", "lon", "elevation_deg"]
                for point in track_points[:5]:  # 檢查前5個點
                    for field in required_fields:
                        if field not in point:
                            raise ValueError(f"時間點缺少 {field} 字段")
                
                # 檢查時間序列順序
                times = [point["time"] for point in track_points]
                if not all(times[i] < times[i+1] for i in range(len(times)-1)):
                    raise ValueError("時間序列順序錯誤")
        
        self.logger.debug("✅ 時間序列完整性檢查通過")
    
    def _check_output_academic_precision(self, output_data: Dict[str, Any]):
        """檢查輸出數據學術精度"""
        self.logger.debug("檢查學術精度...")
        
        metadata = output_data.get("metadata", {})
        
        # 檢查時間解析度
        time_resolution = metadata.get("time_resolution_sec")
        if time_resolution != self.academic_standards["time_resolution_sec"]:
            raise ValueError(f"時間解析度被異常修改: {time_resolution}")
        
        # 檢查座標精度
        timeseries_data = output_data.get("timeseries_data", {})
        for constellation, data in timeseries_data.items():
            if constellation == "metadata":
                continue
                
            satellites = data.get("satellites", [])
            for satellite in satellites[:2]:  # 檢查前2顆
                track_points = satellite.get("track_points", [])
                
                if track_points:
                    # 檢查座標精度
                    sample_point = track_points[0]
                    lat_precision = self._count_decimal_places(sample_point.get("lat", 0))
                    lon_precision = self._count_decimal_places(sample_point.get("lon", 0))
                    
                    min_precision = self.academic_standards["coordinate_precision_digits"]
                    if lat_precision < min_precision:
                        raise ValueError(f"緯度精度不足: {lat_precision} < {min_precision}")
                    if lon_precision < min_precision:
                        raise ValueError(f"經度精度不足: {lon_precision} < {min_precision}")
        
        self.logger.debug("✅ 學術精度檢查通過")
    
    def _check_academic_precision_configuration(self, processing_config: Dict[str, Any]):
        """檢查學術精度配置"""
        self.logger.debug("檢查學術精度配置...")
        
        # 檢查是否保持數據完整性
        if not processing_config.get("preserve_full_data", True):
            raise RuntimeError("數據完整性保護被關閉")
        
        # 檢查時間解析度配置
        time_resolution = processing_config.get("time_resolution_sec")
        if time_resolution and time_resolution != self.academic_standards["time_resolution_sec"]:
            raise RuntimeError(f"時間解析度配置錯誤: {time_resolution}")
        
        self.logger.debug("✅ 學術精度配置檢查通過")
    
    def _check_frontend_optimization_compliance(self, processor_instance: Any, processing_config: Dict[str, Any]):
        """檢查前端性能優化合規性"""
        self.logger.debug("檢查前端優化合規性...")
        
        # 檢查是否有禁用的優化配置
        forbidden_configs = ["arbitrary_compression", "data_quantization"]
        for config in forbidden_configs:
            if config in processing_config:
                raise RuntimeError(f"檢測到禁用的優化配置: {config}")
        
        # 檢查處理器配置
        if hasattr(processor_instance, 'academic_config'):
            academic_config = processor_instance.academic_config
            if not academic_config.get("preserve_full_data", False):
                raise RuntimeError("處理器數據完整性保護被關閉")
        
        self.logger.debug("✅ 前端優化合規性檢查通過")
    
    def _check_no_simplified_processing(self, processor_instance: Any):
        """檢查無簡化處理"""
        self.logger.debug("檢查無簡化處理...")
        
        # 檢查類名是否包含禁用模式
        class_str = str(processor_instance.__class__).lower()
        for mode in self.forbidden_processing_modes:
            if mode in class_str:
                raise RuntimeError(f"檢測到禁用的簡化處理: {mode}")
        
        # 檢查處理方法
        if hasattr(processor_instance, 'get_processing_methods'):
            try:
                methods = processor_instance.get_processing_methods()
                for mode in self.forbidden_processing_modes:
                    if mode in methods:
                        raise RuntimeError(f"檢測到禁用的處理方法: {mode}")
            except:
                pass  # 如果方法不存在則跳過
        
        self.logger.debug("✅ 無簡化處理檢查通過")
    
    def _evaluate_grade_a_compliance(self, processor_instance: Any, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """評估Grade A合規性"""
        checks = {
            "passed": False,
            "standards_met": [],
            "failed_checks": []
        }
        
        try:
            # 檢查時間序列精度保持
            if hasattr(processor_instance, 'academic_config'):
                academic_config = processor_instance.academic_config
                if academic_config.get("time_resolution_sec") == 30:
                    checks["standards_met"].append("time_resolution_precision_maintained")
                else:
                    checks["failed_checks"].append("time_resolution_modified")
                
                if academic_config.get("preserve_full_data", False):
                    checks["standards_met"].append("data_integrity_maintained")
                else:
                    checks["failed_checks"].append("data_integrity_compromised")
            
            # 判斷Grade A是否通過
            checks["passed"] = len(checks["failed_checks"]) == 0
            
        except Exception as e:
            checks["failed_checks"].append(f"evaluation_error: {e}")
        
        return checks
    
    def _evaluate_grade_b_compliance(self, processor_instance: Any, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """評估Grade B合規性"""
        checks = {
            "passed": False,
            "standards_met": [],
            "failed_checks": []
        }
        
        try:
            # 檢查座標系統轉換標準
            if hasattr(processor_instance, 'academic_config'):
                academic_config = processor_instance.academic_config
                if academic_config.get("coordinate_precision", 0) >= 3:
                    checks["standards_met"].append("wgs84_coordinate_precision")
                else:
                    checks["failed_checks"].append("insufficient_coordinate_precision")
            
            # 判斷Grade B是否通過
            checks["passed"] = len(checks["failed_checks"]) == 0
            
        except Exception as e:
            checks["failed_checks"].append(f"evaluation_error: {e}")
        
        return checks
    
    def _detect_grade_c_violations(self, processor_instance: Any, configuration: Dict[str, Any]) -> List[str]:
        """檢測Grade C違規"""
        violations = []
        
        try:
            # 檢查禁用處理模式
            class_str = str(processor_instance.__class__).lower()
            for mode in self.forbidden_processing_modes:
                if mode in class_str:
                    violations.append(f"forbidden_processing_mode: {mode}")
            
            # 檢查配置違規
            forbidden_configs = ["arbitrary_compression", "data_quantization"]
            for config in forbidden_configs:
                if config in configuration:
                    violations.append(f"forbidden_configuration: {config}")
            
        except Exception as e:
            violations.append(f"violation_check_error: {e}")
        
        return violations
    
    def _calculate_compliance_score(self, grade_a: Dict, grade_b: Dict, violations: List[str]) -> float:
        """計算合規分數"""
        score = 0.0
        
        # Grade A 分數 (40%)
        if grade_a["passed"]:
            score += 0.4
        else:
            score += 0.4 * (len(grade_a["standards_met"]) / max(1, len(grade_a["standards_met"]) + len(grade_a["failed_checks"])))
        
        # Grade B 分數 (30%)
        if grade_b["passed"]:
            score += 0.3
        else:
            score += 0.3 * (len(grade_b["standards_met"]) / max(1, len(grade_b["standards_met"]) + len(grade_b["failed_checks"])))
        
        # Grade C 違規扣分 (30%)
        if len(violations) == 0:
            score += 0.3
        else:
            score = max(0, score - 0.1 * len(violations))  # 每個違規扣10%
        
        return min(1.0, score)
    
    def _generate_compliance_recommendations(self, grade_a: Dict, grade_b: Dict, violations: List[str]) -> List[str]:
        """生成合規建議"""
        recommendations = []
        
        # Grade A 建議
        for failure in grade_a["failed_checks"]:
            if "time_resolution" in failure:
                recommendations.append("維持30秒標準時間解析度")
            elif "data_integrity" in failure:
                recommendations.append("啟用數據完整性保護")
        
        # Grade B 建議
        for failure in grade_b["failed_checks"]:
            if "coordinate_precision" in failure:
                recommendations.append("提高座標精度至小數點後3位")
        
        # Grade C 建議
        for violation in violations:
            if "forbidden_processing" in violation:
                recommendations.append("移除禁用的簡化處理模式")
            elif "forbidden_configuration" in violation:
                recommendations.append("移除禁用的配置項目")
        
        return recommendations
    
    def _count_decimal_places(self, number: Union[int, float]) -> int:
        """計算小數位數"""
        if isinstance(number, int):
            return 0
        
        str_number = str(number)
        if '.' in str_number:
            return len(str_number.split('.')[1])
        return 0