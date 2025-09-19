"""
跨階段一致性驗證器 - Stage 5模組化組件

職責：
1. 驗證階段間數據一致性
2. 時間軸同步檢查
3. 衛星ID映射驗證
4. 數據完整性檢查
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class CrossStageValidator:
    """跨階段一致性驗證器 - 確保階段間數據一致性和時間軸同步"""
    
    def __init__(self):
        """初始化跨階段一致性驗證器"""
        self.logger = logging.getLogger(f"{__name__}.CrossStageValidator")
        
        # 驗證統計
        self.validation_statistics = {
            "total_validations": 0,
            "consistency_checks": 0,
            "time_sync_checks": 0,
            "satellite_mapping_checks": 0,
            "validation_errors": 0,
            "validation_warnings": 0
        }
        
        # 驗證閾值配置
        self.validation_thresholds = {
            "time_sync_tolerance_seconds": 300,  # 5分鐘時間容忍度
            "satellite_count_variance_threshold": 0.05,  # 5%衛星數量差異容忍
            "data_completeness_threshold": 0.95  # 95%數據完整性要求
        }
        
        self.logger.info("✅ 跨階段一致性驗證器初始化完成")
        self.logger.info(f"   時間同步容忍度: {self.validation_thresholds['time_sync_tolerance_seconds']}秒")
        self.logger.info(f"   衛星數量差異閾值: {self.validation_thresholds['satellite_count_variance_threshold']*100}%")
    
    def validate_cross_stage_consistency(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證跨階段數據一致性
        
        Args:
            stage_data: 包含所有階段數據的字典
            
        Returns:
            驗證結果報告
        """
        self.logger.info("🔍 開始跨階段一致性驗證...")
        
        validation_results = {
            "overall_valid": True,
            "consistency_checks": {},
            "time_sync_results": {},
            "satellite_mapping_results": {},
            "data_completeness_results": {},
            "validation_summary": {}
        }
        
        self.validation_statistics["total_validations"] += 1
        
        # 1. 數據一致性檢查
        consistency_results = self._validate_data_consistency(stage_data)
        validation_results["consistency_checks"] = consistency_results
        
        if not consistency_results["valid"]:
            validation_results["overall_valid"] = False
            self.validation_statistics["validation_errors"] += len(consistency_results["errors"])
        
        # 2. 時間軸同步檢查
        time_sync_results = self._validate_time_axis_synchronization(stage_data)
        validation_results["time_sync_results"] = time_sync_results
        
        if not time_sync_results["synchronized"]:
            validation_results["overall_valid"] = False
            self.validation_statistics["validation_errors"] += len(time_sync_results["sync_errors"])
        
        # 3. 衛星映射驗證
        mapping_results = self._validate_satellite_mapping(stage_data)
        validation_results["satellite_mapping_results"] = mapping_results
        
        if not mapping_results["mapping_valid"]:
            validation_results["overall_valid"] = False
            self.validation_statistics["validation_errors"] += len(mapping_results["mapping_errors"])
        
        # 4. 數據完整性檢查
        completeness_results = self._validate_data_completeness(stage_data)
        validation_results["data_completeness_results"] = completeness_results
        
        if not completeness_results["complete"]:
            self.validation_statistics["validation_warnings"] += len(completeness_results["completeness_warnings"])
        
        # 生成驗證摘要
        validation_results["validation_summary"] = self._generate_validation_summary(validation_results)
        
        self.validation_statistics["consistency_checks"] += 1
        
        status = "✅ 通過" if validation_results["overall_valid"] else "❌ 失敗"
        self.logger.info(f"{status} 跨階段一致性驗證完成")
        
        return validation_results
    
    def _validate_data_consistency(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據一致性"""
        errors = []
        warnings = []
        
        # 檢查階段數據存在性
        required_stages = ["stage1_orbital", "stage2_visibility", "stage3_timeseries"]
        available_stages = []
        
        for stage in required_stages:
            if stage in stage_data and stage_data[stage]:
                available_stages.append(stage)
            else:
                errors.append(f"缺少必需的{stage}數據")
        
        # 檢查數據格式一致性
        for stage in available_stages:
            data = stage_data[stage]
            
            # 檢查基本結構
            if not isinstance(data, dict):
                errors.append(f"{stage}數據格式錯誤：非字典格式")
                continue
            
            if "data" not in data:
                errors.append(f"{stage}缺少'data'字段")
                continue
            
            if "metadata" not in data:
                warnings.append(f"{stage}缺少'metadata'字段")
            
            # 檢查衛星數據結構
            satellites = data.get("data", {}).get("satellites", [])
            if not isinstance(satellites, list):
                errors.append(f"{stage}衛星數據格式錯誤")
            elif len(satellites) == 0:
                warnings.append(f"{stage}衛星數據為空")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "available_stages": available_stages
        }
    
    def _validate_time_axis_synchronization(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間軸同步"""
        sync_errors = []
        sync_warnings = []
        time_info = {}
        
        self.validation_statistics["time_sync_checks"] += 1
        
        # 收集各階段時間信息
        for stage_name, data in stage_data.items():
            if not data or not isinstance(data, dict):
                continue
            
            metadata = data.get("metadata", {})
            processing_timestamp = metadata.get("processing_timestamp")
            
            if processing_timestamp:
                try:
                    # 解析時間戳
                    if isinstance(processing_timestamp, str):
                        timestamp = datetime.fromisoformat(processing_timestamp.replace('Z', '+00:00'))
                    else:
                        timestamp = processing_timestamp
                    
                    time_info[stage_name] = {
                        "timestamp": timestamp,
                        "timestamp_str": processing_timestamp
                    }
                except Exception as e:
                    sync_errors.append(f"{stage_name}時間戳解析失敗: {e}")
        
        # 檢查時間軸同步
        if len(time_info) >= 2:
            timestamps = list(time_info.values())
            base_time = timestamps[0]["timestamp"]
            
            for i, time_data in enumerate(timestamps[1:], 1):
                time_diff = abs((time_data["timestamp"] - base_time).total_seconds())
                
                if time_diff > self.validation_thresholds["time_sync_tolerance_seconds"]:
                    stage_names = list(time_info.keys())
                    sync_errors.append(
                        f"{stage_names[0]}與{stage_names[i]}時間差異過大: {time_diff:.1f}秒"
                    )
                elif time_diff > 60:  # 1分鐘警告閾值
                    stage_names = list(time_info.keys())
                    sync_warnings.append(
                        f"{stage_names[0]}與{stage_names[i]}時間差異: {time_diff:.1f}秒"
                    )
        
        return {
            "synchronized": len(sync_errors) == 0,
            "sync_errors": sync_errors,
            "sync_warnings": sync_warnings,
            "time_info": time_info,
            "max_time_difference": self._calculate_max_time_difference(time_info)
        }
    
    def _calculate_max_time_difference(self, time_info: Dict[str, Any]) -> float:
        """計算最大時間差異"""
        if len(time_info) < 2:
            return 0.0
        
        timestamps = [info["timestamp"] for info in time_info.values()]
        min_time = min(timestamps)
        max_time = max(timestamps)
        
        return (max_time - min_time).total_seconds()
    
    def _validate_satellite_mapping(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證衛星ID映射"""
        mapping_errors = []
        mapping_warnings = []
        satellite_counts = {}
        satellite_sets = {}
        
        self.validation_statistics["satellite_mapping_checks"] += 1
        
        # 收集各階段衛星ID
        for stage_name, data in stage_data.items():
            if not data or not isinstance(data, dict):
                continue
            
            # 支持多種數據格式：data.satellites 或直接 satellites
            satellites = []
            if "data" in data and isinstance(data["data"], dict) and "satellites" in data["data"]:
                satellites = data["data"]["satellites"]
            elif "satellites" in data:
                satellites = data["satellites"]

            satellite_ids = set()

            for satellite in satellites:
                if not isinstance(satellite, dict):
                    continue
                satellite_id = satellite.get("satellite_id")
                if satellite_id:
                    satellite_ids.add(satellite_id)
            
            satellite_counts[stage_name] = len(satellite_ids)
            satellite_sets[stage_name] = satellite_ids
        
        # 檢查衛星數量一致性
        if len(satellite_counts) >= 2:
            count_values = list(satellite_counts.values())
            max_count = max(count_values)
            min_count = min(count_values)
            
            if max_count > 0:
                variance = (max_count - min_count) / max_count
                
                if variance > self.validation_thresholds["satellite_count_variance_threshold"]:
                    mapping_errors.append(
                        f"衛星數量差異過大: 最大{max_count}, 最小{min_count}, 差異{variance*100:.1f}%"
                    )
        
        # 檢查衛星ID重疊度
        if len(satellite_sets) >= 2:
            stage_names = list(satellite_sets.keys())
            base_set = satellite_sets[stage_names[0]]
            
            for i, stage_name in enumerate(stage_names[1:], 1):
                current_set = satellite_sets[stage_name]
                
                intersection = base_set & current_set
                union = base_set | current_set
                
                if len(union) > 0:
                    overlap_ratio = len(intersection) / len(union)
                    
                    if overlap_ratio < 0.8:  # 80%重疊度閾值
                        mapping_warnings.append(
                            f"{stage_names[0]}與{stage_name}衛星ID重疊度低: {overlap_ratio*100:.1f}%"
                        )
        
        return {
            "mapping_valid": len(mapping_errors) == 0,
            "mapping_errors": mapping_errors,
            "mapping_warnings": mapping_warnings,
            "satellite_counts": satellite_counts,
            "satellite_overlap_analysis": self._analyze_satellite_overlap(satellite_sets)
        }
    
    def _analyze_satellite_overlap(self, satellite_sets: Dict[str, set]) -> Dict[str, Any]:
        """分析衛星ID重疊情況"""
        if len(satellite_sets) < 2:
            return {"analysis": "需要至少兩個階段數據進行重疊分析"}
        
        stage_names = list(satellite_sets.keys())
        overlap_matrix = {}
        
        for i, stage1 in enumerate(stage_names):
            overlap_matrix[stage1] = {}
            for stage2 in stage_names:
                if stage1 != stage2:
                    set1 = satellite_sets[stage1]
                    set2 = satellite_sets[stage2]
                    
                    intersection = set1 & set2
                    union = set1 | set2
                    
                    overlap_ratio = len(intersection) / len(union) if len(union) > 0 else 0
                    overlap_matrix[stage1][stage2] = {
                        "overlap_count": len(intersection),
                        "overlap_ratio": overlap_ratio,
                        "unique_to_stage1": len(set1 - set2),
                        "unique_to_stage2": len(set2 - set1)
                    }
        
        return overlap_matrix
    
    def _validate_data_completeness(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據完整性"""
        completeness_warnings = []
        completeness_info = {}
        
        for stage_name, data in stage_data.items():
            if not data or not isinstance(data, dict):
                continue
            
            satellites = data.get("data", {}).get("satellites", [])
            completeness_info[stage_name] = {
                "total_satellites": len(satellites),
                "satellites_with_complete_data": 0,
                "completeness_ratio": 0.0
            }
            
            if satellites:
                complete_count = 0
                for satellite in satellites:
                    # 檢查基本字段完整性
                    required_fields = ["satellite_id", "constellation"]
                    has_all_fields = all(
                        field in satellite and satellite[field] is not None 
                        for field in required_fields
                    )
                    
                    if has_all_fields:
                        complete_count += 1
                
                completeness_ratio = complete_count / len(satellites)
                completeness_info[stage_name]["satellites_with_complete_data"] = complete_count
                completeness_info[stage_name]["completeness_ratio"] = completeness_ratio
                
                if completeness_ratio < self.validation_thresholds["data_completeness_threshold"]:
                    completeness_warnings.append(
                        f"{stage_name}數據完整性不足: {completeness_ratio*100:.1f}%"
                    )
        
        overall_completeness = self._calculate_overall_completeness(completeness_info)
        
        return {
            "complete": len(completeness_warnings) == 0,
            "completeness_warnings": completeness_warnings,
            "completeness_info": completeness_info,
            "overall_completeness": overall_completeness
        }
    
    def _calculate_overall_completeness(self, completeness_info: Dict[str, Any]) -> float:
        """計算整體完整性"""
        if not completeness_info:
            return 0.0
        
        ratios = [info["completeness_ratio"] for info in completeness_info.values()]
        return sum(ratios) / len(ratios) if ratios else 0.0
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成驗證摘要"""
        summary = {
            "validation_status": "PASS" if validation_results["overall_valid"] else "FAIL",
            "total_errors": 0,
            "total_warnings": 0,
            "key_findings": []
        }
        
        # 統計錯誤和警告
        for check_name, check_result in validation_results.items():
            if isinstance(check_result, dict):
                errors = check_result.get("errors", [])
                warnings = check_result.get("warnings", [])
                
                summary["total_errors"] += len(errors)
                summary["total_warnings"] += len(warnings)
        
        # 關鍵發現
        if validation_results["consistency_checks"].get("available_stages"):
            summary["key_findings"].append(
                f"可用階段: {len(validation_results['consistency_checks']['available_stages'])}"
            )
        
        if validation_results["time_sync_results"].get("max_time_difference"):
            max_diff = validation_results["time_sync_results"]["max_time_difference"]
            summary["key_findings"].append(f"最大時間差異: {max_diff:.1f}秒")
        
        if validation_results["satellite_mapping_results"].get("satellite_counts"):
            counts = validation_results["satellite_mapping_results"]["satellite_counts"]
            summary["key_findings"].append(f"衛星數量範圍: {min(counts.values())}-{max(counts.values())}")
        
        return summary
    
    def run_comprehensive_validation(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """運行綜合驗證檢查"""
        self.logger.info("🔍 開始綜合驗證檢查...")
        
        # 執行所有驗證
        validation_result = self.validate_cross_stage_consistency(stage_data)
        
        # 添加額外檢查
        additional_checks = self._run_additional_checks(stage_data)
        validation_result["additional_checks"] = additional_checks
        
        # 更新整體驗證狀態
        if additional_checks and not additional_checks.get("all_passed", True):
            validation_result["overall_valid"] = False
        
        return validation_result
    
    def _run_additional_checks(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """運行額外檢查"""
        checks = {
            "all_passed": True,
            "metadata_consistency": self._check_metadata_consistency(stage_data),
            "data_version_compatibility": self._check_data_version_compatibility(stage_data),
            "processing_pipeline_integrity": self._check_pipeline_integrity(stage_data)
        }
        
        # 檢查是否有失敗項目
        for check_name, check_result in checks.items():
            if check_name != "all_passed" and isinstance(check_result, dict):
                if not check_result.get("passed", True):
                    checks["all_passed"] = False
                    break
        
        return checks
    
    def _check_metadata_consistency(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查元數據一致性"""
        try:
            metadata_fields = []
            processing_versions = set()
            consistency_errors = []

            # 檢查每個階段的元數據
            for stage_name, data in stage_data.items():
                if not data or not isinstance(data, dict):
                    consistency_errors.append(f"{stage_name}: 數據格式錯誤")
                    continue

                metadata = data.get("metadata", {})
                if not metadata:
                    consistency_errors.append(f"{stage_name}: 缺少metadata")
                    continue

                # 檢查基本字段存在性
                required_fields = ["processing_timestamp", "processor_version"]
                for field in required_fields:
                    if field not in metadata:
                        consistency_errors.append(f"{stage_name}: 缺少{field}字段")

                # 收集版本信息
                version = metadata.get("processor_version")
                if version:
                    processing_versions.add(version)

                metadata_fields.append({
                    "stage": stage_name,
                    "fields_count": len(metadata),
                    "has_timestamp": "processing_timestamp" in metadata,
                    "has_version": "processor_version" in metadata
                })

            # 檢查版本一致性
            if len(processing_versions) > 1:
                consistency_errors.append(f"發現多個處理器版本: {list(processing_versions)}")

            passed = len(consistency_errors) == 0
            info = f"檢查了{len(metadata_fields)}個階段的元數據"
            if not passed:
                info += f"，發現{len(consistency_errors)}個一致性問題"

            return {
                "passed": passed,
                "info": info,
                "metadata_fields": metadata_fields,
                "processing_versions": list(processing_versions),
                "errors": consistency_errors
            }
        except Exception as e:
            return {
                "passed": False,
                "info": f"元數據一致性檢查失敗: {str(e)}",
                "errors": [str(e)]
            }
    
    def _check_data_version_compatibility(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據版本兼容性"""
        try:
            version_info = {}
            compatibility_errors = []

            # 收集各階段版本信息
            for stage_name, data in stage_data.items():
                if not data or not isinstance(data, dict):
                    continue

                metadata = data.get("metadata", {})
                data_version = metadata.get("data_version", "unknown")
                processor_version = metadata.get("processor_version", "unknown")
                schema_version = metadata.get("schema_version", "unknown")

                version_info[stage_name] = {
                    "data_version": data_version,
                    "processor_version": processor_version,
                    "schema_version": schema_version
                }

            # 檢查版本兼容性
            unique_data_versions = set(info["data_version"] for info in version_info.values())
            unique_schema_versions = set(info["schema_version"] for info in version_info.values())

            # 數據版本應該相近或相同
            if len(unique_data_versions) > 2:
                compatibility_errors.append(f"數據版本差異過大: {list(unique_data_versions)}")

            # Schema版本應該兼容
            if len(unique_schema_versions) > 1:
                # 允許minor version差異，但major version應該相同
                major_versions = set()
                for version in unique_schema_versions:
                    if version != "unknown" and "." in str(version):
                        major_version = str(version).split(".")[0]
                        major_versions.add(major_version)

                if len(major_versions) > 1:
                    compatibility_errors.append(f"Schema主版本不兼容: {list(unique_schema_versions)}")

            passed = len(compatibility_errors) == 0
            info = f"檢查了{len(version_info)}個階段的版本信息"
            if not passed:
                info += f"，發現{len(compatibility_errors)}個兼容性問題"

            return {
                "passed": passed,
                "info": info,
                "version_info": version_info,
                "unique_data_versions": list(unique_data_versions),
                "unique_schema_versions": list(unique_schema_versions),
                "errors": compatibility_errors
            }
        except Exception as e:
            return {
                "passed": False,
                "info": f"數據版本兼容性檢查失敗: {str(e)}",
                "errors": [str(e)]
            }
    
    def _check_pipeline_integrity(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查流水線完整性"""
        try:
            pipeline_info = {}
            integrity_errors = []

            # 定義期望的流水線階段順序
            expected_stages = ["stage1_orbital", "stage2_visibility", "stage3_signal", "stage4_timeseries", "stage5_integration"]
            available_stages = [stage for stage in expected_stages if stage in stage_data and stage_data[stage]]

            # 檢查階段完整性
            missing_stages = [stage for stage in expected_stages if stage not in available_stages]
            if missing_stages:
                integrity_errors.append(f"缺少流水線階段: {missing_stages}")

            # 檢查數據流向一致性
            for i, stage in enumerate(available_stages):
                data = stage_data[stage]
                if not isinstance(data, dict):
                    integrity_errors.append(f"{stage}: 數據格式錯誤")
                    continue

                # 檢查輸入來源 (stage2+應該引用前一階段)
                metadata = data.get("metadata", {})
                input_source = metadata.get("input_source")

                if i > 0:  # 非第一階段
                    previous_stage = available_stages[i-1]
                    if input_source and previous_stage not in str(input_source):
                        integrity_errors.append(f"{stage}: 輸入來源不匹配，期望來自{previous_stage}")

                # 檢查處理狀態
                processing_status = metadata.get("processing_status", "unknown")
                if processing_status == "failed":
                    integrity_errors.append(f"{stage}: 處理狀態為失敗")
                elif processing_status == "unknown":
                    integrity_errors.append(f"{stage}: 處理狀態未知")

                pipeline_info[stage] = {
                    "available": True,
                    "input_source": input_source,
                    "processing_status": processing_status,
                    "has_data": "data" in data and bool(data["data"]),
                    "satellite_count": len(data.get("data", {}).get("satellites", []))
                }

            # 檢查數據量級一致性 (相鄰階段的衛星數量不應該差異過大)
            for i in range(len(available_stages) - 1):
                current_stage = available_stages[i]
                next_stage = available_stages[i + 1]

                current_count = pipeline_info[current_stage]["satellite_count"]
                next_count = pipeline_info[next_stage]["satellite_count"]

                if current_count > 0 and next_count > 0:
                    reduction_ratio = (current_count - next_count) / current_count
                    if reduction_ratio > 0.5:  # 數據減少超過50%
                        integrity_errors.append(
                            f"{current_stage}到{next_stage}數據減少過多: {current_count}→{next_count} ({reduction_ratio*100:.1f}%)"
                        )

            passed = len(integrity_errors) == 0
            info = f"檢查了{len(available_stages)}/{len(expected_stages)}個流水線階段"
            if not passed:
                info += f"，發現{len(integrity_errors)}個完整性問題"

            return {
                "passed": passed,
                "info": info,
                "pipeline_info": pipeline_info,
                "available_stages": available_stages,
                "missing_stages": missing_stages,
                "errors": integrity_errors
            }
        except Exception as e:
            return {
                "passed": False,
                "info": f"流水線完整性檢查失敗: {str(e)}",
                "errors": [str(e)]
            }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """獲取驗證統計信息"""
        return self.validation_statistics.copy()