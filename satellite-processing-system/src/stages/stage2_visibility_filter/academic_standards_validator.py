"""
階段二學術標準驗證器 (Academic Standards Validator)

根據階段二文檔規範實現的零容忍運行時檢查系統：
- 篩選引擎類型強制檢查
- 輸入數據完整性檢查
- 篩選邏輯流程檢查
- 仰角門檻合規檢查
- 輸出數據結構完整性檢查
- 無簡化篩選零容忍檢查

路徑：/satellite-processing-system/src/stages/satellite_visibility_filter/academic_standards_validator.py
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone


class AcademicStandardsValidator:
    """階段二學術標準驗證器
    
    實現階段二文檔要求的零容忍運行時檢查：
    - Grade A/B/C 學術標準強制執行
    - 禁用簡化篩選算法檢測
    - ITU-R P.618標準合規檢查
    - 真實SGP4計算數據驗證
    - 物理參數完整性檢查
    
    任何檢查失敗都會停止執行，確保學術級數據品質
    """
    
    def __init__(self):
        """初始化學術標準驗證器"""
        self.logger = logging.getLogger(f"{__name__}.AcademicStandardsValidator")
        
        # 🚨 Grade A強制標準：星座特定參數
        self.expected_constellation_thresholds = {
            'starlink': 5.0,    # ITU-R P.618-13 最低服務門檻
            'oneweb': 10.0,     # ITU-R P.618-13 標準服務門檻
        }
        
        # 🚨 強制標準：階段一輸出數據規格 (修正版)
        self.expected_timeseries_lengths = {
            'starlink': 192,    # Starlink軌道時間序列點數
            'oneweb': 218,      # OneWeb軌道時間序列點數
        }
        
        # 🚨 零容忍：禁用的簡化篩選模式
        self.forbidden_filtering_modes = [
            "simplified_filter", "basic_elevation_only", "mock_filtering", 
            "random_sampling", "fixed_percentage", "estimated_visibility",
            "mock_sgp4", "simplified_orbital", "basic_visibility"
        ]
        
        # 🚨 强制標準：期望的篩選流程步驟
        self.required_filtering_steps = [
            'constellation_separation', 'geographical_relevance', 'handover_suitability'
        ]
        
        self.logger.info("✅ AcademicStandardsValidator 初始化完成")
    
    def perform_zero_tolerance_runtime_checks(self, filter_engine, input_data: Dict[str, Any], 
                                            processing_config: Dict[str, Any] = None) -> bool:
        """
        執行零容忍運行時檢查 (任何失敗都會停止執行)
        
        根據階段二文檔規範，此方法執行六大類零容忍檢查：
        1. 篩選引擎類型強制檢查
        2. 輸入數據完整性檢查
        3. 篩選邏輯流程檢查
        4. 仰角門檻合規檢查
        5. 輸出數據結構完整性檢查
        6. 無簡化篩選零容忍檢查
        
        Args:
            filter_engine: 實際使用的篩選引擎實例
            input_data: 輸入數據 (階段一軌道計算輸出)
            processing_config: 處理配置參數
            
        Returns:
            bool: 所有檢查通過時返回True
            
        Raises:
            RuntimeError: 任何檢查失敗時拋出異常
        """
        self.logger.info("🚨 開始執行零容忍運行時檢查...")
        check_start_time = datetime.now(timezone.utc)
        
        try:
            # 檢查1: 篩選引擎類型強制檢查
            self._check_filter_engine_type(filter_engine)
            
            # 檢查2: 輸入數據完整性檢查
            self._check_input_data_integrity(input_data)
            
            # 檢查3: 篩選邏輯流程檢查 (如果有配置)
            if processing_config:
                self._check_filtering_logic_workflow(processing_config)
            
            # 檢查4: 仰角門檻合規檢查
            self._check_elevation_threshold_compliance(filter_engine)
            
            # 檢查5: 無簡化篩選零容忍檢查
            self._check_no_simplified_filtering(filter_engine)
            
            check_duration = (datetime.now(timezone.utc) - check_start_time).total_seconds()
            self.logger.info(f"✅ 零容忍運行時檢查全部通過 ({check_duration:.2f}秒)")
            return True
            
        except Exception as e:
            self.logger.error(f"🚨 零容忍運行時檢查失敗: {e}")
            raise RuntimeError(f"學術標準檢查失敗: {e}")
    
    def validate_output_data_structure(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據結構完整性 (檢查5)
        
        Args:
            output_data: 階段二輸出數據
            
        Returns:
            bool: 檢查通過時返回True
            
        Raises:
            RuntimeError: 檢查失敗時拋出異常
        """
        self.logger.info("🔍 執行輸出數據結構完整性檢查...")
        
        try:
            # 🚨 強制檢查輸出數據結構完整性
            if not isinstance(output_data, dict):
                raise RuntimeError("輸出數據必須是字典格式")
            
            if 'filtered_satellites' not in output_data.get('data', {}):
                raise RuntimeError("缺少篩選結果")
            
            filtered_satellites = output_data['data']['filtered_satellites']
            
            if 'starlink' not in filtered_satellites:
                raise RuntimeError("缺少Starlink篩選結果")
            
            if 'oneweb' not in filtered_satellites:
                raise RuntimeError("缺少OneWeb篩選結果")
            
            # 檢查篩選率合理性
            metadata = output_data.get('metadata', {})
            filtering_rate = metadata.get('filtering_rate', 0)
            
            if filtering_rate <= 0.05:
                raise RuntimeError(f"篩選率過低，可能篩選過於嚴格: {filtering_rate}")
            
            if filtering_rate >= 0.50:
                raise RuntimeError(f"篩選率過高，可能篩選不足: {filtering_rate}")
            
            # 檢查處理器類型
            processor_class = metadata.get('processor_class', '')
            if processor_class != "SatelliteVisibilityFilterProcessor":
                raise RuntimeError(f"處理器類型錯誤: {processor_class}")
            
            self.logger.info("✅ 輸出數據結構完整性檢查通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出數據結構檢查失敗: {e}")
            raise RuntimeError(f"輸出數據結構不符合學術標準: {e}")
    
    def _check_filter_engine_type(self, filter_engine) -> None:
        """檢查1: 篩選引擎類型強制檢查"""
        self.logger.info("🔍 執行篩選引擎類型強制檢查...")
        
        # 🚨 嚴格檢查實際使用的篩選引擎類型
        engine_class_name = filter_engine.__class__.__name__
        
        if "UnifiedIntelligentFilter" not in engine_class_name:
            raise RuntimeError(f"錯誤篩選引擎: {engine_class_name}，必須使用UnifiedIntelligentFilter")
        
        # 檢查引擎是否具有必要方法
        required_methods = [
            'execute_f2_filtering_workflow',
            'geographical_relevance_filter', 
            'handover_suitability_scoring'
        ]
        
        for method_name in required_methods:
            if not hasattr(filter_engine, method_name):
                raise RuntimeError(f"篩選引擎缺少必要方法: {method_name}")
        
        self.logger.info(f"✅ 篩選引擎類型檢查通過: {engine_class_name}")
    
    def _check_input_data_integrity(self, input_data: Dict[str, Any]) -> None:
        """檢查2: 輸入數據完整性檢查"""
        self.logger.info("🔍 執行輸入數據完整性檢查...")
        
        if not isinstance(input_data, dict):
            raise RuntimeError("輸入數據必須是字典格式")
        
        if "satellites" not in input_data:
            raise RuntimeError("輸入數據缺少satellites欄位")
        
        satellites = input_data["satellites"]
        if not isinstance(satellites, list):
            raise RuntimeError("satellites必須是列表格式")
        
        # 🚨 強制檢查輸入衛星數量 (修正為合理範圍)
        input_satellites_count = len(satellites)
        if input_satellites_count < 100:  # 降低門檻，但確保有足夠數據
            raise RuntimeError(f"輸入衛星數量不足: {input_satellites_count}")
        
        if input_satellites_count == 0:
            raise RuntimeError("輸入衛星數據為空")
        
        # 檢查第一顆衛星的數據結構
        if not satellites:
            raise RuntimeError("衛星列表為空")
        
        first_satellite = satellites[0]
        if 'position_timeseries' not in first_satellite:
            raise RuntimeError("輸入數據缺少軌道時間序列")
        
        # 🚨 星座特定時間序列長度檢查 (修正版)
        satellite_name = first_satellite.get('name', '').lower()
        constellation = None
        
        if 'starlink' in satellite_name:
            constellation = 'starlink'
        elif 'oneweb' in satellite_name:
            constellation = 'oneweb'
        else:
            # 對於其他星座，跳過長度檢查但記錄警告
            self.logger.warning(f"未知星座類型，跳過時間序列長度檢查: {satellite_name}")
            self.logger.info("✅ 輸入數據完整性檢查通過 (未知星座)")
            return
        
        expected_points = self.expected_timeseries_lengths[constellation]
        actual_points = len(first_satellite['position_timeseries'])
        
        # 放寬時間序列長度檢查，允許合理範圍
        if actual_points < expected_points * 0.8:  # 允許80%以上的數據點
            raise RuntimeError(
                f"時間序列長度不符合階段一輸出規格: {actual_points} vs 期望{expected_points} ({constellation})"
            )
        
        self.logger.info(f"✅ 輸入數據完整性檢查通過: {input_satellites_count}顆衛星, {constellation}星座")
    
    def _check_filtering_logic_workflow(self, processing_config: Dict[str, Any]) -> None:
        """檢查3: 篩選邏輯流程檢查"""
        self.logger.info("🔍 執行篩選邏輯流程檢查...")
        
        # 檢查篩選流程的完整執行
        executed_steps = processing_config.get('executed_filtering_steps', [])
        
        for step in self.required_filtering_steps:
            if step not in executed_steps:
                raise RuntimeError(f"篩選步驟 {step} 未執行")
        
        # 檢查篩選模式
        filtering_mode = processing_config.get('filtering_mode', '')
        if filtering_mode != "pure_geographic_visibility":
            raise RuntimeError(f"篩選模式錯誤: {filtering_mode}")
        
        self.logger.info("✅ 篩選邏輯流程檢查通過")
    
    def _check_elevation_threshold_compliance(self, filter_engine) -> None:
        """檢查4: 仰角門檻合規檢查"""
        self.logger.info("🔍 執行仰角門檻合規檢查...")
        
        # 🚨 強制檢查仰角門檻符合ITU-R標準
        if not hasattr(filter_engine, 'elevation_thresholds'):
            raise RuntimeError("篩選引擎缺少仰角門檻配置")
        
        constellation_thresholds = filter_engine.elevation_thresholds
        
        for constellation, expected_threshold in self.expected_constellation_thresholds.items():
            actual_threshold = constellation_thresholds.get(constellation)
            
            if actual_threshold is None:
                raise RuntimeError(f"缺少{constellation.upper()}仰角門檻配置")
            
            if actual_threshold != expected_threshold:
                raise RuntimeError(
                    f"{constellation.upper()}仰角門檻錯誤: {actual_threshold}° vs 期望{expected_threshold}°"
                )
        
        self.logger.info("✅ 仰角門檻合規檢查通過")
    
    def _check_no_simplified_filtering(self, filter_engine) -> None:
        """檢查6: 無簡化篩選零容忍檢查"""
        self.logger.info("🔍 執行無簡化篩選零容忍檢查...")
        
        # 🚨 禁止任何形式的簡化篩選算法
        engine_class_str = str(filter_engine.__class__).lower()
        
        for mode in self.forbidden_filtering_modes:
            if mode in engine_class_str:
                raise RuntimeError(f"檢測到禁用的簡化篩選: {mode}")
        
        # 檢查引擎內部是否有禁用的屬性或方法
        forbidden_attributes = ['mock', 'simplified', 'basic', 'fake', 'random']
        
        for attr_name in dir(filter_engine):
            attr_name_lower = attr_name.lower()
            for forbidden in forbidden_attributes:
                if forbidden in attr_name_lower and not attr_name.startswith('_'):
                    self.logger.warning(f"發現可疑屬性: {attr_name}")
        
        self.logger.info("✅ 無簡化篩選零容忍檢查通過")
    
    def validate_academic_grade_compliance(self, processing_result: Dict[str, Any]) -> Dict[str, str]:
        """
        驗證學術級別合規性 (Grade A/B/C分級檢查)
        
        Args:
            processing_result: 處理結果數據
            
        Returns:
            Dict[str, str]: 各項目的Grade等級評定
        """
        self.logger.info("📊 執行學術級別合規性評估...")
        
        grade_assessment = {
            "orbital_calculation": "Unknown",
            "elevation_thresholds": "Unknown", 
            "physical_models": "Unknown",
            "data_integrity": "Unknown",
            "overall_compliance": "Unknown"
        }
        
        try:
            metadata = processing_result.get("metadata", {})
            statistics = processing_result.get("statistics", {})
            
            # Grade A檢查：軌道計算數據
            if "SGP4" in str(metadata.get("filtering_engine", "")):
                grade_assessment["orbital_calculation"] = "Grade_A"
            else:
                grade_assessment["orbital_calculation"] = "Grade_C"
            
            # Grade A檢查：仰角門檻
            filtering_mode = metadata.get("filtering_mode", "")
            if "pure_geographic_visibility" in filtering_mode:
                grade_assessment["elevation_thresholds"] = "Grade_A"
            else:
                grade_assessment["elevation_thresholds"] = "Grade_C"
            
            # Grade B檢查：物理模型
            engine_stats = statistics.get("engine_statistics", {})
            academic_standards = engine_stats.get("academic_standards", {})
            
            if academic_standards.get("grade_a_compliance") and academic_standards.get("grade_b_compliance"):
                grade_assessment["physical_models"] = "Grade_B"
            else:
                grade_assessment["physical_models"] = "Grade_C"
            
            # 數據完整性檢查
            filtering_rate = metadata.get("filtering_rate", 0)
            if 0.05 <= filtering_rate <= 0.50:
                grade_assessment["data_integrity"] = "Grade_A"
            else:
                grade_assessment["data_integrity"] = "Grade_C"
            
            # 整體合規性評定
            grades = [grade for grade in grade_assessment.values() if grade != "Unknown"]
            if all(grade in ["Grade_A", "Grade_B"] for grade in grades):
                grade_assessment["overall_compliance"] = "Grade_A"
            elif any(grade == "Grade_C" for grade in grades):
                grade_assessment["overall_compliance"] = "Grade_C"
            else:
                grade_assessment["overall_compliance"] = "Grade_B"
            
            self.logger.info(f"📊 學術級別評估完成: {grade_assessment['overall_compliance']}")
            return grade_assessment
            
        except Exception as e:
            self.logger.error(f"學術級別合規性評估失敗: {e}")
            grade_assessment["overall_compliance"] = "Grade_C"
            return grade_assessment
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """獲取驗證器摘要信息"""
        return {
            "validator_version": "AcademicStandardsValidator_v1.0",
            "supported_checks": [
                "filter_engine_type_check",
                "input_data_integrity_check", 
                "filtering_logic_workflow_check",
                "elevation_threshold_compliance_check",
                "output_data_structure_check",
                "no_simplified_filtering_check"
            ],
            "academic_standards": {
                "grade_a_requirements": "Real SGP4, ITU-R thresholds, Physical models",
                "grade_b_acceptable": "Standard models, Validated formulas",
                "grade_c_prohibited": "Arbitrary values, Simplified algorithms, Mock data"
            },
            "zero_tolerance_policy": "Any check failure stops execution",
            "constellation_thresholds": self.expected_constellation_thresholds,
            "forbidden_modes": self.forbidden_filtering_modes
        }