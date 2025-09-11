"""
Stage 3處理器 - 時間序列預處理模組化版本

功能：
1. 載入Stage 2可見性過濾輸出
2. 轉換為動畫時間序列格式
3. 建構前端動畫數據結構
4. 執行學術級別合規驗證
5. 輸出多種格式的處理結果

架構：
- 繼承BaseStageProcessor基礎架構
- 整合5個專用組件完成複雜處理
- 支持多種輸出格式和學術級驗證
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from ...shared.base_processor import BaseStageProcessor
from .visibility_data_loader import VisibilityDataLoader
from .timeseries_converter import TimeseriesConverter
from .animation_builder import AnimationBuilder
from .academic_validator import AcademicValidator
from .output_formatter import OutputFormatter

logger = logging.getLogger(__name__)

class Stage3Processor(BaseStageProcessor):
    """Stage 3: 時間序列預處理器 - 重構版"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化Stage 3處理器"""
        # 呼叫基礎處理器的初始化
        super().__init__(stage_number=3, stage_name="timeseries_preprocessing", config=config)
        
        self.logger.info("🎬 初始化Stage 3時間序列預處理器...")
        
        # 讀取配置
        self.animation_mode = config.get('animation_mode', 'enhanced') if config else 'enhanced'
        self.web_optimization = config.get('web_optimization', True) if config else True
        self.academic_validation = config.get('academic_validation', True) if config else True
        self.output_formats = config.get('output_formats', ['enhanced_animation']) if config else ['enhanced_animation']
        self.time_compression_ratio = config.get('time_compression_ratio', 100) if config else 100
        
        # 初始化組件
        try:
            self.data_loader = VisibilityDataLoader()
            self.timeseries_converter = TimeseriesConverter()
            self.animation_builder = AnimationBuilder()
            self.academic_validator = AcademicValidator()
            self.output_formatter = OutputFormatter()
            
            self.logger.info("✅ Stage 3所有組件初始化成功")
            
        except Exception as e:
            self.logger.error(f"❌ Stage 3組件初始化失敗: {e}")
            raise RuntimeError(f"Stage 3初始化失敗: {e}")
        
        # 處理統計
        self.processing_stats = {
            "satellites_loaded": 0,
            "satellites_processed": 0,
            "animation_frames_created": 0,
            "constellations_animated": 0,
            "academic_validation_passed": 0,
            "output_formats_generated": 0
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據
        
        Stage 3需要Stage 2的可見性過濾輸出
        """
        self.logger.info("🔍 驗證Stage 3輸入數據...")
        
        try:
            # 檢查Stage 2輸出文件存在性
            stage2_data = self.data_loader.load_stage2_output()
            
            # 驗證數據完整性
            validation_result = self.data_loader.validate_visibility_data_completeness(stage2_data)
            
            if not validation_result["overall_valid"]:
                self.logger.error("Stage 2可見性數據驗證失敗:")
                for issue in validation_result["issues"]:
                    self.logger.error(f"  - {issue}")
                return False
            
            self.logger.info("✅ Stage 2可見性數據驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸入數據驗證失敗: {e}")
            return False
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        執行Stage 3的核心處理邏輯
        
        處理步驟:
        1. 載入Stage 2可見性過濾輸出
        2. 轉換為動畫時間序列格式
        3. 建構前端動畫數據結構
        4. 執行學術級合規驗證
        5. 格式化多種輸出格式
        """
        self.logger.info("🎬 開始Stage 3時間序列預處理...")
        
        try:
            # 步驟1: 載入Stage 2數據
            self.logger.info("📥 步驟1: 載入Stage 2可見性數據")
            stage2_data = self.data_loader.load_stage2_output()
            
            load_stats = self.data_loader.get_load_statistics()
            self.processing_stats["satellites_loaded"] = load_stats["satellites_loaded"]
            
            # 步驟2: 轉換為時間序列
            self.logger.info("⏱️ 步驟2: 轉換為動畫時間序列")
            satellites = stage2_data.get("satellites", [])
            timeseries_data = self.timeseries_converter.convert_visibility_to_timeseries(satellites)
            
            converter_stats = self.timeseries_converter.get_conversion_statistics()
            self.processing_stats["satellites_processed"] = converter_stats["total_satellites_processed"]
            
            # 步驟3: 建構動畫數據
            self.logger.info("🎨 步驟3: 建構前端動畫數據")
            animation_data = self.animation_builder.build_animation_data(timeseries_data)
            
            builder_stats = self.animation_builder.get_build_statistics()
            self.processing_stats["animation_frames_created"] = builder_stats["total_frames"]
            self.processing_stats["constellations_animated"] = builder_stats["constellations_processed"]
            
            # 步驟4: 學術級驗證
            validation_passed = True
            if self.academic_validation:
                self.logger.info("🎓 步驟4: 執行學術級合規驗證")
                validation_result = self.academic_validator.validate_timeseries_academic_compliance(
                    timeseries_data,
                    animation_data
                )
                
                if not validation_result["overall_compliance"]:
                    self.logger.warning("學術級驗證警告:")
                    for issue in validation_result["compliance_issues"]:
                        self.logger.warning(f"  - {issue}")
                    validation_passed = False
                else:
                    self.processing_stats["academic_validation_passed"] = 1
            
            # 步驟5: 格式化輸出
            self.logger.info("📋 步驟5: 格式化多種輸出格式")
            formatted_results = {}
            
            for output_format in self.output_formats:
                try:
                    formatted_output = self.output_formatter.format_stage3_output(
                        timeseries_data=timeseries_data,
                        animation_data=animation_data,
                        stage2_metadata=stage2_data.get("metadata", {}),
                        processing_stats=self.processing_stats,
                        output_format=output_format,
                        validation_passed=validation_passed
                    )
                    
                    formatted_results[output_format] = formatted_output
                    self.processing_stats["output_formats_generated"] += 1
                    
                except Exception as e:
                    self.logger.error(f"格式化輸出失敗 {output_format}: {e}")
                    continue
            
            if not formatted_results:
                raise ValueError("所有輸出格式生成失敗")
            
            # 返回主要格式或第一個可用格式
            main_result = formatted_results.get('enhanced_animation') or next(iter(formatted_results.values()))
            
            # 添加額外格式到metadata中
            if len(formatted_results) > 1:
                main_result["metadata"]["additional_formats"] = {
                    fmt: result["metadata"]["output_summary"] 
                    for fmt, result in formatted_results.items() 
                    if fmt != 'enhanced_animation'
                }
            
            self.logger.info(f"✅ Stage 3處理完成: {self.processing_stats['satellites_processed']} 顆衛星, "
                           f"{self.processing_stats['animation_frames_created']} 動畫幀")
            
            return main_result
            
        except Exception as e:
            self.logger.error(f"Stage 3處理失敗: {e}")
            raise RuntimeError(f"Stage 3時間序列預處理失敗: {e}")
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """驗證輸出數據的有效性"""
        self.logger.info("🔍 驗證Stage 3輸出數據...")
        
        try:
            # 檢查基本結構
            if not isinstance(output_data, dict):
                self.logger.error("輸出數據必須是字典格式")
                return False
            
            if "data" not in output_data or "metadata" not in output_data:
                self.logger.error("輸出數據缺少必要的data或metadata欄位")
                return False
            
            # 檢查動畫數據
            data_section = output_data["data"]
            
            # 驗證時間序列數據
            if "timeseries_data" not in data_section:
                self.logger.error("輸出數據缺少時間序列數據")
                return False
            
            timeseries_data = data_section["timeseries_data"]
            satellites = timeseries_data.get("satellites", [])
            
            if not satellites:
                self.logger.error("輸出數據中無衛星時間序列數據")
                return False
            
            # 驗證動畫數據
            if "animation_data" not in data_section:
                self.logger.error("輸出數據缺少動畫數據")
                return False
            
            animation_data = data_section["animation_data"]
            
            # 檢查關鍵動畫組件
            required_animation_components = ["global_timeline", "constellation_animations"]
            for component in required_animation_components:
                if component not in animation_data:
                    self.logger.error(f"動畫數據缺少 {component} 組件")
                    return False
            
            # 檢查metadata完整性
            metadata = output_data["metadata"]
            required_fields = ["stage_number", "stage_name", "processing_timestamp", "output_summary"]
            
            for field in required_fields:
                if field not in metadata:
                    self.logger.error(f"metadata缺少必要欄位: {field}")
                    return False
            
            # 使用學術驗證器進行深度檢查
            if self.academic_validation:
                validation_result = self.academic_validator.validate_timeseries_academic_compliance(
                    timeseries_data, animation_data
                )
                
                if not validation_result["overall_compliance"]:
                    self.logger.error("學術級合規驗證失敗:")
                    for issue in validation_result["compliance_issues"]:
                        self.logger.error(f"  - {issue}")
                    return False
            
            self.logger.info("✅ Stage 3輸出數據驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出數據驗證失敗: {e}")
            return False
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """保存處理結果到文件"""
        try:
            # 構建輸出文件路徑
            output_file = self.output_dir / "timeseries_preprocessing_output.json"
            
            # 確保輸出目錄存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存結果到JSON文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Stage 3結果已保存: {output_file}")
            
            # 保存處理統計到單獨文件
            stats_file = self.output_dir / "stage3_processing_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "processing_statistics": self.processing_stats,
                    "loader_statistics": self.data_loader.get_load_statistics(),
                    "converter_statistics": self.timeseries_converter.get_conversion_statistics(),
                    "builder_statistics": self.animation_builder.get_build_statistics(),
                    "validator_statistics": self.academic_validator.get_validation_statistics(),
                    "formatter_statistics": self.output_formatter.get_formatting_statistics(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            # 如果有多種格式，保存額外格式
            additional_formats = results.get("metadata", {}).get("additional_formats", {})
            if additional_formats:
                for format_name, format_summary in additional_formats.items():
                    format_file = self.output_dir / f"timeseries_preprocessing_output_{format_name}.json"
                    # 這裡應該保存完整的格式數據，但由於已經在主結果中，暫時記錄摘要
                    with open(format_file.with_suffix('.summary.json'), 'w', encoding='utf-8') as f:
                        json.dump(format_summary, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存Stage 3結果失敗: {e}")
            raise IOError(f"無法保存Stage 3結果: {e}")
    
    def extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        try:
            metadata = results.get("metadata", {})
            data_section = results.get("data", {})
            timeseries_data = data_section.get("timeseries_data", {})
            animation_data = data_section.get("animation_data", {})
            
            # 計算時間序列統計
            satellites = timeseries_data.get("satellites", [])
            total_timeseries_points = sum(
                len(sat.get("enhanced_timeseries", [])) for sat in satellites
            )
            
            # 計算動畫統計
            constellation_animations = animation_data.get("constellation_animations", {})
            total_animation_frames = sum(
                len(const_anim.get("keyframes", [])) 
                for const_anim in constellation_animations.values()
            )
            
            # 計算覆蓋範圍統計
            coverage_analysis = animation_data.get("coverage_analysis", {})
            
            key_metrics = {
                "total_satellites_processed": len(satellites),
                "total_timeseries_points": total_timeseries_points,
                "total_animation_frames": total_animation_frames,
                "constellations_animated": len(constellation_animations),
                "processing_duration": self.processing_duration,
                "animation_config": {
                    "mode": self.animation_mode,
                    "web_optimization": self.web_optimization,
                    "time_compression_ratio": self.time_compression_ratio
                },
                "data_quality_metrics": {
                    "academic_validation_passed": self.processing_stats["academic_validation_passed"],
                    "output_formats_generated": self.processing_stats["output_formats_generated"],
                    "avg_timeseries_points_per_satellite": total_timeseries_points / len(satellites) if satellites else 0
                },
                "coverage_metrics": {
                    "total_coverage_events": coverage_analysis.get("total_coverage_events", 0),
                    "coverage_percentage": coverage_analysis.get("overall_coverage_percentage", 0),
                    "handover_scenarios": len(coverage_analysis.get("handover_scenarios", []))
                },
                "performance_metrics": {
                    "animation_compression_ratio": self._calculate_compression_ratio(animation_data),
                    "web_optimization_savings": self._calculate_optimization_savings(animation_data)
                }
            }
            
            return key_metrics
            
        except Exception as e:
            self.logger.error(f"提取關鍵指標失敗: {e}")
            return {"error": f"指標提取失敗: {e}"}
    
    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """執行驗證檢查"""
        try:
            validation_result = {
                "passed": True,
                "totalChecks": 0,
                "passedChecks": 0,
                "failedChecks": 0,
                "criticalChecks": [],
                "allChecks": {},
                "validation_level_info": {
                    "level": "COMPREHENSIVE",
                    "academic_grade": "A",
                    "framework": "unified_pipeline_v2"
                }
            }
            
            checks = [
                ("data_structure_check", self._check_data_structure(results)),
                ("timeseries_completeness_check", self._check_timeseries_completeness(results)),
                ("animation_integrity_check", self._check_animation_integrity(results)),
                ("metadata_completeness_check", self._check_metadata_completeness(results)),
                ("academic_compliance_check", self._check_academic_compliance(results)),
                ("temporal_consistency_check", self._check_temporal_consistency(results)),
                ("web_optimization_check", self._check_web_optimization(results))
            ]
            
            for check_name, check_result in checks:
                validation_result["allChecks"][check_name] = check_result
                validation_result["totalChecks"] += 1
                
                if check_result:
                    validation_result["passedChecks"] += 1
                else:
                    validation_result["failedChecks"] += 1
                    validation_result["criticalChecks"].append({
                        "check": check_name,
                        "status": "FAILED"
                    })
            
            # 整體通過狀態
            if validation_result["failedChecks"] > 0:
                validation_result["passed"] = False
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"驗證檢查失敗: {e}")
            return {
                "passed": False,
                "error": f"驗證檢查異常: {e}",
                "totalChecks": 0,
                "passedChecks": 0,
                "failedChecks": 1
            }
    
    # === 輔助方法 ===
    
    def _calculate_compression_ratio(self, animation_data: Dict[str, Any]) -> float:
        """計算動畫壓縮比率"""
        try:
            global_timeline = animation_data.get("global_timeline", {})
            total_timepoints = global_timeline.get("total_timepoints", 0)
            compressed_keyframes = global_timeline.get("compressed_keyframes", 0)
            
            if compressed_keyframes == 0:
                return 0.0
                
            return total_timepoints / compressed_keyframes
            
        except Exception:
            return 0.0
    
    def _calculate_optimization_savings(self, animation_data: Dict[str, Any]) -> float:
        """計算網頁優化節省比例"""
        try:
            optimization_stats = animation_data.get("optimization_stats", {})
            original_size = optimization_stats.get("original_data_size", 0)
            optimized_size = optimization_stats.get("optimized_data_size", 0)
            
            if original_size == 0:
                return 0.0
                
            return ((original_size - optimized_size) / original_size) * 100
            
        except Exception:
            return 0.0
    
    # === 驗證檢查方法 ===
    
    def _check_data_structure(self, results: Dict[str, Any]) -> bool:
        """檢查數據結構完整性"""
        required_keys = ["data", "metadata"]
        data_keys = ["timeseries_data", "animation_data"]
        
        if not all(key in results for key in required_keys):
            return False
            
        data_section = results.get("data", {})
        return all(key in data_section for key in data_keys)
    
    def _check_timeseries_completeness(self, results: Dict[str, Any]) -> bool:
        """檢查時間序列數據完整性"""
        timeseries_data = results.get("data", {}).get("timeseries_data", {})
        satellites = timeseries_data.get("satellites", [])
        
        if not satellites:
            return False
            
        # 檢查每顆衛星都有足夠的時間序列點
        for satellite in satellites:
            timeseries = satellite.get("enhanced_timeseries", [])
            if len(timeseries) < 50:  # 最少50個時間點
                return False
                
        return True
    
    def _check_animation_integrity(self, results: Dict[str, Any]) -> bool:
        """檢查動畫數據完整性"""
        animation_data = results.get("data", {}).get("animation_data", {})
        
        required_components = ["global_timeline", "constellation_animations", "coverage_analysis"]
        
        return all(component in animation_data for component in required_components)
    
    def _check_metadata_completeness(self, results: Dict[str, Any]) -> bool:
        """檢查metadata完整性"""
        metadata = results.get("metadata", {})
        required_fields = [
            "stage_number", "stage_name", "processing_timestamp", 
            "output_summary", "data_format_version", "processing_statistics"
        ]
        
        return all(field in metadata for field in required_fields)
    
    def _check_academic_compliance(self, results: Dict[str, Any]) -> bool:
        """檢查學術標準合規性"""
        academic_compliance = results.get("metadata", {}).get("academic_compliance", {})
        
        return (
            academic_compliance.get("grade") == "A" and
            academic_compliance.get("validation_passed") == True and
            academic_compliance.get("no_simplified_algorithms") == True
        )
    
    def _check_temporal_consistency(self, results: Dict[str, Any]) -> bool:
        """檢查時間一致性"""
        try:
            timeseries_data = results.get("data", {}).get("timeseries_data", {})
            satellites = timeseries_data.get("satellites", [])
            
            # 檢查時間序列時間戳遞增
            for satellite in satellites[:3]:  # 檢查前3顆衛星
                timeseries = satellite.get("enhanced_timeseries", [])
                if len(timeseries) < 2:
                    continue
                    
                prev_timestamp = None
                for point in timeseries[:10]:  # 檢查前10個點
                    timestamp = point.get("timestamp")
                    if prev_timestamp and timestamp <= prev_timestamp:
                        return False
                    prev_timestamp = timestamp
                    
            return True
            
        except Exception:
            return False
    
    def _check_web_optimization(self, results: Dict[str, Any]) -> bool:
        """檢查網頁優化效果"""
        if not self.web_optimization:
            return True  # 如果沒開啟優化，視為通過
            
        animation_data = results.get("data", {}).get("animation_data", {})
        optimization_stats = animation_data.get("optimization_stats", {})
        
        # 檢查是否有優化統計
        return "optimized_data_size" in optimization_stats and "original_data_size" in optimization_stats