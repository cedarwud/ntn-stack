"""
Stage1 TLE軌道計算處理器測試套件

測試重點：
1. 🚨 TLE epoch時間基準修復驗證
2. 驗證快照更新邏輯測試
3. TDD測試邏輯驗證
4. Stage1處理流程完整性測試
"""

import pytest
import time
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

# 系統導入
import sys
sys.path.append('/satellite-processing/src')

from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor
from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
from shared.data_models import ConstellationType
from tests.fixtures.tle_data_loader import load_test_tle_data, get_tle_epoch_time


class TestStage1TLEOrbitalCalculation:
    """
    Stage1 TLE軌道計算處理器測試套件

    🚨 核心測試目標：確保修復TLE epoch時間基準問題
    """

    @pytest.fixture
    def stage1_processor(self):
        """Stage1處理器 fixture"""
        return Stage1TLEProcessor()

    @pytest.fixture
    def real_starlink_tle_batch(self):
        """真實Starlink TLE數據批次"""
        return load_test_tle_data(constellation='starlink', count=3)

    @pytest.fixture
    def real_oneweb_tle_batch(self):
        """真實OneWeb TLE數據批次"""
        return load_test_tle_data(constellation='oneweb', count=2)

    # =========================================================================
    # 🚨 TLE Epoch時間基準修復驗證測試 - 核心重點！
    # =========================================================================

    @pytest.mark.stage1
    @pytest.mark.critical
    def test_tle_epoch_time_base_fix_verification(self, stage1_processor, real_starlink_tle_batch):
        """
        🚨 核心測試：驗證TLE epoch時間基準修復

        目標：確保Stage1使用TLE epoch時間而非當前時間作為計算基準
        """
        # Given: 真實TLE數據
        tle_data = real_starlink_tle_batch[0]
        tle_epoch_time = get_tle_epoch_time(tle_data)
        current_time = datetime.now(timezone.utc)

        # 確認測試環境有時間差（模擬真實情況）
        time_diff_days = abs((current_time - tle_epoch_time).days)
        assert time_diff_days >= 1, f"測試需要時間差，當前差異：{time_diff_days}天"

        # When: 執行Stage1處理（應使用TLE epoch時間）
        with patch.object(stage1_processor, '_load_tle_data', return_value=real_starlink_tle_batch):
            results = stage1_processor.execute()

        # Then: 驗證使用了正確的時間基準
        assert results is not None, "Stage1處理結果不能為空"
        assert 'satellites' in results, "結果必須包含satellites數據"

        # 檢查第一顆衛星的計算元數據
        first_satellite = results['satellites'][0]
        calculation_metadata = first_satellite.get('calculation_metadata', {})

        # 🚨 核心驗證：確認使用TLE epoch時間作為計算基準
        assert calculation_metadata.get('calculation_base') == 'tle_epoch_time', \
            f"🚨 時間基準錯誤！應該使用'tle_epoch_time'，實際使用：{calculation_metadata.get('calculation_base')}"

        # 驗證SGP4引擎設置
        assert calculation_metadata.get('algorithm_used') == 'SGP4', "必須使用SGP4算法"
        assert calculation_metadata.get('real_sgp4') == True, "必須使用真實SGP4實現"

        print(f"✅ TLE epoch時間基準修復驗證通過")
        print(f"   時間差：{time_diff_days}天")
        print(f"   計算基準：{calculation_metadata.get('calculation_base')}")

    @pytest.mark.stage1
    @pytest.mark.critical
    def test_stage1_tle_epoch_compliance_validation(self, stage1_processor, real_starlink_tle_batch):
        """
        測試Stage1的TLE epoch合規性驗證邏輯
        """
        # Given: 真實TLE數據
        tle_batch = real_starlink_tle_batch

        # Mock the validation methods to capture their calls
        validation_calls = []

        original_check_tle_epoch = stage1_processor._check_tle_epoch_compliance
        def mock_tle_epoch_check(*args, **kwargs):
            validation_calls.append('tle_epoch_compliance')
            return original_check_tle_epoch(*args, **kwargs)

        original_check_sgp4_precision = stage1_processor._check_sgp4_calculation_precision
        def mock_sgp4_precision_check(*args, **kwargs):
            validation_calls.append('sgp4_precision')
            return original_sgp4_precision_check(*args, **kwargs)

        # When: 執行Stage1處理
        with patch.object(stage1_processor, '_load_tle_data', return_value=tle_batch), \
             patch.object(stage1_processor, '_check_tle_epoch_compliance', side_effect=mock_tle_epoch_check), \
             patch.object(stage1_processor, '_check_sgp4_calculation_precision', side_effect=mock_sgp4_precision_check):

            results = stage1_processor.execute()

        # Then: 驗證調用了正確的驗證方法
        assert 'tle_epoch_compliance' in validation_calls, "必須調用TLE epoch合規性檢查"
        assert 'sgp4_precision' in validation_calls, "必須調用SGP4精度檢查"

        # 驗證結果包含驗證信息
        validation_results = results.get('validation_results', {})
        assert validation_results.get('tle_epoch_compliance_rate') == 1.0, "TLE epoch合規率必須100%"
        assert validation_results.get('sgp4_calculation_success_rate') == 1.0, "SGP4計算成功率必須100%"

    # =========================================================================
    # 驗證快照更新邏輯測試
    # =========================================================================

    @pytest.mark.stage1
    @pytest.mark.validation
    def test_verification_snapshot_update_logic(self, stage1_processor, real_starlink_tle_batch):
        """
        測試驗證快照更新邏輯
        """
        # Given: 真實TLE數據和預期的快照格式
        tle_batch = real_starlink_tle_batch

        # When: 執行Stage1處理
        with patch.object(stage1_processor, '_load_tle_data', return_value=tle_batch):
            results = stage1_processor.execute()

        # Then: 驗證快照信息包含必要字段
        validation_snapshot = results.get('validation_snapshot', {})

        # 核心快照字段驗證
        required_snapshot_fields = [
            'timestamp',
            'tle_epoch_compliance_rate',
            'sgp4_calculation_success_rate',
            'total_satellites_processed',
            'calculation_base_verification',
            'time_base_metadata'
        ]

        for field in required_snapshot_fields:
            assert field in validation_snapshot, f"驗證快照缺少必要字段：{field}"

        # 驗證快照數據質量
        assert validation_snapshot['tle_epoch_compliance_rate'] == 1.0, "TLE epoch合規率必須100%"
        assert validation_snapshot['calculation_base_verification'] == 'tle_epoch_time', "必須驗證使用TLE epoch時間"
        assert validation_snapshot['total_satellites_processed'] > 0, "必須處理至少一顆衛星"

        print(f"✅ 驗證快照更新邏輯測試通過")
        print(f"   處理衛星數量：{validation_snapshot['total_satellites_processed']}")
        print(f"   TLE epoch合規率：{validation_snapshot['tle_epoch_compliance_rate']}")

    @pytest.mark.stage1
    @pytest.mark.validation
    def test_tdd_test_logic_verification(self, stage1_processor, real_starlink_tle_batch):
        """
        測試TDD測試邏輯驗證
        """
        # Given: TDD測試場景 - 確保時間基準修復有效
        tle_batch = real_starlink_tle_batch

        # 建立測試斷言函數
        def assert_tle_epoch_usage(result):
            """TDD斷言：確保使用TLE epoch時間"""
            satellites = result.get('satellites', [])
            assert len(satellites) > 0, "TDD: 必須有衛星處理結果"

            for satellite in satellites:
                metadata = satellite.get('calculation_metadata', {})
                assert metadata.get('calculation_base') == 'tle_epoch_time', \
                    "TDD: 每顆衛星都必須使用TLE epoch時間基準"
                assert metadata.get('real_sgp4') == True, \
                    "TDD: 必須使用真實SGP4算法"

        def assert_no_current_time_usage(result):
            """TDD斷言：確保沒有使用當前時間"""
            satellites = result.get('satellites', [])
            current_time = datetime.now(timezone.utc)

            for satellite in satellites:
                calculation_time = satellite.get('calculation_metadata', {}).get('calculation_time')
                if calculation_time:
                    # 計算時間不應該接近當前時間
                    time_diff = abs((current_time - calculation_time).total_seconds())
                    assert time_diff > 3600, \
                        "TDD: 計算時間不應該接近當前時間（避免使用current_time錯誤）"

        # When: 執行Stage1處理
        with patch.object(stage1_processor, '_load_tle_data', return_value=tle_batch):
            results = stage1_processor.execute()

        # Then: 執行TDD測試斷言
        assert_tle_epoch_usage(results)
        assert_no_current_time_usage(results)

        # 驗證TDD測試邏輯本身的正確性
        tdd_validation = results.get('tdd_validation', {})
        assert tdd_validation.get('time_base_verification') == 'passed', "TDD時間基準驗證必須通過"
        assert tdd_validation.get('sgp4_algorithm_verification') == 'passed', "TDD SGP4算法驗證必須通過"

        print(f"✅ TDD測試邏輯驗證通過")

    # =========================================================================
    # Stage1處理流程完整性測試
    # =========================================================================

    @pytest.mark.stage1
    @pytest.mark.integration
    def test_stage1_complete_processing_workflow(self, stage1_processor, real_starlink_tle_batch, real_oneweb_tle_batch):
        """
        測試Stage1完整處理流程
        """
        # Given: 混合星座TLE數據
        mixed_tle_batch = real_starlink_tle_batch + real_oneweb_tle_batch

        # When: 執行完整的Stage1處理流程
        start_time = time.perf_counter()

        with patch.object(stage1_processor, '_load_tle_data', return_value=mixed_tle_batch):
            results = stage1_processor.execute()

        processing_time = time.perf_counter() - start_time

        # Then: 驗證處理結果完整性
        assert results is not None, "Stage1處理結果不能為空"

        # 驗證輸出結構
        required_output_fields = [
            'metadata',
            'satellites',
            'validation_results',
            'validation_snapshot',
            'tdd_validation',
            'processing_statistics'
        ]

        for field in required_output_fields:
            assert field in results, f"Stage1輸出缺少必要字段：{field}"

        # 驗證衛星處理結果
        satellites = results['satellites']
        assert len(satellites) == len(mixed_tle_batch), "處理的衛星數量必須匹配輸入"

        # 驗證每顆衛星的計算結果
        for satellite in satellites:
            assert 'satellite_id' in satellite, "每顆衛星必須有ID"
            assert 'orbital_positions' in satellite, "每顆衛星必須有軌道位置"
            assert 'calculation_metadata' in satellite, "每顆衛星必須有計算元數據"

            # 驗證軌道位置數據
            orbital_positions = satellite['orbital_positions']
            assert len(orbital_positions) > 0, "每顆衛星必須有軌道位置點"

            # 驗證時間基準
            metadata = satellite['calculation_metadata']
            assert metadata.get('calculation_base') == 'tle_epoch_time', "必須使用TLE epoch時間基準"

        # 性能驗證
        processing_stats = results['processing_statistics']
        assert processing_stats['total_processing_time'] < 60.0, "Stage1處理時間不應超過60秒"
        assert processing_stats['satellites_per_second'] > 0.1, "處理效率不應低於0.1衛星/秒"

        print(f"✅ Stage1完整處理流程測試通過")
        print(f"   處理衛星數量：{len(satellites)}")
        print(f"   處理時間：{processing_time:.3f}秒")
        print(f"   處理效率：{len(satellites)/processing_time:.2f}衛星/秒")

    @pytest.mark.stage1
    @pytest.mark.performance
    def test_stage1_performance_baseline(self, stage1_processor, real_starlink_tle_batch):
        """
        測試Stage1性能基線
        """
        # Given: 標準測試數據集
        tle_batch = real_starlink_tle_batch

        # When: 測量處理性能
        start_time = time.perf_counter()

        with patch.object(stage1_processor, '_load_tle_data', return_value=tle_batch):
            results = stage1_processor.execute()

        total_time = time.perf_counter() - start_time

        # Then: 驗證性能基線
        satellites_count = len(results['satellites'])
        avg_time_per_satellite = total_time / satellites_count

        # 性能基線要求
        assert avg_time_per_satellite < 5.0, f"每顆衛星處理時間過長：{avg_time_per_satellite:.3f}秒"
        assert total_time < 30.0, f"總處理時間過長：{total_time:.3f}秒"

        # 記錄性能基線
        performance_baseline = {
            'satellites_processed': satellites_count,
            'total_time_seconds': total_time,
            'avg_time_per_satellite': avg_time_per_satellite,
            'satellites_per_second': satellites_count / total_time,
            'test_timestamp': datetime.now(timezone.utc).isoformat()
        }

        print(f"✅ Stage1性能基線測試通過")
        print(f"   性能基線：{performance_baseline}")

    # =========================================================================
    # 錯誤場景和邊界條件測試
    # =========================================================================

    @pytest.mark.stage1
    @pytest.mark.error_handling
    def test_stage1_error_handling_scenarios(self, stage1_processor):
        """
        測試Stage1錯誤處理場景
        """
        # Scenario 1: 空TLE數據
        with patch.object(stage1_processor, '_load_tle_data', return_value=[]):
            results = stage1_processor.execute()
            assert results is not None, "空數據情況下應該返回有效結果"
            assert len(results.get('satellites', [])) == 0, "空數據應該返回空衛星列表"
            assert 'error_handling' in results, "應該包含錯誤處理信息"

        # Scenario 2: 無效TLE數據
        invalid_tle = {
            'line1': '',
            'line2': '',
            'satellite_name': 'INVALID',
            'epoch_datetime': datetime.now(timezone.utc)
        }

        with patch.object(stage1_processor, '_load_tle_data', return_value=[invalid_tle]):
            results = stage1_processor.execute()
            assert results is not None, "無效數據情況下應該返回有效結果"

            # 應該有錯誤記錄
            error_stats = results.get('processing_statistics', {}).get('error_statistics', {})
            assert error_stats.get('invalid_tle_count', 0) > 0, "應該記錄無效TLE數據"

        print(f"✅ Stage1錯誤處理場景測試通過")

    @pytest.mark.stage1
    @pytest.mark.regression
    def test_stage1_regression_zero_visible_satellites_fix(self, stage1_processor, real_starlink_tle_batch):
        """
        🚨 回歸測試：確保修復了0顆可見衛星的問題

        這個測試確保我們修復的TLE epoch時間問題能夠產生有效的衛星位置
        """
        # Given: 已知會導致0顆可見衛星的TLE數據場景
        tle_batch = real_starlink_tle_batch

        # When: 執行修復後的Stage1處理
        with patch.object(stage1_processor, '_load_tle_data', return_value=tle_batch):
            results = stage1_processor.execute()

        # Then: 確保不再出現0顆可見衛星問題
        satellites = results.get('satellites', [])
        assert len(satellites) > 0, "🚨 回歸失敗：仍然出現0顆衛星問題！"

        # 驗證衛星位置合理性
        valid_positions = 0
        for satellite in satellites:
            orbital_positions = satellite.get('orbital_positions', [])
            if len(orbital_positions) > 0:
                # 檢查第一個位置點
                pos = orbital_positions[0]
                if pos.get('altitude_km', 0) > 200:  # LEO衛星高度基線
                    valid_positions += 1

        assert valid_positions > 0, "🚨 回歸失敗：所有衛星位置都無效！"

        # 記錄回歸測試結果
        regression_results = {
            'total_satellites': len(satellites),
            'valid_positions': valid_positions,
            'success_rate': valid_positions / len(satellites),
            'fix_verified': True
        }

        print(f"✅ 0顆可見衛星問題修復驗證通過")
        print(f"   回歸測試結果：{regression_results}")

        # 確保成功率達到預期
        assert regression_results['success_rate'] > 0.8, \
            f"成功率過低：{regression_results['success_rate']:.2%}，應該 > 80%"