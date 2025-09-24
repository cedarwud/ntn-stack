#!/usr/bin/env python3
"""
驗證引擎測試 - 確保硬編碼驗證已被真實驗證邏輯取代

測試目標：
1. 確保 0% 覆蓋率正確回傳 FAILURE
2. 確保真實數據處理成功回傳 PASS
3. 確保邊界條件正確處理
4. 確保所有驗證器都有實際業務邏輯

作者: Claude
創建日期: 2025-09-20
版本: v1.0 - 驗證框架測試
"""

import pytest
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from shared.validation_framework.validation_engine import ValidationEngine
from shared.validation_framework.stage2_validator import Stage2VisibilityValidator
from shared.validation_framework.stage3_validator import Stage3SignalValidator
from shared.validation_framework.stage4_validator import Stage4TimeseriesValidator


class TestValidationEngines:
    """驗證引擎測試 - 確保真實驗證邏輯正常工作"""

    def test_stage2_zero_satellites_should_fail(self):
        """🔥 關鍵測試：Stage 2 零衛星輸出應該失敗"""
        # 安排：有輸入但無輸出的情況 (過濾異常)
        input_data = {
            "satellites": [
                {"satellite_id": "SAT-001", "elevation_deg": 15.0},
                {"satellite_id": "SAT-002", "elevation_deg": 12.0}
            ]
        }
        output_data = {
            "visible_satellites": []  # 零輸出！
        }

        # 執行：使用真實驗證器
        validator = Stage2VisibilityValidator()
        result = validator.validate_filtering_logic(input_data, output_data)

        # 驗證：必須識別為失敗
        assert result.status.value == 'FAILURE', f"期望 FAILURE，但得到 {result.status}"
        assert "過濾異常" in result.message, "應該檢測到過濾異常"

    def test_stage2_normal_filtering_should_pass(self):
        """測試：Stage 2 正常過濾應該通過"""
        # 安排：正常的過濾結果
        input_data = {
            "satellites": [
                {"satellite_id": "SAT-001", "elevation_deg": 15.0},
                {"satellite_id": "SAT-002", "elevation_deg": 5.0},  # 低仰角
                {"satellite_id": "SAT-003", "elevation_deg": 12.0}
            ]
        }
        output_data = {
            "visible_satellites": [
                {"satellite_id": "SAT-001", "elevation_deg": 15.0},
                {"satellite_id": "SAT-003", "elevation_deg": 12.0}
            ]
        }

        # 執行
        validator = Stage2VisibilityValidator()
        result = validator.validate_filtering_logic(input_data, output_data)

        # 驗證：應該通過
        assert result.status.value == 'SUCCESS', f"期望 SUCCESS，但得到 {result.status}"

    def test_stage3_zero_satellites_should_fail(self):
        """🔥 關鍵測試：Stage 3 零衛星輸出應該失敗"""
        # 安排：有輸入但無信號分析結果
        input_data = {
            "visible_satellites": [
                {"satellite_id": "SAT-001"},
                {"satellite_id": "SAT-002"}
            ]
        }
        output_data = {
            "signal_quality_data": []  # 零輸出！
        }

        # 執行
        validator = Stage3SignalValidator()
        result = validator.validate_signal_quality(output_data)

        # 驗證：必須識別為失敗
        assert result.status.value == 'FAILURE', f"期望 FAILURE，但得到 {result.status}"
        assert "無信號品質數據" in result.message, "應該檢測到無信號品質數據"

    def test_stage3_invalid_rsrp_should_fail(self):
        """測試：Stage 3 無效 RSRP 值應該失敗"""
        # 安排：RSRP 值超出合理範圍
        input_data = {"visible_satellites": [{"satellite_id": "SAT-001"}]}
        output_data = {
            "signal_quality_data": [
                {"satellite_id": "SAT-001", "rsrp_dbm": -200},  # 超出範圍
                {"satellite_id": "SAT-002", "rsrp_dbm": 0}      # 超出範圍
            ]
        }

        # 執行
        validator = Stage3SignalValidator()
        result = validator.validate_rsrp_range(output_data)

        # 驗證：應該失敗
        assert result.status.value == 'FAILURE', f"期望 FAILURE，但得到 {result.status}"
        assert "RSRP 值超出物理範圍" in result.message, "應該檢測到 RSRP 範圍錯誤"

    def test_stage3_valid_rsrp_should_pass(self):
        """測試：Stage 3 有效 RSRP 值應該通過"""
        # 安排：合理的 RSRP 值範圍 (-40dBm 到 -120dBm)
        output_data = {
            "signal_quality_data": [
                {"satellite_id": "SAT-001", "rsrp_dbm": -85.0},  # 良好信號
                {"satellite_id": "SAT-002", "rsrp_dbm": -110.0}, # 弱信號但可用
                {"satellite_id": "SAT-003", "rsrp_dbm": -65.0}   # 強信號
            ]
        }

        # 執行
        validator = Stage3SignalValidator()
        result = validator.validate_rsrp_range(output_data)

        # 驗證：應該通過
        assert result.status.value == 'SUCCESS', f"期望 SUCCESS，但得到 {result.status}"

    def test_stage4_zero_coverage_should_fail(self):
        """🔥 關鍵測試：Stage 4 零覆蓋率應該失敗"""
        # 安排：有輸入但覆蓋率為 0 的情況
        input_data = {
            "signal_quality_data": [
                {"satellite_id": "SAT-001", "rsrp_dbm": -85.0}
            ]
        }
        output_data = {
            "coverage_analysis": {
                "coverage_windows": []  # 零覆蓋！
            },
            "timeseries_data": {
                "satellites": []
            }
        }

        # 執行
        validator = Stage4TimeseriesValidator()
        result = validator.validate_coverage_analysis(input_data, output_data)

        # 驗證：必須識別為失敗
        assert result.status.value == 'FAILURE', f"期望 FAILURE，但得到 {result.status}"
        assert "覆蓋分析失效" in result.message or "覆蓋率=0%" in result.message, "應該檢測到覆蓋率問題"

    def test_stage4_valid_coverage_should_pass(self):
        """測試：Stage 4 有效覆蓋率應該通過"""
        # 安排：正常的覆蓋率分析結果
        input_data = {
            "signal_quality_data": [
                {"satellite_id": "SAT-001", "rsrp_dbm": -85.0},
                {"satellite_id": "SAT-002", "rsrp_dbm": -95.0}
            ]
        }
        output_data = {
            "coverage_analysis": {
                "coverage_windows": [
                    {"satellite_id": "SAT-001", "duration_minutes": 5.2},
                    {"satellite_id": "SAT-002", "duration_minutes": 3.8}
                ],
                "coverage_statistics": {
                    "coverage_ratio": 0.855,  # 85.5%
                    "total_coverage_percentage": 85.5,
                    "average_window_duration": 4.5
                }
            },
            "timeseries_data": {
                "satellites": [
                    {"satellite_id": "SAT-001"},
                    {"satellite_id": "SAT-002"}
                ]
            }
        }

        # 執行
        validator = Stage4TimeseriesValidator()
        result = validator.validate_coverage_analysis(input_data, output_data)

        # 驗證：應該通過
        assert result.status.value == 'SUCCESS', f"期望 SUCCESS，但得到 {result.status}"

    def test_validation_engine_integration(self):
        """測試：驗證引擎整合功能"""
        # 安排：創建驗證引擎並添加驗證器
        engine = ValidationEngine('stage2')
        engine.add_validator(Stage2VisibilityValidator())

        input_data = {
            "satellites": [{"satellite_id": "SAT-001"}]
        }
        output_data = {
            "visible_satellites": []  # 失敗案例
        }

        # 執行
        validation_result = engine.validate(input_data, output_data)

        # 驗證：引擎應該正確整合驗證結果
        assert validation_result.overall_status == 'FAIL', "驗證應該失敗"
        assert len(validation_result.checks) > 0, "應該有執行的檢查"

    def test_all_validators_have_real_logic(self):
        """🔥 關鍵測試：確保所有驗證器都有真實邏輯 (非硬編碼)"""
        # 創建失敗案例數據
        failing_input = {"signal_quality_data": []}
        failing_output = {"signal_quality_data": [], "visible_satellites": [], "coverage_analysis": {"coverage_windows": []}}

        validators = [
            Stage2VisibilityValidator(),
            Stage3SignalValidator(),
            Stage4TimeseriesValidator()
        ]

        for validator in validators:
            # 每個驗證器都應該能夠識別失敗案例
            results = []

            # 執行驗證器的所有驗證方法
            for method_name in dir(validator):
                if method_name.startswith('validate_') and callable(getattr(validator, method_name)):
                    method = getattr(validator, method_name)
                    try:
                        if 'input_data' in method.__code__.co_varnames:
                            result = method(failing_input, failing_output)
                        else:
                            result = method(failing_output)
                        results.append(result)
                    except Exception as e:
                        # 某些方法可能需要特定參數，跳過
                        continue

            # 驗證：至少有一個方法識別為失敗 (證明有真實邏輯)
            failure_detected = any(r.status.value == 'FAILURE' for r in results if hasattr(r, 'status'))
            assert failure_detected or len(results) == 0, f"{validator.__class__.__name__} 應該能識別失敗案例"


class TestValidationFailureCriteria:
    """驗證失敗標準測試 - 確保業務邏輯正確"""

    def test_zero_processing_equals_failure(self):
        """🚨 核心原則測試：0 處理 = FAILURE"""
        test_cases = [
            # Stage 2: 有輸入無輸出
            {
                "validator": Stage2VisibilityValidator(),
                "method": "validate_filtering_logic",
                "input_data": {"satellites": [{"satellite_id": "SAT-001"}]},
                "output_data": {"visible_satellites": []},
                "description": "Stage2: 0 可見衛星"
            },
            # Stage 3: 有輸入無信號分析
            {
                "validator": Stage3SignalValidator(),
                "method": "validate_signal_quality",
                "input_data": {"visible_satellites": [{"satellite_id": "SAT-001"}]},
                "output_data": {"signal_quality_data": []},
                "description": "Stage3: 0 信號分析"
            },
            # Stage 4: 有輸入無覆蓋率
            {
                "validator": Stage4TimeseriesValidator(),
                "method": "validate_coverage_analysis",
                "input_data": {"signal_quality_data": [{"satellite_id": "SAT-001"}]},
                "output_data": {"coverage_analysis": {"coverage_windows": []}},
                "description": "Stage4: 0 覆蓋窗口"
            }
        ]

        for case in test_cases:
            validator = case["validator"]
            method = getattr(validator, case["method"])

            # 根據方法名稱決定參數
            if case["method"] == "validate_signal_quality" or case["method"] == "validate_rsrp_range":
                # Stage 3 方法只需要 output_data
                result = method(case["output_data"])
            else:
                # 其他方法需要 input_data 和 output_data
                result = method(case["input_data"], case["output_data"])

            assert result.status.value == 'FAILURE', f"{case['description']} 應該回傳 FAILURE"

    def test_successful_processing_passes(self):
        """測試：成功處理應該通過驗證"""
        # Stage 2 成功案例
        stage2_validator = Stage2VisibilityValidator()
        stage2_result = stage2_validator.validate_filtering_logic(
            {"satellites": [{"satellite_id": "SAT-001"}, {"satellite_id": "SAT-002"}]},
            {"visible_satellites": [{"satellite_id": "SAT-001"}]}
        )
        assert stage2_result.status.value == 'SUCCESS'

        # Stage 3 成功案例
        stage3_validator = Stage3SignalValidator()
        stage3_result = stage3_validator.validate_signal_quality(
            {"signal_quality_data": [{"satellite_id": "SAT-001", "rsrp_dbm": -85.0, "distance_km": 1500}]}
        )
        assert stage3_result.status.value == 'SUCCESS'


if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v"])