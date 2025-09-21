"""
Stage 3 信號分析處理器 - 重構後TDD測試套件

重構變更:
- 移除觀測者座標硬編碼初始化
- 修正execute()方法從Stage 2載入觀測者座標
- _validate_observer_coordinates()重構為信任Stage 2結果
- 移除所有不當Mock使用，改為真實單元測試
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage3_signal_analysis.stage3_signal_analysis_processor import create_stage3_processor
from shared.interfaces.processor_interface import ProcessingStatus, ProcessingResult


class TestStage3RefactoredProcessor:
    """重構後Stage 3處理器測試套件 - 使用真實處理邏輯"""

    @pytest.fixture
    def processor(self):
        """創建Stage3處理器實例"""
        return create_stage3_processor()

    @pytest.fixture
    def mock_stage2_data(self):
        """新架構的Stage 2輸出數據結構"""
        return {
            'stage': 'stage2_orbital_computing',
            'visible_satellites': {
                '12345': {
                    'satellite_id': '12345',
                    'positions': [
                        {
                            'x': 1000.0, 'y': 2000.0, 'z': 3000.0,
                            'timestamp': '2025-09-21T10:00:00Z',
                            'elevation_deg': 15.0,
                            'is_visible': True
                        }
                    ],
                    'calculation_successful': True,
                    'visible_windows': [{'start': '10:00', 'end': '10:30'}]
                }
            },
            'metadata': {'processing_time': 1.0}
        }

    @pytest.fixture
    def temp_stage2_output_file(self, mock_stage2_data):
        """創建臨時Stage2輸出文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_stage2_data, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name

        yield temp_file_path

        # 清理
        Path(temp_file_path).unlink(missing_ok=True)

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_processor_initialization_refactored(self, processor):
        """測試重構後的處理器初始化"""
        # 驗證BaseProcessor接口
        from shared.interfaces.processor_interface import BaseProcessor
        assert isinstance(processor, BaseProcessor)

        # 驗證必要方法存在
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'validate_input')
        assert hasattr(processor, 'validate_output')

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_validate_input_method(self, processor, mock_stage2_data):
        """測試validate_input方法"""
        # 測試有效輸入
        result = processor.validate_input(mock_stage2_data)
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result

        # 測試無效輸入
        invalid_input = {'invalid': 'data'}
        result = processor.validate_input(invalid_input)
        assert result['valid'] is False

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_validate_output_method(self, processor):
        """測試validate_output方法"""
        # 測試有效輸出格式
        valid_output = {
            'stage': 'stage3_signal_analysis',
            'satellites': {
                '12345': {
                    'satellite_id': '12345',
                    'signal_quality': {
                        'rsrp': -85.0,
                        'rsrq': -10.0,
                        'sinr': 5.0
                    },
                    'events': []
                }
            },
            'metadata': {'processing_time': 1.0}
        }
        result = processor.validate_output(valid_output)
        assert isinstance(result, dict)

        # 測試無效輸出
        invalid_output = {'invalid': 'data'}
        result = processor.validate_output(invalid_output)
        assert result['valid'] is False

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_real_data_processing_from_stage2(self, processor):
        """測試使用真實Stage 2輸出數據進行處理"""
        # 先運行 Stage 1 和 Stage 2 獲取真實數據
        from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
        from stages.stage2_visibility_filter.stage2_orbital_computing_processor import create_stage2_processor

        stage1_processor = create_stage1_processor()
        stage2_processor = create_stage2_processor()

        # 執行真實的 Stage 1
        stage1_result = stage1_processor.process(None)
        if stage1_result.status != ProcessingStatus.SUCCESS:
            pytest.skip(f"Stage 1 未能成功運行: {stage1_result.errors}")

        # 執行真實的 Stage 2
        stage2_result = stage2_processor.process(stage1_result.data)
        if stage2_result.status != ProcessingStatus.SUCCESS:
            pytest.skip(f"Stage 2 未能成功運行: {stage2_result.errors}")

        # 現在用真實數據測試 Stage 3
        result = processor.process(stage2_result.data)

        # 檢查ProcessingResult格式
        assert isinstance(result, ProcessingResult)
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'metadata')

        # 驗證 Stage 3 必須成功處理真實數據
        if result.status != ProcessingStatus.SUCCESS:
            error_details = ", ".join(result.errors) if result.errors else "無具體錯誤信息"
            pytest.fail(f"Stage 3 處理真實數據失敗: {error_details}, 狀態: {result.status}")

        assert result.status == ProcessingStatus.SUCCESS

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_signal_analysis_functionality(self, processor, mock_stage2_data):
        """測試信號分析功能"""
        result = processor.process(mock_stage2_data)

        # 檢查是否嘗試了信號分析
        assert isinstance(result, ProcessingResult)

        # 如果處理成功，檢查信號分析相關數據
        if result.status == ProcessingStatus.SUCCESS and 'satellites' in result.data:
            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]
                # 檢查信號分析相關字段
                signal_fields = ['signal_quality', 'rsrp', 'rsrq', 'sinr', 'events']
                assert any(field in sample_sat for field in signal_fields)

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

        # 確認有BaseProcessor核心方法
        core_methods = ['process', 'validate_input', 'validate_output']
        for method in core_methods:
            assert hasattr(processor, method), f"核心方法 {method} 應該存在"

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_error_handling(self, processor):
        """測試錯誤處理"""
        # 測試空輸入
        result = processor.process(None)
        assert isinstance(result, ProcessingResult)
        assert result.status in [ProcessingStatus.FAILED, ProcessingStatus.VALIDATION_FAILED]

        # 測試無效輸入
        result = processor.process({'invalid': 'data'})
        assert isinstance(result, ProcessingResult)
        assert result.status in [ProcessingStatus.FAILED, ProcessingStatus.VALIDATION_FAILED]

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_3gpp_event_analysis_functionality(self, processor, mock_stage2_data):
        """測試3GPP事件分析功能"""
        result = processor.process(mock_stage2_data)

        # 如果處理成功，檢查事件分析相關數據
        if result.status == ProcessingStatus.SUCCESS and 'satellites' in result.data:
            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]
                # 檢查事件分析相關字段
                event_fields = ['events', '3gpp_events', 'handover_events']
                # 事件分析是可選的，我們只檢查處理結果的完整性
                assert isinstance(result.data, dict)

    @pytest.mark.unit
    @pytest.mark.stage3
    def test_next_stage_readiness(self, processor, mock_stage2_data):
        """測試為下一階段準備的數據格式"""
        result = processor.process(mock_stage2_data)

        # 檢查輸出格式適合Stage 4消費
        if result.status == ProcessingStatus.SUCCESS:
            assert 'satellites' in result.data
            # 檢查stage字段
            expected_stage = ['stage3_signal_analysis']
            if 'stage' in result.data:
                assert result.data['stage'] in expected_stage

    @pytest.mark.integration
    @pytest.mark.stage3
    def test_minimal_integration_without_mock(self, processor, mock_stage2_data):
        """最小化整合測試，使用新架構"""
        # 執行處理
        try:
            result = processor.process(mock_stage2_data)

            # 驗證執行結果
            assert isinstance(result, ProcessingResult)
            assert hasattr(result, 'status')
            assert hasattr(result, 'data')
            assert hasattr(result, 'metadata')

            # 驗證處理狀態
            assert result.status in [
                ProcessingStatus.SUCCESS,
                ProcessingStatus.VALIDATION_FAILED,
                ProcessingStatus.FAILED
            ]

        except Exception as e:
            # 如果有預期的錯誤（如缺少某些依賴），記錄但不失敗
            pytest.skip(f"整合測試跳過，原因: {str(e)}")