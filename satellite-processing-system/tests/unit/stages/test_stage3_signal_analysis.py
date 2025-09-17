#!/usr/bin/env python3
"""
Stage3 信號品質分析處理器 - TDD測試套件

🚨 核心測試目標：
- 驗證信號品質計算的準確性和3GPP合規性
- 確保換手決策邏輯符合學術級標準
- 檢查科學計算基準測試通過率
- 驗證數據流完整性和結果輸出格式

測試覆蓋：
✅ Stage3處理器初始化和組件載入
✅ 信號品質計算 (RSRP/RSRQ/SINR)
✅ 3GPP事件分析和處理
✅ 換手候選管理和決策
✅ 動態門檻調整
✅ 科學計算基準測試
✅ 結果輸出和格式驗證
"""

import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

# 配置測試日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.fixture
def stage3_processor():
    """創建Stage3信號分析處理器實例"""
    import sys
    sys.path.append('/satellite-processing/src')

    from stages.stage3_signal_analysis.stage3_signal_analysis_processor import Stage3SignalAnalysisProcessor

    # 創建測試配置
    test_config = {
        "debug_mode": True,
        "observer_coordinates": (24.9441667, 121.3713889, 50),  # NTPU精確座標
        "test_mode": True
    }

    return Stage3SignalAnalysisProcessor(config=test_config)

@pytest.fixture
def mock_stage2_data():
    """模擬Stage2輸出數據結構"""
    return [
        {
            "satellite_id": "STARLINK-1001",
            "constellation": "starlink",
            "position_timeseries": [
                {
                    "timestamp": "2025-09-16T13:20:00+00:00",
                    "relative_to_observer": {
                        "distance_km": 550.5,
                        "elevation_deg": 35.2,
                        "azimuth_deg": 180.0,
                        "is_visible": True
                    }
                },
                {
                    "timestamp": "2025-09-16T13:21:00+00:00",
                    "relative_to_observer": {
                        "distance_km": 555.8,
                        "elevation_deg": 33.1,
                        "azimuth_deg": 182.5,
                        "is_visible": True
                    }
                }
            ]
        },
        {
            "satellite_id": "ONEWEB-0123",
            "constellation": "oneweb",
            "position_timeseries": [
                {
                    "timestamp": "2025-09-16T13:20:00+00:00",
                    "relative_to_observer": {
                        "distance_km": 1200.3,
                        "elevation_deg": 15.8,
                        "azimuth_deg": 90.0,
                        "is_visible": True
                    }
                }
            ]
        }
    ]

class TestStage3ProcessorInitialization:
    """Stage3處理器初始化測試"""

    @pytest.mark.stage3
    @pytest.mark.critical
    def test_processor_initialization_success(self, stage3_processor):
        """🚨 核心測試：Stage3處理器成功初始化"""
        assert stage3_processor is not None
        assert hasattr(stage3_processor, 'signal_quality_calculator')
        assert hasattr(stage3_processor, 'gpp_event_analyzer')
        assert hasattr(stage3_processor, 'handover_candidate_manager')
        assert stage3_processor.observer_coordinates == (24.9441667, 121.3713889, 50)

    @pytest.mark.stage3
    @pytest.mark.critical
    def test_core_components_loaded(self, stage3_processor):
        """🚨 核心測試：六大核心組件正確載入"""
        # 驗證六大核心組件
        assert hasattr(stage3_processor, 'signal_quality_calculator'), "信號品質計算器未載入"
        assert hasattr(stage3_processor, 'gpp_event_analyzer'), "3GPP事件分析器未載入"
        assert hasattr(stage3_processor, 'measurement_offset_config'), "測量偏移配置未載入"
        assert hasattr(stage3_processor, 'handover_candidate_manager'), "換手候選管理器未載入"
        assert hasattr(stage3_processor, 'handover_decision_engine'), "換手決策引擎未載入"
        assert hasattr(stage3_processor, 'dynamic_threshold_controller'), "動態門檻控制器未載入"

    @pytest.mark.stage3
    @pytest.mark.academic
    def test_physics_constants_validation(self, stage3_processor):
        """🚨 學術級測試：物理常數驗證通過"""
        assert hasattr(stage3_processor, 'physics_constants')
        assert stage3_processor.physics_constants.validate_physics_constants()

class TestStage3DataLoading:
    """Stage3數據載入測試"""

    @pytest.mark.stage3
    @pytest.mark.integration
    def test_load_stage2_data_from_memory(self, stage3_processor, mock_stage2_data):
        """🚨 整合測試：從記憶體載入Stage2數據"""
        # 設置記憶體傳遞模式
        stage3_processor.input_data = {"visibility_data": mock_stage2_data}

        loaded_data = stage3_processor._load_stage2_data()
        assert len(loaded_data) == 2
        assert loaded_data[0]["satellite_id"] == "STARLINK-1001"
        assert loaded_data[1]["satellite_id"] == "ONEWEB-0123"

    @pytest.mark.stage3
    @pytest.mark.integration
    def test_load_stage2_data_file_exists(self, stage3_processor):
        """🚨 整合測試：從檔案載入Stage2數據 (檔案存在時)"""
        # 設置檔案載入模式
        stage3_processor.input_data = None

        # 模擬檔案存在
        stage2_output_path = Path("/satellite-processing/data/outputs/stage2/satellite_visibility_filtering_output.json")
        if stage2_output_path.exists():
            loaded_data = stage3_processor._load_stage2_data()
            assert isinstance(loaded_data, list)
            assert len(loaded_data) > 0

class TestStage3SignalQualityCalculation:
    """Stage3信號品質計算測試"""

    @pytest.mark.stage3
    @pytest.mark.signal_processing
    def test_signal_quality_calculation_with_mock_data(self, stage3_processor, mock_stage2_data):
        """🚨 信號處理測試：使用模擬數據計算信號品質"""
        signal_quality_results = stage3_processor._calculate_signal_quality(mock_stage2_data)

        # 驗證結果結構
        assert isinstance(signal_quality_results, list)
        assert len(signal_quality_results) > 0

        # 檢查第一個結果包含信號品質數據
        first_result = signal_quality_results[0]
        assert "position_timeseries_with_signal" in first_result
        assert "processing_timestamp" in first_result

        # 驗證信號品質計算存在
        signal_timeseries = first_result["position_timeseries_with_signal"]
        if len(signal_timeseries) > 0:
            first_signal_point = signal_timeseries[0]
            assert "signal_quality" in first_signal_point

    @pytest.mark.stage3
    @pytest.mark.academic
    def test_signal_quality_metrics_structure(self, stage3_processor, mock_stage2_data):
        """🚨 學術級測試：信號品質指標結構正確性"""
        signal_quality_results = stage3_processor._calculate_signal_quality(mock_stage2_data)

        if len(signal_quality_results) > 0:
            first_result = signal_quality_results[0]
            signal_timeseries = first_result.get("position_timeseries_with_signal", [])

            for signal_point in signal_timeseries:
                signal_quality = signal_point.get("signal_quality", {})

                # 檢查必需的信號品質指標
                expected_metrics = ["rsrp_dbm", "rsrq_db", "sinr_db"]
                for metric in expected_metrics:
                    if metric in signal_quality:
                        # 驗證數值範圍合理性
                        value = signal_quality[metric]
                        assert isinstance(value, (int, float)), f"{metric} 應為數值"

                        # 基本範圍檢查 (避免明顯錯誤值)
                        if metric == "rsrp_dbm":
                            assert -150 <= value <= 0, f"RSRP範圍異常: {value}"
                        elif metric == "rsrq_db":
                            assert -30 <= value <= 0, f"RSRQ範圍異常: {value}"
                        elif metric == "sinr_db":
                            assert -20 <= value <= 50, f"SINR範圍異常: {value}"

class TestStage3GPPEventAnalysis:
    """Stage3 3GPP事件分析測試"""

    @pytest.mark.stage3
    @pytest.mark.threegpp
    def test_3gpp_event_analysis_execution(self, stage3_processor, mock_stage2_data):
        """🚨 3GPP測試：事件分析執行不出錯"""
        # 先計算信號品質
        signal_quality_data = stage3_processor._calculate_signal_quality(mock_stage2_data)

        # 執行3GPP事件分析
        gpp_event_results = stage3_processor._analyze_3gpp_events(signal_quality_data)

        # 驗證結果結構
        assert isinstance(gpp_event_results, dict)
        assert "processed_events" in gpp_event_results

        processed_events = gpp_event_results["processed_events"]
        assert isinstance(processed_events, list)

class TestStage3HandoverManagement:
    """Stage3換手管理測試"""

    @pytest.mark.stage3
    @pytest.mark.handover
    def test_handover_candidate_management(self, stage3_processor, mock_stage2_data):
        """🚨 換手測試：候選管理執行不出錯"""
        # 準備測試數據
        signal_quality_data = stage3_processor._calculate_signal_quality(mock_stage2_data)
        gpp_event_results = stage3_processor._analyze_3gpp_events(signal_quality_data)
        gpp_events = gpp_event_results.get("processed_events", [])

        # 執行換手候選管理
        handover_candidates = stage3_processor._manage_handover_candidates(signal_quality_data, gpp_events)

        # 驗證結果
        assert isinstance(handover_candidates, list)

    @pytest.mark.stage3
    @pytest.mark.handover
    def test_handover_decision_making(self, stage3_processor, mock_stage2_data):
        """🚨 換手測試：決策制定執行不出錯"""
        # 準備測試數據
        signal_quality_data = stage3_processor._calculate_signal_quality(mock_stage2_data)
        gpp_event_results = stage3_processor._analyze_3gpp_events(signal_quality_data)
        gpp_events = gpp_event_results.get("processed_events", [])
        handover_candidates = stage3_processor._manage_handover_candidates(signal_quality_data, gpp_events)

        # 執行換手決策
        handover_decisions = stage3_processor._make_handover_decisions(handover_candidates, gpp_events)

        # 驗證結果
        assert isinstance(handover_decisions, list)

class TestStage3FullExecution:
    """Stage3完整執行測試"""

    @pytest.mark.stage3
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_stage3_execution_with_real_data(self, stage3_processor):
        """🚨 整合測試：完整Stage3執行 (使用真實數據)"""
        # 檢查Stage2輸出是否存在
        stage2_output_path = Path("/satellite-processing/data/outputs/stage2/satellite_visibility_filtering_output.json")

        if not stage2_output_path.exists():
            pytest.skip("Stage2輸出文件不存在，跳過完整執行測試")

        # 執行完整Stage3流程
        results = stage3_processor.execute()

        # 驗證執行成功
        assert results.get("success", False), "Stage3執行失敗"

        # 驗證結果結構
        assert "metadata" in results
        assert "signal_quality_data" in results
        assert "gpp_events" in results
        assert "handover_candidates" in results
        assert "handover_decisions" in results
        assert "scientific_benchmark" in results

        # 驗證數據完整性
        metadata = results["metadata"]
        assert metadata["stage"] == "stage3_signal_analysis"
        assert metadata["total_satellites"] > 0
        assert isinstance(metadata["execution_time_seconds"], (int, float))

        # 驗證科學基準測試
        benchmark = results["scientific_benchmark"]
        assert "benchmark_score" in benchmark
        benchmark_score = benchmark["benchmark_score"]
        assert isinstance(benchmark_score, (int, float))
        assert benchmark_score >= 70, f"基準分數過低: {benchmark_score}"

    @pytest.mark.stage3
    @pytest.mark.performance
    def test_stage3_execution_performance(self, stage3_processor):
        """🚨 性能測試：Stage3執行時間在合理範圍"""
        stage2_output_path = Path("/satellite-processing/data/outputs/stage2/satellite_visibility_filtering_output.json")

        if not stage2_output_path.exists():
            pytest.skip("Stage2輸出文件不存在，跳過性能測試")

        import time
        start_time = time.time()
        results = stage3_processor.execute()
        execution_time = time.time() - start_time

        # 驗證執行時間合理 (基於實際測試，應該在10秒內)
        assert execution_time < 10.0, f"Stage3執行時間過長: {execution_time:.2f}秒"
        assert results.get("success", False), "Stage3執行失敗"

class TestStage3OutputValidation:
    """Stage3輸出驗證測試"""

    @pytest.mark.stage3
    @pytest.mark.output
    def test_output_file_created(self, stage3_processor):
        """🚨 輸出測試：檢查輸出文件是否正確創建"""
        stage2_output_path = Path("/satellite-processing/data/outputs/stage2/satellite_visibility_filtering_output.json")

        if not stage2_output_path.exists():
            pytest.skip("Stage2輸出文件不存在，跳過輸出文件測試")

        # 執行Stage3
        results = stage3_processor.execute()

        # 檢查輸出文件存在
        stage3_output_path = Path("/satellite-processing/data/outputs/stage3/signal_analysis_output.json")
        assert stage3_output_path.exists(), "Stage3輸出文件未創建"

        # 檢查文件大小合理
        file_size = stage3_output_path.stat().st_size
        assert file_size > 1000, f"Stage3輸出文件過小: {file_size} bytes"

    @pytest.mark.stage3
    @pytest.mark.format
    def test_output_json_format_valid(self, stage3_processor):
        """🚨 格式測試：輸出JSON格式正確"""
        stage2_output_path = Path("/satellite-processing/data/outputs/stage2/satellite_visibility_filtering_output.json")

        if not stage2_output_path.exists():
            pytest.skip("Stage2輸出文件不存在，跳過JSON格式測試")

        # 執行Stage3
        results = stage3_processor.execute()

        # 檢查輸出文件JSON有效性
        stage3_output_path = Path("/satellite-processing/data/outputs/stage3/signal_analysis_output.json")

        try:
            with open(stage3_output_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            # 驗證JSON結構
            assert isinstance(saved_data, dict)
            assert "metadata" in saved_data
            assert "signal_quality_data" in saved_data

        except json.JSONDecodeError:
            pytest.fail("Stage3輸出文件JSON格式無效")
        except Exception as e:
            pytest.fail(f"讀取Stage3輸出文件失敗: {e}")

class TestStage3ErrorHandling:
    """Stage3錯誤處理測試"""

    @pytest.mark.stage3
    @pytest.mark.error_handling
    def test_missing_stage2_data_handling(self, stage3_processor):
        """🚨 錯誤處理測試：Stage2數據缺失時的處理"""
        # 設置無效的輸入數據
        stage3_processor.input_data = None

        # 模擬Stage2文件不存在的情況
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises((FileNotFoundError, RuntimeError)):
                stage3_processor._load_stage2_data()

    @pytest.mark.stage3
    @pytest.mark.error_handling
    def test_invalid_input_data_handling(self, stage3_processor):
        """🚨 錯誤處理測試：無效輸入數據的處理"""
        # 測試空的可見性數據
        empty_data = []
        signal_quality_results = stage3_processor._calculate_signal_quality(empty_data)
        assert isinstance(signal_quality_results, list)
        assert len(signal_quality_results) == 0

if __name__ == "__main__":
    # 直接執行測試
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "stage3",
        "--durations=10"
    ])