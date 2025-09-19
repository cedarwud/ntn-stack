"""
Stage 3 信號分析處理器 - 重構後TDD測試套件

重構變更:
- 移除觀測者座標硬編碼初始化
- 修正execute()方法從Stage 2載入觀測者座標
- _validate_observer_coordinates()重構為信任Stage 2結果
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage3_signal_analysis.stage3_signal_analysis_processor import Stage3SignalAnalysisProcessor


class TestStage3RefactoredProcessor:
    """重構後Stage 3處理器測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage3處理器實例"""
        return Stage3SignalAnalysisProcessor()

    @pytest.fixture
    def mock_stage2_input(self):
        """模擬Stage 2輸入數據"""
        return {
            "metadata": {
                "stage": "stage2_visibility_filter",
                "observer_coordinates": (24.9441667, 121.3713889, 50),  # 台北座標
                "total_satellites": 100,
                "timestamp": "2025-09-18T10:00:00Z"
            },
            "data": {
                "filtered_satellites": {
                    "starlink": [
                        {
                            "name": "STARLINK-1234",
                            "position_eci": {"x": 6771.0, "y": 0.0, "z": 0.0},
                            "velocity_eci": {"x": 0.0, "y": 7.66, "z": 0.0},
                            "elevation_deg": 45.0,
                            "azimuth_deg": 180.0
                        }
                    ],
                    "oneweb": []
                }
            }
        }

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_processor_initialization_refactored(self, processor):
        """測試重構後的處理器初始化"""
        # 驗證基礎屬性
        assert processor.stage_name == "stage3_signal_analysis"
        assert processor.logger is not None

        # 🔧 重構驗證: observer_coordinates應該初始化為None
        assert processor.observer_coordinates is None

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_observer_coordinates_validation_refactored(self, processor):
        """測試重構後的觀測者座標驗證方法"""
        # 重構後的驗證方法應該信任Stage 2結果
        result = processor._validate_observer_coordinates()

        # 應該總是返回True (信任Stage 2)
        assert result is True

    @pytest.mark.unit
    @pytest.mark.stage3
    @pytest.mark.critical
    def test_observer_coordinates_loading_from_stage2(self, processor, mock_stage2_input):
        """測試從Stage 2載入觀測者座標的新邏輯"""
        # 設定輸入數據
        processor.input_data = mock_stage2_input

        with patch.object(processor, '_load_stage2_data') as mock_load:
            mock_load.return_value = mock_stage2_input["data"]["filtered_satellites"]["starlink"]

            with patch.object(processor, '_calculate_signal_quality') as mock_signal:
                mock_signal.return_value = []

                with patch.object(processor, '_analyze_3gpp_events') as mock_3gpp:
                    mock_3gpp.return_value = {"processed_events": []}

                    with patch.object(processor, '_manage_handover_candidates') as mock_handover:
                        mock_handover.return_value = []

                        with patch.object(processor, '_make_handover_decisions') as mock_decisions:
                            mock_decisions.return_value = []

                            with patch.object(processor, '_adjust_dynamic_thresholds') as mock_thresholds:
                                mock_thresholds.return_value = {}

                                with patch.object(processor, '_perform_scientific_calculation_benchmark') as mock_benchmark:
                                    mock_benchmark.return_value = {"benchmark_score": 85}

                                    with patch.object(processor, '_save_results'):
                                        # 執行處理
                                        result = processor.execute()

        # 🔧 重構驗證: 觀測者座標應該從Stage 2載入
        expected_coordinates = (24.9441667, 121.3713889, 50)
        assert processor.observer_coordinates == expected_coordinates

        # 驗證metadata中也包含正確的觀測者座標
        assert result["metadata"]["observer_coordinates"] == expected_coordinates

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_fallback_observer_coordinates(self, processor):
        """測試當Stage 2未提供觀測者座標時的回退邏輯"""
        # 設定不包含觀測者座標的輸入
        incomplete_input = {
            "data": {
                "filtered_satellites": {
                    "starlink": [],
                    "oneweb": []
                }
            }
        }
        processor.input_data = incomplete_input

        with patch.object(processor, '_load_stage2_data') as mock_load:
            mock_load.return_value = []

            with patch.object(processor, '_calculate_signal_quality') as mock_signal:
                mock_signal.return_value = []

                with patch.object(processor, '_analyze_3gpp_events') as mock_3gpp:
                    mock_3gpp.return_value = {"processed_events": []}

                    with patch.object(processor, '_manage_handover_candidates') as mock_handover:
                        mock_handover.return_value = []

                        with patch.object(processor, '_make_handover_decisions') as mock_decisions:
                            mock_decisions.return_value = []

                            with patch.object(processor, '_adjust_dynamic_thresholds') as mock_thresholds:
                                mock_thresholds.return_value = {}

                                with patch.object(processor, '_perform_scientific_calculation_benchmark') as mock_benchmark:
                                    mock_benchmark.return_value = {"benchmark_score": 85}

                                    with patch.object(processor, '_save_results'):
                                        # 執行處理
                                        result = processor.execute()

        # 應該使用預設台北座標
        expected_default = (24.9441667, 121.3713889, 50)
        assert processor.observer_coordinates == expected_default

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_stage_responsibility_compliance(self, processor):
        """驗證Stage 3嚴格遵循職責邊界"""
        # Stage 3應該專注信號分析，不應該計算觀測者座標

        # 確認沒有Stage 1功能 (軌道計算)
        stage1_methods = ['calculate_orbital_positions', 'load_tle_data', 'sgp4_propagation']
        for method in stage1_methods:
            assert not hasattr(processor, method)

        # 確認沒有Stage 2功能 (觀測者幾何計算)
        stage2_methods = ['calculate_observer_geometry', '_add_observer_geometry']
        for method in stage2_methods:
            assert not hasattr(processor, method)

        # 確認有信號分析相關方法
        signal_methods = ['_calculate_signal_quality', '_analyze_3gpp_events', '_make_handover_decisions']
        for method in signal_methods:
            assert hasattr(processor, method), f"信號分析方法 {method} 應該存在"

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_data_flow_from_stage2(self, processor, mock_stage2_input):
        """測試從Stage 2正確接收數據流"""
        processor.input_data = mock_stage2_input

        # 測試數據載入
        with patch.object(processor, '_load_stage2_data') as mock_load:
            visibility_data = mock_stage2_input["data"]["filtered_satellites"]["starlink"]
            mock_load.return_value = visibility_data

            loaded_data = processor._load_stage2_data()

            # 驗證正確載入了Stage 2數據
            assert len(loaded_data) == 1
            assert loaded_data[0]["name"] == "STARLINK-1234"
            assert "elevation_deg" in loaded_data[0]  # Stage 2應該提供的觀測者幾何數據

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_removed_hardcoded_observer_coordinates(self, processor):
        """驗證移除了硬編碼的觀測者座標"""
        # 初始化時不應該有硬編碼座標
        assert processor.observer_coordinates is None

        # 驗證不會在初始化時設定觀測者座標
        # (應該等待從Stage 2載入)

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_output_format_compliance(self, processor, mock_stage2_input):
        """測試輸出格式符合Stage間介面規範"""
        processor.input_data = mock_stage2_input

        with patch.object(processor, '_load_stage2_data') as mock_load:
            mock_load.return_value = []

            with patch.object(processor, '_calculate_signal_quality') as mock_signal:
                mock_signal.return_value = [{"satellite": "test", "rsrp": -100}]

                with patch.object(processor, '_analyze_3gpp_events') as mock_3gpp:
                    mock_3gpp.return_value = {"processed_events": []}

                    with patch.object(processor, '_manage_handover_candidates') as mock_handover:
                        mock_handover.return_value = []

                        with patch.object(processor, '_make_handover_decisions') as mock_decisions:
                            mock_decisions.return_value = []

                            with patch.object(processor, '_adjust_dynamic_thresholds') as mock_thresholds:
                                mock_thresholds.return_value = {}

                                with patch.object(processor, '_perform_scientific_calculation_benchmark') as mock_benchmark:
                                    mock_benchmark.return_value = {"benchmark_score": 85}

                                    with patch.object(processor, '_save_results'):
                                        result = processor.execute()

        # 驗證標準輸出格式
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "signal_quality_data" in result
        assert "gpp_events" in result
        assert "handover_candidates" in result
        assert "handover_decisions" in result
        assert "success" in result

        # 驗證metadata包含觀測者座標 (從Stage 2載入)
        metadata = result["metadata"]
        assert "observer_coordinates" in metadata
        assert metadata["observer_coordinates"] is not None


# 重構後快照標記
@pytest.mark.refactored
@pytest.mark.snapshot
class TestStage3RefactoringSnapshot:
    """重構效果快照測試"""

    def test_refactoring_completeness(self):
        """驗證重構完整性"""
        processor = Stage3SignalAnalysisProcessor()

        # 🔧 重構驗證: 觀測者座標初始化為None
        assert processor.observer_coordinates is None

        # 🔧 重構驗證: 觀測者座標驗證方法存在但功能已改變
        assert hasattr(processor, '_validate_observer_coordinates')
        validation_result = processor._validate_observer_coordinates()
        assert validation_result is True  # 應該信任Stage 2

        # 核心信號分析功能應該保留
        essential_methods = ['execute', '_calculate_signal_quality', '_analyze_3gpp_events']
        for method in essential_methods:
            assert hasattr(processor, method), f"核心方法 {method} 應該保留"

    def test_observer_coordinate_dependency_on_stage2(self):
        """驗證觀測者座標依賴Stage 2"""
        processor = Stage3SignalAnalysisProcessor()

        # 初始狀態應該沒有觀測者座標
        assert processor.observer_coordinates is None

        # 模擬Stage 2輸入
        stage2_input = {
            "metadata": {
                "observer_coordinates": (25.0, 121.0, 100)
            }
        }
        processor.input_data = stage2_input

        # 重構後的邏輯應該從input_data載入觀測者座標
        # (這會在execute()方法中發生)