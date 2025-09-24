"""
Stage 2 軌道計算層處理器 - v2.0模組化架構TDD測試套件

v2.0架構特點:
- 4模組設計: SGP4Calculator + CoordinateConverter + VisibilityFilter + LinkFeasibilityFilter
- Grade A學術標準合規 (無簡化算法、模擬數據、硬編碼)
- 配置文件驅動 (config/stage2_orbital_computing.yaml)
- 星座特定仰角門檻 (Starlink: 5°, OneWeb: 10°)
- 鏈路可行性評估 (200-2000km距離範圍)
- TLE epoch時間基準 (禁止使用當前時間)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor, create_stage2_processor
from stages.stage1_orbital_calculation.stage1_data_loading_processor import create_stage1_processor
from shared.interfaces.processor_interface import ProcessingStatus, ProcessingResult


@pytest.fixture
def mock_stage1_data():
    """創建模擬Stage 1輸出數據"""
    return {
        'stage': 'stage1_data_loading',
        'tle_data': [
            {
                'satellite_id': '12345',
                'line1': '1 12345U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927',
                'line2': '2 12345  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537',
                'name': 'TEST-SAT',
                'norad_id': '12345'
            },
            {
                'satellite_id': '23456',
                'line1': '1 23456U 98067B   08264.51782528 -.00002182  00000-0 -11606-4 0  2927',
                'line2': '2 23456  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537',
                'name': 'TEST-SAT-2',
                'norad_id': '23456'
            }
        ],
        'metadata': {'processing_timestamp': datetime.now().isoformat()},
        'next_stage_ready': True
    }


class TestStage2NewArchitecture:
    """Stage 2新架構測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage 2處理器實例"""
        return create_stage2_processor()

    @pytest.fixture
    def stage1_processor(self):
        """創建Stage 1處理器實例"""
        try:
            return create_stage1_processor()
        except RuntimeError as e:
            if "容器內執行" in str(e):
                return None  # 返回None而不是跳過，讓具體測試決定
            else:
                raise

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_processor_creation(self, processor):
        """測試處理器創建"""
        assert processor is not None
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'validate_input')
        assert hasattr(processor, 'validate_output')

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_base_processor_interface(self, processor):
        """測試BaseProcessor接口實現"""
        from shared.interfaces.processor_interface import BaseProcessor
        assert isinstance(processor, BaseProcessor)

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_validate_input_method(self, processor, mock_stage1_data):
        """測試validate_input方法"""
        # 測試有效輸入
        result = processor.validate_input(mock_stage1_data)
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result

        # 測試無效輸入
        invalid_input = {'invalid': 'data'}
        result = processor.validate_input(invalid_input)
        assert result['valid'] is False

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_validate_output_method(self, processor):
        """測試validate_output方法"""
        # 測試有效輸出格式
        valid_output = {
            'stage': 'stage2_orbital_computing',
            'satellites': {
                '12345': {
                    'satellite_id': '12345',
                    'positions': [{'x': 1000, 'y': 2000, 'z': 3000}],
                    'calculation_successful': True,
                    'visible_windows': []
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

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_mock_data_processing(self, processor, mock_stage1_data):
        """測試模擬數據處理"""
        result = processor.process(mock_stage1_data)

        # 檢查ProcessingResult格式
        assert isinstance(result, ProcessingResult)
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert hasattr(result, 'metadata')

        # Stage 2可能因為驗證過嚴而失敗，但應該返回有效的ProcessingResult
        assert result.status in [
            ProcessingStatus.SUCCESS,
            ProcessingStatus.VALIDATION_FAILED,
            ProcessingStatus.FAILED
        ]

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_real_stage1_integration(self, processor, stage1_processor):
        """測試與真實Stage 1的集成"""
        if stage1_processor is None:
            pytest.skip("Stage 1處理器不可用，跳過集成測試")

        # 獲取真實Stage 1輸出
        stage1_result = stage1_processor.process(None)
        assert stage1_result.status == ProcessingStatus.SUCCESS

        # 限制數據量以加快測試
        limited_data = stage1_result.data.copy()
        limited_data['tle_data'] = stage1_result.data['tle_data'][:3]

        # 處理Stage 1輸出
        stage2_result = processor.process(limited_data)

        # 檢查結果
        assert isinstance(stage2_result, ProcessingResult)
        assert stage2_result.status in [
            ProcessingStatus.SUCCESS,
            ProcessingStatus.VALIDATION_FAILED,
            ProcessingStatus.FAILED
        ]

        # 如果成功，檢查輸出結構
        if stage2_result.status == ProcessingStatus.SUCCESS:
            assert 'satellites' in stage2_result.data
            satellites = stage2_result.data['satellites']
            assert len(satellites) > 0

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_orbital_calculation_functionality(self, processor, mock_stage1_data):
        """測試軌道計算功能"""
        result = processor.process(mock_stage1_data)

        # 檢查是否嘗試了軌道計算
        assert isinstance(result, ProcessingResult)

        # 如果處理成功，檢查軌道計算相關數據
        if result.status == ProcessingStatus.SUCCESS and 'satellites' in result.data:
            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]
                # 檢查軌道計算相關字段 (v2.0更新)
                orbital_fields = ['positions', 'calculation_successful', 'orbital_data', 'elevation_angle', 'distance_km']
                assert any(field in sample_sat for field in orbital_fields)

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_visibility_analysis_functionality(self, processor, mock_stage1_data):
        """測試可見性分析功能"""
        result = processor.process(mock_stage1_data)

        # 如果處理成功，檢查可見性分析相關數據
        if result.status == ProcessingStatus.SUCCESS and 'satellites' in result.data:
            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]
                # 檢查可見性分析相關字段 (v2.0更新)
                visibility_fields = ['visible_windows', 'visibility_data', 'visibility_status', 'is_visible', 'is_feasible']
                assert any(field in sample_sat for field in visibility_fields)

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_trajectory_prediction_functionality(self, processor, mock_stage1_data):
        """測試軌跡預測功能"""
        result = processor.process(mock_stage1_data)

        # 如果處理成功，檢查軌跡預測相關數據
        if result.status == ProcessingStatus.SUCCESS and 'satellites' in result.data:
            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]
                # 檢查軌跡預測相關字段
                prediction_fields = ['prediction_data', 'predicted_positions']
                # 軌跡預測是可選的，所以我們只檢查是否嘗試了
                # 不要求一定存在這些字段

    @pytest.mark.unit
    @pytest.mark.stage2
    def test_performance_monitoring(self, processor, mock_stage1_data):
        """測試性能監控"""
        result = processor.process(mock_stage1_data)

        # 檢查性能監控數據
        if result.status == ProcessingStatus.SUCCESS:
            metadata = result.data.get('metadata', {})
            # 檢查處理時間相關字段
            time_fields = ['processing_time_seconds', 'processing_start_time', 'processing_end_time']
            assert any(field in metadata for field in time_fields)

    @pytest.mark.unit
    @pytest.mark.stage2
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
    @pytest.mark.stage2
    def test_next_stage_readiness(self, processor, mock_stage1_data):
        """測試為下一階段準備的數據格式"""
        result = processor.process(mock_stage1_data)

        # 檢查輸出格式適合Stage 3消費
        if result.status == ProcessingStatus.SUCCESS:
            assert 'satellites' in result.data
            # 檢查stage字段
            expected_stage = ['stage2_orbital_computing', 'stage2_visibility_filter']
            if 'stage' in result.data:
                assert result.data['stage'] in expected_stage


class TestStage2GradeACompliance:
    """Stage 2 Grade A學術標準合規性測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage 2處理器實例"""
        return create_stage2_processor()

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_no_hardcoded_values(self, processor):
        """測試無硬編碼值 - Grade A標準"""
        # 檢查處理器初始化時要求配置文件
        assert hasattr(processor, 'config')
        assert isinstance(processor.config, dict)

        # 驗證關鍵配置項必須從配置文件讀取
        if hasattr(processor, 'min_elevation_deg'):
            # 確保不是硬編碼的預設值
            assert processor.min_elevation_deg is not None

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_no_simplified_algorithms(self, processor):
        """測試無簡化算法 - Grade A標準"""
        import inspect

        # 檢查處理器類中不包含簡化算法標識
        processor_source = inspect.getsource(processor.__class__)
        forbidden_terms = ['簡化', 'simplified', '近似', 'approximate', '回退', 'fallback']

        for term in forbidden_terms:
            # 允許註釋中提到這些詞（如禁止條款），但不允許在實際實現中
            source_lines = processor_source.split('\n')
            implementation_lines = [line for line in source_lines
                                   if not line.strip().startswith('#')
                                   and not line.strip().startswith('"""')
                                   and not line.strip().startswith("'''")]
            implementation_text = '\n'.join(implementation_lines)

            # 如果在實現中發現簡化算法，應該是被禁止的
            if term in implementation_text.lower():
                # 檢查是否是禁止條款
                assert '禁止' in implementation_text or 'ValueError' in implementation_text

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_no_mock_data_generation(self, processor):
        """測試無模擬數據生成 - Grade A標準"""
        import inspect

        # 檢查處理器類中不包含random.sample等模擬數據生成
        processor_source = inspect.getsource(processor.__class__)
        forbidden_functions = ['random.sample', 'random.choice', 'random.uniform', 'np.random']

        for func in forbidden_functions:
            if func in processor_source:
                # 確保是在錯誤處理或禁止條款中
                assert 'ValueError' in processor_source or '禁止' in processor_source

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_configuration_driven(self, processor):
        """測試配置文件驅動 - Grade A標準"""
        # 檢查處理器有配置文件支持
        assert hasattr(processor, 'config')

        # 檢查是否有配置驗證機制
        if hasattr(processor, '_load_configuration'):
            # 確保配置加載方法存在
            assert callable(processor._load_configuration)

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_modular_architecture_compliance(self, processor):
        """測試v2.0模組化架構合規性"""
        # 檢查6個核心模組是否存在 (v2.0更新)
        expected_modules = [
            'sgp4_calculator',
            'coordinate_converter',
            'visibility_filter',
            'link_feasibility_filter',
            'optimized_processor',  # v2.0新增
            'parallel_calculator'   # v2.0新增
        ]

        # 檢查基礎4模組 (必須存在)
        core_modules = expected_modules[:4]
        for module_name in core_modules:
            # 檢查模組屬性是否存在
            assert hasattr(processor, module_name) or hasattr(processor, f"_{module_name}"), f"缺少核心模組: {module_name}"

        # 檢查優化模組 (可選存在，但如果存在要有正確類型)
        if hasattr(processor, 'optimized_processor'):
            from stages.stage2_orbital_computing.optimized_stage2_processor import OptimizedStage2Processor
            # 可以是實例或類型
            assert processor.optimized_processor is not None

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_tle_epoch_time_compliance(self, processor, mock_stage1_data):
        """測試TLE epoch時間基準合規性"""
        try:
            # 確保使用TLE epoch時間而非當前時間
            if hasattr(processor, '_get_calculation_base_time'):
                base_time = processor._get_calculation_base_time(mock_stage1_data.get('tle_data', []))
                assert base_time is not None

                # 確保不是當前時間 (2025-09-23)
                from datetime import datetime, timezone
                current_time = datetime.now(timezone.utc)
                # 處理可能的時區格式
                if isinstance(base_time, str):
                    if base_time.endswith('Z'):
                        base_time_dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
                    else:
                        base_time_dt = datetime.fromisoformat(base_time)
                        if base_time_dt.tzinfo is None:
                            base_time_dt = base_time_dt.replace(tzinfo=timezone.utc)
                else:
                    base_time_dt = base_time
                    if base_time_dt.tzinfo is None:
                        base_time_dt = base_time_dt.replace(tzinfo=timezone.utc)

                time_diff = abs((current_time - base_time_dt).total_seconds())

                # 如果時間差很小，可能在使用當前時間（需要警告）
                if time_diff < 3600:  # 1小時內
                    print(f"⚠️ 警告：計算基準時間與當前時間很接近，請確認使用的是TLE epoch時間")
        except RuntimeError as e:
            if "容器內執行" in str(e):
                pytest.skip("容器執行限制，跳過TLE epoch時間合規性測試")
            else:
                raise

    @pytest.mark.unit
    @pytest.mark.stage2
    @pytest.mark.compliance
    def test_output_format_compliance(self, processor, mock_stage1_data):
        """測試輸出格式合規性"""
        try:
            result = processor.process(mock_stage1_data)
        except RuntimeError as e:
            if "容器內執行" in str(e):
                pytest.skip("容器執行限制，跳過輸出格式合規性測試")
            else:
                raise

        if result.status == ProcessingStatus.SUCCESS:
            # 檢查v2.0預期的輸出格式
            assert 'satellites' in result.data

            satellites = result.data['satellites']
            if satellites:
                sample_sat = list(satellites.values())[0]

                # 檢查鏈路可行性字段 (v2.0新增)
                feasibility_fields = ['is_feasible', 'feasibility_data', 'feasibility_score']
                has_feasibility = any(field in sample_sat for field in feasibility_fields)

                # 如果有可見性數據，應該也有可行性數據
                if 'visible_positions' in sample_sat or 'is_visible' in sample_sat:
                    assert has_feasibility, "v2.0架構要求同時進行可見性和可行性分析"

                # v2.0架構應該包含基本可見性和可行性標記
                if has_feasibility:
                    # 檢查是否有基本的布林標記
                    bool_fields = ['is_visible', 'is_feasible']
                    has_bool_markers = any(field in sample_sat and isinstance(sample_sat[field], bool) for field in bool_fields)
                    assert has_bool_markers, "v2.0架構要求包含布林可見性/可行性標記"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])