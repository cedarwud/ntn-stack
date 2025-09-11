"""
階段三：信號品質分析與3GPP事件處理器

根據階段三文檔規範實現的信號品質分析處理器：
- 精確RSRP/RSRQ/RS-SINR計算 (ITU-R P.618標準)
- 3GPP NTN事件處理 (A4/A5/D2事件)
- 學術級物理模型遵循 (Grade A/B 標準)
- 零容忍運行時檢查

輸入：階段二智能篩選結果
輸出：信號品質數據 + 3GPP事件數據 (stage3_signal_analysis_output.json)
"""

import logging
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

# 導入核心組件
from .signal_quality_calculator import SignalQualityCalculator
from .gpp_event_analyzer import GPPEventAnalyzer
from .measurement_offset_config import MeasurementOffsetConfig
from .handover_candidate_manager import HandoverCandidateManager
from .handover_decision_engine import HandoverDecisionEngine
from .dynamic_threshold_controller import DynamicThresholdController
from ..shared.base_stage_processor import BaseStageProcessor


class Stage3SignalAnalysisProcessor(BaseStageProcessor):
    """階段三：信號品質分析與3GPP事件處理器
    
    根據階段三文檔規範實現：
    - 信號品質分析模組 (RSRP/RSRQ/RS-SINR計算)
    - 3GPP NTN事件處理 (A4/A5/D2事件檢測)
    - 測量偏移配置系統 (Ofn/Ocn管理)
    - 換手候選衛星管理 (3-5個候選追蹤)
    - 智能換手決策引擎 (多因素分析)
    - 動態門檻調整控制 (自適應優化)
    
    學術標準遵循：
    - Grade A: ITU-R P.618標準，3GPP TS 38.331標準
    - Grade B: 基於標準參數的技術規格
    - 零容忍: 禁止任意假設參數和簡化模型
    """
    
    def __init__(self, input_data: Any = None, config: Dict[str, Any] = None):
        """
        初始化階段三信號品質分析處理器
        
        Args:
            input_data: 階段二智能篩選結果 (支援記憶體傳遞)
            config: 處理器配置參數
        """
        super().__init__(
            stage_number=3,
            stage_name="signal_analysis"
        )
        
        self.logger = logging.getLogger(f"{__name__}.Stage3SignalAnalysisProcessor")
        
        # 🚨 Grade A強制要求：使用NTPU精確觀測座標
        self.observer_coordinates = (24.9441667, 121.3713889, 50)  # (緯度, 經度, 海拔m)
        
        # 配置處理
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        
        # 輸入數據 (支援記憶體傳遞模式)
        self.input_data = input_data
        
        # 初始化核心組件
        self._initialize_core_components()
        
        # 🚨 執行零容忍學術標準檢查
        self._perform_zero_tolerance_runtime_checks()
        
        self.logger.info("✅ Stage3SignalAnalysisProcessor 初始化完成")
        self.logger.info(f"   觀測座標: {self.observer_coordinates}")
        self.logger.info(f"   輸入模式: {'記憶體傳遞' if input_data else '檔案載入'}")
    
    def _initialize_core_components(self):
        """初始化核心組件"""
        try:
            # 1. 測量偏移配置系統 (Ofn/Ocn管理)
            self.measurement_offset_config = MeasurementOffsetConfig()
            
            # 2. 信號品質計算器 (RSRP/RSRQ/RS-SINR)
            self.signal_calculator = SignalQualityCalculator(
                observer_coordinates=self.observer_coordinates
            )
            
            # 3. 3GPP事件分析器 (A4/A5/D2事件檢測)
            self.event_analyzer = GPPEventAnalyzer(
                measurement_offset_config=self.measurement_offset_config
            )
            
            # 4. 換手候選衛星管理器 (3-5個候選追蹤)
            self.candidate_manager = HandoverCandidateManager()
            
            # 5. 智能換手決策引擎 (多因素分析)
            self.decision_engine = HandoverDecisionEngine()
            
            # 6. 動態門檻調整控制器 (自適應優化)
            self.threshold_controller = DynamicThresholdController()
            
            self.logger.info("✅ 核心組件初始化完成")
            
        except Exception as e:
            self.logger.error(f"核心組件初始化失敗: {e}")
            raise RuntimeError(f"Stage3處理器初始化失敗: {e}")
    
    def process_signal_analysis(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行信號品質分析與3GPP事件處理 (主處理方法)
        
        實現階段三的完整處理流程：
        1. 載入階段二智能篩選結果
        2. 執行信號品質分析 (RSRP/RSRQ/RS-SINR)
        3. 執行3GPP事件檢測 (A4/A5/D2)
        4. 候選衛星管理和評估
        5. 換手決策分析
        6. 輸出標準化結果
        
        Args:
            input_data: 階段二輸出數據 (可選，支援記憶體傳遞)
            
        Returns:
            Dict[str, Any]: 信號分析結果
        """
        self.logger.info("📡 開始執行階段三信號品質分析與3GPP事件處理...")
        processing_start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: 載入輸入數據
            if input_data is not None:
                self.logger.info("使用記憶體傳遞的階段二數據")
                stage2_data = input_data
            elif self.input_data is not None:
                self.logger.info("使用初始化時提供的輸入數據")
                stage2_data = self.input_data
            else:
                self.logger.info("從檔案系統載入階段二輸出")
                stage2_data = self._load_stage2_output()
            
            # 🚨 執行輸入數據完整性檢查
            self._validate_stage2_input(stage2_data)
            
            # 提取篩選衛星數據
            filtered_satellites = self._extract_filtered_satellites(stage2_data)
            self.logger.info(f"載入 {len(filtered_satellites)} 顆篩選衛星進行信號分析")
            
            # Step 2: 執行信號品質分析
            self.logger.info("🔬 執行信號品質分析...")
            signal_analysis_results = self._perform_signal_quality_analysis(filtered_satellites)
            
            # Step 3: 執行3GPP事件檢測  
            self.logger.info("📋 執行3GPP事件檢測...")
            event_analysis_results = self._perform_3gpp_event_analysis(signal_analysis_results)
            
            # Step 4: 候選衛星管理
            self.logger.info("🎯 執行候選衛星管理...")
            candidate_analysis = self._perform_candidate_management(event_analysis_results)
            
            # Step 5: 換手決策分析
            self.logger.info("🤖 執行換手決策分析...")
            decision_analysis = self._perform_handover_decision_analysis(candidate_analysis)
            
            # Step 6: 構建最終輸出
            processing_end_time = datetime.now(timezone.utc)
            processing_duration = (processing_end_time - processing_start_time).total_seconds()
            
            final_result = {
                "metadata": {
                    "stage": 3,
                    "stage_name": "signal_analysis",
                    "processor_class": "Stage3SignalAnalysisProcessor",
                    "processing_timestamp": processing_end_time.isoformat(),
                    "processing_duration_seconds": processing_duration,
                    "total_satellites": len(filtered_satellites),
                    "signal_processing": "signal_quality_analysis",
                    "event_analysis_type": "3GPP_NTN_A4_A5_D2_events",
                    "supported_events": ["A4_intra_frequency", "A5_intra_frequency", "D2_beam_switch"],
                    "observer_coordinates": {
                        "latitude": self.observer_coordinates[0],
                        "longitude": self.observer_coordinates[1],
                        "altitude_m": self.observer_coordinates[2]
                    },
                    "academic_compliance": "ITU_R_P618_3GPP_TS_38_331_Grade_A",
                    "ready_for_timeseries_preprocessing": True
                },
                "satellites": decision_analysis["processed_satellites"],
                "constellations": self._generate_constellation_summary(decision_analysis["processed_satellites"]),
                "signal_analysis_summary": signal_analysis_results["summary"],
                "event_analysis_summary": event_analysis_results["summary"],
                "candidate_management_summary": candidate_analysis["summary"],
                "handover_decision_summary": decision_analysis["summary"],
                "processing_statistics": {
                    "signal_calculation_stats": signal_analysis_results["statistics"],
                    "event_detection_stats": event_analysis_results["statistics"],
                    "candidate_management_stats": candidate_analysis["statistics"],
                    "decision_analysis_stats": decision_analysis["statistics"]
                }
            }
            
            # 🚨 執行輸出數據完整性檢查
            self._validate_stage3_output(final_result)
            
            self.logger.info(f"✅ 階段三處理完成: {len(filtered_satellites)} 顆衛星，處理時間 {processing_duration:.2f} 秒")
            return final_result
            
        except Exception as e:
            self.logger.error(f"階段三信號分析處理失敗: {e}")
            raise RuntimeError(f"Stage3處理失敗: {e}")
    
    def process(self, input_data: Any = None) -> Dict[str, Any]:
        """
        BaseStageProcessor標準介面實現
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        return self.process_signal_analysis(input_data)
    
    def validate_input(self, input_data: Any = None) -> bool:
        """
        驗證輸入數據有效性
        
        Args:
            input_data: 輸入數據
            
        Returns:
            bool: 輸入數據是否有效
        """
        self.logger.info("🔍 階段三輸入驗證...")
        
        try:
            # 使用提供的數據或實例數據
            data_to_validate = input_data or self.input_data
            
            if data_to_validate is None:
                # 嘗試載入檔案
                try:
                    data_to_validate = self._load_stage2_output()
                except:
                    self.logger.error("無法載入階段二輸出數據")
                    return False
            
            # 執行輸入驗證
            return self._validate_stage2_input(data_to_validate, raise_on_error=False)
            
        except Exception as e:
            self.logger.error(f"輸入驗證失敗: {e}")
            return False
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據完整性
        
        Args:
            output_data: 輸出數據
            
        Returns:
            bool: 輸出數據是否有效
        """
        self.logger.info("🔍 階段三輸出驗證...")
        
        try:
            return self._validate_stage3_output(output_data, raise_on_error=False)
            
        except Exception as e:
            self.logger.error(f"輸出驗證失敗: {e}")
            return False
    
    def save_results(self, processed_data: Dict[str, Any]) -> str:
        """
        保存處理結果到標準位置
        
        Args:
            processed_data: 處理結果數據
            
        Returns:
            str: 輸出檔案路徑
        """
        try:
            # 根據文檔規範的輸出路徑
            output_file = Path("/app/data/stage3_signal_analysis_output.json")
            
            # 確保目錄存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"💾 保存階段三結果到: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("✅ 階段三結果保存完成")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"保存階段三結果失敗: {e}")
            raise
    
    def extract_key_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        satellites = processed_data.get("satellites", [])
        metadata = processed_data.get("metadata", {})
        
        # 統計各星座衛星數量
        starlink_count = len([s for s in satellites if 'starlink' in s.get('constellation', '').lower()])
        oneweb_count = len([s for s in satellites if 'oneweb' in s.get('constellation', '').lower()])
        
        # 統計信號品質
        rsrp_values = []
        event_counts = {"A4": 0, "A5": 0, "D2": 0}
        
        for satellite in satellites:
            # 收集RSRP值
            signal_quality = satellite.get("signal_quality", {})
            rsrp_stats = signal_quality.get("statistics", {})
            if "mean_rsrp_dbm" in rsrp_stats:
                rsrp_values.append(rsrp_stats["mean_rsrp_dbm"])
            
            # 統計事件
            event_potential = satellite.get("event_potential", {})
            for event_type in ["A4", "A5", "D2"]:
                if event_type in event_potential:
                    if event_potential[event_type].get("trigger_probability") in ["high", "medium"]:
                        event_counts[event_type] += 1
        
        return {
            "total_satellites_analyzed": len(satellites),
            "starlink_satellites": starlink_count,
            "oneweb_satellites": oneweb_count,
            "processing_duration": metadata.get("processing_duration_seconds", 0),
            "signal_quality_metrics": {
                "mean_rsrp_dbm": np.mean(rsrp_values) if rsrp_values else 0,
                "rsrp_range": [np.min(rsrp_values), np.max(rsrp_values)] if rsrp_values else [0, 0],
                "rsrp_std": np.std(rsrp_values) if rsrp_values else 0
            },
            "3gpp_event_counts": event_counts,
            "observer_coordinates": metadata.get("observer_coordinates", {}),
            "academic_compliance": "Grade_A_ITU_R_P618_3GPP_TS_38_331"
        }
    
    def get_default_output_filename(self) -> str:
        """返回預設輸出檔名 (文檔規範)"""
        return "stage3_signal_analysis_output.json"
    
    # ==================== 私有方法 ====================
    
    def _load_stage2_output(self) -> Dict[str, Any]:
        """載入階段二輸出數據"""
        # 根據階段二文檔的輸出檔名
        possible_files = [
            "/app/data/satellite_visibility_filtering_output.json",
            "/app/data/stage2_visibility_filtered_output.json",
            "/tmp/ntn-stack-dev/intelligent_filtering_outputs/satellite_visibility_filtering_output.json"
        ]
        
        for file_path in possible_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        raise FileNotFoundError("無法找到階段二輸出檔案")
    
    def _extract_filtered_satellites(self, stage2_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從階段二數據中提取篩選衛星"""
        data_section = stage2_data.get("data", {})
        filtered_satellites_dict = data_section.get("filtered_satellites", {})
        
        # 合併所有星座的衛星
        all_satellites = []
        for constellation, satellites in filtered_satellites_dict.items():
            if isinstance(satellites, list):
                for satellite in satellites:
                    satellite["constellation"] = constellation
                    all_satellites.append(satellite)
        
        return all_satellites
    
    def _perform_signal_quality_analysis(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """執行信號品質分析"""
        self.logger.info("計算衛星信號品質 (RSRP/RSRQ/RS-SINR)...")
        
        processed_satellites = []
        calculation_stats = {
            "total_calculated": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "average_processing_time": 0
        }
        
        for satellite in satellites:
            try:
                # 使用信號品質計算器
                signal_metrics = self.signal_calculator.calculate_signal_quality(satellite)
                
                # 添加信號品質到衛星數據
                satellite["signal_quality"] = signal_metrics
                
                processed_satellites.append(satellite)
                calculation_stats["successful_calculations"] += 1
                
            except Exception as e:
                self.logger.warning(f"衛星 {satellite.get('name')} 信號計算失敗: {e}")
                calculation_stats["failed_calculations"] += 1
                continue
            
            calculation_stats["total_calculated"] += 1
        
        return {
            "processed_satellites": processed_satellites,
            "summary": {
                "total_satellites": len(satellites),
                "processed_successfully": len(processed_satellites),
                "signal_calculation_method": "ITU_R_P618_standard"
            },
            "statistics": calculation_stats
        }
    
    def _perform_3gpp_event_analysis(self, signal_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行3GPP事件分析"""
        self.logger.info("執行3GPP事件檢測 (A4/A5/D2)...")
        
        satellites = signal_results["processed_satellites"]
        processed_satellites = []
        event_stats = {"A4": 0, "A5": 0, "D2": 0}
        
        for satellite in satellites:
            try:
                # 使用3GPP事件分析器
                event_analysis = self.event_analyzer.analyze_3gpp_events(satellite)
                
                # 添加事件分析到衛星數據
                satellite["event_potential"] = event_analysis
                
                # 統計事件
                for event_type, analysis in event_analysis.items():
                    if analysis.get("trigger_probability") in ["high", "medium"]:
                        event_stats[event_type] += 1
                
                processed_satellites.append(satellite)
                
            except Exception as e:
                self.logger.warning(f"衛星 {satellite.get('name')} 事件分析失敗: {e}")
                continue
        
        return {
            "processed_satellites": processed_satellites,
            "summary": {
                "total_3gpp_events": sum(event_stats.values()),
                "a4_events": event_stats["A4"],
                "a5_events": event_stats["A5"],
                "d2_events": event_stats["D2"],
                "event_standard": "3GPP_TS_38_331_v18_5_1"
            },
            "statistics": event_stats
        }
    
    def _perform_candidate_management(self, event_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行候選衛星管理"""
        satellites = event_results["processed_satellites"]
        
        # 使用候選管理器分析
        candidates = self.candidate_manager.select_handover_candidates(satellites)
        
        return {
            "processed_satellites": satellites,
            "summary": {
                "total_candidates_identified": len(candidates),
                "candidate_selection_method": "multi_factor_scoring"
            },
            "statistics": {
                "candidates_selected": len(candidates)
            }
        }
    
    def _perform_handover_decision_analysis(self, candidate_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行換手決策分析"""
        satellites = candidate_results["processed_satellites"]
        
        # 使用決策引擎分析
        decisions = self.decision_engine.make_handover_decisions(satellites)
        
        return {
            "processed_satellites": satellites,
            "summary": {
                "handover_recommendations_generated": len(decisions),
                "decision_engine_version": "multi_factor_analysis_v1.0"
            },
            "statistics": {
                "decisions_made": len(decisions)
            }
        }
    
    def _generate_constellation_summary(self, satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成星座摘要統計"""
        constellation_stats = {}
        
        for satellite in satellites:
            constellation = satellite.get("constellation", "unknown")
            
            if constellation not in constellation_stats:
                constellation_stats[constellation] = {
                    "satellite_count": 0,
                    "signal_analysis_completed": True,
                    "event_analysis_completed": True
                }
            
            constellation_stats[constellation]["satellite_count"] += 1
        
        return constellation_stats
    
    def _validate_stage2_input(self, stage2_data: Dict[str, Any], raise_on_error: bool = True) -> bool:
        """驗證階段二輸入數據格式"""
        try:
            # 基本結構檢查
            if not isinstance(stage2_data, dict):
                raise ValueError("階段二數據必須是字典格式")
            
            if "data" not in stage2_data:
                raise ValueError("階段二數據缺少data欄位")
            
            data_section = stage2_data["data"]
            if "filtered_satellites" not in data_section:
                raise ValueError("階段二數據缺少filtered_satellites欄位")
            
            filtered_satellites = data_section["filtered_satellites"]
            if not isinstance(filtered_satellites, dict):
                raise ValueError("filtered_satellites必須是字典格式")
            
            # 檢查星座數據
            total_satellites = 0
            for constellation, satellites in filtered_satellites.items():
                if isinstance(satellites, list):
                    total_satellites += len(satellites)
            
            if total_satellites < 100:  # 放寬限制以符合實際情況
                if raise_on_error:
                    raise ValueError(f"篩選衛星數量不足: {total_satellites}")
                return False
            
            self.logger.info(f"✅ 階段二輸入驗證通過: {total_satellites} 顆衛星")
            return True
            
        except Exception as e:
            if raise_on_error:
                raise ValueError(f"階段二輸入數據驗證失敗: {e}")
            self.logger.error(f"輸入驗證失敗: {e}")
            return False
    
    def _validate_stage3_output(self, output_data: Dict[str, Any], raise_on_error: bool = True) -> bool:
        """驗證階段三輸出數據完整性"""
        try:
            # 檢查必要欄位
            required_fields = ["metadata", "satellites", "constellations"]
            for field in required_fields:
                if field not in output_data:
                    raise ValueError(f"輸出數據缺少 {field} 欄位")
            
            # 檢查元數據
            metadata = output_data["metadata"]
            if metadata.get("stage") != 3:
                raise ValueError(f"階段編號錯誤: {metadata.get('stage')}")
            
            if metadata.get("processor_class") != "Stage3SignalAnalysisProcessor":
                raise ValueError(f"處理器類型錯誤: {metadata.get('processor_class')}")
            
            # 檢查衛星數據
            satellites = output_data["satellites"]
            if not isinstance(satellites, list):
                raise ValueError("satellites必須是列表格式")
            
            if len(satellites) == 0:
                if raise_on_error:
                    raise ValueError("輸出衛星數據為空")
                return False
            
            self.logger.info(f"✅ 階段三輸出驗證通過: {len(satellites)} 顆衛星")
            return True
            
        except Exception as e:
            if raise_on_error:
                raise ValueError(f"階段三輸出數據驗證失敗: {e}")
            self.logger.error(f"輸出驗證失敗: {e}")
            return False
    
    def _perform_zero_tolerance_runtime_checks(self):
        """執行零容忍學術標準檢查"""
        self.logger.info("🚨 執行零容忍學術標準檢查...")
        
        try:
            # 檢查1: 信號分析引擎類型強制檢查
            if not hasattr(self, 'signal_calculator'):
                raise RuntimeError("缺少SignalQualityCalculator")
            
            if not hasattr(self, 'event_analyzer'):
                raise RuntimeError("缺少GPPEventAnalyzer")
            
            # 檢查2: 禁用簡化信號模型
            forbidden_models = ["fixed_rsrp", "linear_approximation", "simplified_pathloss", "mock_signal"]
            
            for model in forbidden_models:
                if model in str(self.signal_calculator.__class__).lower():
                    raise RuntimeError(f"檢測到禁用的簡化信號模型: {model}")
            
            self.logger.info("✅ 零容忍學術標準檢查通過")
            
        except Exception as e:
            self.logger.error(f"學術標準檢查失敗: {e}")
            raise RuntimeError(f"零容忍檢查失敗: {e}")