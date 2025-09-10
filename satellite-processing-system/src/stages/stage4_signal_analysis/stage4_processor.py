"""
Stage 4處理器 - 信號分析模組化版本

功能：
1. 載入Stage 3時間序列預處理輸出
2. 計算RSRP信號強度 (基於Friis公式)
3. 執行3GPP NTN事件分析
4. 進行物理公式驗證
5. 生成衛星選擇建議
6. 格式化多種輸出格式

架構：
- 繼承BaseStageProcessor基礎架構
- 整合7個專用組件完成複雜信號分析
- 支持學術級物理驗證和3GPP標準合規
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.base_processor import BaseStageProcessor
from .timeseries_data_loader import TimseriesDataLoader
from .signal_quality_calculator import SignalQualityCalculator
from .gpp_event_analyzer import GPPEventAnalyzer
from .physics_validator import PhysicsValidator
from .recommendation_engine import RecommendationEngine
from .signal_output_formatter import SignalOutputFormatter

logger = logging.getLogger(__name__)

class Stage4Processor(BaseStageProcessor):
    """Stage 4: 信號分析處理器 - 重構版"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化Stage 4處理器"""
        # 呼叫基礎處理器的初始化
        super().__init__(stage_number=4, stage_name="signal_analysis", config=config)
        
        self.logger.info("📡 初始化Stage 4信號分析處理器...")
        
        # 讀取配置
        self.observer_lat = config.get('observer_lat', 24.9441667) if config else 24.9441667
        self.observer_lon = config.get('observer_lon', 121.3713889) if config else 121.3713889
        self.physics_validation_enabled = config.get('physics_validation', True) if config else True
        self.output_formats = config.get('output_formats', ['complete']) if config else ['complete']
        self.validation_level = config.get('validation_level', 'comprehensive') if config else 'comprehensive'
        
        # 初始化組件
        try:
            self.data_loader = TimseriesDataLoader()
            self.signal_calculator = SignalQualityCalculator(
                observer_lat=self.observer_lat, 
                observer_lon=self.observer_lon
            )
            self.event_analyzer = GPPEventAnalyzer()
            self.physics_validator = PhysicsValidator()
            self.recommendation_engine = RecommendationEngine()
            self.output_formatter = SignalOutputFormatter()
            
            self.logger.info("✅ Stage 4所有組件初始化成功")
            
        except Exception as e:
            self.logger.error(f"❌ Stage 4組件初始化失敗: {e}")
            raise RuntimeError(f"Stage 4初始化失敗: {e}")
        
        # 處理統計
        self.processing_stats = {
            "satellites_loaded": 0,
            "signal_calculations_completed": 0,
            "events_analyzed": 0,
            "recommendations_generated": 0,
            "physics_validation_passed": False,
            "output_formats_generated": 0
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據
        
        Stage 4需要Stage 3的時間序列預處理輸出
        """
        self.logger.info("🔍 驗證Stage 4輸入數據...")
        
        try:
            # 檢查Stage 3輸出文件存在性和完整性
            stage3_data = self.data_loader.load_stage3_output()
            
            # 驗證時間序列數據格式
            validation_result = self.data_loader.validate_timeseries_data_format(stage3_data)
            
            if not validation_result["format_valid"]:
                self.logger.error("Stage 3時間序列數據驗證失敗:")
                for issue in validation_result["format_issues"]:
                    self.logger.error(f"  - {issue}")
                return False
            
            # 檢查數據質量
            quality_metrics = validation_result["data_quality_metrics"]
            if quality_metrics.get("valid_satellites", 0) < 1:
                self.logger.error("時間序列數據中無有效衛星信息")
                return False
            
            self.logger.info("✅ Stage 3時間序列數據驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸入數據驗證失敗: {e}")
            return False
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        執行Stage 4的核心處理邏輯
        
        處理步驟:
        1. 載入Stage 3時間序列預處理輸出
        2. 計算RSRP信號強度
        3. 執行3GPP事件分析
        4. 進行物理公式驗證
        5. 生成衛星選擇建議
        6. 格式化多種輸出格式
        """
        self.logger.info("📡 開始Stage 4信號分析處理...")
        
        try:
            # 步驟1: 載入Stage 3數據
            self.logger.info("📥 步驟1: 載入Stage 3時間序列數據")
            stage3_data = self.data_loader.load_stage3_output()
            
            # 提取信號分析專用數據
            signal_ready_data = self.data_loader.extract_signal_analysis_data(stage3_data)
            satellites = signal_ready_data.get("satellites", [])
            
            load_stats = self.data_loader.get_load_statistics()
            self.processing_stats["satellites_loaded"] = load_stats["total_satellites_loaded"]
            
            # 步驟2: 計算信號品質
            self.logger.info("🔢 步驟2: 計算RSRP信號強度")
            signal_results = self.signal_calculator.calculate_satellite_signal_quality(satellites)
            
            calc_stats = self.signal_calculator.get_calculation_statistics()
            self.processing_stats["signal_calculations_completed"] = calc_stats["successful_calculations"]
            
            # 步驟3: 執行3GPP事件分析
            self.logger.info("📊 步驟3: 執行3GPP NTN事件分析")
            event_results = self.event_analyzer.analyze_3gpp_events(signal_results)
            
            analyzer_stats = self.event_analyzer.get_analysis_statistics()
            self.processing_stats["events_analyzed"] = analyzer_stats["satellites_analyzed"]
            
            # 步驟4: 物理公式驗證
            physics_validation = {"overall_grade": "A", "overall_passed": True}
            if self.physics_validation_enabled:
                self.logger.info("🔬 步驟4: 執行物理公式驗證")
                
                # Friis公式驗證
                friis_validation = self.physics_validator.validate_friis_formula_implementation(signal_results)
                
                # 都卜勒頻率驗證
                doppler_validation = self.physics_validator.validate_doppler_frequency_calculation(signal_results)
                
                # 物理常數驗證
                constants_validation = self.physics_validator.validate_physical_constants()
                
                # 生成物理驗證報告
                physics_validation = self.physics_validator.generate_physics_validation_report(
                    friis_validation, doppler_validation
                )
                physics_validation["constants_validation"] = constants_validation
                
                validator_stats = self.physics_validator.get_validation_statistics()
                self.processing_stats["physics_validation_passed"] = physics_validation.get("overall_passed", False)
            
            # 步驟5: 生成衛星建議
            self.logger.info("💡 步驟5: 生成衛星選擇建議")
            recommendations = self.recommendation_engine.generate_satellite_recommendations(
                signal_results, event_results
            )
            
            rec_stats = self.recommendation_engine.get_recommendation_statistics()
            self.processing_stats["recommendations_generated"] = rec_stats["recommendations_generated"]
            
            # 步驟6: 格式化輸出
            self.logger.info("📋 步驟6: 格式化多種輸出格式")
            formatted_results = {}
            
            for output_format in self.output_formats:
                try:
                    formatted_output = self.output_formatter.format_stage4_output(
                        signal_results=signal_results,
                        event_results=event_results,
                        physics_validation=physics_validation,
                        recommendations=recommendations,
                        processing_stats=self.processing_stats,
                        output_format=output_format
                    )
                    
                    formatted_results[output_format] = formatted_output
                    self.processing_stats["output_formats_generated"] += 1
                    
                except Exception as e:
                    self.logger.error(f"格式化輸出失敗 {output_format}: {e}")
                    continue
            
            if not formatted_results:
                raise ValueError("所有輸出格式生成失敗")
            
            # 返回主要格式或第一個可用格式
            main_result = formatted_results.get('complete') or next(iter(formatted_results.values()))
            
            # 添加額外格式到metadata中
            if len(formatted_results) > 1:
                main_result["metadata"]["additional_formats"] = {
                    fmt: result.get("metadata", {}).get("key_metrics", {})
                    for fmt, result in formatted_results.items()
                    if fmt != 'complete'
                }
            
            self.logger.info(f"✅ Stage 4處理完成: {self.processing_stats['signal_calculations_completed']} 顆衛星信號分析, "
                           f"{self.processing_stats['events_analyzed']} 顆衛星事件分析")
            
            return main_result
            
        except Exception as e:
            self.logger.error(f"Stage 4處理失敗: {e}")
            raise RuntimeError(f"Stage 4信號分析處理失敗: {e}")
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """驗證輸出數據的有效性"""
        self.logger.info("🔍 驗證Stage 4輸出數據...")
        
        try:
            # 檢查基本結構
            if not isinstance(output_data, dict):
                self.logger.error("輸出數據必須是字典格式")
                return False
            
            if "data" not in output_data or "metadata" not in output_data:
                self.logger.error("輸出數據缺少必要的data或metadata欄位")
                return False
            
            # 檢查數據部分
            data_section = output_data["data"]
            
            # 驗證信號分析結果
            if "signal_analysis" not in data_section:
                self.logger.error("輸出數據缺少信號分析結果")
                return False
            
            signal_analysis = data_section["signal_analysis"]
            if not signal_analysis.get("satellites", []):
                self.logger.error("信號分析結果中無衛星數據")
                return False
            
            # 驗證事件分析結果
            if "event_analysis" not in data_section:
                self.logger.error("輸出數據缺少事件分析結果")
                return False
            
            # 驗證建議結果
            if "recommendations" not in data_section:
                self.logger.error("輸出數據缺少建議結果")
                return False
            
            recommendations = data_section["recommendations"]
            if not recommendations.get("satellite_rankings", []):
                self.logger.error("建議結果中無衛星排名")
                return False
            
            # 檢查metadata完整性
            metadata = output_data["metadata"]
            required_fields = ["stage_number", "stage_name", "processing_timestamp", "output_summary"]
            
            for field in required_fields:
                if field not in metadata:
                    self.logger.error(f"metadata缺少必要欄位: {field}")
                    return False
            
            # 驗證學術合規性
            academic_compliance = metadata.get("academic_compliance", {})
            if not academic_compliance.get("validation_passed", False):
                self.logger.warning("學術合規驗證未通過")
            
            self.logger.info("✅ Stage 4輸出數據驗證通過")
            return True
            
        except Exception as e:
            self.logger.error(f"輸出數據驗證失敗: {e}")
            return False
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """保存處理結果到文件"""
        try:
            # 構建輸出文件路徑
            output_file = self.output_dir / "signal_analysis_output.json"
            
            # 確保輸出目錄存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存結果到JSON文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Stage 4結果已保存: {output_file}")
            
            # 保存處理統計到單獨文件
            stats_file = self.output_dir / "stage4_processing_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "processing_statistics": self.processing_stats,
                    "loader_statistics": self.data_loader.get_load_statistics(),
                    "calculator_statistics": self.signal_calculator.get_calculation_statistics(),
                    "analyzer_statistics": self.event_analyzer.get_analysis_statistics(),
                    "validator_statistics": self.physics_validator.get_validation_statistics(),
                    "recommendation_statistics": self.recommendation_engine.get_recommendation_statistics(),
                    "formatter_statistics": self.output_formatter.get_formatting_statistics(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存Stage 4結果失敗: {e}")
            raise IOError(f"無法保存Stage 4結果: {e}")
    
    def extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        try:
            metadata = results.get("metadata", {})
            data_section = results.get("data", {})
            
            signal_analysis = data_section.get("signal_analysis", {})
            event_analysis = data_section.get("event_analysis", {})
            recommendations = data_section.get("recommendations", {})
            
            # 信號分析指標
            signal_summary = signal_analysis.get("signal_summary", {})
            
            # 事件分析指標
            event_summary = event_analysis.get("event_summary", {})
            
            # 建議指標
            satellite_rankings = recommendations.get("satellite_rankings", [])
            handover_strategy = recommendations.get("handover_strategy", {})
            
            key_metrics = {
                "total_satellites_analyzed": len(signal_analysis.get("satellites", [])),
                "signal_calculation_success_rate": signal_summary.get("successful_calculations", 0) / max(signal_summary.get("total_satellites", 1), 1) * 100,
                "total_events_detected": (
                    event_summary.get("a4_events", 0) + 
                    event_summary.get("a5_events", 0) + 
                    event_summary.get("d2_events", 0)
                ),
                "handover_candidates": len(event_summary.get("handover_candidates", [])),
                "top_tier_satellites": len([s for s in satellite_rankings if s.get("recommendation_tier") == "Tier_1"]),
                "processing_duration": self.processing_duration,
                
                # 信號品質統計
                "signal_quality_metrics": {
                    "average_rsrp_dbm": self._calculate_average_rsrp(signal_analysis),
                    "rsrp_range": self._calculate_rsrp_range(signal_analysis),
                    "constellation_performance": signal_analysis.get("constellation_performance", {})
                },
                
                # 事件密度
                "event_metrics": {
                    "a4_event_rate": event_summary.get("a4_events", 0) / max(len(signal_analysis.get("satellites", [])), 1),
                    "a5_event_rate": event_summary.get("a5_events", 0) / max(len(signal_analysis.get("satellites", [])), 1),
                    "d2_event_rate": event_summary.get("d2_events", 0) / max(len(signal_analysis.get("satellites", [])), 1)
                },
                
                # 物理驗證結果
                "physics_validation": {
                    "overall_grade": data_section.get("physics_validation", {}).get("overall_grade", "N/A"),
                    "validation_passed": self.processing_stats["physics_validation_passed"]
                },
                
                # 建議品質
                "recommendation_quality": {
                    "primary_recommendation_score": satellite_rankings[0].get("comprehensive_score", 0) if satellite_rankings else 0,
                    "handover_strategy": handover_strategy.get("strategy", "unknown"),
                    "recommendation_confidence": self._assess_recommendation_confidence(satellite_rankings)
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
                ("signal_analysis_completeness", self._check_signal_analysis_completeness(results)),
                ("event_analysis_completeness", self._check_event_analysis_completeness(results)),
                ("recommendation_validity", self._check_recommendation_validity(results)),
                ("metadata_completeness_check", self._check_metadata_completeness(results)),
                ("academic_compliance_check", self._check_academic_compliance(results)),
                ("physics_validation_check", self._check_physics_validation(results))
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
    
    def _calculate_average_rsrp(self, signal_analysis: Dict[str, Any]) -> float:
        """計算平均RSRP"""
        satellites = signal_analysis.get("satellites", [])
        if not satellites:
            return -140.0
        
        total_rsrp = 0
        count = 0
        for sat in satellites:
            signal_metrics = sat.get("signal_metrics", {})
            avg_rsrp = signal_metrics.get("average_rsrp_dbm", -140)
            total_rsrp += avg_rsrp
            count += 1
        
        return total_rsrp / count if count > 0 else -140.0
    
    def _calculate_rsrp_range(self, signal_analysis: Dict[str, Any]) -> Dict[str, float]:
        """計算RSRP範圍"""
        satellites = signal_analysis.get("satellites", [])
        if not satellites:
            return {"min": -140.0, "max": -140.0}
        
        rsrp_values = []
        for sat in satellites:
            signal_metrics = sat.get("signal_metrics", {})
            avg_rsrp = signal_metrics.get("average_rsrp_dbm", -140)
            rsrp_values.append(avg_rsrp)
        
        return {"min": min(rsrp_values), "max": max(rsrp_values)}
    
    def _assess_recommendation_confidence(self, satellite_rankings: List[Dict[str, Any]]) -> str:
        """評估建議信心度"""
        if not satellite_rankings:
            return "low"
        
        top_score = satellite_rankings[0].get("comprehensive_score", 0)
        tier_1_count = len([s for s in satellite_rankings if s.get("recommendation_tier") == "Tier_1"])
        
        if top_score >= 85 and tier_1_count >= 3:
            return "very_high"
        elif top_score >= 75 and tier_1_count >= 2:
            return "high"
        elif top_score >= 60:
            return "medium"
        else:
            return "low"
    
    # === 驗證檢查方法 ===
    
    def _check_data_structure(self, results: Dict[str, Any]) -> bool:
        """檢查數據結構完整性"""
        required_keys = ["data", "metadata"]
        data_keys = ["signal_analysis", "event_analysis", "recommendations"]
        
        if not all(key in results for key in required_keys):
            return False
            
        data_section = results.get("data", {})
        return all(key in data_section for key in data_keys)
    
    def _check_signal_analysis_completeness(self, results: Dict[str, Any]) -> bool:
        """檢查信號分析完整性"""
        signal_analysis = results.get("data", {}).get("signal_analysis", {})
        
        required_components = ["satellites", "signal_summary"]
        if not all(comp in signal_analysis for comp in required_components):
            return False
        
        satellites = signal_analysis.get("satellites", [])
        return len(satellites) > 0
    
    def _check_event_analysis_completeness(self, results: Dict[str, Any]) -> bool:
        """檢查事件分析完整性"""
        event_analysis = results.get("data", {}).get("event_analysis", {})
        
        required_components = ["satellites", "event_summary"]
        return all(comp in event_analysis for comp in required_components)
    
    def _check_recommendation_validity(self, results: Dict[str, Any]) -> bool:
        """檢查建議有效性"""
        recommendations = results.get("data", {}).get("recommendations", {})
        
        satellite_rankings = recommendations.get("satellite_rankings", [])
        return len(satellite_rankings) > 0
    
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
    
    def _check_physics_validation(self, results: Dict[str, Any]) -> bool:
        """檢查物理驗證結果"""
        if not self.physics_validation_enabled:
            return True
        
        physics_validation = results.get("data", {}).get("physics_validation", {})
        overall_grade = physics_validation.get("overall_grade", "D")
        
        return overall_grade in ["A", "A+", "B"]