#!/usr/bin/env python3
"""
驗證Stage 2時間基準繼承機制修復
直接測試修復後的實際代碼
"""

import sys
import json
from datetime import datetime, timezone
sys.path.append('/home/sat/ntn-stack/orbit-engine-system/src')

def verify_stage2_time_inheritance_fix():
    """驗證Stage 2時間基準繼承機制修復"""

    print("=== 驗證Stage 2時間基準繼承機制修復 ===")

    try:
        from stages.stage2_visibility_filter.satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor

        # 創建模擬的Stage 1輸出數據
        mock_stage1_data = {
            "data": {
                "satellites": {
                    "STARLINK-1001": {
                        "position_timeseries": [
                            {
                                "timestamp": "2025-09-08T10:30:45.123Z",
                                "position_eci": {"x": 1234.5, "y": 2345.6, "z": 3456.7}
                            }
                        ]
                    }
                }
            },
            "metadata": {
                "stage": 1,
                "data_lineage": {
                    "calculation_base_time": "2025-09-08T10:30:45.123Z",
                    "tle_epoch_time": "2025-09-08T10:30:45.123Z",
                    "time_base_source": "tle_epoch_derived",
                    "tle_epoch_compliance": True,
                    "stage1_time_inheritance": {
                        "exported_time_base": "2025-09-08T10:30:45.123Z",
                        "inheritance_ready": True,
                        "calculation_reference": "tle_epoch_based"
                    }
                }
            }
        }

        # 創建Stage 2處理器實例（使用最小配置）
        processor = SatelliteVisibilityFilterProcessor()

        print("1. 測試_extract_and_inherit_time_base方法...")

        # 測試時間基準繼承方法
        initial_calculation_base_time = getattr(processor, 'calculation_base_time', None)
        print(f"   初始calculation_base_time: {initial_calculation_base_time}")

        # 執行時間基準繼承
        processor._extract_and_inherit_time_base(mock_stage1_data)

        # 檢查結果
        final_calculation_base_time = getattr(processor, 'calculation_base_time', None)
        inherited_time_base = mock_stage1_data.get("inherited_time_base")

        print(f"   修復後calculation_base_time: {final_calculation_base_time}")
        print(f"   設置的inherited_time_base: {inherited_time_base}")

        # 驗證結果
        expected_time = "2025-09-08T10:30:45.123Z"

        success_checks = []

        # 檢查1：calculation_base_time是否正確設置
        if final_calculation_base_time == expected_time:
            print("   ✅ calculation_base_time設置正確")
            success_checks.append(True)
        else:
            print(f"   ❌ calculation_base_time設置錯誤: {final_calculation_base_time}")
            success_checks.append(False)

        # 檢查2：inherited_time_base字段是否正確設置
        if inherited_time_base == expected_time:
            print("   ✅ inherited_time_base字段設置正確")
            success_checks.append(True)
        else:
            print(f"   ❌ inherited_time_base字段設置錯誤: {inherited_time_base}")
            success_checks.append(False)

        print("\n2. 測試處理流程中的時間基準檢查...")

        # 模擬process_intelligent_filtering中的檢查邏輯
        inherited_time_base_check = mock_stage1_data.get("inherited_time_base")
        if inherited_time_base_check:
            print(f"   🎯 v6.0 重構：使用繼承的Stage 1時間基準: {inherited_time_base_check}")
            success_checks.append(True)
        else:
            print("   ⚠️ Stage 1數據中未找到inherited_time_base，可能使用舊版格式")
            success_checks.append(False)

        # 最終結果
        if all(success_checks):
            print("\n✅ Stage 2時間基準繼承機制修復驗證通過")
            return True
        else:
            print("\n❌ Stage 2時間基準繼承機制修復驗證失敗")
            return False

    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_stage2_time_inheritance_fix()
    if success:
        print("\n🎯 修復成功！Stage 2現在能正確繼承Stage 1的時間基準")
        print("下一步: 運行完整的Stage 1+2管道測試")
    else:
        print("\n❌ 修復需要進一步調整")