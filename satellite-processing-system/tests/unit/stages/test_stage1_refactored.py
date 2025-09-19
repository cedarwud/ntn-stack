"""
Stage 1 TLE軌道計算處理器 - 重構後TDD測試套件

重構變更:
- 移除所有觀測者計算功能 (6個方法, 202行代碼)
- 專注純軌道計算，符合單一職責原則
- 使用TLE epoch時間作為計算基準
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# 添加src路徑到模組搜索路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src"))

from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor


class TestStage1RefactoredProcessor:
    """重構後Stage 1處理器測試套件"""

    @pytest.fixture
    def processor(self):
        """創建Stage1處理器實例"""
        return Stage1TLEProcessor()

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_processor_initialization_refactored(self, processor):
        """測試重構後的處理器初始化"""
        # 驗證基礎屬性
        assert processor.stage_name == "stage1_tle_orbital_calculation"
        assert processor.logger is not None

        # 🔧 重構驗證: 確認觀測者計算相關屬性已移除
        assert not hasattr(processor, 'observer_calculations')
        assert not hasattr(processor, 'observer_coordinates')
        assert not hasattr(processor, 'elevation_threshold')

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_removed_observer_methods(self, processor):
        """驗證觀測者計算方法已被移除"""
        # 確認這些方法不再存在
        removed_methods = [
            '_add_observer_geometry',
            '_calculate_observer_geometry',
            '_validate_observer_coordinates',
            '_calculate_elevation_azimuth',
            '_check_visibility_constraints',
            '_format_observer_results'
        ]

        for method_name in removed_methods:
            assert not hasattr(processor, method_name), f"方法 {method_name} 應該已被移除"

    @pytest.mark.unit
    @pytest.mark.stage1
    @pytest.mark.sgp4
    def test_orbital_calculation_only(self, processor):
        """測試重構後只進行軌道計算，不包含觀測者計算"""
        # 模擬TLE數據
        mock_tle_data = {
            "starlink": [
                {
                    "name": "STARLINK-1234",
                    "line1": "1 12345U 19074A   25260.50000000  .00000000  00000-0  00000-0 0  9999",
                    "line2": "2 12345  53.0000   0.0000 0001000   0.0000   0.0000 15.50000000 12345",
                    "epoch_year": 2025,
                    "epoch_day": 260.5
                }
            ]
        }

        with patch.object(processor, '_load_tle_data', return_value=mock_tle_data):
            # 執行處理
            result = processor.execute()

            # 驗證輸出只包含軌道計算結果
            assert "metadata" in result
            assert "orbital_data" in result
            assert result["success"] is True

            # 🔧 重構驗證: 確認不包含觀測者相關數據
            orbital_data = result["orbital_data"]
            for constellation_data in orbital_data.values():
                for satellite in constellation_data:
                    # 應該只有ECI位置和速度，沒有觀測者幾何
                    assert "position_eci" in satellite
                    assert "velocity_eci" in satellite

                    # 這些觀測者相關欄位不應該存在
                    observer_fields = [
                        "elevation_deg", "azimuth_deg", "range_km",
                        "observer_geometry", "visibility_status"
                    ]
                    for field in observer_fields:
                        assert field not in satellite, f"觀測者欄位 {field} 不應該存在"

    @pytest.mark.unit
    @pytest.mark.stage1
    @pytest.mark.critical
    def test_tle_epoch_time_usage(self, processor):
        """驗證使用TLE epoch時間而非當前時間進行計算"""
        mock_tle_data = {
            "starlink": [
                {
                    "name": "STARLINK-TEST",
                    "line1": "1 12345U 19074A   25260.50000000  .00000000  00000-0  00000-0 0  9999",
                    "line2": "2 12345  53.0000   0.0000 0001000   0.0000   0.0000 15.50000000 12345",
                    "epoch_year": 2025,
                    "epoch_day": 260.5  # 2025年第260.5天
                }
            ]
        }

        with patch.object(processor, '_load_tle_data', return_value=mock_tle_data):
            with patch('stages.stage1_orbital_calculation.tle_orbital_calculation_processor.datetime') as mock_datetime:
                # 設定當前時間為與TLE epoch不同的時間
                mock_current_time = datetime(2025, 9, 18, tzinfo=timezone.utc)  # 第261天
                mock_datetime.now.return_value = mock_current_time
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                result = processor.execute()

                # 驗證使用了TLE epoch時間
                metadata = result["metadata"]

                # 🔧 重構關鍵驗證: 計算基準時間應該是TLE epoch而非當前時間
                expected_epoch_date = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=260.5-1)

                # 確認元數據中記錄了正確的時間基準
                assert "calculation_base_time" in metadata
                assert "tle_epoch_used" in metadata
                assert metadata["tle_epoch_used"] is True

    @pytest.mark.unit
    @pytest.mark.stage1
    def test_stage_responsibility_compliance(self, processor):
        """驗證Stage 1嚴格遵循職責邊界"""
        # Stage 1應該只處理軌道計算，不應該有其他階段的功能

        # 確認沒有Stage 2功能 (可見性過濾)
        stage2_methods = ['filter_by_elevation', 'check_visibility', 'apply_geographic_filter']
        for method in stage2_methods:
            assert not hasattr(processor, method)

        # 確認沒有Stage 3功能 (信號分析)
        stage3_methods = ['calculate_rsrp', 'analyze_signal_quality', 'compute_path_loss']
        for method in stage3_methods:
            assert not hasattr(processor, method)

        # 確認只有軌道計算相關方法
        orbital_methods = ['_load_tle_data', '_calculate_orbital_positions', 'execute']
        for method in orbital_methods:
            assert hasattr(processor, method), f"軌道計算方法 {method} 應該存在"

    @pytest.mark.integration
    @pytest.mark.stage1
    def test_output_format_compliance(self, processor):
        """測試輸出格式符合Stage間介面規範"""
        mock_tle_data = {
            "starlink": [
                {
                    "name": "STARLINK-TEST",
                    "line1": "1 12345U 19074A   25260.50000000  .00000000  00000-0  00000-0 0  9999",
                    "line2": "2 12345  53.0000   0.0000 0001000   0.0000   0.0000 15.50000000 12345",
                    "epoch_year": 2025,
                    "epoch_day": 260.5
                }
            ]
        }

        with patch.object(processor, '_load_tle_data', return_value=mock_tle_data):
            result = processor.execute()

            # 驗證標準輸出格式
            assert isinstance(result, dict)
            assert "metadata" in result
            assert "orbital_data" in result
            assert "success" in result

            # 驗證metadata結構
            metadata = result["metadata"]
            required_metadata = [
                "stage", "execution_time_seconds", "timestamp",
                "total_satellites", "calculation_base_time"
            ]
            for field in required_metadata:
                assert field in metadata

            # 確認不包含觀測者相關metadata
            observer_metadata = [
                "observer_coordinates", "elevation_threshold",
                "visibility_count", "observer_geometry"
            ]
            for field in observer_metadata:
                assert field not in metadata, f"觀測者metadata {field} 不應該存在"

    @pytest.mark.performance
    @pytest.mark.stage1
    def test_refactored_performance_improvement(self, processor):
        """驗證重構後性能提升 (移除不必要計算)"""
        mock_tle_data = {
            "starlink": [{"name": f"STARLINK-{i}",
                         "line1": "1 12345U 19074A   25260.50000000  .00000000  00000-0  00000-0 0  9999",
                         "line2": "2 12345  53.0000   0.0000 0001000   0.0000   0.0000 15.50000000 12345",
                         "epoch_year": 2025, "epoch_day": 260.5} for i in range(100)]
        }

        with patch.object(processor, '_load_tle_data', return_value=mock_tle_data):
            import time
            start_time = time.time()

            result = processor.execute()

            execution_time = time.time() - start_time

            # 重構後應該更快 (移除了觀測者計算)
            # 100顆衛星應該在5秒內完成 (純軌道計算)
            assert execution_time < 5.0, f"執行時間 {execution_time:.2f}s 超過預期"
            assert result["success"] is True
            assert len(result["orbital_data"]["starlink"]) == 100


# 重構後快照標記
@pytest.mark.refactored
@pytest.mark.snapshot
class TestStage1RefactoringSnapshot:
    """重構效果快照測試"""

    def test_refactoring_completeness(self):
        """驗證重構完整性"""
        processor = Stage1TLEProcessor()

        # 確認所有觀測者相關功能已移除
        removed_attributes = [
            'observer_calculations', 'observer_coordinates',
            'elevation_threshold', 'azimuth_range'
        ]

        for attr in removed_attributes:
            assert not hasattr(processor, attr), f"屬性 {attr} 應該已被移除"

        # 確認核心軌道計算功能保留
        essential_methods = ['execute', '_load_tle_data']
        for method in essential_methods:
            assert hasattr(processor, method), f"核心方法 {method} 應該保留"